import time
from datetime import datetime
import platform

# Sound alert based on OS
def play_alert_sound():
    system = platform.system()

    if system == "Windows":
        import winsound
        for i in range(3):
            winsound.Beep(2000, 500)
            time.sleep(0.3)
    else:
        try:
            from playsound import playsound
            playsound("alert.mp3")
        except:
            print("⚠ Sound failed — install playsound or add an alert.mp3 file.")

# ---------------------------------------
# MULTIPLE ALERTS PER DAY FOR SAME MEDICINE
# ---------------------------------------

reminders = {}

print("==== Medicine Reminder System (Multiple Alerts Per Day) ====\n")

n = int(input("Enter number of medicines to set reminders for: "))

for i in range(n):
    name = input(f"\nEnter medicine name {i+1}: ")

    print("Enter reminder times for this medicine (HH:MM).")
    print("Type 'done' when finished.\n")

    times = []
    while True:
        t = input("Enter time: ")
        if t.lower() == "done":
            break
        times.append(t)

    reminders[name] = times

print("\nAll reminders set successfully!")
print("The system will alert you at the correct time.\n")
print("Press Ctrl + C to exit.\n")

# To avoid repeating alerts
already_alerted = set()

try:
    while True:
        now = datetime.now().strftime("%H:%M")

        for med, times in reminders.items():
            for t in times:
                key = (med, t)

                if now == t and key not in already_alerted:
                    print(f"\n⏰ ALERT! Time to take your medicine: {med} ({t})")

                    play_alert_sound()

                    already_alerted.add(key)

        time.sleep(10)

except KeyboardInterrupt:
    print("\nProgram stopped.")