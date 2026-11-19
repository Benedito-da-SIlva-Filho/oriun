# -*- coding: utf-8 -*-
# =========================================================
# PROJETO: Orion
# PASTA: C:\orion\backend\utils
# MODULO: backend\utils\morte_fotos.py
# AUTOR: Benedito Silva Filho
# CRIADO EM: 2026-11-01 18:00 -03
# ATUALIZADO EM: 2026-11-01 18:00 -03
# VERSAO: 1.0.0
#
# DESCRICAO:
#     Apoio das fotos da Morte (tb_2022_morte_fotos): pasta de armazenamento, gravacao da imagem e remocao dos arquivos.
#     Os arquivos ficam numa pasta so (C:\orion\storage\morte), com o nome  <id_propriedade>_<id_saida_animal>_<ordem>_<codigo>.jpg ;
#     no banco fica so o nome (a tela nunca mostra o caminho). A imagem e conferida (tem que ser imagem de verdade), girada pela orientacao
#     do celular, reduzida a no maximo 1600 px e salva em JPEG; sem a biblioteca Pillow, so aceita JPEG como veio.
#     apagar_arquivos_das_fotos(): chamado pelo Desfazer da Morte (log_operacoes.py) e pela exclusao da foto.
#
#     v1.0.0: Sessao 111 (01/11/2026) - Criacao. REVERSAO: apagar este arquivo (e tirar a chamada do log_operacoes.py).
# =========================================================
import hashlib
import io
import os
import secrets

PASTA_FOTOS_MORTE = r'C:\orion\storage\morte'
LIMITE_BYTES_FOTO = 12 * 1024 * 1024     # 12 MB (foto de celular)
LADO_MAXIMO = 1600
MAXIMO_FOTOS_POR_ANIMAL = 2


def _caminho(nome):
    return os.path.join(PASTA_FOTOS_MORTE, os.path.basename(nome))


def preparar_imagem(dados):
    """
    Bytes enviados -> (bytes_jpeg, erro). Confere que e imagem de verdade.
    """
    if not dados:
        return None, 'Arquivo vazio.'
    if len(dados) > LIMITE_BYTES_FOTO:
        return None, 'Foto grande demais (máximo 12 MB).'
    try:
        from PIL import Image, ImageOps
    except ImportError:   # sem Pillow: so JPEG, como veio
        if dados[:3] == b'\xff\xd8\xff':
            return dados, None
        return None, 'Envie a foto em JPEG.'
    try:
        imagem = Image.open(io.BytesIO(dados))
        imagem.load()
    except Exception:
        return None, 'Não consegui ler a imagem. Envie uma foto em JPG ou PNG.'
    imagem = ImageOps.exif_transpose(imagem)
    if imagem.mode not in ('RGB', 'L'):
        imagem = imagem.convert('RGB')
    imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
    saida = io.BytesIO()
    imagem.save(saida, format='JPEG', quality=82, optimize=True)
    return saida.getvalue(), None


def gravar_arquivo(id_propriedade, id_saida_animal, ordem, bytes_jpeg):
    """Grava o JPEG na pasta e devolve (nome_do_arquivo, hash_sha256, tamanho)."""
    os.makedirs(PASTA_FOTOS_MORTE, exist_ok=True)
    nome = f'{int(id_propriedade)}_{int(id_saida_animal)}_{int(ordem)}_{secrets.token_hex(6)}.jpg'
    with open(_caminho(nome), 'wb') as f:
        f.write(bytes_jpeg)
    return nome, hashlib.sha256(bytes_jpeg).hexdigest(), len(bytes_jpeg)


def apagar_arquivo(nome):
    try:
        os.remove(_caminho(nome))
    except OSError:
        pass


def caminho_do_arquivo(nome):
    return _caminho(nome)


def apagar_arquivos_das_fotos(nomes):
    """Apaga os arquivos (nomes vindos do banco). Ignora o que ja nao existe."""
    for nome in nomes or []:
        if nome:
            apagar_arquivo(nome)

# =========================================================
# FIM DE ARQUIVO: backend\utils\morte_fotos.py
# =========================================================
