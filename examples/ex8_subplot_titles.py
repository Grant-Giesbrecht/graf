import matplotlib.pyplot as plt
import numpy as np
from graf.base import *

# Create some mock data
t = np.arange(0.01, 10.0, 0.01)
data1 = np.exp(t)
data2 = np.sin(2 * np.pi * t)
data3 = np.sinh(2 * np.pi * t)

fig1 = plt.figure(1)
gs1 = fig1.add_gridspec(1, 3)
ax1a = fig1.add_subplot(gs1[0, 0])
ax1b = fig1.add_subplot(gs1[0, 1])
ax1c = fig1.add_subplot(gs1[0, 2])

ax1a.plot(t, data1)
ax1a.set_title("exp")
ax1b.plot(t, data2)
ax1b.set_title("sin")
ax1c.plot(t, data3)
ax1c.set_title("sin-h")

g1_out = Graf(fig=fig1)
g1_out.save_hdf("ex8.graf")

g1_in = Graf()
g1_in.load_hdf("ex8.graf")
fig1_copy = g1_in.to_fig()




plt.show()