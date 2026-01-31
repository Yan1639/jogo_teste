import pygame
import random
from config import CHAO_Y, MAPA_LARGURA, PLATAFORMAS


def gerar_dados_inimigo(x, y, tipo, limites):
    esq, dir_ = limites
    # Atributos base variando por tipo
    vida = 150 if tipo == 'arqueiro' else 100
    return {
        'rect': pygame.Rect(x, y, 80, 100),
        'vida_max': vida, 'vida': vida, 'dano_base': 8.0,
        'xp_recompensa': 60 if tipo == 'arqueiro' else 40,
        'dir': 1, 'limites': (esq, dir_), 'tipo': tipo, 'origem': (x, y), 'hit_flash': 0,
        'estado': 'patrol', 'timer_estado': 0, 'timer_tiro': 0
    }


def verificar_posicao_livre(rect_novo, lista_inimigos):
    for i in lista_inimigos:
        if rect_novo.colliderect(i['rect']):
            return False
    return True


def criar_inimigos_iniciais():
    inimigos = []
    for _ in range(8):
        for tentativa in range(10):
            x = random.randint(1000, MAPA_LARGURA - 200)
            dados = gerar_dados_inimigo(x, CHAO_Y - 90, 'chao', (800, MAPA_LARGURA - 100))
            if verificar_posicao_livre(dados['rect'], inimigos):
                inimigos.append(dados)
                break

    for p in PLATAFORMAS:
        limite_esq = p[0] + 20
        limite_dir = p[0] + p[2] - 70
        if limite_dir < limite_esq:
            limite_dir = limite_esq
        for _ in range(p[3]):
            for tentativa in range(10):
                x = random.randint(limite_esq, limite_dir)
                dados = gerar_dados_inimigo(x, p[1] - 90, 'plat', (limite_esq, limite_dir))
                if verificar_posicao_livre(dados['rect'], inimigos):
                    inimigos.append(dados)
                    break
    return inimigos

def gerar_dados_boss_final(x, y, limites):
    esq, dir_ = limites
    vida = 900
    return {
        'rect': pygame.Rect(x, y, 140, 170),
        'vida_max': vida, 'vida': vida,
        'dano_base': 18.0,
        'xp_recompensa': 500,
        'dir': -1,
        'limites': (esq, dir_),
        'tipo': 'boss',
        'origem': (x, y),
        'hit_flash': 0,
        'estado': 'chase',
        'timer_estado': 0,
        'timer_tiro': 0,
        'boss_cd': {'slam': 0, 'dash': 0, 'tiro': 0}
    }
