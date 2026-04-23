import torch
from torch import nn
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit, transpile, qpy
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from scipy.stats import norm
import statsmodels.api as sm
from matplotlib import pyplot as plt
from qiskit_ibm_runtime.fake_provider import FakeFez
import streamlit as st






def interpret_qubound_results(result):
    """Convert QuBound numeric output into human-readable performance assessment"""
    
    # Extract values (handles both numpy arrays and lists)
    if not isinstance(result, dict):
        return result


    if isinstance(result["prediction"], np.ndarray):
        pred = result["prediction"][0]
        upper = result["upper"][0]
        lower = result["lower"][0]
    else:
        pred = result["prediction"]
        upper = result["upper"]
        lower = result["lower"]
    
    # Determine performance level
    if pred >= 0.9:
        performance_level = "EXCELLENT"
        description = "Circuit is highly reliable and suitable for quantum advantage tasks"
        recommendation = "Ready for deployment on real quantum hardware"
    elif pred >= 0.7:
        performance_level = "GOOD"
        description = "Circuit performs well with manageable noise effects"
        recommendation = "Consider error mitigation techniques for critical applications"
    elif pred >= 0.5:
        performance_level = "MARGINAL"
        description = "Circuit shows some degradation due to noise"
        recommendation = "Apply error suppression or reduce circuit depth"
    elif pred >= 0.3:
        performance_level = "POOR"
        description = "Circuit is significantly affected by noise"
        recommendation = "Re-evaluate circuit design or use noise-aware training"
    else:
        performance_level = "VERY POOR"
        description = "Circuit is performing near random levels"
        recommendation = "Circuit may be too deep, parameters incorrect, or task too complex"
    
    # Calculate confidence interval width
    ci_width = upper - lower
    if ci_width < 0.05:
        confidence = "HIGH"
        confidence_desc = "Very tight bounds, prediction is reliable"
    elif ci_width < 0.1:
        confidence = "MEDIUM"
        confidence_desc = "Moderate uncertainty in prediction"
    else:
        confidence = "LOW"
        confidence_desc = "Wide bounds, high uncertainty due to noise variability"
    
    # Generate interpretation
    interpretation_string = f"""QUANTUM PERFORMANCE BOUNDS INTERPRETATION

        📊 NUMERIC RESULTS:
        Predicted performance: {pred:.1%}
        95% Confidence Interval: [{lower:.1%}, {upper:.1%}]
        Uncertainty range: ±{ci_width/2:.1%}

        🎯 PERFORMANCE ASSESSMENT:
        Level: {performance_level}
        Description: {description}
        Recommendation: {recommendation}
    """
    
    # Return structured data for further processing
    return interpretation_string

















# --- Model Definition (Fixed: outputs fidelity, not 16 bins) ---
class QuPred(nn.Module):
    def __init__(self, input_features, hidden_dim, output_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_features, hidden_dim, batch_first=True)
        self.fc1 = nn.Linear(hidden_dim, 64)
        self.relu = nn.LeakyReLU()
        # output_dim should be 1 for fidelity prediction
        self.fc2 = nn.Linear(64, output_dim)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        out = self.relu(self.fc1(h_n[-1]))
        return self.fc2(out)

# --- Utility Functions (unchanged signatures) ---
def get_gate_name_for_pair(properties, qubits):
    target_qubits = list(qubits)
    for gate_info in properties.gates:
        if gate_info.qubits == target_qubits:
            return gate_info.gate
    return None

def look_back_window_ForError(backend, date_selected=None):
    if date_selected is None:
        date_selected = datetime.now()
    
    look_back_days = 14
    historical_data = []
    print(f"Collecting 14 days of historical noise data...")

    for i in range(look_back_days, 0, -1):
        target_date = date_selected - timedelta(days=i)
        try:
            props = backend.properties(datetime=target_date)
            if props:
                historical_data.append({"date": target_date.strftime("%Y-%m-%d"), "properties": props})
        except Exception as e:
            continue
            
    return historical_data

def calculate_circuit_fidelity(qc, noise_props, backend):
    """Helper: Calculate actual circuit fidelity under given noise"""
    noise_model = NoiseModel.from_backend(backend, noise_props)
    sim = AerSimulator(noise_model=noise_model)
    
    # Create ideal circuit for comparison
    qc_ideal = qc.copy()
    qc_ideal.save_statevector()
    
    # Run noisy simulation
    qc_noisy = qc.copy()
    qc_noisy.measure_all()
    transpiled = transpile(qc_noisy, backend)
    
    shots = 4096
    
    # Get ideal counts (simulate without noise)
    ideal_sim = AerSimulator()
    ideal_counts = ideal_sim.run(qc_ideal, shots=shots).result().get_counts()
    
    # Get noisy counts
    noisy_counts = sim.run(transpiled, shots=shots).result().get_counts()
    
    # Calculate fidelity using Hellinger distance
    all_states = set(ideal_counts.keys()) | set(noisy_counts.keys())
    fidelity_sum = 0
    for state in all_states:
        p_ideal = ideal_counts.get(state, 0) / shots
        p_noisy = noisy_counts.get(state, 0) / shots
        fidelity_sum += np.sqrt(p_ideal * p_noisy)
    
    return fidelity_sum ** 2

