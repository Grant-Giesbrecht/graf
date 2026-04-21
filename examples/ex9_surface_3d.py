from graf.base import *
import matplotlib.pyplot as plt
import numpy as np
import pylogfile.base as plf

fmt = plf.LogFormat()
fmt.show_detail = True
log = plf.LogPile(str_fmt=fmt)
log.set_terminal_level("LOWDEBUG")

# Build a sinc-like surface
X = np.arange(-5, 5, 0.5)
Y = np.arange(-5, 5, 0.5)
X, Y = np.meshgrid(X, Y)
R = np.sqrt(X**2 + Y**2) + 1e-9
Z = np.sin(R) / R

fig1 = plt.figure()
ax = fig1.add_subplot(111, projection='3d')
ax.plot_surface(X, Y, Z, cmap='viridis')
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D Surface — original")

# Save to GrAF
graf1 = Graf(fig=fig1, log=log)
graf1.save_hdf("ex9_surface_3d.graf")

# Reload and reconstruct
graf2 = Graf(log=log)
graf2.load_hdf("ex9_surface_3d.graf")
fig2 = graf2.to_fig(window_title="3D Surface — reconstructed")

plt.show()
