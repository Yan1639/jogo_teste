import pygame
import math
import uuid
from config import *
from utils import carregar_jogo, salvar_jogo, adicionar_texto_dano, textos_flutuantes, carregar_textura
from entities import gerar_dados_inimigo, gerar_dados_boss_final

TEXTURA_PARADO = None
TEXTURA_IDLE_SEM_ESPADA_FRAMES = None
TEXTURA_SACANDO_SWORD_FRAMES = None
TEXTURA_ANDANDO_SEM_ESPADA_FRAMES = None
TEXTURA_ATAQUE_FRAMES = None

TEXTURA_ATAQUE_1_FRAMES = None  # Primeiro ataque
TEXTURA_ATAQUE_2_FRAMES = None  # Segundo ataque
TEXTURA_ATAQUE_3_FRAMES = None  # Terceiro ataque


PLAYER_W = 128
PLAYER_H = 128


def inicializar_jogo(slot_id):
    import uuid

    p = {
        'rect': pygame.Rect(100, CHAO_Y - 90, 60, 90),
        'vida': 100, 'vida_max': 100, 'xp': 0, 'xp_proximo': 100, 'level': 1,
        'moedas_coletadas': 0, 'pontos_disponiveis': 0,
        'estado_espada': 'guardada',
        'timer_espada': 0,
        'idle_timer': 0,
        'duracao_sacar': 15,
        'duracao_guardar': 30,
        'atacando': 0, 'direcao': 1, 'v_vert': 0,
        'no_chao': False, 'pulos_extras': 1, 'pulo_duplo_ativo': False,
        'ataque_baixo': False, 'shake_timer': 0, 'freeze_timer': 0,
        'combo_step': 0, 'combo_timer': 0, 'parry_timer': 0, 'parry_cooldown': 0,
        'dash_timer': 0, 'dash_cooldown': 0,
        'last_tap_timer': 0, 'last_tap_dir': 0,
        'coyote_timer': 0,
        'buffer_pulo': 0,
        'rastro': [],
        'fantasmas_dash': [],  # <-- Lista de "fantasmas" visuais durante o dash
        'invisivel_timer': 0,
        'menu_aberto': False, 'mercado_aberto': False, 'game_over': False, 'pausado': False,
        'btn_menu': pygame.Rect(25, 150, 50, 50),
        'status': {'forca': 10, 'agilidade': 5, 'defesa': 0, 'esquiva': 0, 'regeneracao': 0.03},
        'inimigos_atingidos': [],
        'espadas_compradas': [{'id': 0, 'encantamento': 1.0, 'stacks': 0.0, 'uuid': str(uuid.uuid4())}],
        'espada_equipada_id': 0,
        'espada_equipada_uuid': None,
        'animacao_frame': 0, 'andando': False, 'particulas_hit': [],
        'msg_loja': "", 'msg_timer': 0,
        'buffer_ataque': False,
        'atk_total': 0,
        'projeteis': [],
        'cinematic_timer': 0,
    }

    # Define UUID da espada inicial
    p['espada_equipada_uuid'] = p['espadas_compradas'][0]['uuid']

    dados = carregar_jogo(slot_id)
    if dados:
        p.update({
            'xp': dados.get('xp', 0),
            'level': dados.get('level', 1),
            'moedas_coletadas': dados.get('moedas_total', 0),
            'status': dados.get('status', p['status']),
            'espadas_compradas': dados.get('espadas_compradas', []),
            'espada_equipada_id': dados.get('espada_equipada_id', 0),
            'espada_equipada_uuid': dados.get('espada_equipada_uuid'),
            'pontos_disponiveis': dados.get('pontos_disponiveis', 0)
        })

        # Adiciona UUID para espadas antigas que não têm
        for esp in p['espadas_compradas']:
            if 'uuid' not in esp:
                esp['uuid'] = str(uuid.uuid4())

        p['xp_proximo'] = 100 + (p['level'] - 1) * 50
    return p

def recortar_spritesheet(sheet, frame_w, frame_h, total_frames):
    frames = []
    count = 0

    for y in range(0, sheet.get_height(), frame_h):
        for x in range(0, sheet.get_width(), frame_w):
            if count >= total_frames:
                return frames  # PARA antes do slot vazio

            frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (x, y, frame_w, frame_h))
            frames.append(frame)
            count += 1

    return frames


