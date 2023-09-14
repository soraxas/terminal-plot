import io
import os
import sys
from functools import lru_cache
from shutil import which
from subprocess import Popen, PIPE, STDOUT

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import logging

LOGGER = logging.getLogger(__file__)

from .base_plotter import Plotter, PlottingError


# noinspection SpellCheckingInspection,PyAttributeOutsideInit
class MatplotlibPlot(Plotter):
    @property
    def unsupported_options(self):
        return []

    def plot(self, *args, label="", **kwargs):
        self.cur_ax.plot(*args, label=label, **kwargs)

    def scatter(self, *args, label="", **kwargs):
        self.cur_ax.scatter(*args, label=label, **kwargs)

    def xlim(self, row, col, limits):
        self.cur_ax.set_xlim(limits)

    def ylim(self, row, col, limits):
        self.cur_ax.set_ylim(limits)

    def xlog(self):
        self.cur_ax.set_xscale("log")

    def ylog(self):
        self.cur_ax.set_yscale("log")

    def xsymlog(self):
        self.cur_ax.set_xscale("symlog")

    def ysymlog(self):
        self.cur_ax.set_yscale("symlog")

    def legend(self):
        self.cur_ax.legend()

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
        try:
            if self.n_row == 1 and self.n_col == 1:
                self.cur_ax = self.axs
            elif self.n_row == 1:
                self.cur_ax = self.axs[col - 1]
            elif self.n_col == 1:
                self.cur_ax = self.axs[row - 1]
            else:
                self.cur_ax = self.axs[row - 1][col - 1]
        except IndexError as e:
            raise PlottingError from e

    def create_subplot(self, row, col):
        super().create_subplot(row, col)
        try:
            self.fig, self.axs = plt.subplots(row, col, figsize=self.args.plotsize)
        except (ValueError, IndexError) as e:
            LOGGER.warn(e)
            raise PlottingError from e

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
        # if self.args.timg:
        #     size = os.get_terminal_size()
        #     my_env = os.environ.copy()
        #     popen_args = ["timg", "-", f"-g{size.columns}x{size.lines}"]
        #     if my_env["TERM"] == "xterm-kitty":
        #         popen_args += ["-pkitty"]
        #     p = Popen(popen_args, stdout=PIPE, stdin=PIPE, stderr=STDOUT, env=my_env)
        #     grep_stdout = p.communicate(input=self._get_image_raw_bytes())[0]
        #     sys.stdout.write(grep_stdout.decode())
        # else:
        sys.stdout.buffer.write(self._get_image_raw_bytes())

    @property
    def fixed_color_seq(self):
        return mcolors.TABLEAU_COLORS

    @property
    def generator_color_seq(self):
        while True:
            yield from mcolors.TABLEAU_COLORS

    def close(self):
        plt.close(self.fig)


class MatplotlibPlotTerminal(MatplotlibPlot):
    def __init__(self, args):
        super().__init__(args)
        self.backend_program_cmds = self.get_supported_backend()
        if self.backend_program_cmds is None:
            raise RuntimeError("No supported program found (e.g. timg, .")

    @classmethod
    @lru_cache()
    def get_supported_backend(cls):
        """Determine if the system has necessary binary to support this plotter."""
        if which("timg"):
            return ["timg", "-"]
        elif which("kitty"):
            return ["kitty", "+kitten", "icat"]

    def show(self):
        program = Popen(
            self.backend_program_cmds,
            stdin=PIPE,
            bufsize=-1,
        )
        # pipe image data to program
        self.fig.savefig(program.stdin)

        program.stdin.close()  # done (no more input)
