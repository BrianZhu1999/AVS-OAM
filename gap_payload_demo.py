"""Small binary payload demo over a gapped sparse OAM receiver."""

from __future__ import annotations

import csv

import numpy as np

from avs_oam_core import OAMConfig, bpsk_ber, build_channel, known_bpsk_ml


def payload_bits() -> np.ndarray:
    img = np.zeros((16, 16), dtype=int)
    img[2:14, 2:4] = 1
    img[2:4, 2:10] = 1
    img[7:9, 2:9] = 1
    img[2:14, 11:13] = 1
    img[12:14, 5:13] = 1
    img[9:12, 8:10] = 1
    return img.reshape(-1)


def transmit_payload(a: np.ndarray, snr_db: float, seed: int) -> float:
    bits = payload_bits()
    n_modes = a.shape[1]
    pad = (-len(bits)) % n_modes
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=int)])
    symbols = 2.0 * bits.reshape(-1, n_modes) - 1.0
    clean = symbols @ a.T
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_var = signal_power / (10.0 ** (snr_db / 10.0))
    rng = np.random.default_rng(seed)
    noise = np.sqrt(noise_var / 2.0) * (
        rng.standard_normal(clean.shape) + 1j * rng.standard_normal(clean.shape)
    )
    decoded = known_bpsk_ml(a, clean + noise)
    decoded_bits = (decoded.reshape(-1) > 0.0).astype(int)[:256]
    return float(np.mean(decoded_bits != payload_bits()))


def main() -> None:
    cfg = OAMConfig()
    modes = [-2, -1, 1, 2]
    rows = []
    for obs in ("p", "p_vxy", "p_vxyz"):
        a, _ = build_channel(modes, 8, cfg, obs, array="gap")
        for snr in (0, 3, 6, 9):
            rows.append(
                {
                    "observation": obs,
                    "SNR_dB": snr,
                    "payload_BER": transmit_payload(a, snr, cfg.seed + snr + len(obs)),
                    "random_BER_check": bpsk_ber(a, a, snr, frames=1000, seed=cfg.seed + 33 + snr),
                }
            )

    with open("gap_payload_demo.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["observation", "SNR_dB", "payload_BER", "random_BER_check"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote gap_payload_demo.csv")


if __name__ == "__main__":
    main()
