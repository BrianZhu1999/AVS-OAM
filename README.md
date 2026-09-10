# AVS-OAM

Compact Python reference implementation for Cartesian acoustic-vector-sensor (AVS) reception of sparse-aperture acoustic orbital-angular-momentum (OAM) signals.

The code accompanies the study *Acoustic Vector-Sensor Reception for Orbital-Angular-Momentum Sound Communication* and provides executable examples of the finite-ring forward model, pressure-equivalent particle-velocity channels, receiving-matrix analysis, BPSK detection, receiver-offset mismatch, and a gapped-aperture payload.

## Components

- `avs_oam_core.py` - finite-ring OAM field model, Cartesian pressure-equivalent velocity channels, observation selection, column normalization, matrix diagnostics, and maximum-likelihood BPSK helpers.
- `matrix_observability.py` - compares pressure-only, transverse-AVS, and full Cartesian-AVS receiving matrices for full, gapped, and random sparse apertures.
- `known_bpsk_snr.py` - evaluates known-mode BPSK bit-error rate over a range of SNR values.
- `offset_robustness.py` - evaluates BER under receiver-position mismatch with a nominal detector channel.
- `gap_payload_demo.py` - evaluates binary payload recovery through a sparse gapped receiver.

## Requirements

- Python 3.10 or newer
- NumPy

Create an environment and install the dependency:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Run the examples

```bash
python matrix_observability.py
python known_bpsk_snr.py
python offset_robustness.py
python gap_payload_demo.py
```

Each example writes a CSV result file in the current directory.

## Model convention

The default configuration in `OAMConfig` uses a 16-element finite source ring at 3430 Hz, with a 0.12 m source radius, a 0.12 m receive radius, and a nominal propagation distance of 1.2 m. The observation vector is ordered as

```text
[pressure, rho0*c0*vx, rho0*c0*vy, rho0*c0*vz]
```

The examples use the same column-normalization convention for comparing observation modes. Change the configuration and mode sets in the example scripts to explore other sparse-aperture conditions.

## Reproducibility

The examples use explicit NumPy random seeds. Numerical settings such as frame counts and scan grids are defined directly in each example script.

## Citation

If you use this code, please cite the accompanying paper and include the repository URL in your methods or software statement.

