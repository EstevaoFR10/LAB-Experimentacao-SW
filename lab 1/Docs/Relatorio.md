# Lab01S02 - Primeira Versão do Relatório
## Características de Repositórios Populares no GitHub

**Curso:** Engenharia de Software  
**Disciplina:** Laboratório de Experimentação de Software  
**Professor:** Danilo de Quadros Maia Filho 
**Turno:** Noite  
**Período:** 6º  
**Universidade:** PUC Minas  

---

## 1. Introdução

Este estudo investiga as características dos 1.000 repositórios com maior número de estrelas no GitHub. O objetivo é entender padrões de desenvolvimento em sistemas open-source populares através de seis questões de pesquisa.

---

## 2. Questões de Pesquisa e Hipóteses Informais

### RQ01: Sistemas populares são maduros/antigos?
**Métrica:** Idade do repositório (dias desde criação)

**Hipótese Informal:** 
Acreditamos que repositórios populares são relativamente antigos (3+ anos), pois precisam de tempo para ganhar reconhecimento da comunidade e acumular estrelas.

---

### RQ02: Sistemas populares recebem muita contribuição externa?
**Métrica:** Total de pull requests aceitas

**Hipótese Informal:** 
Esperamos que projetos populares tenham muitas pull requests aceitas, indicando forte colaboração da comunidade e desenvolvimento aberto.

---

### RQ03: Sistemas populares lançam releases com frequência?
**Métrica:** Total de releases

**Hipótese Informal:** 
Projetos populares devem ter várias releases, demonstrando ciclos de desenvolvimento organizados e entregas estruturadas para os usuários.

---

### RQ04: Sistemas populares são atualizados com frequência?
**Métrica:** Tempo até a última atualização (dias)

**Hipótese Informal:** 
Repositórios populares devem ser atualizados recentemente (últimos 30-90 dias), mostrando manutenção ativa e desenvolvimento contínuo.

---

### RQ05: Sistemas populares são escritos nas linguagens mais populares?
**Métrica:** Linguagem primária de cada repositório

**Hipótese Informal:** 
Esperamos que as linguagens mais comuns sejam JavaScript, Python, Java, TypeScript e C++, refletindo as tendências atuais de desenvolvimento.

---

### RQ06: Sistemas populares possuem um alto percentual de issues fechadas?
**Métrica:** Razão entre issues fechadas e total de issues

**Hipótese Informal:** 
Projetos populares devem ter alta taxa de issues resolvidas (>70%), indicando boa manutenção e responsividade da equipe.

---

## 3. Metodologia

### 3.1 Coleta de Dados
- **Fonte:** GitHub REST API
- **Amostra:** 1.000 repositórios com maior número de estrelas
- **Ferramenta:** Script Python com bibliotecas padrão
- **Critério:** Busca por `stars:>1` ordenada por estrelas (decrescente)

### 3.2 Paginação Implementada
- **10 páginas** de 100 repositórios cada
- **Rate limiting** otimizado (0.1s entre requisições)
- **Search API** para contagem eficiente de PRs e issues

### 3.3 Dados Coletados
Para cada repositório:
- Nome, proprietário, URL, número de estrelas
- Data de criação e última atualização
- Linguagem primária
- Total de PRs aceitas, releases, issues (abertas/fechadas)
- Número de forks e descrição

---

## 4. Próximos Passos (Lab01S03)

Na próxima etapa, iremos:
1. **Analisar os dados coletados** calculando medianas para cada métrica
2. **Criar visualizações** (gráficos e tabelas) 
3. **Testar as hipóteses** comparando resultados esperados vs. obtidos
4. **Elaborar o relatório final** com discussão completa dos resultados

---

## 5. Arquivos Gerados

- **`repositorios_1000.csv`** - Dados principais em formato CSV
- **`repositorios_1000.json`** - Backup dos dados em JSON
- **`main.py`** - Script de coleta otimizado
- **Backups progressivos** a cada 100 repositórios processados

---
