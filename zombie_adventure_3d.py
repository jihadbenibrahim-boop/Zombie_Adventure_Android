"""مغامرة الزومبي ثلاثية الأبعاد.
التثبيت: python -m pip install ursina
لأفضل عرض للعربية اختيارياً: python -m pip install arabic-reshaper python-bidi
"""

from ursina import *
import math
import os
import random
import tempfile
import wave
from array import array

app = Ursina()
window.title = "مغامرة الزومبي 3D"
window.borderless = False
window.fullscreen = False
window.color = color.rgb(40, 55, 70)
window.fps_counter.enabled = True

# دعم تشكيل العربية اختيارياً. إن لم تتوفر المكتبتان سيظل النص العربي ظاهراً
# في البيئات التي تحتوي خطاً عربياً مناسباً.
def ar(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text

WORLD_END = 34
PLAYER_START = Vec3(-42, 0.85, 0)
PLAYER_SPEED, JUMP_SPEED, GRAVITY = 8.2, 8.5, 22
BULLET_SPEED = 30
MAX_HEALTH = 5
MAG_SIZE, START_RESERVE, START_GRENADES = 24, 120, 3
MAX_WAVES = 3

Sky()
AmbientLight(color=color.rgba(125, 125, 145, 255))
sun = DirectionalLight(color=color.rgba(255, 230, 195, 255))
sun.look_at(Vec3(1, -2, -1))

# الردهة: أرضية ومدخل مفتوح، مع إطار وباب جانبي لا يسد الطريق.
Entity(model="cube", color=color.rgb(74, 78, 82), scale=(12, .18, 9),
       position=(-41, -.08, 0))
for z in (-4.35, 4.35):
    Entity(model="cube", color=color.rgb(132, 130, 121), scale=(10, 3.2, .35),
           position=(-41, 1.5, z), collider="box")
for x in (-46, -36):
    Entity(model="cube", color=color.rgb(132, 130, 121), scale=(.35, 3.2, 8.7),
           position=(x, 1.5, 0), collider="box")
# إطار بوابة الخروج إلى الشارع (فتحة بعرض كافٍ في المنتصف).
for z in (-2.0, 2.0):
    Entity(model="cube", color=color.rgb(91, 61, 43), scale=(.35, 3.2, .35),
           position=(-35.6, 1.6, z))
Entity(model="cube", color=color.rgb(91, 61, 43), scale=(.35, .35, 4.3),
       position=(-35.6, 3.2, 0))
# باب خشبي على جانب الردهة، مع لافتة وضوء.
Entity(model="cube", color=color.rgb(85, 51, 37), scale=(.12, 2.2, 1.1),
       position=(-41, 1.05, 3.9))
Entity(model="cube", color=color.rgb(232, 184, 95), scale=(.15, .55, 2.4),
       position=(-41, 2.55, 0))
Text(parent=camera.ui, text=ar("ردهة النجاة"), position=(-.14, .20),
     scale=1.1, color=color.rgb(255, 223, 130))
light_orb = Entity(model="sphere", color=color.rgb(255, 212, 138), scale=.35,
                   position=(-41, 3.4, 0))
PointLight(parent=light_orb, color=color.rgb(255, 190, 110), intensity=1.5, range=12)

# الشارع والممرات.
Entity(model="cube", color=color.rgb(74, 120, 66), scale=(90, 1, 34),
       position=(0, -.55, 0), collider="box")
Entity(model="cube", color=color.rgb(75, 76, 75), scale=(82, .08, 12),
       position=(0, -.015, 0))
for z in (-6.05, 6.05):
    Entity(model="cube", color=color.rgb(225, 203, 140), scale=(82, .12, .12),
           position=(0, .05, z))
for side in (-1, 1):
    for x in range(-32, 38, 10):
        Entity(model="cube", color=color.rgb(118, 112, 99), scale=(7.5, 1.5, .45),
               position=(x, .75, side * 8.7), collider="box")
        Entity(model="cube", color=color.rgb(154, 148, 129), scale=(7.5, .18, .5),
               position=(x, 1.55, side * 8.7))

# من��زل على جانبي الطريق.
def add_house(x, z, tint):
    Entity(model="cube", color=tint, scale=(5, 3.2, 4), position=(x, 1.6, z), collider="box")
    Entity(model="cube", color=color.rgb(91, 48, 41), scale=(5.7, .45, 4.7),
           position=(x, 3.35, z))
    front = -1 if z < 0 else 1
    Entity(model="cube", color=color.rgb(67, 45, 38), scale=(.9, 1.8, .12),
           position=(x, .9, z + front * 2.06))
    for wx in (-1.45, 1.45):
        Entity(model="cube", color=color.rgb(153, 213, 220), scale=(.85, .8, .12),
               position=(x + wx, 2.15, z + front * 2.07))
    lamp = Entity(model="sphere", color=color.rgb(255, 220, 125), scale=.22,
                  position=(x, 2.8, z + front * 2.2))
    PointLight(parent=lamp, color=color.rgb(255, 190, 100), intensity=.4, range=7)

for i, x in enumerate((-25, -13, 1, 15, 27)):
    add_house(x, -12, color.rgb(157 + (i % 2) * 12, 117, 91))
    add_house(x - 4, 12, color.rgb(130, 143 + (i % 2) * 10, 112))

# أعمدة إنارة وأشجار.
for x in range(-30, 35, 10):
    for z in (-7.2, 7.2):
        Entity(model="cube", color=color.rgb(50, 52, 48), scale=(.16, 3.5, .16),
               position=(x, 1.75, z))
        lamp = Entity(model="sphere", color=color.rgb(255, 229, 160), scale=.32,
                      position=(x, 3.55, z))
        PointLight(parent=lamp, color=color.rgb(255, 210, 135), intensity=.6, range=11)
for x in range(-32, 38, 8):
    for z in (-15, 15):
        Entity(model="cube", color=color.rgb(103, 70, 47), scale=(.55, 2.4, .55),
               position=(x, 1.2, z))
        Entity(model="sphere", color=color.rgb(43, 105, 57), scale=(2.2, 2.5, 2.2),
               position=(x, 3.1, z))

# بوابة نهاية المرحلة.
for x, tint in ((WORLD_END, color.rgb(230, 195, 72)),
                (WORLD_END + 2, color.rgb(225, 75, 58))):
    Entity(model="cube", color=tint, scale=(.25, 4, .25), position=(x, 2, 0))
Entity(model="cube", color=color.rgb(239, 218, 145), scale=(2.2, .2, .25),
       position=(WORLD_END + 1, 3.85, 0))

player = Entity(model="cube", color=color.rgb(45, 90, 220), scale=(.85, 1.7, .65),
                position=PLAYER_START, collider="box")
Entity(parent=player, model="sphere", color=color.rgb(231, 190, 150),
       scale=(.68, .52, .68), position=(0, .68, 0))
Entity(parent=player, model="cube", color=color.rgb(45, 48, 55),
       scale=(.22, .18, .9), position=(.28, .12, .55))
player.vy = 0
player.health = MAX_HEALTH
player.score = 0
player.invulnerable = 0
player.grounded = True
player.ammo = MAG_SIZE
player.reserve = START_RESERVE
player.grenades = START_GRENADES

zombies, bullets, coins, grenades, explosions = [], [], [], [], []
state = "menu"
fire_cooldown = 0.0
reload_timer = 0.0
wave = 1
wave_delay = 0.0
mobile_move = Vec3(0, 0, 0)
mobile_move_timer = 0.0
mobile_jump = False

# مؤثرات صوتية مولدة محلياً؛ لا تحتاج ملفات صوت إضافية.
audio_dir = tempfile.mkdtemp(prefix="zombie_game_audio_")
def make_tone(filename, frequency, duration, volume=.3, second_frequency=None):
    path = os.path.join(audio_dir, filename)
    rate = 22050
    samples = array("h")
    count = int(rate * duration)
    for n in range(count):
        fade = min(1.0, n / 220, (count - n) / 400)
        t = n / rate
        value = math.sin(2 * math.pi * frequency * t)
        if second_frequency:
            value = (value + math.sin(2 * math.pi * second_frequency * t)) / 2
        samples.append(int(32767 * volume * max(0, fade) * value))
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())
    return path

