"""File-watching utilities for PANOPTES configuration.

Provides ``ConfigWatcher``, which monitors a YAML config file for changes
and calls registered callbacks with the updated config dict.

Usage::

    from panoptes.utils.config.watcher import ConfigWatcher

    def on_location_change(config):
        print("Location changed:", config["location"])

    watcher = ConfigWatcher("path/to/config.yaml")
    watcher.register("location", on_location_change)
    watcher.start()

    # ... run your application ...

    watcher.stop()

The ``ConfigWatcher`` can also be used as a context manager::

    with ConfigWatcher("path/to/config.yaml") as watcher:
        watcher.register("location", on_location_change)
        # watcher is active for the duration of the block
"""

from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from loguru import logger

from panoptes.utils.config.helpers import load_config


class ConfigWatcher:
    """Watches a YAML config file and fires callbacks on changes.

    Callbacks are registered per top-level config key. When the file
    changes, the new config is loaded and each callback whose key has
    a different value is invoked with the full updated config dict.

    Use ``register(None, callback)`` to receive *all* changes regardless
    of which key changed.

    Args:
        config_file: Path to the YAML config file to watch.
        load_local: Whether to also load ``<name>_local.yaml`` overrides.
            Defaults to True, matching ``load_config`` behaviour.

    Examples:
        >>> import tempfile, pathlib, time
        >>> tmp = pathlib.Path(tempfile.mktemp(suffix=".yaml"))
        >>> _ = tmp.write_text("name: test\\n")
        >>> received = []
        >>> watcher = ConfigWatcher(tmp)
        >>> watcher.register(None, received.append)
        >>> watcher.start()  # doctest: +SKIP
        >>> _ = tmp.write_text("name: changed\\n")  # doctest: +SKIP
        >>> time.sleep(0.5)  # doctest: +SKIP
        >>> watcher.stop()  # doctest: +SKIP
        >>> tmp.unlink()  # doctest: +SKIP
        >>> received[-1]["name"]  # doctest: +SKIP
        'changed'
    """

    def __init__(self, config_file: str | Path, load_local: bool = True) -> None:
        self._config_file = Path(config_file)
        self._load_local = load_local
        self._callbacks: dict[str | None, list[Callable]] = defaultdict(list)
        self._current_config: dict = {}
        self._observer = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, key: str | None, callback: Callable[[dict], None]) -> None:
        """Register a callback for changes to a top-level config key.

        Args:
            key: The top-level config key to watch (e.g. ``"location"``),
                or ``None`` to be notified of *any* change.
            callback: A callable that receives the full updated config dict.
        """
        self._callbacks[key].append(callback)
        logger.debug(f"Registered config callback for key={key!r}")

    def start(self) -> None:
        """Start watching the config file for changes."""
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError as e:
            raise ImportError(
                "watchdog is required for ConfigWatcher. Install it with: pip install watchdog"
            ) from e

        self._current_config = self._load()

        watcher = self

        class _Handler(FileSystemEventHandler):
            def _matches(self, path: str) -> bool:
                return Path(path).resolve() == watcher._config_file.resolve()

            def on_modified(self, event):
                if self._matches(event.src_path):
                    watcher._on_file_changed()

            def on_created(self, event):
                if self._matches(event.src_path):
                    watcher._on_file_changed()

            def on_moved(self, event):
                # Editors that do atomic saves write a temp file then rename it
                if self._matches(event.dest_path):
                    watcher._on_file_changed()

            def on_deleted(self, event):
                if self._matches(event.src_path):
                    logger.warning(f"Config file deleted: {watcher._config_file}")

        self._observer = Observer()
        self._observer.schedule(
            _Handler(),
            path=str(self._config_file.parent),
            recursive=False,
        )
        self._observer.start()
        logger.info(f"ConfigWatcher started: watching {self._config_file}")

    def stop(self) -> None:
        """Stop watching the config file."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            logger.info(f"ConfigWatcher stopped: {self._config_file}")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "ConfigWatcher":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        return load_config(self._config_file, load_local=self._load_local)

    def _on_file_changed(self) -> None:
        try:
            new_config = self._load()
        except Exception as exc:
            logger.warning(f"ConfigWatcher: failed to reload {self._config_file}: {exc}")
            return

        changed_keys = {
            key
            for key in set(new_config) | set(self._current_config)
            if new_config.get(key) != self._current_config.get(key)
        }

        if not changed_keys:
            return

        logger.debug(f"Config changed: {changed_keys}")
        self._current_config = new_config

        notified: set[Callable] = set()

        def _fire(cb: Callable) -> None:
            if cb in notified:
                return
            try:
                cb(new_config)
            except Exception as exc:
                logger.warning(f"ConfigWatcher: callback {cb!r} raised: {exc}")
            notified.add(cb)

        for key in changed_keys:
            for cb in self._callbacks.get(key, []):
                _fire(cb)

        for cb in self._callbacks.get(None, []):
            _fire(cb)
