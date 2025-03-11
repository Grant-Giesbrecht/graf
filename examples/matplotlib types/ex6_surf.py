import matplotlib.pyplot as plt
import numpy as np
from graf.base import *

# Create sample data
x = np.arange(-25, -15, 0.1)
y = np.arange(-5, 5, 0.1)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

fig1 = plt.figure(1)
gs = fig1.add_gridspec(1, 1)
ax1a = fig1.add_subplot(gs[0, 0])

# Display the data using pcolormesh
c = ax1a.pcolormesh(X, Y, Z, cmap='hot') 
fig1.colorbar(c, ax=ax1a)  # Optional: Add a colorbar

fig1.tight_layout()

# Create GrAF
g1 = Graf(fig=fig1)
g1.save_hdf("ex5.graf")

# plt.show()