sounds = {}
try:
    for name, freq, duration in (("shot", 150, .14), ("hit", 90, .22),
                                 ("boom", 65, .55), ("reload", 420, .18),
                                 ("coin", 950, .15), ("win", 520, .55), ("lose", 165, .65)):
        sounds[name] = Audio(make_tone(name + ".wav", freq, duration,
                                       second_frequency=freq * 1.45 if name == "boom" else None),
                             autoplay=False, volume=.75)
except Exception:
    sounds = {}

def play_sound(name):
    sound = sounds.get(name)
    if sound:
        try:
            sound.stop()
            sound.play()
        except Exception:
            pass

# واجهة عربية كبيرة.
hud = Text(parent=camera.ui, text="", origin=(1, 0), position=(.88, .46),
           scale=1.35, background=True, color=color.white)
help_text = Text(parent=camera.ui,
    text=ar("الحركة: WASD أو الأسهم | قفز: مسافة | إطلاق: X/النقر | إعادة تعبئة: R | قنبلة: G"),
    origin=(1, 0), position=(.88, .37), scale=.82, color=color.white)
center_message = Text(parent=camera.ui, text="", origin=(0, 0), position=(0, .27),
                      scale=1.6, color=color.yellow)
menu_panel = Entity(parent=camera.ui, model="quad", color=color.rgba(8, 15, 24, 238),
                    scale=(.9, .88), position=(0, 0))
