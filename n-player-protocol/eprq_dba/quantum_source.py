import aqnsim
from aqnsim.quantum_simulator import quantum_operations as ops

qs = aqnsim.QuantumSimulator()
class QuantumSource:
    def create_epr_pair(self):
        q1 = qs.create_qubit()
        q2 = qs.create_qubit()
        qs.apply_operation(ops.H, q1)
        qs.apply_operation(ops.X, q2)
        qs.apply_operation(ops.CNOT, [q1, q2])
        return q1, q2

    def create_plus_state(self):
        q = qs.create_qubit()
        qs.apply_operation(ops.H, q)
        return q

quantum_source = QuantumSource()
