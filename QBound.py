from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit import QuantumCircuit
from qiskit_aer.noise import NoiseModel
from qiskit_aer import AerSimulator
from qiskit.quantum_info import hellinger_distance  # state_fidelity and total variation distance are used for simple Fidelity calculations
from qiskit import transpile
from qiskit_ibm_runtime.fake_provider import FakeFez
from qiskit import qpy


from .qiskit_circuit_general import *

import torch
from torch import nn

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def get_gate_name_for_pair(properties, qubits):
    target_qubits = list(qubits)
    
    for gate_info in properties.gates:
        if gate_info.qubits == target_qubits:
            return gate_info.gate
            
    return None

def look_back_window_ForError(backend, date_selected = datetime.now()):
    look_back_days = 14
    historical_data = []

    if date_selected is None:
        date_selected = datetime.now()

    print(f"Starting data collection")

    for i in range(look_back_days, 0, -1):
        # target_date = datetime.now() - timedelta(days = i) # 
        target_date = date_selected - timedelta(days = i)
        # print(target_date)

        properties = backend.properties(datetime = target_date)

        historical_data.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "properties": properties
            })
        if i % 7 == 0:
            print("Half way done...") 
    return historical_data

def get_labels_fromNoise(qc, historic_data, backend):
    print("Getting error prediction labels from circuit nonoise and noise values")

    labels = []  # the error we want to predict

    # create a temp circuit, This was done in the q_adapt implementaiton, and compressVQC
    # qc = QuantumCircuit(2)
    # qc.h(0)
    # qc.cx(0, 1)
    qc.measure_all()
    # print(qc)

    qc = transpile(qc, backend, optimization_level=3)
    simulator = AerSimulator()
    # noise_model = NoiseModel
    nonoise_value = simulator.run(qc, shots = 2048).result().get_counts()

    for history in historic_data:
        properties = history['properties']
        noise_model = NoiseModel.from_backend(backend, properties)  # get the noise signature to replicate
        noisy_simulator = AerSimulator(noise_model = noise_model)
        noise_value = noisy_simulator.run(qc, shots = 2048).result().get_counts()

        # using true metric to calculate difference between probability distributions
        error = hellinger_distance(nonoise_value, noise_value)
        labels.append(error)

    return torch.tensor(labels, dtype = torch.float32)   # must convertt to tensor so it can be used in LSTm


def extract_time_series_from_historic(historical_data, qubit_indices = [0], gate_qubit = [(0,1)]):
    print("Starting Error values Extraction from historic data.")
    extracted_data = []

    for history in historical_data:
        date = history['date']
        properties = history['properties']

        row = {'date':date}


        # get the respective T1, T2, readout errors
        for i in qubit_indices:
            row[f'q{i}_t1'] = properties.t1(i)
            row[f'q{i}_t2'] = properties.t2(i)
            row[f'q{i}_readout_err'] = properties.readout_error(i)

        # getting the gate errors
        for g in gate_qubit:
            gate_name = get_gate_name_for_pair(properties, g)
            row[f'gate_err_{g[0]}_{g[1]}'] = properties.gate_error(gate_name, g)

        extracted_data.append(row)

    df  = pd.DataFrame(extracted_data).set_index('date')
    return df


# ---------- Perform QuDeCOM

def decompose_noise(df):
    print("breaking extracted df in to trend and residue.")
    trend = df.rolling(window=3, min_periods=1).mean()  # return the mean for the 3 rows and then the next following rows 
                                                        # then subtract form the df to get the residual
                                                        # essentially do 1d conolution with a window of 3
    residual = df - trend

    # extract the prdictable drift and unpredictable fluctuations, according to the paper
    return trend, residual 



#------------- encoding the drift and fluctuations, 
# into a feature vector for the LSTM
# lstm takes into consideratino of a sequence, hence this is necessary
def create_sequences(df, window_size=5):
    print("preprocessing lstm data ==")
    data = df.values
    sequences = []
    for i in range(len(data) - window_size):
        window = data[i : i + window_size]   # return the sequence/data form 0-5, 1-6, 2-7...
        sequences.append(window)
    return torch.tensor(np.array(sequences), dtype=torch.float32)   # convert to torch tensor, so that we can pass it to a lstm


#------------------------------
# Finally now that pre-processing is complete, 
# the LSTM model 
# or QuPRED
#--------------------------------
class QuPred(nn.Module):
    def __init__(self, input_features, blocks):
        super().__init__()
        self.lstm = nn.LSTM(input_features, blocks, batch_first=True)
        self.fc = nn.Linear(blocks, 1)

    def forward(self, x):
        _, (h_n, _) = self.lstm(x)
        return self.fc(h_n[-1])
    
# using stistical confidence for the loss to get the bound 
# for a bell curve to be with in the 95% of all the data, 
# that is the value should lie between 2 standard deviations of the mean
# taking the idea from the confidence table in the paper
# Statistical theory; we can be 95% sure that out data wont be away from the actual value
def loss_fn(preds, targets, confidence=0.95):
    errors = targets - preds
    return torch.max(confidence * errors, (confidence - 1) * errors).mean()

