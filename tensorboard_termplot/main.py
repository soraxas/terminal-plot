import argparse
import os
import pathlib
from typing import List, Dict

import numpy as np
from tensorboard.backend.event_processing import event_accumulator

from tensorboard_termplot.backend.base_plotter import Plotter
from tensorboard_termplot.backend.matplotlib_plot import MatplotlibPlot
from tensorboard_termplot.backend.matplotlib_plot import MatplotlibPlotTerminal
from tensorboard_termplot.backend.terminal_plot import TerminalPlot


def pair_of_num(arg):
    arg = arg.split(",")
    if len(arg) != 2:
        raise ValueError("It must be in the format of a,b (e.g. 30.0,2.2)")
    return tuple(map(float, arg))


def pair_of_int(arg):
    return tuple(map(int, pair_of_num(arg)))


def pair_of_num_assign_pair_of_num(arg):
    arg = arg.split("=")
    if len(arg) != 2:
        raise ValueError("It must be in the format of a,b=c,d (e.g. 30.0,20=30.2,45)")
    return tuple(map(pair_of_num, arg))


def between_zero_and_one(arg):
    arg = float(arg)
    if not (0 <= arg <= 1):
        raise ValueError()
    return arg


parser = argparse.ArgumentParser()
parser.add_argument(
    "folder", metavar="FOLDER", type=str, help="Folder of a tensorboard runs"
)

# plotting generic flags
parser.add_argument(
    "--backend",
    default="plotext",
    help="Set the plotting backend",
    choices=["plotext", "matplotlib", "matplotlib-terminal"],
    type=str,
)
parser.add_argument(
    "-m",
    "--matplotlib",
    help="Alias of --backend matplotlib",
    action="store_true",
)
parser.add_argument(
    "--plotsize",
    help="Manually set the size of each subplot, e.g., 50,20.",
    metavar="WIDTH,HEIGHT",
    type=pair_of_int,
)
parser.add_argument(
    "-c", "--consolidate", action="store_true", help="Consolidate based on prefix."
)
parser.add_argument(
    "--as-scatter",
    help="Plot as scatter (instead of line plot)",
    action="store_true",
)

# canvas flags
parser.add_argument(
    "--canvas-color",
    type=str,
    help="set the color of the plot canvas " "(the area where the data is plotted)",
)
parser.add_argument(
    "--axes-color",
    type=str,
    help="sets the background color of all the labels surrounding the actual plot, "
    "i.e. the axes, axes labels and ticks, title and legend, if present",
)
parser.add_argument(
    "--ticks-color",
    type=str,
    help="sets the (full-ground) color of the axes ticks and of the grid lines.",
)
parser.add_argument("--grid", action="store_true", help="Show grid.")
parser.add_argument("--colorless", action="store_true", help="Remove color.")
parser.add_argument(
    "-d",
    "--dark-theme",
    action="store_true",
    help="A collection of flags. If set, it is equivalent to setting canvas-color and "
    "axes-color to black, and setting ticks-color to red. Can be overwritten "
    "individually.",
)
parser.add_argument(
    "--no-iter-color",
    action="store_true",
    help="Stop iterating through different colors per plot.",
)
parser.add_argument(
    "--force-label",
    action="store_true",
    help="Force showing label even for plot with one series.",
)

# auto-refresh related flag
parser.add_argument(
    "-f",
    "--follow",
    action="store_true",
    help="Run in a loop to update display periodic.",
)
parser.add_argument(
    "-n",
    "--interval",
    type=float,
    metavar="secs",
    default=5,
    help="seconds to wait between updates",
)

# filtering for stats name
parser.add_argument(
    "-w",
    "--whitelist",
    type=str,
    nargs="+",
    metavar="keyword",
    help="Keyword that the stat must contain for it to be plotted, case sensitive.",
)
parser.add_argument(
    "-b",
    "--blacklist",
    type=str,
    nargs="+",
    metavar="keyword",
    help="Keyword that the stat must not contain for it to be plotted, case sensitive.",
)