Text(parent=menu_panel, text=ar("مغامرة الزومبي ثلاثية الأبعاد"), origin=(0, 0),
     position=(0, .29), scale=1.5, color=color.rgb(255, 220, 125))
Text(parent=menu_panel, text=ar("قاتل موجات الزومبي، اجمع النقاط، ثم اعبر البوابة!"),
     origin=(0, 0), position=(0, .13), scale=.95, color=color.white)
Text(parent=menu_panel, text=ar("تحكم: WASD | قفز: مسافة | إطلاق: X | قنابل: G | تعبئة: R"),
     origin=(0, 0), position=(0, .02), scale=.82, color=color.rgb(205, 220, 230))
end_panel = Entity(parent=camera.ui, model="quad", color=color.rgba(8, 15, 24, 240),
                   scale=(.78, .62), position=(0, 0), enabled=False)
end_title = Text(parent=end_panel, text="", origin=(0, 0), position=(0, .16),
                 scale=2.1, color=color.yellow)
Text(parent=end_panel, text=ar("اضغط R أو زر إعادة اللعب للبدء من جديد"), origin=(0, 0),
     position=(0, -.02), scale=.9, color=color.white)

# أزرار لمس للهواتف.
controls = Entity(parent=camera.ui, enabled=False)
def tap_move(direction):
    global mobile_move, mobile_move_timer
    mobile_move, mobile_move_timer = direction, .25

def tap_jump():
    global mobile_jump
    mobile_jump = True

def touch_button(label, pos, callback, tint=color.rgba(35, 45, 55, 220)):
    return Button(parent=controls, text=label, position=pos, scale=(.09, .09),
                  color=tint, text_color=color.white, on_click=callback)

touch_button("◀", (-.78, -.35), lambda: tap_move(Vec3(-1, 0, 0)))
touch_button("▶", (-.60, -.35), lambda: tap_move(Vec3(1, 0, 0)))
touch_button("▲", (-.69, -.25), lambda: tap_move(Vec3(0, 0, 1)))
touch_button("▼", (-.69, -.45), lambda: tap_move(Vec3(0, 0, -1)))
touch_button(ar("قفز"), (.57, -.35), tap_jump, color.rgba(45, 90, 180, 230))
touch_button(ar("إطلاق"), (.72, -.35), lambda: fire_bullet(), color.rgba(175, 55, 45, 230))
touch_button(ar("قنبلة"), (.87, -.35), lambda: throw_grenade(), color.rgba(160, 95, 25, 230))

# إنشاء وإزالة الكيانات.
def clear_entities(items):
    for item in items:
        destroy(item)
    items.clear()

def spawn_zombies(current_wave):
    count = 7 + current_wave * 3
    for i in range(count):
        x = random.uniform(-24, WORLD_END - 2)
        z = random.choice((-4, -2, 2, 4))
        zombie = Entity(model="cube", color=color.rgb(75, 145, 65),
                        scale=(.9, 1.8, .7), position=(x, .9, z), collider="box")
        Entity(parent=zombie, model="sphere", color=color.rgb(125, 180, 100),
               scale=(.72, .58, .72), position=(0, .68, 0))
        for eye_x in (-.18, .18):
            Entity(parent=zombie, model="sphere", color=color.red, scale=.09,
                   position=(eye_x, .74, .32))
        zombie.hp = 2 if current_wave < 3 else 3
        zombie.speed = random.uniform(1.5, 2.2) + current_wave * .25
        zombie.alive = True
        zombies.append(zombie)

