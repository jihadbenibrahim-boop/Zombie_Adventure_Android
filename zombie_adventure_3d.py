"""Zombie Adventure 3D: third-person shooter built with Ursina.

Install: python -m pip install ursina
Run:     python zombie_adventure_3d.py
Controls: WASD/arrows move, Space jump, left mouse or X shoot, R restart.
On-screen buttons are provided for touch devices.
"""

from ursina import *
import math
import os
import random
import tempfile
import wave
from array import array

app = Ursina()
window.title = "Zombie Adventure 3D"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(110, 175, 205)
window.fps_counter.enabled = True

# World/gameplay settings
WORLD_END = 34
PLAYER_START = Vec3(-30, 0, 0)
PLAYER_SPEED = 7.5
JUMP_SPEED = 8.5
GRAVITY = 22
BULLET_SPEED = 26
MAX_HEALTH = 5

# Use built-in procedural geometry so no external models are required.
Sky()
AmbientLight(color=color.rgba(150, 150, 170, 255))
sun = DirectionalLight(color=color.rgba(255, 238, 205, 255))
sun.look_at(Vec3(1, -2, -1))

# Ground and a long road corridor.
Entity(model="cube", color=color.rgb(74, 120, 66), scale=(90, 1, 34),
       position=(0, -0.55, 0), collider="box")
Entity(model="cube", color=color.rgb(82, 82, 78), scale=(76, 0.08, 12),
       position=(0, -0.015, 0))
for z in (-6.05, 6.05):
    Entity(model="cube", color=color.rgb(220, 202, 145), scale=(76, 0.12, 0.12),
           position=(0, 0.05, z))
# Broken low walls make the path read as a corridor without blocking movement.
for side in (-1, 1):
    for x in range(-35, 37, 10):
        Entity(model="cube", color=color.rgb(118, 112, 99),
               scale=(7.5, 1.5, 0.45), position=(x, 0.75, side * 8.7), collider="box")
        Entity(model="cube", color=color.rgb(154, 148, 129),
               scale=(7.5, 0.18, 0.5), position=(x, 1.55, side * 8.7))

# Houses, roofs, doors and windows on both sides of the street.
def add_house(x, z, tint):
    body = Entity(model="cube", color=tint, scale=(5, 3.2, 4),
                  position=(x, 1.6, z), collider="box")
    Entity(model="cube", color=color.rgb(91, 48, 41), scale=(5.7, 0.45, 4.7),
           position=(x, 3.35, z), rotation=(0, 0, 0))
    Entity(model="cube", color=color.rgb(67, 45, 38), scale=(0.9, 1.8, 0.12),
           position=(x, 0.9, z - (2.06 if z < 0 else -2.06)))
    for wx in (-1.45, 1.45):
        Entity(model="cube", color=color.rgb(153, 213, 220), scale=(0.85, 0.8, 0.12),
               position=(x + wx, 2.15, z - (2.07 if z < 0 else -2.07)))
    # Small porch light
    lamp = Entity(model="sphere", color=color.rgb(255, 220, 125), scale=0.22,
                  position=(x, 2.8, z - (2.2 if z < 0 else -2.2)))
    PointLight(parent=lamp, color=color.rgb(255, 190, 100), intensity=0.45, range=7)

for i, x in enumerate((-25, -13, 1, 15, 27)):
    add_house(x, -12, color.rgb(157 + (i % 2) * 12, 117, 91))
    add_house(x - 4, 12, color.rgb(130, 143 + (i % 2) * 10, 112))

# Street lamps and trees provide depth and lighting landmarks.
for x in range(-30, 35, 10):
    for z in (-7.2, 7.2):
        Entity(model="cube", color=color.rgb(50, 52, 48), scale=(0.16, 3.5, 0.16),
               position=(x, 1.75, z))
        lamp = Entity(model="sphere", color=color.rgb(255, 229, 160), scale=0.32,
                      position=(x, 3.55, z))
        PointLight(parent=lamp, color=color.rgb(255, 210, 135), intensity=0.7, range=12)
for x in range(-32, 38, 8):
    for z in (-15, 15):
        Entity(model="cube", color=color.rgb(103, 70, 47), scale=(0.55, 2.4, 0.55),
               position=(x, 1.2, z))
        Entity(model="sphere", color=color.rgb(43, 105, 57), scale=(2.2, 2.5, 2.2),
               position=(x, 3.1, z))

