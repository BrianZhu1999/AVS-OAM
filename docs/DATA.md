# Website data and conventions

The [English research explorer](https://brianzhu1999.github.io/AVS-OAM/) accompanies *Acoustic vector-sensor reception for orbital-angular-momentum sound communication*. The page presents source-data visualizations and recorded numerical results from the study.

## Data map

| Explorer | Public data | Origin and display treatment |
|---|---|---|
| Acoustic field | `data/field_samples.npz`, `fields.json` | Fig. 2 complex fields; every third point of a 301 × 301 grid. Raw pressure and pressure-equivalent velocity are retained in the NPZ. JSON values use the full-grid 99.5th-percentile pressure amplitude and joint transverse-velocity amplitude as separate, per-mode display scales. |
| Co-located receiver | `data/receiver_matrix.npz`, `receiver.json` | Evaluated with the public `avs_oam_core.py` finite-ring model for S₄ and K = 5. No noise samples are added. |
| Codeword geometry | `data/codeword_distances.csv`, `codewords.json` | Appendix Fig. A1 pairwise squared distances. Classical MDS produces independent 2D projections; codeword IDs enumerate `itertools.product([-1, 1], repeat=4)`. Distances always refer to the full complex observation space. |
| SNR sweep | `data/snr.csv` | Fig. 3; pressure nonorthogonality ε = 0.35; 200000 frames per point. |
| Receiver offset | `data/offset_nominal.csv`, `offset_calibrated.csv` | Figs. 5 and 7; SNR = 6 dB; 200000 frames per point. |
| Propagation distance | `data/distance.csv` | Fig. 8; nominal SNR = 0 dB at z₀ = 1.2 m; normalization fixed at z₀, with the actual-distance channel used by the detector. |
| Pilot calibration | `data/pilots.csv` | Fig. 10; training/data SNR = 5 dB; 6 repeats, 50000 data frames per repeat. |
| Hardware errors | `data/hardware.csv` | Raw sweep underlying Fig. 13; transmitter or sensor errors, 7 amplitude values, 7 phase values, 8 SNR values, 3 mode sets and 3 observation strategies; 2 repeats, 8000 frames per repeat. |
| Image recovery | `data/payload.npz`, `payload_metrics.csv` | Fig. 14; original and three exact 768 × 1024 binary arrays; S₄, K = 6, 90° gap, SNR = 3 dB. |

CSV files are byte-for-byte copies of the manuscript source exports. JSON files provide browser-friendly copies of the values. The [source manifest](data/source_manifest.json) records the original basenames, SHA-256 hashes, transformations and public data checksums.

## Physical model

The time convention is `exp(-i omega t)`. The 16-element source ring operates at 3430 Hz in a free field with c₀ = 343 m/s and ρ₀ = 1.21 kg/m³. Both nominal rings have radius 0.12 m; the nominal range is 1.2 m. Cartesian pressure-equivalent velocity is `v_tilde = rho0*c0*v`. Matrix rows are component-major: all K pressure rows, then K rows of each velocity component. The website labels physical receiving points 1 through K and codewords 0 through 15.

The receiver module normalizes the selected physical matrix columns to equal received-mode power, then multiplies each included velocity row by √3. There is no further column normalization. The implied isotropic ambient-noise covariance is `diag(I_K, I_K/3, I_K/3, I_K/3)` for full AVS: the sum of the three velocity noise energies equals the pressure noise energy. The matrix module's full-space codeword distances agree with the Appendix A1 distances; `tools/verify_site_data.py` checks this correspondence.

The root-level compact reference simulations provide a short, executable introduction to the model. Their simplified normalization/noise examples have their own settings. Website performance results come from the recorded CSV runs, with the noise, normalization and calibration policies recorded in those tables.

## Error counts, repeated runs and projections

- BER is shown at the evaluated settings, with connecting lines as visual guides.
- In the pilot and hardware tables, `n_bit_errors` and BER are means over the indicated repeats. The website identifies the repeat count and the number of bits **per run**.
- Zero observed errors are retained as BER = 0. A downward triangle at the display floor of 10⁻⁶ marks these observations on the logarithmic plot. All positive BER values in the exported sweeps exceed this floor.
- MDS markers may contain multiple codewords. Multiplicity labels describe overlap in the 2D projection, while nearest-neighbor squared distances use the full original space. Markers use their computed projection coordinates.
- The payload display uses binary 1 = white and 0 = black for all four images. Red overlays identify bit differences from the original. The three error totals are 19045, 12874 and 1742, exactly matching the source metrics.
- Payload bits are flattened row by row and assigned four bits per channel use. Replay and shared magnification operate on the recorded reconstructions. Playback uses a fixed visualization rate.

## Visuals and rebuilding

The figure atlas contains all 14 main figures and Appendix Fig. A1, exported as screen previews with their aspect ratios preserved. `tools/export_site_data.py` rebuilds data-derived assets from the committed arrays and tables. PyMuPDF is needed when importing the Figure 1 preview from a PDF source. An ordinary rebuild uses the committed data.

`tools/export_media.py` renders the two MP4 clips, posters, README overview and GIF directly from the public field and payload arrays. The README GIF is a normalized field preview without quantitative axes; use the interactive field explorer or the video for the coordinate context.

```bash
python -m pip install -r tools/requirements-site.txt
python tools/export_site_data.py
python tools/export_media.py
python tools/verify_site_data.py
python -m http.server 8767 --directory docs
```

Open `http://127.0.0.1:8767/`. Stop the local server with Ctrl+C. GitHub Pages serves `main:/docs`; the website needs no backend or external JavaScript libraries.
