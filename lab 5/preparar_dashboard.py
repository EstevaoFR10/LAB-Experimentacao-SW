"""
Lab 05 - Sprint 3: Preparação de Dados para Dashboard Power BI
Processa os resultados do experimento e gera métricas adicionais
"""

import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats

def carregar_dados(arquivo='resultados_experimento.csv'):
    """Carrega os dados do experimento"""
    df = pd.read_csv(arquivo)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def adicionar_metricas_derivadas(df):
    """Adiciona métricas derivadas ao dataset"""
    
    # Extrair número da consulta e complexidade
    df['numero_consulta'] = df['consulta'].str.extract(r'Consulta (\d+)')[0].astype(int)
    
    # Mapear complexidade
    complexidade_map = {
        'Consulta 1 - Simples': 'Simples',
        'Consulta 2 - Média': 'Média',
        'Consulta 3 - Complexa': 'Alta',
        'Consulta 4 - Lista': 'Média',
        'Consulta 5 - Aninhada': 'Alta'
    }
    df['complexidade'] = df['consulta'].map(complexidade_map)
    
    # Número de endpoints REST necessários
    endpoints_map = {
        'Consulta 1 - Simples': 1,
        'Consulta 2 - Média': 2,
        'Consulta 3 - Complexa': 4,
        'Consulta 4 - Lista': 1,
        'Consulta 5 - Aninhada': 2
    }
    df['num_endpoints'] = df['consulta'].map(endpoints_map)
    
    # Extrair informações temporais
    df['data'] = df['timestamp'].dt.date
    df['hora'] = df['timestamp'].dt.hour
    df['minuto'] = df['timestamp'].dt.minute
    df['periodo_dia'] = df['hora'].apply(lambda x: 'Manhã' if 6 <= x < 12 
                                          else 'Tarde' if 12 <= x < 18 
                                          else 'Noite' if 18 <= x < 24 
                                          else 'Madrugada')
    
    # Ordenar por tempo para calcular ordem de execução
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['ordem_execucao'] = df.index + 1
    
    return df

