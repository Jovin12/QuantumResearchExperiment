from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit
from qiskit_aer.noise import NoiseModel
from qiskit_aer import AerSimulator
from qiskit.quantum_info import hellinger_distance  # state_fidelity and total variation distance are used for simple Fidelity calculations
from qiskit import transpile
from qiskit_ibm_runtime.fake_provider import FakeFez
from qiskit import qpy

# from .qiskit_circuit_general import *
from qiskit_circuit_general import *

import torch
from torch import nn

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.stats import norm
from torchmetrics import MeanSquaredLogError

def get_gate_name_for_pair(properties, qubits):
    target_qubits = list(qubits)
    
    for gate_info in properties.gates:
        if gate_info.qubits == target_qubits:
            return gate_info.gate
            
    return None

# function to get the necessary noise data from ibm_cloud 
# gets the properties object for each day of the 14 day window
def look_back_window_ForError(backend, date_selected = datetime.now()):
    look_back_days = 14
    historical_data = []

    if date_selected is None:
        date_selected = datetime.now()

    print(f"Starting data collection")

    for i in range(look_back_days, 0, -1):
        target_date = date_selected - timedelta(days = i)

        properties = backend.properties(datetime = target_date)

        historical_data.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "properties": properties
            })
        if i % 7 == 0:
            print("Half way done...") 
    return historical_data


# uses the properties generated to replicated the noise into a noise model 
# then use that to generate effective labels/outputs with noise 
# and work on it without noise
def get_labels_fromNoise(qc, historic_data, backend):
    print("Getting error prediction labels from circuit nonoise and noise values")

    labels = []

    qc.measure_all()
    qc = transpile(qc, backend, optimization_level=3)

    if qc.num_parameters > 0:
        theta = np.random.uniform(-np.pi, np.pi, qc.num_parameters)
        qc = qc.assign_parameters(theta)

    num_states = 2 ** qc.num_qubits

    if num_states > 2**25:  # ~33 million states
        raise ValueError(f"Circuit has {qc.num_qubits} qubits, resulting in {num_states} states, which exceeds memory limits. Use a smaller circuit or reduce qubits.")

    for history in historic_data:
        properties = history['properties']
        noise_model = NoiseModel.from_backend(backend, properties)
        noisy_simulator = AerSimulator(noise_model = noise_model)

        counts = noisy_simulator.run(qc, shots = 2048).result().get_counts()

        probs = np.zeros(num_states)
        for bitstring, count in counts.items():
            idx = int(bitstring, 2)
            probs[idx] = count / 2048

        labels.append(probs)

    return torch.tensor(labels, dtype = torch.float32)


# this uses the output form the previous funciton to get the 
# T1, Tw, Readout and gate errors
def extract_time_series_from_historic(historical_data, qubit_indices = [0], gate_qubit = [(0,1)]):
    print("Starting Error values Extraction from historic data.")
    extracted_data = []

    for history in historical_data:
        date = history['date']
        properties = history['properties']

        row = {'date':date}

        for i in qubit_indices:
            row[f'q{i}_t1'] = properties.t1(i)
            row[f'q{i}_t2'] = properties.t2(i)
            row[f'q{i}_readout_err'] = properties.readout_error(i)

        for g in gate_qubit:
            gate_name = get_gate_name_for_pair(properties, g)
            row[f'gate_err_{g[0]}_{g[1]}'] = properties.gate_error(gate_name, g)

        extracted_data.append(row)

    df  = pd.DataFrame(extracted_data).set_index('date')
    return df


# ---------- Perform QuDeCOM

def decompose_noise(df):
    print("breaking extracted df in to trend and residue.")

    trend_list = []
    seasonal_list = []
    residual_list = []

    for col in df.columns:
        try:
            result = sm.tsa.seasonal_decompose(df[col], model='additive', period=7, extrapolate_trend='freq')
            trend_list.append(result.trend)
            seasonal_list.append(result.seasonal)
            residual_list.append(result.resid)
        except:
            trend_list.append(df[col])
            seasonal_list.append(pd.Series(np.zeros(len(df)), index=df.index))
            residual_list.append(pd.Series(np.zeros(len(df)), index=df.index))

    trend_df = pd.concat(trend_list, axis=1)
    seasonal_df = pd.concat(seasonal_list, axis=1)
    residual_df = pd.concat(residual_list, axis=1)

    trend_df.columns = df.columns
    seasonal_df.columns = df.columns
    residual_df.columns = df.columns

    return trend_df, seasonal_df, residual_df



#------------- encoding the drift and fluctuations, 
# into a feature vector for the LSTM
# lstm takes into consideratino of a sequence, hence this is necessary
def create_sequences(df, window_size=5):
    print("preprocessing lstm data ==")
    data = df.values
    sequences = []
    for i in range(len(data) - window_size):
        window = data[i : i + window_size]
        sequences.append(window)
    return torch.tensor(np.array(sequences), dtype=torch.float32)


