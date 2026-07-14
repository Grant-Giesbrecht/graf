import matplotlib.pyplot as plt

import graf.widgets as gw

fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3], [0, 1, 4, 9], label="y = x^2")
ax.set_title("Demo")

# No save_graf needed - defaults to the GrAF package's save_graf.
gw.rich_show(fig, title="Demo Graf", default_filename="demo")
