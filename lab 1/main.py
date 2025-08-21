#!/usr/bin/env python3
"""
Lab01S02 - REST API para 1.000 repositórios populares com paginação ULTRA OTIMIZADA
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


def make_github_rest_request(url, params=None):
    """Faz requisição para GitHub API com rate limiting mínimo"""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Lab01S02-Research"
    }
    
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read().decode('utf-8')
            result = json.loads(data)
            
        # Rate limiting mínimo
        time.sleep(0.05)  # 50ms apenas
        
        return result
        
    except urllib.error.HTTPError as e:
        if e.code == 403:  # Rate limit
            print("Rate limit atingido, aguardando 30s...")
            time.sleep(30)
            return make_github_rest_request(url, params)
        print(f"Erro HTTP {e.code}: {e.reason}")
        raise
    except urllib.error.URLError as e:
        print(f"Erro de URL: {e.reason}")
        raise


def make_fast_request(url, headers, params=None):
    """Requisição ultra rápida sem sleep"""
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


def collect_1000_repositories():
    """Coleta 1.000 repositórios usando paginação otimizada"""
    all_repositories = []
    per_page = 100
    total_needed = 1000
    
    print(f"Coletando {total_needed} repositórios...")
    
    total_pages = (total_needed + per_page - 1) // per_page
    
    for page in range(1, total_pages + 1):
        print(f"Página {page}/{total_pages}... (Total: {len(all_repositories)})")
        
        try:
            base_url = "https://api.github.com/search/repositories"
            params = {
                "q": "stars:>1",
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page
            }
            
            search_results = make_github_rest_request(base_url, params)
            
            if 'items' not in search_results:
                print(f"Erro na página {page}")
                break
            
            repositories = search_results['items']
            all_repositories.extend(repositories)
            
            if len(all_repositories) >= total_needed:
                break
                
        except Exception as e:
            print(f"Erro página {page}: {e}")
            break
    
    return all_repositories[:total_needed]


def get_all_counts_batch(owner, repo_name):
    """Faz todas as contagens de uma vez usando Search API"""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Lab01S02-Research"
    }
    
    search_url = "https://api.github.com/search/issues"
    
    # Fazer 3 requisições em sequência rápida
    queries = [
        (f"repo:{owner}/{repo_name} type:pr is:merged", 'merged_prs'),
        (f"repo:{owner}/{repo_name} type:issue is:closed", 'closed_issues'),
        (f"repo:{owner}/{repo_name} type:issue", 'total_issues')
    ]
    
    results = {}
    
    for query, key in queries:
        params = {"q": query, "per_page": 1}
        data, status, _ = make_fast_request(search_url, headers, params)
        results[key] = data.get('total_count', 0) if status == 200 and data else 0
    
    return results


def get_releases_fast(owner, repo_name):
    """Conta releases de forma super otimizada"""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Lab01S02-Research"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"
    params = {"per_page": 100}
    
    data, status, response_headers = make_fast_request(url, headers, params)
    
    if status != 200:
        return 0
    
    # Verificar paginação no header Link
    link_header = response_headers.get('Link', '')
    if 'rel="last"' in link_header:
        match = re.search(r'page=(\d+)[^>]*>;\s*rel="last"', link_header)
        if match:
            return int(match.group(1)) * 100
    
    return len(data) if data else 0


def get_repository_details_ultra_fast(owner, repo_name):
    """Versão ultra otimizada - coleta tudo com mínimas requisições"""
    # 1. Dados básicos (obrigatório)
    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    repo_data = make_github_rest_request(repo_url)
    
    # 2. Todas as contagens via Search API (3 requisições rápidas)
    counts = get_all_counts_batch(owner, repo_name)
    
    # 3. Releases (1 requisição)
    total_releases = get_releases_fast(owner, repo_name)
    
    return {
        'repo_data': repo_data,
        'merged_prs': counts.get('merged_prs', 0),
        'total_releases': total_releases,
        'closed_issues': counts.get('closed_issues', 0),
        'total_issues_from_search': counts.get('total_issues', 0)
    }


def process_repository_data(repo_info):
    """Processa dados do repositório"""
    repo_data = repo_info['repo_data']
    now_utc = datetime.now(timezone.utc)
    
    # Calcular métricas de tempo
    created_at = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
    age_days = (now_utc - created_at).days
    
    updated_at = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
    days_since_update = max(0, (now_utc - updated_at).days)
    
    primary_language = repo_data['language'] or 'Unknown'
    
    # Usar dados do Search API
    total_issues = repo_info['total_issues_from_search']
    closed_issues = repo_info['closed_issues']
    closed_issues_ratio = closed_issues / total_issues if total_issues > 0 else 0
    
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
    """Função principal ULTRA OTIMIZADA - Lab01S02"""
    print("=== Lab01S02 - 1.000 Repositórios ULTRA OTIMIZADO ===")
    print("Coleta rápida dos 1.000 repositórios mais populares...")
    
    start_time = time.time()
    processed_repos = []
    
    try:
        # Etapa 1: Coletar repositórios (10 requisições)
        print("\nEtapa 1: Coletando lista de repositórios...")
        repositories = collect_1000_repositories()
        
        if not repositories:
            print("Nenhum repositório foi coletado.")
            return
        
        step1_time = time.time()
        print(f"Lista coletada em {step1_time - start_time:.1f}s")
        
        # Etapa 2: Processar repositórios em lotes
        print(f"\nEtapa 2: Processando {len(repositories)} repositórios...")
        
        for i, repo in enumerate(repositories, 1):
            try:
                # Log menos verboso
                if i % 10 == 0 or i <= 10:
                    print(f"Processando {i}/{len(repositories)}: {repo['owner']['login']}/{repo['name']}")
                
                # Processar com função ultra otimizada (5 requisições por repo)
                repo_details = get_repository_details_ultra_fast(repo['owner']['login'], repo['name'])
                processed_repo = process_repository_data(repo_details)
                processed_repos.append(processed_repo)
                
                # Backup menos frequente
                if i % 200 == 0:
                    elapsed = time.time() - start_time
                    rate = i / elapsed * 60
                    print(f"Progresso: {i}/{len(repositories)} ({rate:.1f} repos/min)")
                    
                    backup_csv = f'data/backup_{i}.csv'
                    save_to_csv(processed_repos, backup_csv)
                
            except Exception as e:
                print(f"Erro no repo {i}: {e}")
                continue
        
        # Etapa 3: Salvar resultados finais
        print(f"\nSalvando resultados finais...")
        
        csv_file = 'data/repositorios_1000.csv'
        save_to_csv(processed_repos, csv_file)
        
        json_file = 'data/repositorios_1000.json'
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
