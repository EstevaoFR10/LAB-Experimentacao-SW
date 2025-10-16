"""
Lab 03 - Coleta Completa de Dados de Pull Requests
======================================================================
Este script executa todo o processo de coleta em uma única execução:
1. Busca repositórios no GitHub usando GraphQL
2. Coleta dados básicos de PRs (sem descrições)
3. Coleta descrições dos PRs usando GraphQL em batches
4. Gera dataset final completo com todas as métricas

Modos de execução:
- test: Poucos repositórios/PRs para testes rápidos
- production: Coleta completa (200 repos, 500 PRs cada)
"""

import os
import sys
import json
import csv
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
import pandas as pd

# Configura encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class GitHubPRCollector:
    def __init__(self, mode='test'):
        self.mode = mode
        self.github_token = self._load_github_token()
        
        # Configurações baseadas no modo
        if mode == 'test':
            self.max_repositories = 3
            self.max_prs_per_repo = 10
            self.min_prs = 10  # Critério mais baixo para test
            self.output_suffix = '_test'
        else:
            self.max_repositories = 200
            self.max_prs_per_repo = 500
            self.min_prs = 100
            self.output_suffix = '_production'
        
        # Headers para GraphQL
        self.graphql_headers = {
            'Authorization': f'bearer {self.github_token}',
            'Content-Type': 'application/json'
        }
        
        # Arquivos de saída
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.output_file = f'data/lab03_complete{self.output_suffix}_{timestamp}.csv'
        self.checkpoint_file = f'data/checkpoint{self.output_suffix}_{timestamp}.json'
        
        # Estado interno
        self.all_prs = []
        self.collected_descriptions = {}
        self.processed_repos = set()
        
        print(f"🚀 INICIANDO COLETA COMPLETA - MODO: {mode.upper()}")
        print(f"🎯 Objetivo: {self.max_repositories} repositórios, {self.max_prs_per_repo} PRs cada")
        print(f"📁 Arquivo de saída: {self.output_file}")
        print("=" * 60)
    
    def _load_github_token(self):
        """Carrega token do GitHub do arquivo config.env"""
        try:
            with open('config.env', 'r') as f:
                for line in f:
                    if line.startswith('GITHUB_TOKEN='):
                        return line.split('=')[1].strip().strip('"\'')
        except FileNotFoundError:
            print("❌ Arquivo config.env não encontrado!")
            sys.exit(1)
        
        print("❌ Token do GitHub não encontrado no config.env!")
        sys.exit(1)
    
    def search_repositories(self):
        """Fase 1: Busca repositórios populares usando GraphQL"""
        print("🔍 FASE 1: Buscando repositórios...")
        
        # Para modo test, usa repositórios conhecidos
        if self.mode == 'test':
            test_repos = ['facebook/react', 'microsoft/vscode', 'vuejs/vue']
            repositories = []
            for repo_name in test_repos[:self.max_repositories]:
                repositories.append({
                    'name': repo_name,
                    'stars': 50000,
                    'forks': 10000,
                    'language': 'JavaScript',
                    'pr_count': 1000
                })
                print(f"  ✅ {repo_name} (test repository)")
            print(f"📊 Usando {len(repositories)} repositórios de teste")
            return repositories
        
        repositories = []
        cursor = None
        
        while len(repositories) < self.max_repositories:
            stars_threshold = "1000" if self.mode == 'test' else "10000"
            query = f'''
            query {{
                search(query: "stars:>{stars_threshold} language:JavaScript OR language:Python OR language:Java OR language:TypeScript", 
                       type: REPOSITORY, first: 50{f', after: "{cursor}"' if cursor else ''}) {{
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
                    nodes {{
                        ... on Repository {{
                            nameWithOwner
                            stargazerCount
                            forkCount
                            primaryLanguage {{
                                name
                            }}
                            pullRequests(states: [MERGED, CLOSED]) {{
                                totalCount
                            }}
                        }}
                    }}
                }}
            }}
            '''
            
            response = requests.post(
                'https://api.github.com/graphql',
                headers=self.graphql_headers,
                json={'query': query},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Erro na busca de repositórios: {response.status_code}")
                break
            
            data = response.json()
            if 'errors' in data:
                print(f"❌ Erro GraphQL: {data['errors']}")
                break
            
            search_results = data['data']['search']
            
            for repo in search_results['nodes']:
                if len(repositories) >= self.max_repositories:
                    break
                
                pr_count = repo['pullRequests']['totalCount']
                if pr_count >= self.min_prs:
                    repositories.append({
                        'name': repo['nameWithOwner'],
                        'stars': repo['stargazerCount'],
                        'forks': repo['forkCount'],
                        'language': repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'Unknown',
                        'pr_count': pr_count
                    })
                    print(f"  ✅ {repo['nameWithOwner']} ({pr_count} PRs, {repo['stargazerCount']} stars)")
            
            if not search_results['pageInfo']['hasNextPage']:
                break
            
            cursor = search_results['pageInfo']['endCursor']
            time.sleep(1.0)  # Rate limiting
        
        print(f"📊 Encontrados {len(repositories)} repositórios válidos")
        return repositories
    
    def collect_pr_data(self, repositories):
        """Fase 2: Coleta dados básicos dos PRs"""
        print("\\n📥 FASE 2: Coletando dados dos PRs...")
        
        all_prs = []
        
        for i, repo in enumerate(repositories, 1):
            repo_name = repo['name']
            owner, name = repo_name.split('/')
            
            print(f"\\n📦 [{i}/{len(repositories)}] {repo_name}")
            
            # Busca PRs usando GraphQL
            pr_data = self._fetch_prs_graphql(owner, name)
            
            if not pr_data:
                print(f"  ⚠️ Nenhum PR encontrado")
                continue
            
            # Processa cada PR
            for pr in pr_data:
                try:
                    # Calcula métricas
                    created_at = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
                    
                    # Tempo até fechamento
                    if pr['closedAt']:
                        closed_at = datetime.fromisoformat(pr['closedAt'].replace('Z', '+00:00'))
                        time_to_close = int((closed_at - created_at).total_seconds() / 3600)
                    else:
                        time_to_close = None
                    
                    # Tempo até merge (se aplicável)
                    time_to_merge = None
                    if pr['mergedAt']:
                        merged_at = datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00'))
                        time_to_merge = int((merged_at - created_at).total_seconds() / 3600)
                    
                    # Conta participantes únicos
                    participants = set()
                    if pr['author']:
                        participants.add(pr['author']['login'])
                    
                    for comment in pr['comments']['nodes']:
                        if comment['author']:
                            participants.add(comment['author']['login'])
                    
                    for review in pr['reviews']['nodes']:
                        if review['author']:
                            participants.add(review['author']['login'])
                    
                    pr_record = {
                        'repository': repo_name,
                        'pr_number': pr['number'],
                        'title': pr['title'],
                        'status': 'MERGED' if pr['mergedAt'] else 'CLOSED',
                        'created_at': pr['createdAt'],
                        'closed_at': pr['closedAt'],
                        'merged_at': pr['mergedAt'],
                        'files_changed': pr['changedFiles'],
                        'additions': pr['additions'],
                        'deletions': pr['deletions'],
                        'total_changes': pr['additions'] + pr['deletions'],
                        'num_commits': pr.get('commits', {}).get('totalCount', 1),
                        'num_reviews': pr['reviews']['totalCount'],
                        'num_comments': pr['comments']['totalCount'],
                        'analysis_time_hours': time_to_close,
                        'author': pr['author']['login'] if pr['author'] else 'unknown',
                        'description_length': 0  # Será preenchido na fase 3
                    }
                    
                    all_prs.append(pr_record)
                    
                except Exception as e:
                    print(f"  ⚠️ Erro ao processar PR {pr.get('number', '?')}: {e}")
                    continue
            
            print(f"  ✅ {len([p for p in all_prs if p['repository'] == repo_name])} PRs coletados")
            
            # Rate limiting
            time.sleep(1.0)
        
        print(f"\\n📊 Total de PRs coletados: {len(all_prs)}")
        self.all_prs = all_prs
        return all_prs
    
    def _fetch_prs_graphql(self, owner, name):
        """Busca PRs de um repositório usando GraphQL com paginação"""
        prs = []
        cursor = None
        
        while len(prs) < self.max_prs_per_repo:
            query = f'''
            query {{
                repository(owner: "{owner}", name: "{name}") {{
                    pullRequests(
                        states: [MERGED, CLOSED]
                        first: {min(100, self.max_prs_per_repo - len(prs))}
                        {f'after: "{cursor}"' if cursor else ''}
                        orderBy: {{field: CREATED_AT, direction: DESC}}
                    ) {{
                        pageInfo {{
                            hasNextPage
                            endCursor
                        }}
                        nodes {{
                            number
                            title
                            createdAt
                            closedAt
                            mergedAt
                            additions
                            deletions
                            changedFiles
                            author {{
                                login
                            }}
                            comments(first: 100) {{
                                totalCount
                                nodes {{
                                    author {{
                                        login
                                    }}
                                }}
                            }}
                            reviews(first: 100) {{
                                totalCount
                                nodes {{
                                    author {{
                                        login
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            '''
            
            response = requests.post(
                'https://api.github.com/graphql',
                headers=self.graphql_headers,
                json={'query': query},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  ❌ Erro HTTP {response.status_code}")
                break
            
            data = response.json()
            if 'errors' in data:
                print(f"  ❌ Erro GraphQL: {data['errors']}")
                break
            
            if not data.get('data', {}).get('repository'):
                print(f"  ❌ Repositório não encontrado")
                break
            
            pull_requests = data['data']['repository']['pullRequests']
            
            # Filtra PRs válidos
            for pr in pull_requests['nodes']:
                # Verifica critérios de qualidade
                if (pr['comments']['totalCount'] >= 1 and 
                    pr['reviews']['totalCount'] >= 1 and
                    pr['createdAt'] and pr['closedAt']):
                    
                    # Verifica tempo mínimo de análise (1 hora)
                    created = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
                    closed = datetime.fromisoformat(pr['closedAt'].replace('Z', '+00:00'))
                    if (closed - created).total_seconds() >= 3600:  # 1 hora
                        prs.append(pr)
            
            if not pull_requests['pageInfo']['hasNextPage'] or len(prs) >= self.max_prs_per_repo:
                break
                
            cursor = pull_requests['pageInfo']['endCursor']
            time.sleep(0.5)  # Rate limiting interno
        
        return prs[:self.max_prs_per_repo]
    
    def collect_descriptions(self):
        """Fase 3: Coleta descrições dos PRs em batches otimizados"""
        print("\\n📝 FASE 3: Coletando descrições dos PRs...")
        
        # Agrupa PRs por repositório
        repos_prs = {}
        for pr in self.all_prs:
            repo = pr['repository']
            if repo not in repos_prs:
                repos_prs[repo] = []
            repos_prs[repo].append(pr['pr_number'])
        
        print(f"🎯 {len(repos_prs)} repositórios para processar descrições")
        
        # Processa cada repositório
        for i, (repo_name, pr_numbers) in enumerate(repos_prs.items(), 1):
            owner, name = repo_name.split('/')
            
            print(f"\\n📦 [{i}/{len(repos_prs)}] {repo_name} ({len(pr_numbers)} PRs)")
            
            # Processa em batches de 100 PRs
            batch_size = 100
            for batch_start in range(0, len(pr_numbers), batch_size):
                batch_end = min(batch_start + batch_size, len(pr_numbers))
                batch_prs = pr_numbers[batch_start:batch_end]
                
                print(f"      ✅ Batch {batch_start//batch_size + 1} - {len(batch_prs)} PRs")
                
                # Busca descrições via GraphQL
                descriptions = self._get_pr_descriptions_batch(owner, name, batch_prs)
                
                # Atualiza descrições coletadas
                self.collected_descriptions.update(descriptions)
                
                time.sleep(1.0)  # Rate limiting
        
        # Atualiza PRs com descrições
        for pr in self.all_prs:
            pr_id = pr['pr_number']
            if pr_id in self.collected_descriptions:
                pr['description_length'] = self.collected_descriptions[pr_id]
        
        print(f"\\n✅ Descrições coletadas: {len(self.collected_descriptions)}")
    
    def _get_pr_descriptions_batch(self, owner, name, pr_numbers):
        """Busca descrições de múltiplos PRs em uma única query GraphQL"""
        descriptions = {}
        
        # Constrói query para múltiplos PRs
        pr_queries = []
        for i, pr_num in enumerate(pr_numbers):
            pr_queries.append(f'''
                pr{i}: pullRequest(number: {pr_num}) {{
                    number
                    body
                }}
            ''')
        
        query = f'''
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                {chr(10).join(pr_queries)}
            }}
        }}
        '''
        
        for attempt in range(3):  # Retry logic
            try:
                response = requests.post(
                    'https://api.github.com/graphql',
                    headers=self.graphql_headers,
                    json={'query': query},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data']['repository']:
                        repo_data = data['data']['repository']
                        
                        for key, pr_data in repo_data.items():
                            if key.startswith('pr') and pr_data:
                                pr_number = pr_data['number']
                                body = pr_data['body'] or ''
                                descriptions[pr_number] = len(body)
                        
                        return descriptions
                
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Backoff
            
            except Exception as e:
                print(f"        ⚠️ Erro na tentativa {attempt + 1}: {e}")
                if attempt < 2:
                    time.sleep(2)
        
        # Se falhou, retorna descrições vazias
        for pr_num in pr_numbers:
            descriptions[pr_num] = 0
        
        return descriptions
    
    def save_final_dataset(self):
        """Fase 4: Salva dataset final completo"""
        print("\\n💾 FASE 4: Salvando dataset final...")
        
        # Cria diretório se não existe
        os.makedirs('data', exist_ok=True)
        
        # Garante ordem das colunas igual ao dataset original
        columns = [
            'repository', 'pr_number', 'title', 'status', 'created_at', 
            'closed_at', 'merged_at', 'files_changed', 'additions', 
            'deletions', 'total_changes', 'num_commits', 'num_reviews', 
            'num_comments', 'analysis_time_hours', 'author', 'description_length'
        ]
        
        # Salva CSV final
        df = pd.DataFrame(self.all_prs)
        df = df[columns]  # Reordena colunas
        df.to_csv(self.output_file, index=False, encoding='utf-8')
        
        print(f"✅ Dataset salvo: {self.output_file}")
        print(f"📊 Total de registros: {len(df)}")
        print(f"📁 Repositórios únicos: {df['repository'].nunique()}")
        print(f"🔢 Colunas: {len(df.columns)} (compatível com dataset original)")
        
        # Estatísticas básicas
        print("\\n📈 ESTATÍSTICAS FINAIS:")
        print(f"   • PRs MERGED: {len(df[df['status'] == 'MERGED'])}")
        print(f"   • PRs CLOSED: {len(df[df['status'] == 'CLOSED'])}")
        print(f"   • Descrições coletadas: {len(df[df['description_length'] > 0])}")
        print(f"   • Tempo médio análise: {df['analysis_time_hours'].mean():.1f}h")
        print(f"   • Mudanças médias: {df['total_changes'].mean():.0f} linhas")
        
        return self.output_file
    
    def run_complete_collection(self):
        """Executa todo o processo de coleta"""
        start_time = time.time()
        
        try:
            # Fase 1: Buscar repositórios
            repositories = self.search_repositories()
            
            if not repositories:
                print("❌ Nenhum repositório encontrado!")
                return None
            
            # Fase 2: Coletar dados dos PRs
            self.collect_pr_data(repositories)
            
            if not self.all_prs:
                print("❌ Nenhum PR coletado!")
                return None
            
            # Fase 3: Coletar descrições
            self.collect_descriptions()
            
            # Fase 4: Salvar dataset final
            output_file = self.save_final_dataset()
            
            # Tempo total
            total_time = time.time() - start_time
            print(f"\\n🏁 COLETA COMPLETA FINALIZADA!")
            print(f"⏱️ Tempo total: {total_time/60:.1f} minutos")
            print(f"📁 Arquivo gerado: {output_file}")
            
            return output_file
            
        except KeyboardInterrupt:
            print("\\n⚠️ Coleta interrompida pelo usuário")
            return None
        except Exception as e:
            print(f"\\n❌ Erro durante a coleta: {e}")
            return None

def main():
    """Função principal"""
    print("🔬 LAB 03 - COLETA COMPLETA DE DADOS DE PULL REQUESTS")
    print("=" * 60)
    
    # Pergunta o modo de execução
    print("Escolha o modo de execução:")
    print("1. test - Coleta rápida para testes (3 repos, 10 PRs cada)")
    print("2. production - Coleta completa (200 repos, 500 PRs cada)")
    
    choice = input("\\nDigite sua escolha (1 ou 2): ").strip()
    
    if choice == '1':
        mode = 'test'
    elif choice == '2':
        mode = 'production'
    else:
        print("❌ Escolha inválida! Usando modo test por padrão.")
        mode = 'test'
    
    # Confirma execução
    collector = GitHubPRCollector(mode=mode)
    print(f"\\n⚠️ Modo {mode.upper()} selecionado!")
    
    if mode == 'production':
        confirm = input("⚠️ Modo production pode levar horas. Confirma? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Execução cancelada.")
            return
    
    # Executa coleta
    output_file = collector.run_complete_collection()
    
    if output_file:
        print(f"\\n🎉 SUCESSO! Dataset completo gerado: {output_file}")
    else:
        print("\\n❌ Falha na coleta de dados.")

if __name__ == "__main__":
    main()