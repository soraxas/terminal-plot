from argparse import ArgumentParser
from functools import lru_cache
from pathlib import Path

import numpy as np
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

from termplot.data_source import (
    DataSource,
    FigureData,
    DataSourceProcessingException,
    DataSourceMissingException,
)


class TensorboardDataSourceMissingException(DataSourceMissingException):
    pass


class TensorboardDataSourceProcessingException(DataSourceProcessingException):
    pass


class TensorboardDataSource(DataSource):
    def __init__(self, input_file: Path, args: ArgumentParser):
        super().__init__(input_file, args)
        self.figures = []

        def _add_figure(_folder):
            _folder = str(_folder)
            self.figures.append(
                TensorboardFigureData(
                    ea=EventAccumulator(_folder),
                    folder=_folder,
                )
            )

        if self.input.is_file():
            if self.input.name.startswith("events.out."):
                # the given 'folder' is the actual event file
                _add_figure(self.input)
        else:  # is a folder
            if next(self.input.glob("events.out.*"), None) is not None:
                # the given folder is the actual event folder
                _add_figure(self.input)
            else:
                # the given folder nest multiple event folders
                for folder in self.input.iterdir():
                    # ensure they are event folder
                    if next(folder.glob("events.out.*"), None) is not None:
                        _add_figure(folder)

        if len(self.figures) == 0:
            raise TensorboardDataSourceMissingException(
                f"Unable to find tensorboard event files within '{self.input}'."
            )

    def __len__(self):
        return len(self.figures)

    def __getitem__(self, item):
        figure_data = self.figures[item]
        figure_data.refresh()
        return figure_data


class TensorboardFigureData(FigureData):
    def __init__(self, ea: EventAccumulator, folder: str):
        self.ea = ea
        self.folder = folder
        self.refresh()
        if len(self.scalar_names) == 0:
            raise TensorboardDataSourceProcessingException(
                f"Cannot find any scalars within the folder '{self.folder}'."
                f" Is the folder correct? The ea tags are {self.ea.Tags()}"
            )

    def refresh(self):
        self.ea.Reload()

    def get_series(self, *, x: str, y: str):
        if x not in ("step", "time"):
            raise ValueError("Tensorboard only support 'step' or 'time' as x-axis")
        series = np.array(self.ea.Scalars(y))
        # fixes when the pervious output results in an array of object.
        if series.dtype == np.dtype("object"):
            series = np.array([[o.wall_time, o.step, o.value] for o in series])
        wall_t, steps, vals = series.T
        if x == "step":
            x_values = steps
        else:
            assert x == "time"
            x_values = wall_t - self._get_time_origin()
        return x_values, vals

    @property
    def title(self) -> str:
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
            # series = np.array(self.ea.Scalars(scalar_name))
            # wall_t, steps, vals = series.T
            first_item = self.ea.Scalars(scalar_name)[0]
            wall_t_origin = min(wall_t_origin, first_item.wall_time)

        return wall_t_origin

    def __repr__(self):
        return f"{self.__class__.__name__}<folder={self.folder}|ea={self.ea}>"
