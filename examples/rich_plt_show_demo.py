import matplotlib.pyplot as plt

import graf.widgets as gw

fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3], [0, 1, 4, 9], label="y = x^2")
ax.set_title("Demo")

# Optional: name the app in the menu bar / window titles, and set its icon.
# Windows are titled "<app title>: Figure N" unless an explicit title is given.
gw.set_app_title("Demo Plots")
# gw.set_app_icon("/path/to/icon.png")
# gw.set_show_coordinates(False)  # hide the x/y readout in the status bar

# No save_graf needed - defaults to the GrAF package's save_graf.
gw.rich_show(fig, default_filename="demo")
