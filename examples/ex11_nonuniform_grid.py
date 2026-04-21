import matplotlib.pyplot as plt
import numpy as np
from graf.base import Graf

# --- Figure 1: polar-style non-uniform grid ---
# X and Y coordinates are non-separable (x at row i, col j ≠ x at row k, col j)
theta = np.linspace(0, np.pi / 2, 20)
r = np.linspace(0.5, 3.0, 15)
X_polar = np.outer(r, np.cos(theta))   # (15, 20) corner positions
Y_polar = np.outer(r, np.sin(theta))
Z_polar = (X_polar[:-1, :-1]**2 + Y_polar[:-1, :-1]**2)  # (14, 19) cell values

fig1, axes1 = plt.subplots(1, 2, figsize=(11, 4))
fig1.suptitle("Non-uniform pcolormesh (polar-style grid)")

qm1 = axes1[0].pcolormesh(X_polar, Y_polar, Z_polar, cmap='viridis')
axes1[0].set_aspect('equal')
axes1[0].set_title("Original")
axes1[0].set_xlabel("X")
axes1[0].set_ylabel("Y")
fig1.colorbar(qm1, ax=axes1[0], label="r²")

g1 = Graf(fig=fig1)
g1.save_hdf("ex11_polar_grid.graf")

g1b = Graf()
g1b.load_hdf("ex11_polar_grid.graf")
fig1b = g1b.to_fig()
fig1b.get_axes()[0].set_aspect('equal')
fig1b.get_axes()[0].set_title("Reconstructed")
fig1b.suptitle("Non-uniform pcolormesh (polar-style grid) — reconstructed")

# --- Figure 2: stretched non-uniform grid (x-spacing varies with row) ---
# Build a grid where horizontal spacing narrows as y increases
ny, nx = 18, 22
y_edges = np.linspace(0, 2, ny + 1)
X_stretched = np.zeros((ny + 1, nx + 1))
Y_stretched = np.zeros((ny + 1, nx + 1))
for i, yi in enumerate(y_edges):
    squeeze = 1.0 - 0.6 * (yi / 2.0)   # spacing narrows toward top
    X_stretched[i, :] = np.linspace(-squeeze * 3, squeeze * 3, nx + 1)
    Y_stretched[i, :] = yi

Z_stretched = np.sin(X_stretched[:-1, :-1]) * np.cos(Y_stretched[:-1, :-1])

fig2, axes2 = plt.subplots(1, 2, figsize=(11, 4))
fig2.suptitle("Non-uniform pcolormesh (stretched grid)")

qm2 = axes2[0].pcolormesh(X_stretched, Y_stretched, Z_stretched, cmap='RdBu')
axes2[0].set_title("Original")
axes2[0].set_xlabel("X")
axes2[0].set_ylabel("Y")
fig2.colorbar(qm2, ax=axes2[0], label="sin(x)·cos(y)")

g2 = Graf(fig=fig2)
g2.save_hdf("ex11_stretched_grid.graf")

g2b = Graf()
g2b.load_hdf("ex11_stretched_grid.graf")
fig2b = g2b.to_fig()
fig2b.get_axes()[0].set_title("Reconstructed")
fig2b.suptitle("Non-uniform pcolormesh (stretched grid) — reconstructed")

# Verify uniformity flags
print(f"Polar grid   — uniform_grid = {g1b.axes['Ax0'].surfaces['Sf0'].uniform_grid}")
print(f"Stretched grid — uniform_grid = {g2b.axes['Ax0'].surfaces['Sf0'].uniform_grid}")

plt.show()
