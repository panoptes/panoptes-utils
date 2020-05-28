from PIL import Image, ImageOps


def fix_image_size(max_width, max_height, image):
    """Resizes images while maintaining the same aspect ratio.

    Args:
        max_width: Image width
        max_height: Image height
        image: Image to be resized

    Returns:
        The resized image.
    """
    width_ratio = max_width / image.size[0]  # resized image ratios
    height_ratio = max_height / image.size[1]

    new_width = int(width_ratio * image.size[0])  # proportional width, height value calculations
    new_height = int(height_ratio * image.size[1])

    new_image = image.resize((new_width, new_height))
    return new_image


def grid_display(
    background_jpg,
    overlay_png,
    width=4800,
    height=2400,
    alpha=0.2,
    final_im_filename="final_output.png",
):
    """Overlays RA/DEC grid from 'plot-constellations' onto background_jpg image.
    (see https://manpages.debian.org/testing/astrometry.net/plot-constellations.1.en.html)

   Args:
        background_jpg: A jpg image taken for polar alignment test.
        overlay_png: An RA/DEC grid produced by 'plot-constellations' that has a .png extension.
        width: An optional variable for specifying the final image width.
        height: An optional variable for specifying the final image height.
        alpha: An optional variable for specifying the amount of blending between the overlay and the background image.
        final_im_filename: An optional variable for specifying the name of the final image. 

    Returns:
        The background image with an RA/DEC grid overlay.
    """
    overlay_png = Image.open(overlay_png)
    background = Image.open(background_jpg)

    ol_resize = fix_image_size(width, height, overlay_png)
    bg_resize = fix_image_size(width, height, background)

    ol_flip = ImageOps.flip(ol_resize)  # correct overlay_png orientation
    bg_conv = bg_resize.convert("RGBA")  # converts images to same type
    ol_conv = ol_flip.convert("RGBA")

    alpha_blend = Image.blend(bg_conv, ol_conv, alpha)
    blended_image = alpha_blend.save(final_im_filename, "png")

    return blended_image
