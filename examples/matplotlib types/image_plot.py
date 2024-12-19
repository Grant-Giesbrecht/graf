import matplotlib.pyplot as plt
import numpy as np

# Create sample data
x = np.arange(-5, 5, 0.1)
y = np.arange(-5, 5, 0.1)
X, Y = np.meshgrid(x, y)
Z = np.sin(np.sqrt(X**2 + Y**2))

# Display the data using pcolormesh
plt.pcolormesh(X, Y, Z, cmap='hot') 
plt.colorbar()  # Optional: Add a colorbar
plt.show()