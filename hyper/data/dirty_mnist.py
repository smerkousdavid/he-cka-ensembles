""" From https://github.com/omegafragger/DDU """

import torch
import numpy as np
import torch.utils.data as data
from torch.utils.data import Subset

from torch.utils.data.distributed import DistributedSampler
from hyper.data.fast_mnist import create_MNIST_dataset
from hyper.data.ambiguous_mnist import AmbiguousMNIST
from hyper.data.util import ddp_args


def get_train_valid_loader(batch_size, val_seed=1, val_size=0.1, ddp=False, **kwargs):
  error_msg = "[!] val_size should be in the range [0, 1]."
  assert (val_size >= 0) and (val_size <= 1), error_msg

  # load the dataset
  mnist_train_dataset, _ = create_MNIST_dataset()

  # AmbiguousMNIST does whiten the data itself
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  train_dataset = data.ConcatDataset(
    [mnist_train_dataset, AmbiguousMNIST(train=True, device=device),]
  )
  valid_dataset = data.ConcatDataset(
    [mnist_train_dataset, AmbiguousMNIST(train=True, device=device),]
  )

  num_train = len(train_dataset)
  indices = list(range(num_train))
  split = int(np.floor(val_size * num_train))

  np.random.seed(val_seed)
  np.random.shuffle(indices)

  train_idx, valid_idx = indices[split:], indices[:split]
  train_subset = Subset(train_dataset, train_idx)
  valid_subset = Subset(valid_dataset, valid_idx)

  train_loader = torch.utils.data.DataLoader(train_subset, batch_size=batch_size, num_workers=0, **ddp_args(train_subset, ddp=ddp, shuffle=True))

  valid_loader = torch.utils.data.DataLoader(valid_subset, batch_size=batch_size, num_workers=0, **ddp_args(train_subset, ddp=ddp, shuffle=False))

  return train_loader, valid_loader


def get_test_loader(batch_size, ddp=False, **kwargs):
  # load the dataset
  _, mnist_test_dataset = create_MNIST_dataset()

  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
  test_dataset = data.ConcatDataset(
      [mnist_test_dataset, AmbiguousMNIST(train=False, device=device),]
  )

  test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, num_workers=0, **ddp_args(test_dataset, ddp=ddp, shuffle=False))

  return test_loader