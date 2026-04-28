# Qshot — Noise-Aware Shot-Count Recommender

Qshot recommends how many measurement shots a quantum circuit needs
in order to reach a target fidelity on a given (noisy) backend.
Input: a `QuantumCircuit` + a backend noise snapshot (JSON).
Output: an integer shot count and the predicted fidelity at that count.

This package is the **integration-ready snapshot** of the Qshot research
code. It contains only what is needed to load the trained recommender
and serve predictions — no training, evaluation, or experiment scripts.

---

## Package layout

```
Qshot_handover/
├── README.md                 # this file
├── README_zh.md              # Chinese version
├── requirements.txt
├── example_usage.py          # minimal end-to-end call
├── src/
│   ├── recommend_shots_v4.py # main engine + Python API
│   ├── dual_gnn_model.py     # GNN architecture (fallback model)
│   ├── show_dag.py           # QASM → graph conversion (used by GNN)
│   └── train_dual_gnn.py     # referenced by the GNN fallback loader
├── data/
│   ├── shots_dataset_historic*/       (12 directories, ~3280 records)
│   └── noise_json/           # 6 IBM noise snapshots
└── checkpoint/
    └── best_model.pt         # trained GNN fallback (~4.3 MB)
```

All paths under `data/` and `checkpoint/` are auto-discovered by
`recommend_shots_v4.py` at import time — you do not need to pass them
explicitly unless you want to.

---

## Installation

Developed and tested on **Python 3.9**.

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`torch-scatter` and `torch-sparse` need wheels matching your PyTorch
+ CUDA build. If `pip install` fails on those two lines, install them
from the PyG wheel index — see the comment inside `requirements.txt`.

---

## Quick start

```bash
cd Qshot_handover/
python example_usage.py
```

Expected behavior: prints progress, spends ~30–60 seconds loading the
database and building clusters, then prints a recommended shot count.

---

## Python API

Two entry points, both in `src/recommend_shots_v4.py`.

### `QshotRecommender` — load once, query many (recommended for services)

```python
from recommend_shots_v4 import QshotRecommender

# Construction is expensive (~30-60s). Do this once at service startup.
recommender = QshotRecommender()          # uses bundled data + checkpoint
# Or override:
# recommender = QshotRecommender(
#     dataset_dirs=[...], gnn_ckpt="path/to/best_model.pt")

# Each .predict() call is cheap (~seconds, dominated by pilot measurement).
result = recommender.predict(
    circuit=my_quantum_circuit,       # QuantumCircuit or path to .qpy
    noise_json="path/to/noise.json",  # path or already-loaded dict
    alpha=0.95,                       # target fidelity fraction
)
```

### `predict_shots()` — one-shot convenience

```python
from recommend_shots_v4 import predict_shots

result = predict_shots(circuit, noise_json_path, alpha=0.95)
```

This wrapper builds a fresh `QshotRecommender` for each call. Only use
it for one-off scripts — for a service, instantiate `QshotRecommender`
once and reuse it.

---

## Inputs & outputs

### `circuit`
Either a `qiskit.QuantumCircuit` instance (without `measure_all()` — the
recommender adds its own measurements) or a path to a `.qpy` file.

### `noise_json`
Either a filesystem path (str or `pathlib.Path`) to a noise JSON, or an
already-loaded dict.

The 6 noise JSONs shipped in `data/noise_json/` follow the IBM
preprocessed-noise schema used by this project. A noise JSON must contain
a `noise_summary` block with at minimum:
- `twoq_gate_error_mean`, `readout_mean` or (`prob_meas0_prep1_mean` + `prob_meas1_prep0_mean`)
- `T2_mean`
- `sx_gate_error_mean`, `T1_mean`, etc. (used by the noise model builder)

If you need to adapt Qshot to a different backend, the noise JSON is the
interface — reproduce the schema of a bundled file and it should work.

### Return value

A dict with keys:

