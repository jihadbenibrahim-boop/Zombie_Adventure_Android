# لعبة مغامرات وقتال زومبي - Python + Pygame
# التحكم: الأسهم أو A/D للحركة، Space للقفز، X لإطلاق النار، R لإعادة اللعب
# شغّل الملف في Thonny بعد تثبيت pygame.

import pygame
import random
import sys

pygame.init()

WIDTH, HEIGHT = 960, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Adventure - لعبة المغامرات")
clock = pygame.time.Clock()

# الألوان
SKY = (155, 215, 245)
GROUND = (65, 135, 75)
DARK_GREEN = (40, 95, 55)
BROWN = (125, 82, 48)
PLAYER_COLOR = (45, 90, 220)
ZOMBIE_COLOR = (80, 150, 70)
DARK = (30, 35, 45)
WHITE = (255, 255, 255)
YELLOW = (255, 210, 40)
RED = (220, 55, 55)
GRAY = (110, 115, 125)

font = pygame.font.SysFont("arial", 24)
small_font = pygame.font.SysFont("arial", 18)
big_font = pygame.font.SysFont("arial", 46)

WORLD_WIDTH = 3200
GROUND_Y = 500
GRAVITY = 0.65

platforms = [
    pygame.Rect(0, GROUND_Y, WORLD_WIDTH, HEIGHT - GROUND_Y),
    pygame.Rect(340, 420, 150, 18),
    pygame.Rect(650, 365, 160, 18),
    pygame.Rect(980, 430, 180, 18),
    pygame.Rect(1300, 380, 170, 18),
    pygame.Rect(1650, 330, 180, 18),
    pygame.Rect(2000, 420, 180, 18),
    pygame.Rect(2350, 360, 190, 18),
    pygame.Rect(2700, 410, 180, 18),
]

def make_zombies():
    return [
        {"rect": pygame.Rect(x, GROUND_Y - 42, 32, 42), "speed": random.choice([1.1, 1.4, 1.7]), "hp": 2, "alive": True}
        for x in [430, 760, 1080, 1450, 1780, 2130, 2480, 2850, 3050]
    ]

def make_coins():
    positions = [
        (260, 455), (390, 375), (700, 320), (1040, 385),
        (1370, 335), (1720, 285), (2050, 375), (2410, 315),
        (2760, 365), (3000, 455)
    ]
    return [pygame.Rect(x, y, 18, 18) for x, y in positions]

def reset_game():
    player = pygame.Rect(70, GROUND_Y - 54, 34, 54)
    return {
        "player": player,
        "vx": 0.0, "vy": 0.0, "on_ground": False,
        "facing": 1, "health": 5, "score": 0,
        "bullets": [], "zombies": make_zombies(), "coins": make_coins(),
        "won": False, "lost": False, "invulnerable": 0
    }

game = reset_game()
camera_x = 0

def draw_text(text, x, y, color=WHITE, use_font=font):
    surface = use_font.render(text, True, color)
    screen.blit(surface, (x, y))

def move_and_collide(rect, dx, dy):
    rect.x += int(dx)
    for p in platforms:
        if rect.colliderect(p):
            if dx > 0:
                rect.right = p.left
            elif dx < 0:
                rect.left = p.right
    rect.y += int(dy)
    on_ground = False
    for p in platforms:
        if rect.colliderect(p):
            if dy > 0:
                rect.bottom = p.top
                on_ground = True
            elif dy < 0:
                rect.top = p.bottom
    return on_ground