def get_labels_fromNoise(qc, historic_data, backend, max_output_dim=1):
    """
    Returns circuit performance metric for each time period.
    Handles parameterized circuits by binding to zeros.
    """
    print(f"Generating performance labels for circuit with {qc.num_qubits} qubits...")
    if qc.num_parameters > 0:
        print(f"  Circuit has {qc.num_parameters} parameters, binding to zero values.")
    
    labels = []
    shots = 2048
    
    for idx, history in enumerate(historic_data):
        noise_model = NoiseModel.from_backend(backend, history['properties'])
        sim = AerSimulator(noise_model=noise_model)
        
        # Prepare circuit
        qc_meas = qc.copy()
        qc_meas.measure_all()
        
        # Bind parameters if needed
        if qc_meas.num_parameters > 0:
            param_values = np.zeros(qc_meas.num_parameters)
            bound_qc = qc_meas.assign_parameters(param_values)
        else:
            bound_qc = qc_meas
        
        # Transpile for backend
        transpiled_qc = transpile(bound_qc, backend, optimization_level=1)
        
        # Run simulation
        try:
            counts = sim.run(transpiled_qc, shots=shots).result().get_counts()
            
            # Calculate performance metric: probability of most likely outcome
            if counts:
                max_prob = max(counts.values()) / shots
            else:
                max_prob = 0.0
            
            labels.append([max_prob])
            print(f"  {idx+1}/{len(historic_data)}: {history['date']} -> {max_prob:.4f}")
            
        except Exception as e:
            print(f"  {history['date']}: Error - {e}")
            labels.append([0.5])
    
    return torch.tensor(np.array(labels), dtype=torch.float32)


def extract_time_series_from_historic(historical_data, qubit_indices=[0, 1], gate_pairs=[(0, 1)]):
    extracted_data = []
    for history in historical_data:
        props = history['properties']
        row = {'date': history['date']}
        for i in qubit_indices:
            try:
                row[f'q{i}_t1'] = props.t1(i)
                row[f'q{i}_readout_err'] = props.readout_error(i)
            except:
                row[f'q{i}_t1'], row[f'q{i}_readout_err'] = 0, 0
        extracted_data.append(row)
    return pd.DataFrame(extracted_data).set_index('date')

