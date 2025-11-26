# Lab 05 - GraphQL vs REST - Experimento Controlado

## Descrição
Experimento controlado para avaliar quantitativamente os benefícios da adoção de APIs GraphQL em comparação com APIs REST.

## Perguntas de Pesquisa

**RQ1**: Respostas às consultas GraphQL são mais rápidas que respostas às consultas REST?

**RQ2**: Respostas às consultas GraphQL têm tamanho menor que respostas às consultas REST?

## Sprint 1 - Desenho e Preparação

### Arquivos Criados

1. **desenho_experimento.md**: Documento completo com o desenho do experimento, incluindo:
   - Hipóteses nula e alternativa
   - Variáveis dependentes e independentes
   - Tratamentos
   - Objetos experimentais
   - Tipo de projeto experimental
   - Quantidade de medições
   - Ameaças à validade

2. **experimento.py**: Script Python para execução do experimento com:
   - 5 tipos diferentes de consultas (simples, média, complexa, lista, aninhada)
   - Implementação de cada consulta em REST e GraphQL
   - Sistema de medição de tempo e tamanho de resposta
   - 30 repetições por consulta
   - Aleatorização da ordem de execução
   - Exportação de resultados em CSV

## Como Executar

### Pré-requisitos

```powershell
pip install requests
```

### Configuração

1. Obtenha um token de acesso do GitHub:
   - Acesse: https://github.com/settings/tokens
   - Clique em "Generate new token (classic)"
   - Selecione as permissões: `public_repo`, `read:org`
   - Copie o token gerado

2. Edite o arquivo `experimento.py` e substitua `SEU_TOKEN_AQUI` pelo seu token:
   ```python
   GITHUB_TOKEN = "seu_token_aqui"
   ```

### Execução do Experimento

```powershell
cd "c:\Users\Estêvão\Documents\Faculdade\Semestre 6\LAB-Experimentacao-SW\lab 5"
python experimento.py
```

### Saída Esperada

O script irá:
1. Executar 5 tipos diferentes de consultas
2. Realizar 30 medições de cada consulta (15 REST + 15 GraphQL)
3. Total: 300 medições
4. Gerar arquivo `resultados_experimento.csv` com os dados coletados
5. Exibir estatísticas preliminares no console

## Estrutura dos Resultados

O arquivo CSV gerado contém as seguintes colunas:
- `consulta`: Nome da consulta executada
- `tipo_api`: REST ou GraphQL
- `tempo_ms`: Tempo de resposta em milissegundos
- `tamanho_bytes`: Tamanho da resposta em bytes
- `timestamp`: Data e hora da medição

## Tipos de Consultas

1. **Consulta Simples**: Informações básicas de um repositório
2. **Consulta Média**: Repositório com lista de issues
3. **Consulta Complexa**: Repositório com issues, pull requests e contributors
4. **Consulta Lista**: Múltiplos repositórios de uma organização
5. **Consulta Aninhada**: Repositório com commits e autores (múltiplos níveis)

## Próximos Passos (Sprint 2)

- Análise estatística dos dados coletados
- Testes de hipóteses
- Elaboração do relatório final

## Próximos Passos (Sprint 3)

- Criação de dashboard com visualizações
- Gráficos comparativos
- Interpretação visual dos resultados
