import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from qiskit import qpy
from qiskit_aer.primitives import EstimatorV2 as AerEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer.noise import NoiseModel, depolarizing_error, thermal_relaxation_error
from qiskit import transpile
from datetime import datetime, timedelta
from sklearn.cluster import KMeans


# clustering
def extract_noise_features(props):
    """
    Converts backend calibration properties into a feature vector.
    """

    t1_vals = [props.t1(i) for i in range(len(props.qubits))]
    t2_vals = [props.t2(i) for i in range(len(props.qubits))]

    two_q_gates = ['cx', 'ecr', 'cz']
    cx_errors = [
        g.parameters[0].value
        for g in props.gates
        if g.gate in two_q_gates
    ]

    features = np.array([
        np.mean(t1_vals),
        np.mean(t2_vals),
        np.mean(cx_errors) if cx_errors else 0,
        np.std(cx_errors) if cx_errors else 0
    ])

    return features





def qucad_loss_noisy(theta_values, vqc, estimator, observable, z, u, rho):
    # Prepare the Pub (Primitive Unified Bloc)
    pub = (vqc, observable, theta_values)
    job = estimator.run([pub])
    result = job.result()[0]
    
    # Extract the expectation value
    qnn_expectation = result.data.evs
    
    # ADMM Penalty: (rho/2) * ||theta - z + u||^2
    penalty = (rho / 2) * np.linalg.norm(theta_values - z + u)**2
    
    return float(qnn_expectation + penalty)



def run_qucad_training_noisy(vqc, noise_model, backend_ibm, iterations=5, lam=0.01, rho=500.0):
    n = vqc.num_parameters
    theta = np.random.uniform(-np.pi, np.pi, n)
    z, u = np.zeros(n), np.zeros(n)
    
    # CORRECT INITIALIZATION FOR AER ESTIMATOR V2
    noisy_estimator = AerEstimator()
    
    # Update options attributes directly (since .update() is not available)
    noisy_estimator.options.backend_options = {
        "method": "density_matrix", 
        "noise_model": noise_model
    }
    noisy_estimator.options.run_options = {"shots": 1024}
    
    observable = SparsePauliOp.from_list([("Z" + "I" * (vqc.num_qubits - 1), 1)])
    history = {"loss": [], "sparsity": []}

    print(f"\n[QuCAD] Starting Battle Against Noise: {backend_ibm.name}")
    # print(f"{'Iter':<5} | {'Cost':<10} | {'Sparsity'}")
    # print("-" * 35)
    
    for i in range(iterations):
        res = minimize(
            qucad_loss_noisy, 
            theta, 
            args=(vqc, noisy_estimator, observable, z, u, rho),
            method='COBYLA',
            options={'maxiter': 20} 
        )
        theta = res.x

        # Step 2: Z-update (Compression/Pruning)
        threshold = np.sqrt(2 * lam / rho)
        temp_z = theta + u
        z = np.where(np.abs(temp_z) > threshold, temp_z, 0)

        # Step 3: U-update (Dual Variable)
        u = u + (theta - z)

        active_count = np.count_nonzero(z)
        history["loss"].append(res.fun)
        history["sparsity"].append(active_count)
        # print(f"{i+1:02d}    | {res.fun:<10.4f} | {active_count}/{n}")
        print(f"Iter:{i} , Cost:{res.fun}")
        

    return theta, z, history



def get_current_noise_multiplier(current_props, baseline_props):
    # 1. T1 Ratio
    t1_ratios = [baseline_props.t1(i) / current_props.t1(i) for i in range(len(current_props.qubits))]
    avg_t1_ratio = np.mean(t1_ratios) if t1_ratios else 1.0
    
    # 2. Gate Error Ratio - Search for ANY 2-qubit gates (usually the noise bottleneck)
    two_q_gates = ['cx', 'ecr', 'cz']
    
    baseline_errors = [g.parameters[0].value for g in baseline_props.gates if g.gate in two_q_gates]
    current_errors = [g.parameters[0].value for g in current_props.gates if g.gate in two_q_gates]
    
    if not baseline_errors or not current_errors:
        print("[Warning] No 2-qubit gate data found. Defaulting to T1 ratio.")
        cx_ratio = 1.0
    else:
        cx_ratio = np.mean(current_errors) / np.mean(baseline_errors)
    
    # Combine (30% T1 influence, 70% Gate Error influence)
    total_multiplier = (0.3 * avg_t1_ratio) + (0.7 * cx_ratio)
    return total_multiplier



