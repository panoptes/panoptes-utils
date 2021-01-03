PANOPTES Services
=================

Two services are currently defined, one for the configuration server and
another for working with images.

## Config server

The `panoptes-config-server` is a simple Flask application that acts as
a centralized location for configuration items. There is a cli tool to
query the server as well as APi access (via
`panoptes.utils.config.client`).

The `panoptes-config-server` can be controlled via the included
`docker-compose.yaml` file and uses environment variables to control the
host/port as well as the actual configuration file used.

| env var                | description                                                                                |
|:-----------------------|:-------------------------------------------------------------------------------------------|
| `PANOPTES_CONFIG_HOST` | Host IP address. Default `localhost`. :warning: Use `0.0.0.0` for public server. :warning: |
| `PANOPTES_CONFIG_PORT` | Host port. Default `6563`.                                                                 |
| `PANOPTES_CONFIG_FILE` | The host file to use for configuration. **Required**                                       |

The service can be started via docker-compose as follows:

```
docker-compose -f docker/docker-compose.yaml up
```

## Image tools
