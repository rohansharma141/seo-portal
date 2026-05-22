"""Pytest setup. Runs before any test module imports the app, so the
config singleton sees these values.

- The Section 9 scheduler is disabled: otherwise every `TestClient(app)`
  would start background cron jobs via the lifespan.
- PageSpeed Insights (Addendum v1.2) is disabled: otherwise `run_audit`
  in the pipeline tests would make slow (10-30s) network calls to Google.
  PSI logic is tested directly in test_pagespeed.py with a mocked fetch.
"""

import os

os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("PSI_ENABLED", "false")
