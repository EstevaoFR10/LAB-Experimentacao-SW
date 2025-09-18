# Lab 2 - Análise de Qualidade de Repositórios Java

## 🎯 Objetivo
Analisar as características de qualidade de **1.000 repositórios Java** mais populares do GitHub usando métricas CK (Chidamber & Kemerer) e correlacioná-las com características do processo de desenvolvimento.

## 📋 Pré-requisitos
- **Java 11+** (testado com Java 25)
- **Maven 3.6+** 
- **Git**
- **Token do GitHub** (Personal Access Token)

## ⚙️ Configuração

### 1. Clone do Repositório
```bash
git clone <repositorio-url>
cd "lab 2"
```

### 2. Configuração do Token GitHub
1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token (classic)"
3. Selecione os scopes:
   - ✅ `public_repo` (acesso a repositórios públicos)
   - ✅ `read:org` (leitura de organizações)
4. Copie o token gerado
5. Edite o arquivo `config.properties` e substitua `SEU_TOKEN_AQUI` pelo seu token

### 3. Instalação do Maven (se necessário)
#### Windows:
```powershell
# Baixar e extrair Maven
Invoke-WebRequest -Uri "https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip" -OutFile "maven.zip"
Expand-Archive -Path "maven.zip" -DestinationPath "C:\apache-maven" -Force
$env:PATH = "C:\apache-maven\apache-maven-3.9.9\bin;$env:PATH"
```

## 🚀 Execução

### Método Recomendado (Maven Exec)
```bash
# Compilar o projeto
mvn clean compile

# Executar ambos os sprints
mvn exec:java
```

### Execução por Sprint Individual
```bash
# Apenas Sprint 1 (coleta e teste)
mvn exec:java -Dexec.args="s01"

# Apenas Sprint 2 (análise completa dos 1000 repos)
mvn exec:java -Dexec.args="s02"
```

### Método Alternativo (JAR)
```bash
# Gerar JAR executável
mvn clean package -DskipTests

# Executar (pode ter problemas de assinatura)
java -jar target/lab2-java-quality-1.0.0.jar
```

## 📁 Arquivos Gerados

### Sprint 1 (Lab02S01):
- `data/repositorios_1000_java.json` - Lista completa dos repositórios coletados
- `data/repositorios_1000_java.csv` - Dados básicos dos repositórios
- `data/teste_1_repo.csv` - Resultado do teste com métricas CK de 1 repositório

### Sprint 2 (Lab02S02):
- `data/lab02s02_final_java.csv` - **📊 Arquivo principal** com métricas CK dos 1000 repositórios
- `data/progresso_lab02s02.csv` - Progresso salvo a cada 10 repositórios

### Arquivos Temporários:
- `repos_cloned/` - Repositórios clonados (deletados automaticamente)
- `ck_output/` - Saída raw da ferramenta CK

## 📊 Métricas Coletadas

### Métricas de Processo:
- **Popularidade**: Número de estrelas ⭐
- **Maturidade**: Idade do repositório em anos 📅
- **Atividade**: Número de releases 🏷️
- **Tamanho**: Linhas de código (LOC) 📝

### Métricas de Qualidade (CK):
- **CBO**: Coupling Between Objects (Acoplamento entre objetos)
- **DIT**: Depth of Inheritance Tree (Profundidade da árvore de herança)
- **LCOM**: Lack of Cohesion of Methods (Falta de coesão dos métodos)

## 🔬 Questões de Pesquisa

- **RQ01**: Qual a relação entre **popularidade** (estrelas) × **qualidade** (CBO, DIT, LCOM)?
- **RQ02**: Qual a relação entre **maturidade** (idade) × **qualidade**?
- **RQ03**: Qual a relação entre **atividade** (releases) × **qualidade**?
- **RQ04**: Qual a relação entre **tamanho** (LOC) × **qualidade**?

## ⏱️ Tempo Estimado
- **Lab02S01**: ~5-10 minutos (coleta + teste)
- **Lab02S02**: ~8-12 horas (1000 repositórios)
  - Clone: ~2-3 segundos por repo
  - Análise CK: ~5-10 segundos por repo
  - **Total**: ~2-4 horas para clones + 4-8 horas para análises

## 🛠️ Troubleshooting

### Erro de Rate Limit do GitHub:
- Aguarde 1 hora ou use outro token
- Limite: 5000 requisições/hora

### Erro de Memória:
```bash
# Aumentar memória da JVM
export MAVEN_OPTS="-Xmx8g"
mvn exec:java
```

### Problema com JAR (assinatura):
- Use a execução via Maven: `mvn exec:java`
- Problema comum com dependências conflitantes

### Repositório sem código Java:
- O sistema tenta automaticamente outros repositórios
- Alguns repos famosos são apenas documentação

## 📈 Análise dos Resultados

O arquivo final `data/lab02s02_final_java.csv` contém todas as métricas necessárias para:
1. **Análises estatísticas**: média, mediana, desvio padrão
2. **Correlações**: entre variáveis de processo e qualidade  
3. **Visualizações**: gráficos de dispersão, boxplots
4. **Testes estatísticos**: Spearman, Pearson

## 👥 Estrutura do Projeto
```
lab 2/
├── config.properties                    # Configuração do token GitHub
├── pom.xml                             # Dependências Maven
├── src/main/java/br/pucminas/lab/
│   ├── Lab2JavaAnalyzer.java          # 🔧 Classe principal
│   ├── TestConnection.java            # Teste de conectividade  
│   └── TestGitHub.java                # Teste da API GitHub
├── data/                              # 📊 Arquivos de resultado
│   ├── repositorios_1000_java.json   # Lista de repositórios
│   ├── repositorios_1000_java.csv    # Dados básicos
│   └── lab02s02_final_java.csv       # 🎯 RESULTADO FINAL
└── target/                            # Arquivos compilados
```

## ✅ Status do Projeto

- ✅ **Configuração**: GitHub API, Maven, dependências CK
- ✅ **Coleta**: Top 1000 repositórios Java do GitHub  
- ✅ **Análise**: Métricas CK corrigidas e validadas
- ✅ **Processamento**: Sistema de resumo em caso de interrupção
- ✅ **Resultado**: CSV final pronto para análise estatística

## 📝 Relatório Final

Após a execução, elaborar relatório acadêmico com:

1. **Introdução**: Contexto e hipóteses para cada RQ
2. **Metodologia**: Processo de coleta e ferramentas utilizadas
3. **Resultados**: Resposta detalhada para cada RQ com dados estatísticos
4. **Discussão**: Comparação entre hipóteses e resultados obtidos
5. **Conclusão**: Síntese dos achados e implicações

**⏰ Tempo total estimado**: 12-16 horas (execução + análise + relatório)

---

## 🚨 Configurações Importantes

- **MAX_REPOS_LIMIT**: 1000 repositórios (configuração de produção)
- **GitHub Token**: Necessário para evitar rate limiting
- **Timeout**: 5 minutos por clone de repositório  
- **Progresso**: Salvo automaticamente a cada 10 repositórios

**🎯 Objetivo Final**: Arquivo `data/lab02s02_final_java.csv` com 1000 repositórios analisados para responder às questões de pesquisa sobre qualidade de software em projetos Java populares.
