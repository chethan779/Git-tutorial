import tkinter as tk
from tkinter import scrolledtext
import google.generativeai as genai

# ---------------- CONFIG ----------------
API_KEY = "YOUR_API_KEY_HERE"   # <--- put your key here

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Gemini Chat (Dark Mode)")
root.configure(bg="#000000")  # black background

# 🔥 FULLSCREEN MODE 🔥
root.attributes("-fullscreen", True)

# Colors
BG = "#000000"
TEXT = "#FFFFFF"
ENTRY_BG = "#1A1A1A"
BTN_BG = "#262626"
BTN_HOVER = "#3A3A3A"

# Chat Window
chat_box = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    state="disabled",
    bg=BG,
    fg=TEXT,
    font=("Segoe UI", 14),
    insertbackground="white",
    borderwidth=0,
)
chat_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# Entry box
entry = tk.Entry(
    root,
    bg=ENTRY_BG,
    fg=TEXT,
    font=("Segoe UI", 16),
    insertbackground="white",
    relief="flat",
    borderwidth=2,
)
entry.pack(fill=tk.X, padx=20, pady=(0, 20))

# Modern Button (flat + dark)
def on_enter(e):
    send_btn["bg"] = BTN_HOVER

def on_leave(e):
    send_btn["bg"] = BTN_BG

send_btn = tk.Button(
    root,
    text="Send",
    bg=BTN_BG,
    fg=TEXT,
    font=("Segoe UI", 16),
    relief="flat",
    activebackground=BTN_HOVER,
    activeforeground="white",
    cursor="hand2",
    command=lambda: send_message(),
)
send_btn.pack(pady=(0, 20))

send_btn.bind("<Enter>", on_enter)
send_btn.bind("<Leave>", on_leave)

# ------------ Function to send message -------------
def send_message():
    user_text = entry.get().strip()
    if not user_text:
        return
    entry.delete(0, tk.END)

    # 🔥 EXIT THE APP WHEN USER TYPES EXIT/QUIT/BYE
    if user_text.lower() in ["exit", "quit", "bye"]:
        root.destroy()
        return

    # Show user message
    chat_box.config(state="normal")
    chat_box.insert(tk.END, f"You: {user_text}\n")
    chat_box.config(state="disabled")
    chat_box.see(tk.END)

    # Gemini response
    try:
        response = chat.send_message(user_text)
        bot_text = response.text
    except Exception as e:
        bot_text = f"(error) {e}"

    # Show bot reply
    chat_box.config(state="normal")
    chat_box.insert(tk.END, f"Bot: {bot_text}\n\n")
    chat_box.config(state="disabled")
    chat_box.see(tk.END)

# Enter key sends message
entry.bind("<Return>", lambda e: send_message())

# Press ESC to exit fullscreen
root.bind("<Escape>", lambda e: root.destroy())

root.mainloop()
