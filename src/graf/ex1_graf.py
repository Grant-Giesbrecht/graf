from base import *
import matplotlib.pyplot as plt

x1 = [1,2,3,4,5]
y1 = [10,8,12,9,13]

x2 = [1,2,3,4,5,6,7,8,9,10]
y2 = [7,3,7,6,5,7,2,1,9, 0]

# fig1, (ax1, ax2) = plt.subplots(nrows=2)


# ax1.plot(x1, y1)
# ax2.plot(x2, y2)

# graf1 = Graf(fig1)

# Make an example MPL plot
fig1, ax1 = plt.subplots(nrows=1)
ax1.plot(x1, y1)

graf1 = Graf(fig1) # Convert to GrAF
fig2 = graf1.to_fig() # Convert from GrAF to fig

graf1_dict = graf1.pack() # Convert GrAF to dict
graf2 = Graf() 
graf2.unpack(graf1_dict) # Init new GrAF from dict
fig3 = graf2.to_fig() # Convert GrAF to fig

plt.show()