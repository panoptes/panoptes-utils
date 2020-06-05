.. _docker:

======
Docker
======

The PANOPTES utilities are available as a docker image that can be built
locally for testing purposes. We also use containers based off
``latest`` in the Google Cloud Registry (GCR):

Image name: ``panoptes-utils``

Tags: ``latest`` and ``develop``.

Tags
~~~~

The ``panoptes-utils`` image comes in two separate flavors, or tags,
that serve different purposes.

latest
^^^^^^

The ``latest`` image is typically used to run services or to serve as a
foundational layer for other docker images. It includes all the tools
required to run the various functions with the ``panoptes-utils``
module, including a plate-solver (astrometry.net), ``sextractor``, etc.

The ``latest`` image is also used as a base image for the
`POCS <https://github.com/panoptes/POCS>`__ images.

develop
^^^^^^^

The ``develop`` image is used for running the automated tests against
the ``develop`` branch. These are run automatically on both GitHub and
Travis for all code pushes but can also be run locally while doing
development.

Building
~~~~~~~~

To build the test image:

.. code:: bash

    docker/setup-local-environment.sh

Running
~~~~~~~

To run the test suite locally:

.. code:: bash

    scripts/testing/test-software.sh

