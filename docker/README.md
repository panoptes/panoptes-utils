Docker Images
=============

The PANOPTES utilities are available as a docker image hosted on Google Cloud Registry (GCR):

Image name: `gcr.io/panoptes-exp/panoptes-utils`

Tags: `latest`, `develop`, and `testing`.

### Tags

The `panoptes-utils` image comes in two separate flavors, or tags, that serve different
purposes.  

#### latest

The `latest` image is typically used to run services or to serve as a foundational layer
for other docker images. It includes all the tools required to run the various functions
with the `panoptes-utils` module, including a plate-solver (astrometry.net), `sextractor`,
etc.

#### develop

The `develop` image can be used by developers or anyone wishing to explore the code.
The `bin/panoptes-develop` script is a wrapper that will start up a docker container
instance and launce jupyter-lab from `$PANDIR` automatically. 

There are a few ways to get the development version.

> Note:  See also https://github.com/panoptes/panoptes-tutorials

1) If you have `git` and are comfortable using the command line:

```bash
cd $PANDIR

# Get the repository.
git clone https://github.com/panoptes/panoptes-utils.git
cd panoptes-utils

# Run environment. 
bin/panoptes-develop up
```

2) If you would like to build your own local docker image:

```bash
cd $PANDIR/panoptes-utils
# First build the 'latest' image locally.
docker build -t panoptes-utils:latest -f docker/latest.Dockerfile .

# Then build the develop image locally.
docker build \
  --build-arg base_image=panoptes-utils:latest \
  -t panoptes-utils:develop \
  -f docker/develop.Dockerfile .

# Wait for build to finish...

# Run with new image.
IMAGE=panoptes-utils bin/panoptes-develop up
```

3) If you are using a new system:

> TODO: Document this section.

#### testing

The `testing` image is used for running the automated tests. These are run automatically
on both GitHub and Travis for all code pushes but can also be run locally while doing 
development.

To build the test image:

```bash
docker build -t panoptes-utils:testing -f docker/testing.Dockerfile .
```

To run the test suite locally:

```bash
scripts/testing/test-software.sh
```
