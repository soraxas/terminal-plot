import argparse
import pathlib
from typing import List, Dict

import numpy as np
import plotext as plt
import plotext.utility as plt_util
from tensorboard.backend.event_processing import event_accumulator


def pair_of_int(arg):
    arg = arg.split(",")
    if len(arg) != 2:
        raise ValueError("It must be in the format of a,b (e.g. 300,20)")
    return tuple(map(int, arg))


parser = argparse.ArgumentParser()
parser.add_argument(
    "folder", metavar="FOLDER", type=str, help="Folder of a tensorboard runs"
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
parser.add_argument("--colorless", action="store_true", help="Remove color.")
parser.add_argument(
    "-d",
    "--dark-theme",
    action="store_true",
    help="A collection of flags. If set, it is equivalent to setting canvas-color and "
    "axes-color to black, and setting ticks-color to red. Can be overwritten "
    "individually.",
)
# flags
parser.add_argument("--grid", action="store_true", help="Show grid.")
parser.add_argument(
    "--plotsize",
    help="Manually set the size of each subplot, e.g., 50,20.",
    metavar="WIDTH,HEIGHT",
    type=pair_of_int,
)
parser.add_argument(
    "--force-label",
    action="store_true",
    help="Force showing label even for plot with one series.",
)
parser.add_argument(
    "--no-iter-color",
    action="store_true",
    help="Stop iterating through different colors per plot.",
)
parser.add_argument(
    "-c", "--consolidate", action="store_true", help="Consolidate based on prefix."
)
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


class EmptyEventFileError(Exception):
    pass


def _plot_post_setup(args: argparse.ArgumentParser, ylabel: str, **kwargs):
    plt.ylabel(ylabel)
    if args.canvas_color:
        plt.canvas_color(args.canvas_color)
    if args.axes_color:
        plt.axes_color(args.axes_color)
    if args.ticks_color:
        plt.ticks_color(args.ticks_color)
    plt.grid(args.grid)
    if args.plotsize:
        plt.plotsize(args.plotsize[0], args.plotsize[1])
    if args.colorless:
        plt.colorless()


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


def _plot_for_one_run(args: argparse.ArgumentParser, run_dict: Dict, col_num: int):
    title = f"Stats of '{run_dict['ea'].path}'"

    if args.follow:
        title += " [refreshing every {args.interval} secs]"

    if args.no_iter_color:
        colors = plt_util.color_sequence
    else:

        def color_generator():
            while True:
                for c in plt_util.color_sequence:
                    yield c

        colors = color_generator()

    for i, (prefix, scalar_names) in enumerate(run_dict["consolidated_stats"].items()):
        plt.subplot(i + 1, col_num)
        # setup the title for the current top subplot
        if i == 0:
            plt.title(title)
        ###############################

        for scalar_name, color in zip(scalar_names, colors):
            series = np.array(run_dict["ea"].Scalars(scalar_name))
            wall_t, steps, vals = series.T
            # only label the line if we are consolidating stats. (because otherwise it
            # will always be the only line)
            plt.plot(
                steps,
                vals,
                label=scalar_name if (args.consolidate or args.force_label) else None,
                color=color,
                marker="small",
            )
            _plot_post_setup(args=args, ylabel=scalar_name)


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
    def clear_lines(n):
        import sys

        for i in range(n):
            sys.stdout.write("\033[2K")
            if i < n - 1:
                sys.stdout.write("\033[A")
                sys.stdout.write("\033[2K")
        # sys.stdout.write("\r")

    # ea = event_accumulator.EventAccumulator(args.folder)
    runs_to_plot = []
    if next(pathlib.Path(args.folder).glob("events.out.*"), None) is not None:
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
        plt.clf()

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
        plt.subplots(max_plots, len(runs_to_plot))

        # do the actual plotting
        for i, run_dict in enumerate(runs_to_plot):
            # plot the column of subplots for this folder
            _plot_for_one_run(args, run_dict, i)

        plt.show()
        if not args.follow:
            break
        plt.sleep(args.interval)


def run():
    try:
        _args = parser.parse_args()
        if _args.dark_theme:
            if _args.canvas_color is None:
                _args.canvas_color = "black"
            if _args.axes_color is None:
                _args.axes_color = "black"
            if _args.ticks_color is None:
                _args.ticks_color = "white"
        main(_args)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
