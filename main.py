import sys
import os
import uuid
from utils import *
from entities import criar_inimigos_iniciais
from logic import *
from interface import *


def main():
    global SLOT_ATUAL

    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.init()

    tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF)
    pygame.display.set_caption("RPG Samurai - Ultra Polished Combat")

    # === INICIALIZA TEXTURAS ===
    print("Carregando texturas...")
    inicializar_texturas()

    import logic
    import interface

    if hasattr(logic, 'TEXTURA_PARADO'):
        interface.TEXTURA_PARADO = logic.TEXTURA_PARADO
        print("✓ Textura transferida para interface com sucesso!")
    if hasattr(logic, 'TEXTURA_IDLE_SEM_ESPADA_FRAMES'):
        interface.TEXTURA_IDLE_SEM_ESPADA_FRAMES = logic.TEXTURA_IDLE_SEM_ESPADA_FRAMES
        print("✓ Idle sem espada transferido para interface com sucesso!")
    if hasattr(logic, 'TEXTURA_SACANDO_SWORD_FRAMES'):
        interface.TEXTURA_SACANDO_SWORD_FRAMES = logic.TEXTURA_SACANDO_SWORD_FRAMES
        print("✓ Animação sacando espada transferida!")
    if hasattr(logic, 'TEXTURA_ANDANDO_SEM_ESPADA_FRAMES'):
        interface.TEXTURA_ANDANDO_SEM_ESPADA_FRAMES = logic.TEXTURA_ANDANDO_SEM_ESPADA_FRAMES
        print("✓ Andando sem espada transferido!")
    if hasattr(logic, 'TEXTURA_ATAQUE_FRAMES'):
        interface.TEXTURA_ATAQUE_FRAMES = logic.TEXTURA_ATAQUE_FRAMES
        print("✓ Ataque transferido!")
    else:
        print("✗ Erro: Textura não encontrada no logic.")
    if hasattr(logic, 'TEXTURA_ATAQUE_1_FRAMES'):
        interface.TEXTURA_ATAQUE_1_FRAMES = logic.TEXTURA_ATAQUE_1_FRAMES
        print("✓ Ataque 1 transferido!")
    if hasattr(logic, 'TEXTURA_ATAQUE_2_FRAMES'):
        interface.TEXTURA_ATAQUE_2_FRAMES = logic.TEXTURA_ATAQUE_2_FRAMES
        print("✓ Ataque 2 transferido!")
    if hasattr(logic, 'TEXTURA_ATAQUE_3_FRAMES'):
        interface.TEXTURA_ATAQUE_3_FRAMES = logic.TEXTURA_ATAQUE_3_FRAMES
        print("✓ Ataque 3 transferido!")

    print("Texturas carregadas!")

    # === INICIALIZA TEXTURAS ===
    print("Carregando texturas...")
    inicializar_texturas()

    # DEBUG - ADICIONE ISSO AQUI
    import logic
    print(f"DEBUG - logic.TEXTURA_PARADO: {logic.TEXTURA_PARADO is not None}")
    print(f"DEBUG - logic.TEXTURA_ANDANDO: {logic.TEXTURA_ANDANDO_SEM_ESPADA_FRAMES is not None}")
    print(f"DEBUG - logic.TEXTURA_ATAQUE: {logic.TEXTURA_ATAQUE_FRAMES is not None}")

    clock = pygame.time.Clock()
    estado_jogo = "MENU"
    p, inimigos, moedas, fila_respawn = None, [], [], []
    rodando = True

    while rodando:
        mouse_pos = pygame.mouse.get_pos()
        clicou_frame = False
        evs = pygame.event.get()

        for ev in evs:
            if ev.type == pygame.QUIT:
                rodando = False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                clicou_frame = True

        if estado_jogo == "MENU":
            res = desenhar_menu_principal(tela, mouse_pos, clicou_frame)
            if res == "SAIR":
                rodando = False
            elif res != "MENU":
                estado_jogo = res

        elif estado_jogo == "SELECAO_SAVE":
            res = desenhar_selecao_save(tela, mouse_pos, clicou_frame)
            if isinstance(res, int):
                SLOT_ATUAL = res
                p = inicializar_jogo(SLOT_ATUAL)
                inimigos = criar_inimigos_iniciais()
                moedas, fila_respawn = [], []
                estado_jogo = "JOGANDO"
            elif res == "MENU":
                estado_jogo = "MENU"

        elif estado_jogo in ["CONFIG", "CONTROLES"]:
            res = desenhar_tela_config(tela, mouse_pos,
                                       clicou_frame) if estado_jogo == "CONFIG" else desenhar_tela_controles(tela,
                                                                                                             mouse_pos,
                                                                                                             clicou_frame)
            if res == "MENU":
                estado_jogo = "MENU"

        elif estado_jogo == "JOGANDO":
            for ev in evs:
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = mouse_pos

                    # PARRY
                    if ev.button == 3 and not (p['menu_aberto'] or p['mercado_aberto'] or p['pausado']):
                        if p['parry_cooldown'] == 0:
                            p['parry_timer'] = 18
                            p['parry_cooldown'] = 60

                    # ATAQUE/MENUS
                    if ev.button == 1:
                        # MENUS
                        if p['pausado']:
                            cx, cy = LARGURA // 2, ALTURA // 2
                            if pygame.Rect(cx - 120, cy - 60, 240, 60).collidepoint((mx, my)):
                                p['pausado'] = False
                            if pygame.Rect(cx - 120, cy + 20, 240, 60).collidepoint((mx, my)):
                                salvar_jogo(p, SLOT_ATUAL)
                                estado_jogo = "MENU"
                            if pygame.Rect(cx - 120, cy + 100, 240, 60).collidepoint((mx, my)):
                                salvar_jogo(p, SLOT_ATUAL)
                                rodando = False
                        else:
                            if p['btn_menu'].collidepoint((mx, my)):
                                p['menu_aberto'] = not p['menu_aberto']

                            if p['mercado_aberto']:
                                cx, cy = LARGURA // 2, ALTURA // 2
                                pos_x, pos_y = cx - 550, cy - 380

                                if pygame.Rect(pos_x + 70, pos_y + 520, 220, 70).collidepoint((mx, my)):
                                    if p['moedas_coletadas'] >= PRECO_GACHA:
                                        p['moedas_coletadas'] -= PRECO_GACHA
                                        r = random.randint(1, 100)
                                        acumulo = 0
                                        item_ganho = None
                                        for esp in ESPADAS_LOJA:
                                            acumulo += esp['chance']
                                            if r <= acumulo:
                                                item_ganho = esp
                                                break
                                        if not item_ganho:
                                            item_ganho = ESPADAS_LOJA[0]

                                        nova_espada_obj = {
                                            'id': item_ganho['id'],
                                            'encantamento': gerar_encantamento(),
                                            'stacks': 0.0,
                                            'uuid': str(uuid.uuid4())
                                        }
                                        p['espadas_compradas'].append(nova_espada_obj)
                                        p['msg_loja'] = f"Ganhou: {item_ganho['nome']}!"
                                        p['msg_timer'] = 120
                                        salvar_jogo(p, SLOT_ATUAL)

                                contagem = {}
                                y_offset = 0
                                for esp_obj in p['espadas_compradas']:
                                    contagem[esp_obj['id']] = contagem.get(esp_obj['id'], 0) + 1

                                for esp in ESPADAS_LOJA:
                                    if contagem.get(esp['id'], 0) > 0:
                                        rect_item = pygame.Rect(pos_x + 525, pos_y + 185 + y_offset, 540, 70)

                                        if pygame.Rect(rect_item.right - 160, rect_item.y + 10, 70, 50).collidepoint(
                                                (mx, my)) and p['espada_equipada_id'] != esp['id']:
                                            p['espada_equipada_id'] = esp['id']
                                            salvar_jogo(p, SLOT_ATUAL)

                                        if pygame.Rect(rect_item.right - 80, rect_item.y + 10, 70, 50).collidepoint(
                                                (mx, my)):
                                            for idx, e in enumerate(p['espadas_compradas']):
                                                if e['id'] == esp['id']:
                                                    p['espadas_compradas'].pop(idx)
                                                    break
                                            p['moedas_coletadas'] += esp['preco_venda']
                                            if not any(e['id'] == esp['id'] for e in p['espadas_compradas']):
                                                if p['espada_equipada_id'] == esp['id']:
                                                    p['espada_equipada_id'] = 0
                                            salvar_jogo(p, SLOT_ATUAL)
                                        y_offset += 75

                # TECLADO
                if ev.type == pygame.KEYDOWN:
                    # ESC
                    if ev.key == pygame.K_ESCAPE:
                        if p['game_over']:
                            salvar_jogo(p, SLOT_ATUAL)
                            estado_jogo = "MENU"
                        elif p['mercado_aberto']:
                            p['mercado_aberto'] = False
                        elif p['menu_aberto']:
                            p['menu_aberto'] = False
                        else:
                            p['pausado'] = not p['pausado']

                    if not p['pausado'] and not p['game_over'] and not p.get('game_win', False):
                        # E para loja/inventário
                        if ev.key == pygame.K_e and abs(p['rect'].x - 200) < 100:
                            p['mercado_aberto'] = not p['mercado_aberto']
                        if ev.key == pygame.K_e and abs(p['rect'].x - 200) > 100:
                            p['menu_aberto'] = not p['menu_aberto']

                        # PULO COM COYOTE TIME E BUFFER
                        if ev.key in [pygame.K_SPACE, pygame.K_w]:
                            processar_pulo(p)

                        # DASH (com Action Canceling)
                        if ev.key in [pygame.K_a, pygame.K_LEFT]:
                            if p['last_tap_dir'] == -1 and p['last_tap_timer'] > 0 and p['dash_cooldown'] == 0:
                                p['dash_timer'] = DURACAO_DASH
                                p['dash_cooldown'] = COOLDOWN_DASH

                                if p['atacando'] > 5:
                                    p['atacando'] = 0
                                    p['inimigos_atingidos'] = []

                            p['last_tap_dir'] = -1
                            p['last_tap_timer'] = TEMPO_DOUBLE_TAP

                        elif ev.key in [pygame.K_d, pygame.K_RIGHT]:
                            if p['last_tap_dir'] == 1 and p['last_tap_timer'] > 0 and p['dash_cooldown'] == 0:
                                p['dash_timer'] = DURACAO_DASH
                                p['dash_cooldown'] = COOLDOWN_DASH

                                if p['atacando'] > 5:
                                    p['atacando'] = 0
                                    p['inimigos_atingidos'] = []

                            p['last_tap_dir'] = 1
                            p['last_tap_timer'] = TEMPO_DOUBLE_TAP

                    # Renascer
                    elif p['game_over'] and ev.key == pygame.K_r:
                        resetar_posicao_segura(p)

            if not p['pausado'] and not p['game_over']:
                teclas = pygame.key.get_pressed()
                clicou_mouse = any(ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 for ev in evs)
                atualizar_combate_fluido(p, teclas, clicou_mouse)
                atualizar_jogo(p, inimigos, moedas, fila_respawn, SLOT_ATUAL)
                if p['vida'] <= 0:
                    p['game_over'] = True

            # CÂMERA LERP COM SHAKE
            off_x, shake_y = calcular_camera_lerp(p)

            desenhar_jogo(tela, p, inimigos, moedas, off_x, shake_y)

            if p['menu_aberto']:
                desenhar_menu_status_melhorado(tela, p, clicou_frame)
            if p['mercado_aberto']:
                desenhar_mercado_overlay(tela, p)
            if p['pausado']:
                desenhar_menu_pause(tela, mouse_pos, clicou_frame)

            desenhar_fps(tela, clock)

            if p['game_over']:
                s = pygame.Surface((LARGURA, ALTURA))
                s.set_alpha(180)
                s.fill((50, 0, 0))
                tela.blit(s, (0, 0))
                cx, cy = LARGURA // 2, ALTURA // 2
                tela.blit(get_fonte("Impact", 72, bold=True).render("VOCÊ MORREU", True, (255, 50, 50)),
                          (cx - 220, cy - 60))
                tela.blit(get_fonte("Verdana", 28).render("[R] Renascer  |  [ESC] Menu", True, (255, 255, 255)),
                          (cx - 230, cy + 60))

            if p.get('game_win', False):
                s = pygame.Surface((LARGURA, ALTURA))
                s.set_alpha(180)
                s.fill((0, 40, 0))
                tela.blit(s, (0, 0))
                cx, cy = LARGURA // 2, ALTURA // 2
                tela.blit(get_fonte("Impact", 72, bold=True).render("VOCÊ VENCEU!", True, (255, 215, 0)),
                          (cx - 250, cy - 60))
                tela.blit(get_fonte("Verdana", 28).render("[R] Reiniciar  |  [ESC] Menu", True, (255, 255, 255)),
                          (cx - 230, cy + 60))
\d
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()