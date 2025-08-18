#!/usr/bin/env python3
"""
Lab01S01 - REST API para 100 repositórios populares (SOMENTE BIBLIOTECA PADRÃO)
Laboratório de Experimentação de Software - PUC Minas
"""

import urllib.request
import urllib.parse
import json
import time
from datetime import datetime, timezone
from config import GITHUB_TOKEN


def make_github_rest_request(url, params=None):
    """Faz requisição para GitHub API com rate limiting"""
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Lab01S01-Research"
    }
    
    # Construir URL com parâmetros
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    
    print(f"Fazendo requisição REST: {url}")
    
    # Criar requisição com headers
    req = urllib.request.Request(url, headers=headers)
    
    try:
        # Fazer requisição
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read().decode('utf-8')
            result = json.loads(data)
            
        # Sleep para respeitar rate limits
        print("Aguardando 1.5s para respeitar rate limit...")
        time.sleep(1.5)
        
        return result
        
    except urllib.error.HTTPError as e:
        print(f"Erro HTTP {e.code}: {e.reason}")
        raise
    except urllib.error.URLError as e:
        print(f"Erro de URL: {e.reason}")
        raise


def make_simple_request(url, headers, params=None):
    """Requisição HTTP simples sem rate limiting"""
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode('utf-8')
            return json.loads(data), response.status, dict(response.headers)
    except urllib.error.HTTPError as e:
        return None, e.code, {}
    except Exception:
        return None, 0, {}


def get_repository_details(owner, repo_name):
    """Coleta dados completos do repositório"""
    # URL base para o repositório
    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    
    # Dados básicos do repositório
    repo_data = make_github_rest_request(repo_url)
    
    # Headers para requisições auxiliares
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Lab01S01-Research"
    }
    
    # PRs fechadas usando Search API
    search_url = "https://api.github.com/search/issues"
    prs_params = {
        "q": f"repo:{owner}/{repo_name} type:pr state:closed",
        "per_page": 1
    }
    prs_data, prs_status, _ = make_simple_request(search_url, headers, prs_params)
    merged_prs = 0
    if prs_status == 200 and prs_data:
        merged_prs = prs_data.get('total_count', 0)
    
    # Contagem de releases
    releases_url = f"{repo_url}/releases"
    releases_params = {"per_page": 100}  # Pegar mais releases por página
    releases_data, releases_status, releases_headers = make_simple_request(releases_url, headers, releases_params)
    total_releases = 0
    if releases_status == 200:
        # Verificar paginação via header Link
        if 'Link' in releases_headers:
            link_header = releases_headers['Link']
            if 'last' in link_header:
                import re
                last_page_match = re.search(r'page=(\d+)>; rel="last"', link_header)
                if last_page_match:
                    # Total aproximado = última página * itens por página
                    last_page = int(last_page_match.group(1))
                    total_releases = last_page * 100  # Estimativa conservadora
        else:
            # Sem paginação: conta releases na página atual
            if releases_data:
                total_releases = len(releases_data)
    
    # Issues fechadas usando Search API
    closed_params = {
        "q": f"repo:{owner}/{repo_name} type:issue state:closed",
        "per_page": 1
    }
    
    search_data, search_status, _ = make_simple_request(search_url, headers, closed_params)
    closed_issues = 0
    if search_status == 200 and search_data:
        closed_issues = search_data.get('total_count', 0)
    
    return {
        'repo_data': repo_data,
        'merged_prs': merged_prs,
        'total_releases': total_releases,
        'closed_issues': closed_issues
    }


def process_repository_data(repo_info):
    """Processa dados do repositório e calcula métricas"""
    repo_data = repo_info['repo_data']
    now_utc = datetime.now(timezone.utc)
    
    # Calcular idade do repositório
    created_at = datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00'))
    age_days = (now_utc - created_at).days
    
    # Dias desde última atualização
    updated_at = datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00'))
    days_since_update = max(0, (now_utc - updated_at).days)
    
    # Linguagem primária
    primary_language = repo_data['language'] or 'Unknown'
    
    # Cálculo de issues fechadas
    total_issues = repo_data['open_issues_count']  # Issues abertas
    closed_issues = repo_info['closed_issues']     # Issues fechadas
    total_all_issues = total_issues + closed_issues
    closed_issues_ratio = closed_issues / total_all_issues if total_all_issues > 0 else 0
    
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
        'total_issues': total_all_issues,
        'closed_issues': closed_issues,
        'closed_issues_ratio': closed_issues_ratio,
        'forks': repo_data['forks_count'],
        'description': repo_data['description'] or ''
    }


def main():
    """Função principal - coleta e analisa repositórios"""
    print("=== Lab01S01 - Repositórios Populares do GitHub (REST API) ===")
    print("Coletando os 100 repositórios mais populares...\n")
    
    processed_repos = []
    
    try:
        # Buscar repositórios populares
        base_url = "https://api.github.com/search/repositories"
        params = {
            "q": "stars:>1",
            "sort": "stars",
            "order": "desc",
            "per_page": 100
        }
        
        print("Buscando repositórios mais populares...")
        search_results = make_github_rest_request(base_url, params)
        repositories = search_results['items']
        
        if not repositories:
            print("Nenhum repositório foi coletado.")
            return
        
        print(f"Encontrados {len(repositories)} repositórios. Coletando detalhes...\n")
        
        # Processar cada repositório
        for i, repo in enumerate(repositories, 1):
            try:
                print(f"Coletando detalhes do repositório #{i}: {repo['owner']['login']}/{repo['name']}")
                
                # Buscar detalhes do repositório
                repo_details = get_repository_details(repo['owner']['login'], repo['name'])
                
                # Processar dados
                processed_repo = process_repository_data(repo_details)
                processed_repos.append(processed_repo)
                
                print(f"  → {processed_repo['owner']}/{processed_repo['name']} - {processed_repo['stars']:,} stars")
                
                # Salvar dados
                output_file = 'data/repositorios_dados.json'
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(processed_repos, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                print(f"  → Erro ao processar repositório #{i}: {e}")
                continue
        
        print(f"\nDados salvos em: {output_file}")
        
        # Estatísticas finais
        if processed_repos:
            total_stars = sum(repo['stars'] for repo in processed_repos)
            avg_age = sum(repo['age_days'] for repo in processed_repos) / len(processed_repos)
            
            # Contar linguagens
            languages = {}
            for repo in processed_repos:
                lang = repo['primary_language']
                languages[lang] = languages.get(lang, 0) + 1
            
            print(f"\n=== Estatísticas Finais ===")
            print(f"Total de repositórios coletados: {len(processed_repos)}")
            print(f"Total de estrelas: {total_stars:,}")
            print(f"Idade média: {avg_age:.1f} dias ({avg_age/365:.1f} anos)")
            print(f"Linguagens mais populares:")
            for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]:
                percentage = (count / len(processed_repos)) * 100
                print(f"  {lang}: {count} repositórios ({percentage:.1f}%)")
        
        print(f"\n=== Coleta Concluída ===")
        print(f"Total coletado: {len(processed_repos)} repositórios")
        
    except KeyboardInterrupt:
        print(f"\nOperação cancelada pelo usuário.")
        print(f"Repositórios coletados até agora: {len(processed_repos)}")
        
    except Exception as e:
        print(f"\nErro durante a execução: {e}")
        print("Verifique sua conexão com a internet e o token do GitHub.")


if __name__ == "__main__":
    main()
