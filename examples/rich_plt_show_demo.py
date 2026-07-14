import matplotlib.pyplot as plt

from graf.widgets import show_graf

fig, ax = plt.subplots()
ax.plot([0, 1, 2, 3], [0, 1, 4, 9], label="y = x^2")
ax.set_title("Demo")

# No save_graf needed - defaults to the GrAF package's save_graf.
show_graf(fig, title="Demo Graf", default_filename="demo")
