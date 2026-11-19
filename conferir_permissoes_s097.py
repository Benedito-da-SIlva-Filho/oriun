# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion
# MODULO: conferir_permissoes_s097.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-10-15 10:05 -03
# VERSAO: 1.0.0
# DESCRICAO: Lista toda rota /produtor/... SEM modulo registrado no porteiro
#            (essas ficam barradas para quem nao e Titular). Rodar na pasta
#            C:\orion, com o ambiente do projeto:  python conferir_permissoes_s097.py
#            Resultado esperado: "Nenhuma rota sem modulo."
# =========================================================
import re
from app import app
from backend.utils.permissoes import modulo_do_caminho

sem_modulo = []
total = 0
for regra in app.url_map.iter_rules():
    caminho = regra.rule
    if not caminho.startswith('/produtor/'):
        continue
    total += 1
    caminho_teste = re.sub(r'<[^>]+>', '1', caminho)
    if caminho == '/produtor/hub-novo/<slug>' or caminho == '/produtor/hub/<slug>':
        continue
    if modulo_do_caminho(caminho_teste) is None:
        sem_modulo.append(caminho)

print(f'{total} rotas /produtor/ conferidas.')
if sem_modulo:
    print('SEM MODULO (barradas para nao-Titular):')
    for c in sorted(set(sem_modulo)):
        print('  ', c)
else:
    print('Nenhuma rota sem modulo.')
