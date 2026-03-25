.. _cli:

==================
Command Line Utils
==================

``panoptes-utils`` provides a command line interface for some of the common functions
in the module.

Commands
--------

The main command is called ``panoptes-utils`` and includes subcommands for specific
tasks.  The subcommands are available via the help menu:

.. code-block:: bash

    $ panoptes-utils --help
    Usage: panoptes-utils [options] <command> [<args>]
    Options:
      --help  Show this message and exit.
    Commands:
      image     Process an image.

image
=====

The ``image`` subcommand provides access to image conversion and plate-solving as
well as a generic tool for watching a directory and performing any of the other
image subcommands.

.. code-block:: bash

    $ panoptes-utils image --help
    Usage: panoptes-utils image [OPTIONS] COMMAND [ARGS]...

      Process an image.

    Options:
      --help  Show this message and exit.

    Commands:
      cr2
      fits
      watch  Watch a directory for changes and process any new files.

image watch
~~~~~~~~~~~

A tool for watching a directory and performing subcommands on all incoming files.
This command will block until cancelled by the user via ``Ctrl-c``.

.. code-block:: bash

    Usage: panoptes-utils image watch [OPTIONS] PATH

      Watch a directory for changes and process any new files.

      The files will be processed according to the boolean flags, with the flag
      names corresponding to other image commands.

      By default, all the flags are enabled, which will:

         * Extract JPG files from a CR2.
         * Convert CR2 files to FITS.
         * Plate-solve FITS files.

    Arguments:
      PATH  [required]

    Options:
      --to-jpg / --no-to-jpg          [default: to-jpg]
      --to-fits / --no-to-fits        [default: to-fits]
      --solve / --no-solve            [default: solve]
      --overwrite / --no-overwrite    [default: no-overwrite]
      --remove-cr2 / --no-remove-cr2  [default: no-remove-cr2]
      --help                          Show this message and exit.


image cr2
~~~~~~~~~

Canon ``CR2`` can have a JPG extracted and be converted to FITS files. See the ``--help``
command for each of the specific subcommands for more details.

.. code-block:: bash

    Usage: panoptes-utils image cr2 [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      to-fits  Convert a CR2 image to a FITS, return the new path name.
      to-jpg   Extract a JPG image from a CR2, return the new path name.


image fits
~~~~~~~~~~

FITS files can be easily plate-solved.

.. code-block:: bash

    Usage: panoptes-utils image fits [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      solve  Plate-solve a FITS file.