# axis flag
parser.add_argument(
    "-x",
    "--xaxis-type",
    default="step",
    help="Set value type to be used for x-axis",
    choices=["step", "walltime"],
    type=str,
)
parser.add_argument(
    "--xlog",
    help="Set the list of subplots to use log scale in x-axis",
    metavar="row,col",
    type=pair_of_int,
    nargs="*",
)
parser.add_argument(
    "--ylog",
    help="Set the list of subplots to use log scale in y-axis",
    metavar="row,col",
    type=pair_of_int,
    nargs="*",
)
parser.add_argument(
    "--xsymlog",
    help="Set the list of subplots to use symlog scale in x-axis",
    metavar="row,col",
    type=pair_of_int,
    nargs="*",
)
parser.add_argument(
    "--ysymlog",
    help="Set the list of subplots to use symlog scale in y-axis",
    metavar="row,col",
    type=pair_of_int,
    nargs="*",
)
parser.add_argument(
    "--xlim",
    help="Set the list of xlim for the specified subplot.",
    metavar="row,col=min,max",
    type=pair_of_num_assign_pair_of_num,
    nargs="+",
)
parser.add_argument(
    "--ylim",
    help="Set the list of ylim for the specified subplot.",
    metavar="row,col=min,max",
    type=pair_of_num_assign_pair_of_num,
    nargs="+",
)

# matplotlib backend specific
parser.add_argument(
    "--as-raw-bytes",
    action="store_true",
    help="Writes the raw image bytes to stdout.",
)
parser.add_argument(
    "-s",
    "--smooth",
    metavar="0-1",
    const=0.05,
    nargs="?",
    type=between_zero_and_one,
    help="A value from 0 to 1 as a smoothing factor.",
)
parser.add_argument(
    "--smooth-poly-order",
    metavar="poly-order",
    default=3,
    type=int,
    help="Polynomial order for the savgol smoothing algorithm.",
)

# plotext backend specific
parser.add_argument(
    "--terminal-width",
    type=int,
    help="Manually set the terminal width.",
)
parser.add_argument(
    "--terminal-height",
    type=int,
    help="Manually set the terminal height.",
)


class EmptyEventFileError(Exception):
    pass


def ensure_odd(x: int, roundup: bool):
    if x % 2 == 0:
        if roundup:
            return x + 1
        else:
            return x - 1
    return x


def apply_smoothing(y_vals, smoothing_factor: float, poly_order: int):
    from scipy.signal import savgol_filter

    # factor controls the window size, with factor 0 being the min and 1
    # being the max
    # window size must be odd, and greater than the polynomial order
    min_win_size = poly_order + 1
    max_win_size = len(y_vals)

    min_win_size = ensure_odd(min_win_size, roundup=True)
    max_win_size = ensure_odd(max_win_size, roundup=False)
    assert min_win_size < max_win_size

    # apply the user-supplied factor
    win_size = int(min_win_size + smoothing_factor * (max_win_size - min_win_size))

    win_size = ensure_odd(win_size, roundup=False)

    return savgol_filter(y_vals, win_size, poly_order)


def get_consolidated_stats_list(
    args: argparse.ArgumentParser, scalar_names: List[str]
) -> Dict[str, List[str]]:
    """Return a consolidated version of stats to be plotted. Consolidation is based
    on prefix.
    E.g., a list of [Loss/train, Loss/test, Score/train, Score/test]
    will returns a dictionary of
    {'Loss': [Loss/train, Loss/test], 'Score': [Score/train, Score/test]}

    :return: a dictionary that maps a prefix to a list of related stats
    """
    # combine related stats based on prefix
    consolidated_stats = {}
    if args.consolidate:
        # condense stats based on prefix
        for scalar_name in scalar_names:
            # e.g. Loss/train, Loss/test, etc.
            prefix = scalar_name.split("/")[0]
            stats = consolidated_stats.get(prefix, [])
            stats.append(scalar_name)
            consolidated_stats[prefix] = stats
    else:
        # construct dummy dict in consistent with the consolidation version
        consolidated_stats.update(
            {scalar_name: [scalar_name] for scalar_name in scalar_names}
        )
    return consolidated_stats


def _plot_for_one_run(plotter: Plotter, run_dict: Dict, col_num: int):
    title = f"'{run_dict['ea'].path}'"

    if plotter.args.follow:
        title += f" [refresh every {plotter.args.interval}s]"

    colors = plotter.get_colors()

    # find the earliest time across all stats
    wall_t_origin = float("inf")
    if plotter.args.xaxis_type == "walltime":
        for prefix, scalar_names in run_dict["consolidated_stats"].items():
            for scalar_name in scalar_names:
                series = np.array(run_dict["ea"].Scalars(scalar_name))
                wall_t, steps, vals = series.T
                wall_t_origin = min(wall_t_origin, wall_t[0])

    for i, (prefix, scalar_names) in enumerate(run_dict["consolidated_stats"].items()):
        cur_row, cur_col = i + 1, col_num + 1
        plotter.target_subplot(cur_row, cur_col)
        # setup the title for the current top subplot
        if i == 0:
            plotter.set_title(title)
        ###############################

        for scalar_name, color in zip(scalar_names, colors):
            series = np.array(run_dict["ea"].Scalars(scalar_name))
            wall_t, steps, vals = series.T
            if plotter.args.smooth:
                vals = apply_smoothing(
                    vals, plotter.args.smooth, plotter.args.smooth_poly_order
                )

            if plotter.args.xaxis_type == "step":
                x = steps
            elif plotter.args.xaxis_type == "walltime":
                x = wall_t - wall_t_origin
            else:
                raise NotImplementedError()
            # only label the line if we are consolidating stats. (because otherwise it
            # will always be the only line)
            _plot_func = plotter.scatter if plotter.args.as_scatter else plotter.plot
            _plot_func(
                x,
                vals,
                label=scalar_name
                if (plotter.args.consolidate or plotter.args.force_label)
                else None,
                color=color,
            )
            plotter.post_setup(
                xlabel=plotter.args.xaxis_type,
                ylabel=scalar_name,
                cur_row=cur_row,
                cur_col=cur_col,
            )


