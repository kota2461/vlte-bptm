"""Deterministic timestamps for generated artifacts.

Generator scripts embed a ``generated_at`` / ``frozen_at`` / ``measured_at``
field in their output. When that value is a live wall clock, regenerating an
otherwise-identical artifact rewrites the file, so every test run (which
regenerates artifacts) leaves tracked files dirty and the committed copy can
never be confirmed canonical.

These helpers honour the reproducible-builds ``SOURCE_DATE_EPOCH`` convention:
when that environment variable is set (the test suite sets it; see
``tests/conftest.py``), the timestamp is derived from it and is therefore
stable across runs. When it is unset, behaviour is unchanged -- a live UTC
timestamp -- so ad-hoc manual runs still record real authoring time.

The environment variable is inherited by subprocesses, so generators that the
test suite launches via ``subprocess.run`` pick up the frozen clock too.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

_EPOCH_ENV = "SOURCE_DATE_EPOCH"


def reproducible_now(*, tz: timezone = timezone.utc) -> datetime:
    """Return ``datetime.now`` unless ``SOURCE_DATE_EPOCH`` pins it."""
    epoch = os.environ.get(_EPOCH_ENV)
    if epoch:
        return datetime.fromtimestamp(int(epoch), tz=tz)
    return datetime.now(tz)


def reproducible_now_iso(*, tz: timezone = timezone.utc) -> str:
    """ISO-8601 string form of :func:`reproducible_now`."""
    return reproducible_now(tz=tz).isoformat()
