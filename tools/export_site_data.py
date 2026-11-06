"""Build the static research website assets from traceable manuscript exports.

Initial import: python tools/export_site_data.py --revision PATH --archive PATH
Rebuild derived assets from the committed data: python tools/export_site_data.py
Requires numpy and Pillow; PyMuPDF is used only when importing Figure 1.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import itertools
import json
import shutil
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from avs_oam_core import OAMConfig, finite_ring_matrix, receiver_ring

DATA = ROOT / "docs/data"
ASSETS = ROOT / "docs/assets"
OBS = ["pressure_only", "pressure_plus_vx_vy", "pressure_plus_vx_vy_vz"]
SOURCES = {
    "snr": "fig4_nonorth_avs2xnoise/fig4_known_bpsk_nonorth_avs2xnoise_source_data.csv",
    "offset_nominal": "offset_avs2xnoise/fig6_known_bpsk_offset_mismatch_avs2xnoise_source_data.csv",
    "offset_calibrated": "offset_avs2xnoise/fig7_known_bpsk_offset_calibrated_avs2xnoise_source_data.csv",
    "distance": "distance_avs2xnoise/fig8_distance_calibrated_avs2xnoise_source_data.csv",
    "pilots": "unknown_channel_unitwhite/fig9_unknown_channel_calibration_avs2xnoise_source_data.csv",
    "hardware": "known_bpsk_hw_error/fig10_hw_error_required_snr_landscape_raw.csv",
    "codeword_distances": "appendix_decision_geometry/figA1_bpsk_decision_geometry_pairwise_distances.csv",
}
GALLERY = [
    ("1", "System and receiver geometry"), ("2", "Pressure and velocity fields"),
    ("3", "Known-mode BPSK detection"), ("4", "Receiver offset geometry"),
    ("5", "Offset with a nominal detector"), ("6", "Fields at displaced receivers"),
    ("7", "Offset with a calibrated detector"), ("8", "Propagation distance"),
    ("9", "Fields at different distances"), ("10", "Finite pilot calibration"),
    ("11", "Estimated receiving matrices"), ("12", "Transmitter error geometry"),
    ("13", "Hardware error robustness"), ("14", "Binary image recovery"),
    ("A1", "BPSK codeword geometry"),
]


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(name, data):
    (DATA / name).write_text(json.dumps(data, separators=(",", ":"), allow_nan=False), encoding="utf-8")


def rows(name):
    return list(csv.DictReader((DATA / (name + ".csv")).open(encoding="utf-8-sig")))


def import_sources(revision, archive):
    base = revision / "code/06_figures_nature_style"
    manifest = {"description": "Source data for the AVS-OAM study", "sources": []}

    def record(src, dest, transform="byte-for-byte copy"):
        manifest["sources"].append({"source": src.name, "sha256_source": digest(src),
            "public_file": dest, "transformation": transform})

    for name, rel in SOURCES.items():
        src = base / rel
        shutil.copy2(src, DATA / (name + ".csv"))
        record(src, name + ".csv")
    src = base / "field_phys/field_phys_data.npz"
    z = np.load(src)
    sampled = {k: (z[k][::3, ::3] if z[k].ndim == 2 else z[k][::3] if k in ["x", "y"] else z[k])
               for k in z.files if "intensity" not in k}
    # Display scales come from the full-resolution arrays, separately per mode.
    for ell in z["modes"]:
        sampled[f"ell_{ell}_p_scale"] = np.percentile(abs(z[f"ell_{ell}_p"]), 99.5)
        sampled[f"ell_{ell}_vxy_scale"] = np.percentile(np.sqrt(abs(z[f"ell_{ell}_vtx"])**2 + abs(z[f"ell_{ell}_vty"])**2), 99.5)
    np.savez_compressed(DATA / "field_samples.npz", **sampled)
    record(src, "field_samples.npz", "Every third point in each spatial dimension; raw complex p and pressure-equivalent velocity. Display scales saved separately.")
    src = archive / "04_simulation/results_v5_logo_window_screen/source_data/v5_forced_gap90_beidalou_snr3dB_hires_reconstructions.npz"
    shutil.copy2(src, DATA / "payload.npz")
    record(src, "payload.npz")
    src = revision / "code/04_simulation/results_v5_logo_window_screen/tables/v5_forced_gap90_beidalou_snr3dB_hires_metrics.csv"
    shutil.copy2(src, DATA / "payload_metrics.csv")
    record(src, "payload_metrics.csv")
    for fig, title in GALLERY:
        if fig == "1":
            import fitz
            src = revision / "06_figures_nature_style/_cn_original_18_figures/Fig01_system_schematic.pdf"
            doc = fitz.open(src)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            doc.close()
        else:
            src = revision / ("06_figures_nature_style/bldg_payload/bldg_payload_gap90_snr3_1200dpi.png" if fig == "14" else f"qa/Fig{fig}.png")
            im = Image.open(src).convert("RGB")
        im.thumbnail((2200, 2200))
        im.save(ASSETS / f"figure-{fig}.webp", quality=93, method=6)
        record(src, f"../assets/figure-{fig}.webp", "Screen preview, resized with aspect ratio preserved; manuscript files unchanged")
    write_json("source_manifest.json", manifest)


def build():
    fields = {}
    z = np.load(DATA / "field_samples.npz")
    for ell in map(int, z["modes"]):
        p = z[f"ell_{ell}_p"] / z[f"ell_{ell}_p_scale"]
        vx = z[f"ell_{ell}_vtx"] / z[f"ell_{ell}_vxy_scale"]
        vy = z[f"ell_{ell}_vty"] / z[f"ell_{ell}_vxy_scale"]
        fields[str(ell)] = {k: np.round(v.ravel(), 6).tolist() for k, v in
                           dict(pr=p.real, pi=p.imag, xr=vx.real, xi=vx.imag, yr=vy.real, yi=vy.imag).items()}
    write_json("fields.json", fields)
    # Exact finite-ring model from the public reference implementation.
    cfg = OAMConfig()
    rx = receiver_ring(5, cfg)
    raw = finite_ring_matrix(rx, [-2, -1, 1, 2], cfg)
    np.savez_compressed(DATA / "receiver_matrix.npz", raw=raw, receivers=rx, modes=[-2,-1,1,2])
    matrices = []
    for n in [1, 3, 4]:
        a = raw[:n*5].copy()
        a /= np.linalg.norm(a, axis=0, keepdims=True)
        a[5:] *= np.sqrt(3)
        matrices.append({"real": a.real.round(9).tolist(), "imag": a.imag.round(9).tolist(), "magnitude": abs(a).round(9).tolist()})
    write_json("receiver.json", {"points": rx.tolist(), "raw_real": raw.real.tolist(), "raw_imag": raw.imag.tolist(), "matrices": matrices})
    dist_rows = rows("codeword_distances")
    geometries = []
    for obs in OBS:
        d2 = np.zeros((16,16))
        for r in dist_rows:
            if r["observation_mode"] == obs:
                i,j = int(r["codeword_i"]),int(r["codeword_j"])
                d2[i,j]=d2[j,i]=float(r["d2"])
        j = np.eye(16)-np.ones((16,16))/16
        vals,vecs = np.linalg.eigh(-.5*j@d2@j)
        idx = np.argsort(vals)[::-1][:2]
        xy = vecs[:,idx]*np.sqrt(np.maximum(vals[idx],0))
        for k in range(2):
            if xy[np.argmax(abs(xy[:,k])),k]<0: xy[:,k]*=-1
        geometries.append({"observation":obs,"xy":xy.round(8).tolist(), "d2":d2.tolist(),
            "minimum_d2":float(np.min(d2[np.triu_indices(16,1)])),
            "retained_variance":float(np.sum(np.maximum(vals[idx],0))/np.sum(np.maximum(vals,0)))})
    write_json("codewords.json", {"symbols":list(itertools.product([-1,1],repeat=4)),"views":geometries})
    for name in SOURCES:
        if name == "codeword_distances": continue
        converted=[]
        for row in rows(name):
            for k,v in row.items():
                try: row[k] = float(v)
                except (ValueError,TypeError): pass
            converted.append(row)
        write_json(name + ".json", converted)
    payload=np.load(DATA / "payload.npz")
    original=payload["original"]
    metrics=rows("payload_metrics")
    for key in ["original"]+OBS:
        arr=payload[key]
        # Binary reconstruction convention: bit 1 is white.
        Image.fromarray(arr.astype("uint8")*255).save(ASSETS / f"payload-{key}.png", optimize=True)
        if key != "original":
            err=arr!=original
            row=next(r for r in metrics if r["observation_mode"]==key)
            assert int(err.sum())==int(row["bit_errors"])
            assert abs(err.mean()-float(row["BER"]))<1e-14
            rgba=np.zeros((*arr.shape,4),dtype="uint8")
            rgba[err]=[226,54,65,240]
            Image.fromarray(rgba).save(ASSETS / f"errors-{key}.png", optimize=True)
    write_json("payload_metrics.json", metrics)
    write_json("gallery.json",[{"id":k,"title":v,"image":f"assets/figure-{k}.webp"} for k,v in GALLERY])
    manifest=json.loads((DATA/"source_manifest.json").read_text(encoding="utf-8"))
    manifest["public_checksums"]={p.name:digest(p) for p in sorted(DATA.iterdir()) if p.name!="source_manifest.json"}
    write_json("source_manifest.json",manifest)
    print(f"Export complete: {len(fields)} fields; {sum(len(rows(n)) for n in SOURCES)} source rows; 3 payload error counts verified.")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision",type=Path)
    parser.add_argument("--archive",type=Path)
    args=parser.parse_args()
    DATA.mkdir(parents=True,exist_ok=True)
    ASSETS.mkdir(parents=True,exist_ok=True)
    if args.revision:
        if not args.archive: parser.error("--archive is required with --revision")
        import_sources(args.revision,args.archive)
    build()
