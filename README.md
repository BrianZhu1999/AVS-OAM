# AVS-OAM

Minimal core scripts for the paper idea: Cartesian acoustic vector sensors (pressure plus particle velocity) improve sparse-aperture acoustic OAM reception compared with pressure-only sampling.

This trimmed repository intentionally omits the manuscript folder, formal figure folders, LaTeX build files, old plotting scripts, and large intermediate outputs. It keeps only the scripts needed to reproduce the main numerical mechanisms.

## Files

- `avs_oam_core.py` - finite-ring OAM forward model, pressure-equivalent Cartesian velocity channels, observation selection, matrix metrics, and BPSK receiver helpers.
- `matrix_observability.py` - compares pressure-only, transverse AVS, and full Cartesian AVS receiving matrices.
- `known_bpsk_snr.py` - known-mode BPSK BER versus SNR.
- `offset_robustness.py` - BER under receiver-position mismatch while using a nominal receiver model.
- `gap_payload_demo.py` - small binary payload recovery through a sparse gapped receiver.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python matrix_observability.py
python known_bpsk_snr.py
python offset_robustness.py
python gap_payload_demo.py
```

Each script writes a CSV file in the repository root.

