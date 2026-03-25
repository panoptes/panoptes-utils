from matplotlib import pyplot as plt
from astropy.wcs import WCS
from panoptes.utils.images.misc import crop_data
from panoptes.utils.images.plot import add_colorbar, get_palette
from panoptes.utils.images.fits import getdata
fits_url = 'https://github.com/panoptes/panoptes-utils/raw/develop/tests/data/solved.fits.fz'
data, header = getdata(fits_url, header=True)
wcs = WCS(header)
cropped = crop_data(data, center=(600, 400), box_width=100, wcs=wcs, data_only=False)
fig, ax = plt.subplots()
im = ax.imshow(cropped.data, origin='lower', cmap=get_palette())
add_colorbar(im)
plt.show()
