"""
Lab 03 - Sprint 1: Coleta de Dados de Pull Requests (Versão Otimizada)
========================================================================
- Usa GraphQL para buscar repositórios
- Coleta até encontrar 200 repositórios VÁLIDOS (com >=100 PRs)
- Limita coleta a 500 PRs VÁLIDOS por repositório
- Implementa paginação adequada

"""

import os
import sys
import json
import csv
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv

# Configura encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Força flush imediato dos prints
sys.stdout.reconfigure(line_buffering=True)

# Carrega variáveis de ambiente
load_dotenv('config.env')

# Configurações
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
MODE = os.getenv('MODE', 'test')

if MODE == 'test':
    MAX_REPOSITORIES = int(os.getenv('TEST_MAX_REPOSITORIES', 3))
    MAX_PRS_PER_REPO = int(os.getenv('TEST_MAX_PRS_PER_REPO', 5))
    MIN_PRS = int(os.getenv('TEST_MIN_PRS', 10))
else:
    MAX_REPOSITORIES = int(os.getenv('PROD_MAX_REPOSITORIES', 200))
    MAX_PRS_PER_REPO = int(os.getenv('PROD_MAX_PRS_PER_REPO', 500))
    MIN_PRS = int(os.getenv('PROD_MIN_PRS', 100))

DELAY_BETWEEN_REQUESTS = 1.0  # Cooldown de 1s entre requisições GraphQL
RATE_LIMIT_THRESHOLD = 500  # Pausa preventiva quando rate limit cai abaixo disso
RATE_LIMIT_PAUSE = 300  # Pausa de 5 minutos quando rate limit está baixo

# Arquivos de checkpoint
CHECKPOINT_FILE = f'data/checkpoint_{MODE}.json'
CHECKPOINT_CSV = f'data/checkpoint_{MODE}.csv'

# Headers
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

GRAPHQL_HEADERS = {
    'Authorization': f'bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json'
}

# Lock para prints thread-safe
print_lock = threading.Lock()

def safe_print(msg, end='\n', flush=True):
    """Print thread-safe"""
    with print_lock:
        print(msg, end=end, flush=flush)


class GitHubAPIError(Exception):
    """Exceção customizada para erros da API do GitHub"""
    pass


