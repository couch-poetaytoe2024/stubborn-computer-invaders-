import pygame, sys
from pygame.locals import *
from random import randint, choice
from enum import Enum
from time import time
from math import sin, cos, radians
import math

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Space Invaders")
font = pygame.font.SysFont("Arial", 30)
clock = pygame.time.Clock()

# Load images
try:
    INVADER_IMG = pygame.image.load("invader_monster.webp")
    print("Loaded invader image successfully")
    INVADER_IMG = pygame.transform.scale(INVADER_IMG, (40, 40))
except Exception as e:
    print(f"Failed to load invader image: {e}")
    INVADER_IMG = None

try:
    PLAYER_IMG = pygame.image.load("player_ship.png")
    print("Loaded player image successfully")
    PLAYER_IMG = pygame.transform.scale(PLAYER_IMG, (50, 50))
except Exception as e:
    print(f"Failed to load player image: {e}")
    PLAYER_IMG = None

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
BLUE = (0, 191, 255)
ORANGE = (255, 165, 0)

# Game states
game_over = False
score = 0

# Add PowerUp types
class PowerUpType(Enum):
    RAPID_FIRE = 1
    PIERCING = 2
    SHIELD = 3
    BUDDY = 4
    SPEED = 5
    MEDKIT = 6  # New power-up type

# try:
#     POWERUP_ICONS = {
#         'rapid': pygame.transform.scale(INVADER_IMG, (20, 20)),
#         'buddy': pygame.transform.scale(PLAYER_IMG, (20, 20))
#     }
# except Exception as e:
#     print(f"Failed to create power-up icons: {e}")
#     POWERUP_ICONS = {}

class Buddy:
    buddy_count = 0  # Class variable to track number of buddies

    def __init__(self, player_x, position=None):
        self.position = position
        # Expanded positions around the player
        self.offsets = {
            'left': (-30, 0),
            'right': (30, 0),
            'top_left': (-20, -30),
            'top_right': (20, -30),
            'far_left': (-60, 0),
            'far_right': (60, 0),
            'bottom_left': (-20, 30),
            'bottom_right': (20, 30),
            'top': (0, -30),
            'bottom': (0, 30),
            'top_far_left': (-40, -30),
            'top_far_right': (40, -30),
            'bottom_far_left': (-40, 30),
            'bottom_far_right': (40, 30)
        }
        
        # If no position specified, create a new one
        if position is None:
            # Calculate a new position based on buddy count
            angle = Buddy.buddy_count * (math.pi / 6)  # 30 degree spacing
            radius = 40  # Distance from player
            x_offset = int(math.cos(angle) * radius)
            y_offset = int(math.sin(angle) * radius)
            self.position = f'dynamic_{Buddy.buddy_count}'
            self.offsets[self.position] = (x_offset, y_offset)
            Buddy.buddy_count += 1  # Increment counter

        offset_x, offset_y = self.offsets[self.position]
        self.rect = pygame.Rect(player_x + offset_x, 500 + offset_y, 30, 30)
        self.alive = True
        self.shoot_timer = 0
        self.shoot_delay = 45
        self.move_timer = 0
        self.base_offset = self.offsets[self.position]
        self.wiggle_amount = 10
        self.wiggle_speed = 0.1
        self.rapid_fire = False
        self.piercing_bullets = False
        self.shield_active = False

    def update(self, player_x, player_y, player_bullets, power_ups):
        if not self.alive:
            return
            
        # Copy power-up states from main player
        self.rapid_fire = power_ups['rapid_fire']
        self.piercing_bullets = power_ups['piercing']
        self.shield_active = power_ups['shield']
        
        # Update shooting delay based on rapid fire
        current_delay = 20 if self.rapid_fire else 45
            
        # Update movement
        self.move_timer += self.wiggle_speed
        
        # Calculate slight movement offsets using sine waves
        side_offset = sin(self.move_timer) * self.wiggle_amount
        up_offset = cos(self.move_timer * 1.5) * (self.wiggle_amount / 2)
        
        # Update position relative to player with wiggle movement
        base_x = player_x + self.base_offset[0]
        base_y = player_y + self.base_offset[1]
        
        self.rect.x = base_x + side_offset
        self.rect.y = base_y + up_offset
        
        # Keep buddy within screen bounds
        self.rect.x = max(0, min(self.rect.x, 770))
        self.rect.y = max(0, min(self.rect.y, 570))
        
        # Shooting logic
        self.shoot_timer += 1
        if self.shoot_timer >= current_delay:
            self.shoot_timer = 0
            bullet = pygame.Rect(self.rect.centerx, self.rect.y, 8, 16)
            player_bullets.append(bullet)

    def draw(self, screen):
        if not self.alive:
            return
            
        # Draw buddy
        if PLAYER_IMG:
            scaled_img = pygame.transform.scale(PLAYER_IMG, (30, 30))
            screen.blit(scaled_img, self.rect)
        else:
            pygame.draw.rect(screen, GREEN, self.rect)
            
        # Draw shield if active, using current position that includes wiggle movement
        if self.shield_active:
            shield_radius = 25  # Smaller shield than player
            pygame.draw.circle(screen, BLUE, 
                             (int(self.rect.centerx), int(self.rect.centery)), 
                             shield_radius, 2)