def calcular_metricas_comparativas(df):
    """Calcula métricas comparativas entre REST e GraphQL"""
    
    metricas = []
    
    for consulta in df['consulta'].unique():
        df_consulta = df[df['consulta'] == consulta]
        
        # Dados REST
        rest_data = df_consulta[df_consulta['tipo_api'] == 'REST']
        tempo_rest = rest_data['tempo_ms'].values
        tamanho_rest = rest_data['tamanho_bytes'].values
        
        # Dados GraphQL
        graphql_data = df_consulta[df_consulta['tipo_api'] == 'GraphQL']
        tempo_graphql = graphql_data['tempo_ms'].values
        tamanho_graphql = graphql_data['tamanho_bytes'].values
        
        # Estatísticas de Tempo
        metrica = {
            'consulta': consulta,
            'complexidade': df_consulta['complexidade'].iloc[0],
            'num_endpoints': df_consulta['num_endpoints'].iloc[0],
            
            # REST - Tempo
            'rest_tempo_media': np.mean(tempo_rest),
            'rest_tempo_mediana': np.median(tempo_rest),
            'rest_tempo_desvio': np.std(tempo_rest),
            'rest_tempo_min': np.min(tempo_rest),
            'rest_tempo_max': np.max(tempo_rest),
            'rest_tempo_p25': np.percentile(tempo_rest, 25),
            'rest_tempo_p75': np.percentile(tempo_rest, 75),
            'rest_tempo_p95': np.percentile(tempo_rest, 95),
            
            # GraphQL - Tempo
            'graphql_tempo_media': np.mean(tempo_graphql),
            'graphql_tempo_mediana': np.median(tempo_graphql),
            'graphql_tempo_desvio': np.std(tempo_graphql),
            'graphql_tempo_min': np.min(tempo_graphql),
            'graphql_tempo_max': np.max(tempo_graphql),
            'graphql_tempo_p25': np.percentile(tempo_graphql, 25),
            'graphql_tempo_p75': np.percentile(tempo_graphql, 75),
            'graphql_tempo_p95': np.percentile(tempo_graphql, 95),
            
            # REST - Tamanho
            'rest_tamanho_media': np.mean(tamanho_rest),
            'rest_tamanho_desvio': np.std(tamanho_rest),
            
            # GraphQL - Tamanho
            'graphql_tamanho_media': np.mean(tamanho_graphql),
            'graphql_tamanho_desvio': np.std(tamanho_graphql),
            
            # Ganhos Percentuais
            'ganho_tempo_percentual': ((np.mean(tempo_rest) - np.mean(tempo_graphql)) / np.mean(tempo_rest)) * 100,
            'ganho_tamanho_percentual': ((np.mean(tamanho_rest) - np.mean(tamanho_graphql)) / np.mean(tamanho_rest)) * 100,
            
            # Speedup
            'speedup': np.mean(tempo_rest) / np.mean(tempo_graphql),
            
            # Redução absoluta
            'reducao_tempo_ms': np.mean(tempo_rest) - np.mean(tempo_graphql),
            'reducao_tamanho_bytes': np.mean(tamanho_rest) - np.mean(tamanho_graphql),
            
            # Coeficiente de Variação (estabilidade)
            'rest_cv_tempo': (np.std(tempo_rest) / np.mean(tempo_rest)) * 100,
            'graphql_cv_tempo': (np.std(tempo_graphql) / np.mean(tempo_graphql)) * 100,
            
            # Teste estatístico (t-test pareado)
            't_statistic_tempo': stats.ttest_rel(tempo_rest, tempo_graphql)[0],
            'p_value_tempo': stats.ttest_rel(tempo_rest, tempo_graphql)[1],
            't_statistic_tamanho': stats.ttest_rel(tamanho_rest, tamanho_graphql)[0],
            'p_value_tamanho': stats.ttest_rel(tamanho_rest, tamanho_graphql)[1],
            
            # Significância estatística (α = 0.05)
            'significante_tempo': 'Sim' if stats.ttest_rel(tempo_rest, tempo_graphql)[1] < 0.05 else 'Não',
            'significante_tamanho': 'Sim' if stats.ttest_rel(tamanho_rest, tamanho_graphql)[1] < 0.05 else 'Não',
        }
        
        metricas.append(metrica)
    
    return pd.DataFrame(metricas)

def calcular_metricas_gerais(df):
    """Calcula métricas gerais do experimento"""
    
    rest_data = df[df['tipo_api'] == 'REST']
    graphql_data = df[df['tipo_api'] == 'GraphQL']
    
    metricas_gerais = {
        'total_medicoes': len(df),
        'medicoes_rest': len(rest_data),
        'medicoes_graphql': len(graphql_data),
        
        # Tempo - Geral
        'tempo_medio_rest': rest_data['tempo_ms'].mean(),
        'tempo_medio_graphql': graphql_data['tempo_ms'].mean(),
        'ganho_tempo_geral': ((rest_data['tempo_ms'].mean() - graphql_data['tempo_ms'].mean()) / rest_data['tempo_ms'].mean()) * 100,
        'speedup_geral': rest_data['tempo_ms'].mean() / graphql_data['tempo_ms'].mean(),
        
        # Tamanho - Geral
        'tamanho_medio_rest': rest_data['tamanho_bytes'].mean(),
        'tamanho_medio_graphql': graphql_data['tamanho_bytes'].mean(),
        'ganho_tamanho_geral': ((rest_data['tamanho_bytes'].mean() - graphql_data['tamanho_bytes'].mean()) / rest_data['tamanho_bytes'].mean()) * 100,
        'reducao_tamanho_geral': rest_data['tamanho_bytes'].mean() / graphql_data['tamanho_bytes'].mean(),
        
        # Testes estatísticos gerais
        'p_value_tempo_geral': stats.ttest_ind(rest_data['tempo_ms'], graphql_data['tempo_ms'])[1],
        'p_value_tamanho_geral': stats.ttest_ind(rest_data['tamanho_bytes'], graphql_data['tamanho_bytes'])[1],
        
        # Metadados
        'data_inicio': df['timestamp'].min(),
        'data_fim': df['timestamp'].max(),
        'duracao_experimento_minutos': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
    }
    
    return pd.DataFrame([metricas_gerais])

