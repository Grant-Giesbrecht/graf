import matplotlib.pyplot as plt
import numpy as np

# Create some mock data
t = np.arange(0.01, 10.0, 0.01)
data1 = np.exp(t)
data2 = np.sin(2 * np.pi * t)

fig, ax1 = plt.subplots()

color = 'tab:red'
ax1.set_xlabel('time (s)')
ax1.set_ylabel('exp', color=color)
ax1.plot(t, data1, color=color)
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis

color = 'tab:blue'
ax2.set_ylabel('sin', color=color)  # we already handled the x-label with ax1
ax2.plot(t, data2, color=color)
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
plt.show()

# Detects that ax1 has a twin
hasattr(ax1, 'get_shared_x_axes')

ax1._sharex # is None
ax2._sharex # points to ax1 - is 


# Will need to ID and pair twin-axes before I start with calls to mimic()
		# Find twin-axes and merge them here.
sole_axes = []
twin_axes = []
for ax in fig.get_axes():
	
	# Check if has twin
	if hasattr(ax, 'get_shared_x_axes'):
		if ax._share is None:
			# If primary - add to twins list
			twin_axes.append([ax])
		else:
			# Scan over twin axes lists
			for tals in twin_axes:
				if ax._sharex in tals:
					tals.append(ax)
	else:
		# No twin - add to list
		sole_axes.append(ax)



# Used this code to find differences between the axes
for att in ax1.__dict__:
	if ax1.__dict__[att] != ax2.__dict__[att]:
		try:
			if ax1.__dict__[att].__dict__ == ax2.__dict__[att].__dict__:
				continue
		except:
			pass
		print(f"mismatch: {att}")
		ax1d = ax1.__dict__[att]
		ax2d = ax2.__dict__[att]
		print(f"    {ax1d}")
		print(f"    {ax2d}")