def spawn_coins():
    for x, z in [(-23, 2), (-11, -4), (0, 4), (12, -4), (22, 4), (31, 0)]:
        coins.append(Entity(model="sphere", color=color.rgb(255, 210, 40), scale=.42,
                            position=(x, 1.1, z)))

def update_hud():
    alive = sum(1 for z in zombies if z.alive)
    hud.text = ar(f"الصحة: {player.health}/{MAX_HEALTH}   الذخيرة: {player.ammo}/{player.reserve}   القنابل: {player.grenades}   النقاط: {player.score}   الموجة: {wave}/{MAX_WAVES}   أعداء: {alive}")

def reset_game():
    global fire_cooldown, reload_timer, wave, wave_delay, mobile_move_timer, mobile_jump
    for group in (bullets, zombies, coins, grenades, explosions):
        clear_entities(group)
    player.position = PLAYER_START
    player.rotation_y = 0
    player.vy = 0
    player.health = MAX_HEALTH
    player.score = 0
    player.invulnerable = 0
    player.grounded = True
    player.ammo, player.reserve, player.grenades = MAG_SIZE, START_RESERVE, START_GRENADES
    fire_cooldown = reload_timer = wave_delay = mobile_move_timer = 0
    mobile_jump = False
    wave = 1
    spawn_zombies(wave)
    spawn_coins()
    update_hud()

def start_game():
    global state
    reset_game()
    state = "playing"
    menu_panel.enabled = False
    end_panel.enabled = False
    controls.enabled = True
    center_message.text = ""

def finish_game(won):
    global state
    state = "won" if won else "lost"
    controls.enabled = False
    end_panel.enabled = True
    end_title.text = ar("أحسنت! لقد نجوت" if won else "انتهت اللعبة")
    end_title.color = color.yellow if won else color.rgb(245, 80, 65)
    play_sound("win" if won else "lose")

def reload_weapon():
    global reload_timer
    if state != "playing" or reload_timer > 0 or player.ammo >= MAG_SIZE or player.reserve <= 0:
        return
    reload_timer = 1.0
    play_sound("reload")

def fire_bullet():
    global fire_cooldown
    if state != "playing" or fire_cooldown > 0 or reload_timer > 0:
        return
    if player.ammo <= 0:
        reload_weapon()
        return
    direction = player.forward
    bullet = Entity(model="sphere", color=color.yellow, scale=.2,
                    position=player.position + Vec3(0, .25, 0) + direction * .85)
    bullet.velocity = direction * BULLET_SPEED
    bullet.life = 1.5
    bullets.append(bullet)
    player.ammo -= 1
    fire_cooldown = .16
    play_sound("shot")
    update_hud()

def throw_grenade():
    if state != "playing" or player.grenades <= 0:
        return
    direction = player.forward
    grenade = Entity(model="sphere", color=color.rgb(63, 75, 55), scale=.38,
                     position=player.position + Vec3(0, .5, 0) + direction * .8)
    grenade.velocity = direction * 8 + Vec3(0, 5, 0)
    grenade.fuse = 1.1
    grenades.append(grenade)
    player.grenades -= 1
    play_sound("shot")
    update_hud()

def explode(grenade):
    center = grenade.position
    effect = Entity(model="sphere", color=color.rgba(255, 115, 25, 170),
                    scale=.5, position=center)
    effect.life = .35
    explosions.append(effect)
    for zombie in zombies:
        if zombie.alive and (zombie.position - center).length() < 5.2:
            zombie.hp -= 3
            if zombie.hp <= 0:
                zombie.alive = False
                zombie.enabled = False
                player.score += 10
    destroy(grenade)
    grenades.remove(grenade)
    play_sound("boom")
    update_hud()

def take_damage():
    if player.invulnerable > 0 or state != "playing":
        return
    player.health -= 1
    player.invulnerable = 1.0
    play_sound("hit")
    if player.health <= 0:
        player.health = 0
        update_hud()
        finish_game(False)

camera.position = player.position + Vec3(0, 6.5, -10)
camera.fov = 78

