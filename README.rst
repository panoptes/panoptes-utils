|PyPI version| |Build Status| |codecov| |Documentation Status|

PANOPTES Utils
--------------

-  `PANOPTES Utils`_
-  `Getting`_

   -  `pip`_
   -  `Docker`_

-  `Using`_

   -  `Modules`_
   -  `Services`_

      -  `Config Server`_
      -  `Messaging Hub`_

-  `Development`_

   -  `Environment`_
   -  `Logging`_

Utility functions for use within the PANOPTES ecosystem and for general
astronomical processing.

This library defines a number of modules that contain useful functions
as well as a few `services`_.

See the full documentation at: https://panoptes-utils.readthedocs.io

Getting
-------

See `Docker`_ for ways to run ``panoptes-utils`` services without
installing to your host computer.

pip
~~~

To install type:

.. code:: bash

   pip install panoptes-utils

Docker
~~~~~~

Docker containers are available for running the ``panoptes-utils``
module and associated services, which also serve as the base container
for all other PANOPTES related containers.

See our `Docker documentation`_ for details.

Using
-----

Modules
~~~~~~~

The modules can be used as helper utilities anywhere you would like. See
the complete documentation for details:
https://panoptes-utils.readthedocs.io/en/latest/.

Services
~~~~~~~~

The services can be run either from a `docker`_ image or from the
installed script, as described below.

Config Server
^^^^^^^^^^^^^

A simple config param server. Runs as a Flask microservice that delivers
JSON documents in response to requests for config key items.

Can be run from the installed script (defaults to
``http://localhost:6563/get-config``):

.. code:: bash

   $ bin/panoptes-config-server
    * Serving Flask app "panoptes.utils.config.server" (lazy loading)
    * Environment: production
      WARNING: This is a development server. Do not use it in a production deployment.
      Use a production WSGI server instead.
    * Debug mode: off

Or inside a python process:

.. code:: python

   >>> from panoptes.utils.config.server import config_server
   >>> from panoptes.utils.config import client

   >>> server_process=config_server()

   >>> client.get_config('location.horizon')
   30.0

   >>> server_process.terminate()  # Or just exit notebook/console

For more details and usage examples, see the `config server README`_.

Messaging Hub
^^^^^^^^^^^^^

The messaging hub is responsible for relaying zeromq messages between
the various components of a PANOPTES system. Running the Messaging Hub
will set up a forwarding service that allows for an arbitrary number of
publishers and subscribers.

.. code:: bash

   panoptes-messaging-hub --from-config

Development
-----------

Environment
~~~~~~~~~~~

There is a docker development environment that has a number of support
modules installed. This also defaults to running a ``jupyter-lab``
instance with the ``$PANDIR`` folder as the root.

You should have all ``panoptes`` repositories for development (maybe
``POCS``, ``panoptes-utils``, ``panoptes-tutorials``) inside the
``$PANDIR`` folder (default ``/var/panoptes``). Ideally you have just
run the install script at **TODO: reference install script here.**.

You can then start the development environment by:

.. code:: sh

   bin/panoptes-develop up

You can then connect to the provided url in your browser. The default
password is ``panotpes``, which is not supplied for security purposes
but just to allow access.

The environment can be stopped with:

.. code:: sh

   bin/panoptes-develop down

Logging
~~~~~~~

The ``panoptes-utils`` module uses `loguru`_ for logging, which also
serves as the basis for the POCS logger (see `Logger`_).

To access the logs for the module, you can import directly from the
``logger`` module, i.e., ``from panoptes.utils.logger import logger``.
This is a simple wrapper around ``luguru`` with no extra configuration:

::

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


.. _PANOPTES Utils: #panoptes-utils
.. _Getting: #getting
.. _pip: #pip
.. _Docker: #docker
.. _Using: #using
.. _Modules: #modules
.. _Services: #services
.. _Config Server: #config-server
.. _Messaging Hub: #messaging-hub
.. _Development: #development
.. _Environment: #environment
.. _Logging: #logging
.. _services: #services
.. _Docker documentation: https://panoptes-utils.readthedocs.io/en/latest/docker.html
.. _docker: #docker
.. _config server README: panoptes/utils/config/README.md
.. _loguru: https://github.com/Delgan/loguru
.. _Logger: #logger

.. |PyPI version| image:: https://badge.fury.io/py/panoptes-utils.svg
   :target: https://badge.fury.io/py/panoptes-utils
.. |Build Status| image:: https://travis-ci.com/panoptes/panoptes-utils.svg?branch=develop
   :target: https://travis-ci.com/panoptes/panoptes-utils
.. |codecov| image:: https://codecov.io/gh/panoptes/panoptes-utils/branch/develop/graph/badge.svg
   :target: https://codecov.io/gh/panoptes/panoptes-utils
.. |Documentation Status| image:: https://readthedocs.org/projects/panoptes-utils/badge/?version=latest
   :target: https://panoptes-utils.readthedocs.io/en/latest/?badge=latest
