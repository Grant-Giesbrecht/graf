import matplotlib.pyplot as plt
import numpy as np

# Create a sample figure with twin y-axes
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

# Plot some data on both axes
x = np.linspace(0, 10, 100)
line1, = ax1.plot(x, np.sin(x), label="Sin(x)")
line2, = ax2.plot(x, np.cos(x), label="Cos(x)")

# Function to get lines associated with each y-axis
def get_twin_axis_lines(ax1, ax2):
    left_y_lines = ax1.get_lines()
    right_y_lines = ax2.get_lines()
    
    return left_y_lines, right_y_lines

# Get the lines
left_y_lines, right_y_lines = get_twin_axis_lines(ax1, ax2)

# Print the line labels for verification
print("Left Y-Axis Lines:")
for line in left_y_lines:
    print(line.get_label())

print("\nRight Y-Axis Lines:")
for line in right_y_lines:
    print(line.get_label())

# Display the figure
plt.show()
