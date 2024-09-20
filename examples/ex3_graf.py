'''
Complex subplot arrangement, borrowed from:
https://www.geeksforgeeks.org/make-subplots-span-multiple-grid-rows-and-columns-in-matplotlib/


'''

from graf.base import *


# explictit function to hide index 
# of sub plots in the figure
def formatAxes(fig):
	for i, ax in enumerate(fig.axes):
		ax.text(0.5, 0.5, "ax%d" % (i+1), va="center", ha="center")
		ax.tick_params(labelbottom=False, labelleft=False)
 
# import required modules
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
 
# create objects
fig = plt.figure(constrained_layout=True)
gs = GridSpec(3, 3, figure=fig)
 
# create sub plots as grid
ax1 = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[1, :-1])
ax3 = fig.add_subplot(gs[1:, -1])
ax4 = fig.add_subplot(gs[-1, 0])
ax5 = fig.add_subplot(gs[-1, -2])
 
# depict illustration
fig.suptitle("GridSpec")
formatAxes(fig)


graf1 = Graf(fig) # Convert to GrAF
fig2 = graf1.to_fig() # Convert from GrAF to fig

plt.show()
