import pygame
import random
import sys

# --- Initialization ---
pygame.init()

# --- Full Screen Setup ---
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
pygame.display.set_caption("Pixel Highway: OG Edition")
clock = pygame.time.Clock()

# --- Configuration ---
FPS = 60
BLOCK_SIZE = 4 
CAR_WIDTH = 14 * BLOCK_SIZE  # Slightly wider for OG look
CAR_HEIGHT = 24 * BLOCK_SIZE

# --- Colors ---
C_ASPHALT = (40, 40, 50)     # Lighter asphalt for better contrast
C_GRASS = (20, 30, 20)
C_LINE = (255, 255, 0)       # Yellow lines (classic arcade style)
C_WHITE = (255, 255, 255)
C_RED = (200, 0, 0)
C_CYAN = (0, 255, 255)
C_BLACK = (0, 0, 0)
C_WINDSHIELD = (100, 150, 255) # Light blue glass
C_TIRE = (10, 10, 10)
C_ROOF = (0, 0, 0, 50)       # Shadow for roof

# Fonts
font_small = pygame.font.SysFont("Consolas", 30)
font_large = pygame.font.SysFont("Impact", 80)

def draw_text_centered(text, font, color, y_offset=0):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
    screen.blit(surface, rect)

def draw_og_car(x, y, body_color):
    """
    Draws a classic boxy 'Sedan' style car.
    """
    # 1. Tires (Tucked slightly inside)
    tire_w = 3 * BLOCK_SIZE
    tire_h = 5 * BLOCK_SIZE
    # Left tires
    pygame.draw.rect(screen, C_TIRE, (x + BLOCK_SIZE, y + 3*BLOCK_SIZE, tire_w, tire_h))
    pygame.draw.rect(screen, C_TIRE, (x + BLOCK_SIZE, y + CAR_HEIGHT - 7*BLOCK_SIZE, tire_w, tire_h))
    # Right tires
    pygame.draw.rect(screen, C_TIRE, (x + CAR_WIDTH - tire_w - BLOCK_SIZE, y + 3*BLOCK_SIZE, tire_w, tire_h))
    pygame.draw.rect(screen, C_TIRE, (x + CAR_WIDTH - tire_w - BLOCK_SIZE, y + CAR_HEIGHT - 7*BLOCK_SIZE, tire_w, tire_h))

    # 2. Main Chassis (The big rectangle)
    pygame.draw.rect(screen, body_color, (x + 2*BLOCK_SIZE, y, CAR_WIDTH - 4*BLOCK_SIZE, CAR_HEIGHT))

    # 3. Roof (The Center Box)
    roof_offset = 6 * BLOCK_SIZE
    roof_height = 10 * BLOCK_SIZE
    pygame.draw.rect(screen, (min(body_color[0]+20, 255), min(body_color[1]+20, 255), min(body_color[2]+20, 255)), 
                     (x + 3*BLOCK_SIZE, y + roof_offset, CAR_WIDTH - 6*BLOCK_SIZE, roof_height))

    # 4. Windshield (Front Glass)
    pygame.draw.rect(screen, C_WINDSHIELD, (x + 3.5*BLOCK_SIZE, y + roof_offset + BLOCK_SIZE, CAR_WIDTH - 7*BLOCK_SIZE, 2*BLOCK_SIZE))
    
    # 5. Rear Window (Back Glass)
    pygame.draw.rect(screen, C_WINDSHIELD, (x + 3.5*BLOCK_SIZE, y + roof_offset + roof_height - 3*BLOCK_SIZE, CAR_WIDTH - 7*BLOCK_SIZE, 2*BLOCK_SIZE))

