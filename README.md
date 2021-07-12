# Terminal-plot for Tensorboard

[![pypi](https://img.shields.io/pypi/v/tensorboard-termplot)](https://pypi.org/project/tensorboard-termplot/)
[![python-version](https://img.shields.io/pypi/pyversions/tensorboard-termplot)](https://pypi.org/project/tensorboard-termplot/)
[![Master Update](https://img.shields.io/github/last-commit/soraxas/tensorboard-termplot/master.svg)](https://github.com/soraxas/tensorboard-termplot/commits/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/github/license/soraxas/sbp-env.svg)](https://github.com/soraxas/tensorboard-termplot/blob/master/LICENSE)

A plotter for tensorboard, directly within your terminal. This is useful when you are training your neural network on a remote server, and you just want to quickly peek at the training curve without launching a tensorboard instance and mess with forwarding ports.

## Install

You can install the package published in PyPI with
```sh
$ pip install tensorboard-termplot
# or install with an isolated environment
# $ pipx install tensorboard-termplot
```

## Usage

```sh
$ tensorboard-termplot FOLDER
```
For example,
```sh
$ tensorboard-termplot ~/my_amazing_nn/runs
```
where `runs` is the folder that tensorboard had created.
