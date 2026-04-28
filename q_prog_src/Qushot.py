"""Qushot — noise-aware shots recommender.

Exposes a single entry point:

    from Qushot import recommend_shots
    result = recommend_shots(circuit, noise_json_path, nq=7, alpha=0.95)

The heavy implementation lives in ``qushot_internals/`` (a verbatim copy of
the Qshot handover package). Data and the GNN checkpoint are auto-discovered
relative to ``qushot_internals/src/``.
"""
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_INTERNALS_SRC = _HERE / "qushot_internals" / "src"
if str(_INTERNALS_SRC) not in sys.path:
    sys.path.insert(0, str(_INTERNALS_SRC))

# from q_prog_src/qushot_internals.src import recommend_shots_v4  # noqa: F401

from recommend_shots_v4 import QshotRecommender  # noqa: E402

_recommender = None  # lazy singleton; construction takes ~30-60s


def recommend_shots(circuit, noise_json, nq, alpha=0.95):
    """Return the recommended shot count for a circuit on a noisy backend.

    Parameters
    ----------
    circuit : qiskit.QuantumCircuit or path-like
        Target circuit (or path to a .qpy file).
    noise_json : path-like
        Path to an IBM backend noise snapshot JSON.
    nq : int
        Number of qubits of the circuit.
    alpha : float, default 0.95
        Target fraction of the converged fidelity.

    Returns
    -------
    dict | None
        Dict with keys ``recommended_shots``, ``method``, ``predicted_fidelity``,
        ``predicted_std``, (optionally) ``tier`` and ``cluster_label``.
        ``None`` if the recommender could not produce a result.
    """
    global _recommender
    if _recommender is None:
        _recommender = QshotRecommender()
    return _recommender.predict(
        circuit=circuit, noise_json=noise_json, nq=nq, alpha=alpha
    )