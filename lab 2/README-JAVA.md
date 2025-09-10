# Lab 2: Java Quality Analysis

## Configuração e Execução

### 1. Pré-requisitos
- **Java 11+** instalado
- **Maven 3.6+** instalado
- **Git** instalado
- **GitHub Token** configurado

### 2. Configuração do GitHub Token

1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token (classic)"
3. Selecione os scopes: `public_repo`, `read:org`
4. Copie o token gerado
5. Edite o arquivo `config.properties` e substitua `SEU_TOKEN_AQUI` pelo seu token

### 3. Compilação

```bash
mvn clean compile
```

### 4. Execução

#### Executar Lab02S01 (Coleta de repositórios + teste)
```bash
mvn exec:java -Dexec.args="s01"
```

#### Executar Lab02S02 (Análise completa)
```bash
mvn exec:java -Dexec.args="s02"
```

#### Executar ambos os sprints
```bash
mvn exec:java
```

#### Gerar JAR executável
```bash
mvn package
java -jar target/lab2-java-quality-1.0.0.jar s01
```

### 5. Arquivos Gerados

#### Lab02S01:
- `data/repositorios_1000_java.json` - Lista completa dos repositórios
- `data/repositorios_1000_java.csv` - Dados básicos em CSV
- `data/teste_1_repo.csv` - Teste com 1 repositório

#### Lab02S02:
- `data/lab02s02_final_java.csv` - Resultado final com métricas CK
- `data/progresso_lab02s02.csv` - Arquivo de progresso (salvo a cada 10 repos)

### 6. Vantagens da Implementação Java

1. **Integração nativa** com CK (sem subprocess)
2. **Performance** superior ao Python
3. **Gerenciamento automático** de dependências via Maven
4. **API GitHub** robusta e bem documentada
5. **Processamento paralelo** natural do Java
6. **Menos dependências externas**

### 7. Estrutura do Projeto

```
lab 2/
├── pom.xml                     # Configuração Maven
├── config.properties           # Token GitHub
├── src/main/java/br/pucminas/lab/
│   └── Lab2JavaAnalyzer.java   # Código principal
├── data/                       # Arquivos gerados
└── repos_cloned/              # Repositórios clonados (temporário)
```

### 8. Observações

- O limite inicial está configurado para 50 repositórios para teste
- Altere `MAX_REPOS_LIMIT` na classe para processar todos os 1000
- Os repositórios são clonados temporariamente e deletados após análise
- O progresso é salvo automaticamente a cada 10 repositórios processados
