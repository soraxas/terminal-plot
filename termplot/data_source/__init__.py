from abc import ABC, abstractmethod
from argparse import ArgumentParser
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import numpy as np


class DataSourceMissingException(Exception, ABC):
    pass


class DataSourceProcessingException(Exception, ABC):
    pass


def guess_prefix(token: str, determiner_list: Tuple[str] = ("/", "_")):
    for determiner in determiner_list:
        prefix = token.split(determiner)
        if len(prefix) > 1:
            return prefix[0]
    return token


class DataSource(ABC):
    def __init__(self, input_file: Optional[Path], args: ArgumentParser):
        self.args = args
        if input_file is not None:
            self.input = Path(input_file)
            if not self.input.exists():
                raise RuntimeError(
                    f"The given input file '{self.input}' does not exists"
                )

    def get_all_scalar_names(self):
        all_scalar_names = []
        for figure_data in self:
            # filter tags
            all_scalar_names.extend(
                figure_data.get_filtered_scalar_names(
                    whitelist=self.args.whitelist, blacklist=self.args.blacklist
                )
            )
        return all_scalar_names

    def get_consolidated_stats(self) -> Dict[str, List[str]]:
        """Return a consolidated version of stats to be plotted. Consolidation is based
        on prefix.
        E.g., a list of [Loss/train, Loss/test, Score/train, Score/test]
        will returns a dictionary of
        {'Loss': [Loss/train, Loss/test], 'Score': [Score/train, Score/test]}

        :return: a dictionary that maps a prefix to a list of related stats
        """
        all_scalar_names = self.get_all_scalar_names()
        # filter out if this stat is used as the x-axis
        all_scalar_names = list(
            filter(lambda x: x != self.args.xaxis_type, all_scalar_names)
        )
        if not self.args.consolidate:
            # construct dummy dict in consistent with the consolidation version
            return {scalar_name: [scalar_name] for scalar_name in all_scalar_names}

        consolidated_stats = dict()
        # combine related stats based on prefix
        if self.args.consolidate == 1:
            for scalar_name in all_scalar_names:
                # e.g. Loss/train, Loss/test, etc.
                prefix = guess_prefix(scalar_name)
                stats = consolidated_stats.get(prefix, [])
                stats.append(scalar_name)
                consolidated_stats[prefix] = stats
        elif self.args.consolidate >= 2:
            # combine everything
            consolidated_stats[""] = []
            for scalar_name in all_scalar_names:
                consolidated_stats[""].append(scalar_name)
        # sort so that results are consistent and look uniform.
        return {
            prefix: sorted(mapped_stat)
            for prefix, mapped_stat in consolidated_stats.items()
        }

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def __getitem__(self, item) -> "FigureData":
        pass


class FigureData(ABC):
    title: str
    scalar_names: str

    @abstractmethod
    def get_series(self, *, x: str, y: str) -> np.ndarray:
        pass

    @property
    def title(self):
        raise NotImplementedError()

    @property
    def scalar_names(self):
        raise NotImplementedError()

    @abstractmethod
    def refresh(self):
        pass

    def get_filtered_scalar_names(self, whitelist: List[str], blacklist: List[str]):
        """Filter out scalar_names based on white and black list"""
        filtered_scalar_names = self.scalar_names
        if whitelist:
            filtered_scalar_names = filter(
                lambda name: any(keyword in name for keyword in whitelist),
                filtered_scalar_names,
            )
        if blacklist:
            filtered_scalar_names = filter(
                lambda name: not any(keyword in name for keyword in blacklist),
                filtered_scalar_names,
            )
        return list(filtered_scalar_names)
