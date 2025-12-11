"""
Script para arredondar tempo_ms para 2 casas decimais
"""

import pandas as pd

def arredondar_tempo(arquivo_entrada, arquivo_saida=None):
    """
    Arredonda a coluna tempo_ms para 2 casas decimais
    
    Args:
        arquivo_entrada: nome do arquivo CSV de entrada
        arquivo_saida: nome do arquivo de saída (opcional, sobrescreve se None)
    """
    # Carregar dados
    print(f"Carregando {arquivo_entrada}...")
    df = pd.read_csv(arquivo_entrada)
    
    # Mostrar exemplo antes
    print("\nAntes do arredondamento (primeiras 5 linhas):")
    print(df[['consulta', 'tipo_api', 'tempo_ms']].head())
    
    # Arredondar tempo_ms para 2 casas decimais
    df['tempo_ms'] = df['tempo_ms'].round(2)
    
    # Mostrar exemplo depois
    print("\nDepois do arredondamento (primeiras 5 linhas):")
    print(df[['consulta', 'tipo_api', 'tempo_ms']].head())
    
    # Salvar arquivo
    if arquivo_saida is None:
        arquivo_saida = arquivo_entrada
    
    df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
    print(f"\n✓ Arquivo salvo: {arquivo_saida}")
    
    return df

def main():
    """Função principal"""
    print("="*60)
    print("ARREDONDAMENTO DE DADOS - tempo_ms para 2 casas decimais")
    print("="*60)
    
    # Lista de arquivos para processar
    arquivos = [
        'resultados/resultados_experimento.csv',
        'resultados/dados_enriquecidos.csv'
    ]
    
    for arquivo in arquivos:
        try:
            print(f"\n{'='*60}")
            arredondar_tempo(arquivo)
        except FileNotFoundError:
            print(f"⚠️  Arquivo {arquivo} não encontrado, pulando...")
        except Exception as e:
            print(f"❌ Erro ao processar {arquivo}: {e}")
    
    print("\n" + "="*60)
    print("✓ Processamento concluído!")
    print("="*60)

if __name__ == "__main__":
    main()
