import random

# --- CONSTANTES GERAIS - FULL HD NATIVO ---
LARGURA = 1920
ALTURA = 1080

MAPA_LARGURA, MAPA_ALTURA = 6000, 2000
CHAO_Y = 900
FPS = 60
ATAQUE_FRAME_MS = 100

# --- PALETA DE CORES ---
COR_CEU_TOPO = (10, 10, 25)
COR_CEU_BASE = (40, 20, 50)
COR_CHAO = (20, 15, 25)
COR_GRAMA = (30, 100, 50)
COR_DASH = (100, 200, 255)

# --- CORES DE RARIDADE ---
RAR_COMUM = (180, 180, 180)
RAR_INCOMUM = (50, 255, 50)
RAR_RARO = (50, 150, 255)
RAR_EPICO = (180, 80, 255)
RAR_LENDARIO = (255, 215, 0)
RAR_SUBLIME = (255, 20, 20)

COR_INIMIGO = (60, 20, 20)
COR_INIMIGO_AGRO = (200, 50, 50)
COR_TELEGRAFO = (255, 100, 0)
COR_INIMIGO_ATK = (255, 255, 255)

COR_MOEDA_B = (255, 215, 0)
COR_MOEDA_H = (255, 255, 200)

COR_DANO_DEALER = (255, 255, 255)
COR_DANO_TAKEN = (255, 50, 50)
COR_CRITICO = (255, 255, 0)
COR_PARRY = (100, 255, 255)
COR_EXECUCAO = (255, 0, 0)

LIMITE_SEGURANCA = 750
AREA_SEGURA_X = 400
GRAVIDADE = 0.7
DISTANCIA_DASH, DURACAO_DASH = 22, 12
COOLDOWN_DASH, TEMPO_DOUBLE_TAP = 30, 18
TEMPO_RESPAWN = 4 * FPS
TEMPO_INVISIBILIDADE = 90

# --- SHAKE REDUZIDO ---
# Multiplicadores para reduzir a intensidade do shake
SHAKE_MULT_PEQUENO = 0.3  # Para hits normais
SHAKE_MULT_MEDIO = 0.5    # Para hits críticos
SHAKE_MULT_GRANDE = 0.7   # Para execuções

PLAYER_W = 128
PLAYER_H = 128


# --- CONFIGURAÇÃO DA LOJA ---
PRECO_GACHA = 15
ESPADAS_LOJA = [
    {"id": 1, "nome": "Katana Velha", "forca": 20, "vel": 45, "preco_venda": 5, "chance": 81.3,
     "cor_rastro": (200, 150, 100), "raridade_cor": RAR_COMUM},
    {"id": 2, "nome": "Lâmina de Aço", "forca": 40, "vel": 35, "preco_venda": 8, "chance": 10,
     "cor_rastro": (200, 200, 220), "raridade_cor": RAR_INCOMUM},
    {"id": 3, "nome": "Espada Flamejante", "forca": 60, "vel": 30, "preco_venda": 15, "chance": 5,
     "cor_rastro": (255, 100, 0), "raridade_cor": RAR_RARO},
    {"id": 4, "nome": "Lâmina Sombria", "forca": 80, "vel": 25, "preco_venda": 25, "chance": 2.5,
     "cor_rastro": (100, 0, 200), "raridade_cor": RAR_EPICO},
    {"id": 5, "nome": "Muramasa", "forca": 120, "vel": 20, "preco_venda": 50, "chance": 1,
     "cor_rastro": (255, 255, 100), "raridade_cor": RAR_LENDARIO},
    {"id": 6, "nome": "Matadora de Onis", "forca": 200, "vel": 15, "preco_venda": 100, "chance": 0.2,
     "cor_rastro": (255, 50, 50), "raridade_cor": RAR_SUBLIME}
]

PLATAFORMAS = [
    (1100, 750, 300, 1), (1800, 620, 300, 1),
    (2600, 780, 400, 2), (3500, 650, 500, 3), (4300, 700, 400, 2)
]

SLOT_ATUAL = 1
ESTRELAS_BG = [{'x': random.randint(0, LARGURA), 'y': random.randint(0, 900), 'tam': random.randint(1, 3),
                'brilho': random.randint(100, 255)} for _ in range(120)]