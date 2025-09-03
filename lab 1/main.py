#!/usr/bin/env python3
"""
Lab01S02 - GraphQL API para 1.000 repositórios populares - DADOS REAIS ULTRA RÁPIDOS
Laboratório de Experimentação de Software - PUC Minas
"""

import urllib.request
import urllib.parse
import json
import time
import csv
import re
from datetime import datetime, timezone
from config import GITHUB_TOKEN


def make_graphql_request(query, variables=None):
    """Faz requisição GraphQL para GitHub API - MUITO mais eficiente"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Lab01S02-Research"
    }
    
    payload = {
        "query": query,
        "variables": variables or {}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:  # Timeout maior
            result = json.loads(response.read().decode('utf-8'))
            
        return result
        
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("Rate limit GraphQL atingido, cancelando...")
            raise Exception("Rate limit excedido")
        print(f"Erro GraphQL HTTP {e.code}: {e.reason}")
        raise
    except Exception as e:
        print(f"Erro GraphQL: {e}")
        raise

''
def make_simple_request(url, headers, params=None):
    """Requisição HTTP simples otimizada"""
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read().decode('utf-8')
            return json.loads(data), response.status, dict(response.headers)
    except urllib.error.HTTPError as e:
        return None, e.code, {}
    except Exception:
        return None, 0, {}


def collect_repositories_graphql():
    """
    REVOLUÇÃO: Usa GraphQL para coletar repositórios + TODOS os dados reais
    UMA requisição GraphQL = dados completos de múltiplos repositórios
    """
    print("🚀 GRAPHQL: Coletando 1000 repositórios com TODOS os dados reais...")
    
    all_repositories = []
    total_needed = 1000
    per_query = 25  # Reduzido para 25 repositórios por requisição (mais rápido)
    
    # Query GraphQL SIMPLIFICADA para coleta mais rápida
    query = """
    query GetRepositoriesWithStats($first: Int!, $after: String) {
        search(query: "stars:>1", type: REPOSITORY, first: $first, after: $after) {
            pageInfo {
                hasNextPage
                endCursor
            }
            nodes {
                ... on Repository {
                    name
                    owner {
                        login
                    }
                    url
                    description
                    stargazerCount
                    forkCount
                    createdAt
                    updatedAt
                    pushedAt
                    primaryLanguage {
                        name
                    }
                    hasIssuesEnabled
                    
                    # DADOS REAIS essenciais (otimizado)
                    pullRequests(states: MERGED) {
                        totalCount
                    }
                    openIssues: issues(states: OPEN) {
                        totalCount
                    }
                    closedIssues: issues(states: CLOSED) {
                        totalCount
                    }
                    releases {
                        totalCount
                    }
                }
            }
        }
    }
    """
    
    cursor = None
    page = 1
    
    while len(all_repositories) < total_needed:
        print(f"📊 GraphQL Página {page}: Coletando até 25 repositórios com dados completos...")
        
        variables = {
            "first": min(per_query, total_needed - len(all_repositories)),
            "after": cursor
        }
        
        try:
            result = make_graphql_request(query, variables)
            
            if 'data' not in result or 'search' not in result['data']:
                print(f"Erro na resposta GraphQL: {result}")
                break
                
            search_data = result['data']['search']
            repositories = search_data['nodes']
            
            print(f"  ✅ Coletados {len(repositories)} repositórios com dados REAIS")
            
            # Processar cada repositório (dados já vêm completos)
            for repo in repositories:
                if repo:  # Verificar se não é None
                    processed_repo = {
                        'name': repo['name'],
                        'owner': {'login': repo['owner']['login']},
                        'full_name': f"{repo['owner']['login']}/{repo['name']}",
                        'html_url': repo['url'],
                        'description': repo.get('description', ''),
                        'stargazers_count': repo['stargazerCount'],
                        'forks_count': repo['forkCount'],
                        'created_at': repo['createdAt'],
                        'updated_at': repo['updatedAt'],
                        'pushed_at': repo['pushedAt'],
                        'language': repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else None,
                        'has_issues': repo['hasIssuesEnabled'],
                        'has_projects': False,  # Simplificado
                        'has_wiki': False,      # Simplificado
                        'size': 0,              # Simplificado
                        
                        # DADOS REAIS coletados via GraphQL
                        'merged_prs_count': repo['pullRequests']['totalCount'],
                        'open_issues_count': repo['openIssues']['totalCount'], 
                        'closed_issues_count': repo['closedIssues']['totalCount'],
                        'total_releases': repo['releases']['totalCount']
                    }
                    
                    all_repositories.append(processed_repo)
            
            # Verificar se há próxima página
            page_info = search_data['pageInfo']
            if not page_info['hasNextPage'] or len(all_repositories) >= total_needed:
                break
                
            cursor = page_info['endCursor']
            page += 1
            
        except Exception as e:
            print(f"Erro na página GraphQL {page}: {e}")
            break
    
    print(f"✅ GraphQL: Coletados {len(all_repositories)} repositórios com dados REAIS completos")
    return all_repositories[:total_needed]


def get_all_counts_FAST(owner, repo_name, headers, repo_data=None):
    """Coleta dados de forma ULTRA RÁPIDA com limite inteligente de páginas"""
    results = {
        'merged_prs': 0,
        'closed_issues': 0,
        'total_issues': 0
    }
    
    print(f"    ⚡ Coleta rápida para {owner}/{repo_name}...")
    
    # 1. PRs merged - LIMITE INTELIGENTE (máximo 5 páginas = 500 PRs)
    merged_prs_count = 0
    max_pages_prs = 5  # Limite para acelerar
    
    for page in range(1, max_pages_prs + 1):
        prs_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        prs_params = {"state": "closed", "per_page": 100, "page": page}
        prs_data, prs_status, prs_headers = make_simple_request(prs_url, headers, prs_params)
        
        if prs_status == 200 and prs_data:
            page_merged = sum(1 for pr in prs_data if pr.get('merged_at'))
            merged_prs_count += page_merged
            
            # Para se a página não está cheia (fim dos dados)
            if len(prs_data) < 100:
                break
        else:
            break
    
    # 2. Issues fechadas - LIMITE INTELIGENTE (máximo 3 páginas = 300 issues)
    closed_issues_count = 0
    max_pages_issues = 3  # Limite para acelerar
    
    for page in range(1, max_pages_issues + 1):
        issues_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
        issues_params = {"state": "closed", "per_page": 100, "page": page}
        issues_data, issues_status, issues_headers = make_simple_request(issues_url, headers, issues_params)
        
        if issues_status == 200 and issues_data:
            actual_issues = [issue for issue in issues_data if not issue.get('pull_request')]
            closed_issues_count += len(actual_issues)
            
            if len(issues_data) < 100:
                break
        else:
            break
    
    results['merged_prs'] = merged_prs_count
    results['closed_issues'] = closed_issues_count
    
    return results


def get_releases_FAST(owner, repo_name, headers):
    """Conta releases de forma RÁPIDA com limite inteligente"""
    total_releases = 0
    max_pages = 2  # Máximo 2 páginas = 200 releases
    
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"
        params = {"per_page": 100, "page": page}
        
        data, status, response_headers = make_simple_request(url, headers, params)
        
        if status == 200 and data:
            total_releases += len(data)
            
            if len(data) < 100:
                break
        else:
            break
    
    return total_releases


def get_repository_details(owner, repo_name):
    """
    VERSÃO COMPLETA OTIMIZADA: Coleta TODOS os dados reais de forma eficiente
    Usa paginação inteligente até obter dados completos
    """
    print(f"� COMPLETO: {owner}/{repo_name}")
    
    # 1. Dados básicos do repositório (1 requisição principal)
    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Lab01S02-Research"
    }
    repo_data, status, _ = make_simple_request(repo_url, headers)
    
    if status != 200 or not repo_data:
        print(f"[ERRO] Falha ao obter dados de {owner}/{repo_name}")
        return None
    
    # 2. COLETA COMPLETA de PRs merged com paginação eficiente
    print(f"    📋 Coletando TODOS os PRs merged...")
    merged_prs_count = 0
    page = 1
    max_pages = 50  # Limite máximo para evitar loops infinitos
    
    while page <= max_pages:
        prs_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls"
        prs_params = {"state": "closed", "per_page": 100, "page": page}
        prs_data, prs_status, _ = make_simple_request(prs_url, headers, prs_params)
        
        if prs_status == 200 and prs_data:
            page_merged = sum(1 for pr in prs_data if pr.get('merged_at'))
            merged_prs_count += page_merged
            print(f"      📄 Página {page}: +{page_merged} PRs merged (Total: {merged_prs_count})")
            
            # Se retornou menos que 100, chegamos ao final
            if len(prs_data) < 100:
                break
                
            page += 1
        else:
            break
    
    # 3. COLETA COMPLETA de issues fechadas com paginação eficiente  
    print(f"    🐛 Coletando TODAS as issues fechadas...")
    closed_issues_count = 0
    page = 1
    
    while page <= max_pages:
        issues_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
        issues_params = {"state": "closed", "per_page": 100, "page": page}
        issues_data, issues_status, _ = make_simple_request(issues_url, headers, issues_params)
        
        if issues_status == 200 and issues_data:
            # Filtrar apenas issues (não PRs)
            actual_issues = [issue for issue in issues_data if not issue.get('pull_request')]
            page_issues = len(actual_issues)
            closed_issues_count += page_issues
            print(f"      📄 Página {page}: +{page_issues} issues fechadas (Total: {closed_issues_count})")
            
            # Se retornou menos que 100, chegamos ao final
            if len(issues_data) < 100:
                break
                
            page += 1
        else:
            break
    
    # 4. COLETA COMPLETA de releases
    print(f"    🚀 Coletando TODOS os releases...")
    total_releases = 0
    releases_url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"
    page = 1
    
    while page <= 10:  # Máximo 10 páginas para releases (1000 releases é bastante)
        releases_params = {"per_page": 100, "page": page}
        releases_data, releases_status, _ = make_simple_request(releases_url, headers, releases_params)
        
        if releases_status == 200 and releases_data:
            page_releases = len(releases_data)
            total_releases += page_releases
            print(f"      📄 Página {page}: +{page_releases} releases (Total: {total_releases})")
            
            if len(releases_data) < 100:
                break
                
            page += 1
        else:
            break
    
    print(f"    ✅ TOTAIS: {merged_prs_count} PRs merged, {closed_issues_count} issues fechadas, {total_releases} releases")
    
    # Retornar dados COMPLETOS e REAIS
    return {
        'repo_data': repo_data,
        'merged_prs': merged_prs_count,  # TODOS os PRs merged
        'total_releases': total_releases,  # TODOS os releases
        'closed_issues': closed_issues_count,  # TODAS as issues fechadas
        'total_issues': repo_data.get('open_issues_count', 0) + closed_issues_count,
        'open_issues': repo_data.get('open_issues_count', 0),
        
        # Dados extras já disponíveis na resposta básica:
        'has_issues': repo_data.get('has_issues', False),
        'has_projects': repo_data.get('has_projects', False), 
        'has_wiki': repo_data.get('has_wiki', False),
        'has_pages': repo_data.get('has_pages', False),
        'has_downloads': repo_data.get('has_downloads', False)
    }


def process_repository_data(repo_info):
    """Processa dados do repositório e calcula métricas"""
    repo_data = repo_info['repo_data']
    now_utc = datetime.now(timezone.utc)
    
    # Calcular idade do repositório
    created_at = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
    age_days = (now_utc - created_at).days
    
    # Dias desde última atualização - usar pushed_at (último commit) em vez de updated_at
    # updated_at pode ser atualizado por outras ações (issues, wiki, etc.)
    last_push = repo_data.get('pushed_at', repo_data['updated_at'])
    if last_push:
        pushed_at = datetime.fromisoformat(last_push.replace('Z', '+00:00'))
        days_since_update = (now_utc - pushed_at).days
    else:
        days_since_update = 0
    
    # Linguagem primária - CORRIGIDA para mostrar dados reais
    primary_language = repo_data.get('language') 
    if primary_language is None or primary_language == "":
        primary_language = 'Not specified'  # Mais claro que "Unknown"
    
    # Usar dados REAIS coletados (abordagem híbrida otimizada)
    total_issues = repo_info.get('total_issues', 0)
    closed_issues = repo_info.get('closed_issues', 0)
    
    # Calcular ratio com dados reais
    if total_issues > 0:
        closed_issues_ratio = closed_issues / total_issues
    else:
        closed_issues_ratio = 0
    
    return {
        'name': repo_data['name'],
        'owner': repo_data['owner']['login'],
        'url': repo_data['html_url'],
        'stars': repo_data['stargazers_count'],
        'age_days': age_days,
        'merged_prs': repo_info['merged_prs'],
        'total_releases': repo_info['total_releases'],
        'days_since_update': days_since_update,
        'primary_language': primary_language,
        'total_issues': total_issues,
        'closed_issues': closed_issues,
        'closed_issues_ratio': closed_issues_ratio,
        'forks': repo_data['forks_count'],
        'description': repo_data['description'] or ''
    }


def save_to_csv(repositories, filename):
    """Salva dados em arquivo CSV"""
    if not repositories:
        print("Nenhum dado para salvar")
        return
    
    fieldnames = [
        'name', 'owner', 'url', 'stars', 'age_days', 'merged_prs', 
        'total_releases', 'days_since_update', 'primary_language',
        'total_issues', 'closed_issues', 'closed_issues_ratio', 
        'forks', 'description'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(repositories)
    
    print(f"Dados salvos em CSV: {filename}")


def print_statistics(repositories):
    """Imprime estatísticas dos repositórios coletados"""
    if not repositories:
        return
    
    print(f"\n=== Estatísticas dos {len(repositories)} Repositórios ===")
    
    # Estatísticas básicas
    total_stars = sum(repo['stars'] for repo in repositories)
    avg_age = sum(repo['age_days'] for repo in repositories) / len(repositories)
    avg_prs = sum(repo['merged_prs'] for repo in repositories) / len(repositories)
    avg_releases = sum(repo['total_releases'] for repo in repositories) / len(repositories)
    avg_days_update = sum(repo['days_since_update'] for repo in repositories) / len(repositories)
    avg_closed_ratio = sum(repo['closed_issues_ratio'] for repo in repositories) / len(repositories)
    
    print(f"Total de estrelas: {total_stars:,}")
    print(f"Idade média: {avg_age:.1f} dias ({avg_age/365:.1f} anos)")
    print(f"PRs aceitas (média): {avg_prs:.1f}")
    print(f"Releases (média): {avg_releases:.1f}")
    print(f"Dias desde última atualização (média): {avg_days_update:.1f}")
    print(f"Taxa de issues fechadas (média): {avg_closed_ratio:.2%}")
    
    # Top 10 linguagens
    languages = {}
    for repo in repositories:
        lang = repo['primary_language']
        languages[lang] = languages.get(lang, 0) + 1
    
    print(f"\nTop 10 Linguagens:")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / len(repositories)) * 100
        print(f"  {lang}: {count} repositórios ({percentage:.1f}%)")
    
    # Top 10 repositórios por estrelas
    print(f"\nTop 10 Repositórios (por estrelas):")
    sorted_repos = sorted(repositories, key=lambda x: x['stars'], reverse=True)
    for i, repo in enumerate(sorted_repos[:10], 1):
        print(f"  {i:2d}. {repo['owner']}/{repo['name']} - {repo['stars']:,} stars")


def main():
    """Função principal COLETA COMPLETA - Lab01S02"""
    print("=== Lab01S02 - 1000 Repositórios COLETA COMPLETA ===")
    
    start_time = time.time()
    processed_repos = []
    
    try:
        # Etapa 1: Coletar repositórios (10 requisições)
        print("\nEtapa 1: Coletando lista de repositórios...")
        repositories = collect_repositories_graphql()
        
        if not repositories:
            print("Nenhum repositório foi coletado.")
            return
        
        step1_time = time.time()
        print(f"Lista coletada em {step1_time - start_time:.1f}s")
        
        # Etapa 2: Processar repositórios INSTANTANEAMENTE (dados já coletados via GraphQL)
        print(f"\nEtapa 2: Processando {len(repositories)} repositórios (DADOS REAIS INSTANTÂNEOS)...")
        
        for i, repo in enumerate(repositories, 1):
            try:
                if i % 50 == 0 or i <= 5 or i > len(repositories) - 5:
                    print(f"⚡ Processando #{i}/{len(repositories)}: {repo['full_name']}")
                
                # PROCESSAMENTO INSTANTÂNEO - dados reais já coletados via GraphQL
                repo_details = {
                    'repo_data': repo,
                    'merged_prs': repo.get('merged_prs_count', 0),  # DADOS REAIS
                    'total_releases': repo.get('total_releases', 0),  # DADOS REAIS
                    'closed_issues': repo.get('closed_issues_count', 0),  # DADOS REAIS
                    'total_issues': repo.get('open_issues_count', 0) + repo.get('closed_issues_count', 0),  # DADOS REAIS
                    'open_issues': repo.get('open_issues_count', 0),  # DADOS REAIS
                    'has_issues': repo.get('has_issues', False),
                    'has_projects': repo.get('has_projects', False),
                    'has_wiki': repo.get('has_wiki', False),
                    'has_pages': False,  # GraphQL não tem esse campo
                    'has_downloads': False  # GraphQL não tem esse campo
                }
                
                # Processar dados rapidamente
                processed_repo = process_repository_data(repo_details)
                processed_repos.append(processed_repo)
                
                if i % 50 == 0 or i <= 5 or i > len(repositories) - 5:
                    print(f"  ✅ PRs REAIS: {processed_repo['merged_prs']}, Issues REAIS: {processed_repo['closed_issues']}, Releases REAIS: {processed_repo['total_releases']}")
                    
            except Exception as e:
                print(f"Erro ao processar repositório #{i}: {e}")
                continue
                
            except Exception as e:
                print(f"Erro ao processar repositório #{i}: {e}")
                continue
        
        # Etapa 3: Salvar resultados finais
        print(f"\nSalvando resultados finais...")
        
        csv_file = 'data/repositorios_1000_completo.csv'
        save_to_csv(processed_repos, csv_file)
        
        json_file = 'data/repositorios_1000_completo.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(processed_repos, f, indent=2, ensure_ascii=False)
        
        # Estatísticas
        total_time = time.time() - start_time
        print_statistics(processed_repos)
        
        print(f"\n=== Lab01S02 Concluído ===")
        print(f"Tempo total: {total_time:.1f}s ({total_time/60:.1f} min)")
        print(f"Taxa média: {len(processed_repos)/total_time*60:.1f} repositórios/minuto")
        print(f"Total processado: {len(processed_repos)} repositórios")
        print(f"Arquivos gerados: {csv_file}, {json_file}")
        
    except KeyboardInterrupt:
        print(f"\nOperação cancelada pelo usuário.")
        if processed_repos:
            save_to_csv(processed_repos, 'data/repositorios_parcial.csv')
        
    except Exception as e:
        print(f"\nErro durante a execução: {e}")


if __name__ == "__main__":
    main()
