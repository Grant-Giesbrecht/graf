import matplotlib.pyplot as plt
import numpy as np
from graf.base import *

# Create some mock data
t = np.arange(0.01, 10.0, 0.01)
data1 = np.exp(t)
data2 = np.sin(2 * np.pi * t)

# fig1, ax1a = plt.subplots()

fig1 = plt.figure(1)
gs = fig1.add_gridspec(1, 1)
ax1a = fig1.add_subplot(gs[0, 0])
ax1b = ax1a.twinx()  # instantiate a second Axes that shares the same x-axis

color = 'tab:red'
ax1a.set_xlabel('time (s)')
ax1a.set_ylabel('exp', color=color)
ax1a.plot(t, data1, color=color)
ax1a.tick_params(axis='y', labelcolor=color)



color = 'tab:blue'
ax1b.set_ylabel('sin', color=color)  # we already handled the x-label with ax1a
ax1b.plot(t, data2, color=color)
ax1b.tick_params(axis='y', labelcolor=color)

ax1a.grid(True)

fig1.tight_layout()  # otherwise the right y-label is slightly clipped

# Example of non-twin axis
fig2, ax2a = plt.subplots()
ax2a.plot([1,2,3], [4,6,5])

# # Note: I used to think this approach would work, but it does not!
# print(f"(Has Twin) hasattr(ax1b, 'get_shared_x_axes'): {hasattr(ax1b, 'get_shared_x_axes')}")
# print(f"(No twin) hasattr(ax2a, 'get_shared_x_axes'): {hasattr(ax2a, 'get_shared_x_axes')}")
# 
# # New approach:
# def has_twin(ax):
# 	if ax in ax.figure.get_axes():
# 		if len(ax.figure.get_axes()) > 1:  # More than 1 axis in the figure
# 			# Iterate through the axes to check if any axis shares the same x-axis
# 			for other_ax in ax.figure.get_axes():
# 				if ax != other_ax and ax.get_shared_x_axes() == other_ax.get_shared_x_axes():
# 					return True
# 					print("This axis has a twin x-axis.")
# 					break
# 	return False
# 
# print(f"(Has Twin) hasattr(ax1b, 'get_shared_x_axes'): {has_twin(ax1b)}")
# print(f"(No twin) hasattr(ax2a, 'get_shared_x_axes'): {has_twin(ax2a)}")

g1 = Graf(fig=fig1)
g1.save_hdf("ex5_twin.graf")

g2 = Graf(fig=fig2)
g2.save_hdf("ex5_notwin.graf")

g1x = Graf()
g1x.load_hdf("ex5_twin.graf")
fig3 = g1x.to_fig()

g2x = Graf()
g2x.load_hdf("ex5_notwin.graf")
fig4 = g2x.to_fig()


plt.show()