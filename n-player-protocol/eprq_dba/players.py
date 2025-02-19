from dataclasses import dataclass, field
import numpy as np
import math
from aqnsim.quantum_simulator.simulation_engine_backends.cirq.qubit_cirq import QubitCirq
from eprq_dba.quantum_source import quantum_source, qs
from eprq_dba.config import COMMANDER_NAME, LIEUTENANT_NAMES, M, N

@dataclass
class InitialEvidence:
    decision: bool | None = None  # Claim
    command_vector: list[bool | None] = field(default_factory=list)  # Evidence

@dataclass
class IntermediaryEvidence:
    decision: bool | None = None  # Claim
    command_vectors: list[list[bool | None]] = field(default_factory=list)  # Evidence

@dataclass
class EvidenceBundle:
    initial: InitialEvidence = field(default_factory=InitialEvidence)
    intermediary: IntermediaryEvidence = field(default_factory=IntermediaryEvidence)

@dataclass
class Player:
    name: str
    is_traitor: bool = False
    qubits: list[QubitCirq] = field(default_factory=list)
    bit_vector: list[bool | None] = field(default_factory=list)

    def measure_qubits(self):
        if not self.qubits:
            raise ValueError(f"Player {self.name} has no qubits to measure")
        for qubit in self.qubits:
            cbit = qs.measure(qubit, basis='Z')
            self.bit_vector.append(cbit)
            

@dataclass(kw_only=True)
class Lieutenant(Player):
    lieutenant_index: int
    command_vector: list[bool | None] = field(default_factory=list)
    received_order: bool | None = None
    initial_decision: bool | None = None
    intermediate_decision: bool | None = None
    final_decision: bool | None = None
    proofs: dict[int, EvidenceBundle] = field(default_factory=dict)

    @staticmethod
    def approx_equal_int(actual: int, expected: int, tolerance: int = 0) -> bool:
        return abs(actual - expected) <= tolerance

    @staticmethod
    def T_i_x(v: list[bool | None], i: int, x: bool) -> set[int]:
        """
        Returns the set of tuple indices k (0 <= k < m) for which the i-th element
        (0 <= i < n-1) of the k-th tuple in v equals x.
        """
        result = set()
        tuple_length = N - 1
        for k in range(M):
            pos = tuple_length * k + i
            if v[pos] is not None and v[pos] == x:
                result.add(k)
        return result

    @staticmethod
    def T_i_x_j_y(v: list[bool | None], i: int, j: int, x: bool, y: bool) -> set[int]:
        """
        Returns the set of tuple indices k (0 <= k < m) for which:
          - The i-th element of the k-th tuple equals x, and
          - The j-th element of the k-th tuple equals y.
        Here, 0 <= i, j < n-1 and i != j.
        """
        result = set()
        tuple_length = N - 1
        for k in range(M):
            pos_i = tuple_length * k + i
            pos_j = tuple_length * k + j
            if (v[pos_i] is not None and v[pos_j] is not None and
                v[pos_i] == x and v[pos_j] == y):
                result.add(k)
        return result
        
    def check_alice(self, tolerance: int = 0) -> bool:
        """
        Check Alice's (commander's) command vector against this lieutenant's bit vector.
        Returns True if consistent.
        """

        if self.received_order is None:
            raise ValueError(f"No order specified for lieutenant {self.lieutenant_index}")

        T = self.T_i_x(v = self.command_vector, i = self.lieutenant_index, x = self.received_order)
        if not self.approx_equal_int(len(T), M // 2, tolerance):
            return False

        # The protocol expects anti-correlation in every tuple
        tuple_length = N - 1
        for k in range(M):
            pos = tuple_length * k + self.lieutenant_index
            if self.command_vector[pos] == self.bit_vector[pos]:
                return False
        return True

    def check_lieutenant_by_command_vector(self, j: int, c: bool, j_command_vector: list[bool | None], tolerance: int = 0) -> bool:
        """
        Check another lieutenant's command vector against this lieutenant's bit vector.
        """

        if c is None:
            raise ValueError(f"Order must be certain not {c}")
        if not j_command_vector:
            raise ValueError(f"Command vector must be concrete not {j_command_vector}")
            
        T1 = self.T_i_x_j_y(v = j_command_vector, i = self.lieutenant_index, j = j, x = c, y = c)
        if not self.approx_equal_int(len(T1), M // 4, tolerance):
            return False

        T2 = self.T_i_x_j_y(v = j_command_vector, i = self.lieutenant_index, j = j, x = (not c), y = c)
        if not self.approx_equal_int(len(T2), M // 4, tolerance):
            return False

        T3 = self.T_i_x_j_y(v = self.command_vector, i = self.lieutenant_index, j = j, x = (not c), y = c)
       
        if not self.approx_equal_int(len(T2.symmetric_difference(T3)), 0, tolerance):
            return False    
        return True

    def check_lieutenant_by_bit_vector(self, j: int, c: bool, j_command_vector: list[bool | None], tolerance: int = 0) -> bool:
        """
        Check another lieutenant's command vector against this lieutenant's bit vector.
        """
        T1 = self.T_i_x_j_y(v = j_command_vector, i = self.lieutenant_index, j = j, x = c, y = c)
        if not self.approx_equal_int(len(T1), M // 4, tolerance):
            return False

        T2 = self.T_i_x_j_y(v = j_command_vector, i = self.lieutenant_index, j = j, x = (not c), y = c)
        if not self.approx_equal_int(len(T2), M // 4, tolerance):
            return False

        tuple_length = N - 1
        for k in range(M):
            pos = tuple_length * k + self.lieutenant_index
            if j_command_vector[pos] == self.bit_vector[pos]:
                return False
        return True

@dataclass(kw_only=True)
class Commander(Player):
    orders: list[bool]

    def distribute_entanglement(self, lieutenants: list[Lieutenant]) -> None:

        total_pairs = M * len(lieutenants)
        def designate_owner_for_pair(lieutenants: list[Lieutenant], k: int) -> int:
            return k % len(lieutenants)
            
        for k in range(total_pairs):
            j = designate_owner_for_pair(lieutenants, k)
            q1, q2 = quantum_source.create_epr_pair()
            self.qubits.append(q1)
            lieutenants[j].qubits.append(q2)
            for i in range(len(lieutenants)):
                if i == j:
                    continue
                q = quantum_source.create_plus_state()
                lieutenants[i].qubits.append(q)
    
    def construct_command_vector(self, lieutenant_index: int) -> list[bool | None]:
        """
        Construct a command vector for a given lieutenant based on Alice's bit string.
        This function uses a simple scheme: reveal tuples that correspond to this lieutenant's entangled positions, 
        hide others with placeholders.
        """
        command_vector = []
        tuple_length = N - 1
        
        if lieutenant_index >= len(self.orders):
            raise IndexError(f"No order specified for lieutenant {lieutenant_index}")
            
        order_for_lieutenant = self.orders[lieutenant_index]
        
        for k in range(M):
            start_index = k * tuple_length
            end_index = (k + 1) * tuple_length
            tuple_k = self.bit_vector[start_index:end_index]
            if self.bit_vector[k*(N-1) + lieutenant_index] == order_for_lieutenant:
                command_vector.extend(tuple_k)
            else:
                command_vector.extend(tuple_length * [None])
        return command_vector
