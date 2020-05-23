#!/usr/bin/env python
# Licensed under an MIT style license - see LICENSE.txt

from configparser import ConfigParser
from setuptools import setup, find_namespace_packages

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
        'coverage',  # testing
        'Flask',
        'google-cloud-bigquery[pandas,pyarrow]',
        'google-cloud-storage',
        'holoviews',
        'hvplot',
        'loguru',
        'matplotlib>=3.1.3',
        'mocket',  # testing
        'numpy',
        'pandas',
        'pendulum',
        'photutils',
        'Pillow',
        'pycodestyle',  # testing
        'pyserial',
        'pytest',  # testing
        'pytest-cov',  # testing
        'pytest-remotedata>=0.3.1',  # testing
        'python-dateutil',
        'PyYAML',
        'pyzmq',
        'requests',  # social
        'ruamel.yaml>=0.15',
        'scalpl',
        'scipy',
        'setuptools-scm',
        'tweepy',  # social
        'versioneer',
    ],
}

setup(name=NAME,
      use_scm_version=True,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      keywords=KEYWORDS,
      python_requires='>=3.7',
      setup_requires=['pytest-runner', 'setuptools_scm'],
      tests_require=modules['required'],
      scripts=[
          'bin/cr2-to-jpg',
          'bin/panoptes-config-server',
          'bin/panoptes-messaging-hub',
          'bin/panoptes-solve-field',
          'bin/panoptes-develop',
      ],
      install_requires=modules['required'],
      packages=find_namespace_packages(include=['panoptes.utils.*'],
                                       exclude=['tests', 'test_*']),
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
      zip_safe=False
      )
