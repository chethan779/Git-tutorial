import time
import threading
from datetime import datetime
import platform
import pygame
import sys

# ---------------------------------------
# SOUND ALERT
# ---------------------------------------
def play_alert_sound():
    system = platform.system()

    if system == "Windows":
        import winsound
        for _ in range(3):
            winsound.Beep(2000, 500)
            time.sleep(0.2)
    else:
        pygame.mixer.init()
        try:
            pygame.mixer.music.load("alert.mp3")
            pygame.mixer.music.play()
        except:
            print("No alert sound found.")


# ---------------------------------------
# Pygame GRAPHICAL ALERT POPUP
# ---------------------------------------
def pygame_alert(medicine, time_now):
    pygame.init()
    WIDTH, HEIGHT = 600, 400
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Medicine Alert")

    clock = pygame.time.Clock()

    # Fonts
    font_title = pygame.font.SysFont("Arial", 36, bold=True)
    font_text = pygame.font.SysFont("Arial", 24)
    font_button = pygame.font.SysFont("Arial", 26, bold=True)

    # Load pill image
    try:
        pill_img = pygame.image.load("pill.png")
        pill_img = pygame.transform.scale(pill_img, (120, 120))
    except:
        pill_img = None  # continue without image

    # OK button
    button_rect = pygame.Rect(WIDTH//2 - 70, HEIGHT - 80, 140, 50)

    glow_alpha = 0
    glow_direction = 1

    play_alert_sound()

    # The alert loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    pygame.quit()
                    return

        # -------------------------
        # Gradient background
        # -------------------------
        for y in range(HEIGHT):
            color = (20 + y//10, 20, 80 + y//6)
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))

        # -------------------------
        # Glow animation
        # -------------------------
        glow_alpha += glow_direction * 5
        if glow_alpha >= 180:
            glow_direction = -1
        if glow_alpha <= 0:
            glow_direction = 1

        glow_surface = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surface, (255, 0, 0, glow_alpha), (50, 0, WIDTH-100, 90))
        screen.blit(glow_surface, (0, 20))

        # -------------------------
        # Text
        # -------------------------
        title = font_title.render("⏰ TIME TO TAKE YOUR MEDICINE", True, (255, 255, 255))
        screen.blit(title, (40, 40))

        med_text = font_text.render(f"Medicine: {medicine}", True, (255, 255, 255))
        time_text = font_text.render(f"Time: {time_now}", True, (255, 255, 255))
        screen.blit(med_text, (50, 160))
        screen.blit(time_text, (50, 200))

        # -------------------------
        # Pill Image
        # -------------------------
        if pill_img:
            screen.blit(pill_img, (WIDTH - 170, 130))

        # -------------------------
        # Button (hover effect)
        # -------------------------
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (0, 255, 100), button_rect, border_radius=10)
        else:
            pygame.draw.rect(screen, (0, 180, 70), button_rect, border_radius=10)

        button_text = font_button.render("OK", True, (255, 255, 255))
        screen.blit(button_text, (button_rect.x + 45, button_rect.y + 10))

        pygame.display.update()
        clock.tick(30)


# ---------------------------------------
# REMINDER SYSTEM (same as before)
# ---------------------------------------

reminders = {}
already_alerted = set()

print("==== Medicine Reminder System (Graphics + Sound) ====\n")
n = int(input("Enter number of medicines: "))

for i in range(n):
    name = input(f"\nEnter medicine name {i+1}: ")
    print("Enter times (HH:MM). Type 'done' to finish.")

    times = []
    while True:
        t = input("Time: ")
        if t.lower() == "done":
            break
        times.append(t)

    reminders[name] = times

print("\nReminders set! Program running...\n")


# Background loop thread
def reminder_loop():
    while True:
        now = datetime.now().strftime("%H:%M")

        for med, times in reminders.items():
            for t in times:
                key = (med, t)

                if now == t and key not in already_alerted:
                    print(f"\n⏰ ALERT! Take your medicine: {med} ({t})")

                    pygame_alert(med, t)

                    already_alerted.add(key)

        time.sleep(10)


threading.Thread(target=reminder_loop, daemon=True).start()

# Keep program alive
while True:
    time.sleep(1)