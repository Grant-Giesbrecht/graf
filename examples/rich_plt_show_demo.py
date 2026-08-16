import matplotlib.pyplot as plt

import graf.widgets as gw

# Optional: name the app in the macOS menu bar / Dock, the Windows and Linux
# taskbars, and every window title ("Demo Plots: Figure 1"). Best set before
# any figures are created - the macOS menu bar reads the name only once.
gw.set_app_title("Demo Plots")
# gw.set_app_icon("/path/to/icon.png")
# gw.set_show_coordinates(False)  # hide the x/y readout in the status bar

fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3], [0, 1, 4, 9], label="y = x^2")
ax.set_title("Demo")

# No save_graf needed - defaults to the GrAF package's save_graf.
gw.rich_show(fig, default_filename="demo")
