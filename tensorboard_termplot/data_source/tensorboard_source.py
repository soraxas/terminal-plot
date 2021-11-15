import os
from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path

import numpy as np
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

from tensorboard_termplot.data_source import DataSource, FigureData
from tensorboard_termplot.main import EmptyEventFileError


class TensorboardDataSource(DataSource):
    def __init__(self, args: ArgumentParser):
        super().__init__(args)
        folder = Path(self.args.folder)
        figures = []

        def _add_figure(_folder):
            _folder = str(_folder)
            figures.append(
                TensorboardFigureData(
                    ea=EventAccumulator(_folder),
                    folder=_folder,
                    consolidated_stats=self.args.consolidate,
                )
            )

        if os.path.basename(folder).startswith("events.out."):
            # the given 'folder' is the actual event file
            _add_figure(folder)
        elif next(folder.glob("events.out.*"), None) is not None:
            # the given folder is the actual event folder
            _add_figure(folder)
        else:
            # the given folder nest multiple event folders
            for folder in folder.iterdir():
                # ensure they are event folder
                if next(folder.glob("events.out.*"), None) is not None:
                    _add_figure(folder)

        if len(figures) == 0:
            raise ValueError(
                f"Unable to find tensorboard event files within '{folder}'."
            )

        self.figures = figures

    def __len__(self):
        return len(self.figures)

    def __getitem__(self, item):
        figure_data = self.figures[item]
        figure_data.refresh()
        return figure_data


class TensorboardFigureData(FigureData):
    def __init__(
        self, ea: EventAccumulator, folder: str, consolidated_stats: bool = False
    ):
        self.ea = ea
        self.folder = folder
        self.consolidated_stats = consolidated_stats
        self.refresh()
        if len(self.scalar_names) == 0:
            raise EmptyEventFileError(
                f"Cannot find any scalars within the folder '{self.folder}'."
                f" Is the folder correct? The ea tags are {self.ea.Tags()}"
            )

    def refresh(self):
        self.ea.Reload()

    # def get_series(self, *, x, y, scalar_name: str):
    def get_series(self, *, x: str, y: str):
        if x not in ("step", "walltime"):
            raise ValueError("Tensorboard only support 'step' or 'walltime' as x-axis")
        series = np.array(self.ea.Scalars(y))
        wall_t, steps, vals = series.T
        if x == "step":
            x_values = steps
        else:
            assert x == "walltime"
            x_values = wall_t - self._get_time_origin()
        return x_values, vals

    @property
    def title(self):
        return self.ea.path

    @property
    def scalar_names(self):
        return self.ea.Tags()["scalars"]

    @lru_cache()
    def _get_time_origin(self) -> float:
        """
        Helper function that get the origin of time via checking through all stats.
        :return: time origin
        """
        # find the earliest time across all stats
        wall_t_origin = float("inf")

        for scalar_name in self.scalar_names:
            series = np.array(self.ea.Scalars(scalar_name))
            wall_t, steps, vals = series.T
            wall_t_origin = min(wall_t_origin, wall_t[0])

        return wall_t_origin
