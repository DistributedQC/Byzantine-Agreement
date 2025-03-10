import aqnsim
from dataclasses import dataclass, field
from protocol.players import Player
from protocol.config import (
    COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER, COMMANDER_QMEMORY_ADDR,
    LIEUTENANT_NAMES, TRAITOR_INDICES,
    DISTRIBUTOR_NAME,
    NUM_PLAYERS, NUM_LIEUTENANTS, M, N,
    SEND_ORDER_ACTION, SEND_CV_ACTION, ROUND2_ACTION, ROUND3_ACTION
)

"""
DEFINE DATACLASSES FOR EVIDENCE
"""

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

"""
DEFINE LIEUTENANT AND COMMANDER
"""

@dataclass
class LieutenantCMemory:
    name: str
    lieutenant_index: int
    is_traitor: bool = False
    bit_vector: list[bool | None] = field(default_factory=list)
    command_vector: list[bool | None] = field(default_factory=list)
    received_order: bool | None = None
    initial_decision: bool | None = None
    intermediate_decision: bool | None = None
    final_decision: bool | None = None
    intermediary_proofs: dict[int, IntermediaryEvidence] = field(default_factory=dict) # Used for counting, merged into "proofs" once filled
    proofs: dict[int, EvidenceBundle] = field(default_factory=dict)


