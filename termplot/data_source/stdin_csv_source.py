import io
from argparse import ArgumentParser

from termplot.data_source import DataSource
from termplot.data_source.csv_source import CsvFigureData


class StdinCsvDataSource(DataSource):
    def __init__(self, string_buffer: str, args: ArgumentParser):
        super().__init__(None, args)
        self.figures = []

        f = io.StringIO(string_buffer)
        self.figures.append(CsvFigureData(f))

        if len(self.figures) == 0:
            raise ValueError(f"Unable to find csv files within '{self.input}'.")

    def __len__(self):
        return 1

    def __getitem__(self, item):
        figure_data = self.figures[item]
        figure_data.refresh()
        return figure_data
