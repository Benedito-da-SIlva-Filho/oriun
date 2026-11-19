# -*- coding: utf-8 -*-
# Script temporario so para testar se o RLS esta funcionando.
# Depois de confirmar que funciona, pode apagar este arquivo.

from sqlalchemy import create_engine, text

# TROQUE a senha abaixo pela senha real do orion_app
SENHA = '2fPtXPCT81fOLiO8lv4ESG9ZQlCLVa00Jy8U'

engine = create_engine(f'postgresql://orion_app:{SENHA}@localhost:5433/orion')
conn = engine.connect()

print('--- Teste 1: SEM definir produtor (deve dar ERRO) ---')
try:
    conn.execute(text('SELECT COUNT(*) FROM tb_4001_gta')).scalar()
    print('FALHOU - conseguiu ler sem definir produtor! RLS nao esta funcionando.')
except Exception as e:
    print('OK - bloqueado como esperado:', str(e)[:120])

conn.rollback()

print('--- Teste 2: COM produtor definido (deve funcionar) ---')
conn.execute(text("SET app.produtor_id = '1'"))
resultado = conn.execute(text('SELECT COUNT(*) FROM tb_4001_gta')).scalar()
print('OK - leu normalmente, total:', resultado)

conn.close()