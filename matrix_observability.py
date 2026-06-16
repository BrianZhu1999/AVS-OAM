"""Compare pressure-only and AVS receiving matrices."""

from __future__ import annotations

import csv

from avs_oam_core import OAMConfig, OBSERVATION_MODES, build_channel, observability


def main() -> None:
    cfg = OAMConfig()
    modes = [-4, -3, -2, -1, 1, 2, 3, 4]
    rows = []
    for array in ("full", "gap", "random"):
        for k in (6, 8, 12):
            for obs in OBSERVATION_MODES:
                a, _ = build_channel(modes, k, cfg, obs, array=array)
                row = {"array": array, "K": k, "observation": obs}
                row.update(observability(a))
                rows.append(row)

    fields = ["array", "K", "observation", "rows", "condition", "min_singular", "mutual_coherence", "gram_offdiag_energy"]
    with open("matrix_observability.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print("wrote matrix_observability.csv")


if __name__ == "__main__":
    main()
