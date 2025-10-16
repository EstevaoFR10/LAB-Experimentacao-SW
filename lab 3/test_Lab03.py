"""
Script Teste Completo - Lab 03
===============================
Versão corrigida com todas as métricas do dataset original
"""

import os
import sys
import json
import time
from datetime import datetime
import requests
import pandas as pd

def load_github_token():
    """Carrega token do GitHub"""
    try:
        with open('config.env', 'r') as f:
            for line in f:
                if line.startswith('GITHUB_TOKEN='):
                    return line.split('=')[1].strip().strip('"\'')
    except:
        print("❌ Erro ao carregar token")
        return None

def test_collection_complete():
    """Teste completo com todas as métricas necessárias"""
    print("🔬 TESTE COMPLETO DO SCRIPT UNIFICADO")
    print("=" * 45)
    
    # Carrega token
    token = load_github_token()
    if not token:
        print("❌ Token não encontrado!")
        return
    
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Repositórios de teste
    test_repos = ['facebook/react', 'microsoft/vscode', 'vuejs/vue']
    all_data = []
    
    for i, repo_name in enumerate(test_repos, 1):
        owner, name = repo_name.split('/')
        print(f"\\n📦 [{i}] {repo_name}")
        
        # Query GraphQL mais completa
        query = f'''
        query {{
            repository(owner: "{owner}", name: "{name}") {{
                pullRequests(states: [MERGED, CLOSED], first: 5, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
                    nodes {{
                        number
                        title
                        body
                        createdAt
                        closedAt
                        mergedAt
                        additions
                        deletions
                        changedFiles
                        author {{
                            login
                        }}
                        commits {{
                            totalCount
                        }}
                        comments {{ 
                            totalCount 
                        }}
                        reviews {{ 
                            totalCount 
                        }}
                    }}
                }}
            }}
        }}
        '''
        
        try:
            response = requests.post(
                'https://api.github.com/graphql',
                headers=headers,
                json={'query': query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']['repository']:
                    prs = data['data']['repository']['pullRequests']['nodes']
                    
                    for pr in prs:
                        # Filtra PRs válidos (com comentários/reviews e tempo mínimo)
                        if (pr['comments']['totalCount'] >= 1 and 
                            pr['reviews']['totalCount'] >= 1 and
                            pr['createdAt'] and pr['closedAt']):
                            
                            # Calcula tempo de análise em horas
                            created_at = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
                            closed_at = datetime.fromisoformat(pr['closedAt'].replace('Z', '+00:00'))
                            analysis_time_hours = (closed_at - created_at).total_seconds() / 3600
                            
                            # Verifica tempo mínimo (1 hora)
                            if analysis_time_hours >= 1.0:
                                pr_data = {
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
                                    'num_commits': pr['commits']['totalCount'],
                                    'num_reviews': pr['reviews']['totalCount'],
                                    'num_comments': pr['comments']['totalCount'],
                                    'analysis_time_hours': round(analysis_time_hours, 2),
                                    'author': pr['author']['login'] if pr['author'] else 'unknown',
                                    'description_length': len(pr['body'] or '')
                                }
                                all_data.append(pr_data)
                    
                    valid_prs = len([p for p in all_data if p['repository'] == repo_name])
                    print(f"  ✅ Coletados {valid_prs} PRs válidos (com reviews >= 1, comments >= 1, tempo >= 1h)")
                else:
                    print(f"  ❌ Erro nos dados: {data}")
            else:
                print(f"  ❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
        
        time.sleep(1)  # Rate limiting
    
    # Salva resultado
    if all_data:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'data/lab03_complete_test_{timestamp}.csv'
        
        df = pd.DataFrame(all_data)
        
        # Reordena colunas conforme dataset original
        columns_order = [
            'repository', 'pr_number', 'title', 'status', 'created_at', 'closed_at', 
            'merged_at', 'files_changed', 'additions', 'deletions', 'total_changes',
            'num_commits', 'num_reviews', 'num_comments', 'analysis_time_hours', 
            'author', 'description_length'
        ]
        
        df = df[columns_order]
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"\\n✅ TESTE COMPLETO CONCLUÍDO!")
        print(f"📁 Arquivo: {output_file}")
        print(f"📊 Total PRs válidos: {len(df)}")
        print(f"📈 Repositórios: {df['repository'].nunique()}")
        
        # Estatísticas detalhadas
        print(f"\\n📋 ESTATÍSTICAS:")
        print(f"   • PRs MERGED: {len(df[df['status'] == 'MERGED'])}")
        print(f"   • PRs CLOSED: {len(df[df['status'] == 'CLOSED'])}")
        print(f"   • Tempo médio análise: {df['analysis_time_hours'].mean():.1f}h")
        print(f"   • Reviews médias: {df['num_reviews'].mean():.1f}")
        print(f"   • Comments médios: {df['num_comments'].mean():.1f}")
        print(f"   • Descrições com texto: {len(df[df['description_length'] > 0])}")
        
        # Mostra amostra
        print("\\n📋 AMOSTRA DOS DADOS:")
        for _, row in df.head(3).iterrows():
            print(f"   • {row['repository']} PR#{row['pr_number']}: {row['title'][:50]}...")
            print(f"     Status: {row['status']}, Reviews: {row['num_reviews']}, Comments: {row['num_comments']}, Tempo: {row['analysis_time_hours']:.1f}h")
        
        # Verificação de compatibilidade
        print(f"\\n🔍 VERIFICAÇÃO DE COMPATIBILIDADE:")
        print(f"   • Colunas esperadas: 17")
        print(f"   • Colunas geradas: {len(df.columns)}")
        print(f"   • Estrutura compatível: {'✅' if len(df.columns) == 17 else '❌'}")
        
        return output_file
    else:
        print("\\n❌ Nenhum dado válido coletado!")
        return None

if __name__ == "__main__":
    test_collection_complete()