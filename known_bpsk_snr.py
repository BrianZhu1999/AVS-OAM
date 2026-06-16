"""Known-mode BPSK detection versus SNR."""

from __future__ import annotations

import csv

from avs_oam_core import OAMConfig, OBSERVATION_MODES, bpsk_ber, build_channel


def main() -> None:
    cfg = OAMConfig()
    modes = [-2, -1, 1, 2]
    snr_values = [-5, 0, 5, 10, 15, 20]
    rows = []
    for obs in OBSERVATION_MODES:
        a, _ = build_channel(modes, 8, cfg, obs, array="gap")
        for snr in snr_values:
            ber = bpsk_ber(a, a, snr, frames=3000, seed=cfg.seed + int(10 * snr) + len(obs))
            rows.append({"observation": obs, "SNR_dB": snr, "BER": ber})

    with open("known_bpsk_snr.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation", "SNR_dB", "BER"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote known_bpsk_snr.csv")


if __name__ == "__main__":
    main()
