# MPL Boilerplate
import numpy as np
import matplotlib
import json
import types
matplotlib.use('Agg')
# pylint: disable=unused-import
import matplotlib.pyplot as plt
from matplotlib import rcParams
# pylint: disable=unused-import
import matplotlib.cm as cm
import matplotlib.colors
import matplotlib.patches
# pylint: disable=unused-import
import matplotlib as mpl

################################################################################
# Basic styles and defaults

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
def make_clr(n_colors):
  '''Return an array of n_colors colors, interpolated from the primary four.'''
  # Not the most efficient thing in the world...
  source_xs = np.arange(0,4)*n_colors/4.
  source_ys = zip(*[crimson,blue,teal,orange])
  dest_xs = np.arange(0,n_colors)
  dest_ys = np.array([np.interp(dest_xs,source_xs,source_y) for source_y in source_ys]).T.tolist()
  return dest_ys

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

################################################################################
# Mechanism for attaching debug/logging information to plots simply.

def attach_notes(figure):
  '''Expands a figure and adds a right-hand column for logging text notes.

  Note: this mutates the figure object in a non-standard way. Any other
  modifications to the figure may break this.'''
  # Implementation details: In order to make a persistent, detectable notes
  # column, we grab and expand the figure dimensions, then monkey-patch in
  # some extra data to flag this is a notes-enabled figure.

  if hasattr(figure,'_mplp_notes_enabled'):
    return # only use one notes column
  figure._mplp_notes_enabled = True

  COLWIDTH = 3 # NOTE: this value controls the notes column width

  w = figure.get_figwidth()
  spp = figure.subplotpars

  # Create paper space for the new column
  new_w = float(w+COLWIDTH)
  figure.set_figwidth(new_w)

  # Push the old stuff over
  new_sp_left = spp.left*w/new_w
  new_sp_right = spp.right*w/new_w
  figure.subplots_adjust(left=new_sp_left, right=new_sp_right)

  # Create a new axes for the text
  # NOTE: tight_layout still does not work properly with this, as it only
  #   recognizes subplots, which this is not. If you really need auto-fitting,
  #   try "bbox_inches='tight'" as a kwarg to savefig(). This does something
  #   similar and avoids the issue.
  rect = [w/new_w, 0, COLWIDTH/new_w, 1.0]
  print 'rect',rect
  figure._mplp_notes_ax = figure.add_axes(rect, label='NOTES', xmargin=0)
  figure._mplp_notes_ax.set_xticks([])
  figure._mplp_notes_ax.set_yticks([])
  # Text axes are in real (paper dimension) coordinates
  figure._mplp_notes_ax.set_xlim([0,COLWIDTH])
  figure._mplp_notes_ax.set_ylim([0,figure.get_figheight()])

  # Track the note offset
  figure._mplp_offset = 2/72. # 2 pt. vertical offset on bottom

  # Also monkey-patch in add_note as bound method to figure. (shortcut)
  figure.add_note = types.MethodType(add_note, figure)
  # NOTE: you (perhaps obviously) have to call attach_notes or add_note
  #   first, before you can use this as a method

def add_note(figure, *strings, **kwargs):
  '''Adds a textual note to a figure's notes column.

  Multiple strings can be passed positionally and will be ' '-concatenated.
  Keyword arguments (aside from a few reserved ones) will be passed to text().

  NOTE: If this function is called on a figure without a notes column, we
  do *NOT* add a note. This is to allow a user to wantonly throw add_note()'s
  around, and disable them by eliminating the attach_notes() call once.'''

  if not hasattr(figure, '_mplp_notes_enabled'):
    return

  fd={'family':'monospace', 'color': 'black', 'weight':100, 'size': 10}
  for kw in ['x','y','s','fontdict','wrap']:
    try:
      del kwargs[kw]
    except: pass
  t = figure._mplp_notes_ax.text(
    x=0,
    y=figure._mplp_offset, # only works because axes are set manually to real coordinates
    s=' '.join([str(s) for s in strings]), # emulate print's functionality
    fontdict=fd,
    wrap=False) # Getting multi-line heights to increment offset is *ugly*.
  #height = t
  figure._mplp_offset += t.get_fontsize()/72. # ~ points per inch


################################################################################
# Data caching and fast re-plotting utilities

class Cacher(object):
  '''Mix-in class for storing a snapshot of data.'''
  def _save(self, blob, filename='cache.json'):
    with open(filename,'w') as fp:
      json.dump(blob, fp)
      print '[MemoPlot]: File "'+str(filename)+'" saved.'

  def _load(self, filename='cache.json'):
    with open(filename,'r') as fp:
      blob = json.load(fp)
      print '[MemoPlot]: File "'+str(filename)+'" loaded.'
      return blob

class MemoPlot(Cacher):
  '''Abstract base class for a reproducible, persistable, and memoizing plotter.'''
  def __init__(self, mpl_params=None):
    if mpl_params is None:
      mpl_params = {}
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
    self._save(D,filename)

  def load(self, filename='memoplot.json'):
    D = self._load(filename)
    self.data = D['data']
    self.mpl_params = D['mpl_params']
    self.config = D['config']
