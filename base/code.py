import pandas as pd
import json

def consolidar_candidatos_para_json():
    sep = ';'
    encoding = 'latin1'

    print("Carregando arquivos...")
    cand = pd.read_csv('consulta_cand_2026_PR.csv', sep=sep, encoding=encoding, dtype=str)
    comp = pd.read_csv('consulta_cand_complementar_2026_PR.csv', sep=sep, encoding=encoding, dtype=str)
    bens = pd.read_csv('bem_candidato_2026_PR.csv', sep=sep, encoding=encoding, dtype=str)
    cass = pd.read_csv('motivo_cassacao_2026_PR.csv', sep=sep, encoding=encoding, dtype=str)

    # 1. Tratamento e agrupamento dos Bens
    print("Processando bens...")
    bens['VR_BEM_NUM'] = pd.to_numeric(
        bens['VR_BEM_CANDIDATO'].str.replace(',', '.', regex=False), 
        errors='coerce'
    ).fillna(0.0)

    # Agrupa os bens em objetos estruturados por candidato
    bens_dict = {}
    for sq_cand, grupo in bens.groupby('SQ_CANDIDATO'):
        lista_bens = []
        for _, linha in grupo.iterrows():
            lista_bens.append({
                'tipo': linha.get('DS_TIPO_BEM_CANDIDATO', ''),
                'descricao': linha.get('DS_BEM_CANDIDATO', ''),
                'valor': float(linha.get('VR_BEM_NUM', 0.0))
            })
        bens_dict[sq_cand] = {
            'bens': lista_bens,
            'valor_total_bens': round(grupo['VR_BEM_NUM'].sum(), 2)
        }

    # 2. Tratamento e agrupamento dos Motivos de Cassação
    print("Processando cassações...")
    cass_dict = {}
    for sq_cand, grupo in cass.groupby('SQ_CANDIDATO'):
        cass_dict[sq_cand] = {
            'tp_motivo': list(grupo['DS_TP_MOTIVO'].dropna().unique()),
            'motivo': list(grupo['DS_MOTIVO'].dropna().unique())
        }

    # 3. Limpeza de colunas genéricas/repetidas no arquivo complementar
    colunas_descarte = ['DT_GERACAO', 'HH_GERACAO', 'ANO_ELEICAO', 'CD_TIPO_ELEICAO', 
                        'NM_TIPO_ELEICAO', 'CD_ELEICAO', 'DS_ELEICAO', 'DT_ELEICAO', 
                        'SG_UF', 'SG_UE', 'NM_UE']
    comp = comp.drop(columns=[c for c in colunas_descarte if c in comp.columns])

    # 4. Merge dos dados principais e complementares
    print("Unindo informações...")
    df_candidatos = pd.merge(cand, comp, on='SQ_CANDIDATO', how='left', suffixes=('', '_COMP'))

    # 5. Montagem da estrutura JSON final
    lista_candidatos_json = []

    for _, linha in df_candidatos.iterrows():
        sq_cand = linha['SQ_CANDIDATO']
        
        # Converte a linha do DataFrame para dicionário simples (removendo NaN)
        dados_candidato = {k: v for k, v in linha.to_dict().items() if pd.notna(v)}
        
        # Adiciona os dados de bens
        info_bens = bens_dict.get(sq_cand, {'bens': [], 'valor_total_bens': 0.0})
        dados_candidato['bens'] = info_bens['bens']
        dados_candidato['valor_total_bens'] = info_bens['valor_total_bens']
        
        # Adiciona os dados de cassação
        dados_candidato['motivo_cassacao'] = cass_dict.get(sq_cand, {'tp_motivo': [], 'motivo': []})
        
        lista_candidatos_json.append(dados_candidato)

    # 6. Salvar em arquivo JSON
    arquivo_saida = 'candidatos_2026_PR_consolidado.json'
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(lista_candidatos_json, f, ensure_ascii=False, indent=2)

    print(f"Pronto! Arquivo JSON gerado com sucesso: {arquivo_saida}")
    print(f"Total de candidatos processados: {len(lista_candidatos_json)}")

if __name__ == '__main__':
    consolidar_candidatos_para_json()