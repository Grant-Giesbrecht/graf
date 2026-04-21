import matplotlib.pyplot as plt
import numpy as np
from graf.base import Graf

np.random.seed(42)
x = np.linspace(1, 5, 8)
y = np.sin(x) + 0.1 * np.random.randn(len(x))
y_err = 0.1 + 0.05 * np.abs(np.sin(x))     # asymmetric y errors
x_err = 0.15                                 # symmetric x errors

# --- Figure 1: y-errors only ---
fig1, axes1 = plt.subplots(1, 2, figsize=(11, 4))
fig1.suptitle("Errorbars — y-only")

axes1[0].errorbar(x, y, yerr=y_err, fmt='o', color='royalblue',
                  ecolor='gray', elinewidth=1.5, capsize=5, capthick=2,
                  label='sin(x)', linewidth=1.2)
axes1[0].set_title("Original")
axes1[0].set_xlabel("X")
axes1[0].set_ylabel("Y")
axes1[0].legend()

g1 = Graf(fig=fig1)
g1.save_hdf("ex12_yerr.graf")

g1b = Graf()
g1b.load_hdf("ex12_yerr.graf")
fig1b = g1b.to_fig()
fig1b.get_axes()[0].set_title("Reconstructed")
fig1b.suptitle("Errorbars — y-only (reconstructed)")

# --- Figure 2: both x and y errors, custom caps ---
fig2, axes2 = plt.subplots(1, 2, figsize=(11, 4))
fig2.suptitle("Errorbars — x and y")

axes2[0].errorbar(x, y, xerr=x_err, yerr=y_err, fmt='s', color='crimson',
                  ecolor='darkred', elinewidth=2, capsize=7, capthick=2.5,
                  linestyle='--', linewidth=1.5, label='data', markersize=8)
axes2[0].set_title("Original")
axes2[0].set_xlabel("X")
axes2[0].set_ylabel("Y")
axes2[0].legend()

g2 = Graf(fig=fig2)
g2.save_hdf("ex12_xyerr.graf")

g2b = Graf()
g2b.load_hdf("ex12_xyerr.graf")
fig2b = g2b.to_fig()
fig2b.get_axes()[0].set_title("Reconstructed")
fig2b.suptitle("Errorbars — x and y (reconstructed)")

# --- Figure 3: two traces, one normal line + one errorbar ---
fig3, axes3 = plt.subplots(1, 2, figsize=(11, 4))
fig3.suptitle("Mixed: line + errorbar")

axes3[0].plot(x, np.cos(x), '-^', color='green', label='cos(x)')
axes3[0].errorbar(x, y, yerr=y_err, fmt='o', color='purple',
                  ecolor='violet', elinewidth=1, capsize=4, capthick=1.5,
                  label='sin(x) ± err')
axes3[0].set_title("Original")
axes3[0].set_xlabel("X")
axes3[0].set_ylabel("Y")
axes3[0].legend()

g3 = Graf(fig=fig3)
g3.save_hdf("ex12_mixed.graf")

g3b = Graf()
g3b.load_hdf("ex12_mixed.graf")
fig3b = g3b.to_fig()
fig3b.get_axes()[0].set_title("Reconstructed")
fig3b.suptitle("Mixed: line + errorbar (reconstructed)")

plt.show()
