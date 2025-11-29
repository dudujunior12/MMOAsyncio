import asyncio
import pygame

FONT_SIZE = 28
pygame.font.init()
FONT = pygame.font.SysFont("Arial", FONT_SIZE)

SCREEN = pygame.display.set_mode((500, 200))
pygame.display.set_caption("Login")

COLOR_BG = (30, 30, 30)
COLOR_TEXT = (200, 200, 200)
COLOR_INPUT = (80, 80, 80)


def draw_text(text, y, color=COLOR_TEXT):
    img = FONT.render(text, True, color)
    SCREEN.blit(img, (20, y))


async def get_auth_choice():
    """
    Tela inicial: escolher LOGIN (L) ou REGISTER (R)
    """
    while True:
        SCREEN.fill(COLOR_BG)
        draw_text("Press L to Login", 40)
        draw_text("Press R to Register", 90)
        pygame.display.flip()

        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_l:
                    return "L"
                if event.key == pygame.K_r:
                    return "R"


async def get_text_input(prompt):
    """
    Caixa de input genérica (para username e password)
    """
    text = ""
    active = True

    while active:
        SCREEN.fill(COLOR_BG)
        draw_text(prompt, 40)
        pygame.draw.rect(SCREEN, COLOR_INPUT, pygame.Rect(20, 90, 460, 40))

        draw_text(text, 95)
        pygame.display.flip()

        await asyncio.sleep(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return text

                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode


async def get_credentials(is_register=False):
    """
    Coleta username + password
    """
    username = await get_text_input("Username:")
    if username is None:
        return None

    password = await get_text_input("Password:")
    if password is None:
        return None

    return username, password


async def display_message(message: str, is_system=False):
    """
    Mostra mensagens como "Autenticação falhou"
    """
    timer = 1.5

    while timer > 0:
        SCREEN.fill(COLOR_BG)
        draw_text(message, 80, COLOR_TEXT if not is_system else (255, 200, 50))
        pygame.display.flip()
        await asyncio.sleep(0.05)
        timer -= 0.05


async def prompt_for_game_action():
    """
    Caso no futuro queira escolher ações antes de entrar no jogo.
    """
    pass
