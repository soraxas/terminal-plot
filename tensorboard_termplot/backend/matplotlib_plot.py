import io
import os
import sys
from subprocess import Popen, PIPE, STDOUT

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

from .base_plotter import Plotter


class MatplotlibPlot(Plotter):
    @property
    def unsupported_options(self):
        return []
        return ["follow"]

    def plot(self, *args, label="", **kwargs):
        self.cur_ax.plot(*args, label=label, **kwargs)

    def xlog(self):
        self.cur_ax.set_xscale("log")

    def ylog(self):
        self.cur_ax.set_yscale("log")

    def xsymlog(self):
        self.cur_ax.set_xscale("symlog")

    def ysymlog(self):
        self.cur_ax.set_yscale("symlog")

    def xlabel(self, xlabel, **kwargs):
        # only add xlabel to the bottom subplot
        if self.match_subplot(
            [(self.n_row, i) for i in range(1, self.n_col + 1)],
            kwargs["cur_row"],
            kwargs["cur_col"],
        ):
            self.cur_ax.set_xlabel(xlabel)

    def ylabel(self, ylabel, **kwargs):
        self.cur_ax.set_ylabel(ylabel)

    def canvas_color(self):
        self.fig.set_facecolor(self.args.canvas_color)

    def axes_color(self):
        self.cur_ax.set_facecolor(self.args.axes_color)

    def ticks_color(self):
        self.cur_ax.tick_params(colors=self.args.ticks_color)
        self.cur_ax.xaxis.label.set_color(self.args.ticks_color)
        self.cur_ax.yaxis.label.set_color(self.args.ticks_color)
        for spine in self.cur_ax.spines.values():
            spine.set_edgecolor(self.args.ticks_color)

    def plotsize(self):
        pass

    def target_subplot(self, row, col):
        if self.n_row == 1:
            self.cur_ax = self.axs[col - 1]
        elif self.n_col == 1:
            self.cur_ax = self.axs[row - 1]
        else:
            self.cur_ax = self.axs[row - 1][col - 1]

    # self.args.plotsize[0], self.args.plotsize[1]
    def create_subplot(self, row, col):
        super().create_subplot(row, col)
        self.fig, self.axs = plt.subplots(row, col, figsize=self.args.plotsize)

    def set_title(self, title):
        kwargs = {}
        if self.args.ticks_color is not None:
            kwargs["color"] = self.args.ticks_color
        self.cur_ax.set_title(title, fontsize=10, **kwargs)

    def clear_current_figure(self):
        pass
        # self.cur_ax.clf()

    def clear_terminal_printed_lines(self):
        pass
        # self.fig.clear()

    def show(self):
        self.fig.tight_layout()
        plt.show()

    def _get_image_raw_bytes(self):
        self.fig.tight_layout()
        string_io_bytes = io.BytesIO()
        plt.savefig(string_io_bytes, format="png")
        string_io_bytes.seek(0)
        return string_io_bytes.read()

    def as_image_raw_bytes(self):
        if self.args.timg:
            size = os.get_terminal_size()
            my_env = os.environ.copy()
            popen_args = ["timg", "-", f"-g{size.columns}x{size.lines}"]
            if my_env["TERM"] == "xterm-kitty":
                popen_args += ["-pkitty"]
            p = Popen(popen_args, stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=my_env)
            grep_stdout = p.communicate(input=self._get_image_raw_bytes())[0]
            sys.stdout.write(grep_stdout.decode())
        else:
            sys.stdout.buffer.write(self._get_image_raw_bytes())

    @property
    def fixed_color_seq(self):
        return mcolors.TABLEAU_COLORS

    @property
    def generator_color_seq(self):
        while True:
            yield from mcolors.TABLEAU_COLORS
