import aqnsim
from aqnsim.networks.nodes.node import Node
import simpy
from dataclasses import dataclass, field
from eprq_dba.config import M, N



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

class Lieutenant(aqnsim.Node):
    def __init__(
        self,
        env: simpy.Environment,
        qs: aqnsim.QuantumSimulator,
        name: str,
        is_traitor: bool,
        bit_vector: list[bool | None],
        lieutenant_index: int,
        command_vector: list[bool | None] = field(default_factory=list),
        received_order: bool | None = None,
        initial_decision: bool | None = None,
        intermediate_decision: bool | None = None,
        final_decision: bool | None = None,
        proofs: dict[int, EvidenceBundle] = field(default_factory=dict)
    ):
        super().__init__(
            env=env, ports=["Alice"]+[f"lt_{i}" for i in range(N - 1) if i != lieutenant_index], name=name
        )

        self.qmemory = aqnsim.QMemory(
            env=self.env,
            qs=self.qs,
            n=M*(N-1),
            ports=["Alice"],
            name=f"QMemory-{name}",
        )
        # self.qmemory.ports[""].forward_output_to_output(self.ports[""])


class Commander(aqnsim.Node):
    def __init__(
        self,
        env: simpy.Environment,
        qs: aqnsim.QuantumSimulator,
        name: str,
        is_traitor: bool,
        bit_vector: list[bool | None],
        orders: list[bool]
    ):
        super().__init__(
            env=env, ports=[f"lt_{i}" for i in range(N)], name=name
        )

        self.qmemory = aqnsim.QMemory(
            env=self.env,
            qs=self.qs,
            n=M*(N-1),
            ports=["Alice"],
            name=f"QMemory-{name}",
        )
        # self.qmemory.ports[""].forward_output_to_output(self.ports[""])