class Invader:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.direction = 1
        self.speed = 6
        self.shoot_delay = randint(120, 240)
        self.shoot_timer = randint(0, 120)
        self.health = 20  # Keep at 20 HP
        self.max_health = 20  # Add max_health for health bar calculation

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = radians(randint(0, 360))
        speed = randint(4, 8)  # Increased speed range
        self.vx = cos(angle) * speed
        self.vy = sin(angle) * speed
        self.lifetime = 90  # Increased lifetime (was 60)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # gravity
        self.lifetime -= 1
        
    def draw(self, screen):
        if self.lifetime > 0:
            # Larger particles
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)  # Increased size
            # Add glow effect
            if self.lifetime > 30:
                pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 4, 1)

class Explosion:
    def __init__(self, x, y, color=ORANGE, delay=0):
        self.x = x
        self.y = y
        self.radius = 0 if delay > 0 else 5  # Start at 0 if delayed
        self.max_radius = 20
        self.growth_rate = 2
        self.color = color
        self.delay = delay
        self.particles = []
        # Create explosion particles
        for _ in range(12):
            angle = radians(randint(0, 360))
            speed = randint(2, 5)
            self.particles.append({
                'x': self.x,
                'y': self.y,
                'vx': cos(angle) * speed,
                'vy': sin(angle) * speed,
                'lifetime': 30
            })

    def update(self):
        if self.delay > 0:
            self.delay -= 1
            return
            
        self.radius += self.growth_rate
        # Update particles
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['lifetime'] -= 1

    def draw(self, screen):
        # Draw expanding circle
        if self.radius < self.max_radius:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))
        # Draw particles
        for particle in self.particles:
            if particle['lifetime'] > 0:
                alpha = int((particle['lifetime'] / 30) * 255)
                color = (*self.color, alpha)
                pos = (int(particle['x']), int(particle['y']))
                pygame.draw.circle(screen, color, pos, 2)

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, wave):
        super().__init__()
        try:
            self.image = pygame.image.load(r'C:\Users\Andywandy\my codeing\hackathon\141-1418158_invader-boss-2-pixel-exclamation-point-hd-png.png')
            self.image = pygame.transform.scale(self.image, (100, 100))
            print("Loaded boss image successfully")
        except Exception as e:
            print(f"Failed to load boss image: {e}")
            self.image = pygame.Surface((100, 100))
            self.image.fill(RED)
            pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 3)
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        # New health calculation: starts at 1000, increases by 5000 each time
        boss_number = wave // 10
        self.max_health = 1000 + (boss_number - 1) * 5000
        self.health = self.max_health
        self.damage = 25  # Boss deals 25 damage
        self.direction = 1
        self.speed = 2 + (wave // 20)
        self.shoot_timer = 0
        self.shoot_delay = max(30, 60 - (wave // 20) * 5)
        self.pattern_timer = 0
        self.attack_pattern = 0
        print(f"Boss initialized at wave {wave} with health {self.health}")

    def update(self):
        # Keep boss within screen bounds
        self.rect.x += self.speed * self.direction
        if self.rect.right >= 750 or self.rect.left <= 50:  # Added margins
            self.direction *= -1
            # Move away from edge slightly
            if self.rect.right >= 750:
                self.rect.right = 749
            if self.rect.left <= 50:
                self.rect.left = 51

        # Keep boss from going too high or low
        if self.rect.top < 50:
            self.rect.top = 50
        if self.rect.bottom > 300:
            self.rect.bottom = 300

        # Change attack patterns periodically
        self.pattern_timer += 1
        if self.pattern_timer >= 300:
            self.pattern_timer = 0
            self.attack_pattern = (self.attack_pattern + 1) % 3

    def shoot(self):
        bullets = []
        if self.attack_pattern == 0:
            # Spread shot
            for angle in range(-2, 3):
                bullets.append(pygame.Rect(
                    self.rect.centerx + (angle * 20),
                    self.rect.bottom,
                    4, 10
                ))
        elif self.attack_pattern == 1:
            # Circle shot
            for angle in range(0, 360, 45):
                rad = math.radians(angle)
                bullets.append(pygame.Rect(
                    self.rect.centerx + math.cos(rad) * 30,
                    self.rect.bottom + math.sin(rad) * 30,
                    4, 10
                ))
        else:
            # Targeted shot
            bullets.append(pygame.Rect(
                self.rect.centerx,
                self.rect.bottom,
                8, 15
            ))

        return bullets

class PowerUp:
    def __init__(self, power_type):
        self.type = power_type
        self.rect = pygame.Rect(randint(50, 750), 0, 30, 30)
        self.speed = 2
        self.flash_timer = 0
        
        # Set color based on type
        self.color = {
            PowerUpType.RAPID_FIRE: RED,
            PowerUpType.PIERCING: PURPLE,
            PowerUpType.SHIELD: BLUE,
            PowerUpType.BUDDY: GREEN,
            PowerUpType.SPEED: YELLOW,
            PowerUpType.MEDKIT: (255, 105, 180)  # Hot pink for med kit
        }[self.type]

    def draw(self, screen):
        # Flash effect
        self.flash_timer += 1
        if self.flash_timer > 30:
            self.flash_timer = 0
            
        if self.flash_timer < 15:
            # Draw outer glow
            glow_rect = self.rect.inflate(12, 12)  # Increased glow size
            pygame.draw.rect(screen, self.color, glow_rect, 3)  # Thicker glow
        
        # Draw power-up background
        pygame.draw.rect(screen, self.color, self.rect)
        
        # Draw appropriate icon or symbol
        if self.type == PowerUpType.RAPID_FIRE and INVADER_IMG:
            # Scale invader image to fit inside power-up
            scaled_invader = pygame.transform.scale(INVADER_IMG, (24, 24))  # Larger icon
            screen.blit(scaled_invader, 
                       (self.rect.centerx - 12, self.rect.centery - 12))
        elif self.type == PowerUpType.BUDDY and PLAYER_IMG:
            # Scale player image to fit inside power-up
            scaled_player = pygame.transform.scale(PLAYER_IMG, (24, 24))  # Larger icon
            screen.blit(scaled_player, 
                       (self.rect.centerx - 12, self.rect.centery - 12))
        elif self.type == PowerUpType.PIERCING:
            # Draw a bold piercing arrow
            # Arrow head (larger triangle)
            pygame.draw.polygon(screen, WHITE, [
                (self.rect.centerx, self.rect.top + 3),          # Sharp tip
                (self.rect.centerx - 12, self.rect.top + 18),    # Wide left corner
                (self.rect.centerx + 12, self.rect.top + 18)     # Wide right corner
            ])
            
            # Main shaft (thicker)
            pygame.draw.rect(screen, WHITE, 
                           pygame.Rect(self.rect.centerx - 4, 
                                     self.rect.top + 15,
                                     8, self.rect.height - 18))
            
            # Purple trail effect
            for i in range(3):  # Multiple trailing lines for effect
                offset = i * 2
                pygame.draw.rect(screen, PURPLE, 
                               pygame.Rect(self.rect.centerx - (3 - i), 
                                         self.rect.centery + offset,
                                         (6 - i * 2), 
                                         self.rect.height - 25))
        elif self.type == PowerUpType.SHIELD:
            # Draw simple shield circle
            # Outer circle (glow)
            pygame.draw.circle(screen, self.color, self.rect.center, 12, 3)
            # Inner circle
            pygame.draw.circle(screen, WHITE, self.rect.center, 10, 2)
            # Center dot
            pygame.draw.circle(screen, WHITE, self.rect.center, 3)
        elif self.type == PowerUpType.SPEED:
            # Draw speed boost icon (lightning bolt)
            points = [
                (self.rect.centerx - 7, self.rect.top + 5),      # Top
                (self.rect.centerx + 4, self.rect.centery - 2),   # Middle right
                (self.rect.centerx - 3, self.rect.centery + 2),   # Middle left
                (self.rect.centerx + 7, self.rect.bottom - 5)     # Bottom
            ]
            # Draw outline for bold effect
            pygame.draw.lines(screen, self.color, False, points, 5)  # Thick colored outline
            pygame.draw.lines(screen, WHITE, False, points, 3)  # White center
        elif self.type == PowerUpType.MEDKIT:
            # Draw medical cross with bold lines and detail
            cross_color = WHITE
            # Outer glow
            pygame.draw.circle(screen, self.color, self.rect.center, 12, 2)
            # Vertical line
            pygame.draw.line(screen, cross_color,
                           (self.rect.centerx, self.rect.top + 5),
                           (self.rect.centerx, self.rect.bottom - 5), 4)
            # Horizontal line
            pygame.draw.line(screen, cross_color,
                           (self.rect.left + 5, self.rect.centery),
                           (self.rect.right - 5, self.rect.centery), 4)
            # Add circles at the ends for detail
            for point in [(self.rect.centerx, self.rect.top + 5),
                         (self.rect.centerx, self.rect.bottom - 5),
                         (self.rect.left + 5, self.rect.centery),
                         (self.rect.right - 5, self.rect.centery)]:
                pygame.draw.circle(screen, cross_color, point, 3)

def create_invader_formation(wave):
    invaders = []
    
    # Check for boss wave
    if wave % 10 == 0:
        print(f"Creating boss for wave {wave}")
        boss = Boss(350, 50, wave)
        return [boss]
    
    # Regular wave formation
    formation_type = wave % 7
    
    if formation_type == 0:  # V formation
        for row in range(5):
            for col in range(10):
                x = 100 + (col * 60) + (row * 30)
                y = 50 + (row * 50)
                if 2 <= col <= 7 + row:
                    invaders.append(Invader(x, y))
    
    elif formation_type == 1:  # Diamond formation
        positions = [
            (4, 0), (5, 0),
            (3, 1), (4, 1), (5, 1), (6, 1),
            (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2),
            (3, 3), (4, 3), (5, 3), (6, 3),
            (4, 4), (5, 4)
        ]
        for col, row in positions:
            x = 100 + (col * 60)
            y = 50 + (row * 50)
            invaders.append(Invader(x, y))
    
    elif formation_type == 2:  # X formation
        for row in range(5):
            for col in range(5):
                if row == col or row == 4 - col:
                    x = 200 + (col * 60)
                    y = 50 + (row * 50)
                    invaders.append(Invader(x, y))
    
    elif formation_type == 3:  # Circle formation
        center_x, center_y = 400, 200
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x = center_x + math.cos(rad) * 150
            y = center_y + math.sin(rad) * 100
            invaders.append(Invader(int(x), int(y)))
        # Add center invaders
        for i in range(3):
            invaders.append(Invader(center_x, center_y - 20 + i * 40))
    
    elif formation_type == 4:  # Double line formation
        for row in range(2):
            for col in range(12):
                x = 100 + (col * 50)
                y = 50 + (row * 100)
                invaders.append(Invader(x, y))
    
    elif formation_type == 5:  # Arrow formation
        for row in range(5):
            for col in range(9):
                if (row <= 2 and col == 4) or row == 3 or row == 4:
                    x = 150 + (col * 60)
                    y = 50 + (row * 50)
                    invaders.append(Invader(x, y))
    
    else:  # Wave formation
        for col in range(12):
            y_offset = math.sin(col * 0.5) * 50
            x = 100 + (col * 50)
            y = 150 + y_offset
            invaders.append(Invader(x, int(y)))
            # Add second row
            invaders.append(Invader(x, int(y) - 70))

    # Cap enemy speed at wave 14
    capped_wave = min(wave, 14)  # Wave number won't go above 14 for speed calculation
    for invader in invaders:
        invader.speed = 6 + (capped_wave * 1.2)  # Speed increase stops at wave 14
    
    return invaders

def create_boss_level(current_level):
    if current_level % 10 == 0:  # Every 10th level is a boss level
        boss = Boss(screen_width // 2, 50)  # Position boss at top center
        boss.health = 100 * (current_level // 10)  # Health increases with level
        
        # Spawn additional minions based on level
        num_minions = 5 * (current_level // 10)
        spawn_minions(num_minions)
        
        return boss
    return None

def apply_powerup(player, powerup_type, buddy_group):
    if powerup_type == 'shield':
        player.shield_active = True
        player.shield_timer = 10 * FPS  # 10 seconds
        # Apply shield to buddies
        for buddy in buddy_group:
            buddy.shield_active = True
            
    elif powerup_type == 'rapid_fire':
        player.rapid_fire = True
        player.rapid_fire_timer = 5 * FPS  # 5 seconds
        # Apply rapid fire to buddies
        for buddy in buddy_group:
            buddy.rapid_fire = True

# Main game loop
def main():
    global game_over, score
    player = pygame.Rect(375, 500, 50, 50)
    player_bullets = []
    invader_bullets = []
    invaders = create_invader_formation(1)
    move_timer = 0
    player_speed = 7
    wave = 1
    
    # Power-up states
    power_ups = []
    last_power_up_time = time()
    power_up_interval = 8  # Changed from 10 to 8 seconds
    
    # Power-up effect states
    rapid_fire = False
    rapid_fire_end = 0
    piercing_bullets = False
    piercing_end = 0
    shield_active = False
    shield_end = 0
    buddies = []  # Start with no buddies
    speed_boost = False
    speed_boost_end = 0
    normal_speed = player_speed
    
    particles = []
    boost_text = None
    boost_text_timer = 0
    
    # Add this new class for explosions
    explosions = []
    
    # Player state
    player_bob_timer = 0
    player_bob_speed = 0.08
    player_bob_amount = 5
    player_health = 100  # Changed from 3 to 100 for percentage
    player_invulnerable = False
    player_invulnerable_end = 0
    player_flash_timer = 0

    # Add health bar colors
    HEALTH_GREEN = (50, 205, 50)
    HEALTH_RED = (220, 20, 60)
    
    while True:
        current_time = time()
        screen.fill(BLACK)
        
        # Check for power-up spawning
        if current_time - last_power_up_time >= power_up_interval:
            power_type = PowerUpType(randint(1, len(PowerUpType)))
            power_ups.append(PowerUp(power_type))
            last_power_up_time = current_time
        
        # Update power-up states
        if rapid_fire and current_time > rapid_fire_end:
            rapid_fire = False
        if piercing_bullets and current_time > piercing_end:
            piercing_bullets = False
        if shield_active and current_time > shield_end:
            shield_active = False
        if speed_boost and current_time > speed_boost_end:
            speed_boost = False
            player_speed = normal_speed

        # Draw score and wave
        score_text = font.render(f'Score: {score}', True, WHITE)
        wave_text = font.render(f'Wave: {wave}', True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(wave_text, (10, 40))
        
        if not game_over:
            # Player bobbing motion
            player_bob_timer += player_bob_speed
            bob_offset = sin(player_bob_timer) * player_bob_amount
            
            # Draw player with bob motion
            player_draw_pos = player.copy()
            player_draw_pos.y += bob_offset
            
            # Flash when hit
            if not player_invulnerable or player_flash_timer % 4 < 2:
                if PLAYER_IMG:
                    screen.blit(PLAYER_IMG, player_draw_pos)
                else:
                    pygame.draw.rect(screen, GREEN, player_draw_pos)
            
            # Draw health bar
            health_width = 150
            health_height = 15
            health_x = 10
            health_y = 70
            # Background (empty health)
            pygame.draw.rect(screen, HEALTH_RED, (health_x, health_y, health_width, health_height))
            # Filled health
            health_fill = (health_width * player_health) // 100  # Changed from 3 to 100
            if health_fill > 0:
                pygame.draw.rect(screen, HEALTH_GREEN, (health_x, health_y, health_fill, health_height))
            # Health text
            health_text = font.render(f'Health: {player_health}%', True, WHITE)  # Added % symbol
            screen.blit(health_text, (health_x + health_width + 10, health_y))
            
            # Draw and update power-ups
            for power_up in power_ups[:]:
                power_up.rect.y += power_up.speed
                power_up.draw(screen)
                
                # Check collision with player
                if power_up.rect.colliderect(player):
                    # Create confetti
                    for _ in range(50):  # Increased from 30 to 50 particles
                        particles.append(Particle(player.centerx, player.centery, power_up.color))
                    
                    # Set boost text
                    boost_name = {
                        PowerUpType.RAPID_FIRE: "RAPID FIRE!",
                        PowerUpType.PIERCING: "PIERCING BULLETS!",
                        PowerUpType.SHIELD: "SHIELD ACTIVATED!",
                        PowerUpType.BUDDY: "BUDDY JOINED!",
                        PowerUpType.SPEED: "SPEED BOOST!",
                        PowerUpType.MEDKIT: "HEALTH RESTORED!"
                    }[power_up.type]
                    boost_text = font.render(boost_name, True, power_up.color)
                    boost_text_timer = 90  # Show for 1.5 seconds
                    
                    # Apply power-up effect (existing code)
                    if power_up.type == PowerUpType.RAPID_FIRE:
                        rapid_fire = True
                        rapid_fire_end = current_time + 10
                    elif power_up.type == PowerUpType.PIERCING:
                        piercing_bullets = True
                        piercing_end = current_time + 15
                    elif power_up.type == PowerUpType.SHIELD:
                        shield_active = True
                        shield_end = current_time + 30  # Changed to 30 seconds
                    elif power_up.type == PowerUpType.BUDDY:
                        # Create a new buddy with dynamic positioning
                        buddies.append(Buddy(player.x))
                        # Create spawn effect
                        for _ in range(30):
                            particles.append(Particle(
                                player.centerx, 
                                player.centery, 
                                GREEN
                            ))
                    elif power_up.type == PowerUpType.SPEED:
                        speed_boost = True
                        player_speed = normal_speed * 1.5
                        speed_boost_end = current_time + 8
                    elif power_up.type == PowerUpType.MEDKIT:
                        player_health = min(100, player_health + 20)  # Heal 20% but don't exceed 100%
                        # Create healing effect particles
                        for _ in range(30):
                            particles.append(Particle(player.centerx, player.centery, (255, 105, 180)))
                    
                    power_ups.remove(power_up)
                
                # Remove if off screen
                if power_up.rect.y > 600:
                    power_ups.remove(power_up)

            # Draw active power-up effects
            if shield_active:
                # Draw shield as a circle around the player, following bob motion
                shield_radius = 35
                pygame.draw.circle(screen, BLUE, 
                                 (player_draw_pos.centerx, player_draw_pos.centery), 
                                 shield_radius, 2)  # Use player_draw_pos instead of player

            # Update buddies
            power_up_states = {
                'rapid_fire': rapid_fire,
                'piercing': piercing_bullets,
                'shield': shield_active
            }
            
            for buddy in buddies:
                if buddy.alive:
                    buddy.update(player.x, player.y, player_bullets, power_up_states)
                    buddy.draw(screen)

            # Move and draw invaders
            move_timer += 1
            if move_timer >= 8:  # Even faster movement (reduced from 10)
                move_timer = 0
                # Check if any invader hits the edges
                should_move_down = False
                for invader in invaders:
                    if (invader.rect.right >= 800 and invader.direction > 0) or \
                       (invader.rect.left <= 0 and invader.direction < 0):
                        should_move_down = True
                        break
                
                if should_move_down:
                    # Change direction and move down
                    for invader in invaders:
                        invader.direction *= -1
                        invader.rect.y += 30  # Move down faster
                else:
                    # Move sideways
                    for invader in invaders:
                        invader.rect.x += invader.speed * invader.direction
            
            # Invader shooting
            for invader in invaders:
                invader.shoot_timer += 1
                if invader.shoot_timer >= invader.shoot_delay:
                    # Only 10% chance to actually shoot when delay is reached
                    if randint(1, 10) == 1:
                        invader_bullets.append(pygame.Rect(invader.rect.centerx - 2, invader.rect.bottom, 4, 10))
                    invader.shoot_timer = 0
                    invader.shoot_delay = randint(120, 240)  # Random delay between 2-4 seconds
            
            # Draw and update invader bullets
            for bullet in invader_bullets[:]:
                bullet.y += 5
                if bullet.y > 600:
                    invader_bullets.remove(bullet)
                # Draw bullet with glow effect
                pygame.draw.rect(screen, PURPLE, bullet.inflate(4, 4))  # Outer glow
                pygame.draw.rect(screen, WHITE, bullet)  # Bright center

            # Draw invaders/boss
            for invader in invaders:
                if isinstance(invader, Boss):
                    # Update boss
                    invader.update()
                    
                    # Boss shooting
                    invader.shoot_timer += 1
                    if invader.shoot_timer >= invader.shoot_delay:
                        invader.shoot_timer = 0
                        invader_bullets.extend(invader.shoot())
                    
                    # Draw boss health bar
                    health_width = 400  # Wider health bar
                    health_height = 20   # Taller health bar
                    health_x = 200       # Centered more
                    health_y = 20
                    
                    # Background (red)
                    pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
                    
                    # Filled health (green)
                    health_fill = (health_width * invader.health) // invader.max_health
                    if health_fill > 0:
                        pygame.draw.rect(screen, GREEN, (health_x, health_y, health_fill, health_height))
                    
                    # Health text
                    health_text = font.render(f'Boss Health: {invader.health}/{invader.max_health}', True, WHITE)
                    screen.blit(health_text, (health_x + health_width/2 - health_text.get_width()/2, health_y - 25))
                    
                    # Draw boss
                    screen.blit(invader.image, invader.rect)
                else:
                    # Regular invader drawing and behavior
                    if INVADER_IMG:
                        screen.blit(INVADER_IMG, invader.rect)
                    else:
                        pygame.draw.rect(screen, YELLOW, invader.rect)

            # Update bullet collision for boss and invaders
            for bullet in player_bullets[:]:
                for invader in invaders[:]:
                    if bullet.colliderect(invader.rect):
                        if isinstance(invader, Boss):
                            # Boss damage
                            damage = 75 if piercing_bullets else 50
                            invader.health = max(0, invader.health - damage)  # Prevent negative health
                            print(f"Boss hit! Damage: {damage}, Health: {invader.health}/{invader.max_health}")
                            
                            # Create hit effect
                            explosions.append(Explosion(
                                bullet.centerx, 
                                bullet.centery,
                                color=RED if piercing_bullets else ORANGE
                            ))
                            
                            # Remove bullet unless piercing
                            if not piercing_bullets:
                                if bullet in player_bullets:
                                    player_bullets.remove(bullet)
                                break
                            
                            # Check if boss is defeated
                            if invader.health <= 0:
                                if invader in invaders:
                                    invaders.remove(invader)
                                    score += 5000 * (wave // 10)  # More points for higher level bosses
                                    # Create massive explosion
                                    for _ in range(50):
                                        explosions.append(Explosion(
                                            invader.rect.centerx + randint(-70, 70),
                                            invader.rect.centery + randint(-70, 70),
                                            color=ORANGE
                                        ))
                        else:
                            # Regular invader damage
                            damage = 75 if piercing_bullets else 50
                            invader.health -= damage
                            
                            # Create hit effect
                            explosions.append(Explosion(
                                bullet.centerx, 
                                bullet.centery,
                                color=YELLOW
                            ))
                            
                            if invader.health <= 0 and invader in invaders:
                                invaders.remove(invader)
                                score += 10
                                for _ in range(10):
                                    particles.append(Particle(
                                        invader.rect.centerx,
                                        invader.rect.centery,
                                        YELLOW
                                    ))
                            
                            if not piercing_bullets:
                                if bullet in player_bullets:
                                    player_bullets.remove(bullet)
                                break

            # Draw and update player bullets
            for bullet in player_bullets[:]:
                bullet.y -= 15  # Faster player bullets
                if bullet.y < 0:
                    player_bullets.remove(bullet)
                    continue  # Skip rest of loop for off-screen bullets

                # Draw bullet (and trail if piercing)
                if piercing_bullets:
                    pygame.draw.line(screen, PURPLE, 
                                   (bullet.centerx, bullet.bottom), 
                                   (bullet.centerx, bullet.top), 3)
                else:
                    pygame.draw.rect(screen, RED, bullet)
                
                # Handle bullet collisions
                hits = []  # Track enemies hit by this bullet
                for invader in invaders[:]:
                    if bullet.colliderect(invader.rect):
                        if piercing_bullets:
                            # Create multiple purple explosions
                            for i in range(3):
                                explosions.append(Explosion(
                                    invader.rect.centerx + randint(-10, 10), 
                                    invader.rect.centery + randint(-10, 10),
                                    color=PURPLE,
                                    delay=i * 3
                                ))
                            # Create purple particles
                            for _ in range(40):
                                particles.append(Particle(
                                    invader.rect.centerx, 
                                    invader.rect.centery, 
                                    PURPLE
                                ))
                            hits.append(invader)
                        else:
                            # Normal bullet explosion
                            explosions.append(Explosion(invader.rect.centerx, invader.rect.centery))
                            for _ in range(10):
                                particles.append(Particle(invader.rect.centerx, invader.rect.centery, YELLOW))
                            invaders.remove(invader)
                            player_bullets.remove(bullet)
                        score += 10
                        if not piercing_bullets:
                            break

                # Remove hit invaders for piercing bullets
                if piercing_bullets and hits:
                    for invader in hits:
                        if invader in invaders:
                            invaders.remove(invader)

            # Respawn invaders if all are destroyed
            if len(invaders) == 0:
                wave += 1
                invaders = create_invader_formation(wave)
                # Speed is now handled in create_invader_formation
        
            # Handle rapid fire
            if rapid_fire and keys[K_SPACE]:
                if randint(1, 4) == 1:  # 25% chance each frame to shoot
                    player_bullets.append(pygame.Rect(player.x + 20, player.y, 10, 20))

            # Check if player gets hit
            if not player_invulnerable:  # Only check hits when not invulnerable
                for bullet in invader_bullets[:]:
                    if bullet.colliderect(player):
                        if shield_active:
                            invader_bullets.remove(bullet)
                        else:
                            # Different damage for boss bullets vs regular invader bullets
                            damage = 25 if any(isinstance(inv, Boss) for inv in invaders) else 20
                            player_health -= damage
                            invader_bullets.remove(bullet)
                            # Create hit effect
                            for _ in range(20):
                                particles.append(Particle(player.centerx, player.centery, RED))
                            # Temporary invulnerability
                            player_invulnerable = True
                            player_invulnerable_end = current_time + 2
                            if player_health <= 0:
                                game_over = True
                            break

            # Update invulnerability
            if player_invulnerable:
                player_flash_timer += 1
                if current_time > player_invulnerable_end:
                    player_invulnerable = False
                    player_flash_timer = 0

        else:
            # Game Over screen
            game_over_text = font.render('Game Over! Press R to restart', True, WHITE)
            final_score = font.render(f'Final Score: {score} - Wave: {wave}', True, WHITE)
            screen.blit(game_over_text, (250, 250))
            screen.blit(final_score, (250, 300))
        
        # Draw all effects last (on top of everything)
        # Update and draw particles
        for particle in particles[:]:
            particle.update()
            particle.draw(screen)
            if particle.lifetime <= 0:
                particles.remove(particle)
        
        # Draw boost text
        if boost_text and boost_text_timer > 0:
            # Make text bounce using sine wave
            y_offset = sin(boost_text_timer * 0.2) * 10
            text_x = 400 - boost_text.get_width() // 2
            text_y = 200 + y_offset
            screen.blit(boost_text, (text_x, text_y))
            boost_text_timer -= 1

        # Update and draw explosions
        for explosion in explosions[:]:
            explosion.update()
            explosion.draw(screen)
            if explosion.radius >= explosion.max_radius and all(p['lifetime'] <= 0 for p in explosion.particles):
                explosions.remove(explosion)

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
                    # Only create one bullet per space press
                    player_bullets.append(pygame.Rect(player.x + 20, player.y, 10, 20))
                if event.key == K_r and game_over:
                    # Reset game
                    game_over = False
                    score = 0
                    wave = 1
                    player.x = 375
                    player_health = 100  # Reset to full health (100%)
                    player_invulnerable = False
                    player_flash_timer = 0
                    player_bullets.clear()
                    invader_bullets.clear()
                    invaders = create_invader_formation(1)
                    particles.clear()
                    explosions.clear()
                    buddies.clear()  # Clear all buddies
                    boost_text = None
                    boost_text_timer = 0
                    Buddy.buddy_count = 0  # Reset buddy counter
        
        # Player movement
        keys = pygame.key.get_pressed()
        if not game_over:
            if keys[K_LEFT] and player.x > 0:
                player.x -= player_speed
            if keys[K_RIGHT] and player.x < 750:
                player.x += player_speed
        
        clock.tick(60)
        
        # Check if buddies get hit
        for buddy in buddies:
            if buddy.alive:
                for bullet in invader_bullets[:]:
                    if bullet.colliderect(buddy.rect):
                        if buddy.shield_active:
                            # If shield is active, just remove the bullet
                            invader_bullets.remove(bullet)
                            # Optional: Add shield hit effect
                            for _ in range(5):
                                particles.append(Particle(
                                    buddy.rect.centerx, 
                                    buddy.rect.centery, 
                                    BLUE
                                ))
                        else:
                            # If no shield, buddy dies
                            buddy.alive = False
                            invader_bullets.remove(bullet)
                            # Create explosion effect when buddy is destroyed
                            explosions.append(Explosion(buddy.rect.centerx, buddy.rect.centery))
                            for _ in range(15):
                                particles.append(Particle(buddy.rect.centerx, buddy.rect.centery, GREEN))
                            break

if __name__ == "__main__":
    main()
