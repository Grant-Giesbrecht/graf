from graf.base import *
import matplotlib.pyplot as plt
import pylogfile.base as plf

fmt = plf.LogFormat()
fmt.show_detail = True
log = plf.LogPile(str_fmt=fmt)
log.set_terminal_level("LOWDEBUG")

# create objects
# fig1 = plt.figure(constrained_layout=True)
fig1 = plt.figure()
# ax = fig.add_subplot((1,1,1), projection='3d')
ax = fig1.add_subplot(111, projection='3d')
line1 = ax.plot([1,2,3,4,2,3], [1,1,1,1,2,2], [1,2,3,4,5,6], marker='o', linestyle=':')
ax.set_xlabel("X-axis")
ax.set_ylabel("Y-axis")
ax.set_zlabel("Z-axis")

graf1 = Graf(fig=fig1, log=log)
graf1.save_hdf("ex4_line3d.graf")

graf2 = Graf(log=log)
# graf2.log.set_terminal_level("LOWDEBUG")
# graf2.log.str_format.show_detail = True

graf2.load_hdf("ex4_line3d.graf")
fig2 = graf2.to_fig()

plt.show()