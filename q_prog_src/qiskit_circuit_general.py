import qiskit
from qiskit import QuantumCircuit
from qiskit import qasm2, qasm3, qpy
from qiskit_ibm_runtime.fake_provider import FakeFez, FakeMarrakesh, FakeTorino
from qiskit import transpile
from qiskit.quantum_info import Statevector, state_fidelity

def display_circuit(qc: QuantumCircuit):
    return qc.draw("mpl")

def qasmFile_toCircuit(file):
    # qpy_content = file.read().decode("utf-8")
    # qc = qpy.load(qpy_content)[0]
    # qasm_content = file.read()

    # if "OPENQASM 3" in qasm_content[:100]:
    #     return qasm3.loads(qasm_content)
    # else:
    #     return qasm2.loads(qasm_content)
    return qpy.load(file)[0]
    
def transpile_optim(qc, backend, optim):
    backends = {
        "ibm_fez": FakeFez(),          
        "ibm_marrakesh": FakeMarrakesh(), 
        "ibm_torino": FakeTorino() 
    }

    provider = backends[backend]


    optim_qc = transpile(qc, backend=provider, optimization_level=optim,basis_gates=['sx', 'rz', 'cx', 'id'])
    return optim_qc

def simpleFidelityEstimator(qc):

    # qc = QuantumCircuit(2)
    # qc.h(0)
    # qc.cx(0, 1)
    # print(qc)

    qc = qc.remove_final_measurements(inplace=False) # remove the measurements since statevector doesnt do measurements
    print(qc)

    final_state = Statevector.from_instruction(qc)

    # Define the target state (e.g., (|00> + |11>)/sqrt(2))
    target_state = Statevector.from_label('0' * qc.num_qubits) 
    #Calculate fidelity
    fidelity = state_fidelity(final_state, target_state)
    print(f"Fidelity: {fidelity}")
    return fidelity

# with open("C:/Users/jovin/OneDrive/Desktop/streamlit/my_circuit.qpy", "rb") as f:
#     qc = qpy.load(f)[0]
# simpleFidelityEstimator(qc)