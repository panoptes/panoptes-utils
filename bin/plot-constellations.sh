#!/bin/bash -e

usage() {
  echo -n "##################################################
# Make a png with an RA/DEC grid overlay from a FITS image and a PPM input file.
#
# Uses imagemagick tool to flip jpeg image and astrometry.net 'plot-consellations' tool to create overlay.
#
# If present the TITLE is added as a title to the png.
##################################################
 $ $(basename $0) FILENAME PPM

 Options:
  FILENAME          Name of fits file to be converted into a png overlay.
  JPEG               JPEG input file to get image pixels (will get converted to PPM).

 Example:
  plot-constellations Documents/pole_canon01.fits pole_canon01.jpg 
"
}

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

export PATH=/usr/share/doc:$PATH

FNAME=$1
JPG=$2
TITLE="${3}"

PNG="${FNAME%.fits}-output.png"

echo "Converting fits image to ${PNG} with an overlay."

function command_exists {
    # https://gist.github.com/gubatron/1eb077a1c5fcf510e8e5
    # this should be a very portable way of checking if something is on the path
    # usage: "if command_exists foo; then echo it exists; fi"
  type "$1" &> /dev/null
}

# Use imagemagick to correct jpeg orientation
if command_exists imagemagick; then
    echo "Using imagemagick to flip jpeg image."
    convert -flip "${JPG}" > "${JPG%.jpg}-flip.jpg"
else
    echo "Can't find imagemagick, cannot proceed"
    exit 1
    if command_exists plot-constellations; then
        # Create PNG overlay
        echo "Using plot-constellations to create png image w/ an overlay."
        jpegtopnm "${JPG%.jpg}-flip.jpg" | plot-constellations -w ${FNAME} -G 60 -B -b 25 -f 30 -i- -o ${PNG}
    else
        echo "Can't find plot-constellations, cannot proceed"
        exit 1
    fi
fi

echo "${PNG}"
