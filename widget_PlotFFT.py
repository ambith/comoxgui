import tkinter as tk
import matplotlib
import matplotlib.pyplot
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

class PlotFFT(tk.Frame):
    def __init__(self, parent, title, xtitle, ytitle, row, column, xmin=None, xmax=None, ymin=None, ymax=None, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.parent = parent
        self.title = title
        self.xtitle = xtitle
        self.ytitle = ytitle
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.row = row
        self.column = column
        fig = Figure(figsize=(3.5, 2.5), dpi=100)
        fig.set_tight_layout(True)
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(fig, self.parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=self.row, column=self.column)
        self.updatePlot(x=[1E-1], y=[1E-1])

    def hide(self):
        self.canvas.get_tk_widget().grid_remove()

    def show(self):
        self.canvas.get_tk_widget().grid()

    def updatePlot(self, x, y, yn=None):
        self.ax.clear()
        self.ax.set_title(self.title, fontsize=8, family="verdana")
        self.ax.set_xlabel(self.xtitle, fontsize=8)
        self.ax.set_ylabel(self.ytitle, fontsize=8)
        self.ax.tick_params(labelsize=8)
        self.ax.grid()
        if (self.xmin is not None) and (self.xmax is not None):
            self.ax.set_xlim(left=self.xmin, right=self.xmax)
        if (self.ymin is not None) and (self.ymax is not None):
            self.ax.set_ylim(bottom=self.ymin, top=self.ymax)
        if yn is not None:
            self.ax.plot(x, [yn]*len(y), color="silver")
        self.ax.plot(x, y, color="tab:blue")
        self.canvas.draw()