# Goal marker at the far end of the street.
Entity(model="cube", color=color.rgb(230, 195, 72), scale=(0.25, 4, 0.25),
       position=(WORLD_END, 2, 0))
Entity(model="cube", color=color.rgb(225, 75, 58), scale=(0.25, 4, 0.25),
       position=(WORLD_END + 2, 2, 0))
Entity(model="cube", color=color.rgb(239, 218, 145), scale=(2.2, 0.2, 0.25),
       position=(WORLD_END + 1, 3.85, 0))

# Player model and simple visible weapon.
player = Entity(model="cube", color=color.rgb(45, 90, 220), scale=(0.85, 1.7, 0.65),
                position=PLAYER_START, collider="box")
player_head = Entity(parent=player, model="sphere", color=color.rgb(231, 190, 150),
                     scale=(0.68, 0.52, 0.68), position=(0, 0.68, 0))
Entity(parent=player, model="cube", color=color.rgb(45, 48, 55), scale=(0.22, 0.18, 0.9),
       position=(0.28, 0.12, 0.55))
player.vy = 0
player.health = MAX_HEALTH
player.score = 0
player.invulnerable = 0
player.grounded = True

# Gameplay entities and state.
zombies = []
bullets = []
coins = []
state = "menu"
fire_cooldown = 0.0
mobile_move = Vec3(0, 0, 0)
mobile_move_timer = 0.0
mobile_jump = False

# Procedurally create short WAV effects; game still works if audio is unavailable.
audio_dir = tempfile.mkdtemp(prefix="zombie_adventure_audio_")
def make_tone(filename, frequency, duration, volume=0.18, second_frequency=None):
    path = os.path.join(audio_dir, filename)
    sample_rate = 22050
    samples = array("h")
    count = int(sample_rate * duration)
    for n in range(count):
        fade = min(1.0, n / 250, (count - n) / 500)
        t = n / sample_rate
        value = math.sin(2 * math.pi * frequency * t)
        if second_frequency:
            value = (value + math.sin(2 * math.pi * second_frequency * t)) * 0.5
        samples.append(int(32767 * volume * max(0, fade) * value))
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples.tobytes())
    return path

sound_effects = {}
try:
    for name, freq, duration in (("shot", 720, .08), ("hit", 115, .18),
                                 ("coin", 1000, .12), ("win", 523, .45),
                                 ("lose", 180, .55)):
        sound_effects[name] = Audio(make_tone(name + ".wav", freq, duration,
                                              second_frequency=freq * 1.5 if name == "win" else None),
                                    autoplay=False, volume=.45)
except Exception:
    sound_effects = {}

def play_sound(name):
    sound = sound_effects.get(name)
    if sound:
        try:
            sound.stop()
            sound.play()
        except Exception:
            pass

# HUD and screens.
hud = Text(parent=camera.ui, text="", position=(-0.86, 0.45), scale=1.15,
           background=True, color=color.white)
help_text = Text(parent=camera.ui,
                 text="WASD / arrows: move   SPACE: jump   X or left click: shoot",
                 position=(-0.86, 0.40), scale=0.75, color=color.white)
message = Text(parent=camera.ui, text="", origin=(0, 0), position=(0, 0.22),
               scale=2.2, color=color.yellow)

menu_panel = Entity(parent=camera.ui, model="quad", color=color.rgba(12, 20, 28, 225),
                    scale=(0.76, 0.70), position=(0, 0))
Text(parent=menu_panel, text="ZOMBIE ADVENTURE 3D", origin=(0, 0),
     position=(0, 0.30), scale=1.5, color=color.rgb(245, 215, 115))
Text(parent=menu_panel, text="Survive the street, defeat every zombie, then reach the gate.",
     origin=(0, 0), position=(0, 0.12), scale=0.9, color=color.white)

end_panel = Entity(parent=camera.ui, model="quad", color=color.rgba(12, 20, 28, 230),
                   scale=(0.64, 0.50), position=(0, 0), enabled=False)
end_title = Text(parent=end_panel, text="", origin=(0, 0), position=(0, 0.15),
                 scale=2, color=color.yellow)
Text(parent=end_panel, text="Press R or tap Restart to play again", origin=(0, 0),
     position=(0, -0.02), scale=0.9, color=color.white)

