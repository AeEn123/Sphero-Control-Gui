import tkinter as tk
from tkinter import colorchooser
import pygame
import threading
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from spherov2.utils import ToyUtil
from spherov2.utils import Color
import math, time

def joystick_to_distance_angle(x, y):
    """
    Converts joystick X and Y values to distance and angle (0° points up).

    Parameters:
    x (float): Joystick X-axis value (typically -1.0 to 1.0).
    y (float): Joystick Y-axis value (typically -1.0 to 1.0).

    Returns:
    tuple: A tuple containing:
        - distance (float): Magnitude from the neutral position (0 to ~1.414).
        - angle (float): Direction in degrees (0°=up, 90°=right, etc.), or None if distance is 0.
    """
    distance = math.sqrt(x**2 + y**2)
    if distance == 0:
        return (0.0, None)
    
    # Calculate angle relative to the UP (Y-axis) direction
    angle_rad = math.atan2(x, y)  # Swapped X/Y to make 0° point up
    angle_deg = math.degrees(angle_rad) % 360
    
    return (distance, angle_deg)

def set_raw_motor(toy,left,right):
    ToyUtil.set_raw_motor(toy,
                        2 if left < 0 else 1,
                        abs(left),
                        2 if right < 0 else 1,
                        abs(right))

class Application(tk.Tk):
    def __init__(self, toy, api):
        super().__init__()
        self.title("Sphero GUI")
        self.geometry("640x400")
        self.current_color = (255, 255, 255)
        self.pressed_keys = {}
        self.controller_buttons = {}
        self.setup_gui()
        self.setup_controller()
        self.setup_keyboard()
        self.after_id = None
        self.toy = toy
        self.api = api
        self.speed = 255
        self.fpv = False
        self.x_axis = 0
        self.y_axis = 0
        self.z_axis = 0
        threading.Thread(target=self.movement_loop, daemon=True).start()

    def setup_gui(self):
        # Color Picker Button
        frame = tk.Frame(self)
        
        self.color_btn = tk.Button(frame, text="Set Main LED colour", command=self.choose_color)
        self.color_btn.pack(side=tk.LEFT)
        self.fpv_mode_checkbox = tk.Checkbutton(frame, text="FPV mode (B)", command=self.toggle_mode)
        self.fpv_mode_checkbox.pack(side=tk.RIGHT)
        tk.Button(frame, text="Recalibrate (A)", command=self.recalibrate).pack(side=tk.RIGHT)


        frame.pack(expand=True)

        # LED Slider
        self.led_slider_label = tk.Label(self, text="Back LED brightness")
        self.led_slider_label.pack(pady=0)
        self.led_slider = tk.Scale(self, from_=0, to=255, orient=tk.HORIZONTAL, command=self.led_slider_changed)
        self.led_slider.pack(fill=tk.X, padx=20, pady=0)
        
        # Speed Slider
        self.speed_slider_label = tk.Label(self, text="Speed (right stick)")
        self.speed_slider_label.pack(pady=0)
        self.speed_slider = tk.Scale(self, from_=0, to=255, orient=tk.HORIZONTAL, command=self.speed_slider_changed)
        self.speed_slider.set(255)
        self.speed_slider.pack(fill=tk.X, padx=20, pady=0)

        # Color Display
        self.color_display = tk.Canvas(self, width=100, height=100, bg="#ffffff")
        self.color_display.pack(pady=20)

        tk.Button(self, text="Quit", command=quit).pack(side=tk.BOTTOM)


    def quit(self):
        self.destroy()
    
    def recalibrate(self):
        api.reset_aim()
    
    def toggle_mode(self, fpv=None):
        if fpv == None:
            fpv = not self.fpv
        
        self.fpv = fpv

        if fpv:
            api.set_stabilization(False)
        else:
            api.raw_motor(0,0,0) # Reset motors
            api.set_stabilization(True)
        
        return fpv

    def move(self, x,y):
        print(x,y)
        startTime = time.time()
        if self.fpv:
            left_motor = int(min(max(y+x,-1),1)*self.speed)
            right_motor = int(min(max(y-x,-1),1)*self.speed)
            set_raw_motor(self.toy, left_motor, right_motor)
        else:
            distance, angle = joystick_to_distance_angle(x,y)
            speed = min(max(distance*self.speed,0),self.speed)
            api.set_speed(round(speed))
            if angle != None:
                api.set_heading(round(angle))
        print(time.time()-startTime)
        return time.time()-startTime
    
    def movement_loop(self):
        while True:
            self.move(self.x_axis, self.y_axis)
            if self.z_axis != 0:
                self.speed_slider.set(int(self.speed_slider.get() + self.z_axis*16))
        
    def setup_keyboard(self):
        self.bind("<KeyPress>", self.handle_key_down)
        self.bind("<KeyRelease>", self.handle_key_up)

    def setup_controller(self):
        pygame.init()
        pygame.joystick.init()
        try:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller detected: {self.joystick.get_name()}")
            threading.Thread(target=self.poll_controller, daemon=True).start()
        except Exception as e:
            print(f"No controller found: {e}")

    def choose_color(self):        
        color = colorchooser.askcolor(self.current_color)[0]
        if color:
            self.current_color = tuple(map(int, color))
            self.update_color_display()

    def led_slider_changed(self, value):
        api.set_back_led(int(value))
    
    def speed_slider_changed(self, value):
        self.speed = int(value)

    def update_color_display(self):
        hex_color = "#%02x%02x%02x" % self.current_color
        self.color_display.config(bg=hex_color)
        api.set_main_led(Color(self.current_color[0],self.current_color[1],self.current_color[2]))

    def handle_key_down(self, event):
        if event.keysym not in self.pressed_keys:
            self.pressed_keys[event.keysym] = True
            self.update_key_display()

    def handle_key_up(self, event):
        if event.keysym in self.pressed_keys:
            del self.pressed_keys[event.keysym]
            self.update_key_display()


    def cancel_repeat(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None

    def update_key_display(self):
        print(self.pressed_keys.keys())
        up = 0
        down = 0
        left = 0
        right = 0
        zup = 0
        zdown = 0
        if "w" in self.pressed_keys.keys():
            up = 1
        if "s" in self.pressed_keys.keys():
            down = 1
        if "a" in self.pressed_keys.keys():
            left = 1
        if "d" in self.pressed_keys.keys():
            right = 1
        if "e" in self.pressed_keys.keys():
            self.fpv_mode_checkbox.toggle()
            self.toggle_mode()
        if "Left" in self.pressed_keys.keys():
            zdown = 1
        if "Right" in self.pressed_keys.keys():
            zup = 1
        

        self.x_axis = right-left
        self.y_axis = up-down
        self.z_axis = zup-zdown

    def poll_controller(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    self.controller_buttons[event.button] = True
                    self.after(0, self.update_controller_display)
                    if event.button == 0:  # A button
                        self.after(0, self.recalibrate)
                    elif event.button == 1: # B button
                        self.fpv_mode_checkbox.toggle()
                        self.after(0, self.toggle_mode)
                elif event.type == pygame.JOYBUTTONUP:
                    if event.button in self.controller_buttons:
                        del self.controller_buttons[event.button]
                        self.after(0, self.update_controller_display)

                elif event.type == pygame.JOYAXISMOTION:
                    value = event.value
                    if abs(event.value) < 0.1:
                        value = 0
                    if event.axis == 0:  # Left stick horizontal
                        self.x_axis = value
                    elif event.axis == 1: # Left stick vertical
                        self.y_axis = -value
                    elif event.axis == 3: # Right stick horizontal                            
                        self.z_axis = value
            pygame.time.wait(50)

    def update_controller_display(self):
        print(self.controller_buttons.keys())

if __name__ == "__main__":
    toy = scanner.find_toy()
    with SpheroEduAPI(toy) as api:
        app = Application(toy,api)
        app.mainloop()
