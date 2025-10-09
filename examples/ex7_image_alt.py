import matplotlib.pyplot as plt
import numpy as np
from graf.base import Graf

import matplotlib.cbook as cbook
import matplotlib.cm as cm
from matplotlib.patches import PathPatch
from matplotlib.path import Path

# Fixing random state for reproducibility
np.random.seed(19680801)

delta = 0.025
x = y = np.arange(-3.0, 3.0, delta)
X, Y = np.meshgrid(x, y)
Z1 = np.exp(-X**2 - Y**2)
Z2 = np.exp(-(X - 1)**2 - (Y - 1)**2)
Z = (Z1 - Z2) * 2

fig, ax0 = plt.subplots()
im = ax0.imshow(Z, interpolation='bilinear', cmap=cm.RdYlGn, origin='lower', extent=[-3, 3, -3, 3], vmax=abs(Z).max(), vmin=-abs(Z).max())

A = np.random.rand(5, 5)

fig1, axs1 = plt.subplots(1, 3, figsize=(10, 3))
for ax, interp in zip(axs1, ['nearest', 'bilinear', 'bicubic']):
    ax.imshow(A, interpolation=interp)
    ax.set_title(interp.capitalize())
    ax.grid(True)

g1 = Graf(fig=fig)
g1.save_hdf("ex7.graf")

g1b = Graf(fig=fig1)
g1b.save_hdf("ex7_fig2.graf")

g2 = Graf()
g2.load_hdf("ex7.graf")
fig2 = g2.to_fig()

g3 = Graf()
g3.load_hdf("ex7_fig2.graf")
fig4 = g3.to_fig()

plt.show()
