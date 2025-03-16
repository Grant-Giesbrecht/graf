from graf.base import *
import matplotlib.pyplot as plt
 
# create objects
fig1 = plt.figure(constrained_layout=True)
# ax = fig.add_subplot((1,1,1), projection='3d')
ax = fig1.add_subplot(111, projection='3d')
line1 = ax.plot([1,2,3,4,2,3], [1,1,1,1,2,2], [1,2,3,4,5,6], marker='o', linestyle=':')


graf1 = Graf(fig=fig1)
graf1.save_hdf("ex4_line3d.graf")

graf2 = Graf()
graf2.load_hdf("ex4_line3d.graf")
fig2 = graf2.to_fig()

plt.show()