# Touch controls: tap directional buttons to move briefly; hold desktop keys for continuous motion.
def tap_move(direction):
    global mobile_move, mobile_move_timer
    mobile_move = direction
    mobile_move_timer = 0.24

def tap_jump():
    global mobile_jump
    mobile_jump = True

def tap_shoot():
    fire_bullet()

controls = Entity(parent=camera.ui, enabled=False)
def touch_button(label, pos, callback, tint=color.rgba(35, 45, 55, 210)):
    return Button(parent=controls, text=label, position=pos, scale=(0.075, 0.075),
                  color=tint, text_color=color.white, on_click=callback)

touch_button("◀", (-0.78, -0.35), lambda: tap_move(Vec3(-1, 0, 0)))
touch_button("▶", (-0.60, -0.35), lambda: tap_move(Vec3(1, 0, 0)))
touch_button("▲", (-0.69, -0.25), lambda: tap_move(Vec3(0, 0, 1)))
touch_button("▼", (-0.69, -0.45), lambda: tap_move(Vec3(0, 0, -1)))
touch_button("JUMP", (0.65, -0.35), tap_jump, color.rgba(45, 90, 180, 220))
touch_button("FIRE", (0.80, -0.35), tap_shoot, color.rgba(175, 55, 45, 230))

# Button references are created after callbacks; functions resolve these globals when used.
def start_game():
    global state
    reset_game()
    state = "playing"
    menu_panel.enabled = False
    end_panel.enabled = False
    controls.enabled = True
    message.text = ""

def restart_game():
    start_game()

def show_end(result):
    global state
    state = result
    controls.enabled = False
    end_panel.enabled = True
    end_title.text = "YOU WIN!" if result == "won" else "GAME OVER"
    end_title.color = color.yellow if result == "won" else color.rgb(245, 80, 65)
    play_sound("win" if result == "won" else "lose")

start_button = Button(parent=menu_panel, text="START GAME", position=(0, -0.12),
                      scale=(0.28, 0.09), color=color.rgb(58, 130, 75),
                      text_color=color.white, on_click=start_game)
restart_button = Button(parent=end_panel, text="RESTART", position=(0, -0.19),
                        scale=(0.25, 0.09), color=color.rgb(58, 130, 75),
                        text_color=color.white, on_click=restart_game)

# Creation/reset functions.
def clear_entities(items):
    for item in items:
        destroy(item)
    items.clear()

def spawn_zombies():
    for x, z in [(-20, -3), (-14, 3), (-7, -2), (1, 3), (9, -3),
                 (16, 2), (23, -2), (29, 3)]:
        zombie = Entity(model="cube", color=color.rgb(80, 150, 70),
                        scale=(0.9, 1.8, 0.7), position=(x, 0.9, z), collider="box")
        Entity(parent=zombie, model="sphere", color=color.rgb(125, 180, 100),
               scale=(0.72, 0.58, 0.72), position=(0, 0.68, 0))
        # Glowing eyes
        for eye_x in (-0.18, 0.18):
            Entity(parent=zombie, model="sphere", color=color.red, scale=0.09,
                   position=(eye_x, 0.74, 0.32))
        zombie.hp = 2
        zombie.speed = random.uniform(1.4, 2.0)
        zombie.alive = True
        zombies.append(zombie)

def spawn_coins():
    for x, z in [(-23, 2), (-11, -4), (0, 4), (12, -4), (22, 4), (31, 0)]:
        coin = Entity(model="sphere", color=color.rgb(255, 210, 40), scale=0.42,
                      position=(x, 1.1, z))
        coins.append(coin)

def reset_game():
    global fire_cooldown, mobile_move_timer, mobile_jump
    clear_entities(bullets)
    clear_entities(zombies)
    clear_entities(coins)
    player.position = PLAYER_START
    player.rotation_y = 0
    player.vy = 0
    player.health = MAX_HEALTH
    player.score = 0
    player.invulnerable = 0
    player.grounded = True
    fire_cooldown = 0
    mobile_move_timer = 0
    mobile_jump = False
    spawn_zombies()
    spawn_coins()
    update_hud()

# Combat / HUD.
def fire_bullet():
    global fire_cooldown
    if state != "playing" or fire_cooldown > 0:
        return
    direction = player.forward
    bullet = Entity(model="sphere", color=color.yellow, scale=0.18,
                    position=player.position + Vec3(0, 0.25, 0) + direction * 0.8)
    bullet.velocity = direction * BULLET_SPEED
    bullet.life = 1.7
    bullets.append(bullet)
    fire_cooldown = 0.22
    play_sound("shot")

