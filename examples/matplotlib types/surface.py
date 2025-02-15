import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# Create a figure and an axes object
fig = plt.figure()
ax = fig.add_subplot(projection='3d')

# Generate data for the surface
X = np.arange(-5, 5, 0.25)
Y = np.arange(-5, 5, 0.25)
X, Y = np.meshgrid(X, Y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R)

# Plot the surface
surf = ax.plot_surface(X, Y, Z, cmap='viridis')

# Add labels and a colorbar
ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
fig.colorbar(surf)


# Recovering 'surf' after the fig is created, look in ax.collections
# Will be a Poly3DCollection type.
print(ax.collections)
print(type(ax.collections[0]))

# Show the plot
plt.show()