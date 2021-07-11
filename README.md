# tensorboard-termplot

A plotter for tensorboard, directly within your terminal. This is useful when you are training your neural network on a remote server, and you just want to quickly peek at the training curve without launching a tensorboard instance and mess with forwarding ports.

## Usage

```sh
$ tensorboard-termplot FOLDER
# e.g. tensorboard-termplot ~/my_amazing_nn/runs
# where `runs` is the folder that tensorboard had created
```
