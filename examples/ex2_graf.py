from graf.base import *
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 6.283)
y1 = np.sin(x)
y2 = np.sin(x*2)+np.sin(x*7)

# Make an example MPL plot
fig1, (ax1, ax2) = plt.subplots(nrows=2)

ax1.plot(x, y1, marker='o', linestyle=':', color=(0.4, 0, 0.8))
ax1.set_xlabel("X-axis")
ax1.set_ylabel("Y-axis")
ax1.set_title("sin(x)")
fig1.suptitle("Test with Subplots")
ax1.grid(True)

ax2.plot(x, y2, marker='o', linestyle=':', color=(0.25, 0, 0.6))
ax2.set_xlabel("X-axis")
ax2.set_ylabel("Y-axis")
ax2.set_title("sin(2*x)+sin(7*x)")
fig1.suptitle("Test with Subplots")
ax2.grid(True)

graf1 = Graf(fig1) # Convert to GrAF
fig2 = graf1.to_fig() # Convert from GrAF to fig

# graf1_dict = graf1.pack() # Convert GrAF to dict
# graf2 = Graf()
# dict_summary(graf1_dict)
# graf2.unpack(graf1_dict) # Init new GrAF from dict
# fig3 = graf2.to_fig() # Convert GrAF to fig

# graf2.save_hdf("ex1_test.GrAF")
# graf3 = Graf()
# graf3.load_hdf("ex1_test.GrAF")
# fig4 = graf3.to_fig()

plt.show()