def inicializar_texturas():
    """Carrega todas as texturas necessárias a partir de 1 spritesheet (usa 53 frames)."""
    global TEXTURA_PARADO, TEXTURA_IDLE_SEM_ESPADA_FRAMES, TEXTURA_SACANDO_SWORD_FRAMES
    global TEXTURA_ANDANDO_SEM_ESPADA_FRAMES, TEXTURA_ATAQUE_FRAMES
    global TEXTURA_ATAQUE_1_FRAMES, TEXTURA_ATAQUE_2_FRAMES, TEXTURA_ATAQUE_3_FRAMES

    sheet = carregar_textura("personagem_principal") or carregar_textura("personagem principal")
    if not sheet:
        print("✗ Não achei o spritesheet do personagem em /texturas (personagem_principal.png)")
        TEXTURA_PARADO = None
        TEXTURA_IDLE_SEM_ESPADA_FRAMES = None
        TEXTURA_SACANDO_SWORD_FRAMES = None
        TEXTURA_ANDANDO_SEM_ESPADA_FRAMES = None
        TEXTURA_ATAQUE_FRAMES = None
        TEXTURA_ATAQUE_1_FRAMES = None
        TEXTURA_ATAQUE_2_FRAMES = None
        TEXTURA_ATAQUE_3_FRAMES = None
        return

    # Recorta 53 frames
    frames_all = recortar_spritesheet(sheet, 128, 128, 53)
    frames_all = [pygame.transform.scale(f, (128, 128)) for f in frames_all]

    if len(frames_all) < 53:
        print(f"✗ Spritesheet recortou só {len(frames_all)} frames (esperado 53).")
        TEXTURA_PARADO = None
        TEXTURA_IDLE_SEM_ESPADA_FRAMES = None
        TEXTURA_SACANDO_SWORD_FRAMES = None
        TEXTURA_ANDANDO_SEM_ESPADA_FRAMES = None
        TEXTURA_ATAQUE_FRAMES = None
        TEXTURA_ATAQUE_1_FRAMES = None
        TEXTURA_ATAQUE_2_FRAMES = None
        TEXTURA_ATAQUE_3_FRAMES = None
        return

    # ✅ SEPARAÇÃO CORRETA:
    # 1..9   idle_c_sword
    # 10..20 idle_sem_sword
    # 21..28 idle_sac_espada
    # 29..40 andando_sem_sword
    # 40..45 ataque_1 (6 frames)
    # 46..49 ataque_2 (4 frames)
    # 50..53 ataque_3 (4 frames)

    TEXTURA_PARADO = frames_all[0:9]  # 1-9
    TEXTURA_IDLE_SEM_ESPADA_FRAMES = frames_all[9:20]  # 10-20
    TEXTURA_SACANDO_SWORD_FRAMES = frames_all[20:28]  # 21-28
    TEXTURA_ANDANDO_SEM_ESPADA_FRAMES = frames_all[28:40]  # 29-40

    # ✅ ATAQUES SEPARADOS POR COMBO
    TEXTURA_ATAQUE_1_FRAMES = frames_all[40:46]  # 40-45 (índices 39-44)
    TEXTURA_ATAQUE_2_FRAMES = frames_all[47:49]  # 46-49 (índices 45-48)
    TEXTURA_ATAQUE_3_FRAMES = frames_all[50:51]  # 50-53 (índices 49-52)

    # Mantém compatibilidade (usa ataque 1 como padrão)
    TEXTURA_ATAQUE_FRAMES = TEXTURA_ATAQUE_1_FRAMES

    print(f"✓ Texturas carregadas: {len(frames_all)} frames totais")
    print(f"  - Parado: {len(TEXTURA_PARADO)} frames")
    print(f"  - Idle sem espada: {len(TEXTURA_IDLE_SEM_ESPADA_FRAMES)} frames")
    print(f"  - Sacando: {len(TEXTURA_SACANDO_SWORD_FRAMES)} frames")
    print(f"  - Andando: {len(TEXTURA_ANDANDO_SEM_ESPADA_FRAMES)} frames")
    print(f"  - Ataque 1: {len(TEXTURA_ATAQUE_1_FRAMES)} frames")
    print(f"  - Ataque 2: {len(TEXTURA_ATAQUE_2_FRAMES)} frames")
    print(f"  - Ataque 3: {len(TEXTURA_ATAQUE_3_FRAMES)} frames")

def obter_atributos_reais(p):
    if 'agilidade' not in p['status']:
        p['status']['agilidade'] = 5

    esp_obj = next((e for e in p['espadas_compradas'] if e['id'] == p['espada_equipada_id']), None)
    mult = (esp_obj['encantamento'] + esp_obj['stacks']) if esp_obj else 1.0

    dano_base_espada = next((eb['forca'] for eb in ESPADAS_LOJA if eb['id'] == p['espada_equipada_id']), 0)
    forca_total = (p['status']['forca'] + dano_base_espada) * mult

    vel_espada = next((eb['vel'] for eb in ESPADAS_LOJA if eb['id'] == p['espada_equipada_id']), 50)
    atk_speed_final = max(5, vel_espada - (p['status']['agilidade'] * 2))

    cor_rastro = next((eb['cor_rastro'] for eb in ESPADAS_LOJA if eb['id'] == p['espada_equipada_id']), (200, 200, 200))

    return {
        'forca': forca_total,
        'atk_speed': atk_speed_final,
        'cor_rastro': cor_rastro,
        'esquiva': p['status'].get('esquiva', 0),
        'defesa': p['status'].get('defesa', 0),
        'regeneracao': p['status'].get('regeneracao', 0.03)
    }


# ========================================
# SISTEMA DE COLISÃO PERFEITO
# ========================================

