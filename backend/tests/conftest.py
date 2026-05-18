"""Pytest setup. Runs before any test module imports the app, so the
config singleton sees these values.

The Section 9 scheduler is disabled in the test process: otherwise every
`TestClient(app)` would start background cron jobs via the lifespan.
"""

import os

os.environ.setdefault("SCHEDULER_ENABLED", "false")