def gerar_tabela_pivot_tempo(df):
    """Gera tabela pivot para análise de tempo"""
    return df.pivot_table(
        values='tempo_ms',
        index='consulta',
        columns='tipo_api',
        aggfunc=['mean', 'median', 'std', 'min', 'max']
    ).round(2)

def gerar_tabela_pivot_tamanho(df):
    """Gera tabela pivot para análise de tamanho"""
    return df.pivot_table(
        values='tamanho_bytes',
        index='consulta',
        columns='tipo_api',
        aggfunc=['mean', 'std', 'min', 'max']
    ).round(2)

def criar_dataset_boxplot(df):
    """Cria dataset otimizado para box plots"""
    stats_list = []
    
    for consulta in df['consulta'].unique():
        for tipo_api in ['REST', 'GraphQL']:
            dados = df[(df['consulta'] == consulta) & (df['tipo_api'] == tipo_api)]
            
            for metrica, coluna in [('Tempo (ms)', 'tempo_ms'), ('Tamanho (bytes)', 'tamanho_bytes')]:
                valores = dados[coluna].values
                stats_list.append({
                    'consulta': consulta,
                    'tipo_api': tipo_api,
                    'metrica': metrica,
                    'min': np.min(valores),
                    'q1': np.percentile(valores, 25),
                    'mediana': np.median(valores),
                    'q3': np.percentile(valores, 75),
                    'max': np.max(valores),
                    'media': np.mean(valores),
                    'desvio': np.std(valores)
                })
    
    return pd.DataFrame(stats_list)

