import pygame
import os
import config

SOUND_DIR = config.resource_path("sounds")
MUSIC_DIR = os.path.join(SOUND_DIR, "music")
SFX_DIR = os.path.join(SOUND_DIR, "sfx")

VOLUME = 0.7
muted = False
current_music = None
_sfx_cache = {}
graze_sound = None

def init_mixer():
    try:
        pygame.mixer.init()
        pygame.mixer.set_num_channels(64)
        return True
    except pygame.error:
        return False

def find_audio_file(folder, base_name):
    for ext in (".ogg", ".mp3", ".wav"):
        path = os.path.join(folder, base_name + ext)
        if os.path.exists(path):
            return path
    return None

def play_music_any(candidates, loop=-1, start_pos=0.0):
    global current_music
    if not pygame.mixer.get_init():
        return
    resolved = None
    for name in candidates:
        path = find_audio_file(MUSIC_DIR, name)
        if path:
            resolved = path
            break
    if resolved == current_music:
        return
    if resolved is None:
        current_music = None
        return
    try:
        pygame.mixer.music.load(resolved)
        pygame.mixer.music.set_volume(0 if muted else VOLUME)
        pygame.mixer.music.play(loop, start_pos)
        current_music = resolved
    except pygame.error:
        current_music = None

def stop_music():
    global current_music
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
    current_music = None

def play_sfx(base_name):
    if not pygame.mixer.get_init():
        return
    if base_name not in _sfx_cache:
        path = find_audio_file(SFX_DIR, base_name)
        snd = None
        if path:
            try:
                snd = pygame.mixer.Sound(path)
            except pygame.error:
                snd = None
        _sfx_cache[base_name] = snd
    snd = _sfx_cache[base_name]
    if snd:
        snd.set_volume(0 if muted else VOLUME)
        snd.play()

def load_graze_sound():
    global graze_sound
    path = find_audio_file(SFX_DIR, "graze_click")
    if path:
        try:
            graze_sound = pygame.mixer.Sound(path)
            graze_sound.set_volume(0.4)
        except:
            graze_sound = None
    else:
        graze_sound = None

def play_graze_sound():
    global graze_sound
    if graze_sound is None:
        load_graze_sound()
    if graze_sound and pygame.mixer.get_init():
        graze_sound.play()

def adjust_volume(delta):
    global VOLUME
    VOLUME = max(0.0, min(1.0, VOLUME + delta))
    if pygame.mixer.get_init() and not muted:
        pygame.mixer.music.set_volume(VOLUME)

def toggle_mute():
    global muted
    muted = not muted
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(0 if muted else VOLUME)

def update_music(game_state, secret_boss_active, boss_spawned, boss, current_level, secret_boss_defeated):
    if game_state == "menu":
        play_music_any(["menu"], loop=-1, start_pos=3.0)
    elif game_state in ("playing", "dialog", "paused"):
        if secret_boss_active:
            play_music_any(["secret_boss", "boss"])
        elif boss_spawned and boss is not None and boss.alive:
            level = current_level
            play_music_any([f"boss{level}", "boss"])
        else:
            play_music_any([f"stage{current_level}", "stage"])
    elif game_state == "game_over":
        play_music_any(["game_over"], loop=0)
    elif game_state == "victory":
        if secret_boss_defeated:
            play_music_any(["secret_victory", "victory"], loop=0)
        else:
            play_music_any(["victory"], loop=0)