| key | type | meaning |
|---|---|---|
| `recommended_shots` | `int` | what to pass as `shots=` when running the circuit |
| `method` | `str` | `"regression"` (cluster + curve fit) or `"gnn_fallback"` (outlier) |
| `predicted_fidelity` | `float` | model's estimate of fidelity at the recommended shots |
| `predicted_std` | `float` | standard deviation on that estimate |
| `cluster_label` | `int` | HDBSCAN cluster the circuit was matched to (`-1` if outlier) |
| `tier` | `int` | shot-regime tier within the cluster |
| `n_matched` | `int` | how many neighbors were used for curve fitting |
| `fit` | `dict` | raw fit parameters (`F_inf`, `a`, `b`, `target`, ...) |

Returns `None` if recommendation failed (inspect logs for reason).

---

## How it works (briefly)

Two code paths, selected automatically per query:

1. **Main path (regression)**: extract 9 structural + noise features from
   the query; find the nearest HDBSCAN cluster in the training DB; pick
   a tier by kNN vote; run a pilot (a small set of real measurements at
   tier-appropriate shot counts); k-nearest-match the pilot's PF curve to
   records in the cluster; fit `F(s) = F_inf - a/s^b` on matched neighbors;
   solve for the smallest `s` where `F(s) - z·σ ≥ α·F_conv`.

2. **Fallback path (GNN)**: if the query does not match any cluster, a
   dual-graph GINEConv network (`dual_gnn_model.py`, trained checkpoint in
   `checkpoint/best_model.pt`) predicts the full fidelity curve from
   `(circuit DAG graph, backend coupling graph)`, and the same
   threshold logic picks `s`.

---

## Performance notes

- **Cold start**: ~30–60 seconds (loads ~3280 records + HDBSCAN clustering
  + GNN checkpoint). Do this at service startup, not per-request.
- **Per query**: dominated by pilot measurements. Roughly a few seconds to
  tens of seconds depending on circuit size and pilot config.
- **Memory**: < 1 GB resident. No GPU required for inference (the GNN
  fallback uses CPU by default; pass a CUDA-enabled torch build if you
  want GPU speed-ups on the fallback path).

---

## Limitations & scope

- **Qubit range**: training data covers 5–8 qubits. Outside this range the
  GNN fallback may extrapolate but accuracy is unvalidated.
- **Backend family**: training noise snapshots are from IBM Marrakesh and
  Pittsburgh only. Noise JSONs from other vendors need schema mapping.
- **Circuit families**: best for QAOA-like, HEA brickwall, semi-random
  layered, and fully random circuits. Very structured algorithmic
  circuits (QFT, Grover, error-correction codes, etc.) are out of
  distribution.
- **Transpiler**: the recommender transpiles the query with
  `optimization_level=1` and `seed_transpiler=1234` internally — do not
  pre-transpile.

---

## Invariants worth knowing (for anyone modifying the code)

- The two shots sequences `SHOTS_SEQUENCE_QAOA` and `SHOTS_SEQUENCE_DEFAULT`
  in `recommend_shots_v4.py` must match the sequences used when the
  training dataset was built. Do not change them without rebuilding the
  dataset.
- `CIRCUIT_FEATURE_KEYS` (6 circuit features) and `NOISE_FEATURE_KEYS`
  (3 noise features) define the clustering feature space. Changing them
  invalidates the bundled data.
- The train/test split is deterministic: `test_ratio=0.1, seed=42`. The
  recommender trains its clusters on the 90% train half regardless of
  what the caller does with the 10% held out.
- `record_id` in the training DB is a hash that includes the noise
  filename. The 12 dataset directories are not interchangeable — treat
  them as one logical dataset and always load all of them.
- `base.qasm` in records may be OpenQASM 3; the loader falls back to a
  subset QASM3→QASM2 converter (`_qasm3_to_qasm2`) for compatibility.

---

## Files you can ignore

`train_dual_gnn.py` is only imported indirectly (the GNN fallback uses
some of its constants). You do not need to invoke it for inference.
Likewise `show_dag.py` exposes a CLI but its only runtime role here is
the `qasm_to_graph_data` helper used by the GNN fallback.

---

## Contact

Questions about the model, dataset, or algorithm: Tong Li (`tli24@gmu.edu`).
