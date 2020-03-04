#!/usr/bin/env python
# Licensed under an MIT style license - see LICENSE.txt

from configparser import ConfigParser
from setuptools import setup, find_namespace_packages

import itertools

import versioneer


# Get some values from the setup.cfg
conf = ConfigParser()
conf.read(['setup.cfg'])
metadata = dict(conf.items('metadata'))

AUTHOR = metadata.get('author', '')
AUTHOR_EMAIL = metadata.get('author_email', '')
DESCRIPTION = metadata.get('description', '')
KEYWORDS = metadata.get('keywords', 'Project PANOPTES')
LICENSE = metadata.get('license', 'unknown')
LONG_DESCRIPTION = metadata.get('long_description', '')
NAME = metadata.get('name', 'panoptes-utils')
PACKAGENAME = metadata.get('package_name', 'packagename')
URL = metadata.get('url', 'https://projectpanoptes.org')

modules = {
    'required': [
        'astroplan>=0.6',
        'astropy>=4.0.0',
        'Flask',
        'loguru',
        'matplotlib>=3.0.0',
        'numpy',
        'photutils',
        'pyserial',
        'python-json-logger',
        'python-dateutil',
        'PyYAML',
        'pyzmq',
        'ruamel.yaml>=0.15',
        'scalpl',
        'scikit-image',
        'scipy',
        'versioneer'
    ],
    'social': ['requests', 'tweepy'],
    'testing': [
        'codecov',
        'coverage',
        'coveralls',
        'mocket',
        'pycodestyle',
        'pytest',
        'pytest-cov',
        'pytest-remotedata>=0.3.1'
    ],
}


setup(name=NAME,
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      keywords=KEYWORDS,
      python_requires='>=3.6',
      setup_requires=['pytest-runner'],
      tests_require=modules['testing'],
      scripts=[
          'bin/cr2-to-jpg',
          'bin/panoptes-config-server',
          'bin/panoptes-messaging-hub',
          'bin/panoptes-solve-field',
      ],
      install_requires=modules['required'],
      extras_require={
          'social': modules['social'],
          'testing': modules['testing'],
          'all': list(set(itertools.chain.from_iterable(modules.values())))
      },
      packages=find_namespace_packages(exclude=['tests', 'test_*']),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX',
          'Programming Language :: C',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3 :: Only',
          'Topic :: Scientific/Engineering :: Astronomy',
          'Topic :: Scientific/Engineering :: Physics',
      ],
      )
