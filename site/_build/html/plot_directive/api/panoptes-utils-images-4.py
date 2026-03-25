from matplotlib import pyplot as plt
import numpy as np
from panoptes.utils.images.plot import add_pixel_grid
x = np.arange(-5, 5)
y = np.arange(-5, 5)
X, Y = np.meshgrid(x, y)
func = lambda x, y: x**2 - y**2
fig, ax = plt.subplots()
im1 = ax.imshow(func(X, Y), origin='lower', cmap='Greys')
add_pixel_grid(ax, grid_height=10, grid_width=10, show_superpixel=True, show_axis_labels=False)
fig.show()
