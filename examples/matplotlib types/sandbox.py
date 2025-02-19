import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

x = np.linspace(10, 20, 11)
y = np.linspace(-20, -10, 11)
X, Y = np.meshgrid(x, y)
Z = np.sin(X**2 + Y**2)

fig, ax = plt.subplots()
quadmesh = ax.pcolormesh(X, Y, Z, shading='auto')

# Extract the face colors from the QuadMesh (this is the Z data)
Z_data = quadmesh.get_array().data

# Extract the coordinates of the vertices
paths = quadmesh.get_paths()
X_data, Y_data = np.meshgrid(
    [p.vertices[:, 0].mean() for p in paths],
    [p.vertices[:, 1].mean() for p in paths]
)

# Reshape Z_data to match the shape of X and Y
Z_data = Z_data.reshape(X_data.shape)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(X_data, Y_data, Z_data, cmap='viridis')
fig.colorbar(surf)
plt.show()
