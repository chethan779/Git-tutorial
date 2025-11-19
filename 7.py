import time
from datetime import datetime, date, timedelta
import platform
import pygame
import sys

# -------------------------
# Setup: get reminders via console (same as original)
# -------------------------
reminders = {}

print("==== Medicine Reminder System (Pygame) ====\n")

try:
    n = int(input("Enter number of medicines to set reminders for: "))
except ValueError:
    print("Invalid number. Exiting.")
    sys.exit(1)

for i in range(n):
    name = input(f"\nEnter medicine name {i+1}: ")

    print("Enter reminder times for this medicine (HH:MM).")
    print("Type 'done' when finished.\n")

    times = []
    while True:
        t = input("Enter time: ").strip()
        if t.lower() == "done":
            break
        # basic validation
        try:
            hh, mm = t.split(":")
            hh = int(hh); mm = int(mm)
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                times.append(f"{hh:02d}:{mm:02d}")
            else:
                print("Invalid time. Use HH:MM 24-hour.")
        except Exception:
            print("Invalid format. Use HH:MM")
    reminders[name] = sorted(set(times))

print("\nAll reminders set successfully!")
print("The pygame window will open. Press Ctrl+C in console or close the window to exit.")
time.sleep(1)

# -------------------------
# Pygame initialization and sound loading
# -------------------------
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Medicine Reminder (Pygame)")

# fonts
FONT_SMALL = pygame.font.SysFont(None, 20)
FONT_MED = pygame.font.SysFont(None, 28)
FONT_LARGE = pygame.font.SysFont(None, 48)
FONT_XL = pygame.font.SysFont(None, 72)

# load sound
sound_available = False
alert_sound = None
try:
    pygame.mixer.init()
    # try mp3 then wav
    try:
        alert_sound = pygame.mixer.Sound("alert.mp3")
    except Exception:
        try:
            alert_sound = pygame.mixer.Sound("alert.wav")
        except Exception:
            alert_sound = None
    if alert_sound:
        sound_available = True
except Exception:
    sound_available = False

if not sound_available:
    print("⚠ Could not load alert sound (alert.mp3 / alert.wav). Visual alerts will still work.")

clock = pygame.time.Clock()

# -------------------------
# State for alerts
# -------------------------
already_alerted = set()   # (med, "HH:MM")
current_date = date.today()

# snooze dict: (med, time) -> snooze_until datetime
snoozed_until = {}

# alert popup state
active_alerts = []  # list of tuples (med, time, started_at_dt)
FLASH_ON = False
flash_timer = 0

# helper: play alert
def play_alert():
    if sound_available and alert_sound:
        try:
            # play in non-blocking mode
            alert_sound.play(loops=2)  # play 3 times total if file small
        except Exception:
            pass

# helper: validate time string
def validate_time(t):
    try:
        hh, mm = t.split(":")
        hh = int(hh); mm = int(mm)
        return 0 <= hh <= 23 and 0 <= mm <= 59
    except Exception:
        return False

# -------------------------
# Main loop
# -------------------------
running = True
CHECK_INTERVAL_MS = 1000  # check every second

def draw_text(surface, text, font, color, x, y):
    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))

def refresh_daily_reset():
    global current_date, already_alerted, snoozed_until
    today = date.today()
    if today != current_date:
        current_date = today
        already_alerted.clear()
        snoozed_until.clear()