def filter_stats(scalar_names, args):
    if args.whitelist:
        filtered_scalar_names = filter(
            lambda name: any(keyword in name for keyword in args.whitelist),
            scalar_names,
        )
    else:
        filtered_scalar_names = list(scalar_names)
    if args.blacklist:
        filtered_scalar_names = filter(
            lambda name: not any(keyword in name for keyword in args.blacklist),
            filtered_scalar_names,
        )
    return list(filtered_scalar_names)


def main(args):
    if args.backend == "plotext":
        plotter = TerminalPlot(args)
    elif args.backend == "matplotlib":
        plotter = MatplotlibPlot(args)
    elif args.backend == "matplotlib-terminal":
        plotter = MatplotlibPlotTerminal(args)
    else:
        raise NotImplementedError()

    # ea = event_accumulator.EventAccumulator(args.folder)
    runs_to_plot = []
    if os.path.basename(args.folder).startswith("events.out."):
        # the given 'folder' is the actual event file
        runs_to_plot.append(
            dict(ea=event_accumulator.EventAccumulator(args.folder), folder=args.folder)
        )
    elif next(pathlib.Path(args.folder).glob("events.out.*"), None) is not None:
        # the given folder is the actual event folder
        runs_to_plot.append(
            dict(ea=event_accumulator.EventAccumulator(args.folder), folder=args.folder)
        )
    else:
        # the given folder nest multiple event folders
        for folder in pathlib.Path(args.folder).iterdir():
            # ensure they are event folder
            if next(folder.glob("events.out.*"), None) is not None:
                runs_to_plot.append(
                    dict(
                        ea=event_accumulator.EventAccumulator(str(folder)),
                        folder=str(folder),
                    )
                )
    if len(runs_to_plot) == 0:
        raise ValueError(
            f"Unable to find tensorboard event files within '{args.folder}'."
        )

    while True:
        plotter.clear_current_figure()

        # First loop through and find the maximum number of subplots across all folder
        # first, in case some folders have more subplots than others, will take the max
        max_plots = 1
        for run_dict in runs_to_plot:
            run_dict["ea"].Reload()
            scalar_names = run_dict["ea"].Tags()["scalars"]
            if len(scalar_names) == 0:
                raise EmptyEventFileError(
                    f"Cannot find any scalars within the folder '{run_dict['folder']}'."
                    f" Is the folder correct? The ea tags are {run_dict['ea'].Tags()}"
                )
            # filter tags
            scalar_names = filter_stats(scalar_names, args)
            # merge the stats together with the same prefix (if necessary)
            run_dict["consolidated_stats"] = get_consolidated_stats_list(
                args, scalar_names=scalar_names
            )
            max_plots = max(max_plots, len(run_dict["consolidated_stats"]))

        # create the master plot of all folders
        plotter.create_subplot(max_plots, len(runs_to_plot))

        # do the actual plotting
        for i, run_dict in enumerate(runs_to_plot):
            # plot the column of subplots for this folder
            _plot_for_one_run(plotter, run_dict, i)

        plotter.clear_terminal_printed_lines()
        if args.as_raw_bytes:
            plotter.as_image_raw_bytes()
        else:
            plotter.show()
        if not args.follow:
            break
        plotter.sleep()


def run():
    try:
        _args = parser.parse_args()
        # handles alias of options
        if _args.dark_theme:
            # only set values when unset, such that they can be overridden
            if _args.canvas_color is None:
                _args.canvas_color = "black"
            if _args.axes_color is None:
                _args.axes_color = "black"
            if _args.ticks_color is None:
                _args.ticks_color = "white"
        if _args.matplotlib:
            _args.backend = "matplotlib"
        main(_args)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
