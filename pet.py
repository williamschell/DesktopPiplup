import tkinter as tk
import time
import ctypes
import ctypes.wintypes
from PIL import Image, ImageTk, ImageSequence
import random

# --- SETTINGS ---
WALK_SPEED = 1
FRAME_DELAY = 16
last_time = time.time()

# --- WINDOW ---
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.config(bg="pink")
root.wm_attributes("-transparentcolor", "pink")

# --- SCREEN INFO ---
user32 = ctypes.windll.user32
screen_width = user32.GetSystemMetrics(0)

SPI_GETWORKAREA = 0x0030
rect = ctypes.wintypes.RECT()
ctypes.windll.user32.SystemParametersInfoW(
    SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
)
size = 128
def get_ground_y():
    """Return the current ground level based on Piplup's size."""
    return int(rect.bottom - 0.65 * size)


# --- PET STATE ---
x = 100
y = get_ground_y() - 50
direction = 1
velocity_y = 0
GRAVITY = 0.6


state = "idle"
animation_frames = []
current_frame = 0
frame_counter = 0
frame_delay = 5

# --- GIF LOADER ---
def load_gif_frames(path, size=(128, 128)):
    frames = []
    img = Image.open(path)
    for frame in ImageSequence.Iterator(img):
        frame = frame.convert("RGBA").resize(size, Image.Resampling.NEAREST)
        frames.append(ImageTk.PhotoImage(frame))
    return frames

def flip_frames(frames):
    flipped = []
    for img in frames:
        pil = ImageTk.getimage(img)
        pil = pil.transpose(Image.FLIP_LEFT_RIGHT)
        flipped.append(ImageTk.PhotoImage(pil))
    return flipped

# --- LOAD ANIMATIONS ---
idle_animations = [
    load_gif_frames("idle1.gif"),
    load_gif_frames("idle2.gif")
]

walk_right = load_gif_frames("walk.gif")
walk_left  = flip_frames(walk_right)

drag_frames = load_gif_frames("drag.gif")
fall_right  = load_gif_frames("fall.gif")
fall_left   = flip_frames(fall_right)
ANIM_SPEEDS = {
    "idle": 20,
    "walking": 16,
    "fall": 3,
    "drag": 2
}

# --- PICK IDLE ---
def pick_idle():
    global animation_frames, current_frame
    animation_frames = random.choice(idle_animations)
    current_frame = 0

pick_idle()

label = tk.Label(root, image=animation_frames[0], bg="pink")
label.pack()

# --- DRAGGING ---
dragging = False
offset_x = offset_y = 0

def start_drag(e):
    global dragging, state, animation_frames, offset_x, offset_y
    dragging = True
    state = "drag"
    animation_frames = drag_frames
    offset_x = e.x
    offset_y = e.y


def stop_drag(e):
    global dragging, velocity_y, state
    dragging = False
    velocity_y = 0
    state = "idle"
    pick_idle()

def drag(e):
    global x, y
    if dragging:
        x = e.x_root - int(.520 * size)
        y = e.y_root - int(.39 * size)

label.bind("<ButtonPress-1>", start_drag)
label.bind("<ButtonRelease-1>", stop_drag)
label.bind("<B1-Motion>", drag)



# --- MAIN LOOP ---
def update():
    global x, y, velocity_y, state, animation_frames
    global current_frame, frame_counter, last_time, direction

    dt = time.time() - last_time
    last_time = time.time()

    if dragging:
        state = "drag"
        animation_frames = drag_frames
    else:
        velocity_y += GRAVITY * dt * 60
        y += velocity_y

        if y < get_ground_y():
            state = "fall"
            animation_frames = fall_right if direction == 1 else fall_left

        else:
            # JUST LANDED
            if state == "fall":
                state = "idle"
                pick_idle()

            y = get_ground_y()
            velocity_y = 0
            if random.random() < 0.002:
                if state != "walking":
                    state = "walking"
                    direction *= random.choice([-1, 1])
                    animation_frames = walk_right if direction == 1 else walk_left
                else:
                    state = "idle"
                    pick_idle()

            if state == "walking":
                x += WALK_SPEED * direction

                # --- SCREEN EDGE COLLISION ---
                if x <= 0:
                    x = 0
                    direction = 1
                elif x >= screen_width - 50:
                    x = screen_width - 50
                    direction = -1

                # --- ensure correct based on current direction ---
                animation_frames = walk_right if direction == 1 else walk_left


    frame_delay = ANIM_SPEEDS.get(state, 5)
    frame_counter += 1
    if frame_counter >= frame_delay:
        frame_counter = 0
        current_frame = (current_frame + 1) % len(animation_frames)
        label.config(image=animation_frames[current_frame])

    root.geometry(f"+{int(x)}+{int(y)}")
    root.after(FRAME_DELAY, update)

    
# --- SETTINGS WINDOW ---
def open_settings():
    settings = tk.Toplevel(root)
    settings.title("Desktop Piplup")
    settings.geometry("280x220")
    settings.attributes("-topmost", True)
    settings.config(bg="#FFCCEE")

    label_font = ("Comic Sans MS", 12, "bold")
    button_font = ("Comic Sans MS", 10, "bold")

    # --- Size Slider ---
    size_frame = tk.Frame(settings, bg="#FFCCEE")
    size_frame.pack(pady=10, fill="x")
    tk.Label(size_frame, text="🐧 Piplup Size", bg="#FFCCEE", font=label_font).pack(pady=5)
    size_var = tk.IntVar(value=128)

    # BOOG, certified my work (ws)
    def update_size(value):
        global animation_frames, walk_right, walk_left, drag_frames, fall_right, fall_left, idle_animations, size
        size = int(value)
        # reload all GIFs at new size
        walk_right = load_gif_frames("walk.gif", size=(size, size))
        walk_left  = flip_frames(walk_right)
        drag_frames = load_gif_frames("drag.gif", size=(size, size))
        fall_right  = load_gif_frames("fall.gif", size=(size, size))
        fall_left   = flip_frames(fall_right)
        idle_animations[0] = load_gif_frames("idle1.gif", size=(size, size))
        idle_animations[1] = load_gif_frames("idle2.gif", size=(size, size))
        # update current animation to reflect new size
        animation_frames = walk_right if direction == 1 else walk_left

    tk.Scale(
        size_frame,
        from_=64,
        to=256,
        orient="horizontal",
        variable=size_var,
        command=update_size,
        length=200,
        bg="#FFCCEE",
        fg="#333",
        troughcolor="#FFC0CB",
        highlightthickness=0
    ).pack(pady=5)


    # --- Buttons Frame ---
    btn_frame = tk.Frame(settings, bg="#FFCCEE")
    btn_frame.pack(pady=15)
    # --- Respawn Button ---
    def respawn():
        global x, y, velocity_y
        x = 100
        y = get_ground_y() - size // 2
        velocity_y = 0

    tk.Button(
        btn_frame,
        text="✨ Respawn Piplup",
        command=respawn,
        bg="#FF99CC",
        fg="white",
        font=button_font,
        relief="flat",
        width=20,
        activebackground="#FF66AA"
    ).pack(pady=5)


    # --- exit Button ---
    tk.Button(
        btn_frame,
        text="❌ Exit",
        command=root.destroy,
        bg="#FF6666",
        fg="white",
        font=button_font,
        relief="flat",
        width=20,
        activebackground="#FF3333"
    ).pack(pady=5)

# --- settings button ---
root.bind("<Button-3>", lambda e: open_settings())

# --- START ---
root.geometry(f"+{x}+{y}")
update()
root.mainloop()
