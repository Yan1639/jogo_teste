import pygame
import random
import math
from config import *
from utils import get_fonte, textos_flutuantes, desenhar_texto, ler_info_resumida_save, carregar_textura
from logic import obter_atributos_reais, ordenar_espadas_por_dps, combinar_3_espadas

CACHE_VINHETA = {}
CACHE_PARTICULAS = {}
MAX_CACHE_SIZE = 100
SURFACE_DASH_MOLDE = pygame.Surface((60, 90), pygame.SRCALPHA)
pygame.draw.rect(SURFACE_DASH_MOLDE, COR_DASH, (0, 0, 60, 90), border_radius=4)

TEXTURA_PARADO = None
TEXTURA_IDLE_SEM_ESPADA_FRAMES = None
TEXTURA_SACANDO_SWORD_FRAMES = None
TEXTURA_ANDANDO_SEM_ESPADA_FRAMES = None
TEXTURA_ATAQUE_FRAMES = None
TEXTURA_ESPADA_SOZINHA = None
CACHE_ESPADA_OVERLAY = {}  # (id(tex_atual), w, h) -> (sword_surface, (ox, oy))

TEXTURA_ATAQUE_1_FRAMES = None  # Primeiro ataque
TEXTURA_ATAQUE_2_FRAMES = None  # Segundo ataque
TEXTURA_ATAQUE_3_FRAMES = None  # Terceiro ataque

# === SAKURA (árvores + pétalas) ===
SAKURA_PETALAS = []
TEXTURA_ARVORE_FUNDO = None
CACHE_ARVORE_FUNDO = {}
CACHE_PETALAS_SPRITE = {}
MAX_PETALAS_TELA = 120
CORES_PETALAS = [(255, 195, 220), (255, 185, 214), (255, 170, 205)]

# posições das árvores no "mundo"
SAKURA_ARVORES = [
    {'x': 900,  'y': CHAO_Y, 'scale': 0.95},
    {'x': 2400, 'y': CHAO_Y, 'scale': 1.00},
    {'x': 4100, 'y': CHAO_Y, 'scale': 1.05},
]




