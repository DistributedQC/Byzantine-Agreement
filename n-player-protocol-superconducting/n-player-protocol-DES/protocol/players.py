import aqnsim
from dataclasses import dataclass, field
from protocol.config import NUM_PLAYERS, COMMANDER_NAME, LIEUTENANT_NAMES, N, M, NUM_LIEUTENANTS, DISTRIBUTOR_NAME

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
        if len(self.bit_vector) == (NUM_PLAYERS - 1) * M:
            self.simlogger.info(f"All qubits recieved and measured by node {self.name}")
