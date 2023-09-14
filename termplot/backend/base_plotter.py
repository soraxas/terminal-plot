import argparse
import inspect
import time
from abc import ABCMeta, abstractmethod


class UnsupportedOption(NotImplementedError):
    pass


class PlottingError(Exception):
    pass


# noinspection SpellCheckingInspection
class Plotter(metaclass=ABCMeta):
    def __init__(self, args: argparse.ArgumentParser):
        self.args = args
        self.n_row = None
        self.n_col = None
        for opt in self.unsupported_options:
            if opt in args and getattr(args, opt) not in [None, False]:
                self.raise_not_supported_option(f"--{opt}")

    @property
    @abstractmethod
    def unsupported_options(self):
        pass

    @abstractmethod
    def plot(self, label, *args, **kwargs):
        pass

    @abstractmethod
    def scatter(self, label, *args, **kwargs):
        pass

    @staticmethod
    def match_subplot(subplots_to_apply, cur_row, cur_col):
        # empty list denotes wildcard
        if subplots_to_apply is not None:
            if len(subplots_to_apply) == 0 or (cur_row, cur_col) in subplots_to_apply:
                return True
        return False

    def post_setup(self, xlabel, ylabel, cur_row, cur_col):
        self.xlabel(xlabel, cur_row=cur_row, cur_col=cur_col)
        self.ylabel(ylabel, cur_row=cur_row, cur_col=cur_col)
        if self.args.canvas_color:
            self.canvas_color()
        if self.args.axes_color:
            self.axes_color()
        if self.args.ticks_color:
            self.ticks_color()
        if self.args.grid:
            self.grid()
        if self.args.plotsize:
            self.plotsize()
        if self.args.colorless:
            self.colorless()
        if self.args.consolidate:
            self.legend()
        if self.match_subplot(self.args.xlog, cur_row, cur_col):
            self.xlog()
        if self.match_subplot(self.args.ylog, cur_row, cur_col):
            self.ylog()
        if self.match_subplot(self.args.xsymlog, cur_row, cur_col):
            self.xsymlog()
        if self.match_subplot(self.args.ysymlog, cur_row, cur_col):
            self.ysymlog()
        for _lim_arg, _lim_func in [
            (self.args.xlim, self.xlim),
            (self.args.ylim, self.ylim),
        ]:
            if _lim_arg is not None:
                for _target_idx, _target_limit in _lim_arg:
                    if (_target_idx is None) or (_target_idx == (cur_row, cur_col)):
                        # None is wildcard, always applies
                        _lim_func(cur_row, cur_col, _target_limit)
                        break

    def legend(self):
        pass

    @abstractmethod
    def xlim(self, row, col, limits):
        pass

    @abstractmethod
    def ylim(self, row, col, limits):
        pass

    @abstractmethod
    def xlabel(self, xlabel, **kwargs):
        pass

    @abstractmethod
    def ylabel(self, ylabel, **kwargs):
        pass

    def xsymlog(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def ysymlog(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def xlog(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def ylog(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def as_image_raw_bytes(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def canvas_color(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def axes_color(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def ticks_color(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def grid(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def plotsize(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    def colorless(self):
        raise UnsupportedOption(inspect.currentframe().f_code.co_name)

    @abstractmethod
    def target_subplot(self, row, col):
        pass

    @abstractmethod
    def create_subplot(self, row, col):
        self.n_row = row
        self.n_col = col

    @abstractmethod
    def set_title(self, title):
        pass

    @abstractmethod
    def clear_current_figure(self):
        pass

    @abstractmethod
    def clear_terminal_printed_lines(self):
        pass

    @abstractmethod
    def show(self):
        pass

    @property
    @abstractmethod
    def fixed_color_seq(self):
        pass

    @property
    @abstractmethod
    def generator_color_seq(self):
        pass

    def close(self):
        pass

    def get_colors(self):
        if self.args.no_iter_color:
            return self.fixed_color_seq
        else:
            return self.generator_color_seq

    def sleep(self):
        time.sleep(self.args.interval)

    def raise_not_supported_option(self, option_str):
        print(
            f"ERROR: Plotter backend '{self.__class__.__name__}' does not "
            f"support option '{option_str}'"
        )
        exit(1)
