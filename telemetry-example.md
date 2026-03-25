# IPython log file

```python
from panoptes.utils.telemetry import TelemetryClient

client = TelemetryClient()
client.current()
# {'stream': 'system', 'current': {}}

client.ready()
# {'ready': True,
#  'run_active': False,
#  'version': '0.2.54.dev41+g80defd029.d20260317'}

client.post_event("weather", {"sky": "clear", "wind_mps": 2.1}, meta={"source": "demo"})
# {'seq': 1,
#  'ts': '2026-03-17T23:52:07.377Z',
#  'stream': 'system',
#  'type': 'weather',
#  'data': {'sky': 'clear', 'wind_mps': 2.1},
#  'meta': {'source': 'demo'}}

client.current()
# {'stream': 'system',
#  'current': {'weather': {'seq': 1,
#    'ts': '2026-03-17T23:52:07.377Z',
#    'stream': 'system',
#    'type': 'weather',
#    'data': {'sky': 'clear', 'wind_mps': 2.1},
#    'meta': {'source': 'demo'}}}}

client.start_run("/tmp/panoptes-run-001", meta={"run_id": "001"})
# {'run_dir': '/tmp/panoptes-run-001',
#  'meta': {'run_id': '001'},
#  'started_at': '2026-03-17T23:52:16.809Z'}

client.post_event("status", {"state": "running"})
# {'seq': 1,
#  'ts': '2026-03-17T23:52:22.756Z',
#  'stream': 'run',
#  'type': 'status',
#  'data': {'state': 'running'},
#  'meta': {}}

client.current()
# {'stream': 'run',
#  'current': {'status': {'seq': 1,
#    'ts': '2026-03-17T23:52:22.756Z',
#    'stream': 'run',
#    'type': 'status',
#    'data': {'state': 'running'},
#    'meta': {}}}}

client.stop_run()
# {'run_dir': '/tmp/panoptes-run-001',
#  'meta': {'run_id': '001'},
#  'started_at': '2026-03-17T23:52:16.809Z'}

client.shutdown()
# {'shutting_down': True}
```
