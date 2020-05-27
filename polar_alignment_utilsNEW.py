from PIL import Image, ImageOps


   
def jpg2png(background):                        #converts jpg image to png
    background = Image.open(f"{background}")
    bg_png = background.save('newPNG.png', "png")


def fixImageSize(maxWidth, maxHeight, image):
    '''Resizes images while maintaining the same aspect ratio.

    Args: 
    maxWidth: Image Width
    maxHeight: Image Height
    image: Image to be resized

    Returns:
    The resized image.
    '''
    widthRatio = maxWidth/image.size[0]  #resized image ratios
    heightRatio = maxHeight/image.size[1]

    newWidth = int(widthRatio*image.size[0])    #proportional width, height value calculations
    newHeight = int(heightRatio*image.size[1])

    newImage = image.resize((newWidth, newHeight))
    return newImage

def grid_Display(background, overlay):  
    '''Overlays RA/DEC grid from 'plot-constellations' onto background image.
    (see https://manpages.debian.org/testing/astrometry.net/plot-constellations.1.en.html)

   Args: 
   background('example1.png'): A PNG image taken for polar alignment test.
   overlay('example2.png'): An RA/DEC grid produced by 'plot-constellations'.
    '''
     
    overlay = Image.open(f"{overlay}")
    background = Image.open(f"{background}")

    ol_resize = fixImageSize (4800,2400,overlay)
    bg_resize = fixImageSize(4800,2400,background)

    ol_flip = ImageOps.flip(ol_resize)       #correct overlay orientation


    bg_conv = bg_resize.convert("RGBA")        #converts images to same type
    ol_conv = ol_flip.convert("RGBA")

    alphaBlend = Image.blend(bg_conv, ol_conv, alpha = 0.2)     #blends background and overlay together
    alphaBlend.save("FINAL.png", "PNG")


