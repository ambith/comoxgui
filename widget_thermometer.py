import tkinter as tk

class Thermometer():
    def __init__(self, parent, xpos, ypos, mintemp, maxtemp):
        self.parent = parent
        self.xpos = xpos
        self.ypos = ypos
        self.mintemp = mintemp
        self.maxtemp = maxtemp
        self.canvas = tk.Canvas(self.parent, width=90, height=210, bg="white")
        self.canvas.place(x=self.xpos, y=self.ypos)
        self.canvas.create_rectangle(20, 10, 37, 180)
        self.fixed_oval = self.canvas.create_oval(10, 170, 45, 205, fill="white")
        self.fixed_rect = self.canvas.create_rectangle(21, 160, 37, 180, fill="white", outline="")
        self.slider = self.canvas.create_rectangle(21, 160, 37, 160, fill="white", outline="")
        self.canvas.create_line(32, 160, 42, 160, width=1)
        self.canvas.create_line(32, 10, 42, 10, width=1)
        self.slider_text = self.canvas.create_text(65, 85, font=("Verdana", 8), text="")

    def display(self, temp=None):
        self.temp = temp
        if self.temp is None:
            self.canvas.itemconfig(self.slider_text, text="")
            level_pos = 160 - (0 - self.mintemp) / ((self.maxtemp - self.mintemp) / (160 - 10))
            self.canvas.coords(self.slider, 21, level_pos, 37, 160)
            self.canvas.itemconfig(self.slider, fill="white")
            self.canvas.itemconfig(self.fixed_oval, fill="white")
            self.canvas.itemconfig(self.fixed_rect, fill="white")
        else:
            self.canvas.itemconfig(self.slider_text, text=str(self.temp) + "°C")
            level_pos = 160 - (self.temp - self.mintemp) / ((self.maxtemp - self.mintemp) / (160 - 10))
            if self.temp < self.mintemp:
                self.canvas.coords(self.slider, 21, 160, 37, 160)
                self.canvas.itemconfig(self.slider, fill="blue")
                self.canvas.itemconfig(self.fixed_oval, fill="blue")
                self.canvas.itemconfig(self.fixed_rect, fill="blue")
            elif self.temp > self.maxtemp:
                self.canvas.coords(self.slider, 21, 10, 37, 160)
                self.canvas.itemconfig(self.slider, fill="red")
                self.canvas.itemconfig(self.fixed_oval, fill="red")
                self.canvas.itemconfig(self.fixed_rect, fill="red")
            else:
                self.canvas.coords(self.slider, 21, level_pos, 37, 160)
                self.canvas.itemconfig(self.slider, fill="green")
                self.canvas.itemconfig(self.fixed_oval, fill="green")
                self.canvas.itemconfig(self.fixed_rect, fill="green")