#------------------------------
# Finally now that pre-processing is complete, 
# the LSTM model 
# or QuPRED
#--------------------------------
class QuPred(nn.Module):
    def __init__(self, input_features, blocks):
        super().__init__()
        self.lstm = nn.LSTM(input_features, blocks, batch_first=True)
        self.fc1 = nn.Linear(blocks, 64)
        self.relu = nn.LeakyReLU()
        self.fc2 = nn.Linear(64, 16)  # multi-state output

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        out = self.relu(self.fc1(h_n[-1]))
        return self.fc2(out)
    

# using stistical confidence for the loss to get the bound 
# for a bell curve to be with in the 95% of all the data, 
# that is the value should lie between 2 standard deviations of the mean
# taking the idea from the confidence table in the paper
# Statistical theory; we can be 95% sure that out data wont be away from the actual value
def loss_fn(preds, targets, confidence=0.95):
    criterion = MeanSquaredLogError()
    return criterion(preds, targets)


def train_loop(x_train, y_train):

    print("Entered Model training ...")

    model = QuPred(input_features= x_train.shape[2], blocks = 32)
    optimizer = torch.optim.Adam(model.parameters(), lr = 0.008)
    epochs = 100

    best_loss = float('inf')
    best_state = None

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()

        predictions = model(x_train)
        loss = loss_fn(predictions, y_train)

        loss.backward()
        optimizer.step()

        if loss.item() < best_loss:
            best_loss = loss.item()
            best_state = model.state_dict()

        if epoch % 10 == 0:
            print(f"Epoch {epoch} | Model Loss: {loss.item():.6f}")
    
    if best_state:
        model.load_state_dict(best_state)

    return model


def predict_vqc_bound(model, x_train):
    model.eval()
    with torch.no_grad():

        latest_noise = x_train[-1].unsqueeze(0)
        pred = model(latest_noise).numpy()[0]

        z = norm.ppf(0.95)

        std = np.std(pred)
        upper = pred + z * std
        lower = pred - z * std

        return {
            "prediction": pred,
            "upper_bound": upper,
            "lower_bound": lower
        }


# provider is the fake backend that will be used for transpiling and other uses
# this is the function that will be called by the website to run the QuBound from scratch
# IF YOU WANT TO RUN THE VQE CHECK THE MAIN FUNCTION WHICH RUNS THE PRESET VQC train_circuit.qpy
def call_QuBound(qc, provider, date = datetime.now()):
    token="ucK-WJCddM2wD85T6tXy3dSWpuj-FIH4GLw9kf48q7Bn"
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", 
        token=token,
        plans_preference=["open"] 
    )

    backend = service.backend("ibm_fez")
    historic_data = look_back_window_ForError(backend, date)

    extracted_df = extract_time_series_from_historic(historic_data)
    trend_df, seasonal_df, residual_df = decompose_noise(extracted_df)

    combined_df = pd.concat([trend_df, seasonal_df, residual_df], axis=1)
    combined_df = combined_df.fillna(0)
    normalized_df = (combined_df - combined_df.mean()) / combined_df.std()

    x_train = create_sequences(normalized_df, window_size=5)

    y_train = get_labels_fromNoise(qc,historic_data, provider)
    y_train = y_train[5:]

    model = train_loop(x_train, y_train)

    final_bound = predict_vqc_bound(model, x_train)
    print(final_bound)
    return final_bound, model



# testing the model on example input
def main():

    with open(r'C:\Users\jovin\OneDrive\Desktop\streamlit\trained_circuit.qpy', 'rb') as file:
        qc = qpy.load(file)[0]
    qc.draw('mpl')
    plt.show()


    token="ucK-WJCddM2wD85T6tXy3dSWpuj-FIH4GLw9kf48q7Bn"
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", 
        token=token,
        plans_preference=["open"] 
    )

    print(f"Connected using instance: {service.active_account()}")

    backend = service.backend("ibm_fez")

    historic_data = look_back_window_ForError(backend)

    extracted_df = extract_time_series_from_historic(historic_data)
    trend_df, seasonal_df, residual_df = decompose_noise(extracted_df)

    combined_df = pd.concat([trend_df, seasonal_df, residual_df], axis=1)
    combined_df = combined_df.fillna(0)
    normalized_df = (combined_df - combined_df.mean()) / combined_df.std()

    x_train = create_sequences(normalized_df, window_size=5)

    backend = FakeFez()

    y_train = get_labels_fromNoise(qc, historic_data, backend)
    y_train = y_train[5:]

    model = train_loop(x_train, y_train)

    backend = FakeFez()

    final_bound = predict_vqc_bound(model, x_train)
    print(final_bound)


if __name__ == '__main__':
    with open(r'C:\Users\jovin\Desktop\streamlit\QRE\trained_circuit_3.qpy', 'rb') as file:
        qc = qpy.load(file)[0]
    call_QuBound(qc, FakeFez())