def decompose_noise(df):
    trend_list, seasonal_list, residual_list = [], [], []
    for col in df.columns:
        if df[col].std() == 0:
            trend_list.append(df[col])
            seasonal_list.append(pd.Series(0, index=df.index))
            residual_list.append(pd.Series(0, index=df.index))
            continue
        period = min(7, len(df)//2)
        if period < 2:
            trend_list.append(df[col])
            seasonal_list.append(pd.Series(0, index=df.index))
            residual_list.append(pd.Series(0, index=df.index))
        else:
            try:
                res = sm.tsa.seasonal_decompose(df[col], model='additive', period=period, extrapolate_trend='freq')
                trend_list.append(res.trend.fillna(0))
                seasonal_list.append(res.seasonal.fillna(0))
                residual_list.append(res.resid.fillna(0))
            except:
                trend_list.append(df[col])
                seasonal_list.append(pd.Series(0, index=df.index))
                residual_list.append(pd.Series(0, index=df.index))
    return pd.concat(trend_list, axis=1), pd.concat(seasonal_list, axis=1), pd.concat(residual_list, axis=1)

def train_loop(x_train, y_train):
    # y_train shape: [timesteps, 1] (fidelity values)
    model = QuPred(input_features=x_train.shape[2], hidden_dim=32, output_dim=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    best_loss = float('inf')
    patience = 10
    patience_counter = 0
    
    for epoch in range(200):
        model.train()
        optimizer.zero_grad()
        preds = model(x_train)  # Shape: [batch, 1]
        loss = criterion(preds, y_train)
        loss.backward()
        optimizer.step()
        
        if loss.item() < best_loss:
            best_loss = loss.item()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter > patience:
                break
        
        if epoch % 50 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.6f}")
            
    return model

# --- Core QuBound Function (SAME signature, FIXED logic) ---
def call_QuBound(qc, fake_backend, token=st.secrets["YOUR_TOKEN"]):
    """
    Returns: (result_dict, model)
    result_dict = {
        "prediction": float,  # Single fidelity prediction
        "upper": float,       # Upper bound of 95% CI
        "lower": float        # Lower bound of 95% CI
    }
    """
    try:
        if token:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        else:
            service = QiskitRuntimeService()
            
        real_backend = service.backend("ibm_fez")
    except Exception as e:
        print(f"Auth Error: {e}. Try running service.save_account(token='...') once.")
        return None

    # Data Processing
    historic_data = look_back_window_ForError(real_backend)
    
    if len(historic_data) < 5:
        print(f"Warning: Only {len(historic_data)} historical data points collected. Need at least 5.")
        # Return fallback bounds
        fallback_result = {
            "prediction": np.array([0.5]),
            "upper": np.array([0.7]),
            "lower": np.array([0.3])
        }
        return fallback_result, None
    
    df = extract_time_series_from_historic(historic_data)
    t, s, r = decompose_noise(df)
    
    combined = pd.concat([t, s, r], axis=1).fillna(0)
    normalized = (combined - combined.mean()) / (combined.std() + 1e-9)
    
    # Feature Windows
    window_size = min(5, len(normalized) // 2)
    if window_size < 2:
        window_size = 2
    
    data_val = normalized.values
    x_seq = [data_val[i: i + window_size] for i in range(len(data_val) - window_size)]
    x_train = torch.tensor(np.array(x_seq), dtype=torch.float32)
    
    # Labels (FIXED: now returns fidelity values)
    y_train = get_labels_fromNoise(qc, historic_data, fake_backend, max_output_dim=1)
    
    # Align sequences
    y_train = y_train[window_size:]
    
    # Ensure matching lengths
    min_len = min(len(x_train), len(y_train))
    x_train = x_train[:min_len]
    y_train = y_train[:min_len]
    
    if len(x_train) == 0:
        print("Error: Not enough data for training")
        return None
    
    # Model Execution
    model = train_loop(x_train, y_train)
    model.eval()
    
    with torch.no_grad():
        latest_noise = x_train[-1].unsqueeze(0)
        prediction_fidelity = model(latest_noise).numpy()[0][0]  # Single float
        
        # Calculate prediction uncertainty using ensemble of recent predictions
        recent_predictions = []
        for i in range(max(0, len(x_train) - 5), len(x_train)):
            pred_val = model(x_train[i:i+1]).numpy()[0][0]
            recent_predictions.append(pred_val)
        
        if len(recent_predictions) > 1:
            std_pred = np.std(recent_predictions)
        else:
            # Use historical variance as fallback
            historical_fidelities = y_train.numpy().flatten()
            std_pred = np.std(historical_fidelities) if len(historical_fidelities) > 1 else 0.05
        
        z = norm.ppf(0.975)  # 95% confidence interval
        margin = z * std_pred
        
        # Clip to valid fidelity range [0, 1]
        upper_bound = np.clip(prediction_fidelity + margin, 0, 1)
        lower_bound = np.clip(prediction_fidelity - margin, 0, 1)
        
        # Return in original format (numpy arrays for compatibility)
        result = {
            "prediction": np.array([prediction_fidelity]),  # Keep as array for compatibility
            "upper": np.array([upper_bound]),
            "lower": np.array([lower_bound])
        }
        
        print(f"\n=== QuBound Performance Prediction ===")
        print(f"Predicted Circuit Fidelity: {prediction_fidelity:.4f}")
        print(f"95% Confidence Interval: [{lower_bound:.4f}, {upper_bound:.4f}]")
        print(f"Prediction Uncertainty (σ): {std_pred:.4f}")
        print("Final Bounds Calculated.")
        
        return result, model

if __name__ == '__main__':
    # REPLACE WITH YOUR TOKEN OR SAVE ACCOUNT BEFORE RUNNING
    MY_TOKEN = st.secrets["YOUR_TOKEN"]
    
    circuit_path = r'C:\Users\jovin\Desktop\streamlit\QRE\trained_circuit_3.qpy'
    
    try:
        with open(circuit_path, 'rb') as file:
            qc = qpy.load(file)[0]
        
        # Execute - SAME function call signature
        result = call_QuBound(qc, FakeFez(), token=MY_TOKEN)
        
        if result is not None:
            bounds, trained_model = result
            print(f"\nResults (original format):")
            print(f"  Prediction: {bounds['prediction'][0]:.4f}")
            print(f"  Upper bound: {bounds['upper'][0]:.4f}")
            print(f"  Lower bound: {bounds['lower'][0]:.4f}")
            print(f"\nInterpretation: Circuit fidelity will be between {bounds['lower'][0]*100:.1f}% and {bounds['upper'][0]*100:.1f}% with 95% confidence")
        else:
            print("QuBound execution failed. Check authentication.")
            
    except FileNotFoundError:
        print(f"Error: Could not find circuit file at {circuit_path}")
    except Exception as e:
        print(f"Unexpected error: {e}")