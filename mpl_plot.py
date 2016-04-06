# MPL Boilerplate
import matplotlib
import json
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.cm as cm
import matplotlib.patches
import matplotlib as mpl
def rgb(r,g,b):
    return (float(r)/256.,float(g)/256.,float(b)/256.)
# Plot colors:
#   visually distinct under colorblindness and grayscale
crimson = rgb(172,63,64)
blue    = rgb(62,145,189)
teal    = rgb(98,189,153)
orange  = rgb(250,174,83)
#   luminance channel sweeps from dark to light, (for ordered comparisons)
clr = [crimson, blue, teal, orange]
mrk = ['o','D','^','s']
rcParams['figure.figsize'] = (8,6) # (w,h)
rcParams['figure.dpi'] = 150
# !$%ing matplotlib broke the interface. Why would you *replace* this!? >:(
try:
  from cycler import cycler
  rcParams['axes.prop_cycle'] = cycler('color',clr)
except ImportError:
  rcParams['axes.color_cycle'] = clr
rcParams['lines.linewidth'] = 2
rcParams['lines.marker'] = None
rcParams['lines.markeredgewidth'] = 0
rcParams['axes.facecolor'] = 'white'
rcParams['font.size'] = 22
rcParams['patch.edgecolor'] = 'black'
rcParams['patch.facecolor'] = clr[0]
rcParams['xtick.major.pad'] = 8
rcParams['xtick.minor.pad'] = 8
rcParams['ytick.major.pad'] = 8
rcParams['ytick.minor.pad'] = 8
#rcParams['font.family'] = 'Helvetica'
#rcParams['font.family'] = 'Liberation Sans'
rcParams['font.weight'] = 100


class MemoPlot(object):
  '''Abstract base class for a reproducible, persistable, and memoizing plotter.'''
  def __init__(self, mpl_params={}):
    # three JSON objects
    self.data = {} # data, generated by generate
    self.mpl_params = mpl_params # plotting kwargs
    self.config = {} # settings used for plotting

  def generate(self):
    '''Override this function to collect data for a plot.'''
    pass

  def plot(self, ax):
    '''Override this function to reproduce the plot from saved data.'''
    ax.plot(self.data, **self.mpl_params)

  def save(self, filename='memoplot.json'):
    D = {
      'data': self.data,
      'mpl_params': self.mpl_params,
      'config': self.config
    }
    with open(filename,'w') as fp:
      json.dump(D, fp)
      print '[MemoPlot]: File "'+str(filename)+'" saved.'

  def load(self, filename='memoplot.json'):
    with open(filename,'r') as fp:
      D = json.load(fp)
      self.data = D['data']
      self.mpl_params = D['mpl_params']
      self.config = D['config']
      print '[MemoPlot]: File "'+str(filename)+'" loaded.'
