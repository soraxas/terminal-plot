import os
from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import pandas as pd

from termplot.data_source import DataSource, FigureData
from termplot.etc import EmptyEventFileError


class CsvDataSource(DataSource):
    def __init__(self, folder: str, args: ArgumentParser):
        super().__init__(folder, args)
        path = Path(self.folder)
        self.figures = []

        if os.path.isfile(path) and os.path.basename(path).endswith(".csv"):
            # the given 'folder' is the actual csv file
            self.figures.append(CsvFigureData(path))
        elif os.path.isdir(path):
            # the given 'folder' is a folder
            for csv_file in path.glob("*.csv"):
                self.figures.append(CsvFigureData(csv_file))

        if len(self.figures) == 0:
            raise ValueError(f"Unable to find csv files within '{path}'.")

    def __len__(self):
        return len(self.figures)

    def __getitem__(self, item):
        figure_data = self.figures[item]
        figure_data.refresh()
        return figure_data


class CsvFigureData(FigureData):
    def __init__(self, path: str):
        self.path = path
        self.df = pd.read_csv(path)
        self.refresh()
        if len(self.scalar_names) == 0:
            raise EmptyEventFileError(
                f"Cannot find any scalars within the csv file '{self.path}'"
            )

    def refresh(self):
        pass

    # def get_series(self, *, x, y, scalar_name: str):
    def get_series(self, *, x: str, y: str):
        y_values = self.df[y]
        if x == "step":
            x_values = np.arange(len(y_values))
        else:
            x_values = self.df[x]
        return x_values, y_values

    @property
    def title(self):
        return self.path

    @property
    def scalar_names(self):
        return list(self.df.columns)

    def __repr__(self):
        return f"{self.__class__.__name__}<path={self.path}|df={self.df}>"
