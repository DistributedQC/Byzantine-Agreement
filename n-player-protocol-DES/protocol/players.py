import aqnsim
from dataclasses import dataclass, field
from protocol.config import NUM_PLAYERS, NUM_ROUNDS, COMMANDER_NAME, LIEUTENANT_NAMES, N, M, NUM_LIEUTENANTS, DISTRIBUTOR_NAME

"""
DEFINE BASE PLAYER CLASS
"""

class Player(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports=[DISTRIBUTOR_NAME] + [COMMANDER_NAME] + LIEUTENANT_NAMES, # All-to-all classical communication; port with your own name isn't used
            name=name
        )
        self.data_collector.register_attribute(self.name)
        self.bit_vector = []

        self.qmemory = aqnsim.QMemory(
            sim_context=self.sim_context,
            n=1,
            ports=[DISTRIBUTOR_NAME], 
            name=f"QMemory-{name}",
        )

    @aqnsim.process
    def measure_qubit(self):
        meas_result = yield self.qmemory.measure(0)
        self.bit_vector.append(meas_result)
        if len(self.bit_vector) == (NUM_PLAYERS - 1) * NUM_ROUNDS:
            self.simlogger.info(f"All qubits recieved and measured by node {self.name}")

# """
# DEFINE DATACLASSES FOR EVIDENCE
# """

# @dataclass
# class InitialEvidence:
#     decision: bool | None = None  # Claim
#     command_vector: list[bool | None] = field(default_factory=list)  # Evidence

# @dataclass
# class IntermediaryEvidence:
#     decision: bool | None = None  # Claim
#     command_vectors: list[list[bool | None]] = field(default_factory=list)  # Evidence

# @dataclass
# class EvidenceBundle:
#     initial: InitialEvidence = field(default_factory=InitialEvidence)
#     intermediary: IntermediaryEvidence = field(default_factory=IntermediaryEvidence)

# """
# DEFINE LIEUTENANT AND COMMANDER
# """

# @dataclass
# class LieutenantCMemory:
#     name: str
#     lieutenant_index: int
#     is_traitor: bool = False
#     bit_vector: list[bool | None] = field(default_factory=list)
#     command_vector: list[bool | None] = field(default_factory=list)
#     received_order: bool | None = None
#     initial_decision: bool | None = None
#     intermediate_decision: bool | None = None
#     final_decision: bool | None = None
#     intermediary_proofs: dict[int, IntermediaryEvidence] = field(default_factory=dict) # Used for counting, merged into "proofs" once filled
#     proofs: dict[int, EvidenceBundle] = field(default_factory=dict)


# class Lieutenant(Player):
#     def __init__(self, sim_context: aqnsim.SimulationContext, name: str, lieutenant_index: int, is_traitor: bool):
#         super().__init__(sim_context=sim_context, name=name)

#         # Quantum Memory is initialized by the parent Player class

#         # Setup Classical Memory
#         self.memory = LieutenantCMemory(name=name, lieutenant_index=lieutenant_index, is_traitor=is_traitor, bit_vector = self.bit_vector)  # Shared reference for bit_vector!
    
#     @staticmethod
#     def approx_equal_int(actual: int, expected: int, tolerance: int = 0) -> bool:
#         return abs(actual - expected) <= tolerance

#     @staticmethod
#     def T_i_x(v: list[bool | None], i: int, x: bool) -> set[int]:
#         """
#         Returns the set of tuple indices k (0 <= k < m) for which the i-th element
#         (0 <= i < n-1) of the k-th tuple in v equals x.
#         """
#         result = set()
#         tuple_length = N - 1
#         for k in range(M):
#             pos = tuple_length * k + i
#             if v[pos] is not None and v[pos] == x:
#                 result.add(k)
#         return result

#     @staticmethod
#     def T_i_x_j_y(v: list[bool | None], i: int, j: int, x: bool, y: bool) -> set[int]:
#         """
#         Returns the set of tuple indices k (0 <= k < m) for which:
#           - The i-th element of the k-th tuple equals x, and
#           - The j-th element of the k-th tuple equals y.
#         Here, 0 <= i, j < n-1 and i != j.
#         """
#         result = set()
#         tuple_length = N - 1
#         for k in range(M):
#             pos_i = tuple_length * k + i
#             pos_j = tuple_length * k + j
#             if (v[pos_i] is not None and v[pos_j] is not None and
#                 v[pos_i] == x and v[pos_j] == y):
#                 result.add(k)
#         return result
        