def resolver_colisao_inimigos(inimigos):
    """Colisão ultra suave entre inimigos"""
    for i, inim1 in enumerate(inimigos):
        for inim2 in inimigos[i + 1:]:
            if inim1['rect'].colliderect(inim2['rect']):
                dx = inim2['rect'].centerx - inim1['rect'].centerx
                dist = abs(dx)

                if dist < 5:
                    dx = 1
                    dist = 1

                # Empurrão MÍNIMO
                empurrao = 0.5
                inim1['rect'].x -= int((dx / dist) * empurrao) if dx > 0 else int(empurrao)
                inim2['rect'].x += int((dx / dist) * empurrao) if dx > 0 else -int(empurrao)

                inim1['rect'].x = max(inim1['limites'][0], min(inim1['rect'].x, inim1['limites'][1]))
                inim2['rect'].x = max(inim2['limites'][0], min(inim2['rect'].x, inim2['limites'][1]))


def resolver_colisao_player_inimigos(p, inimigos):
    """Colisão player - Dash atravessa, normal empurra suave"""
    if p['dash_timer'] > 0 or p['invisivel_timer'] > 0:  # Dash E invencibilidade atravessam
        return

        # Conta colisões para evitar empurrão excessivo
    colisoes = 0
    for inim in inimigos:
        if p['rect'].colliderect(inim['rect']):
            colisoes += 1
            # Empurrão mais suave
            if p['rect'].centerx < inim['rect'].centerx:
                p['rect'].x -= 2
                inim['rect'].x += 2
            else:
                p['rect'].x += 2
                inim['rect'].x -= 2

            # Respeita limites
            inim['rect'].x = max(inim['limites'][0], min(inim['rect'].x, inim['limites'][1]))

    # Se cercado (3+ inimigos), teleporta para posição segura
    if colisoes >= 3 and p['atacando'] == 0:
        p['rect'].x += 50 * p['direcao']


def obter_hitbox_precisa_player(p):
    return pygame.Rect(
        p['rect'].x + 40,
        p['rect'].y + 25,
        48,
        90
    )


# ========================================
# SISTEMA DE COMBATE ULTRA POLIDO
# ========================================

def obter_dados_combo(combo_step, is_dashing):
    """Dados de cada ataque otimizados"""
    if is_dashing:
        return {
            'nome': 'DASH STRIKE',
            'dano_mult': 2.2,
            'alcance': (180, 100),
            'offset': (30, 0),
            'duracao_hit': (0.15, 0.65),
            'knockback': 35,
            'particulas': 20,
            'critico': True,
            'freeze': 4,
            'shake': 8,
            'impulso': 0,
            'lunge': 0
        }

    combos = {
        0: {
            'nome': 'CORTE INICIAL',
            'dano_mult': 1.0,
            'alcance': (180, 140),
            'offset': (60, 20),
            'duracao_hit': (0.20, 0.70),
            'knockback': 15,
            'particulas': 10,
            'critico': False,
            'freeze': 2,
            'shake': 3,
            'impulso': 8,
            'lunge': 15  # NOVO: Avanço em direção ao inimigo
        },
        1: {
            'nome': 'CORTE GIRATÓRIO',
            'dano_mult': 1.3,
            'alcance': (150, 110),
            'offset': (40, -5),
            'duracao_hit': (0.25, 0.75),
            'knockback': 25,
            'particulas': 14,
            'critico': False,
            'freeze': 3,
            'shake': 4,
            'impulso': 6,
            'lunge': 20
        },
        2: {
            'nome': 'FINALIZADOR',
            'dano_mult': 1.7,
            'alcance': (180, 120),
            'offset': (0, -15),
            'duracao_hit': (0.30, 0.90),
            'knockback': 50,
            'particulas': 18,
            'critico': True,
            'freeze': 5,
            'shake': 10,
            'impulso': 0,
            'lunge': 25
        }
    }
    return combos.get(combo_step, combos[0])


def encontrar_inimigo_mais_proximo(p, inimigos, alcance_max=250):
    """Encontra inimigo mais próximo para Attack Lunge"""
    inimigo_mais_proximo = None
    menor_dist = alcance_max

    for i in inimigos:
        dist = abs(p['rect'].centerx - i['rect'].centerx)
        if dist < menor_dist and abs(p['rect'].centery - i['rect'].centery) < 150:
            menor_dist = dist
            inimigo_mais_proximo = i

    return inimigo_mais_proximo, menor_dist


def obter_hitbox_ataque(p, combo_dados):
    alcance_x, alcance_y = combo_dados['alcance']
    offset_x, offset_y = combo_dados['offset']

    if p['direcao'] == 1:
        x = p['rect'].centerx + offset_x
    else:
        x = p['rect'].centerx - alcance_x - offset_x

    y = p['rect'].y + offset_y
    return pygame.Rect(x, y, alcance_x, alcance_y)