def main():
    """Função principal"""
    print("="*60)
    print("PREPARAÇÃO DE DADOS PARA DASHBOARD POWER BI")
    print("="*60)
    
    # 1. Carregar dados
    print("\n1. Carregando dados do experimento...")
    df_original = carregar_dados()
    print(f"   ✓ {len(df_original)} registros carregados")
    
    # 2. Adicionar métricas derivadas
    print("\n2. Adicionando métricas derivadas...")
    df_enriquecido = adicionar_metricas_derivadas(df_original)
    print(f"   ✓ Dataset enriquecido com {len(df_enriquecido.columns)} colunas")
    
    # 3. Calcular métricas comparativas
    print("\n3. Calculando métricas comparativas...")
    df_metricas = calcular_metricas_comparativas(df_enriquecido)
    print(f"   ✓ Métricas calculadas para {len(df_metricas)} consultas")
    
    # 4. Calcular métricas gerais
    print("\n4. Calculando métricas gerais...")
    df_gerais = calcular_metricas_gerais(df_enriquecido)
    print(f"   ✓ Métricas gerais calculadas")
    
    # 5. Criar datasets para visualizações
    print("\n5. Criando datasets para visualizações...")
    df_boxplot = criar_dataset_boxplot(df_enriquecido)
    print(f"   ✓ Dataset para box plots criado")
    
    # 6. Salvar arquivos
    print("\n6. Salvando arquivos...")
    
    # Dataset principal enriquecido
    df_enriquecido.to_csv('dados_enriquecidos.csv', index=False, encoding='utf-8-sig')
    print("   ✓ dados_enriquecidos.csv")
    
    # Métricas comparativas
    df_metricas.to_csv('metricas_comparativas.csv', index=False, encoding='utf-8-sig')
    print("   ✓ metricas_comparativas.csv")
    
    # Métricas gerais
    df_gerais.to_csv('metricas_gerais.csv', index=False, encoding='utf-8-sig')
    print("   ✓ metricas_gerais.csv")
    
    # Dataset para box plots
    df_boxplot.to_csv('dados_boxplot.csv', index=False, encoding='utf-8-sig')
    print("   ✓ dados_boxplot.csv")
    
    # Pivots para tabelas
    pivot_tempo = gerar_tabela_pivot_tempo(df_enriquecido)
    pivot_tempo.to_csv('pivot_tempo.csv', encoding='utf-8-sig')
    print("   ✓ pivot_tempo.csv")
    
    pivot_tamanho = gerar_tabela_pivot_tamanho(df_enriquecido)
    pivot_tamanho.to_csv('pivot_tamanho.csv', encoding='utf-8-sig')
    print("   ✓ pivot_tamanho.csv")
    
    # 7. Exibir resumo
    print("\n" + "="*60)
    print("RESUMO DAS MÉTRICAS GERAIS")
    print("="*60)
    
    print(f"\nTotal de medições: {df_gerais['total_medicoes'].iloc[0]:.0f}")
    print(f"Duração do experimento: {df_gerais['duracao_experimento_minutos'].iloc[0]:.1f} minutos")
    
    print("\n--- TEMPO DE RESPOSTA (RQ1) ---")
    print(f"REST - Média: {df_gerais['tempo_medio_rest'].iloc[0]:.2f} ms")
    print(f"GraphQL - Média: {df_gerais['tempo_medio_graphql'].iloc[0]:.2f} ms")
    print(f"Ganho: {df_gerais['ganho_tempo_geral'].iloc[0]:.2f}%")
    print(f"Speedup: {df_gerais['speedup_geral'].iloc[0]:.2f}x")
    print(f"P-value: {df_gerais['p_value_tempo_geral'].iloc[0]:.6f}")
    print(f"Significante: {'Sim' if df_gerais['p_value_tempo_geral'].iloc[0] < 0.05 else 'Não'}")
    
    print("\n--- TAMANHO DA RESPOSTA (RQ2) ---")
    print(f"REST - Média: {df_gerais['tamanho_medio_rest'].iloc[0]:.2f} bytes")
    print(f"GraphQL - Média: {df_gerais['tamanho_medio_graphql'].iloc[0]:.2f} bytes")
    print(f"Redução: {df_gerais['ganho_tamanho_geral'].iloc[0]:.2f}%")
    print(f"P-value: {df_gerais['p_value_tamanho_geral'].iloc[0]:.6f}")
    print(f"Significante: {'Sim' if df_gerais['p_value_tamanho_geral'].iloc[0] < 0.05 else 'Não'}")
    
    print("\n--- MÉTRICAS POR CONSULTA ---")
    for _, row in df_metricas.iterrows():
        print(f"\n{row['consulta']}:")
        print(f"  Ganho Tempo: {row['ganho_tempo_percentual']:.2f}% | Speedup: {row['speedup']:.2f}x")
        print(f"  Ganho Tamanho: {row['ganho_tamanho_percentual']:.2f}%")
        print(f"  Significância: Tempo={row['significante_tempo']}, Tamanho={row['significante_tamanho']}")
    
    print("\n" + "="*60)
    print("ARQUIVOS PRONTOS PARA POWER BI!")
    print("="*60)
    print("\nImporte os seguintes arquivos no Power BI:")
    print("1. dados_enriquecidos.csv - Dataset completo para análises detalhadas")
    print("2. metricas_comparativas.csv - KPIs e métricas por consulta")
    print("3. metricas_gerais.csv - Métricas gerais do experimento")
    print("4. dados_boxplot.csv - Dados para gráficos de distribuição")
    print("5. pivot_tempo.csv - Tabela resumo de tempo")
    print("6. pivot_tamanho.csv - Tabela resumo de tamanho")
    
    print("\n✓ Processamento concluído com sucesso!")

if __name__ == "__main__":
    main()
