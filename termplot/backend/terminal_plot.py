from argparse import ArgumentParser
import os
import pandas as pd
import numpy as np
import plotext
import plotext as plt
import plotext._utility as plt_util

from .base_plotter import Plotter


# noinspection SpellCheckingInspection
class TerminalPlot(Plotter):

    def __init__(self, args: ArgumentParser):
        super().__init__(args)
        self._fixed_color_seq = [
            "blue",
            "red",
            "magenta",
            "green",
            "orange",
            "cyan",
            "black",
            "white",
            "gray",
        ]
        # do not use the color sequence that's same as the canvas
        canvas_color = "white"
        if self.args.canvas_color is not None:
            canvas_color = self.args.canvas_color
        try:
            self._fixed_color_seq.pop(self._fixed_color_seq.index(canvas_color))
        except ValueError:
            pass

    @property
    def unsupported_options(self):
        return ["xsymlog", "ysymlog"]

    def _args_transformer(self, args):
        for arg in args:
            if isinstance(arg, pd.Series):
                if pd.core.dtypes.common.is_datetime_or_timedelta_dtype(arg):
                    arg = plotext.datetimes_to_string(arg)

            # if isinstance(arg, (pd.Series, np.ndarray)):
            #     arg = list(arg)

            yield arg

    def plot(self, *args, label="", **kwargs):
        plt.plot(*self._args_transformer(args), label=label, marker="fhd", **kwargs)

    def scatter(self, *args, label="", **kwargs):
        plt.scatter(*self._args_transformer(args), label=label, **kwargs)

    def xlabel(self, xlabel, **kwargs):
        plt.xlabel(xlabel)

    def ylabel(self, ylabel, **kwargs):
        plt.ylabel(ylabel)

    def xlim(self, row, col, limits):
        plt.xlim(*limits)

    def ylim(self, row, col, limits):
        plt.ylim(*limits)

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
        plt.main().subplot(row, col)

    def create_subplot(self, row, col):
        super().create_subplot(row, col)
        plt.main().subplots(row, col)

    def set_title(self, title):
        plt.title(title)

    def clear_current_figure(self):
        plt.clf()

    def clear_terminal_printed_lines(self):
        # plt.clear_terminal()
        os.system("cls" if os.name == "nt" else "clear")

    def show(self):
        if self.args.terminal_width and self.args.terminal_height:
            import mock

            with mock.patch("shutil.get_terminal_size") as MockClass:
                MockClass.return_value = (
                    self.args.terminal_width,
                    self.args.terminal_height,
                )
                plt.show()
        else:
            plt.show()

    @property
    def fixed_color_seq(self):
        return self._fixed_color_seq
