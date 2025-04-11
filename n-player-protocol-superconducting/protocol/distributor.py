import aqnsim
import numpy as np
from protocol.config import (
    COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER, COMMANDER_QMEMORY_ADDR,
    LIEUTENANT_NAMES, TRAITOR_INDICES,
    DISTRIBUTOR_NAME,
    NUM_PLAYERS, NUM_LIEUTENANTS, M, N,
    NOISE_TIME, T1_TIME,
)


class Distributor(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports= [COMMANDER_NAME] + [name for name in LIEUTENANT_NAMES],
            name=name
        )

        self.qmemory = aqnsim.QMemory(
            sim_context=self.sim_context,
            n=NUM_PLAYERS,
            ports= [COMMANDER_NAME] + [name for name in LIEUTENANT_NAMES], 
            name=f"QMemory-{name}",
            # DO T1 NOISE HERE BEFORE SENDING QUBIT FOR NOW
            idle_noise = {qubit_position: aqnsim.T1NoiseModel(qs=sim_context.qs, relaxation_time=T1_TIME, name = "T1") for qubit_position in range(N)}
        )
        
        self.qmemory.ports[COMMANDER_NAME].forward_output_to_output(self.ports[COMMANDER_NAME])
        for lieutenant in LIEUTENANT_NAMES:
            self.qmemory.ports[lieutenant].forward_output_to_output(self.ports[lieutenant])

    @aqnsim.process
    def create_epr_pair(self, q1_idx, q2_idx):
        circuit = aqnsim.QCircuit(n=2)
        circuit.add_op(aqnsim.ops.RX(np.pi), qpos=q2_idx)
        circuit.add_op(aqnsim.ops.SQRTISWAP, qpos=[q1_idx, q2_idx])
        yield self.qmemory.run_circuit(circuit=circuit)

    @aqnsim.process
    def create_plus_state(self, q_idx):
        circuit = aqnsim.QCircuit(n=2)
        circuit.add_op(aqnsim.ops.RX(np.pi), qpos=q_idx)
        circuit.add_op(aqnsim.ops.RY(np.pi / 2), qpos=q_idx)
        yield self.qmemory.run_circuit(circuit=circuit)
    

class DistributorProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node):
        super().__init__(sim_context=sim_context, node=node, name=node.name)
        self.distributor = node

    @aqnsim.process
    def run(self):
        current_tuple = 0
        while (current_tuple < M):

            for j in range(NUM_LIEUTENANTS):
                ### Distribute EPR Pair ###
                alice_idx = COMMANDER_QMEMORY_ADDR  # Distributor prepares Alice's qubit in the N'th qmemory slot 
                player_j_idx = j % NUM_LIEUTENANTS # Distributor prepares the Lieutenant's qubits in the first (N-1) qmemory slots
                player_name = LIEUTENANT_NAMES[player_j_idx]
                yield self.distributor.create_epr_pair(alice_idx, player_j_idx)
                yield self.wait(NOISE_TIME) # LET NOISE APPLY
                self.distributor.qmemory.positions[alice_idx].pop_replace(COMMANDER_NAME)
                self.distributor.qmemory.positions[player_j_idx].pop_replace(player_name)
                # self.simlogger.info(f"EPR Pair ready for {COMMANDER_NAME} and {player_name} at indices {alice_idx} and {player_j_idx}")
                
                ### Distribute |+> States ###
                for player_k_idx in range(NUM_LIEUTENANTS):
                    if player_k_idx == player_j_idx:
                        continue
                    yield self.distributor.create_plus_state(player_k_idx)
                    yield self.wait(NOISE_TIME) # LET NOISE APPLY
                    player_name = LIEUTENANT_NAMES[player_k_idx]
                    self.distributor.qmemory.positions[player_k_idx].pop_replace(player_name)
                    
                yield self.wait(1 - NOISE_TIME)  # TODO: Can parameterize wait time

            ### Wait for each player to receive and measure their qubit ###
            current_tuple += 1