def update_hud():
    hud.text = f"Health: {player.health}/{MAX_HEALTH}    Score: {player.score}    Zombies: {sum(1 for z in zombies if z.alive)}"

def take_damage():
    if player.invulnerable > 0 or state != "playing":
        return
    player.health -= 1
    player.invulnerable = 1.0
    play_sound("hit")
    if player.health <= 0:
        player.health = 0
        update_hud()
        show_end("lost")

# Third-person follow camera.
camera.position = player.position + Vec3(0, 6.5, -10)
camera.fov = 78

def update():
    global fire_cooldown, mobile_move_timer, mobile_jump
    dt = time.dt
    if state != "playing":
        return

    fire_cooldown = max(0, fire_cooldown - dt)
    player.invulnerable = max(0, player.invulnerable - dt)
    if player.invulnerable > 0 and int(player.invulnerable * 12) % 2 == 0:
        player.color = color.rgb(245, 245, 245)
    else:
        player.color = color.rgb(45, 90, 220)

    move_x = held_keys["d"] + held_keys["right arrow"] - held_keys["a"] - held_keys["left arrow"]
    move_z = held_keys["w"] + held_keys["up arrow"] - held_keys["s"] - held_keys["down arrow"]
    if mobile_move_timer > 0:
        move_x += mobile_move.x
        move_z += mobile_move.z
        mobile_move_timer = max(0, mobile_move_timer - dt)
    movement = Vec3(move_x, 0, move_z)
    if movement.length() > 0:
        movement = movement.normalized()
        player.position += movement * PLAYER_SPEED * dt
        player.rotation_y = math.degrees(math.atan2(movement.x, movement.z))

    if (held_keys["space"] or mobile_jump) and player.grounded:
        player.vy = JUMP_SPEED
        player.grounded = False
    mobile_jump = False
    player.vy -= GRAVITY * dt
    player.y += player.vy * dt
    if player.y <= 0.85:
        player.y = 0.85
        player.vy = 0
        player.grounded = True

    player.x = clamp(player.x, -WORLD_END, WORLD_END + 3)
    player.z = clamp(player.z, -5.0, 5.0)
    camera_target = player.position + Vec3(0, 6.0, -10.5)
    camera.position = lerp(camera.position, camera_target, min(1, dt * 5))
    camera.look_at(player.position + Vec3(0, 0.8, 1.2))

    if held_keys["x"] or held_keys["left mouse"]:
        fire_bullet()

    for bullet in bullets[:]:
        bullet.position += bullet.velocity * dt
        bullet.life -= dt
        hit_target = None
        for zombie in zombies:
            if zombie.alive and (bullet.position - zombie.position).length() < 0.95:
                hit_target = zombie
                break
        if hit_target:
            hit_target.hp -= 1
            destroy(bullet)
            bullets.remove(bullet)
            play_sound("hit")
            if hit_target.hp <= 0:
                hit_target.alive = False
                hit_target.enabled = False
                player.score += 10
            update_hud()
        elif bullet.life <= 0 or abs(bullet.x) > WORLD_END + 8:
            destroy(bullet)
            bullets.remove(bullet)

    for zombie in zombies:
        if not zombie.alive:
            continue
        delta = player.position - zombie.position
        horizontal = Vec3(delta.x, 0, delta.z)
        distance = horizontal.length()
        if distance < 16 and distance > 1.05:
            direction = horizontal.normalized()
            zombie.position += direction * zombie.speed * dt
            zombie.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
        if distance < 1.35:
            take_damage()

    for coin in coins[:]:
        coin.rotation_y += 100 * dt
        if (coin.position - player.position).length() < 1.25:
            destroy(coin)
            coins.remove(coin)
            player.score += 5
            play_sound("coin")
            update_hud()

    if player.x >= WORLD_END and all(not zombie.alive for zombie in zombies):
        show_end("won")
    update_hud()

# Keyboard shortcuts / menu flow.
def input(key):
    if key == "escape":
        application.quit()
    elif key == "left mouse down" and state == "playing":
        fire_bullet()
    elif key == "r" and state in ("won", "lost"):
        start_game()

update_hud()
app.run()
