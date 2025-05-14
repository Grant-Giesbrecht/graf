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

fig1 = plt.figure(1)
gs1 = fig1.add_gridspec(2, 1)
ax1 = fig1.add_subplot(gs1[0, 0])
ax2 = fig1.add_subplot(gs1[1, 0])

im1 = ax1.imshow(Z, interpolation='bilinear', cmap=cm.RdYlGn, origin='lower', extent=[-3, 3, -3, 3], vmax=abs(Z).max(), vmin=-abs(Z).max())
fig1.colorbar(im1, label="Foiled again!")

im2 = ax2.imshow(Z, interpolation='bilinear', cmap='plasma', origin='lower', extent=[-3, 3, -3, 3], vmax=abs(Z).max(), vmin=-abs(Z).max())
# fig1.colorbar(im1)


# g1 = Graf(fig=fig1)
# g1.save_hdf("ex7a.graf")
# 
# g2 = Graf()
# g2.load_hdf("ex7a.graf")
# fig2 = g2.to_fig()

fig1.tight_layout()

plt.show()
