"""Core finite-ring acoustic OAM and Cartesian AVS receiver utilities.

The scripts in this repository use this file to reproduce the paper's
central numerical claim: co-located pressure and particle-velocity
observations improve sparse-aperture OAM mode separation compared with
pressure-only sampling under a common normalization convention.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np


@dataclass(frozen=True)
class OAMConfig:
    c0: float = 343.0
    rho0: float = 1.21
    f0: float = 3430.0
    n_tx: int = 16
    r_tx: float = 0.12
    r_rx: float = 0.12
    z_rx: float = 1.2
    seed: int = 20260604


OBSERVATION_MODES = {
    "p": (0,),
    "p_vxy": (0, 1, 2),
    "p_vxyz": (0, 1, 2, 3),
}


def source_ring(cfg: OAMConfig) -> tuple[np.ndarray, np.ndarray]:
    theta = np.linspace(0.0, 2.0 * np.pi, cfg.n_tx, endpoint=False)
    points = np.column_stack((cfg.r_tx * np.cos(theta), cfg.r_tx * np.sin(theta), np.zeros(cfg.n_tx)))
    return points, theta


def receiver_ring(
    k: int,
    cfg: OAMConfig,
    array: str = "full",
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> np.ndarray:
    if array == "full":
        theta = np.linspace(0.0, 2.0 * np.pi, k, endpoint=False)
    elif array == "gap":
        gap = 0.55 * np.pi
        theta = np.linspace(gap / 2.0, 2.0 * np.pi - gap / 2.0, k, endpoint=True)
    elif array == "random":
        rng = np.random.default_rng(cfg.seed + 1009 * k)
        theta = np.sort(rng.uniform(0.0, 2.0 * np.pi, size=k))
    else:
        raise ValueError(f"unknown array: {array}")
    points = np.column_stack((cfg.r_rx * np.cos(theta), cfg.r_rx * np.sin(theta), np.full(k, cfg.z_rx)))
    return points + np.asarray(offset, dtype=float)[None, :]


def finite_ring_matrix(receiver_points: np.ndarray, modes: list[int], cfg: OAMConfig) -> np.ndarray:
    """Return component-major rows [p, rho*c*vx, rho*c*vy, rho*c*vz]."""
    src, src_theta = source_ring(cfg)
    omega = 2.0 * np.pi * cfg.f0
    k0 = omega / cfg.c0
    r_vec = receiver_points[:, None, :] - src[None, :, :]
    dist = np.linalg.norm(r_vec, axis=2)
    green = np.exp(1j * k0 * dist) / (4.0 * np.pi * dist)
    grad_factor = green * (1j * k0 - 1.0 / dist) / dist
    n_rx = receiver_points.shape[0]
    mat = np.zeros((4 * n_rx, len(modes)), dtype=np.complex128)
    for col, ell in enumerate(modes):
        weights = np.exp(1j * ell * src_theta)
        pressure = np.sum(green * weights[None, :], axis=1)
        grad = np.sum(grad_factor[:, :, None] * r_vec * weights[None, :, None], axis=1)
        velocity = grad / (1j * omega * cfg.rho0)
        mat[:n_rx, col] = pressure
        mat[n_rx : 2 * n_rx, col] = cfg.rho0 * cfg.c0 * velocity[:, 0]
        mat[2 * n_rx : 3 * n_rx, col] = cfg.rho0 * cfg.c0 * velocity[:, 1]
        mat[3 * n_rx : 4 * n_rx, col] = cfg.rho0 * cfg.c0 * velocity[:, 2]
    return mat


def observation_matrix(raw: np.ndarray, n_rx: int, mode: str) -> np.ndarray:
    rows: list[int] = []
    for comp in OBSERVATION_MODES[mode]:
        rows.extend(range(comp * n_rx, (comp + 1) * n_rx))
    return raw[rows, :]


def column_normalize(a: np.ndarray, reference_norms: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    norms = np.linalg.norm(a, axis=0) if reference_norms is None else reference_norms
    norms = np.maximum(norms, 1e-15)
    return a / norms[None, :], norms


def observability(a: np.ndarray) -> dict[str, float]:
    s = np.linalg.svd(a, compute_uv=False)
    an, _ = column_normalize(a)
    gram = an.conj().T @ an
    offdiag = gram - np.diag(np.diag(gram))
    return {
        "rows": float(a.shape[0]),
        "condition": float(s[0] / max(s[-1], 1e-15)),
        "min_singular": float(s[-1]),
        "mutual_coherence": float(np.max(np.abs(offdiag))),
        "gram_offdiag_energy": float(np.sum(np.abs(offdiag) ** 2)),
    }


def known_bpsk_ml(a_receiver: np.ndarray, y: np.ndarray) -> np.ndarray:
    n_modes = a_receiver.shape[1]
    candidates = np.asarray(list(product([-1.0, 1.0], repeat=n_modes)), dtype=float)
    predicted = candidates @ a_receiver.T
    out = np.zeros((y.shape[0], n_modes), dtype=np.float64)
    for idx, row in enumerate(y):
        err = np.sum(np.abs(predicted - row[None, :]) ** 2, axis=1)
        out[idx] = candidates[int(np.argmin(err))]
    return out


def bpsk_ber(
    a_channel: np.ndarray,
    a_receiver: np.ndarray,
    snr_db: float,
    frames: int = 2000,
    seed: int = 0,
) -> float:
    rng = np.random.default_rng(seed)
    bits = rng.integers(0, 2, size=(frames, a_channel.shape[1]))
    x = 2.0 * bits - 1.0
    clean = x @ a_channel.T
    signal_power = float(np.mean(np.abs(clean) ** 2))
    noise_var = signal_power / (10.0 ** (snr_db / 10.0))
    noise = np.sqrt(noise_var / 2.0) * (
        rng.standard_normal(clean.shape) + 1j * rng.standard_normal(clean.shape)
    )
    x_hat = known_bpsk_ml(a_receiver, clean + noise)
    return float(np.mean((x_hat > 0.0) != bits))


def build_channel(
    modes: list[int],
    k: int,
    cfg: OAMConfig,
    obs: str,
    array: str = "full",
    offset: tuple[float, float, float] = (0.0, 0.0, 0.0),
    reference_norms: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    rx = receiver_ring(k, cfg, array=array, offset=offset)
    raw = finite_ring_matrix(rx, modes, cfg)
    mat = observation_matrix(raw, k, obs)
    return column_normalize(mat, reference_norms)