class Lieutenant(Player):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str, lieutenant_index: int, is_traitor: bool):
        super().__init__(sim_context=sim_context, name=name)

        # Quantum Memory is initialized by the parent Player class

        # Setup Classical Memory
        self.memory = LieutenantCMemory(name=name, lieutenant_index=lieutenant_index, is_traitor=is_traitor, bit_vector = self.bit_vector)  # Shared reference for bit_vector!
    
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

        if self.memory.received_order is None:
            raise ValueError(f"No order specified for lieutenant {self.memory.lieutenant_index}")

        T = self.T_i_x(v = self.memory.command_vector, i = self.memory.lieutenant_index, x = self.memory.received_order)
        if not self.approx_equal_int(len(T), M // 2, tolerance):
            return False

        # The protocol expects anti-correlation in every tuple
        tuple_length = N - 1
        for k in range(M):
            pos = tuple_length * k + self.memory.lieutenant_index
            if self.memory.command_vector[pos] == self.memory.bit_vector[pos]:
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
            
        T1 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = c, y = c)
        if not self.approx_equal_int(len(T1), M // 4, tolerance):
            return False

        T2 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = (not c), y = c)
        if not self.approx_equal_int(len(T2), M // 4, tolerance):
            return False

        T3 = self.T_i_x_j_y(v = self.memory.command_vector, i = self.memory.lieutenant_index, j = j, x = (not c), y = c)
       
        if not self.approx_equal_int(len(T2.symmetric_difference(T3)), 0, tolerance):
            return False    
        return True

    def check_lieutenant_by_bit_vector(self, j: int, c: bool, j_command_vector: list[bool | None], tolerance: int = 0) -> bool:
        """
        Check another lieutenant's command vector against this lieutenant's bit vector.
        """
        T1 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = c, y = c)
        if not self.approx_equal_int(len(T1), M // 4, tolerance):
            return False

        T2 = self.T_i_x_j_y(v = j_command_vector, i = self.memory.lieutenant_index, j = j, x = (not c), y = c)
        if not self.approx_equal_int(len(T2), M // 4, tolerance):
            return False

        tuple_length = N - 1
        for k in range(M):
            pos = tuple_length * k + self.memory.lieutenant_index
            if j_command_vector[pos] == self.memory.bit_vector[pos]:
                return False
        return True


class LieutenantProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: Lieutenant):
        super().__init__(sim_context=sim_context, node=node, name=node.name)

        self.node.ports[DISTRIBUTOR_NAME].add_rx_input_handler(
            handler=lambda msg: self.quantum_port_source_handler(msg=msg)
        )

        self.node.ports[COMMANDER_NAME].add_rx_input_handler(self.classical_port_commander_handler)

        for idx, lieutenant_name in enumerate(LIEUTENANT_NAMES):
            if idx == self.node.memory.lieutenant_index:
                continue
            self.node.ports[lieutenant_name].add_rx_input_handler(self.classical_port_lieutenant_handler)


    @aqnsim.process
    def quantum_port_source_handler(self, msg: aqnsim.Qubit):
        
        if isinstance(msg, aqnsim.Qubit):
            self.node.qmemory.positions[0].put(qubit=msg)
            yield self.node.measure_qubit() 

    @aqnsim.process
    def classical_port_commander_handler(self, msg: aqnsim.CMessage):
        
        # Round 1/2: 

        if isinstance(msg, aqnsim.CMessage):
            if msg.action == SEND_ORDER_ACTION:
                self.node.memory.received_order = msg.content
                # self.simlogger.info(f"{self.node.name} stored order {self.node.memory.received_order}")
                yield self.wait(0)
            elif msg.action == SEND_CV_ACTION:
                self.node.memory.command_vector = msg.content
                self.simlogger.info(f"{self.node.name} stored CV {self.node.memory.command_vector}")
                if self.node.check_alice(tolerance = M//10):
                    self.node.memory.initial_decision = self.node.memory.received_order
                else:
                    self.node.memory.initial_decision = None

                # SHARE COMMAND VECTOR WITH OTHERS 
                first_evidence_bundle = EvidenceBundle(
                    initial=InitialEvidence(
                        decision=self.node.memory.initial_decision,
                        command_vector=self.node.memory.command_vector
                    ),
                    # No intermediary evidence is sent yet
                    intermediary=IntermediaryEvidence())
                self.node.memory.proofs[self.node.memory.lieutenant_index] = first_evidence_bundle  # Save your own initial evidence
                for idx, lieutenant_name in enumerate(LIEUTENANT_NAMES):
                    if idx == self.node.memory.lieutenant_index:
                        continue
                    cv_message = aqnsim.CMessage(
                        sender=self.node.memory.lieutenant_index, action=ROUND2_ACTION, content=first_evidence_bundle
                    )
                    self.node.ports[lieutenant_name].rx_output(cv_message)
             
        # All done listening to Commander!

    @aqnsim.process
    def classical_port_lieutenant_handler(self, msg: aqnsim.CMessage):
        
        if isinstance(msg, aqnsim.CMessage):
            if msg.action == ROUND2_ACTION:
                self.node.memory.proofs[msg.sender] = msg.content
                if len(self.node.memory.proofs) == NUM_LIEUTENANTS:
                    self.simlogger.info(f"{self.node.name} received inital evidence bundles from all lieutenants")
                    # Rule 3.1
                    d_i = self.node.memory.initial_decision
                    collected_proofs = []  

                    received_decisions = [
                        bundle.initial.decision 
                        for sender_idx, bundle in self.node.memory.proofs.items()
                    ]

                    if all(d == d_i for d in received_decisions):
                        self.node.memory.intermediate_decision = d_i
                    elif d_i in (0, 1):
                        # Rule 3.2
                        if all(d == None for d in received_decisions):
                            self.node.memory.intermediate_decision = d_i
                    
                        else:
                            conflict_found = False
                            for sender_idx, bundle in self.node.memory.proofs.items():
                                if bundle.initial.decision == (not d_i):
                                    if self.node.check_lieutenant_by_command_vector(
                                        sender_idx,
                                        bundle.initial.decision,
                                        bundle.initial.command_vector,
                                        tolerance = M//10
                                    ):
                                        conflict_found = True
                                        collected_proofs.append(bundle.initial.command_vector)
                            # Rule 3.3/3.4
                            if conflict_found:
                                self.node.memory.intermediate_decision = None
                            else:
                                self.node.memory.intermediate_decision = d_i
                    else:  # d_i is None
                        valid_decisions = []
                        valid_proofs = []
                        for sender_idx, bundle in self.node.memory.proofs.items():
                            if bundle.initial.decision is not None:
                                if self.node.check_lieutenant_by_bit_vector(
                                    sender_idx,
                                    bundle.initial.decision,
                                    bundle.initial.command_vector,
                                    tolerance = M//10
                                ):
                                    valid_decisions.append(bundle.initial.decision)
                                    valid_proofs.append(bundle.initial.command_vector)
                        # Rule 3.5/3.6
                        if valid_decisions and all(d == valid_decisions[0] for d in valid_decisions):
                            self.node.memory.intermediate_decision = valid_decisions[0]
                            collected_proofs.append(valid_proofs[0])  # Send 1 CV as proof
                        else:
                            self.node.memory.intermediate_decision = d_i
                            unique_proofs = dict(zip(valid_decisions, valid_proofs))
                            contradicting_proofs = list(unique_proofs.values())[:2]  # Guarenteed to have exactly 2 values
                            collected_proofs.extend(contradicting_proofs)  # Send 2 contradicting CVs as proof
                        
                    # SEND INTERMEDIARY EVIDENCE FOR LIEUTENANT TO UPDATE THEIR EVIDENCE BUNDLE

                    intermediary_evidence = IntermediaryEvidence(
                        decision=self.node.memory.intermediate_decision,
                        command_vectors = collected_proofs
                    )
                    self.node.memory.intermediary_proofs[self.node.memory.lieutenant_index] = intermediary_evidence 
                    for idx, lieutenant_name in enumerate(LIEUTENANT_NAMES):
                        if idx == self.node.memory.lieutenant_index:
                            continue
                        cv_message = aqnsim.CMessage(
                            sender=self.node.memory.lieutenant_index, action=ROUND3_ACTION, content=intermediary_evidence
                        )
                        self.node.ports[lieutenant_name].rx_output(cv_message)
             
            if msg.action == ROUND3_ACTION:
                self.node.memory.intermediary_proofs[msg.sender] = msg.content
                if len(self.node.memory.intermediary_proofs) == NUM_LIEUTENANTS:
                    self.simlogger.info(f"{self.node.name} received intermediary evidence bundles from all lieutenants")

                    ## UPDATE PROOFS WITH INTERMEDIARY_PROOFS ##
                    for proof_id, intermediary_evidence in self.node.memory.intermediary_proofs.items():
                        self.node.memory.proofs[proof_id].intermediary = self.node.memory.intermediary_proofs[proof_id]

                    for i in range(1):  # Trivial loop to be able to break out of logic sequence with "continue"s
                        d_i = self.node.memory.intermediate_decision
                        # Rule 4.1
                        if (d_i == None and len(self.node.memory.proofs[i].intermediary.command_vectors) == 2):
                            self.node.memory.final_decision = d_i
                            continue

                        received_decisions = [
                            bundle.intermediary.decision 
                            for sender_idx, bundle in self.node.memory.proofs.items()
                        ]

                        # Rule 4.2
                        if all(d == d_i for d in received_decisions):
                            self.node.memory.final_decision = d_i
                            continue

                        if d_i in (0, 1):
                            conflict_found = False
                            if any(bundle.intermediary.decision is None and bundle.initial.decision is not None
                                for sender_idx, bundle in self.node.memory.proofs.items()):
                                for sender_idx, bundle in self.node.memory.proofs.items():
                                    # Verifying consistent application of Rule 3.3
                                    if bundle.intermediary.decision is None and bundle.initial.decision is not None:
                    
                                        if (bundle.intermediary.command_vectors and
                                            self.node.check_lieutenant_by_command_vector(
                                                sender_idx,
                                                bundle.initial.decision,
                                                bundle.intermediary.command_vectors[0],
                                                tolerance=M//10
                                            )):
                                            conflict_found = True
                                            break
                                # Rule 4.3/4.4
                                if conflict_found:
                                    self.node.memory.final_decision = None
                                else:
                                    self.node.memory.final_decision = d_i
                                continue 

                            conflict_found = False
                            for sender_idx, bundle in self.node.memory.proofs.items():
                                if bundle.intermediary.decision == (not d_i):
                                    if (bundle.intermediary.command_vectors and
                                        self.node.check_lieutenant_by_command_vector(
                                            sender_idx,
                                            bundle.intermediary.decision,
                                            bundle.intermediary.command_vectors[0],
                                            tolerance=M//10
                                        )):
                                            conflict_found = True
                                            break
            
                            # Rule 4.5/4.6
                            if conflict_found:
                                self.node.memory.final_decision = None
                            else:
                                self.node.memory.final_decision = d_i
                            continue
                    self.node.data_collector.update_attribute(self.name, {"is_traitor":self.node.memory.is_traitor,
                                                                          "received_order": self.node.memory.received_order,
                                                                          "initial_decision": self.node.memory.initial_decision,
                                                                          "intermediate_decision": self.node.memory.intermediate_decision,
                                                                          "final_decision": self.node.memory.final_decision})
                yield self.wait(0) # Trivial event