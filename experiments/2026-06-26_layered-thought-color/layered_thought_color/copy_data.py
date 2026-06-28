"""Copy visible PLM benchmark data into the experiment."""

from __future__ import annotations

import json

from .data import copy_visible_benchmark


def main() -> None:
    manifest = copy_visible_benchmark()
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