def processar_ataque_player(p, inimigos):
    """Sistema de combate PERFEITO com todos os polimentos"""
    if p['atacando'] <= 0:
        p['inimigos_atingidos'] = []  # Reset quando ataque termina
        p['ataque_baixo'] = False  # Reset ataque baixo
        return

    stats = obter_atributos_reais(p)
    is_dashing = p['dash_timer'] > 0
    combo_dados = obter_dados_combo(p['combo_step'], is_dashing)

    atk_total = int(p.get('atk_total', stats['atk_speed']))
    atk_total = max(1, atk_total)
    progresso = (atk_total - p['atacando']) / atk_total

    # === ATTACK LUNGE ===
    if p['atacando'] == atk_total and combo_dados['lunge'] > 0 and not is_dashing:
        inimigo_alvo, dist = encontrar_inimigo_mais_proximo(p, inimigos)

        if inimigo_alvo:
            # Avança em direção ao inimigo
            direcao_lunge = 1 if inimigo_alvo['rect'].centerx > p['rect'].centerx else -1
            p['rect'].x += combo_dados['lunge'] * direcao_lunge
            p['direcao'] = direcao_lunge
        else:
            # Se não há inimigo, avança na direção que está olhando
            p['rect'].x += combo_dados['impulso'] * p['direcao']

    # Janela de acerto
    inicio_hit, fim_hit = combo_dados['duracao_hit']

    # ATAQUE PARA BAIXO (Pogo)
    if p['ataque_baixo'] and not p['no_chao']:
        if inicio_hit <= progresso <= fim_hit:
            atk_rect = pygame.Rect(
                p['rect'].centerx - 30,
                p['rect'].bottom,
                60, 80
            )
            processar_hits(p, inimigos, atk_rect, combo_dados, stats)
        p['atacando'] -= 1
        return

    # ATAQUES NORMAIS
    if inicio_hit <= progresso <= fim_hit:
        # Usa um flag para garantir reset único por janela
        if not hasattr(p, '_hit_window_started') or not p['_hit_window_started']:
            p['inimigos_atingidos'] = []
            p['_hit_window_started'] = True
    else:
        p['_hit_window_started'] = False

        atk_rect = obter_hitbox_ataque(p, combo_dados)
        processar_hits(p, inimigos, atk_rect, combo_dados, stats)

    p['atacando'] -= 1


def processar_hits(p, inimigos, atk_rect, combo_dados, stats):
    """Processa acertos com feedback MÁXIMO"""
    for i in inimigos[:]:
        if i in p['inimigos_atingidos']:
            continue

        hitbox_inimigo = pygame.Rect(i['rect'].x + 20, i['rect'].y + 15, 40, 70)

        if atk_rect.colliderect(hitbox_inimigo):
            dano_final = int(stats['forca'] * combo_dados['dano_mult'])

            i['vida'] -= dano_final
            i['hit_flash'] = 18
            p['inimigos_atingidos'].append(i)

            # === FEEDBACK VISUAL INTENSO ===
            cor_dano = COR_CRITICO if combo_dados['critico'] else COR_DANO_DEALER
            adicionar_texto_dano(i['rect'].centerx, i['rect'].y, dano_final, cor_dano)
            adicionar_hit_feedback(p, i, combo_dados)

            # === HITSTOP + SCREEN SHAKE ===
            p['freeze_timer'] = combo_dados['freeze']
            p['shake_timer'] = combo_dados['shake'] * 2
            p['shake_intensidade'] = combo_dados['shake']

            # Knockback
            dir_knock = 1 if p['rect'].centerx < i['rect'].centerx else -1
            i['rect'].x += combo_dados['knockback'] * dir_knock
            i['rect'].x = max(i['limites'][0], min(i['rect'].x, i['limites'][1]))

            # Pogo bounce
            if p['ataque_baixo']:
                p['v_vert'] = -15
                p['pulos_extras'] = 1
                p['dash_cooldown'] = 0
                p['shake_timer'] = 8
                p['shake_intensidade'] = 6


def adicionar_hit_feedback(p, inimigo, combo_dados):
    """Partículas explosivas de impacto"""
    dir_particulas = 1 if p['rect'].centerx < inimigo['rect'].centerx else -1
    qtd = combo_dados['particulas']

    for _ in range(qtd):
        angulo = random.uniform(-80, 80)
        velocidade = random.uniform(7, 14) if combo_dados['critico'] else random.uniform(5, 10)

        p['particulas_hit'].append({
            'x': inimigo['rect'].centerx,
            'y': inimigo['rect'].centery,
            'timer': 45,
            'vx': math.cos(math.radians(angulo)) * velocidade * dir_particulas,
            'vy': math.sin(math.radians(angulo)) * velocidade,
            'size': random.randint(6, 11) if combo_dados['critico'] else random.randint(4, 7),
            'cor': COR_CRITICO if combo_dados['critico'] else COR_DANO_DEALER
        })


# ========================================
# ATUALIZAÇÃO PRINCIPAL COM TODOS OS POLIMENTOS
# ========================================