def make_request(url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[Dict]:
    """
    Faz requisição à API com monitoramento proativo de rate limit
    """
    time.sleep(DELAY_BETWEEN_REQUESTS)  # Cooldown entre requisições
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            
            # Monitora rate limit PROATIVAMENTE
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
            rate_limit_reset = response.headers.get('X-RateLimit-Reset')
            
            if rate_limit_remaining:
                remaining = int(rate_limit_remaining)
                
                # PAUSA PREVENTIVA quando rate limit está baixo
                if remaining < RATE_LIMIT_THRESHOLD:
                    reset_time = int(rate_limit_reset) if rate_limit_reset else 0
                    wait_time = reset_time - time.time() if reset_time > time.time() else RATE_LIMIT_PAUSE
                    
                    safe_print(f"\n⚠️  RATE LIMIT PREVENTIVO: {remaining} requisições restantes")
                    safe_print(f"   ⏸️  Pausando por {wait_time/60:.1f} minutos para evitar bloqueio...")
                    time.sleep(wait_time + 10)
                    safe_print(f"   ▶️  Retomando coleta...")
                
                # Avisa periodicamente
                elif remaining % 500 == 0:
                    safe_print(f"   ⚡ Rate limit: {remaining} requisições restantes")
            
            # Tratamento de rate limit (caso ainda atinja)
            if response.status_code == 403:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = reset_time - time.time()
                if wait_time > 0:
                    safe_print(f"\n❌ RATE LIMIT ATINGIDO! Aguardando {wait_time/60:.1f} minutos...")
                    time.sleep(wait_time + 10)
                    continue
            
            # Tratamento de erros de servidor (502, 503, 504)
            if response.status_code in [502, 503, 504]:
                if attempt < max_retries - 1:
                    safe_print(f"\n⚠️  Erro {response.status_code}, tentativa {attempt+1}/{max_retries}...")
                    time.sleep(15)
                    continue
                else:
                    safe_print(f"\n❌ Erro {response.status_code} persistente, pulando...")
                    return None
            
            if response.status_code == 200:
                return response.json()
            else:
                safe_print(f"\n⚠️  Status {response.status_code}: {url}")
                return None
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                safe_print(f"\n⚠️  Timeout, tentativa {attempt+1}/{max_retries}...")
                time.sleep(10)
                continue
            else:
                return None
        except Exception as e:
            safe_print(f"\n⚠️  Erro: {e}")
            return None
    
    return None


def get_top_repositories_graphql(count: int = 200, min_prs: int = 100) -> List[Dict]:
    """
    Busca repositórios usando GraphQL até encontrar 'count' repositórios VÁLIDOS
    """
    print(f"\n{'='*70}", flush=True)
    print(f"🔍 FASE 1: Buscando repositórios via GraphQL", flush=True)
    print(f"   Meta: {count} repositórios com pelo menos {min_prs} PRs", flush=True)
    print(f"{'='*70}", flush=True)
    
    url = "https://api.github.com/graphql"
    valid_repositories = []
    cursor = None
    total_searched = 0
    
    query = """
    query($cursor: String) {
      search(query: "stars:>1", type: REPOSITORY, first: 100, after: $cursor) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          ... on Repository {
            name
            nameWithOwner
            owner {
              login
            }
            stargazerCount
            forkCount
            primaryLanguage {
              name
            }
            createdAt
            url
            pullRequests(states: [MERGED, CLOSED]) {
              totalCount
            }
          }
        }
      }
    }
    """
    
    while len(valid_repositories) < count:
        variables = {"cursor": cursor}
        
        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers=GRAPHQL_HEADERS,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"\n❌ Erro GraphQL: {response.status_code}", flush=True)
                break
            
            data = response.json()
            
            if 'errors' in data:
                print(f"\n❌ Erro GraphQL: {data['errors']}", flush=True)
                break
            
            search_result = data['data']['search']
            nodes = search_result['nodes']
            
            for repo in nodes:
                if repo:
                    total_searched += 1
                    total_prs = repo['pullRequests']['totalCount']
                    
                    if total_prs >= min_prs:
                        repo_info = {
                            'name': repo['name'],
                            'full_name': repo['nameWithOwner'],
                            'owner': repo['owner']['login'],
                            'stars': repo['stargazerCount'],
                            'forks': repo['forkCount'],
                            'language': repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'Unknown',
                            'created_at': repo['createdAt'],
                            'url': repo['url'],
                            'total_prs': total_prs
                        }
                        valid_repositories.append(repo_info)
                        
                        if len(valid_repositories) % 10 == 0:
                            print(f"   ✅ {len(valid_repositories)}/{count} repositórios válidos (de {total_searched} analisados)", flush=True)
                        
                        if len(valid_repositories) >= count:
                            break
            
            if len(valid_repositories) >= count:
                print(f"\n   🎯 Meta atingida! {count} repositórios válidos coletados!", flush=True)
                break
            
            if not search_result['pageInfo']['hasNextPage']:
                print(f"\n   ⚠️  Fim dos resultados. {len(valid_repositories)} repositórios válidos encontrados.", flush=True)
                break
            
            cursor = search_result['pageInfo']['endCursor']
            time.sleep(1)  # Pausa entre páginas GraphQL
            
        except Exception as e:
            print(f"\n❌ Erro na busca GraphQL: {e}", flush=True)
            break
    
    print(f"\n   📊 Total: {len(valid_repositories)} repositórios válidos de {total_searched} analisados", flush=True)
    return valid_repositories


