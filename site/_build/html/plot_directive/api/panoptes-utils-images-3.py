from matplotlib import pyplot as plt
import numpy as np
from panoptes.utils.images.plot import add_colorbar
x = np.arange(0.0, 100.0)
y = np.arange(0.0, 100.0)
X, Y = np.meshgrid(x, y)
func = lambda x, y: x**2 + y**2
z = func(X, Y)
fig, ax = plt.subplots()
im1 = ax.imshow(z, origin='lower')
add_colorbar(im1)
fig.show()