# انتقال بين موجات الزومبي.
def advance_waves(dt):
    global wave, wave_delay
    if any(z.alive for z in zombies) or wave >= MAX_WAVES:
        return
    if wave_delay <= 0:
        wave_delay = 2.0
        center_message.text = ar("استعد للموجة التالية!")
    else:
        wave_delay -= dt
        if wave_delay <= 0:
            wave += 1
            spawn_zombies(wave)
            center_message.text = ar(f"الموجة {wave}!")
            update_hud()


def update():
    global fire_cooldown, reload_timer, mobile_move_timer, mobile_jump
    dt = time.dt
    if state != "playing":
        return
    fire_cooldown = max(0, fire_cooldown - dt)
    if reload_timer > 0:
        reload_timer -= dt
        if reload_timer <= 0:
            needed = MAG_SIZE - player.ammo
            loaded = min(needed, player.reserve)
            player.ammo += loaded
            player.reserve -= loaded
            reload_timer = 0
            update_hud()
    player.invulnerable = max(0, player.invulnerable - dt)
    player.color = (color.rgb(245, 245, 245) if player.invulnerable > 0 and
                    int(player.invulnerable * 12) % 2 == 0 else color.rgb(45, 90, 220))

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
    if player.y <= .85:
        player.y, player.vy, player.grounded = .85, 0, True
    player.x = clamp(player.x, -WORLD_END - 9, WORLD_END + 3)
    player.z = clamp(player.z, -5, 5)
    camera_target = player.position + Vec3(0, 6, -10.5)
    camera.position = lerp(camera.position, camera_target, min(1, dt * 5))
    camera.look_at(player.position + Vec3(0, .8, 1.2))

    if held_keys["x"] or held_keys["left mouse"]:
        fire_bullet()
    for bullet in bullets[:]:
        bullet.position += bullet.velocity * dt
        bullet.life -= dt
        target = next((z for z in zombies if z.alive and
                       (bullet.position - z.position).length() < 1.0), None)
        if target:
            target.hp -= 1
            destroy(bullet)
            bullets.remove(bullet)
            if target.hp <= 0:
                target.alive = False
                target.enabled = False
                player.score += 10
                play_sound("hit")
        elif bullet.life <= 0 or abs(bullet.x) > WORLD_END + 10:
            destroy(bullet)
            bullets.remove(bullet)

    for grenade in grenades[:]:
        grenade.position += grenade.velocity * dt
        grenade.velocity.y -= GRAVITY * dt
        if grenade.y < .25:
            grenade.y = .25
            grenade.velocity.y = abs(grenade.velocity.y) * .35
            grenade.velocity.x *= .75
            grenade.velocity.z *= .75
        grenade.fuse -= dt
        if grenade.fuse <= 0:
            explode(grenade)
    for effect in explosions[:]:
        effect.life -= dt
        effect.scale += Vec3(12, 12, 12) * dt
        if effect.life <= 0:
            destroy(effect)
            explosions.remove(effect)

    for zombie in zombies:
        if not zombie.alive:
            continue
        delta = player.position - zombie.position
        horizontal = Vec3(delta.x, 0, delta.z)
        distance = horizontal.length()
        if distance < 20 and distance > 1.05:
            direction = horizontal.normalized()
            zombie.position += direction * zombie.speed * dt
            zombie.rotation_y = math.degrees(math.atan2(direction.x, direction.z))
        if distance < 1.4:
            take_damage()

    for coin in coins[:]:
        coin.rotation_y += 120 * dt
        if (coin.position - player.position).length() < 1.25:
            destroy(coin)
            coins.remove(coin)
            player.score += 5
            play_sound("coin")
    advance_waves(dt)
    if wave == MAX_WAVES and not any(z.alive for z in zombies) and player.x >= WORLD_END:
        finish_game(True)
    update_hud()

# واجهات البدء والنهاية وأزرارها.
Button(parent=menu_panel, text=ar("ابدأ المغامرة"), position=(0, -.16),
       scale=(.32, .1), color=color.rgb(45, 125, 70), text_color=color.white,
       on_click=start_game)
Button(parent=end_panel, text=ar("إعادة اللعب"), position=(0, -.18),
       scale=(.30, .1), color=color.rgb(45, 125, 70), text_color=color.white,
       on_click=start_game)

def input(key):
    if key == "escape":
        application.quit()
    elif key == "left mouse down":
        fire_bullet()
    elif key == "g":
        throw_grenade()
    elif key == "r":
        if state in ("won", "lost"):
            start_game()
        else:
            reload_weapon()

update_hud()
app.run()
