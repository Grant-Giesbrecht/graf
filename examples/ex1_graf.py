from graf.base import *
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
ax1.plot(x1, y1, marker='o', linestyle=':', color=(0.8, 0, 0.4))
ax1.set_xlabel("X-axis")
ax1.set_ylabel("Y-axis")
fig1.suptitle("Test")
ax1.grid(True)

graf1 = Graf(fig1) # Convert to GrAF
fig2 = graf1.to_fig() # Convert from GrAF to fig

graf1_dict = graf1.pack() # Convert GrAF to dict
graf2 = Graf()
print(graf1_dict)
dict_summary(graf1_dict)
graf2.unpack(graf1_dict) # Init new GrAF from dict
fig3 = graf2.to_fig() # Convert GrAF to fig

graf2.save_hdf("ex1_test.GrAF")
graf3 = Graf()
graf3.load_hdf("ex1_test.GrAF")
fig4 = graf3.to_fig()

plt.show()