def train_loop(x_train, y_train):

    print("Entered Model training ...")
    # hyper parameters
    model = QuPred(input_features= 8, blocks = 16)
    optimizer = torch.optim.Adam(model.parameters(), lr = 0.01)
    epochs = 50

    # the actually training
    for epoch in range(epochs):
        model.train()
        model.zero_grad()

        predictions = model(x_train)  # remember that x train is of the size 9,5,4
        loss = loss_fn(predictions, y_train, confidence = 0.95)

        # calculate the gradients
        loss.backward()
        # make changes to the weights
        optimizer.step()

        if epoch % 10 == 0:
            print(f"Epoch {epoch} | Model Loss: {loss.item():.6f}")
    
    return model

def predict_vqc_bound(model, x_train):
    model.eval()
    with torch.no_grad():

        # model.eval()
        # with torch.no_grad():
        #     # Take the VERY LAST noise, which is today's noise to predict the performance
        #     latest_noise = x_train[-1].unsqueeze(0) 
        #     predicted_bound = model(latest_noise_sequence)
        #     print(f"The predicted error bound today: {predicted_bound.item():.4f}")

        latest_noise = x_train[-1].unsqueeze(0) 
        predicted_bound = model(latest_noise).item()
        
        return predicted_bound

# provider is the fake backend that will be used for transpiling and other uses
def call_QuBound(qc, provider, date = datetime.now()):
    token="ucK-WJCddM2wD85T6tXy3dSWpuj-FIH4GLw9kf48q7Bn"
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform", 
        token=token,
        # This tells Qiskit to specifically look for your free/open access
        plans_preference=["open"] 
    )

    backend = service.backend("ibm_fez")
    historic_data = look_back_window_ForError(backend, date)  # this uses the true backend, since we ened the history data, 
    # now using fake
    extracted_df = extract_time_series_from_historic(historic_data)
    trend_df, residual_df = decompose_noise(extracted_df)

    combined_df = pd.concat([trend_df, residual_df], axis=1)
    combined_df = combined_df.fillna(0)
    normalized_df = (combined_df - combined_df.mean()) / combined_df.std()

    x_train = create_sequences(normalized_df, window_size=5)
    y_train = get_labels_fromNoise(qc,historic_data, provider)
    y_train = y_train[5:].unsqueeze(1)

    model = train_loop(x_train, y_train)

    # qc = transpile(qc, backend, optimization_level=3)
    # depth = qc.depth()
    # gate_counts = qc.count_ops().get('ecr', 0) + qc.count_ops().get('cz', 0) + qc.count_ops().get('cx', 0)
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
        # This tells Qiskit to specifically look for your free/open access
        plans_preference=["open"] 
    )

    print(f"Connected using instance: {service.active_account()}")

    backend = service.backend("ibm_fez")
    # props = backend.properties()

    historic_data = look_back_window_ForError(backend)
    # print(historic_data)
    extracted_df = extract_time_series_from_historic(historic_data)
    # print(extracted_df.head(14))
    trend_df, residual_df = decompose_noise(extracted_df)
    # print(trend_df)
    # print()
    # print(residual_df)
    # Normalize before sequencing 
    combined_df = pd.concat([trend_df, residual_df], axis=1)
    combined_df = combined_df.fillna(0)
    normalized_df = (combined_df - combined_df.mean()) / combined_df.std()


    x_train = create_sequences(normalized_df, window_size=5)
    # print(f"Input shape for PyTorch: {x_train.shape}") 
    # return a [9,5,4] tensor which consists of the 9 sets of data, 5 is the window/previous days, and 4 is the T1, T1, readout and gate error
    backend = FakeFez()

    y_train = get_labels_fromNoise(qc, historic_data, backend)
    y_train = y_train[5:].unsqueeze(1)
    # print(y_train.shape)

    model = train_loop(x_train, y_train)

    # model.eval()
    # with torch.no_grad():
    #     # Take the VERY LAST sequence from your data (which includes the most recent noise)
    #     latest_noise_sequence = x_train[-1].unsqueeze(0) 
    #     predicted_bound = model(latest_noise_sequence)
    #     print(f"The predicted error bound today: {predicted_bound.item():.4f}")

    #------------ For given circuit get the prediction
    
    # qc.draw('mpl')

    backend = FakeFez()

    # qc = transpile(qc, backend, optimization_level=3)
    depth = qc.depth()
    gate_counts = qc.count_ops().get('ecr', 0) + qc.count_ops().get('cz', 0) + qc.count_ops().get('cx', 0)

    # why is this scaling factor necessary
    # REASON: the model is trained on a single gate for each of the basis gates
    #         but vqcs can have n number of gates/qubits, hence we need to scale the gates to the depth to help with it
    #      depth/2 => we only used a Handmard gate and cx gate, hence 2 depth, and scale based on it 
    #      gate_counts/1 => we only used one cx gate (2 qubit gate) hence 1, and scale based on it 
    # scaling_factor = (depth / 2.0) * (gate_counts / 1.0)

    final_bound = predict_vqc_bound(model, x_train)
    print(final_bound)
    


    


if __name__ == '__main__':
    with open(r'C:\Users\jovin\OneDrive\Desktop\streamlit\trained_circuit.qpy', 'rb') as file:
        qc = qpy.load(file)[0]
    # main()
    call_QuBound(qc, FakeFez())