def intro_screen():
    waiting = True
    pulse = 0
    while waiting:
        screen.fill(C_ASPHALT)
        draw_text_centered("RETRO RACER", font_large, C_CYAN, -100)
        draw_text_centered("OG EDITION", font_small, C_RED, -40)
        
        pulse += 1
        if (pulse // 30) % 2 == 0:
            draw_text_centered("PRESS SPACE TO START", font_small, C_WHITE, 50)
        
        draw_text_centered("ARROWS to Steer | ESC to Quit", font_small, C_LINE, 150)
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_SPACE:
                    waiting = False

def main_game():
    # Player Setup
    player_x = SCREEN_WIDTH // 2 - CAR_WIDTH // 2
    player_y = SCREEN_HEIGHT - CAR_HEIGHT - 50
    player_speed = 12

    # Road Bounds
    road_left = SCREEN_WIDTH // 4
    road_right = SCREEN_WIDTH - (SCREEN_WIDTH // 4)
    lane_width = road_right - road_left

    # Game State
    score = 0
    lives = 3
    base_speed = 10
    game_speed = base_speed
    
    enemies = []
    shake_timer = 0
    
    # This variable controls the visual movement of the road lines
    lane_marker_move_y = 0 
    
    running = True
    while running:
        # --- 1. Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > road_left + 10:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < road_right - CAR_WIDTH - 10:
            player_x += player_speed

        # --- 2. Logic & Physics ---
        
        # Increase Speed based on Score (Dino Style)
        game_speed = base_speed + (score // 5)
        
        # Update Road Marker Position (Synced with Game Speed)
        lane_marker_move_y += game_speed
        if lane_marker_move_y >= 100: # Reset after one "segment" length
            lane_marker_move_y = 0
        
        # Spawn Enemies
        if random.randint(0, 100) < 2 + (score // 10):
            safe_spawn = True
            spawn_x = random.randint(road_left + 20, road_right - CAR_WIDTH - 20)
            for e in enemies:
                if e['y'] < 300: # Increased safe distance so they don't clump
                    safe_spawn = False
            
            if safe_spawn:
                enemies.append({'x': spawn_x, 'y': -150, 'color': C_RED}) # Spawn higher up

        # Move Enemies
        for e in enemies:
            e['y'] += game_speed # EXACT same speed as road markers

        # Collision Detection
        player_rect = pygame.Rect(player_x + 4, player_y + 4, CAR_WIDTH - 8, CAR_HEIGHT - 8)
        
        for e in enemies[:]:
            enemy_rect = pygame.Rect(e['x'] + 4, e['y'] + 4, CAR_WIDTH - 8, CAR_HEIGHT - 8)
            
            if player_rect.colliderect(enemy_rect):
                lives -= 1
                shake_timer = 20 # Stronger shake
                enemies.remove(e)
                if lives <= 0:
                    running = False 
            elif e['y'] > SCREEN_HEIGHT:
                score += 1
                enemies.remove(e)

        # --- 3. Drawing ---
        
        offset_x = random.randint(-10, 10) if shake_timer > 0 else 0
        offset_y = random.randint(-10, 10) if shake_timer > 0 else 0
        if shake_timer > 0: shake_timer -= 1

        screen.fill(C_GRASS)
        
        # Draw Road
        pygame.draw.rect(screen, C_ASPHALT, (road_left + offset_x, 0 + offset_y, lane_width, SCREEN_HEIGHT))
        
        # Draw Lane Markers (SYCHRONIZED MOVEMENT)
        # We draw extra markers above and below the screen to prevent popping
        for i in range(-2, SCREEN_HEIGHT // 100 + 2):
            y_pos = (i * 100) + lane_marker_move_y
            pygame.draw.rect(screen, C_LINE, (SCREEN_WIDTH // 2 - 5 + offset_x, y_pos + offset_y, 10, 50))

        # Draw Player
        draw_og_car(player_x + offset_x, player_y + offset_y, C_CYAN)
        
        # Draw Enemies
        for e in enemies:
            draw_og_car(e['x'] + offset_x, e['y'] + offset_y, e['color'])

        # Flash Red on Hit
        if shake_timer > 0:
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(100)
            s.fill(C_RED)
            screen.blit(s, (0,0))

        # UI
        score_surf = font_small.render(f"SCORE: {score}", True, C_WHITE)
        lives_surf = font_small.render(f"LIVES: {lives}", True, C_WHITE)
        screen.blit(score_surf, (50, 50))
        screen.blit(lives_surf, (50, 100))

        pygame.display.flip()
        clock.tick(FPS)
    
    return score

# --- Main Execution ---
while True:
    intro_screen()
    final_score = main_game()
    
    screen.fill(C_ASPHALT)
    draw_text_centered("CRASHED!", font_large, C_RED, -50)
    draw_text_centered(f"Final Score: {final_score}", font_small, C_WHITE, 50)
    draw_text_centered("Press SPACE to Restart", font_small, C_LINE, 100)
    pygame.display.flip()
    
    waiting_end = True
    while waiting_end:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_SPACE:
                    waiting_end = False