def atualizar_jogo(p, inimigos, moedas, fila_respawn, slot_atual):
    atualizar_sistema_espada(p)

    # Hitstop
    if p['freeze_timer'] > 0:
        p['freeze_timer'] -= 1
        return

    # Timers básicos
    if p['invisivel_timer'] > 0: p['invisivel_timer'] -= 1
    p['dash_cooldown'] = max(0, p['dash_cooldown'] - 1)
    p['last_tap_timer'] = max(0, p['last_tap_timer'] - 1)

    # Screen shake gradual
    if p['shake_timer'] > 0:
        p['shake_timer'] -= 1
        p['shake_intensidade'] = max(0, p['shake_intensidade'] - 0.3)

    p['animacao_frame'] = (p['animacao_frame'] + 1) % 60

    if p['combo_timer'] > 0:
        p['combo_timer'] -= 1
    else:
        p['combo_step'] = 0

    if p['parry_timer'] > 0: p['parry_timer'] -= 1
    if p['parry_cooldown'] > 0: p['parry_cooldown'] -= 1
    if p['msg_timer'] > 0: p['msg_timer'] -= 1

    # Coyote time e Jump buffer
    if p['coyote_timer'] > 0: p['coyote_timer'] -= 1
    if p['buffer_pulo'] > 0: p['buffer_pulo'] -= 1

    # Partículas
    for part in p['particulas_hit'][:]:
        part['timer'] -= 1
        if part.get('tipo') != 'slash_kill':
            part['y'] -= part['vy']
            part['x'] += part['vx']
            part['vy'] *= 0.90
        if part['timer'] <= 0:
            p['particulas_hit'].remove(part)

    # Fantasmas do dash
    for fantasma in p['fantasmas_dash'][:]:
        fantasma['timer'] -= 1
        fantasma['alpha'] -= 15
        if fantasma['timer'] <= 0 or fantasma['alpha'] <= 0:
            p['fantasmas_dash'].remove(fantasma)

    # Textos flutuantes
    for txt in textos_flutuantes[:]:
        txt['timer'] -= 1
        txt['y'] += txt['vy']
        txt['x'] += txt['vx']
        txt['vy'] *= 0.9
        if txt['timer'] <= 0:
            textos_flutuantes.remove(txt)

    stats_reais = obter_atributos_reais(p)
    if p['vida'] < p['vida_max'] and not p['game_over']:
        p['vida'] = min(p['vida_max'], p['vida'] + stats_reais['regeneracao'])

    if p['mercado_aberto'] and abs(p['rect'].x - 200) > 100:
        p['mercado_aberto'] = False

    # Movimento
    p['andando'] = False
    teclas = pygame.key.get_pressed()

    if p['dash_timer'] > 0:
        # After-images
        p['fantasmas_dash'].append({
            'x': p['rect'].x,
            'y': p['rect'].y,
            'timer': 15,
            'alpha': 150,
            'dir': p['direcao']
        })

        p['rastro'].append({'x': p['rect'].x, 'y': p['rect'].y, 'timer': 20, 'dir': p['direcao']})
        p['rect'].x += DISTANCIA_DASH * p['direcao']
        p['dash_timer'] -= 1
    else:
        velocidade = 8
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            p['rect'].x -= velocidade
            p['direcao'] = -1
            p['andando'] = True
        elif teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            p['rect'].x += velocidade
            p['direcao'] = 1
            p['andando'] = True

    for r in p['rastro'][:]:
        r['timer'] -= 2
        if r['timer'] <= 0: p['rastro'].remove(r)

    p['rect'].x = max(0, min(p['rect'].x, MAPA_LARGURA - 60))

    # Gravidade
    grav_atual = GRAVIDADE
    if p['atacando'] > 0 and not p['no_chao']:
        grav_atual = 0.30
        p['v_vert'] *= 0.91

    p['v_vert'] += grav_atual
    p['rect'].y += p['v_vert']

    # Armazena estado anterior do chão
    estava_no_chao = p['no_chao']
    p['no_chao'] = False

    # Chão
    if p['rect'].bottom >= CHAO_Y and p['v_vert'] >= 0:
        p['rect'].bottom = CHAO_Y
        p['v_vert'] = 0
        p['no_chao'] = True
        p['pulos_extras'] = 1
        p['pulo_duplo_ativo'] = False

        # Jump buffer - Se apertou pulo recentemente, pula ao aterrissar
        if p['buffer_pulo'] > 0:
            p['v_vert'] = -14
            p['buffer_pulo'] = 0
            p['no_chao'] = False

    # Plataformas
    deseja_descer = teclas[pygame.K_s] or teclas[pygame.K_DOWN]
    if p['v_vert'] >= 0 and not deseja_descer:
        for plat in PLATAFORMAS:
            if p['rect'].colliderect(pygame.Rect(plat[0], plat[1], plat[2], 20)):
                if p['rect'].bottom <= plat[1] + 15:
                    p['rect'].bottom = plat[1]
                    p['v_vert'] = 0
                    p['no_chao'] = True
                    p['pulos_extras'] = 1
                    p['pulo_duplo_ativo'] = False

                    if p['buffer_pulo'] > 0:
                        p['v_vert'] = -14
                        p['buffer_pulo'] = 0
                        p['no_chao'] = False
                    break

    # Coyote time - Permite pular brevemente após sair de plataforma
    if estava_no_chao and not p['no_chao'] and p['v_vert'] >= 0:
        p['coyote_timer'] = 10

    # Colisões
    resolver_colisao_inimigos(inimigos)
    resolver_colisao_player_inimigos(p, inimigos)

    # [Resto do código de inimigos continua igual...]
    hitbox_player = obter_hitbox_precisa_player(p)

    if not p.get('boss_spawned', False) and p['rect'].x > MAPA_LARGURA - 1200:
        inimigos.clear()
        fila_respawn.clear()
        moedas.clear()

        boss = gerar_dados_boss_final(MAPA_LARGURA - 650, CHAO_Y - 170, (MAPA_LARGURA - 1100, MAPA_LARGURA - 120))
        inimigos.append(boss)
        p['boss_spawned'] = True

    for i in inimigos[:]:
        if i['hit_flash'] > 0: i['hit_flash'] -= 1
        if i['timer_estado'] > 0: i['timer_estado'] -= 1
        dist_x = p['rect'].centerx - i['rect'].centerx
        dist_y = p['rect'].centery - i['rect'].centery

        if i['vida'] <= 0:
            if i.get('tipo') == 'boss':
                p['game_win'] = True
                inimigos.remove(i)
                continue
            p['xp'] += i['xp_recompensa']
            moedas.append(pygame.Rect(i['rect'].centerx, i['rect'].centery, 20, 20))
            fila_respawn.append({
                'tempo': TEMPO_RESPAWN,
                'dados': gerar_dados_inimigo(i['origem'][0], i['origem'][1], i['tipo'], i['limites'])
            })
            adicionar_texto_dano(
                i['rect'].centerx,
                i['rect'].y - 20,
                f"+{i['xp_recompensa']} XP",
                (255, 215, 0),
                tamanho_extra=1.0,  # 2x maior
                duracao=30,  # pouco tempo
                vy=-2.0,  # sobe suave
                vx=0  # não anda pro lado
            )

            inimigos.remove(i)
            continue

        if i['tipo'] == 'arqueiro' and i['estado'] == 'chase':
            if i['timer_tiro'] <= 0 and abs(dist_x) < 800:
                vel_flecha = 12 if dist_x > 0 else -12
                p['projeteis'].append({
                    'rect': pygame.Rect(i['rect'].centerx, i['rect'].centery, 25, 8),
                    'vx': vel_flecha,
                    'dono': 'inimigo'
                })
                i['timer_tiro'] = 120
            i['timer_tiro'] -= 1

        # ✅ CÓDIGO CORRIGIDO
        projeteis_para_remover = []

        for proj in p['projeteis']:
            proj['rect'].x += proj['vx']

            if proj['rect'].colliderect(hitbox_player) and proj['dono'] == 'inimigo':
                if p['parry_timer'] > 0:
                    proj['vx'] *= -1.5
                    proj['dono'] = 'player'
                    # ... feedback ...
                elif p['invisivel_timer'] == 0:
                    p['vida'] -= 10
                    projeteis_para_remover.append(proj)
                    continue

        # Remove projéteis marcados DEPOIS do loop
        for proj in projeteis_para_remover:
            if proj in p['projeteis']:
                p['projeteis'].remove(proj)

            if proj['dono'] == 'player':
                for inim in inimigos:
                    if proj['rect'].colliderect(inim['rect']):
                        inim['vida'] -= stats_reais['forca'] * 2
                        inim['hit_flash'] = 10
                        if proj in p['projeteis']:
                            p['projeteis'].remove(proj)
                        break

            if proj['rect'].x < 0 or proj['rect'].x > MAPA_LARGURA:
                if proj in p['projeteis']:
                    p['projeteis'].remove(proj)

        # IA Inimigo (continua igual ao código anterior)
        if i['estado'] == 'stun':
            if i['timer_estado'] <= 0:
                i['estado'] = 'chase'
        elif i['estado'] == 'atk':
            if i['timer_estado'] <= 0:
                i['estado'] = 'chase'
            if 5 < i['timer_estado'] < 25:
                espada_hitbox = pygame.Rect(
                    i['rect'].centerx + (15 if i['dir'] == 1 else -45),
                    i['rect'].centery - 15, 30, 30
                )
                if hitbox_player.colliderect(espada_hitbox) and p['invisivel_timer'] == 0:
                    if p['parry_timer'] > 0:
                        p['cinematic_timer'] = 50
                        p['freeze_timer'] = 5
                        adicionar_texto_dano(p['rect'].centerx, p['rect'].y - 60, "EXECUÇÃO!", COR_EXECUCAO, 1.5)
                        p['shake_timer'] = 15
                        p['shake_intensidade'] = 10
                        lado_oposto = 1 if dist_x < 0 else -1
                        p['rect'].x = i['rect'].centerx + (60 * lado_oposto)
                        p['direcao'] = -lado_oposto
                        p['particulas_hit'].append({
                            'x': i['rect'].centerx, 'y': i['rect'].centery,
                            'timer': 15, 'tipo': 'slash_kill'
                        })
                        i['vida'] = 0
                    else:
                        if random.randint(1, 100) > stats_reais['esquiva']:
                            dano = max(5, 10 - stats_reais['defesa'])
                            p['vida'] -= dano
                            adicionar_texto_dano(p['rect'].centerx, p['rect'].y, dano, COR_DANO_TAKEN)
                            p['invisivel_timer'] = TEMPO_INVISIBILIDADE
                            p['rect'].x += 40 * (1 if dist_x > 0 else -1)
                            p['shake_timer'] = 6
                            p['shake_intensidade'] = 4
        elif i['estado'] == 'pre_atk':
            if i['timer_estado'] <= 0:
                i['estado'] = 'atk'
                i['timer_estado'] = 30
                i['rect'].x += 30 * (1 if dist_x > 0 else -1)
        elif i['estado'] == 'chase':
            if abs(dist_x) < 400 and abs(dist_y) < 100 and p['rect'].x > LIMITE_SEGURANCA:
                if abs(dist_x) < 80:
                    i['estado'] = 'pre_atk'
                    i['timer_estado'] = 30
                else:
                    move = 2.5 if dist_x > 0 else -2.5
                    i['rect'].x += move
                    i['dir'] = 1 if dist_x > 0 else -1
            else:
                i['estado'] = 'patrol'
        elif i['estado'] == 'patrol':
            if abs(dist_x) < 400 and abs(dist_y) < 100 and p['rect'].x > LIMITE_SEGURANCA:
                i['estado'] = 'chase'
            else:
                i['rect'].x += (1.5 * i['dir'])
                if i['rect'].x <= i['limites'][0] or i['rect'].x >= i['limites'][1]:
                    i['dir'] *= -1

        i['rect'].x = max(i['limites'][0], min(i['rect'].x, i['limites'][1]))

    processar_ataque_player(p, inimigos)

    if p['xp'] >= p['xp_proximo']:
        p['xp'] -= p['xp_proximo']
        p['level'] += 1
        p['xp_proximo'] += 50
        p['pontos_disponiveis'] += 1
        salvar_jogo(p, slot_atual)

    for m in moedas[:]:
        if p['rect'].colliderect(m):
            p['moedas_coletadas'] += 1
            moedas.remove(m)

    for r in fila_respawn[:]:
        r['tempo'] -= 1
        if r['tempo'] <= 0:
            offset_camera = p['rect'].x - (LARGURA // 2)
            pos_spawn = r['dados']['origem'][0]
            if pos_spawn - offset_camera < -100 or pos_spawn - offset_camera > (LARGURA + 100):
                inimigos.append(r['dados'])
                fila_respawn.remove(r)


def processar_pulo(p):
    """Processa pulo com Coyote Time"""
    # Pulo normal
    if p['no_chao']:
        p['v_vert'] = -14
        p['no_chao'] = False
        p['pulo_duplo_ativo'] = False
        p['buffer_pulo'] = 0
        return True

    # Coyote time - Permite pular logo após sair de plataforma
    elif p['coyote_timer'] > 0:
        p['v_vert'] = -14
        p['coyote_timer'] = 0
        p['pulo_duplo_ativo'] = False
        p['buffer_pulo'] = 0
        return True

    # Pulo duplo
    elif p['pulos_extras'] > 0:
        p['v_vert'] = -14
        p['pulos_extras'] -= 1
        p['pulo_duplo_ativo'] = True
        p['buffer_pulo'] = 0
        return True

    # Não pode pular, mas ativa buffer
    else:
        p['buffer_pulo'] = 10  # 10 frames de buffer
        return False

def _iniciar_ataque(p, ataque_baixo_solicitado):
    """Inicia um ataque e garante duração mínima para a animação não ficar rápida/cortada."""
    if p.get('estado_espada') != 'pronta':
        return False

    stats = obter_atributos_reais(p)

    # Combo só avança em ataques normais (não no pogo)
    if not ataque_baixo_solicitado:
        if p.get('combo_timer', 0) > 0:
            p['combo_step'] = (p.get('combo_step', 0) + 1) % 3
        else:
            p['combo_step'] = 0
        p['combo_timer'] = 60

    combo_step = p.get('combo_step', 0)

    dur = int(stats.get('atk_speed', 20))

    # quantidade de frames da animação escolhida
    frames_len = 0
    if combo_step == 0 and TEXTURA_ATAQUE_1_FRAMES:
        frames_len = len(TEXTURA_ATAQUE_1_FRAMES)
    elif combo_step == 1 and TEXTURA_ATAQUE_2_FRAMES:
        frames_len = len(TEXTURA_ATAQUE_2_FRAMES)
    elif combo_step == 2 and TEXTURA_ATAQUE_3_FRAMES:
        frames_len = len(TEXTURA_ATAQUE_3_FRAMES)
    elif TEXTURA_ATAQUE_1_FRAMES:
        frames_len = len(TEXTURA_ATAQUE_1_FRAMES)

    # garante duração mínima baseada nos frames
    if frames_len > 0:
        min_frames = int(math.ceil((frames_len * ATAQUE_FRAME_MS) * FPS / 1000.0))
        dur = max(dur, min_frames)

    p['atacando'] = dur
    p['atk_total'] = dur
    p['atk_anim_start'] = pygame.time.get_ticks()
    p['ataque_baixo'] = bool(ataque_baixo_solicitado)
    p['buffer_ataque'] = False
    return True


def atualizar_combate_fluido(p, teclas, clicou_mouse):
    """Combate com buffer de ataque (não perde clique ao spammar) + ataque mais lento."""

    if p.get('menu_aberto') or p.get('mercado_aberto') or p.get('pausado') or p.get('game_over'):
        return

    # dash cancela ataque
    if p.get('dash_timer', 0) > 0 and p.get('atacando', 0) > 0:
        if p.get('combo_step', 0) != 0:
            p['atacando'] = 0
            p['atk_total'] = 0
            p['inimigos_atingidos'] = []
            p['buffer_ataque'] = False

    atk_baixo_solicitado = (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) and (not p.get('no_chao', True))

    if clicou_mouse:
        p['buffer_ataque_baixo'] = bool(atk_baixo_solicitado)

        # se está atacando, guarda o clique (buffer SEM “janela pequena”)
        if p.get('atacando', 0) > 0:
            p['buffer_ataque'] = True

        # durante sacar/guardar: também bufferiza
        elif p.get('estado_espada') in ['sacando', 'guardando']:
            p['buffer_ataque'] = True

        # espada guardada: saca e já bufferiza o ataque
        elif p.get('estado_espada') == 'guardada':
            p['estado_espada'] = 'sacando'
            p['timer_espada'] = p.get('duracao_sacar', 15)
            p['idle_timer'] = 0
            p['buffer_ataque'] = True

        # espada pronta e não atacando: ataca agora
        elif p.get('estado_espada') == 'pronta' and p.get('atacando', 0) <= 0:
            _iniciar_ataque(p, atk_baixo_solicitado)
            return

    # executa buffer assim que puder
    if p.get('buffer_ataque', False) and p.get('atacando', 0) <= 0 and p.get('estado_espada') == 'pronta':
        _iniciar_ataque(p, p.get('buffer_ataque_baixo', False))
        p['buffer_ataque'] = False

    # pogo
    if p.get('ataque_baixo', False) and p.get('atacando', 0) > 0:
        p['v_vert'] = min(p.get('v_vert', 0), 2)

# ========================================
# CÂMERA LERP (Suavização)
# ========================================

def calcular_camera_lerp(p):
    """Calcula posição da câmera com suavização (lerp) e shake.

    Fixes:
    - Usa chave de dict ("camera_x") ao invés de hasattr (p é dict).
    - Usa centerx do player (melhor centrado).
    - Evita KeyError quando shake_intensidade não existe.
    """
    target_x = p['rect'].centerx - (LARGURA // 2)
    target_x = max(0, min(target_x, MAPA_LARGURA - LARGURA))

    if 'camera_x' not in p:
        p['camera_x'] = float(target_x)
    else:
        p['camera_x'] += (target_x - p['camera_x']) * 0.15

    shake_x = 0
    shake_y = 0
    if p.get('shake_timer', 0) > 0:
        intensidade = int(p.get('shake_intensidade', 0))
        shake_x = random.randint(-intensidade, intensidade) if intensidade > 0 else 0
        shake_y = random.randint(-intensidade, intensidade) if intensidade > 0 else 0

    return int(p['camera_x']) + shake_x, shake_y



# Funções auxiliares (continuam iguais)
def calcular_dps_espada(esp_obj, dados_base):
    forca_total = dados_base['forca'] * esp_obj.get('encantamento', 1.0) * (1 + esp_obj.get('stacks', 0.0))
    velocidade = dados_base['vel']
    dps = forca_total / (velocidade / 60)
    return dps


def ordenar_espadas_por_dps(p):
    espadas_com_dps = []
    for esp_obj in p['espadas_compradas']:
        dados_base = next((eb for eb in ESPADAS_LOJA if eb['id'] == esp_obj['id']), ESPADAS_LOJA[0])
        dps = calcular_dps_espada(esp_obj, dados_base)
        espadas_com_dps.append({'obj': esp_obj, 'base': dados_base, 'dps': dps})
    espadas_com_dps.sort(key=lambda x: x['dps'], reverse=True)
    return espadas_com_dps


def atualizar_sistema_espada(p):
    if p['estado_espada'] in ['sacando', 'guardando']:
        if p['timer_espada'] > 0:
            p['timer_espada'] -= 1
        else:
            if p['estado_espada'] == 'sacando':
                p['timer_espada'] -= 1

                if p['timer_espada'] <= 0:
                    p['estado_espada'] = 'pronta'
                    p['timer_espada'] = 0

                p['idle_timer'] = 0   # <<< zera aqui
            else:
                p['estado_espada'] = 'guardada'
                p['idle_timer'] = 0   # <<< e zera aqui também


    elif p['estado_espada'] == 'pronta':

        # Reset mais agressivo do timer

        if p['atacando'] > 0 or p['andando'] or p['dash_timer'] > 0:

            p['idle_timer'] = 0

        else:

            p['idle_timer'] += 1

        # Não guarda durante combos ativos

        if p['idle_timer'] > 300 and p['combo_timer'] == 0:
            p['estado_espada'] = 'guardando'

            p['timer_espada'] = p['duracao_guardar']

            p['idle_timer'] = 0  # Reset para evitar loop

        if p['idle_timer'] > 300:
            p['estado_espada'] = 'guardando'
            p['timer_espada'] = p['duracao_guardar']



def combinar_3_espadas(p, id_espada):
    iguais = [e for e in p['espadas_compradas'] if e['id'] == id_espada]
    if len(iguais) >= 3:
        removidas = 0
        maior_encantamento = 0.7
        bonus_atual = 0
        nova_lista = []
        for e in p['espadas_compradas']:
            if e['id'] == id_espada and removidas < 3:
                maior_encantamento = max(maior_encantamento, e['encantamento'])
                bonus_atual = max(bonus_atual, e['stacks'])
                removidas += 1
            else:
                nova_lista.append(e)
        novo_bonus = min(bonus_atual + 0.05, 0.30)
        nova_lista.append({'id': id_espada, 'encantamento': maior_encantamento, 'stacks': novo_bonus})
        p['espadas_compradas'] = nova_lista
        return True
    return False