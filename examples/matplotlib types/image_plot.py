import matplotlib.pyplot as plt
import numpy as np

# Create sample data
x = np.arange(-5, 5, 0.1)
y = np.arange(-5, 5, 0.1)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

# Display the data using pcolormesh
c = plt.pcolormesh(X, Y, Z, cmap='hot') 
plt.colorbar()  # Optional: Add a colorbar
plt.show()

# TO find 'c' after the fact, look in ax.collections:
# for imshow() calls it will be in ax.images, not collections.
ax = plt.gca()
print(ax.collections)
print(type(ax.collections[0])) # Will be a QuadMesh type