#     def check_alice(self, tolerance: int = 0) -> bool:
#         """
#         Check Alice's (commander's) command vector against this lieutenant's bit vector.
#         Returns True if consistent.
#         """

#         if self.memory.received_order is None:
#             raise ValueError(f"No order specified for lieutenant {self.memory.lieutenant_index}")

#         T = self.T_i_x(v = self.memory.command_vector, i = self.memory.lieutenant_index, x = self.memory.received_order)
#         if not self.approx_equal_int(len(T), M // 2, tolerance):
#             return False

#         # The protocol expects anti-correlation in every tuple
#         tuple_length = N - 1
#         for k in range(M):
#             pos = tuple_length * k + self.memory.lieutenant_index
#             if self.memory.command_vector[pos] == self.memory.bit_vector[pos]:
#                 return False
#         return True

#     def check_lieutenant_by_command_vector(self, j: int, c: bool, j_command_vector: list[bool | None], tolerance: int = 0) -> bool:
#         """
#         Check another lieutenant's command vector against this lieutenant's bit vector.
#         """

#         if c is None:
#             raise ValueError(f"Order must be certain not {c}")
#         if not j_command_vector:
#             raise ValueError(f"Command vector must be concrete not {j_command_vector}")
            
#         T1 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = c, y = c)
#         if not self.approx_equal_int(len(T1), M // 4, tolerance):
#             return False

#         T2 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = (not c), y = c)
#         if not self.approx_equal_int(len(T2), M // 4, tolerance):
#             return False

#         T3 = self.T_i_x_j_y(v = self.memory.command_vector, i = self.memory.lieutenant_index, j = j, x = (not c), y = c)
       
#         if not self.approx_equal_int(len(T2.symmetric_difference(T3)), 0, tolerance):
#             return False    
#         return True

#     def check_lieutenant_by_bit_vector(self, j: int, c: bool, j_command_vector: list[bool | None], tolerance: int = 0) -> bool:
#         """
#         Check another lieutenant's command vector against this lieutenant's bit vector.
#         """
#         T1 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = c, y = c)
#         if not self.approx_equal_int(len(T1), M // 4, tolerance):
#             return False

#         T2 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = (not c), y = c)
#         if not self.approx_equal_int(len(T2), M // 4, tolerance):
#             return False

#         tuple_length = N - 1
#         for k in range(M):
#             pos = tuple_length * k + self.memory.lieutenant_index
#             if j_command_vector[pos] == self.memory.bit_vector[pos]:
#                 return False
#         return True



# @dataclass
# class CommanderCMemory:
#     name: str
#     orders: list[bool]
#     is_traitor: bool = False
#     bit_vector: list[bool | None] = field(default_factory=list)
#     command_vectors:  dict[int, list[bool | None]] = field(default_factory=dict)


# class Commander(Player):
#     def __init__(self, sim_context: aqnsim.SimulationContext, name: str, orders: list[bool], is_traitor: bool):
#         super().__init__(sim_context=sim_context, name=name)

#         # Quantum Memory is initialized by the parent Player class

#         # Setup Classical Memory
#         self.memory = CommanderCMemory(name=name, orders=orders, is_traitor=is_traitor, bit_vector = self.bit_vector)  # Shared reference for bit_vector!

#     def construct_command_vectors(self):
#         for idx in range(NUM_LIEUTENANTS):
#             self.memory.command_vectors[idx] = self._construct_command_vector(idx)

#     def _construct_command_vector(self, lieutenant_index: int) -> list[bool | None]:
#         """
#         Construct a command vector for a given lieutenant based on Alice's bit string.
#         This function uses a simple scheme: reveal tuples that correspond to this lieutenant's entangled positions, 
#         hide others with placeholders.
#         """
#         command_vector = []
#         tuple_length = N - 1
        
#         if lieutenant_index >= len(self.memory.orders):
#             raise IndexError(f"No order specified for lieutenant {lieutenant_index}")
            
#         order_for_lieutenant = self.memory.orders[lieutenant_index]
        
#         for k in range(M):
#             start_index = k * tuple_length
#             end_index = (k + 1) * tuple_length
#             tuple_k = self.memory.bit_vector[start_index:end_index]
#             if self.memory.bit_vector[k*(NUM_LIEUTENANTS) + lieutenant_index] == order_for_lieutenant:
#                 command_vector.extend(tuple_k)
#             else:
#                 command_vector.extend(tuple_length * [None])
        
#         return command_vector