def get_particula_surface(tamanho, cor):
    chave = (tamanho, cor)

    if chave not in CACHE_PARTICULAS:
        # Limpa cache se muito grande
        if len(CACHE_PARTICULAS) >= MAX_CACHE_SIZE:
            # Remove 20% mais antigos
            remover = list(CACHE_PARTICULAS.keys())[:MAX_CACHE_SIZE // 5]
            for k in remover:
                del CACHE_PARTICULAS[k]

        s = pygame.Surface((tamanho * 3, tamanho * 3), pygame.SRCALPHA)
        centro = tamanho * 3 // 2
        pygame.draw.circle(s, cor, (centro, centro), tamanho)
        CACHE_PARTICULAS[chave] = s

    return CACHE_PARTICULAS[chave]

def desenhar_ui_samurai(tela, p):
    """Desenha UI temática de samurai"""
    font_ui = get_fonte("Verdana", 18, bold=True)
    font_stats = get_fonte("Verdana", 16, bold=True)

    # === BARRA DE VIDA (Estilo Pergaminho) ===
    hp_x, hp_y = 30, 25
    hp_largura, hp_altura = 300, 38

    # Fundo (pergaminho envelhecido)
    pygame.draw.rect(tela, (60, 50, 40), (hp_x - 4, hp_y - 4, hp_largura + 8, hp_altura + 8), border_radius=8)
    pygame.draw.rect(tela, (40, 30, 20), (hp_x, hp_y, hp_largura, hp_altura), border_radius=6)

    # Preenchimento (vermelho degradê)
    hp_atual = (p['vida'] / p['vida_max']) * (hp_largura - 8)
    if hp_atual > 0:
        # Gradiente vermelho -> vermelho escuro
        for i in range(int(hp_atual)):
            alpha = 1 - (i / hp_largura) * 0.3
            cor_r = int(200 * alpha)
            pygame.draw.line(tela, (cor_r, 40, 40),
                             (hp_x + 4 + i, hp_y + 4),
                             (hp_x + 4 + i, hp_y + hp_altura - 4))

    # Borda externa (dourada)
    pygame.draw.rect(tela, (255, 215, 0), (hp_x - 4, hp_y - 4, hp_largura + 8, hp_altura + 8), 3, border_radius=8)

    # Símbolo samurai (Mon - brasão)
    pygame.draw.circle(tela, (139, 0, 0), (hp_x + 15, hp_y + hp_altura // 2), 12)
    pygame.draw.circle(tela, (255, 215, 0), (hp_x + 15, hp_y + hp_altura // 2), 12, 2)
    pygame.draw.circle(tela, (255, 215, 0), (hp_x + 15, hp_y + hp_altura // 2), 6)

    # Texto DENTRO da barra
    hp_texto = f"HP: {int(p['vida'])}/{int(p['vida_max'])}"
    txt_hp = font_stats.render(hp_texto, True, (255, 255, 255))
    # Sombra do texto
    txt_hp_sombra = font_stats.render(hp_texto, True, (0, 0, 0))
    tela.blit(txt_hp_sombra, (hp_x + 37, hp_y + 10))
    tela.blit(txt_hp, (hp_x + 35, hp_y + 8))

    # === BARRA DE XP (Estilo Espada) ===
    xp_x, xp_y = 30, 72
    xp_largura, xp_altura = 300, 24

    # Fundo
    pygame.draw.rect(tela, (30, 30, 40), (xp_x - 2, xp_y - 2, xp_largura + 4, xp_altura + 4), border_radius=6)
    pygame.draw.rect(tela, (20, 20, 30), (xp_x, xp_y, xp_largura, xp_altura), border_radius=4)

    # Preenchimento (azul brilhante)
    xp_atual = (p['xp'] / p['xp_proximo']) * (xp_largura - 4)
    if xp_atual > 0:
        # Gradiente azul
        for i in range(int(xp_atual)):
            alpha = 0.7 + (i / xp_largura) * 0.3
            cor_b = int(200 * alpha)
            pygame.draw.line(tela, (50, 150, cor_b),
                             (xp_x + 2 + i, xp_y + 2),
                             (xp_x + 2 + i, xp_y + xp_altura - 2))

    # Borda
    pygame.draw.rect(tela, (100, 150, 200), (xp_x - 2, xp_y - 2, xp_largura + 4, xp_altura + 4), 2, border_radius=6)

    # === INFO (LEVEL E MOEDAS) ===
    info_y = 105
    # Fundo para info
    pygame.draw.rect(tela, (20, 20, 30, 180), (25, info_y - 5, 310, 32), border_radius=6)

    lvl_txt = font_ui.render(f"NÍVEL {p['level']}", True, (255, 215, 0))
    tela.blit(lvl_txt, (30, info_y))

    moedas_txt = font_ui.render(f" {p['moedas_coletadas']}", True, (255, 215, 0))
    tela.blit(moedas_txt, (200, info_y))

def desenhar_fundo_samurai(tela):
    """Desenha fundo temático japonês"""
    # Gradiente de fundo
    desenhar_gradiente_ceu(tela)

    # Montanhas ao fundo (estilo ukiyo-e)
    for i, offset in enumerate([0, 150, 300]):
        cor_montanha = (20 + i * 15, 20 + i * 15, 35 + i * 15)
        pontos = [
            (0, 600 - offset),
            (400, 400 - offset),
            (800, 500 - offset),
            (1200, 350 - offset),
            (1600, 450 - offset),
            (1920, 550 - offset),
            (1920, 1080),
            (0, 1080)
        ]
        pygame.draw.polygon(tela, cor_montanha, pontos)

    # Lua cheia
    pygame.draw.circle(tela, (255, 250, 220), (1600, 200), 80)
    pygame.draw.circle(tela, (255, 255, 240), (1600, 200), 75)

    # Sakuras caindo (pétalas)
    for i in range(20):
        x = (i * 100 + pygame.time.get_ticks() // 10) % 1920
        y = (i * 50 + pygame.time.get_ticks() // 5) % 1080
        pygame.draw.ellipse(tela, (255, 200, 220, 180), (x, y, 8, 12))
        pygame.draw.ellipse(tela, (255, 180, 200, 180), (x + 4, y + 2, 8, 12))

def desenhar_gradiente_ceu(tela):
    for y in range(0, ALTURA, 4):
        p = y / ALTURA
        r = int(COR_CEU_TOPO[0] * (1 - p) + COR_CEU_BASE[0] * p)
        g = int(COR_CEU_TOPO[1] * (1 - p) + COR_CEU_BASE[1] * p)
        b = int(COR_CEU_TOPO[2] * (1 - p) + COR_CEU_BASE[2] * p)
        pygame.draw.rect(tela, (r, g, b), (0, y, LARGURA, 4))

def desenhar_icone_mochila(tela, x, y, tamanho, cor_base):
    """Desenha ícone de mochila pixelado"""
    s = pygame.Surface((tamanho, tamanho), pygame.SRCALPHA)

    # Corpo da mochila
    pygame.draw.rect(s, cor_base, (8, 12, 34, 30), border_radius=4)
    pygame.draw.rect(s, (max(0, cor_base[0] - 40), max(0, cor_base[1] - 40), max(0, cor_base[2] - 40)),
                     (8, 12, 34, 30), 2, border_radius=4)

    # Tampa
    pygame.draw.rect(s, cor_base, (10, 8, 30, 8), border_radius=2)

    # Bolso frontal
    pygame.draw.rect(s, (max(0, cor_base[0] - 30), max(0, cor_base[1] - 30), max(0, cor_base[2] - 30)),
                     (14, 18, 22, 18), border_radius=3)

    # Fecho
    pygame.draw.circle(s, (200, 180, 50), (25, 27), 3)

    # Alças
    pygame.draw.line(s, (80, 60, 40), (12, 10), (12, 4), 3)
    pygame.draw.line(s, (80, 60, 40), (38, 10), (38, 4), 3)

    tela.blit(s, (x, y))

def desenhar_mercado_overlay(tela, p):
    """Loja com visual de templo/dojo japonês"""
    cx, cy = LARGURA // 2, ALTURA // 2
    pos_x, pos_y = cx - 550, cy - 380

    # === FUNDO ESTILO PAPEL DE ARROZ ===
    s_fundo = pygame.Surface((1100, 760))
    s_fundo.fill((240, 235, 215))  # Bege papel de arroz
    tela.blit(s_fundo, (pos_x, pos_y))

    # Bordas de madeira
    pygame.draw.rect(tela, (80, 50, 30), (pos_x, pos_y, 1100, 760), 12, border_radius=5)
    pygame.draw.rect(tela, (139, 69, 19), (pos_x, pos_y, 1100, 760), 4, border_radius=5)

    # Cabeçalho com faixa vermelha
    pygame.draw.rect(tela, (139, 0, 0), (pos_x + 10, pos_y + 10, 1080, 80), border_radius=8)
    pygame.draw.rect(tela, (255, 215, 0), (pos_x + 10, pos_y + 10, 1080, 80), 3, border_radius=8)

    titulo = get_fonte("Impact", 42).render("FERREIRO TAKESHI", True, (255, 215, 0))
    tela.blit(titulo, (cx - titulo.get_width() // 2, pos_y + 30))

    # === DIVISÓRIA VERTICAL (Shoji - porta deslizante) ===
    div_x = pos_x + 480
    pygame.draw.rect(tela, (60, 40, 20), (div_x - 8, pos_y + 110, 16, 630))
    # Detalhes da grade
    for i in range(5):
        y_det = pos_y + 150 + (i * 120)
        pygame.draw.rect(tela, (100, 70, 40), (div_x - 6, y_det, 12, 4))

    # === LADO ESQUERDO: BAÚ GACHA ===
    # Título com caligrafia
    txt_bau = get_fonte("Impact", 28).render("BAU DA FORTUNA", True, (139, 0, 0))
    tela.blit(txt_bau, (pos_x + 180 - txt_bau.get_width() // 2, pos_y + 120))

    # Pedestal de madeira
    pygame.draw.rect(tela, (101, 67, 33), (pos_x + 80, pos_y + 450, 200, 30))
    pygame.draw.polygon(tela, (80, 50, 20), [
        (pos_x + 70, pos_y + 450),
        (pos_x + 290, pos_y + 450),
        (pos_x + 280, pos_y + 480),
        (pos_x + 80, pos_y + 480)
    ])

    # Baú japonês (Tansu)
    bau_rect = pygame.Rect(pos_x + 100, pos_y + 280, 160, 170)
    # Corpo do baú
    pygame.draw.rect(tela, (101, 67, 33), bau_rect, border_radius=8)
    pygame.draw.rect(tela, (139, 69, 19), bau_rect, 4, border_radius=8)

    # Detalhes metálicos dourados
    pygame.draw.rect(tela, (255, 215, 0), (bau_rect.x + 10, bau_rect.y + 60, 140, 4))
    pygame.draw.rect(tela, (255, 215, 0), (bau_rect.x + 10, bau_rect.y + 100, 140, 4))

    # Fechadura (Mon - símbolo do clã)
    pygame.draw.circle(tela, (255, 215, 0), (bau_rect.centerx, bau_rect.centery), 18)
    pygame.draw.circle(tela, (139, 0, 0), (bau_rect.centerx, bau_rect.centery), 12)
    pygame.draw.circle(tela, (255, 215, 0), (bau_rect.centerx, bau_rect.centery), 6)

    # Fitas vermelhas decorativas
    pygame.draw.line(tela, (200, 0, 0), (bau_rect.x + 20, bau_rect.bottom),
                     (bau_rect.x + 10, bau_rect.bottom + 30), 4)
    pygame.draw.line(tela, (200, 0, 0), (bau_rect.right - 20, bau_rect.bottom),
                     (bau_rect.right - 10, bau_rect.bottom + 30), 4)

    # Botão de abrir
    btn_sortear = pygame.Rect(pos_x + 70, pos_y + 520, 220, 70)
    cor_btn = (50, 150, 50) if p['moedas_coletadas'] >= PRECO_GACHA else (100, 50, 50)
    pygame.draw.rect(tela, cor_btn, btn_sortear, border_radius=8)
    pygame.draw.rect(tela, (255, 215, 0), btn_sortear, 3, border_radius=8)

    t_btn = get_fonte("Verdana", 22, bold=True).render(f"ABRIR ({PRECO_GACHA} Ryo)", True, (255, 255, 255))
    tela.blit(t_btn, (btn_sortear.centerx - t_btn.get_width() // 2,
                      btn_sortear.centery - t_btn.get_height() // 2))

    # Mensagem de resultado
    if p['msg_timer'] > 0:
        msg_surf = get_fonte("Verdana", 18, bold=True).render(p['msg_loja'], True, (139, 0, 0))
        # Fundo pergaminho
        pygame.draw.rect(tela, (240, 230, 200),
                         (pos_x + 180 - msg_surf.get_width() // 2 - 10, pos_y + 630,
                          msg_surf.get_width() + 20, 40), border_radius=5)
        tela.blit(msg_surf, (pos_x + 180 - msg_surf.get_width() // 2, pos_y + 640))

    # === LADO DIREITO: INVENTÁRIO ===
    txt_inv = get_fonte("Impact", 28).render("ARSENAL", True, (139, 0, 0))
    tela.blit(txt_inv, (pos_x + 750 - txt_inv.get_width() // 2, pos_y + 120))

    # Área de scroll com papel de arroz
    area_inv = pygame.Rect(pos_x + 510, pos_y + 170, 570, 550)
    pygame.draw.rect(tela, (250, 245, 230), area_inv, border_radius=5)
    pygame.draw.rect(tela, (139, 69, 19), area_inv, 2, border_radius=5)

    # Listar espadas
    contagem = {}
    for esp_obj in p['espadas_compradas']:
        contagem[esp_obj['id']] = contagem.get(esp_obj['id'], 0) + 1

    y_offset = 0
    for esp in ESPADAS_LOJA:
        if contagem.get(esp['id'], 0) > 0:
            rect_item = pygame.Rect(pos_x + 525, pos_y + 185 + y_offset, 540, 70)

            # Fundo da espada (papel envelhecido)
            cor_fundo = (220, 240, 220) if p['espada_equipada_id'] == esp['id'] else (245, 240, 230)
            pygame.draw.rect(tela, cor_fundo, rect_item, border_radius=6)
            pygame.draw.rect(tela, (139, 69, 19), rect_item, 2, border_radius=6)

            # Símbolo da raridade (círculo colorido)
            pygame.draw.circle(tela, esp['raridade_cor'], (rect_item.x + 20, rect_item.centery), 12)
            pygame.draw.circle(tela, (0, 0, 0), (rect_item.x + 20, rect_item.centery), 12, 2)

            # Nome da espada
            nome_render = get_fonte("Verdana", 16, bold=True).render(
                f"{esp['nome']} x{contagem[esp['id']]}", True, (40, 30, 20))
            tela.blit(nome_render, (rect_item.x + 45, rect_item.y + 12))

            # Stats
            stats_txt = f"ATK:{esp['forca']} | SPD:{esp['vel']}"
            stats_render = get_fonte("Verdana", 13).render(stats_txt, True, (100, 80, 60))
            tela.blit(stats_render, (rect_item.x + 45, rect_item.y + 38))

            # Botões com estilo japonês
            if p['espada_equipada_id'] != esp['id']:
                btn_eq = pygame.Rect(rect_item.right - 160, rect_item.y + 10, 70, 50)
                pygame.draw.rect(tela, (50, 100, 150), btn_eq, border_radius=5)
                pygame.draw.rect(tela, (255, 255, 255), btn_eq, 2, border_radius=5)
                txt_eq = get_fonte("Verdana", 13, bold=True).render("USAR", True, (255, 255, 255))
                tela.blit(txt_eq, (btn_eq.centerx - txt_eq.get_width() // 2,
                                   btn_eq.centery - txt_eq.get_height() // 2))
            else:
                equipado_txt = get_fonte("Verdana", 12, bold=True).render("EQUIPADO", True, (50, 150, 50))
                tela.blit(equipado_txt, (rect_item.right - 150, rect_item.centery - 6))

            # Botão vender
            btn_vender = pygame.Rect(rect_item.right - 80, rect_item.y + 10, 70, 50)
            pygame.draw.rect(tela, (150, 50, 50), btn_vender, border_radius=5)
            pygame.draw.rect(tela, (255, 255, 255), btn_vender, 2, border_radius=5)
            txt_venda = get_fonte("Verdana", 12, bold=True).render(f"{esp['preco_venda']}$", True, (255, 255, 255))
            tela.blit(txt_venda, (btn_vender.centerx - txt_venda.get_width() // 2,
                                  btn_vender.centery - txt_venda.get_height() // 2))

            y_offset += 80

def desenhar_cenario_loja(tela, off_x):
    """Desenha forja tradicional japonesa"""
    x_loja = 200 - off_x
    if x_loja < -300 or x_loja > LARGURA + 200:
        return  # Não desenha se estiver muito longe

    # === BASE DE PEDRA ===
    pygame.draw.rect(tela, (60, 60, 70), (x_loja - 120, CHAO_Y - 10, 240, 10))

    # === PAREDES DE MADEIRA ESCURA ===
    # Parede esquerda
    pygame.draw.rect(tela, (60, 40, 20), (x_loja - 120, CHAO_Y - 180, 20, 180))
    # Parede direita
    pygame.draw.rect(tela, (60, 40, 20), (x_loja + 100, CHAO_Y - 180, 20, 180))
    # Parede traseira
    pygame.draw.rect(tela, (40, 30, 15), (x_loja - 100, CHAO_Y - 180, 200, 20))

    # === TELHADO TRADICIONAL (YANE) ===
    # Camada inferior (mais escura)
    pontos_telhado_baixo = [
        (x_loja - 140, CHAO_Y - 180),
        (x_loja + 140, CHAO_Y - 180),
        (x_loja + 110, CHAO_Y - 220),
        (x_loja, CHAO_Y - 250),
        (x_loja - 110, CHAO_Y - 220)
    ]
    pygame.draw.polygon(tela, (100, 40, 40), pontos_telhado_baixo)

    # Camada superior (telhas vermelhas)
    pontos_telhado_cima = [
        (x_loja - 135, CHAO_Y - 185),
        (x_loja + 135, CHAO_Y - 185),
        (x_loja + 105, CHAO_Y - 223),
        (x_loja, CHAO_Y - 253),
        (x_loja - 105, CHAO_Y - 223)
    ]
    pygame.draw.polygon(tela, (139, 0, 0), pontos_telhado_cima)

    # Detalhes do telhado (linhas horizontais)
    for i in range(3):
        y_linha = CHAO_Y - 195 - (i * 20)
        largura = 120 - (i * 15)
        pygame.draw.line(tela, (180, 40, 40),
                         (x_loja - largura, y_linha),
                         (x_loja + largura, y_linha), 3)

    # Ponta do telhado (decoração dourada)
    pygame.draw.circle(tela, (255, 215, 0), (x_loja, CHAO_Y - 250), 8)
    pygame.draw.circle(tela, (255, 255, 100), (x_loja, CHAO_Y - 250), 5)

    # === PORTA SHOJI (porta deslizante) ===
    porta_x, porta_y = x_loja - 30, CHAO_Y - 120
    # Moldura da porta
    pygame.draw.rect(tela, (80, 60, 40), (porta_x, porta_y, 60, 120), border_radius=3)
    # Papel de arroz (interior)
    pygame.draw.rect(tela, (240, 230, 210), (porta_x + 5, porta_y + 5, 50, 110), border_radius=2)
    # Grade da porta (4 divisões)
    for i in range(1, 4):
        y_grade = porta_y + (i * 30)
        pygame.draw.line(tela, (80, 60, 40), (porta_x, y_grade), (porta_x + 60, y_grade), 2)
    # Divisão vertical central
    pygame.draw.line(tela, (80, 60, 40), (porta_x + 30, porta_y), (porta_x + 30, porta_y + 120), 2)
    # Puxador
    pygame.draw.circle(tela, (200, 180, 50), (porta_x + 15, porta_y + 60), 4)

    # === JANELA LATERAL ===
    janela_x = x_loja + 60
    janela_y = CHAO_Y - 140
    pygame.draw.rect(tela, (80, 60, 40), (janela_x, janela_y, 35, 50), border_radius=2)
    pygame.draw.rect(tela, (255, 200, 100), (janela_x + 3, janela_y + 3, 29, 44), border_radius=1)
    # Grade da janela
    pygame.draw.line(tela, (80, 60, 40), (janela_x, janela_y + 25), (janela_x + 35, janela_y + 25), 2)
    pygame.draw.line(tela, (80, 60, 40), (janela_x + 17, janela_y), (janela_x + 17, janela_y + 50), 2)

    # === BIGORNA E FERRAMENTAS ===
    # Bigorna (à esquerda da porta)
    bigorna_x = x_loja - 80
    pygame.draw.polygon(tela, (60, 60, 70), [
        (bigorna_x - 15, CHAO_Y - 30),
        (bigorna_x + 15, CHAO_Y - 30),
        (bigorna_x + 10, CHAO_Y - 50),
        (bigorna_x - 10, CHAO_Y - 50)
    ])
    pygame.draw.rect(tela, (70, 70, 80), (bigorna_x - 5, CHAO_Y - 30, 10, 30))

    # Martelo encostado
    pygame.draw.rect(tela, (100, 70, 40), (bigorna_x + 20, CHAO_Y - 60, 6, 40))
    pygame.draw.rect(tela, (80, 80, 90), (bigorna_x + 15, CHAO_Y - 65, 16, 10))

    # === FORNALHA (à direita) ===
    fornalha_x = x_loja + 70
    # Estrutura de pedra
    pygame.draw.rect(tela, (80, 70, 60), (fornalha_x - 20, CHAO_Y - 60, 40, 60))
    # Abertura com fogo
    pygame.draw.rect(tela, (40, 30, 25), (fornalha_x - 15, CHAO_Y - 50, 30, 35))
    # Efeito de fogo (animado com tempo)
    tempo = pygame.time.get_ticks()
    for i in range(3):
        offset_x = random.randint(-3, 3)
        offset_y = int(math.sin(tempo / 100 + i) * 5)
        cor_fogo = (255, random.randint(100, 200), 0) if i % 2 == 0 else (255, 150, 0)
        pygame.draw.circle(tela, cor_fogo,
                           (fornalha_x + offset_x, CHAO_Y - 35 + offset_y),
                           random.randint(4, 8))

    # === PLACA "FORJA" ===
    placa_y = CHAO_Y - 280
    # Fundo da placa (madeira envelhecida)
    pygame.draw.rect(tela, (100, 70, 40), (x_loja - 50, placa_y, 100, 40), border_radius=5)
    pygame.draw.rect(tela, (80, 50, 20), (x_loja - 50, placa_y, 100, 40), 3, border_radius=5)
    # Texto
    t_placa = get_fonte("Impact", 22, bold=True).render("FORJA", True, (255, 215, 0))
    tela.blit(t_placa, (x_loja - t_placa.get_width() // 2, placa_y + 8))
    # Subtexto
    t_sub = get_fonte("Verdana", 12, bold=True).render("[E] Abrir", True, (200, 180, 140))
    tela.blit(t_sub, (x_loja - t_sub.get_width() // 2, placa_y + 25))

    # === SUPORTE DA PLACA ===
    pygame.draw.line(tela, (80, 60, 40), (x_loja - 45, placa_y + 40), (x_loja - 45, placa_y + 60), 4)
    pygame.draw.line(tela, (80, 60, 40), (x_loja + 45, placa_y + 40), (x_loja + 45, placa_y + 60), 4)


def desenhar_menu_status_melhorado(tela, p, clicou_frame):
    """Versão melhorada do menu de status com scroll no inventário"""
    # Overlay de fundo
    s = pygame.Surface((LARGURA, ALTURA))
    s.set_alpha(220)
    s.fill((10, 10, 15))
    tela.blit(s, (0, 0))

    mouse_pos = pygame.mouse.get_pos()
    stats = obter_atributos_reais(p)

    # === TÍTULO ===
    txt_titulo = get_fonte("Impact", 60).render("STATUS DO SAMURAI", True, (255, 255, 255))
    tela.blit(txt_titulo, (LARGURA // 2 - txt_titulo.get_width() // 2, 50))

    # === COLUNA ESQUERDA: STATUS ===
    x_stats = 150
    y_stats = 200

    desenhar_texto(tela, f"NÍVEL: {p['level']}", x_stats, y_stats, (255, 215, 0))
    desenhar_texto(tela, f"XP: {p['xp']} / {p['xp_proximo']}", x_stats, y_stats + 40, (200, 200, 200))

    # Barra de Vida
    y_v = y_stats + 120
    desenhar_texto(tela, "VITALIDADE", x_stats, y_v - 30, (100, 255, 100))
    pygame.draw.rect(tela, (40, 40, 40), (x_stats, y_v, 400, 30))
    larg_v = (p['vida'] / p['vida_max']) * 400
    pygame.draw.rect(tela, (50, 200, 50), (x_stats, y_v, larg_v, 30))

    # Força Total
    y_f = y_stats + 220
    desenhar_texto(tela, f"FORÇA TOTAL: {int(stats['forca'])}", x_stats, y_f - 30, (255, 100, 100))
    pygame.draw.rect(tela, (40, 40, 40), (x_stats, y_f, 400, 30))
    larg_f = min((stats['forca'] / (50 + p['level'] * 10)) * 400, 400)
    pygame.draw.rect(tela, (200, 50, 50), (x_stats, y_f, larg_f, 30))

    # Attack Speed
    y_a = y_stats + 320
    max_visual_speed = 50.0
    min_visual_speed = 5.0
    porcentagem_speed = 1 - ((stats['atk_speed'] - min_visual_speed) / (max_visual_speed - min_visual_speed))
    porcentagem_speed = max(0, min(1, porcentagem_speed))

    desenhar_texto(tela, f"VELOCIDADE: {stats['atk_speed']:.1f} (Menor = Melhor)", x_stats, y_a - 30, (100, 150, 255))
    pygame.draw.rect(tela, (40, 40, 40), (x_stats, y_a, 400, 30))
    pygame.draw.rect(tela, (50, 150, 255), (x_stats, y_a, 400 * porcentagem_speed, 30))

    # Botões de Upgrade
    if desenhar_botao(tela, "UP FORÇA (1 PONTO)", x_stats, y_a + 80, 250, 40, (100, 30, 30), (150, 50, 50), "up_f",
                      mouse_pos, clicou_frame):
        if p['pontos_disponiveis'] > 0:
            p['status']['forca'] += 2
            p['pontos_disponiveis'] -= 1

    if desenhar_botao(tela, "UP AGILIDADE (1 PONTO)", x_stats, y_a + 130, 250, 40, (30, 30, 100), (50, 50, 150), "up_a",
                      mouse_pos, clicou_frame):
        if p['pontos_disponiveis'] > 0:
            p['status']['agilidade'] += 1
            p['pontos_disponiveis'] -= 1

    # === COLUNA DIREITA: INVENTÁRIO COM SCROLL ===
    x_inv = 700
    desenhar_texto(tela, "ARSENAL (Ordenado por DPS)", x_inv, 170, (200, 200, 255))
    desenhar_texto(tela, "DPS | ATK | Speed", x_inv, 195, (180, 180, 180))

    # Área de scroll
    area_scroll = pygame.Rect(x_inv - 10, 230, 820, 620)
    pygame.draw.rect(tela, (20, 20, 30, 150), area_scroll, border_radius=5)

    # Ordena espadas
    espadas_ordenadas = ordenar_espadas_por_dps(p)
    contagem = {}
    for e in p['espadas_compradas']:
        contagem[e['id']] = contagem.get(e['id'], 0) + 1

    # Sistema de scroll  ✅ (corrigido para dict)
    if 'scroll_inventario' not in p:
        p['scroll_inventario'] = 0

    max_visiveis = 8
    altura_item = 70
    total_itens = len(espadas_ordenadas)

    # Clamp do scroll (evita sair do range quando muda a quantidade de itens)
    max_scroll = max(0, total_itens - max_visiveis)
    p['scroll_inventario'] = max(0, min(p['scroll_inventario'], max_scroll))

    y_inicio = 240

    # Desenha apenas itens visíveis
    for i in range(p['scroll_inventario'], min(p['scroll_inventario'] + max_visiveis, total_itens)):
        item = espadas_ordenadas[i]
        y_item = y_inicio + ((i - p['scroll_inventario']) * altura_item)

        esp_obj = item['obj']
        dados_base = item['base']
        dps = item['dps']
        cor_rar = dados_base.get('raridade_cor', (255, 255, 255))

        p_enc = int(esp_obj.get('encantamento', 1.0) * 100)
        p_stk = int(esp_obj.get('stacks', 0.0) * 100)

        txt_principal = f"{dps:.1f} DPS | {dados_base['nome']}"
        txt_stats = f"ATK:{dados_base['forca']} | SPD:{dados_base['vel']} | [{p_enc}%] +{p_stk}%"

        # Verifica se esta espada ESPECÍFICA está equipada (por UUID)
        esta_equipada = esp_obj.get('uuid') == p.get('espada_equipada_uuid')

        # Destaque se equipada
        if esta_equipada:
            pygame.draw.rect(tela, (50, 50, 70), (x_inv - 10, y_item - 10, 800, 65), border_radius=5)
            badge = get_fonte("Verdana", 12, bold=True).render("EQUIPADA", True, (100, 255, 100))
            tela.blit(badge, (x_inv + 680, y_item + 5))

        nome_render = get_fonte("Verdana", 16, bold=True).render(txt_principal, True, cor_rar)
        stats_render = get_fonte("Verdana", 13).render(txt_stats, True, (180, 180, 180))

        tela.blit(nome_render, (x_inv, y_item))
        tela.blit(stats_render, (x_inv, y_item + 25))

        # Botão EQUIPAR
        if not esta_equipada:
            btn_eq = pygame.Rect(x_inv + 450, y_item, 100, 50)
            hover_eq = btn_eq.collidepoint(mouse_pos)
            cor_eq = (80, 80, 80) if hover_eq else (50, 50, 50)
            pygame.draw.rect(tela, cor_eq, btn_eq, border_radius=5)
            pygame.draw.rect(tela, (255, 255, 255), btn_eq, 2, border_radius=5)
            txt_eq = get_fonte("Verdana", 13, bold=True).render("USAR", True, (255, 255, 255))
            tela.blit(txt_eq, (btn_eq.centerx - txt_eq.get_width() // 2,
                               btn_eq.centery - txt_eq.get_height() // 2))

            if hover_eq and clicou_frame:
                p['espada_equipada_id'] = esp_obj['id']
                p['espada_equipada_uuid'] = esp_obj.get('uuid')
        else:
            equipado_txt = get_fonte("Verdana", 12, bold=True).render("EQUIPADA", True, (50, 150, 50))
            tela.blit(equipado_txt, (x_inv + 450, y_item + 20))

        # Botão COMBINAR
        if contagem[esp_obj['id']] >= 3:
            btn_comb = pygame.Rect(x_inv + 560, y_item, 90, 50)
            hover_comb = btn_comb.collidepoint(mouse_pos)
            cor_comb = (120, 40, 180) if hover_comb else (80, 20, 120)
            pygame.draw.rect(tela, cor_comb, btn_comb, border_radius=5)
            pygame.draw.rect(tela, (255, 255, 255), btn_comb, 2, border_radius=5)
            txt_comb = get_fonte("Verdana", 13, bold=True).render("x3", True, (255, 255, 255))
            tela.blit(txt_comb, (btn_comb.centerx - txt_comb.get_width() // 2,
                                 btn_comb.centery - txt_comb.get_height() // 2))

            if hover_comb and clicou_frame:
                if combinar_3_espadas(p, esp_obj['id']):
                    # Atualiza UUID se a espada combinada era a equipada
                    if esta_equipada:
                        p['espada_equipada_uuid'] = None
                        for e in p['espadas_compradas']:
                            if e['id'] == esp_obj['id']:
                                p['espada_equipada_uuid'] = e.get('uuid')
                                break
                    break

    # Indicador de scroll
    if total_itens > max_visiveis:
        # Seta para cima
        if p['scroll_inventario'] > 0:
            btn_up = pygame.Rect(x_inv + 700, 230, 50, 40)
            hover_up = btn_up.collidepoint(mouse_pos)
            cor_up = (80, 80, 80) if hover_up else (50, 50, 50)
            pygame.draw.rect(tela, cor_up, btn_up, border_radius=5)
            pygame.draw.rect(tela, (255, 255, 255), btn_up, 2, border_radius=5)
            txt_up = get_fonte("Verdana", 20, bold=True).render("↑", True, (255, 255, 255))
            tela.blit(txt_up, (btn_up.centerx - txt_up.get_width() // 2, btn_up.centery - txt_up.get_height() // 2))

            if hover_up and clicou_frame:
                p['scroll_inventario'] = max(0, p['scroll_inventario'] - 1)

        # Seta para baixo
        if p['scroll_inventario'] + max_visiveis < total_itens:
            btn_down = pygame.Rect(x_inv + 700, 810, 50, 40)
            hover_down = btn_down.collidepoint(mouse_pos)
            cor_down = (80, 80, 80) if hover_down else (50, 50, 50)
            pygame.draw.rect(tela, cor_down, btn_down, border_radius=5)
            pygame.draw.rect(tela, (255, 255, 255), btn_down, 2, border_radius=5)
            txt_down = get_fonte("Verdana", 20, bold=True).render("↓", True, (255, 255, 255))
            tela.blit(txt_down,
                      (btn_down.centerx - txt_down.get_width() // 2, btn_down.centery - txt_down.get_height() // 2))

            if hover_down and clicou_frame:
                p['scroll_inventario'] = min(total_itens - max_visiveis, p['scroll_inventario'] + 1)

        # Contador
        contador_txt = f"{p['scroll_inventario'] + 1}-{min(p['scroll_inventario'] + max_visiveis, total_itens)} / {total_itens}"
        contador = get_fonte("Verdana", 12).render(contador_txt, True, (180, 180, 180))
        tela.blit(contador, (x_inv + 680, 860))

    # Botão Fechar
    if desenhar_botao(tela, "FECHAR MENU", LARGURA // 2 - 100, ALTURA - 80, 200, 50, (150, 50, 50), (200, 70, 70),
                      "fechar", mouse_pos, clicou_frame):
        p['menu_aberto'] = False


def desenhar_menu_pause(tela, mouse_pos, clicou):
    s = pygame.Surface((LARGURA, ALTURA))
    s.set_alpha(150)
    s.fill((0, 0, 0))
    tela.blit(s, (0, 0))
    cx, cy = LARGURA // 2, ALTURA // 2
    pygame.draw.rect(tela, (40, 40, 60), (cx - 250, cy - 200, 500, 400), border_radius=15)
    pygame.draw.rect(tela, (255, 255, 255), (cx - 250, cy - 200, 500, 400), 3, border_radius=15)
    tela.blit(get_fonte("Impact", 60).render("PAUSADO", True, (255, 255, 255)), (cx - 110, cy - 150))

    desenhar_botao(tela, "VOLTAR AO JOGO", cx - 120, cy - 60, 240, 60, (50, 150, 50), (70, 200, 70), "resume",
                   mouse_pos, clicou)
    desenhar_botao(tela, "MENU PRINCIPAL", cx - 120, cy + 20, 240, 60, (50, 50, 150), (70, 70, 200), "menu", mouse_pos,
                   clicou)
    desenhar_botao(tela, "SAIR DO JOGO", cx - 120, cy + 100, 240, 60, (150, 50, 50), (200, 70, 70), "sair", mouse_pos,
                   clicou)


# SUBSTITUA APENAS A FUNÇÃO desenhar_jogo no seu interface.py

def desenhar_jogo(tela, p, inimigos, moedas, off_x, shake_y=0):
    """
    Versão atualizada com:
    - After-images do dash (fantasmas)
    - Screen shake suave
    - Camera lerp
    """

    tela_jogo = pygame.Surface((LARGURA, ALTURA))
    desenhar_fundo_parallax(tela_jogo, off_x)
    desenhar_cenario_loja(tela_jogo, off_x)

    pygame.draw.rect(tela_jogo, COR_CHAO, (0 - off_x, CHAO_Y, MAPA_LARGURA, 500))
    pygame.draw.rect(tela_jogo, COR_GRAMA, (0 - off_x, CHAO_Y, MAPA_LARGURA, 10))
    _desenhar_arvores_sakura_parallax(tela_jogo, off_x, fator=0.60)

    for plat in PLATAFORMAS:
        r = pygame.Rect(plat[0] - off_x, plat[1], plat[2], 20)
        pygame.draw.rect(tela_jogo, (60, 60, 70), r)
        pygame.draw.rect(tela_jogo, (40, 40, 50), r, 2)
        pygame.draw.rect(tela_jogo, (150, 150, 160), (r.x, r.y, r.width, 4))

    placa_x = 150 - off_x
    if placa_x > -100 and placa_x < LARGURA + 100:
        pygame.draw.rect(tela_jogo, (200, 150, 50), (placa_x, CHAO_Y - 80, 80, 60), border_radius=8)
        pygame.draw.rect(tela_jogo, (100, 70, 20), (placa_x, CHAO_Y - 80, 80, 60), 3, border_radius=8)
        t_placa = get_fonte("Verdana", 14, bold=True).render("SHOP [E]", True, (50, 30, 10))
        tela_jogo.blit(t_placa, (placa_x + 40 - t_placa.get_width() // 2, CHAO_Y - 60))

    # === FANTASMAS DO DASH (After-images) ===
    for fantasma in p['fantasmas_dash']:
        s_fantasma = pygame.Surface((60, 90), pygame.SRCALPHA)
        # Desenha silhueta do jogador
        pygame.draw.rect(s_fantasma, (100, 200, 255, fantasma['alpha']), (0, 0, 60, 90), border_radius=4)
        tela_jogo.blit(s_fantasma, (fantasma['x'] - off_x, fantasma['y']))

    # Rastro dash normal
    for r in p['rastro']:
        alpha = int(150 * (r['timer'] / 20))
        SURFACE_DASH_MOLDE.set_alpha(alpha)
        tela_jogo.blit(SURFACE_DASH_MOLDE, (r['x'] - off_x, r['y']))

    # Partículas
    for part in p['particulas_hit']:
        if part.get('tipo') == 'slash_kill':
            sx, sy = part['x'] - off_x, part['y']
            pygame.draw.line(tela_jogo, (255, 0, 0), (sx - 40, sy - 40), (sx + 40, sy + 40), 5)
            pygame.draw.line(tela_jogo, (200, 200, 200), (sx - 40, sy - 40), (sx + 40, sy + 40), 2)
        else:
            cor_part = part.get('cor', COR_DANO_DEALER)
            tamanho = part.get('size', 3)
            s = get_particula_surface(tamanho, cor_part)
            alpha = int(255 * (part['timer'] / 45))
            s_copia = s.copy()
            s_copia.set_alpha(alpha)
            centro = tamanho * 3 // 2
            pos_x = int(part['x'] - off_x) - centro
            pos_y = int(part['y']) - centro
            tela_jogo.blit(s_copia, (pos_x, pos_y))

    desenhar_personagem(tela_jogo, p, off_x)
    desenhar_ataque(tela_jogo, p, off_x)

    for i in inimigos:
        rx, ry = i['rect'].x - off_x, i['rect'].y
        cx_inim, cy_inim = rx + 35, ry + 45

        COR_CORPO = (80, 80, 90)
        COR_PELE_INIM = (220, 180, 140)

        if i['hit_flash'] > 0:
            COR_CORPO = (255, 255, 255)
        elif i['estado'] == 'pre_atk':
            COR_CORPO = COR_TELEGRAFO
        elif i['estado'] == 'atk':
            COR_CORPO = COR_INIMIGO_ATK

        # Pernas
        pygame.draw.line(tela_jogo, (60, 60, 70), (cx_inim - 5, cy_inim + 12), (cx_inim - 5, cy_inim + 30), 6)
        pygame.draw.line(tela_jogo, (60, 60, 70), (cx_inim + 5, cy_inim + 12), (cx_inim + 5, cy_inim + 30), 6)

        # Corpo
        pygame.draw.rect(tela_jogo, COR_CORPO, (cx_inim - 12, cy_inim - 10, 24, 25), border_radius=3)
        pygame.draw.ellipse(tela_jogo, COR_CORPO, (cx_inim - 18, cy_inim - 12, 14, 10))
        pygame.draw.ellipse(tela_jogo, COR_CORPO, (cx_inim + 4, cy_inim - 12, 14, 10))

        # Cabeça
        pygame.draw.circle(tela_jogo, (70, 70, 80), (cx_inim, cy_inim - 18), 10)
        pygame.draw.rect(tela_jogo, (40, 40, 50), (cx_inim - 8, cy_inim - 15, 16, 8))
        pygame.draw.circle(tela_jogo, (255, 50, 50), (cx_inim - 4, cy_inim - 13), 2)
        pygame.draw.circle(tela_jogo, (255, 50, 50), (cx_inim + 4, cy_inim - 13), 2)

        # Braço traseiro
        pygame.draw.line(tela_jogo, COR_CORPO, (cx_inim - 8, cy_inim - 5), (cx_inim - 15, cy_inim + 10), 5)

        # Braço com espada
        braco_x, braco_y = cx_inim + 8, cy_inim - 5
        mao_x, mao_y = cx_inim + (18 if i['dir'] == 1 else -18), cy_inim + 8
        pygame.draw.line(tela_jogo, COR_CORPO, (braco_x, braco_y), (mao_x, mao_y), 5)

        if i['estado'] in ['pre_atk', 'atk']:
            espada_base_x, espada_base_y = mao_x, mao_y
            if i['estado'] == 'pre_atk':
                espada_ponta_x = mao_x + (-30 if i['dir'] == 1 else 30)
                espada_ponta_y = mao_y - 25
            else:
                espada_ponta_x = mao_x + (35 if i['dir'] == 1 else -35)
                espada_ponta_y = mao_y - 10
                pontos_cone = [
                    (espada_base_x, espada_base_y),
                    (espada_ponta_x - 10, espada_ponta_y - 15),
                    (espada_ponta_x, espada_ponta_y),
                    (espada_ponta_x - 10, espada_ponta_y + 15)
                ]
                s_cone = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                pygame.draw.polygon(s_cone, (255, 100, 100, 80), pontos_cone)
                tela_jogo.blit(s_cone, (0, 0))

            pygame.draw.line(tela_jogo, (200, 200, 220), (espada_base_x, espada_base_y),
                             (espada_ponta_x, espada_ponta_y), 4)
            pygame.draw.line(tela_jogo, (255, 255, 255), (espada_base_x, espada_base_y),
                             (espada_ponta_x, espada_ponta_y), 1)

        pygame.draw.circle(tela_jogo, COR_PELE_INIM, (int(mao_x), int(mao_y)), 4)

        # Barra de vida
        barra_vida_largura = 70 * (i['vida'] / i['vida_max'])
        pygame.draw.rect(tela_jogo, (50, 255, 50), (rx, ry - 8, barra_vida_largura, 5))
        pygame.draw.rect(tela_jogo, (0, 0, 0), (rx, ry - 8, 70, 5), 1)

    for m in moedas:
        cx, cy = m.centerx - off_x, m.centery
        pygame.draw.circle(tela_jogo, COR_MOEDA_B, (cx, cy), 10)
        pygame.draw.circle(tela_jogo, COR_MOEDA_H, (cx, cy), 6)

    for txt in textos_flutuantes:
        tx, ty = txt['x'] - off_x, txt['y']
        scale_font = get_fonte("Verdana", int(20 * txt.get('escala', 1)), bold=True)
        lbl = scale_font.render(str(txt['val']), True, txt['cor'])
        lbl_s = scale_font.render(str(txt['val']), True, (0, 0, 0))
        tela_jogo.blit(lbl_s, (tx + 1, ty + 1))
        tela_jogo.blit(lbl, (tx, ty))

    desenhar_vinheta(tela_jogo)

    # Aplica shake Y (shake X já está em off_x)
    tela.blit(tela_jogo, (0, shake_y))

    desenhar_ui_samurai(tela, p)
    desenhar_vinheta(tela)

    if p['dash_cooldown'] > 0:
        pygame.draw.rect(tela, (100, 100, 100), (25, 125, 120, 8))
        pygame.draw.rect(tela, (100, 200, 255), (25, 125, 120 * (1 - p['dash_cooldown'] / COOLDOWN_DASH), 8))

    if p['parry_cooldown'] > 0:
        pygame.draw.rect(tela, (100, 100, 100), (25, 140, 60, 6))
        pygame.draw.rect(tela, COR_PARRY, (25, 140, 60 * (1 - p['parry_cooldown'] / 60), 6))

    c = (255, 255, 0) if p['pontos_disponiveis'] > 0 else (80, 60, 50)
    pygame.draw.rect(tela, c, p['btn_menu'], border_radius=5)
    pygame.draw.rect(tela, (255, 255, 255), p['btn_menu'], 2, border_radius=5)

    cor_mochila = (139, 90, 43) if p['pontos_disponiveis'] == 0 else (200, 140, 80)
    desenhar_icone_mochila(tela, p['btn_menu'].x + 2, p['btn_menu'].y + 2, 46, cor_mochila)

    if p['pontos_disponiveis'] > 0:
        aviso = get_fonte("Verdana", 18, bold=True).render("PONTOS!", True, (255, 255, 0))
        tela.blit(aviso, (p['btn_menu'].x + 60, p['btn_menu'].y + 15))

    if p['cinematic_timer'] > 0:
        altura_barra = 120
        pygame.draw.rect(tela, (0, 0, 0), (0, 0, LARGURA, altura_barra))
        pygame.draw.rect(tela, (0, 0, 0), (0, ALTURA - altura_barra, LARGURA, altura_barra))
        p['cinematic_timer'] -= 1

def desenhar_fps(tela, clock):
    """Mostra o FPS no canto superior direito com mudança de cor"""
    fps = int(clock.get_fps())

    # Muda a cor: Verde (bom), Amarelo (médio), Vermelho (ruim)
    if fps >= 50:
        cor = (0, 255, 0)
    elif fps >= 30:
        cor = (255, 255, 0)
    else:
        cor = (255, 0, 0)

    # Cria o texto usando sua função get_fonte existente
    txt_fps = get_fonte("Verdana", 20, bold=True).render(f"FPS: {fps}", True, cor)

    # Sombra preta para melhor leitura
    txt_sombra = get_fonte("Verdana", 20, bold=True).render(f"FPS: {fps}", True, (0, 0, 0))

    # Posição: Direita em cima (LARGURA - tamanho do texto - margem, margem y)
    pos_x = LARGURA - txt_fps.get_width() - 20
    pos_y = 20

    tela.blit(txt_sombra, (pos_x + 2, pos_y + 2))
    tela.blit(txt_fps, (pos_x, pos_y))

def desenhar_textos_flutuantes(tela, off_x):
    # Percorre a lista de trás para frente para poder remover itens sem erro
    for texto in textos_flutuantes[::-1]:
        texto['y'] -= 1.5  # Faz o texto subir (Animação)
        texto['timer'] -= 1  # Conta o tempo de vida

        # Define a fonte (Maior que a anterior)
        fonte_xp = get_fonte("Verdana", 24, bold=True)

        # Cor amarela/dourada para XP
        cor = (255, 215, 0)

        # Desenha sombra (para leitura melhor)
        txt_sombra = fonte_xp.render(texto['msg'], True, (0, 0, 0))
        tela.blit(txt_sombra, (texto['x'] - off_x + 2, texto['y'] + 2))

        # Desenha o texto principal
        txt_surf = fonte_xp.render(texto['msg'], True, cor)
        tela.blit(txt_surf, (texto['x'] - off_x, texto['y']))

        # Remove se o tempo acabar
        if texto['timer'] <= 0:
            textos_flutuantes.remove(texto)

def desenhar_botao(tela, texto, x, y, w, h, cor_base, cor_hover, acao=None, mouse_pos=None, clicou_flag=False):
    rect = pygame.Rect(x, y, w, h)
    hover = rect.collidepoint(mouse_pos)
    cor = cor_hover if hover else cor_base
    pygame.draw.rect(tela, (max(0, cor[0] - 30), max(0, cor[1] - 30), max(0, cor[2] - 30)), (x, y + 4, w, h),
                     border_radius=10)
    pygame.draw.rect(tela, cor, rect, border_radius=10)
    pygame.draw.rect(tela, (255, 255, 255), rect, 2, border_radius=10)
    t = get_fonte("Verdana", 24, bold=True).render(texto, True, (255, 255, 255))
    tela.blit(t, (x + (w - t.get_width()) // 2, y + (h - t.get_height()) // 2))

    if hover and clicou_flag and acao: return acao
    return None

def desenhar_menu_principal(tela, mouse_pos, clicou):
    desenhar_fundo_samurai(tela)  # ← MUDE ESTA LINHA

    cx = LARGURA // 2

    # Título com estilo oriental
    titulo = get_fonte("Impact", 120).render("RPG SAMURAI", True, (255, 215, 0))
    titulo_sombra = get_fonte("Impact", 120).render("RPG SAMURAI", True, (139, 0, 0))
    tela.blit(titulo_sombra, (cx - 302, 252))
    tela.blit(titulo, (cx - 300, 250))

    # Resto do código continua igual...
    if desenhar_botao(tela, "JOGAR", cx - 150, 500, 300, 80, (139, 0, 0), (180, 0, 0), "sel", mouse_pos, clicou):
        return "SELECAO_SAVE"
    if desenhar_botao(tela, "CONFIGURAÇÕES", cx - 150, 600, 300, 80, (50, 50, 150), (70, 70, 200), "cfg", mouse_pos,
                      clicou):
        return "CONFIG"
    if desenhar_botao(tela, "CONTROLES", cx - 150, 700, 300, 80, (150, 100, 50), (200, 140, 70), "ctrl", mouse_pos,
                      clicou):
        return "CONTROLES"
    if desenhar_botao(tela, "SAIR", cx - 150, 800, 300, 80, (150, 50, 50), (200, 70, 70), "sair", mouse_pos, clicou):
        return "SAIR"
    return "MENU"

def desenhar_selecao_save(tela, mouse_pos, clicou):
    desenhar_gradiente_ceu(tela)
    desenhar_vinheta(tela)
    cx = LARGURA // 2
    tela.blit(get_fonte("Verdana", 48, bold=True).render("SELECIONE UM SLOT", True, (255, 255, 255)),
              (cx - 250, 180))
    for i in range(1, 4):
        y = 300 + (i - 1) * 180
        pygame.draw.rect(tela, (40, 40, 50), (cx - 400, y, 800, 150), border_radius=10)
        tela.blit(get_fonte("Verdana", 28).render(ler_info_resumida_save(i), True, (200, 200, 200)),
                  (cx - 370, y + 80))
        if desenhar_botao(tela, f"JOGAR SLOT {i}", cx - 370, y + 25, 320, 60, (50, 100, 50), (70, 150, 70), i,
                          mouse_pos, clicou): return i
    if desenhar_botao(tela, "VOLTAR", 60, ALTURA - 120, 180, 60, (100, 50, 50), (150, 70, 70), "v", mouse_pos,
                      clicou): return "MENU"
    return "SELECAO_SAVE"

def desenhar_tela_config(tela, mouse_pos, clicou):
    desenhar_gradiente_ceu(tela)
    desenhar_vinheta(tela)
    cx = LARGURA // 2
    tela.blit(get_fonte("Verdana", 48, bold=True).render("CONFIGURAÇÕES", True, (255, 255, 255)),
              (cx - 240, 250))
    if desenhar_botao(tela, "VOLTAR", cx - 120, 700, 240, 70, (150, 50, 50), (200, 70, 70), "MENU", mouse_pos,
                      clicou): return "MENU"
    return "CONFIG"

def desenhar_tela_controles(tela, mouse_pos, clicou):
    desenhar_gradiente_ceu(tela)
    desenhar_vinheta(tela)
    cx = LARGURA // 2
    tela.blit(get_fonte("Verdana", 48, bold=True).render("CONTROLES", True, (255, 255, 255)), (cx - 180, 120))
    ctrls = [
        ("A / Esquerda", "Mover Esquerda"),
        ("D / Direita", "Mover Direita"),
        ("Espaço / W", "Pulo Duplo"),
        ("S + Click", "Ataque Aéreo (Pogo)"),
        ("Mouse Esq.", "Atacar / Combo"),
        ("Mouse Dir.", "Parry / Executar"),
        ("2x Tecla Dir.", "Dash"),
        ("E (Perto Loja)", "Abrir Loja"),
        ("E / Mochila", "Inventário"),
        ("R", "Renascer"),
        ("ESC", "Pausar / Voltar")
    ]
    f2 = get_fonte("Verdana", 24)
    for i, (k, a) in enumerate(ctrls):
        y = 220 + i * 62
        pygame.draw.rect(tela, (40, 40, 50), (cx - 450, y, 900, 56), border_radius=5)
        tela.blit(f2.render(k, True, (255, 215, 0)), (cx - 420, y + 14))
        tela.blit(f2.render(a, True, (255, 255, 255)), (cx + 60, y + 14))
    if desenhar_botao(tela, "VOLTAR", cx - 120, 900, 240, 70, (150, 50, 50), (200, 70, 70), "MENU", mouse_pos,
                      clicou): return "MENU"
    return "CONTROLES"

def desenhar_vinheta(tela):
    s_topo = pygame.Surface((LARGURA, 120), pygame.SRCALPHA)
    s_base = pygame.Surface((LARGURA, 120), pygame.SRCALPHA)
    for i in range(120):
        alpha = int(180 * (1 - i / 120))
        pygame.draw.line(s_topo, (0, 0, 0, alpha), (0, i), (LARGURA, i))
        pygame.draw.line(s_base, (0, 0, 0, alpha), (0, 120 - i), (LARGURA, 120 - i))
    tela.blit(s_topo, (0, 0))
    tela.blit(s_base, (0, ALTURA - 120))

def desenhar_fundo_parallax(tela, off_x):
    # 0) Céu (fixo)
    desenhar_gradiente_ceu(tela)

    # 1) Estrelas (bem distante = anda quase nada)
    for e in ESTRELAS_BG:
        x_tela = (e['x'] - off_x * 0.08) % LARGURA
        cor = (e['brilho'], e['brilho'], 255)
        pygame.draw.circle(tela, cor, (int(x_tela), e['y']), e['tam'])

    # 2) Lua (quase fixa)
    pygame.draw.circle(tela, (255, 250, 220), (1600, 200), 80)
    pygame.draw.circle(tela, (255, 255, 240), (1600, 200), 75)

    # 3) Montanhas distantes (anda pouco)
    _desenhar_montanhas_parallax(tela, off_x, fator=0.18, base_y=720, cor_base=(25, 25, 45), altura=220)

    # 4) Montanhas médias (anda médio)
    _desenhar_montanhas_parallax(tela, off_x, fator=0.35, base_y=820, cor_base=(35, 30, 55), altura=260)

    # 5) Névoa leve (dá clima)
    s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    s.fill((30, 25, 40, 35))
    tela.blit(s, (0, 0))


def _desenhar_arvores_sakura_parallax(tela, off_x, fator=0.60):
    """Desenha árvores usando sprite (arvore_fundo) e emite poucas pétalas/folhas."""
    tempo = pygame.time.get_ticks()

    for arv in SAKURA_ARVORES:
        x_tela = int(arv['x'] - off_x * fator)
        y_base = int(arv.get('y', CHAO_Y))
        sc = float(arv.get('scale', 1.0))

        if x_tela < -600 or x_tela > LARGURA + 600:
            continue

        img = _get_arvore_fundo_surface(sc)

        if img is None:
            continue

        x_draw = x_tela - img.get_width() // 2

        ARVORE_Y_OFFSET = 20
        y_draw = y_base - img.get_height() + ARVORE_Y_OFFSET
        tela.blit(img, (x_draw, y_draw))

        chance = 0.018 * sc
        if random.random() < chance:
            margem_x = int(img.get_width() * 0.12)
            x_min = x_draw + margem_x
            x_max = x_draw + img.get_width() - margem_x

            y_min = y_draw + int(img.get_height() * 0.18)
            y_max = y_draw + int(img.get_height() * 0.25)

            # ✅ CORREÇÃO: Converte coordenadas da tela para coordenadas do mundo
            spawn_x_mundo = random.uniform(x_min, x_max) + off_x * fator
            spawn_y = random.uniform(y_min, y_max)

            _spawn_petala_sakura(spawn_x_mundo, spawn_y, sc, raio=int(img.get_width() * 0.03))

        if random.random() < (0.006 * sc):
            # ✅ CORREÇÃO: Usa coordenadas do mundo (da árvore original)
            copa_x_mundo = arv['x']
            copa_y = y_draw + int(img.get_height() * 0.25)
            raio = int(img.get_width() * 0.22)
            _spawn_petala_sakura(copa_x_mundo, copa_y, sc, raio)

    # ✅ CORREÇÃO: Passa off_x para a função
    _atualizar_desenhar_petalas(tela, off_x)


def _desenhar_montanhas_parallax(tela, off_x, fator, base_y, cor_base, altura):
    # “tile” horizontal: desenha 2 vezes pra cobrir a tela toda
    shift = -(off_x * fator) % LARGURA

    for k in (-1, 0, 1):
        x0 = int(k * LARGURA + shift)

        pontos = [
            (x0 + 0,      base_y),
            (x0 + 300,    base_y - altura * 0.6),
            (x0 + 650,    base_y - altura * 0.25),
            (x0 + 980,    base_y - altura * 0.75),
            (x0 + 1320,   base_y - altura * 0.35),
            (x0 + 1920,   base_y - altura * 0.55),
            (x0 + 1920,   ALTURA),
            (x0 + 0,      ALTURA),
        ]
        pygame.draw.polygon(tela, cor_base, pontos)

def _get_arvore_fundo_surface(sc: float):
    """Carrega e devolve a arvore_fundo escalada (pixel art: usa scale, não smoothscale)."""
    global TEXTURA_ARVORE_FUNDO

    if TEXTURA_ARVORE_FUNDO is None:
        # agora tudo está em /texturas
        TEXTURA_ARVORE_FUNDO = carregar_textura("arvore_fundo", pasta="texturas")
        if TEXTURA_ARVORE_FUNDO is None:
            TEXTURA_ARVORE_FUNDO = carregar_textura("arvore_fundo.png", pasta="texturas")

    if TEXTURA_ARVORE_FUNDO is None:
        return None

    chave = round(sc, 2)
    if chave not in CACHE_ARVORE_FUNDO:
        w0, h0 = TEXTURA_ARVORE_FUNDO.get_width(), TEXTURA_ARVORE_FUNDO.get_height()
        w = max(1, int(w0 * sc))
        h = max(1, int(h0 * sc))
        CACHE_ARVORE_FUNDO[chave] = pygame.transform.scale(TEXTURA_ARVORE_FUNDO, (w, h))

    return CACHE_ARVORE_FUNDO[chave]

def _get_petala_sprite(tam: int, cor_base):
    """Cria uma petala bonitinha com alpha (cache)."""
    chave = (tam, cor_base)
    if chave not in CACHE_PETALAS_SPRITE:
        if len(CACHE_PETALAS_SPRITE) > 80:
            CACHE_PETALAS_SPRITE.clear()

        w = tam * 2
        h = int(tam * 2.2)
        s = pygame.Surface((w, h), pygame.SRCALPHA)

        # corpo
        pygame.draw.ellipse(s, (*cor_base, 190), (int(w*0.20), int(h*0.25), int(w*0.65), int(h*0.70)))
        # sombra
        pygame.draw.ellipse(s, (cor_base[0]-10, cor_base[1]-20, cor_base[2]-10, 90),
                           (int(w*0.35), int(h*0.55), int(w*0.55), int(h*0.50)))
        # brilho
        pygame.draw.ellipse(s, (255, 255, 255, 70), (int(w*0.35), int(h*0.35), int(w*0.22), int(h*0.35)))

        CACHE_PETALAS_SPRITE[chave] = s

    return CACHE_PETALAS_SPRITE[chave]



def _desenhar_uma_sakura(tela, x, y_base, sc, tempo):
    """Árvore simples estilizada (sem sprite), com copa rosa e tronco"""
    # Tronco
    tronco_w = int(22 * sc)
    tronco_h = int(160 * sc)
    tronco_x = x - tronco_w // 2
    tronco_y = y_base - tronco_h
    pygame.draw.rect(tela, (85, 55, 35), (tronco_x, tronco_y, tronco_w, tronco_h), border_radius=6)

    # Galhos (simples)
    pygame.draw.line(tela, (85, 55, 35), (x, tronco_y + int(50 * sc)), (x - int(60 * sc), tronco_y + int(20 * sc)), 6)
    pygame.draw.line(tela, (85, 55, 35), (x, tronco_y + int(45 * sc)), (x + int(70 * sc), tronco_y + int(10 * sc)), 6)

    # Copa (bolhas rosas com leve "balanço")
    sway = int((math.sin(tempo / 500) * 6) * sc)
    cx = x + sway
    cy = tronco_y - int(20 * sc)

    for (dx, dy, r, cor) in [
        (-70,  10, 70, (255, 175, 205)),
        (  0, -10, 85, (255, 185, 215)),
        ( 75,  15, 65, (255, 170, 205)),
        (-20,  55, 60, (255, 165, 200)),
        ( 35,  55, 55, (255, 160, 195)),
    ]:
        pygame.draw.circle(tela, cor, (int(cx + dx * sc), int(cy + dy * sc)), int(r * sc))

    # brilho leve na copa (dá volume)
    pygame.draw.circle(tela, (255, 210, 230), (int(cx - 20 * sc), int(cy - 35 * sc)), int(35 * sc))


def _spawn_petala_sakura(x_copa, y_copa, sc, raio):
    """Cria 1 pétala/folha saindo da copa."""
    if len(SAKURA_PETALAS) >= MAX_PETALAS_TELA:
        return

    cor = random.choice(CORES_PETALAS)
    tam = max(6, int(random.randint(8, 13) * (0.85 + sc * 0.10)))

    # mais lento que antes
    vx = random.uniform(-0.12, 0.22) * sc
    vy = random.uniform(0.35, 0.85) * sc

    life_max = random.randint(260, 420)

    SAKURA_PETALAS.append({
        'x': float(x_copa + random.uniform(-raio, raio)),
        'y': float(y_copa + random.uniform(-raio * 0.35, raio * 0.10)),
        'vx': float(vx),
        'vy': random.uniform(1.1, 1.5) * sc,
        'rot': random.uniform(0, 360),
        'rot_spd': random.uniform(-1.8, 1.8),
        'amp': random.uniform(0.4, 1.2),
        'freq': random.uniform(0.004, 0.010),
        'life': life_max,
        'life_max': life_max,
        'tam': tam,
        'cor': cor,
        'alpha0': random.randint(210, 255),
    })

def _atualizar_desenhar_petalas(tela, off_x, fator_parallax=0.60):
    """CORRIGIDO: Pétalas agora usam o mesmo parallax das árvores"""
    for p in SAKURA_PETALAS[:]:
        p['life'] -= 1
        if p['life'] <= 0 or p['y'] > ALTURA + 120:
            SAKURA_PETALAS.remove(p)
            continue

        # movimento (coordenadas do mundo)
        p['x'] += p['vx']
        p['y'] += p['vy']

        # --- COLISÃO COM O CHÃO ---
        chao = CHAO_Y - 2
        if p['y'] >= chao:
            p['y'] = chao
            SAKURA_PETALAS.remove(p)
            continue

        p['rot'] += p['rot_spd']

        # fade suave
        vida_ratio = p['life'] / p['life_max']
        fade = 0.35 + 0.65 * (vida_ratio ** 0.35)
        alpha = int(p['alpha0'] * fade)

        if alpha < 90:
            alpha = 90

        sprite = _get_petala_sprite(p['tam'], p['cor'])
        spr_rot = pygame.transform.rotate(sprite, p['rot'])
        spr_rot.set_alpha(alpha)

        # ✅ CORREÇÃO: Usa o mesmo parallax das árvores (0.60)
        x_tela = int(p['x'] - off_x * fator_parallax)
        tela.blit(spr_rot, (x_tela, int(p['y'])))


def desenhar_personagem(tela, p, off_x):
    """Desenha personagem com animações suaves e separadas por combo."""
    if p.get('invisivel_timer', 0) > 0 and (p['invisivel_timer'] // 5) % 2 == 0:
        return

    rect = p['rect']
    dir_lado = p.get('direcao', 1)
    x_centro = rect.centerx - off_x

    # Inicializa controle de animação
    if 'anim_frame_atual' not in p:
        p['anim_frame_atual'] = 0
        p['anim_timer'] = 0
        p['anim_estado_anterior'] = None

    def _desenhar_sombra():
        s_sombra = pygame.Surface((44, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(s_sombra, (0, 0, 0, 110), (0, 0, 44, 12))
        tela.blit(s_sombra, (int(x_centro - 22), int(rect.bottom - 6)))

    def _blit_textura(tex, flip_horizontal=False, overlay_sword=False, sword_anchor=None):
        global TEXTURA_ESPADA_SOZINHA, CACHE_ESPADA_OVERLAY

        if tex is None:
            return False

        tex_atual = tex
        if flip_horizontal:
            tex_atual = pygame.transform.flip(tex_atual, True, False)

        _desenhar_sombra()

        x_draw = int(x_centro - tex_atual.get_width() // 2)
        y_draw = int(rect.bottom - tex_atual.get_height())

        # 1) desenha o personagem
        tela.blit(tex_atual, (x_draw, y_draw))

        # 2) overlay da espada (só quando pedido)
        if overlay_sword and TEXTURA_ESPADA_SOZINHA:

            # === OPÇÃO 1: ÂNCORA FIXA (idle) ===
            if sword_anchor is not None:
                ox, oy, escala = sword_anchor

                esp = TEXTURA_ESPADA_SOZINHA
                if flip_horizontal:
                    esp = pygame.transform.flip(esp, True, False)

                sw, sh = esp.get_width(), esp.get_height()
                esp_s = pygame.transform.smoothscale(
                    esp, (int(sw * escala), int(sh * escala))
                )

                tela.blit(esp_s, (x_draw + ox, y_draw + oy))
                return True

            # === CASO CONTRÁRIO: continua usando o modo automático ===
            # (não mexa no código automático que você já tem abaixo)

        return True

    # === SACANDO / GUARDANDO ESPADA ===
    if p.get('estado_espada') in ('sacando', 'guardando') and TEXTURA_SACANDO_SWORD_FRAMES:
        frames = TEXTURA_SACANDO_SWORD_FRAMES
        estado = p.get('estado_espada')
        duracao = int(p.get('duracao_sacar', 15)) if estado == 'sacando' else int(p.get('duracao_guardar', 30))
        duracao = max(1, duracao)
        timer = p.get('timer_espada', duracao)
        progresso = 1.0 - (float(timer) / duracao)
        progresso = max(0.0, min(1.0, progresso))
        n = len(frames)
        idx = int(progresso * (n - 1))
        if estado == 'guardando':
            idx = (n - 1) - idx
        _blit_textura(frames[idx], flip_horizontal=(dir_lado == -1))
        return

    # === ATACANDO (COM SEPARAÇÃO POR COMBO) ===
    if p.get('estado_espada') == 'pronta' and p.get('atacando', 0) > 0:
        # ✅ ESCOLHE A ANIMAÇÃO BASEADO NO COMBO_STEP
        combo_step = p.get('combo_step', 0)

        if combo_step == 0 and TEXTURA_ATAQUE_1_FRAMES:
            frames_ataque = TEXTURA_ATAQUE_1_FRAMES
        elif combo_step == 1 and TEXTURA_ATAQUE_2_FRAMES:
            frames_ataque = TEXTURA_ATAQUE_2_FRAMES
        elif combo_step == 2 and TEXTURA_ATAQUE_3_FRAMES:
            frames_ataque = TEXTURA_ATAQUE_3_FRAMES
        else:
            # Fallback: usa ataque 1
            frames_ataque = TEXTURA_ATAQUE_1_FRAMES

        if frames_ataque:
            n = len(frames_ataque)

            atk_total = int(p.get('atk_total', 0))
            if atk_total <= 0:
                atk_total = max(1, int(p.get('atacando', 1)))

            restante = max(0, int(p.get('atacando', 0)))
            progresso = 1.0 - (restante / atk_total)
            progresso = max(0.0, min(1.0, progresso))

            idx = int(progresso * (n - 1))
            idx = max(0, min(idx, n - 1))

            _blit_textura(frames_ataque[idx], flip_horizontal=(dir_lado == -1), overlay_sword=True)
            return

    # === SISTEMA DE ANIMAÇÃO SUAVE PARA IDLE/ANDAR ===
    estado_atual = None
    frames_atuais = None
    velocidade_frame = 0

    # 1) ANDANDO SEM ESPADA
    if (TEXTURA_ANDANDO_SEM_ESPADA_FRAMES and
            p.get('estado_espada') == 'guardada' and
            p.get('atacando', 0) <= 0 and
            p.get('andando', False) and
            p.get('no_chao', False) and
            abs(float(p.get('v_vert', 0))) < 0.1):

        estado_atual = 'andando_sem_espada'
        frames_atuais = TEXTURA_ANDANDO_SEM_ESPADA_FRAMES
        velocidade_frame = 8

    # 2) PARADO COM ESPADA
    elif (TEXTURA_PARADO and
          p.get('estado_espada') == 'pronta' and
          p.get('atacando', 0) <= 0 and
          not p.get('andando', False) and
          p.get('no_chao', False)):

        estado_atual = 'parado_com_espada'
        frames_atuais = TEXTURA_PARADO
        velocidade_frame = 10

    # 3) IDLE SEM ESPADA
    elif (TEXTURA_IDLE_SEM_ESPADA_FRAMES and
          p.get('estado_espada') == 'guardada' and
          p.get('atacando', 0) <= 0 and
          not p.get('andando', False) and
          p.get('no_chao', False)):

        estado_atual = 'idle_sem_espada'
        frames_atuais = TEXTURA_IDLE_SEM_ESPADA_FRAMES
        velocidade_frame = 10

    # Reset ao trocar de estado
    if estado_atual != p['anim_estado_anterior']:
        p['anim_frame_atual'] = 0
        p['anim_timer'] = 0
        p['anim_estado_anterior'] = estado_atual

    # Atualiza frame
    if frames_atuais and velocidade_frame > 0:
        p['anim_timer'] += 1
        if p['anim_timer'] >= velocidade_frame:
            p['anim_timer'] = 0
            p['anim_frame_atual'] = (p['anim_frame_atual'] + 1) % len(frames_atuais)

        frame_atual = frames_atuais[p['anim_frame_atual']]

        if estado_atual == 'andando_sem_espada':
            com_espada = (p.get('estado_espada') == 'pronta')
            # âncora fixa para idle com espada (ajuste uma vez e pronto)
            SWORD_IDLE_ANCHOR = (48, 54, 0.85)  # (ox, oy, escala)

            _blit_textura(
                frame_atual,
                flip_horizontal=(dir_lado == -1),
                overlay_sword=True,
                sword_anchor=SWORD_IDLE_ANCHOR
            )


        else:
            com_espada = (p.get('estado_espada') == 'pronta')
            # âncora fixa para idle com espada (ajuste uma vez e pronto)
            SWORD_IDLE_ANCHOR = (48, 54, 0.85)  # (ox, oy, escala)

            _blit_textura(
                frame_atual,
                flip_horizontal=(dir_lado == -1),
                overlay_sword=True,
                sword_anchor=SWORD_IDLE_ANCHOR
            )

        return

    # === FALLBACK ===
    x_real = rect.x - off_x
    y_real = rect.y
    cx = x_real + rect.w // 2
    cy = y_real + rect.h // 2
    _desenhar_sombra()
    cor_roupa = (40, 40, 55)
    cor_cinto = (120, 70, 30)
    cor_pele = (255, 220, 180)
    pygame.draw.line(tela, (30, 30, 40), (cx - 10, y_real + rect.h - 5), (cx - 10, y_real + rect.h + 18), 6)
    pygame.draw.line(tela, (30, 30, 40), (cx + 10, y_real + rect.h - 5), (cx + 10, y_real + rect.h + 18), 6)
    pygame.draw.rect(tela, cor_roupa, (cx - 16, cy - 18, 32, 34), border_radius=4)
    pygame.draw.rect(tela, (20, 20, 30), (cx - 16, cy - 18, 32, 34), 2, border_radius=4)
    pygame.draw.rect(tela, cor_cinto, (cx - 16, cy + 2, 32, 6), border_radius=2)
    pygame.draw.circle(tela, cor_pele, (cx, cy - 30), 10)
    pygame.draw.circle(tela, (0, 0, 0), (cx - 3, cy - 32), 2)
    pygame.draw.circle(tela, (0, 0, 0), (cx + 3, cy - 32), 2)

def desenhar_ataque(tela, p, off_x):
    if p['atacando'] <= 0: return
    stats = obter_atributos_reais(p)
    progresso = (stats['atk_speed'] - p['atacando']) / stats['atk_speed']

    # Centro do corpo (Base para o ombro/pivô)
    x_real, y_real = p['rect'].x - off_x, p['rect'].y
    cx, cy = x_real + 30, y_real + 40  # Altura do peito/ombro

    # Cores
    COR_PELE = (255, 220, 180)
    if p['parry_timer'] > 0: COR_PELE = (255, 255, 255)

    # --- 1. ATAQUE PARA BAIXO (Pogo) ---
    if p['ataque_baixo']:
        # Mão fica centralizada embaixo do corpo
        mao_x, mao_y = cx, cy + 40
        # Espada para baixo
        ponta_x, ponta_y = cx, mao_y + 80

        # Rastro triangular
        pontos = [(mao_x, mao_y), (mao_x - 25, ponta_y), (mao_x + 25, ponta_y)]
        s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*stats['cor_rastro'], 150), pontos)
        tela.blit(s, (0, 0))

        # Espada e Mão
        pygame.draw.line(tela, (220, 220, 220), (mao_x, mao_y), (ponta_x, ponta_y), 5)
        pygame.draw.circle(tela, COR_PELE, (int(mao_x), int(mao_y)), 6)
        return

    # --- 2. ATAQUES NORMAIS ---
    step = p['combo_step']
    is_dashing = p['dash_timer'] > 0
    ang_ini = 0

    # Comprimento da espada (Reduzido para 110)
    comp_espada = 110
    dist_mao = 35  # Distância do ombro até a mão (comprimento do braço)

    if is_dashing:
        ang_ini = 0 if p['direcao'] == 1 else 180
        comp_espada = 120
        amp = 0
        ang_atual = ang_ini
    else:
        if step == 0:
            # Combo 1: Saque da bainha (De baixo/trás para cima/frente)
            ang_ini = -140 if p['direcao'] == 1 else 320
            amp = 160
        elif step == 1:
            # Combo 2: Corte de volta (Horizontal)
            ang_ini = 170 if p['direcao'] == 1 else 10
            amp = -200
        else:
            # Giro
            ang_ini = 0 if p['direcao'] == 1 else 180
            amp = 360 * progresso * (1 if p['direcao'] == 1 else -1)

    # Calcula o ângulo atual baseado no progresso
    if not is_dashing and step != 2:
        ang_atual = ang_ini + (amp * progresso * (1 if p['direcao'] == 1 else -1))
    elif step == 2:
        ang_atual = ang_ini + amp

    rad = math.radians(ang_atual)

    # --- CÁLCULO DAS POSIÇÕES ---
    # A mão gira em torno do ombro (cx, cy)
    mao_x = cx + dist_mao * math.cos(rad)
    mao_y = cy + dist_mao * math.sin(rad)

    # A ponta da espada continua na mesma linha, mais longe
    ponta_x = cx + comp_espada * math.cos(rad)
    ponta_y = cy + comp_espada * math.sin(rad)

    # --- DESENHO DO RASTRO (SLASH) ---
    pontos = [(mao_x, mao_y)]

    if step == 2 and not is_dashing:
        # Giro 360
        s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        rect_arc = pygame.Rect(cx - 90, cy - 50, 180, 100)
        pygame.draw.ellipse(s, (*stats['cor_rastro'], 100), rect_arc, 10)
        tela.blit(s, (0, 0))
    elif not is_dashing:
        # Rastro Curvo
        tamanho_rastro = 40
        ang_tail_start = ang_atual - (tamanho_rastro * (1 if step == 0 else -1) * (1 if p['direcao'] == 1 else -1))

        qtd_pontos = 8
        for i in range(qtd_pontos + 1):
            fator = i / qtd_pontos
            a = ang_tail_start + (ang_atual - ang_tail_start) * fator
            r_rad = math.radians(a)
            # Rastro segue a ponta
            pontos.append((cx + comp_espada * math.cos(r_rad), cy + comp_espada * math.sin(r_rad)))
    else:
        # Rastro Dash (Reto)
        pontos.append((ponta_x, ponta_y - 20))
        pontos.append((ponta_x, ponta_y + 20))

    pontos.append((ponta_x, ponta_y))  # Fecha na ponta atual

    # Desenha polígono do rastro
    if step != 2 and len(pontos) >= 3:
        s = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        cor_base = COR_CRITICO if is_dashing else stats['cor_rastro']
        pygame.draw.polygon(s, (*cor_base, 120), pontos)
        tela.blit(s, (0, 0))

    # --- DESENHO DA ARMA E MÃO ---
    # 1. Lâmina da espada (Linha Prata)
    pygame.draw.line(tela, (220, 220, 220), (mao_x, mao_y), (ponta_x, ponta_y), 4)

    # 2. A Mão (Círculo na base da espada)
    pygame.draw.circle(tela, COR_PELE, (int(mao_x), int(mao_y)), 6)

def desenhar_barra_status(tela, x, y, largura, valor, valor_max, cor, label):
    # Desenha o fundo da barra
    pygame.draw.rect(tela, (30, 30, 30), (x, y, largura, 25))
    # Calcula preenchimento
    preenchimento = (valor / valor_max) * largura
    pygame.draw.rect(tela, cor, (x, y, preenchimento, 25))
    # Texto
    img = get_fonte("Arial", 20).render(f"{label}: {valor:.1f}/{valor_max}", True, (255, 255, 255))
    tela.blit(img, (x, y - 22))