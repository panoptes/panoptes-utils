==================
PANOPTES Utilities
==================

|PyPI version| |Build Status| |codecov| |Documentation Status|

Utility functions for use within the PANOPTES ecosystem and for general astronomical processing.

This library defines a number of modules that contain useful functions as well as a few services.

Getting
=======

See :ref:`docker` for ways to run ``panoptes-utils`` services without installing to your host computer.

pip
---

To install type:

.. code:: bash

   pip install panoptes-utils

Docker
------

Docker containers are available for running the ``panoptes-utils``
module and associated services, which also serve as the base container
for all other PANOPTES related containers.

See the :ref:`docker` page for details.

Using
=====

Modules
-------

The modules can be used as helper utilities anywhere you would like.

Services
--------

The services can be run either from a :ref:`docker` image or from the
installed script, as described below.

Config Server
~~~~~~~~~~~~~

A simple config param server. Runs as a Flask microservice that delivers
JSON documents in response to requests for config key items.

Can be run from the installed script (defaults to ``http://localhost:6563/get-config``):

.. code::
    bash

    $ panoptes-config-server -h
    usage: panoptes-config-server [-h] [--host HOST] [--port PORT] [--public] [--config-file CONFIG_FILE] [--no-save] [--ignore-local] [--debug]

    Start the config server for PANOPTES

    optional arguments:
      -h, --help            show this help message and exit
      --host HOST           Host name, defaults to local interface.
      --port PORT           Local port, default 6563
      --public              If server should be public, default False. Note: inside a docker container set this to True to expose to host.
      --config-file CONFIG_FILE
                            Config file, default $PANDIR/conf_files/pocs.yaml
      --no-save             Prevent auto saving of any new values.
      --ignore-local        Ignore the local config files, default False. Mostly for testing.
      --debug               Debug


Or inside a python process:

.. code::
    python

    >>> from panoptes.utils.config.server import config_server
    >>> from panoptes.utils.config import client

    >>> server_process=config_server()

    >>> client.get_config('location.horizon')
    30.0

    >>> server_process.terminate()  # Or just exit notebook/console

For more details and usage examples, see the :ref:`config-server`.

Development
===========

Environment
-----------

Most users of ``panoptes-utils`` who need the full environment will also
want the fulle `POCS Environment`_.

Logging
-------

The ``panoptes-utils`` module uses `loguru`_ for logging, which also
serves as the basis for the POCS logger (see `Logger`_).

To access the logs for the module, you can import directly from the
``logger`` module, i.e., ``from panoptes.utils.logger import logger``.
This is a simple wrapper around ``luguru`` with no extra configuration:

.. code-block::
    python

   >>> from panoptes.utils import CountdownTimer
   >>> # No logs by default
   >>> t0 = CountdownTimer(5)
   >>> t0.sleep()
   False

   >>> # Enable the logs
   >>> from panoptes.utils.logger import logger
   >>> logger.enable('panoptes')

   >>> t1 = CountdownTimer(5)
   2020-03-04 06:42:50 | DEBUG | panoptes.utils.time:restart:162 - Restarting Timer (blocking) 5.00/5.00
   >>> t1.sleep()
   2020-03-04 06:42:53 | DEBUG | panoptes.utils.time:sleep:183 - Sleeping for 2.43 seconds
   False

Contents
========

.. toctree::
    :maxdepth: 2

    Config Server <config-server>
    Docker <docker>
    License <license>
    Authors <authors>
    Changelog <changelog>
    Module Reference <api/modules>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _toctree: http://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html
.. _reStructuredText: http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _references: http://www.sphinx-doc.org/en/stable/markup/inline.html
.. _Python domain syntax: http://sphinx-doc.org/domains.html#the-python-domain
.. _Sphinx: http://www.sphinx-doc.org/
.. _Python: http://docs.python.org/
.. _Numpy: http://docs.scipy.org/doc/numpy
.. _SciPy: http://docs.scipy.org/doc/scipy/reference/
.. _matplotlib: https://matplotlib.org/contents.html#
.. _Pandas: http://pandas.pydata.org/pandas-docs/stable
.. _Scikit-Learn: http://scikit-learn.org/stable
.. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
.. _Google style: https://github.com/google/styleguide/blob/gh-pages/pyguide.md#38-comments-and-docstrings
.. _NumPy style: https://numpydoc.readthedocs.io/en/latest/format.html
.. _classical style: http://www.sphinx-doc.org/en/stable/domains.html#info-field-lists
.. _PANOPTES Utils: #panoptes-utils
.. _Getting: #getting
.. _pip: #pip
.. _Using: #using
.. _Modules: #modules
.. _Services: #services
.. _Config Server: #config-server
.. _Development: #development
.. _Environment: #environment
.. _Logging: #logging
.. _services: #services
.. _loguru: https://github.com/Delgan/loguru
.. _Logger: #logger
.. _POCS Environment: https://pocs.readthedocs.io/en/latest/#pocs-environment

.. |PyPI version| image:: https://badge.fury.io/py/panoptes-utils.svg
   :target: https://badge.fury.io/py/panoptes-utils
.. |Build Status| image:: https://travis-ci.com/panoptes/panoptes-utils.svg?branch=develop
   :target: https://travis-ci.com/panoptes/panoptes-utils
.. |codecov| image:: https://codecov.io/gh/panoptes/panoptes-utils/branch/develop/graph/badge.svg
   :target: https://codecov.io/gh/panoptes/panoptes-utils
.. |Documentation Status| image:: https://readthedocs.org/projects/panoptes-utils/badge/?version=latest
   :target: https://panoptes-utils.readthedocs.io/en/latest/?badge=latest