def deploy_qucad_model(vqc, lut, current_multiplier):

    clusters = lut["clusters"]

    # We embed multiplier into same dimensionality
    # as centroid for compatibility
    query = np.array([current_multiplier, 0, 0, 0])

    best_dist = float("inf")
    best_weights = None

    for c in clusters:

        centroid = np.array(c["centroid"])

        dist = np.linalg.norm(query - centroid)

        if dist < best_dist:
            best_dist = dist
            best_weights = c["weights"]

    print("[QuCAD] Deploying cluster representative model")
    print("Best Cluster Centroid:", centroid)

    deployed_circuit = vqc.assign_parameters(best_weights)
    deployed_circuit = transpile(deployed_circuit, optimization_level=3)

    return deployed_circuit




def generate_qucad_lut(vqc, backend, days=20, clusters=4):

    feature_bank = []
    weight_bank = []

    print("\n[QuCAD] Collecting Noise Snapshots")

    for day in range(days):

        cal_date = datetime.now() - timedelta(days=day)
        props = backend.properties(datetime=cal_date)

        if props is None:
            continue

        print(f"[QuCAD] Snapshot {cal_date.strftime('%Y-%m-%d')}")

        noise_model = NoiseModel.from_backend(backend)

        features = extract_noise_features(props)

        theta_trained, z_mask, _ = run_qucad_training_noisy(
            vqc,
            noise_model,
            backend,
            iterations=10,
            lam=0.005,
            rho=500.0
        )

        robust_theta = theta_trained * (z_mask != 0)

        feature_bank.append(features)
        weight_bank.append(robust_theta)

    feature_bank = np.array(feature_bank)

    print("\n[QuCAD] Performing Unsupervised Clustering")

    kmeans = KMeans(n_clusters=clusters, random_state=42)
    labels = kmeans.fit_predict(feature_bank)

    lut = {"clusters": []}

    for c in range(clusters):

        cluster_indices = np.where(labels == c)[0]

        if len(cluster_indices) == 0:
            continue

        # Choose first model as representative
        rep_idx = cluster_indices[0]

        lut["clusters"].append({
            "centroid": kmeans.cluster_centers_[c],
            "weights": weight_bank[rep_idx]
        })

        print(f"[QuCAD] Cluster {c} created with {len(cluster_indices)} models")

    return lut



def get_noiseModel_andBackend_ondate(date_time=datetime.now()):
    TOKEN = "ucK-WJCddM2wD85T6tXy3dSWpuj-FIH4GLw9kf48q7Bn"
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=TOKEN)
    backend_ibm = service.backend("ibm_fez")
    
    # This is where you specify the date to get historical data
    target_props = backend_ibm.properties(datetime=date_time)
    
    # Build a noise model from those specific historical properties
    noise_model = NoiseModel.from_backend(backend_ibm)
    
    return noise_model, backend_ibm, target_props

def main():
    noise_model, backend_ibm, target_props = get_noiseModel_andBackend_ondate()
    with open("../../trained_circuit_3.qpy", 'rb') as file:
        vqc = qpy.load(file)[0]
    num_params = vqc.num_parameters

    final_theta, final_mask, stats = run_qucad_training_noisy(
        vqc, 
        noise_model, 
        backend_ibm,
        iterations=10, 
        lam=0.005, 
        rho=500.0
    )

    # Robust parameters filtered by the mask
    robust_theta = final_theta * (final_mask != 0)

    print("\n--- Summary ---")
    print(f"Original Parameters: {num_params}")
    print(f"Compressed Parameters: {np.count_nonzero(final_mask)}")

    # reconstruct the circuit, # COmpression works
    bound_vqc = vqc.assign_parameters(robust_theta)
    robust_vqc_compressed = transpile(bound_vqc, optimization_level=3)
    print("--- QuCAD Compression Results ---")
    print(f"Original Depth: {vqc.depth()}")
    print(f"Robust Depth:   {robust_vqc_compressed.depth()}")
    print(f"Gate Reduction: {vqc.size() - robust_vqc_compressed.size()} gates removed")


    # generate LUT
    qucad_bank = generate_qucad_lut(vqc, backend_ibm)
    print(qucad_bank)

    target_date = datetime(2025, 2, 3)
    noise_model_future, backend_future, props_future = get_noiseModel_andBackend_ondate(target_date)
    multiplier = get_current_noise_multiplier(props_future, backend_ibm.properties())

    print(f"Calculated Noise Drift: {multiplier:.2f}x")

    circuit = deploy_qucad_model(vqc,qucad_bank , multiplier)
    circuit.draw("mpl")
    plt.show()

if __name__ == "__main__":
    main()