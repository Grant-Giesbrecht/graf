from graf.base import *
import matplotlib.pyplot as plt
 
# create objects
fig = plt.figure(constrained_layout=True)
# ax = fig.add_subplot((1,1,1), projection='3d')
ax = fig.add_subplot(111, projection='3d')
line1 = ax.plot([1,2,3,4,2,3], [1,1,1,1,2,2], [1,2,3,4,5,6], marker='o', linestyle=':')

plt.show()