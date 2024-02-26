from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import abc
import numpy as np

class SamplingMethod(object):
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def __init__(self, X, **kwargs):
    self.X = X

  def flatten_X(self):
    shape = self.X.shape
    flat_X = self.X
    if len(shape) > 2:
      flat_X = np.reshape(self.X, (shape[0],np.product(shape[1:])))
    return flat_X


  @abc.abstractmethod
  def select_batch_(self):
    return

  def select_batch(self, **kwargs):
    return self.select_batch_(**kwargs)

  def to_dict(self):
    return None