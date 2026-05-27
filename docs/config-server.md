# Config Server (Deprecated)

> **Deprecated:**
> The HTTP config server (`panoptes.utils.config.server`) and its client
> (`panoptes.utils.config.client`) are deprecated as of `panoptes-utils` 0.X and
> will be removed in a future release (tracked in
> [#366](https://github.com/panoptes/panoptes-utils/issues/366)).
>
> Use the **[Config Store](config.md)** instead — it reads config directly from
> the YAML file with no server process required.

---

## Migration

Replace any use of the HTTP client with the config store:

```python
# Before (deprecated)
from panoptes.utils.config.client import get_config, set_config

value = get_config("location.horizon")
set_config("location.horizon", 45)

# After
from panoptes.utils.config.store import get_config, init_config, set_config

init_config("~/.panoptes/config.yaml")  # once at startup
value = get_config("location.horizon")
set_config("location.horizon", 45)
```

Replace CLI usage:

```bash
# Before (deprecated)
panoptes-utils config run --config-file /path/to/config.yaml
panoptes-utils config get location.elevation   # required a running server
panoptes-utils config stop

# After — no server needed
export PANOPTES_CONFIG_FILE=/path/to/config.yaml
panoptes-utils config get location.elevation
panoptes-utils config set location.elevation "3400 m"
```

See the **[Configuration](config.md)** page for full documentation on the config store,
typed models, and the file watcher.

