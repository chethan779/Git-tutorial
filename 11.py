import customtkinter as ctk
import tkinter as tk
import math
import time
import random
import ctypes

# --- 1. DPI Fix (Sharp rendering on Windows) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass


# --- Config ---
ctk.set_appearance_mode("Dark")
COLOR_BG = "#020205" # Almost pure black

# Colors for the connections (Simulating fading opacity)
# Closest = Bright Cyan, Furthest = Dark Blue
LINE_COLORS = ["#FFFFFF", "#80DEEA", "#26C6DA", "#006064"]
MAX_DISTANCE = 130 # Pixels. Nodes further than this won't connect.

class Particle:
    def _init_(self, w, h):
        self.w = w
        self.h = h
        self.x = random.randint(0, w)
        self.y = random.randint(0, h)
        # Random slow velocity
        self.vx = random.uniform(-0.8, 0.8)
        self.vy = random.uniform(-0.8, 0.8)
        self.radius = random.randint(2, 4)

    def move(self):
        self.x += self.vx
        self.y += self.vy

        # Bounce off edges
        if self.x <= 0 or self.x >= self.w: self.vx *= -1
        if self.y <= 0 or self.y >= self.h: self.vy *= -1

class FocusNetworkApp(ctk.CTk):
    def _init_(self):
        super()._init_()

        self.title("Neural Focus")
        self.geometry("800x600")
        self.configure(fg_color=COLOR_BG)
        
        self.running = False
        self.total_seconds = 0
        self.start_time = 0
        self.particles = []
        self.quotes = ["Connect the dots.", "Thinking...", "Deep Work Mode.", "Neural Link: Active.", "Silence the noise."]
        
        # --- Canvas ---
        self.canvas = tk.Canvas(self, bg=COLOR_BG, highlightthickness=0, bd=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # --- UI INPUTS (Floating) ---
        self.entry = ctk.CTkEntry(
            self, placeholder_text="Minutes", width=140, height=40,
            font=("Arial", 20), justify="center", 
            fg_color="#101015", border_color="#333344"
        )
        
        self.btn_start = ctk.CTkButton(
            self, text="INITIALIZE", font=("Consolas", 16, "bold"), 
            width=140, height=40, fg_color="#00BCD4", hover_color="#0097A7",
            text_color="black", command=self.start_focus
        )

        # --- CANVAS TEXT (Transparency Fix) ---
        
        # Title
        self.txt_title = self.canvas.create_text(
            0, 0, text="NEURAL LINK", font=("Consolas", 50, "bold"), fill="#FFFFFF", tags="ui"
        )
        
        # Timer
        self.txt_timer = self.canvas.create_text(
            0, 0, text="", font=("Consolas", 120, "bold"), fill="#FFFFFF", state="hidden", tags="ui"
        )
        
        # Quote
        self.txt_quote = self.canvas.create_text(
            0, 0, text="", font=("Arial", 20, "italic"), fill="#B0BEC5", state="hidden", tags="ui"
        )

        self.bind("<Escape>", self.stop_focus)
        self.bind("<Configure>", self.on_resize)
        
        self.after(100, self.init_particles)
        self.animate()

    def init_particles(self):
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        # Create 60 nodes. Too many = lag (O(N^2) complexity)
        self.particles = [Particle(w, h) for _ in range(60)]
        self.center_ui()

    def on_resize(self, event):
        self.center_ui()
        
    def center_ui(self):
        w = self.winfo_width()
        h = self.winfo_height()
        self.canvas.coords(self.txt_title, w//2, h//2 - 80)
        self.canvas.coords(self.txt_timer, w//2, h//2 - 40)
        self.canvas.coords(self.txt_quote, w//2, h//2 + 100)
        
        if not self.running:
            self.entry.place(relx=0.5, rely=0.5, anchor="center")
            self.btn_start.place(relx=0.5, rely=0.6, anchor="center")

    def start_focus(self):
        try:
            minutes = int(self.entry.get())
            self.total_seconds = minutes * 60
            self.start_time = time.time()
            self.running = True
            
            self.entry.place_forget()
            self.btn_start.place_forget()
            self.canvas.itemconfigure(self.txt_title, state="hidden")
            
            self.canvas.itemconfigure(self.txt_timer, state="normal")
            self.canvas.itemconfigure(self.txt_quote, state="normal")
            
            self.attributes("-fullscreen", True)
            self.focus_force()
            self.update_idletasks()
            self.center_ui()
            
        except ValueError:
            pass

    def stop_focus(self, event=None):
        self.running = False
        self.attributes("-fullscreen", False)
        
        self.canvas.itemconfigure(self.txt_timer, state="hidden")
        self.canvas.itemconfigure(self.txt_quote, state="hidden")
        
        self.canvas.itemconfigure(self.txt_title, state="normal")
        self.entry.place(relx=0.5, rely=0.5, anchor="center")
        self.btn_start.place(relx=0.5, rely=0.6, anchor="center")

    def animate(self):
        # 1. Move Particles & Redraw Dots
        self.canvas.delete("network") # Clear previous frame's lines/dots
        
        # We draw lines first so dots appear on top
        for i, p1 in enumerate(self.particles):
            p1.move()
            
            # Check connection with neighbors (O(N^2) loop)
            for j in range(i + 1, len(self.particles)):
                p2 = self.particles[j]
                
                # Calculate Euclidean distance
                dx = p1.x - p2.x
                dy = p1.y - p2.y
                dist = math.hypot(dx, dy)
                
                if dist < MAX_DISTANCE:
                    # Determine color based on distance (Fake transparency)
                    intensity = int((dist / MAX_DISTANCE) * len(LINE_COLORS))
                    if intensity >= len(LINE_COLORS): intensity = len(LINE_COLORS) - 1
                    col = LINE_COLORS[intensity]
                    
                    self.canvas.create_line(
                        p1.x, p1.y, p2.x, p2.y,
                        fill=col, width=1, tags="network"
                    )

            # Draw the Node itself
            r = p1.radius
            self.canvas.create_oval(
                p1.x - r, p1.y - r, p1.x + r, p1.y + r,
                fill="white", outline="", tags="network"
            )
            
        # Keep text on top
        self.canvas.tag_raise("ui")

        # Timer Logic
        if self.running:
            elapsed = time.time() - self.start_time
            remaining = self.total_seconds - elapsed
            
            if remaining <= 0:
                self.stop_focus()
            else:
                m = int(remaining // 60)
                s = int(remaining % 60)
                self.canvas.itemconfigure(self.txt_timer, text=f"{m:02}:{s:02}")
                
                q_idx = int(elapsed // 15) % len(self.quotes)
                self.canvas.itemconfigure(self.txt_quote, text=self.quotes[q_idx])

        self.after(30, self.animate)

# --- THE FIX IS HERE ---
if __name__ == "_main_":
    app = FocusNetworkApp()
    app.mainloop()