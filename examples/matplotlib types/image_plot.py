import matplotlib.pyplot as plt
import numpy as np

# Create sample data
x = np.arange(-25, -15, 0.1)
y = np.arange(-5, 5, 0.1)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))


# # Display the data using pcolormesh
# c = plt.pcolormesh(X, Y, Z, cmap='hot') 
# plt.colorbar()  # Optional: Add a colorbar
# plt.tight_layout()
# ax1a = plt.gca()


fig1 = plt.figure(1)
gs = fig1.add_gridspec(1, 1)
ax1a = fig1.add_subplot(gs[0, 0])

# Display the data using pcolormesh
c = ax1a.pcolormesh(X, Y, Z, cmap='hot') 
fig1.colorbar(c, ax=ax1a)  # Optional: Add a colorbar

fig1.tight_layout()

# TO find 'c' after the fact, look in ax.collections:
# for imshow() calls it will be in ax.images, not collections.
print(ax1a.collections)
print(type(ax1a.collections[0])) # Will be a QuadMesh type

plt.show()