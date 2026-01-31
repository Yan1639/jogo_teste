import pygame
import os
import json
import random
from config import CHAO_Y, AREA_SEGURA_X, TEMPO_INVISIBILIDADE

textos_flutuantes = []
FONTES_CACHE = {}
TEXTURAS_CACHE = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_nome_arquivo(slot_id):
    return f"save_slot_{slot_id}.json"


def get_fonte(nome, tamanho, bold=False):
    """Obtém fonte do cache ou cria nova"""
    chave = (nome, tamanho, bold)
    if chave not in FONTES_CACHE:
        FONTES_CACHE[chave] = pygame.font.SysFont(nome, tamanho, bold=bold)
    return FONTES_CACHE[chave]

def carregar_textura(nome_arquivo, pasta="texturas"):
    """Carrega textura do cache ou do arquivo.
    pasta: subpasta dentro do projeto (agora padrão = 'texturas')
    Aceita nome sem extensão (tenta .png e .PNG).
    """
    if not nome_arquivo:
        return None

    base = os.path.basename(nome_arquivo)
    tentativas = [nome_arquivo]
    if "." not in base:
        tentativas = [nome_arquivo + ".png", nome_arquivo + ".PNG", nome_arquivo]

    for arq in tentativas:
        chave = (pasta, arq)
        if chave in TEXTURAS_CACHE:
            return TEXTURAS_CACHE[chave]

        caminho = os.path.join(BASE_DIR, pasta, arq) if pasta else os.path.join(BASE_DIR, arq)

        if os.path.exists(caminho):
            try:
                TEXTURAS_CACHE[chave] = pygame.image.load(caminho).convert_alpha()
                print(f"✓ Textura carregada: {pasta}\\{arq}")
            except Exception as e:
                print(f"✗ Erro ao carregar {pasta}\\{arq}: {e}")
                TEXTURAS_CACHE[chave] = None
            return TEXTURAS_CACHE[chave]

    print(f"✗ Arquivo não encontrado: {pasta}\\{tentativas[0]}")
    TEXTURAS_CACHE[(pasta, tentativas[0])] = None
    return None




def carregar_jogo(slot_id):
    if os.path.exists(get_nome_arquivo(slot_id)):
        try:
            with open(get_nome_arquivo(slot_id), 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def salvar_jogo(p, slot_id):
    dados_save = {
        'moedas_total': p['moedas_coletadas'],
        'xp': p['xp'],
        'level': p['level'],
        'status': p['status'],
        'espadas_compradas': p['espadas_compradas'],
        'espada_equipada_id': p['espada_equipada_id'],
        'espada_equipada_uuid': p.get('espada_equipada_uuid'),
        'pontos_disponiveis': p['pontos_disponiveis']
    }
    try:
        with open(get_nome_arquivo(slot_id), 'w') as f:
            json.dump(dados_save, f)
    except:
        pass


def gerar_encantamento():
    return random.randint(70, 130) / 100.0


def desenhar_texto(tela, texto, x, y, cor):
    """Helper para desenhar texto"""
    img = get_fonte("Verdana", 20).render(texto, True, cor)
    tela.blit(img, (x, y))


def ler_info_resumida_save(slot_id):
    dados = carregar_jogo(slot_id)
    if dados:
        return f"Nível: {dados.get('level', 1)} | Moedas: {dados.get('moedas_total', 0)}"
    return "Espaço Vazio - Novo Jogo"


def resetar_posicao_segura(p):
    p['rect'].x = AREA_SEGURA_X
    p['rect'].bottom = CHAO_Y
    p['v_vert'] = 0
    p['no_chao'] = True
    p['vida'] = p['vida_max']
    p['invisivel_timer'] = TEMPO_INVISIBILIDADE * 2
    p['game_over'] = False
    p['pulo_duplo_ativo'] = False

def adicionar_texto_dano(x, y, texto, cor, tamanho_extra=0, duracao=50, vy=-3.5, vx=None):
    if vx is None:
        vx = random.uniform(-1.5, 1.5)

    if isinstance(texto, (int, float)):
        texto_formatado = f"{texto:.2f}" if isinstance(texto, float) else str(int(texto))
    else:
        texto_formatado = str(texto)

    textos_flutuantes.append({
        'x': x, 'y': y,
        'val': texto_formatado,
        'timer': duracao,
        'vy': vy,
        'vx': vx,
        'cor': cor,
        'escala': 1.0
    })
