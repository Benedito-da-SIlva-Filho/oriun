import sqlite3
from sync_07_logs import log_execucao, registrar_erro

def exportar_propriedades_para_txt(caminho_saida="C:\\Oriun\\06-logs\\propriedades_listadas.txt"):
    try:
        # Conexão com SQLite — direto ao arquivo local
        conn = sqlite3.connect(r"C:\Oriun\03-banco\oriun_local.db")
        cursor = conn.cursor()

        # Campos específicos solicitados
        campos = [
            "a001_cod_propriedade", "a001_nirf_incra", "a001_car", "a001_cod_eras_sisbov",
            "a001_inscr_estadual", "a001_nome_propriedade", "a001_endereco", "a001_municipio",
            "a001_uf", "a001_cx_postal", "a001_fone", "a001_email", "a001_municipio_proximo",
            "a001_distancia_sede_propriedade", "a001_area_total", "a001_latitude", "a001_longitude",
            "a001_roteiro_propriedade", "a001_data_cadastro", "a001_status", "a001_cliente_fornecedor",
            "a001_data_de_criacao", "a001_data_de_movimentacao"
        ]

        # Consulta SQL
        query = f"SELECT {', '.join(campos)} FROM a001_propriedades"
        cursor.execute(query)
        registros = cursor.fetchall()

        # Escrita no arquivo TXT
        with open(caminho_saida, "w", encoding="utf-8") as arquivo:
            arquivo.write("LISTAGEM DE PROPRIEDADES\n\n")
            for linha in registros:
                linha_formatada = "\n".join([f"{campo}: {valor}" for campo, valor in zip(campos, linha)])
                arquivo.write(linha_formatada + "\n" + "-"*40 + "\n")

        log_execucao(f"[EXPORTAÇÃO] ✔ Listagem exportada para {caminho_saida}")

    except Exception as e:
        registrar_erro(f"[EXPORTAÇÃO] ✖ Erro ao exportar propriedades: {e}")

# Chamada direta
exportar_propriedades_para_txt()
