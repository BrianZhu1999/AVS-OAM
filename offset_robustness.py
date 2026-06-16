"""Receiver-offset mismatch test with a nominal receiver model."""

from __future__ import annotations

import csv

from avs_oam_core import OAMConfig, OBSERVATION_MODES, bpsk_ber, build_channel


def main() -> None:
    cfg = OAMConfig()
    modes = [-2, -1, 1, 2]
    offsets_mm = [0, 2, 5, 10, 15, 20]
    snr_db = 10.0
    rows = []
    for obs in OBSERVATION_MODES:
        nominal, norms = build_channel(modes, 8, cfg, obs, array="gap")
        for dx_mm in offsets_mm:
            actual, _ = build_channel(
                modes,
                8,
                cfg,
                obs,
                array="gap",
                offset=(dx_mm * 1e-3, -0.4 * dx_mm * 1e-3, 0.5 * dx_mm * 1e-3),
                reference_norms=norms,
            )
            ber = bpsk_ber(actual, nominal, snr_db, frames=3000, seed=cfg.seed + dx_mm + len(obs))
            rows.append({"observation": obs, "offset_mm": dx_mm, "SNR_dB": snr_db, "BER": ber})

    with open("offset_robustness.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation", "offset_mm", "SNR_dB", "BER"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote offset_robustness.csv")


if __name__ == "__main__":
    main()
