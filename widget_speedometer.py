import math
import cmath
import tkinter as tk

class Speedometer():
    def __init__(self, parent, xpos, ypos, size=100,
                 max_value: (float, int) = 100.0,
                 min_value: (float, int) = 0.0,
                 img_data: str = None,
                 bg_col: str = 'blue', unit: str = None):
        self.size = size
        self.xpos = xpos
        self.ypos = ypos
        self.parent = parent
        self.max_value = float(max_value)
        self.min_value = float(min_value)
        self.size = size
        self.bg_col = bg_col
        self.unit = '' if not unit else unit

    def draw(self):
        self.canvas = tk.Canvas(self.parent, width=self.size, height=self.size - self.size / 6, bg=self.bg_col,
                                highlightthickness=0)
        self.canvas.place(x=self.xpos, y=self.ypos)
        self.draw_background()
        self.draw_tick()
        initial_value = 0.0
        self.set_value(initial_value)

    def to_absolute(self, x, y):
        return x + self.size / 2, y + self.size / 2

    def draw_dial(self, canv, x0, y0, degree, t, r):
        this_color = "#00A2E8"
        xr = x0
        yr = y0
        angle = math.radians(degree)
        cos_val = math.cos(angle)
        sin_val = math.sin(angle)
        dy = r * sin_val
        dx = r * cos_val
        dx2 = t * sin_val
        dy2 = t * cos_val
        mlx = xr + dx
        mly = yr - dy
        mrx = xr - dx
        mry = yr + dy
        px = xr + dx2
        py = yr + dy2
        xy = x0 - r, y0 - r, x0 + 1 * r, y0 + 1 * r
        xyz = mlx, mly, px, py, mrx, mry
        canv.delete('dial')
        canv.create_arc(xy, start=degree, extent=180, fill=this_color, tags=('dial', 'one', 'two', 'three', 'four'))
        canv.create_polygon(xyz, fill=this_color, tags=('dial', 'two'))
        canv.create_oval(xr - 5, yr - 5, xr + 5, yr + 5, fil=this_color, tags=('dial', 'three'))
        canv.create_line(xr, yr, px, py, fill="light gray", tags=('dial', 'four'))

    def draw_background(self, divisions=100):
        self.canvas.create_arc(self.size / 5, self.size / 6, self.size - self.size / 6, self.size - self.size / 6,
                               style="arc", width=self.size / 10, start=-61, extent=61,
                               outline="red")  # style=tk.PIESLICE
        self.canvas.create_arc(self.size / 6, self.size / 6, self.size - self.size / 6, self.size - self.size / 6,
                               width=self.size / 10, style="arc", start=0, extent=60,
                               outline="orange")
        self.canvas.create_arc(self.size / 6, self.size / 6, self.size - self.size / 6, self.size - self.size / 6,
                               width=self.size / 10, style="arc", start=60, extent=60,
                               outline="yellow")
        self.canvas.create_arc(self.size / 6, self.size / 6, self.size - self.size / 6, self.size - self.size / 6,
                               width=self.size / 10, style="arc", start=120, extent=60,
                               outline="light green")
        self.canvas.create_arc(self.size / 6, self.size / 6, self.size - self.size / 6, self.size - self.size / 6,
                               width=self.size / 10, style="arc", start=180, extent=60,
                               outline="green")
        self.readout = self.canvas.create_text(self.size / 2, 4 * self.size / 5,
                                               font=("Arial", int(self.size / 18), 'bold'), fill="black", text='')

    def draw_tick(self, divisions=100):
        inner_tick_radius = int((self.size - self.size / 9) * 0.35)
        outer_tick_radius = int((self.size - self.size / 9) * 0.43)
        label = self.unit
        self.canvas.create_text(self.size / 2, 3 * self.size / 5, font=("Arial", int(self.size / 20)), fill="black",
                                text=label, angle=0)
        self.readout = self.canvas.create_text(self.size / 2, 4 * self.size / 5,
                                               font=("Arial", int(self.size / 18), 'bold'), fill="black", text='')
        inner_tick_radius2 = int((self.size - self.size / 9) * 0.48)
        outer_tick_radius2 = int((self.size - self.size / 9) * 0.51)
        inner_tick_radius3 = int((self.size - self.size / 9) * 0.35)
        outer_tick_radius3 = int((self.size - self.size / 9) * 0.40)

        for tick in range(divisions + 1):
            angle_in_radians = (2.0 * cmath.pi / 3.0) + tick / divisions * (5.0 * cmath.pi / 3.0)
            inner_point = cmath.rect(inner_tick_radius, angle_in_radians)
            outer_point = cmath.rect(outer_tick_radius, angle_in_radians)
            if (tick % 10) == 0:
                self.canvas.create_line(
                    self.to_absolute(inner_point.real, inner_point.imag),
                    self.to_absolute(outer_point.real, outer_point.imag),
                    width=2, fill='blue')
            else:
                inner_point3 = cmath.rect(inner_tick_radius3, angle_in_radians)
                outer_point3 = cmath.rect(outer_tick_radius3, angle_in_radians)
                self.canvas.create_line(
                    self.to_absolute(inner_point3.real, inner_point3.imag),
                    self.to_absolute(outer_point3.real, outer_point3.imag),
                    width=1, fill='black')
            if (tick % 10) == 0:
                inner_point2 = cmath.rect(inner_tick_radius2, angle_in_radians)
                outer_point2 = cmath.rect(outer_tick_radius2, angle_in_radians)
                x = outer_point2.real + self.size / 2
                y = outer_point2.imag + self.size / 2
                label = int(self.min_value + tick * (self.max_value - self.min_value) / 100)
                if self.min_value < label < self.max_value:
                    self.canvas.create_text(x, y, font=("Arial", int(self.size / 25)), fill="black", text=str(label))

    def set_value(self, number):
        number = number if number <= self.max_value else self.max_value
        number = number if number > self.min_value else self.min_value
        degree = 30.0 + (number - self.min_value) / (self.max_value - self.min_value) * 300.0
        self.draw_dial(self.canvas, self.size / 2, self.size / 2, -1 * degree, self.size / 3, 8)
        label = str('{:3.2f}'.format(number))
        self.canvas.delete(self.readout)
        self.readout = self.canvas.create_text(self.size / 2, 4 * self.size / 5, font=("Arial", int(self.size / 18), 'bold'), fill="black", text=label, angle=0)
