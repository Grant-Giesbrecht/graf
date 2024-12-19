import matplotlib.pyplot as plt

fig = plt.figure(1)

# Can also do it like this: ax = plt.axes(projection='3d') supposedly
ax = fig.add_subplot(1, 1, 1, projection='3d')

# If you don't call projection='3d' first, it will get very grumpy
ax.plot([1,2,3,4], [5, 3, 4, 5], zs=[10, 11, 12, 13])

# NOTE: 3d projection name does not differentiate between 3d line plots and 3d surfaces. will need to look at dimensionality of data to determine this
print(f"Axis projection type: {ax.name}") # Will be 3d, vs rectilinear (2D), polar (2D), etc