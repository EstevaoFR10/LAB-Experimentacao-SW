# Desenho do Experimento - GraphQL vs REST

## A. Hipóteses

### Hipótese Nula (H0)
- **H0₁**: Não há diferença significativa no tempo de resposta entre consultas GraphQL e REST.
- **H0₂**: Não há diferença significativa no tamanho das respostas entre consultas GraphQL e REST.

### Hipótese Alternativa (H1)
- **H1₁**: Consultas GraphQL apresentam tempo de resposta significativamente menor que consultas REST.
- **H1₂**: Consultas GraphQL apresentam tamanho de resposta significativamente menor que consultas REST.

## B. Variáveis Dependentes

As variáveis dependentes são aquelas que serão medidas durante o experimento:

1. **Tempo de Resposta (ms)**: Tempo decorrido desde o envio da requisição até o recebimento completo da resposta.
2. **Tamanho da Resposta (bytes)**: Tamanho total dos dados retornados pela API.

## C. Variáveis Independentes

A variável independente é aquela que será manipulada:

1. **Tipo de API**: GraphQL ou REST

## D. Tratamentos

Os tratamentos que serão aplicados aos objetos experimentais:

1. **Tratamento 1 (T1)**: Consultas utilizando API GraphQL
2. **Tratamento 2 (T2)**: Consultas utilizando API REST

## E. Objetos Experimentais

APIs públicas que oferecem tanto GraphQL quanto REST:

1. **GitHub API**
   - REST: https://api.github.com
   - GraphQL: https://api.github.com/graphql
   
2. **Shopify API** (alternativa)
   - REST: https://shopify.dev/api/admin-rest
   - GraphQL: https://shopify.dev/api/admin-graphql

**Objeto Escolhido**: GitHub API (oferece ambas as interfaces para os mesmos dados)

## F. Tipo de Projeto Experimental

**Projeto Pareado (Paired Design)**

- Cada consulta será executada tanto via GraphQL quanto via REST
- Isso permite comparação direta entre os tratamentos, controlando variáveis externas
- Reduz a variabilidade experimental

## G. Quantidade de Medições

Para garantir significância estatística:

- **Número de consultas diferentes**: 5 tipos de consultas (queries)
- **Repetições por consulta**: 30 execuções de cada tipo
- **Total de medições**: 5 consultas × 2 tratamentos × 30 repetições = 300 medições

### Tipos de Consultas a serem testadas:

1. **Consulta Simples**: Buscar informações básicas de um repositório
2. **Consulta Média**: Buscar repositório com issues
3. **Consulta Complexa**: Buscar repositório com issues, pull requests e contributors
4. **Consulta de Lista**: Buscar múltiplos repositórios
5. **Consulta Aninhada**: Buscar dados com múltiplos níveis de profundidade

## H. Ameaças à Validade

### Validade Interna
1. **Variação de rede**: Diferentes condições de rede podem afetar o tempo de resposta
   - *Mitigação*: Executar todas as medições no mesmo ambiente e horário, com múltiplas repetições
   
2. **Cache**: Respostas em cache podem distorcer os resultados
   - *Mitigação*: Alternar entre GraphQL e REST de forma aleatória, adicionar timestamps únicos

3. **Rate limiting**: APIs podem limitar requisições
   - *Mitigação*: Incluir delays entre requisições, usar token de autenticação

### Validade Externa
1. **Generalização**: Resultados podem não se aplicar a outras APIs
   - *Mitigação*: Documentar claramente o contexto e características da API testada

2. **Tipos de consulta**: Consultas escolhidas podem não representar casos reais
   - *Mitigação*: Selecionar consultas que representem casos de uso comuns

### Validade de Construção
1. **Métricas**: Tempo e tamanho podem não capturar toda a complexidade
   - *Mitigação*: Documentar limitações e focar nas perguntas de pesquisa específicas

### Validade de Conclusão
1. **Tamanho da amostra**: Amostra insuficiente pode levar a conclusões incorretas
   - *Mitigação*: Realizar 30 repetições por consulta para garantir poder estatístico
   
2. **Análise estatística inadequada**: Uso de testes inadequados
   - *Mitigação*: Aplicar testes estatísticos apropriados (teste t pareado ou Wilcoxon)

## I. Ambiente de Execução

- **Sistema Operacional**: Windows
- **Linguagem**: Python 3.x
- **Bibliotecas**: requests, time, statistics, pandas
- **Conexão**: Rede estável, mesma máquina para todas as medições
- **Horário**: Medições realizadas em período controlado para minimizar variações