def get_prs_graphql(owner: str, repo: str, cursor: Optional[str] = None, max_prs: int = 100, max_retries: int = 3) -> tuple[List[Dict], Optional[str], bool]:
    """
    Busca PRs usando GraphQL - MUITO mais eficiente!
    Retorna (prs, next_cursor, has_next_page)
    Inclui retry logic para erros temporários (502, 503, timeout)
    """
    query = """
    query($owner: String!, $repo: String!, $cursor: String) {
      repository(owner: $owner, name: $repo) {
        pullRequests(first: 100, after: $cursor, states: [MERGED, CLOSED], orderBy: {field: UPDATED_AT, direction: DESC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            number
            title
            state
            createdAt
            closedAt
            mergedAt
            additions
            deletions
            changedFiles
            commits {
              totalCount
            }
            reviews {
              totalCount
            }
            comments {
              totalCount
            }
            author {
              login
            }
          }
        }
      }
    }
    """
    
    variables = {
        "owner": owner,
        "repo": repo,
        "cursor": cursor
    }
    
    for attempt in range(max_retries):
        try:
            time.sleep(DELAY_BETWEEN_REQUESTS)
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=GRAPHQL_HEADERS,
                timeout=30
            )
            
            # Erros temporários que podem ser retentados
            if response.status_code in [502, 503, 504]:
                retry_delay = 5 * (attempt + 1)  # 5s, 10s, 15s
                safe_print(f"\n⚠️  GraphQL erro {response.status_code} (tentativa {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    safe_print(f"   ⏳ Aguardando {retry_delay}s antes de tentar novamente...")
                    time.sleep(retry_delay)
                    continue
                else:
                    safe_print(f"   ❌ Todas as tentativas falharam")
                    return [], None, False
            
            if response.status_code != 200:
                safe_print(f"\n⚠️  GraphQL erro {response.status_code}")
                return [], None, False
            
            data = response.json()
            
            if 'errors' in data:
                safe_print(f"\n⚠️  GraphQL errors: {data['errors']}")
                return [], None, False
            
            pr_data = data['data']['repository']['pullRequests']
            page_info = pr_data['pageInfo']
            prs = pr_data['nodes']
            
            return prs, page_info['endCursor'], page_info['hasNextPage']
            
        except requests.exceptions.Timeout:
            retry_delay = 5 * (attempt + 1)
            safe_print(f"\n⚠️  Timeout (tentativa {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                safe_print(f"   ⏳ Aguardando {retry_delay}s antes de tentar novamente...")
                time.sleep(retry_delay)
                continue
            else:
                safe_print(f"   ❌ Todas as tentativas falharam")
                return [], None, False
                
        except Exception as e:
            safe_print(f"\n⚠️  Erro GraphQL: {e}")
            return [], None, False
    
    return [], None, False


def calculate_pr_metrics_from_graphql(pr: Dict, repo_full_name: str) -> Optional[Dict]:
    """Calcula métricas de um PR vindo do GraphQL"""
    try:
        created_at = datetime.strptime(pr['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
        
        if pr['closedAt']:
            closed_at = datetime.strptime(pr['closedAt'], '%Y-%m-%dT%H:%M:%SZ')
        else:
            return None
        
        analysis_time = closed_at - created_at
        analysis_hours = analysis_time.total_seconds() / 3600
        
        # Filtros:
        # 1. Tempo de análise > 1 hora
        if analysis_hours <= 1.0:
            return None
        
        # 2. Precisa ter pelo menos 1 review
        num_reviews = pr['reviews']['totalCount']
        if num_reviews == 0:
            return None
        
        return {
            'repository': repo_full_name,
            'pr_number': pr['number'],
            'title': pr['title'],
            'status': 'MERGED' if pr['mergedAt'] else 'CLOSED',
            'created_at': pr['createdAt'],
            'closed_at': pr['closedAt'],
            'merged_at': pr.get('mergedAt'),
            'files_changed': pr.get('changedFiles', 0),
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0),
            'total_changes': pr.get('additions', 0) + pr.get('deletions', 0),
            'num_commits': pr['commits']['totalCount'],
            'num_reviews': num_reviews,
            'num_comments': pr['comments']['totalCount'],
            'analysis_time_hours': analysis_hours,
            'author': pr['author']['login'] if pr['author'] else 'unknown'
        }
    except Exception as e:
        return None


def collect_repository_prs(repo: Dict, max_prs: int) -> List[Dict]:
    """
    Coleta até 'max_prs' PRs VÁLIDOS de um repositório usando GraphQL
    - UMA requisição GraphQL busca 100 PRs com TODOS os dados (reviews, comments, etc)
    - Muito mais eficiente que REST API (que precisava de 3-4 requests por PR)
    """
    owner = repo['owner']
    name = repo['name']
    full_name = repo['full_name']
    
    safe_print(f"\n{'─'*70}")
    safe_print(f"📊 Repositório: {full_name}")
    safe_print(f"   ⭐ Stars: {repo['stars']:,} | Total PRs: {repo['total_prs']}")
    
    valid_prs = []
    cursor = None
    page = 1
    total_processed = 0
    had_error = False
    
    # Continua até encontrar max_prs PRs VÁLIDOS ou acabar os PRs
    while len(valid_prs) < max_prs:
        # GraphQL: 1 requisição busca 100 PRs com TODAS as informações
        safe_print(f"   📦 Página {page}: Buscando 100 PRs via GraphQL...")
        prs_batch, next_cursor, has_next = get_prs_graphql(owner, name, cursor, 100)
        
        if not prs_batch:
            if page == 1:
                safe_print(f"   ⚠️  Erro ao buscar PRs (possível erro 502/503 do GitHub)")
                had_error = True
            else:
                safe_print(f"   ℹ️  Nenhum PR retornado nesta página")
            break
        
        safe_print(f"   ✅ Recebidos {len(prs_batch)} PRs (1 requisição GraphQL!)")
        
        # Processa PRs do batch
        page_results = []
        for pr in prs_batch:
            total_processed += 1
            
            # Calcula métricas (já temos todos os dados!)
            metrics = calculate_pr_metrics_from_graphql(pr, full_name)
            
            if metrics:
                page_results.append(metrics)
                safe_print(f"      ✅ PR #{pr['number']} válido")
            else:
                safe_print(f"      ❌ PR #{pr['number']} filtrado")
        
        # Adiciona PRs válidos da página
        valid_prs.extend(page_results)
        safe_print(f"   📊 Página {page} concluída: {len(page_results)} válidos | Total acumulado: {len(valid_prs)}/{max_prs}")
        
        # Verifica se deve continuar
        if len(valid_prs) >= max_prs:
            valid_prs = valid_prs[:max_prs]
            safe_print(f"   🎯 Meta de {max_prs} PRs válidos alcançada!")
            break
        
        if not has_next:
            safe_print(f"   ℹ️  Última página alcançada")
            break
        
        cursor = next_cursor
        page += 1
    
    safe_print(f"\n   📊 RESULTADO: {len(valid_prs)} PRs válidos de {total_processed} processados")
    
    if len(valid_prs) == 0 and had_error:
        safe_print(f"   ⚠️  ATENÇÃO: 0 PRs coletados devido a erro de comunicação com GitHub")
    elif len(valid_prs) == 0:
        safe_print(f"   ℹ️  Nenhum PR atendeu aos critérios (>1h análise + >=1 revisão)")
    
    return valid_prs


def load_checkpoint() -> tuple[List[Dict], set]:
    """
    Carrega checkpoint existente e retorna (all_prs, processed_repos)
    """
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_prs = data.get('prs', [])
                processed_repos = set(data.get('processed_repos', []))
                safe_print(f"\n📂 Checkpoint encontrado!")
                safe_print(f"   ✅ {len(all_prs)} PRs já coletados")
                safe_print(f"   ✅ {len(processed_repos)} repositórios já processados")
                return all_prs, processed_repos
        except Exception as e:
            safe_print(f"\n⚠️  Erro ao carregar checkpoint: {e}")
    
    return [], set()


def save_checkpoint(all_prs: List[Dict], processed_repos: set):
    """
    Salva checkpoint incremental (atualiza o mesmo arquivo)
    """
    try:
        os.makedirs('data', exist_ok=True)
        
        # Salva JSON
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'total_prs': len(all_prs),
            'total_repos': len(processed_repos),
            'processed_repos': list(processed_repos),
            'prs': all_prs
        }
        
        with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        # Salva CSV
        if all_prs:
            keys = all_prs[0].keys()
            with open(CHECKPOINT_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(all_prs)
        
        safe_print(f"   💾 Checkpoint salvo: {len(all_prs)} PRs, {len(processed_repos)} repos")
        
    except Exception as e:
        safe_print(f"   ⚠️  Erro ao salvar checkpoint: {e}")


def save_data(prs: List[Dict], mode: str, suffix: str = ""):
    """Salva dados em JSON e CSV"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON
    json_file = f'data/lab03_{mode}{suffix}_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(prs, f, indent=2, ensure_ascii=False)
    
    # CSV
    csv_file = f'data/lab03_{mode}{suffix}_{timestamp}.csv'
    if prs:
        keys = prs[0].keys()
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(prs)
    
    return json_file, csv_file


def generate_statistics(prs: List[Dict]) -> Dict:
    """Gera estatísticas dos PRs coletados"""
    if not prs:
        return {}
    
    merged = [pr for pr in prs if pr['status'] == 'MERGED']
    closed = [pr for pr in prs if pr['status'] == 'CLOSED']
    
    stats = {
        'total_prs': len(prs),
        'merged_prs': len(merged),
        'closed_prs': len(closed),
        'repositories_count': len(set(pr['repository'] for pr in prs)),
        'metrics': {
            'files_changed': {
                'mean': sum(pr['files_changed'] for pr in prs) / len(prs),
                'min': min(pr['files_changed'] for pr in prs),
                'max': max(pr['files_changed'] for pr in prs)
            },
            'total_changes': {
                'mean': sum(pr['total_changes'] for pr in prs) / len(prs),
                'min': min(pr['total_changes'] for pr in prs),
                'max': max(pr['total_changes'] for pr in prs)
            },
            'analysis_time_hours': {
                'mean': sum(pr['analysis_time_hours'] for pr in prs) / len(prs),
                'min': min(pr['analysis_time_hours'] for pr in prs),
                'max': max(pr['analysis_time_hours'] for pr in prs)
            },
            'num_reviews': {
                'mean': sum(pr['num_reviews'] for pr in prs) / len(prs),
                'min': min(pr['num_reviews'] for pr in prs),
                'max': max(pr['num_reviews'] for pr in prs)
            },
            'num_comments': {
                'mean': sum(pr['num_comments'] for pr in prs) / len(prs),
                'min': min(pr['num_comments'] for pr in prs),
                'max': max(pr['num_comments'] for pr in prs)
            }
        }
    }
    
    return stats


def main():
    """Função principal"""
    print("="*70, flush=True)
    print("Lab 03 - Sprint 1: Coleta de Dados de Pull Requests", flush=True)
    print(f"Modo: {MODE.upper()}", flush=True)
    print("="*70, flush=True)
    
    os.makedirs('data', exist_ok=True)
    
    start_time = time.time()
    
    # Carrega checkpoint se existir
    all_prs, processed_repos = load_checkpoint()
    
    # FASE 1: Buscar repositórios VÁLIDOS
    repositories = get_top_repositories_graphql(MAX_REPOSITORIES, MIN_PRS)
    
    if not repositories:
        print("\n❌ Nenhum repositório encontrado!", flush=True)
        return
    
    # Filtra repositórios já processados
    remaining_repos = [r for r in repositories if r['full_name'] not in processed_repos]
    
    if remaining_repos:
        safe_print(f"\n📋 {len(remaining_repos)} repositórios restantes para processar (de {len(repositories)} totais)")
    else:
        safe_print(f"\n✅ Todos os {len(repositories)} repositórios já foram processados!")
        if all_prs:
            safe_print(f"   Total de PRs coletados: {len(all_prs)}")
        return
    
    # FASE 2: Coletar PRs
    print(f"\n{'='*70}", flush=True)
    print(f"📥 FASE 2: Coletando PRs dos repositórios", flush=True)
    print(f"   Limite: {MAX_PRS_PER_REPO} PRs válidos por repositório", flush=True)
    print(f"   💾 Checkpoint incremental ativado", flush=True)
    print(f"{'='*70}", flush=True)
    
    for idx, repo in enumerate(remaining_repos, 1):
        repo_name = repo['full_name']
        total_idx = len(repositories) - len(remaining_repos) + idx
        
        print(f"\n[{total_idx}/{len(repositories)}] Coletando {repo_name}...", flush=True)
        
        try:
            repo_prs = collect_repository_prs(repo, MAX_PRS_PER_REPO)
            all_prs.extend(repo_prs)
            processed_repos.add(repo_name)
            
            print(f"   ✅ {len(repo_prs)} PRs coletados | Total acumulado: {len(all_prs)}", flush=True)
            
            # Salva checkpoint incremental (mesmo arquivo)
            save_checkpoint(all_prs, processed_repos)
            
        except Exception as e:
            print(f"   ❌ Erro: {e}", flush=True)
            # Mesmo com erro, salva checkpoint
            save_checkpoint(all_prs, processed_repos)
            continue
    
    # Salvar dados finais
    if all_prs:
        print(f"\n{'='*70}", flush=True)
        print(f"💾 Salvando dados finais...", flush=True)
        json_file, csv_file = save_data(all_prs, MODE, "_final")
        print(f"   JSON: {json_file}", flush=True)
        print(f"   CSV: {csv_file}", flush=True)
        
        # Estatísticas
        stats = generate_statistics(all_prs)
        stats_file = f'data/lab03_{MODE}_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\n{'='*70}", flush=True)
        print(f"📊 ESTATÍSTICAS FINAIS", flush=True)
        print(f"{'='*70}", flush=True)
        print(f"✅ Total de PRs coletados: {len(all_prs)}", flush=True)
        print(f"📦 Repositórios processados: {len(processed_repos)}", flush=True)
        print(f"✔️  PRs Merged: {stats['merged_prs']}", flush=True)
        print(f"❌ PRs Closed: {stats['closed_prs']}", flush=True)
        print(f"⏱️  Tempo total: {(time.time() - start_time)/60:.1f} minutos", flush=True)
        print(f"{'='*70}", flush=True)
    else:
        print("\n❌ Nenhum PR válido coletado!", flush=True)


if __name__ == '__main__':
    main()