while running:
    # events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_d:
                # dismiss current alerts
                if active_alerts:
                    print("Dismissed alerts:", active_alerts)
                    active_alerts.clear()
            elif event.key == pygame.K_s:
                # snooze active alerts for 5 minutes
                if active_alerts:
                    snooze_minutes = 5
                    now_dt = datetime.now()
                    for med, t in active_alerts:
                        key = (med, t)
                        snoozed_until[key] = now_dt + timedelta(minutes=snooze_minutes)
                    print(f"Snoozed {len(active_alerts)} alerts for {snooze_minutes} minutes.")
                    active_alerts.clear()

    # reset daily
    refresh_daily_reset()

    # check reminders (every second)
    now_str = datetime.now().strftime("%H:%M")
    now_dt = datetime.now()

    # check scheduled reminders
    for med, times in reminders.items():
        for t in times:
            key = (med, t)

            # if snoozed and snooze not expired, skip
            if key in snoozed_until:
                if now_dt < snoozed_until[key]:
                    continue
                else:
                    # snooze expired
                    del snoozed_until[key]

            if now_str == t and key not in already_alerted:
                # trigger alert
                already_alerted.add(key)
                active_alerts.append((med, t, now_dt))
                play_alert()

    # UI drawing
    screen.fill((30, 35, 40))

    # current time
    curr_time_display = datetime.now().strftime("%H:%M:%S")
    draw_text(screen, f"Current time: {curr_time_display}", FONT_MED, (240,240,240), 20, 20)
    draw_text(screen, "Press D to Dismiss alerts, S to Snooze 5 minutes, ESC to Quit", FONT_SMALL, (200,200,200), 20, 52)

    # draw reminders list box
    box_x, box_y = 20, 90
    box_w, box_h = 420, 480
    pygame.draw.rect(screen, (45,50,60), (box_x, box_y, box_w, box_h))
    draw_text(screen, "Scheduled Reminders", FONT_MED, (220,220,220), box_x+10, box_y+8)
    y = box_y + 40
    for med, times in sorted(reminders.items()):
        draw_text(screen, f"{med} :", FONT_SMALL, (200,200,200), box_x+12, y)
        x_off = 120
        for t in times:
            color = (160,160,160)
            if (med, t) in already_alerted:
                color = (255,180,180)
            draw_text(screen, t, FONT_SMALL, color, box_x + x_off, y)
            x_off += 55
        y += 22

    # draw Snoozed list
    snooze_x = box_x + box_w + 20
    snooze_y = box_y
    draw_text(screen, "Snoozed Until (active)", FONT_MED, (220,220,220), snooze_x, snooze_y+8)
    sy = snooze_y + 40
    for key, until in sorted(snoozed_until.items(), key=lambda x: x[1]):
        med, t = key
        draw_text(screen, f"{med} @ {t} -> {until.strftime('%H:%M:%S')}", FONT_SMALL, (200,200,200), snooze_x, sy)
        sy += 20

    # Active alerts popup
    if active_alerts:
        # flash background and draw popup
        flash_timer += clock.get_time()
        if flash_timer > 500:
            FLASH_ON = not FLASH_ON
            flash_timer = 0
        popup_color = (200, 50, 50) if FLASH_ON else (120, 10, 10)
        popup_w = 420
        popup_h = 220
        popup_x = (WIDTH - popup_w) // 2
        popup_y = (HEIGHT - popup_h) // 2
        pygame.draw.rect(screen, popup_color, (popup_x, popup_y, popup_w, popup_h), border_radius=8)
        pygame.draw.rect(screen, (255,255,255), (popup_x+6, popup_y+6, popup_w-12, popup_h-12), border_radius=6)

        # show first active alert (or count)
        first_med, first_t, start_dt = active_alerts[0]
        draw_text(screen, "⏰ Medicine Alert!", FONT_XL, (10,10,10), popup_x+24, popup_y+14)
        draw_text(screen, f"{first_med}  —  {first_t}", FONT_LARGE, (10,10,10), popup_x+30, popup_y+100)

        draw_text(screen, "Press S to Snooze (5 min)   |   Press D to Dismiss", FONT_MED, (10,10,10), popup_x+24, popup_y+170)

    # small footer
    draw_text(screen, "Made with pygame — visual alerts + sound (if alert.mp3/alert.wav present)", FONT_SMALL, (160,160,160), 20, HEIGHT-26)

    pygame.display.flip()
    clock.tick(30)  # 30 FPS, checks run every second (we compare seconds string)

pygame.quit()
print("Program stopped.")
