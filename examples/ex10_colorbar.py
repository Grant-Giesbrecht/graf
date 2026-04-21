import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from graf.base import Graf

# --- Shared data ---
x = np.linspace(-3, 3, 40)
y = np.linspace(-3, 3, 40)
X, Y = np.meshgrid(x, y)
Z1 = np.exp(-X**2 - Y**2)
Z2 = np.exp(-(X - 1)**2 - (Y - 1)**2)
Z = (Z1 - Z2) * 2

# --- Figure 1: pcolormesh with vertical colorbar ---
fig1, axes1 = plt.subplots(1, 2, figsize=(10, 4))
fig1.suptitle("pcolormesh — vertical colorbar")

qm_l = axes1[0].pcolormesh(X, Y, Z, cmap='plasma')
axes1[0].set_title("Original")
axes1[0].set_xlabel("X")
axes1[0].set_ylabel("Y")
fig1.colorbar(qm_l, ax=axes1[0], label="Amplitude")

g1 = Graf(fig=fig1)
g1.save_hdf("ex10_pcolormesh_cbar.graf")

g1b = Graf()
g1b.load_hdf("ex10_pcolormesh_cbar.graf")
fig1b = g1b.to_fig()
fig1b.get_axes()[0].set_title("Reconstructed")
fig1b.suptitle("pcolormesh — vertical colorbar (reconstructed)")

# --- Figure 2: imshow with horizontal colorbar ---
fig2, ax2 = plt.subplots(figsize=(6, 5))
fig2.suptitle("imshow — horizontal colorbar")

im = ax2.imshow(Z, interpolation='bilinear', cmap=cm.RdYlGn,
                origin='lower', extent=[-3, 3, -3, 3],
                vmax=abs(Z).max(), vmin=-abs(Z).max())
ax2.set_title("Original")
ax2.set_xlabel("X")
ax2.set_ylabel("Y")
fig2.colorbar(im, ax=ax2, orientation='horizontal', label="Value")

g2 = Graf(fig=fig2)
g2.save_hdf("ex10_imshow_cbar.graf")

g2b = Graf()
g2b.load_hdf("ex10_imshow_cbar.graf")
fig2b = g2b.to_fig()
fig2b.get_axes()[0].set_title("Reconstructed")
fig2b.suptitle("imshow — horizontal colorbar (reconstructed)")

# --- Figure 3: 3D surface with colorbar ---
X3 = np.arange(-4, 4, 0.3)
Y3 = np.arange(-4, 4, 0.3)
X3, Y3 = np.meshgrid(X3, Y3)
R3 = np.sqrt(X3**2 + Y3**2) + 1e-9
Z3 = np.sin(R3) / R3

fig3 = plt.figure(figsize=(6, 5))
ax3 = fig3.add_subplot(111, projection='3d')
surf3 = ax3.plot_surface(X3, Y3, Z3, cmap='coolwarm')
ax3.set_xlabel("X")
ax3.set_ylabel("Y")
ax3.set_zlabel("Z")
ax3.set_title("3D surface — original")
fig3.colorbar(surf3, ax=ax3, label="sinc(r)")

g3 = Graf(fig=fig3)
g3.save_hdf("ex10_surface3d_cbar.graf")

g3b = Graf()
g3b.load_hdf("ex10_surface3d_cbar.graf")
fig3b = g3b.to_fig("3D surface — reconstructed")
fig3b.get_axes()[0].set_title("3D surface — reconstructed")

plt.show()
