import aqnsim
from aqnsim.quantum_simulator import qubit_noise
from dataclasses import dataclass, field
import importlib
import config
# from protocol.config import NUM_PLAYERS, COMMANDER_NAME, LIEUTENANT_NAMES, N, NUM_LIEUTENANTS, DISTRIBUTOR_NAME
from protocol.config import SimulationConfig, NoiseType
# M = config.M

"""
DEFINE BASE PLAYER CLASS
"""

class Player(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str, sim_config: SimulationConfig):
        self.sim_config = sim_config
        
        super().__init__(
            sim_context=sim_context,
            ports=[self.sim_config.DISTRIBUTOR_NAME] + [self.sim_config.COMMANDER_NAME] + self.sim_config.LIEUTENANT_NAMES, # All-to-all classical communication; port with your own name isn't used
            name=name
        )
        self.data_collector.register_attribute(self.name)
        self.bit_vector = []

        self.qmemory = aqnsim.QMemory(
            sim_context=self.sim_context,
            n=1,
            ports=[sim_config.DISTRIBUTOR_NAME], 
            name=f"QMemory-{name}",
        )

    @aqnsim.process
    def measure_qubit(self):
        # if (self.sim_config.NOISE_TYPE == NoiseType.Pauli and sum(self.sim_config.NOISE_VALS) > 0):
        #     # print(self.qmemory.positions[0].peek())
        #     qubit_noise.apply_pauli_noise(self.qs, self.sim_config.NOISE_VALS[0], self.sim_config.NOISE_VALS[0], self.sim_config.NOISE_VALS[0], self.sim_config.NOISE_VALS[0], self.qmemory.positions[0].peek())
            # self.qmemory.positions[0].put(qubict_noise.apply_pauli_noise(self.qs, self.sim_config.NOISE_VALS[0], self.sim_config.NOISE_VALS[1], self.sim_config.NOISE_VALS[2], self.sim_config.NOISE_VALS[3], self.qmemory.positions[0].peek()))
            # meas_result = noisy_qubit.
                
        meas_result = yield self.qmemory.measure(0)
        self.bit_vector.append(meas_result)
        if len(self.bit_vector) == (self.sim_config.NUM_PLAYERS - 1) * self.sim_config.M:
            self.simlogger.info(f"All qubits recieved and measured by node {self.name}")
