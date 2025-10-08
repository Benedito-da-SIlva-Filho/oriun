import pandas as pd
import sqlite3

# 1. Carregar o CSV
df = pd.read_csv("backup_a001.csv")

# 2. Remover a coluna da chave primária (se ainda estiver presente)
if "a001_cod_propriedade" in df.columns:
    df.drop(columns=["a001_cod_propriedade"], inplace=True)

# 3. Conectar ao banco SQLite
conn = sqlite3.connect("seu_banco.sqlite")
cursor = conn.cursor()

# 4. Inserir os dados linha por linha
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO a001_propriedades (
            a001_nirf_incra,
            a001_car,
            a001_cod_eras_sisbov,
            a001_inscr_estadual,
            a001_nome_propriedade,
            a001_endereco,
            a001_municipio,
            a001_uf,
            a001_cx_postal,
            a001_fone,
            a001_email,
            a001_municipio_proximo,
            a001_distancia_sede_propriedade,
            a001_area_total,
            a001_latitude,
            a001_longitude,
            a001_roteiro_propriedade,
            a001_data_cadastro,
            a001_status,
            a001_cliente_fornecedor,
            a001_data_de_criacao,
            a001_data_de_movimentacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(row))

# 5. Salvar e fechar
conn.commit()
conn.close()
