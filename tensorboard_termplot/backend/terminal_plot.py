import plotext as plt
import plotext.utility as plt_util

from .base_plotter import Plotter


class TerminalPlot(Plotter):
    @property
    def unsupported_options(self):
        return ["xsymlog", "ysymlog"]

    def plot(self, *args, label="", marker="small", **kwargs):
        plt.plot(*args, label=label, marker=marker, **kwargs)

    def ylabel(self, ylabel):
        plt.ylabel(ylabel)

    def xlog(self):
        plt.xscale("log")

    def ylog(self):
        plt.yscale("log")

    def canvas_color(self):
        plt.canvas_color(self.args.canvas_color)

    def axes_color(self):
        plt.axes_color(self.args.axes_color)

    def ticks_color(self):
        plt.ticks_color(self.args.ticks_color)

    def grid(self):
        plt.grid(self.args.grid)

    def plotsize(self):
        plt.plotsize(self.args.plotsize[0], self.args.plotsize[1])

    def colorless(self):
        plt.colorless()

    def target_subplot(self, row, col):
        plt.subplot(row, col)

    def create_subplot(self, row, col):
        plt.subplots(row, col)

    def set_title(self, title):
        plt.title(title)

    def clear_current_figure(self):
        plt.clf()

    def clear_terminal_printed_lines(self):
        plt.clear_terminal_printed_lines()

    def show(self):
        plt.show()

    @property
    def fixed_color_seq(self):
        return plt_util.color_sequence

    @property
    def generator_color_seq(self):
        while True:
            for c in plt_util.color_sequence:
                yield c
