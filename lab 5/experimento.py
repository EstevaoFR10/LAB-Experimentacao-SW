"""
Lab 05 - GraphQL vs REST - Experimento Controlado
Sprint 1: Preparação do Experimento

Este script prepara e executa o experimento para comparar APIs GraphQL e REST
"""

import requests
import time
import json
import csv
import random
from datetime import datetime
import statistics

# Configurações
GITHUB_TOKEN = "SEU_TOKEN_AQUI"  # Token do GitHub
HEADERS_REST = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
HEADERS_GRAPHQL = {
    "Authorization": f"bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

REST_BASE_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

# Número de repetições por consulta
REPETICOES = 30
DELAY_ENTRE_REQUESTS = 1  # segundos

class ExperimentoAPI:
    """Classe para executar o experimento comparativo entre GraphQL e REST"""
    
    def __init__(self):
        self.resultados = []
    
    def medir_tempo_tamanho(self, funcao_request):
        """
        Executa uma requisição e mede tempo de resposta e tamanho
        
        Returns:
            tuple: (tempo_ms, tamanho_bytes, sucesso, dados)
        """
        try:
            inicio = time.time()
            resposta = funcao_request()
            fim = time.time()
            
            tempo_ms = (fim - inicio) * 1000  # Converter para milissegundos
            tamanho_bytes = len(resposta.content)
            
            return tempo_ms, tamanho_bytes, True, resposta.json()
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None, None, False, None
    
    # ========== CONSULTA 1: SIMPLES - Informações básicas de um repositório ==========
    
    def consulta1_rest(self, owner="torvalds", repo="linux"):
        """REST: Buscar informações básicas de um repositório"""
        url = f"{REST_BASE_URL}/repos/{owner}/{repo}"
        return requests.get(url, headers=HEADERS_REST)
    
    def consulta1_graphql(self, owner="torvalds", repo="linux"):
        """GraphQL: Buscar informações básicas de um repositório"""
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            name
            description
            stargazerCount
            forkCount
            createdAt
            updatedAt
          }
        }
        """
        variables = {"owner": owner, "repo": repo}
        payload = {"query": query, "variables": variables}
        return requests.post(GRAPHQL_URL, headers=HEADERS_GRAPHQL, json=payload)
    
    # ========== CONSULTA 2: MÉDIA - Repositório com issues ==========
    
    def consulta2_rest(self, owner="facebook", repo="react"):
        """REST: Buscar repositório e suas issues (requer múltiplas requisições)"""
        # Primeira requisição: dados do repo
        repo_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}", 
            headers=HEADERS_REST
        )
        # Segunda requisição: issues
        issues_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}/issues?per_page=10&state=all",
            headers=HEADERS_REST
        )
        # Combinar resultados
        combined_data = {
            "repository": repo_response.json(),
            "issues": issues_response.json()
        }
        # Criar objeto de resposta simulado
        class CombinedResponse:
            def __init__(self, data):
                self.content = json.dumps(data).encode('utf-8')
                self._json = data
            def json(self):
                return self._json
        
        return CombinedResponse(combined_data)
    
    def consulta2_graphql(self, owner="facebook", repo="react"):
        """GraphQL: Buscar repositório e suas issues (uma única requisição)"""
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            name
            description
            stargazerCount
            issues(first: 10) {
              nodes {
                title
                state
                createdAt
                author {
                  login
                }
              }
            }
          }
        }
        """
        variables = {"owner": owner, "repo": repo}
        payload = {"query": query, "variables": variables}
        return requests.post(GRAPHQL_URL, headers=HEADERS_GRAPHQL, json=payload)
    
    # ========== CONSULTA 3: COMPLEXA - Repositório com issues, PRs e contributors ==========
    
    def consulta3_rest(self, owner="microsoft", repo="vscode"):
        """REST: Dados complexos (múltiplas requisições)"""
        repo_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}",
            headers=HEADERS_REST
        )
        issues_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}/issues?per_page=5",
            headers=HEADERS_REST
        )
        pulls_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}/pulls?per_page=5",
            headers=HEADERS_REST
        )
        contributors_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}/contributors?per_page=5",
            headers=HEADERS_REST
        )
        
        combined_data = {
            "repository": repo_response.json(),
            "issues": issues_response.json(),
            "pulls": pulls_response.json(),
            "contributors": contributors_response.json()
        }
        
        class CombinedResponse:
            def __init__(self, data):
                self.content = json.dumps(data).encode('utf-8')
                self._json = data
            def json(self):
                return self._json
        
        return CombinedResponse(combined_data)
    
    def consulta3_graphql(self, owner="microsoft", repo="vscode"):
        """GraphQL: Dados complexos (uma única requisição)"""
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            name
            description
            stargazerCount
            issues(first: 5) {
              nodes {
                title
                state
              }
            }
            pullRequests(first: 5) {
              nodes {
                title
                state
              }
            }
            mentionableUsers(first: 5) {
              nodes {
                login
                name
              }
            }
          }
        }
        """
        variables = {"owner": owner, "repo": repo}
        payload = {"query": query, "variables": variables}
        return requests.post(GRAPHQL_URL, headers=HEADERS_GRAPHQL, json=payload)
    
    # ========== CONSULTA 4: LISTA - Múltiplos repositórios ==========
    
    def consulta4_rest(self, user="google"):
        """REST: Buscar repositórios de uma organização"""
        url = f"{REST_BASE_URL}/orgs/{user}/repos?per_page=10"
        return requests.get(url, headers=HEADERS_REST)
    
    def consulta4_graphql(self, user="google"):
        """GraphQL: Buscar repositórios de uma organização"""
        query = """
        query($user: String!) {
          organization(login: $user) {
            repositories(first: 10) {
              nodes {
                name
                description
                stargazerCount
              }
            }
          }
        }
        """
        variables = {"user": user}
        payload = {"query": query, "variables": variables}
        return requests.post(GRAPHQL_URL, headers=HEADERS_GRAPHQL, json=payload)
    
    # ========== CONSULTA 5: ANINHADA - Dados com múltiplos níveis ==========
    
    def consulta5_rest(self, owner="nodejs", repo="node"):
        """REST: Repositório com commits recentes e seus autores"""
        repo_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}",
            headers=HEADERS_REST
        )
        commits_response = requests.get(
            f"{REST_BASE_URL}/repos/{owner}/{repo}/commits?per_page=5",
            headers=HEADERS_REST
        )
        
        combined_data = {
            "repository": repo_response.json(),
            "commits": commits_response.json()
        }
        
        class CombinedResponse:
            def __init__(self, data):
                self.content = json.dumps(data).encode('utf-8')
                self._json = data
            def json(self):
                return self._json
        
        return CombinedResponse(combined_data)
    
    def consulta5_graphql(self, owner="nodejs", repo="node"):
        """GraphQL: Repositório com commits recentes e seus autores"""
        query = """
        query($owner: String!, $repo: String!) {
          repository(owner: $owner, name: $repo) {
            name
            description
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 5) {
                    nodes {
                      message
                      author {
                        name
                        email
                        date
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {"owner": owner, "repo": repo}
        payload = {"query": query, "variables": variables}
        return requests.post(GRAPHQL_URL, headers=HEADERS_GRAPHQL, json=payload)
    
    def executar_consulta(self, nome_consulta, func_rest, func_graphql, repeticoes=REPETICOES):
        """
        Executa uma consulta múltiplas vezes alternando entre REST e GraphQL
        """
        print(f"\n{'='*60}")
        print(f"Executando: {nome_consulta}")
        print(f"{'='*60}")
        
        # Lista para alternar de forma aleatória
        ordem = ['REST', 'GraphQL'] * repeticoes
        random.shuffle(ordem)
        
        for i, tipo in enumerate(ordem):
            print(f"Medição {i+1}/{len(ordem)} - {tipo}...", end=" ")
            
            if tipo == 'REST':
                tempo, tamanho, sucesso, dados = self.medir_tempo_tamanho(func_rest)
            else:
                tempo, tamanho, sucesso, dados = self.medir_tempo_tamanho(func_graphql)
            
            if sucesso:
                self.resultados.append({
                    'consulta': nome_consulta,
                    'tipo_api': tipo,
                    'tempo_ms': tempo,
                    'tamanho_bytes': tamanho,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"✓ Tempo: {tempo:.2f}ms, Tamanho: {tamanho} bytes")
            else:
                print("✗ Falha")
            
            # Delay para evitar rate limiting
            time.sleep(DELAY_ENTRE_REQUESTS)
    
    def executar_experimento_completo(self):
        """Executa todas as consultas do experimento"""
        print("="*60)
        print("INICIANDO EXPERIMENTO: GraphQL vs REST")
        print("="*60)
        print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Repetições por consulta: {REPETICOES}")
        print(f"Total de medições: {5 * 2 * REPETICOES}")
        
        # Executar cada tipo de consulta
        self.executar_consulta("Consulta 1 - Simples", self.consulta1_rest, self.consulta1_graphql)
        self.executar_consulta("Consulta 2 - Média", self.consulta2_rest, self.consulta2_graphql)
        self.executar_consulta("Consulta 3 - Complexa", self.consulta3_rest, self.consulta3_graphql)
        self.executar_consulta("Consulta 4 - Lista", self.consulta4_rest, self.consulta4_graphql)
        self.executar_consulta("Consulta 5 - Aninhada", self.consulta5_rest, self.consulta5_graphql)
        
        print(f"\n{'='*60}")
        print("EXPERIMENTO CONCLUÍDO!")
        print(f"{'='*60}")
    
    def salvar_resultados(self, arquivo='resultados_experimento.csv'):
        """Salva os resultados em arquivo CSV"""
        if not self.resultados:
            print("Nenhum resultado para salvar.")
            return
        
        with open(arquivo, 'w', newline='', encoding='utf-8') as f:
            campos = ['consulta', 'tipo_api', 'tempo_ms', 'tamanho_bytes', 'timestamp']
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            writer.writerows(self.resultados)
        
        print(f"\nResultados salvos em: {arquivo}")
        self.gerar_estatisticas_preliminares()
    
    def gerar_estatisticas_preliminares(self):
        """Gera estatísticas preliminares dos resultados"""
        print("\n" + "="*60)
        print("ESTATÍSTICAS PRELIMINARES")
        print("="*60)
        
        # Agrupar por consulta e tipo
        for consulta in set(r['consulta'] for r in self.resultados):
            print(f"\n{consulta}:")
            
            rest_tempo = [r['tempo_ms'] for r in self.resultados 
                         if r['consulta'] == consulta and r['tipo_api'] == 'REST']
            graphql_tempo = [r['tempo_ms'] for r in self.resultados 
                           if r['consulta'] == consulta and r['tipo_api'] == 'GraphQL']
            
            rest_tamanho = [r['tamanho_bytes'] for r in self.resultados 
                          if r['consulta'] == consulta and r['tipo_api'] == 'REST']
            graphql_tamanho = [r['tamanho_bytes'] for r in self.resultados 
                             if r['consulta'] == consulta and r['tipo_api'] == 'GraphQL']
            
            if rest_tempo and graphql_tempo:
                print(f"  Tempo REST: {statistics.mean(rest_tempo):.2f}ms (±{statistics.stdev(rest_tempo):.2f})")
                print(f"  Tempo GraphQL: {statistics.mean(graphql_tempo):.2f}ms (±{statistics.stdev(graphql_tempo):.2f})")
                print(f"  Tamanho REST: {statistics.mean(rest_tamanho):.2f} bytes")
                print(f"  Tamanho GraphQL: {statistics.mean(graphql_tamanho):.2f} bytes")


def main():
    """Função principal para executar o experimento"""
    print("="*60)
    print("Lab 05 - GraphQL vs REST")
    print("Sprint 1 - Preparação e Execução")
    print("="*60)
    
    # Verificar token
    if GITHUB_TOKEN == "SEU_TOKEN_AQUI":
        print("\n⚠️  ATENÇÃO: Configure seu token do GitHub!")
        print("1. Acesse: https://github.com/settings/tokens")
        print("2. Gere um token com permissões de leitura")
        print("3. Substitua 'SEU_TOKEN_AQUI' no código")
        return
    
    # Criar e executar experimento
    experimento = ExperimentoAPI()
    
    # Executar experimento completo
    experimento.executar_experimento_completo()
    
    # Salvar resultados
    experimento.salvar_resultados('resultados_experimento.csv')


if __name__ == "__main__":
    main()
