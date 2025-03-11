import matplotlib.pyplot as plt
import numpy as np
from graf.base import *

# Create some mock data
t = np.arange(0.01, 10.0, 0.01)
data1 = np.exp(t)
data2 = np.sin(2 * np.pi * t)

# Create figure with twin axes
fig1 = plt.figure(1)
gs1 = fig1.add_gridspec(1, 1)
ax1a = fig1.add_subplot(gs1[0, 0])
ax1b = ax1a.twinx()

# Plot things
ax1a.set_xlabel('time (s)')
ax1a.set_ylabel('exp', color=[0.7, 0, 0])
ax1a.plot(t, data1, color=[0.7, 0, 0])
ax1a.tick_params(axis='y', labelcolor=[0.7, 0, 0])
ax1a.grid(True)
ax1b.set_ylabel('sin', color=[0, 0.7, 0])  # we already handled the x-label with ax1a
ax1b.plot(t, data2, color=[0, 0.7, 0])
ax1b.tick_params(axis='y', labelcolor=[0, 0.7, 0])

# Create figure without twin axes for comparison
fig2 = plt.figure(2)
gs2 = fig2.add_gridspec(1, 1)
ax2a = fig2.add_subplot(gs2[0, 0])
ax2a.plot([1,2,3], [4,6,5])

#------------- This will NOT work -------------
# It will show false and will not realize that these are twins
ax1a.get_shared_x_axes().get_siblings(ax1a) == ax1b 

#------------ This WILL work --------------
# The get_siblings() function returns a list which will have 1 empty Axis object
# if no twin was created. Comparing the list to an Axis will always return false
# as we saw above, instead you have to always compare the elements in the list.

# Get list of sibling axes (will contain the original axis too)
sib_list_1a = ax1a.get_shared_x_axes().get_siblings(ax1a)

# Print comparisons
result_1 = (sib_list_1a[0] == ax1a)
result_2 = (sib_list_1a[0] == ax1b)
result_3 = (sib_list_1a[1] == ax1a)
result_4 = (sib_list_1a[1] == ax1b)
print(f"sib_list_1a[0] == ax1a: {result_1}")
print(f"sib_list_1a[0] == ax1b: {result_2}")
print(f"sib_list_1a[1] == ax1a: {result_3}")
print(f"sib_list_1a[1] == ax1b: {result_4}\n")

##----------- How do sole-axes compare? ---------
#

# This is going to contain 1 axis that is the original axis.
sib_list_2a = ax2a.get_shared_x_axes().get_siblings(ax2a)

print(f"ax1a sibling list (has-twin): {sib_list_1a}")
print(f"ax2a sibling list (no-twin):  {sib_list_2a}\n")

#--------- We can turn all of this into a function -------------
#

def has_twinx(ax):
	
	# Get list of siblings
	sibling_list = ax.get_shared_x_axes().get_siblings(ax)
	
	# Scan over all axes in figure
	for fig_ax in ax.figure.axes:
		
		# Skip axis if is original axis
		if fig_ax == ax:
			continue
		
		# Scan over all siblings 
		for sib_ax in sibling_list:
			
			# Return true if found a match
			if sib_ax == fig_ax:
				return True
	
	# No twin was found
	return False

print(f"has_twinx(ax1a): {has_twinx(ax1a)}")
print(f"has_twinx(ax1b): {has_twinx(ax1b)}")
print(f"has_twinx(ax2a): {has_twinx(ax2a)}")