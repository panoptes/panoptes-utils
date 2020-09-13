PANOPTES Utils Image
====================

The `panoptes-utils` image is built on top of `panoptes-base` and installs 
the `panoptes-utils` module (in editable mode) from the appropriate branch on Github.

By default the module is installed with the `testing` and `google` extras 
(i.e `pip install -e ".[testing,google]"`).

# Image Details

Image name: `gcr.io/panoptes-exp/panoptes-utils`

Tags: `latest`, `develop`

Platforms: `amd64` (`x86_64`) as well as `arm64` (`aarch64`). Other builds are 
possible but not provided by default.

Workdir: `$PANDIR/panoptes-utils` (default is `/var/panoptes/panoptes-utils`)

Entrypoint: `/usr/bin/zsh` as `$PANUSER` (default `panoptes`) user via `gosu`. See 
`resources/docker/entrypoint.sh` for details.

Cmd: The default `CMD` is a `zsh` with a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) 
activated (named `panoptes`) and the `WORKDIR` is `PANDIR`.

# Building the image locally

> Note: Make sure you have your `$PANDIR` environment variable set 
> to something like: `PANDIR=/var/panoptes`

You can build a local copy of the images for testing. The easiest way is:

```bash
INCLUDE_BASE=true scripts/setup-local-environment.sh
``` 

> Note that the `.git` folder is passed to the Docker build context when running locally.
This is because our `pyscaffold` package tool relies on `setuptools_scm` for version
numbers, which are ultimately based off the current code according to git.  This means
the local `develop` image will likely be much larger than the official `latest` image.
>
> In practice this doesn't matter because when you run the local image you usually want
> to mount the working directory anyway, e.g.
>
>     docker run -it --rm \
>         -v "${PANDIR}/panoptes-utils":/var/panoptes/panoptes-utils \
>         panoptes-utils:develop 

### Testing local image and code

After building the `develop` image (see above), you can run the tests inside a docker container via:

```bash
scripts/testing/test-software.sh
```