def draw_world():
    screen.fill(SKY)
    # سحب بسيطة
    for x, y in [(100, 85), (390, 125), (730, 75), (900, 150)]:
        pygame.draw.ellipse(screen, WHITE, (x - (camera_x // 3) % 1100, y, 70, 28))
        pygame.draw.ellipse(screen, WHITE, (x + 20 - (camera_x // 3) % 1100, y - 12, 60, 35))
    # تلال في الخلفية
    for x in range(-100, WIDTH + 250, 260):
        pygame.draw.ellipse(screen, (120, 190, 130), (x - (camera_x // 5) % 260, 360, 330, 150))
    # منصات وأرض
    for p in platforms:
        r = pygame.Rect(p.x - camera_x, p.y, p.width, p.height)
        pygame.draw.rect(screen, GROUND if p.y == GROUND_Y else BROWN, r)
        if p.y == GROUND_Y:
            pygame.draw.rect(screen, DARK_GREEN, (r.x, r.y, r.width, 9))
        else:
            pygame.draw.rect(screen, (70, 65, 60), (r.x, r.y + 10, r.width, 8))
    # أشجار زخرفية
    for x in range(180, WORLD_WIDTH, 420):
        sx = x - camera_x
        if -50 < sx < WIDTH + 50:
            pygame.draw.rect(screen, BROWN, (sx, GROUND_Y - 65, 14, 65))
            pygame.draw.circle(screen, DARK_GREEN, (sx + 7, GROUND_Y - 78), 33)

def draw_player(rect, facing, invulnerable):
    x, y = rect.x - camera_x, rect.y
    if invulnerable and (invulnerable // 5) % 2 == 0:
        return
    # شخصية بسيطة: رأس، جسم، ذراع وسلاح
    pygame.draw.rect(screen, PLAYER_COLOR, (x + 5, y + 19, 24, 29), border_radius=5)
    pygame.draw.circle(screen, (245, 205, 165), (x + 17, y + 10), 11)
    pygame.draw.rect(screen, DARK, (x + 5, y + 45, 10, 9))
    pygame.draw.rect(screen, DARK, (x + 20, y + 45, 10, 9))
    if facing == 1:
        pygame.draw.line(screen, (245, 205, 165), (x + 25, y + 27), (x + 36, y + 25), 6)
        pygame.draw.rect(screen, GRAY, (x + 31, y + 20, 22, 8), border_radius=2)
    else:
        pygame.draw.line(screen, (245, 205, 165), (x + 9, y + 27), (x - 2, y + 25), 6)
        pygame.draw.rect(screen, GRAY, (x - 19, y + 20, 22, 8), border_radius=2)

def draw_zombie(z):
    r = z["rect"]
    x, y = r.x - camera_x, r.y
    pygame.draw.rect(screen, ZOMBIE_COLOR, (x + 3, y + 12, 26, 28), border_radius=5)
    pygame.draw.circle(screen, (125, 180, 100), (x + 16, y + 8), 12)
    pygame.draw.circle(screen, RED, (x + 12, y + 7), 2)
    pygame.draw.circle(screen, RED, (x + 20, y + 7), 2)
    pygame.draw.line(screen, ZOMBIE_COLOR, (x + 5, y + 20), (x - 3, y + 29), 5)
    pygame.draw.line(screen, ZOMBIE_COLOR, (x + 27, y + 20), (x + 35, y + 29), 5)
    pygame.draw.rect(screen, DARK, (x + 5, y + 38, 9, 4))
    pygame.draw.rect(screen, DARK, (x + 19, y + 38, 9, 4))
    if z["hp"] == 1:
        pygame.draw.rect(screen, RED, (x, y - 8, 32, 4))

def fire_bullet(g):
    p = g["player"]
    bx = p.right if g["facing"] == 1 else p.left - 12
    by = p.y + 25
    g["bullets"].append({"rect": pygame.Rect(bx, by, 14, 5), "vx": 10 * g["facing"]})

running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_r and (game["lost"] or game["won"]):
                game = reset_game()
            if not game["lost"] and not game["won"]:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and game["on_ground"]:
                    game["vy"] = -13
                if event.key == pygame.K_x:
                    fire_bullet(game)

    keys = pygame.key.get_pressed()
    if not game["lost"] and not game["won"]:
        p = game["player"]
        game["vx"] = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            game["vx"] = -5
            game["facing"] = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            game["vx"] = 5
            game["facing"] = 1

        game["vy"] += GRAVITY
        if game["vy"] > 14:
            game["vy"] = 14
        game["on_ground"] = move_and_collide(p, game["vx"], game["vy"])
        if game["on_ground"]:
            game["vy"] = 0
        if p.left < 0:
            p.left = 0
        if p.right > WORLD_WIDTH:
            p.right = WORLD_WIDTH

        # الكاميرا تتبع اللاعب
        camera_x = max(0, min(WORLD_WIDTH - WIDTH, p.centerx - WIDTH // 2))

        # إطلاق النار المستمر عند الضغط على X
        if keys[pygame.K_x] and random.random() < 0.18:
            fire_bullet(game)

        for b in game["bullets"][:]:
            b["rect"].x += b["vx"]
            if b["rect"].right < 0 or b["rect"].left > WORLD_WIDTH:
                game["bullets"].remove(b)
                continue
            for z in game["zombies"]:
                if z["alive"] and b["rect"].colliderect(z["rect"]):
                    z["hp"] -= 1
                    if b in game["bullets"]:
                        game["bullets"].remove(b)
                    if z["hp"] <= 0:
                        z["alive"] = False
                        game["score"] += 10
                    break

        # الزومبي يتحركون باتجاه اللاعب عندما يكون قريبًا
        for z in game["zombies"]:
            if not z["alive"]:
                continue
            zr = z["rect"]
            if abs(p.centerx - zr.centerx) < 420:
                if p.centerx < zr.centerx:
                    zr.x -= z["speed"]
                elif p.centerx > zr.centerx:
                    zr.x += z["speed"]
            # تثبيت الزومبي على الأرض أو المنصة الأقرب تحته
            if zr.bottom < GROUND_Y and not any(zr.bottom == pl.top and zr.colliderect(pl) for pl in platforms[1:]):
                zr.y += 3
                if zr.bottom > GROUND_Y:
                    zr.bottom = GROUND_Y

            if p.colliderect(zr) and game["invulnerable"] <= 0:
                game["health"] -= 1
                game["invulnerable"] = 60
                # دفع اللاعب بعيدًا قليلًا
                game["vx"] = -7 if p.centerx < zr.centerx else 7
                if game["health"] <= 0:
                    game["lost"] = True

        if game["invulnerable"] > 0:
            game["invulnerable"] -= 1

        for coin in game["coins"][:]:
            if p.colliderect(coin):
                game["coins"].remove(coin)
                game["score"] += 5

        if p.centerx >= WORLD_WIDTH - 100 and all(not z["alive"] for z in game["zombies"]):
            game["won"] = True

    draw_world()

    # العملات
    for coin in game["coins"]:
        pygame.draw.circle(screen, YELLOW, (coin.centerx - camera_x, coin.centery), 10)
        pygame.draw.circle(screen, (255, 245, 150), (coin.centerx - camera_x - 3, coin.centery - 3), 999999999)

    # الرصاص
    for b in game["bullets"]:
        pygame.draw.rect(screen, YELLOW, (b["rect"].x - camera_x, b["rect"].y, b["rect"].width, b["rect"].height))

    for z in game["zombies"]:
        if z["alive"]:
            draw_zombie(z)

    draw_player(game["player"], game["facing"], game["invulnerable"])

    # واجهة اللعبة
    pygame.draw.rect(screen, (20, 25, 35), (12, 12, 290, 74), border_radius=8)
    draw_text(f"Health: {game['health']}   Score: {game['score']}", 24, 20)
    draw_text("Move: A/D or arrows | Jump: SPACE | Shoot: X", 24, 52, WHITE, small_font)
    draw_text("Defeat all zombies, collect coins, reach the end!", 18, HEIGHT - 30, DARK, small_font)

    if game["lost"] or game["won"]:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        screen.blit(overlay, (0, 0))
        title = "YOU WIN!" if game["won"] else "GAME OVER"
        title_surface = big_font.render(title, True, YELLOW if game["won"] else RED)
        screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 35)))
        subtitle = font.render("Press R to play again or ESC to exit", True, WHITE)
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25)))

    pygame.display.flip()

pygame.quit()
sys.exit()
