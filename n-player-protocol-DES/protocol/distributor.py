import aqnsim
from protocol.config import SimulationConfig
# from protocol.config import (
#     COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER, COMMANDER_QMEMORY_ADDR,
#     LIEUTENANT_NAMES, TRAITOR_INDICES,
#     DISTRIBUTOR_NAME,
#     NUM_PLAYERS, NUM_LIEUTENANTS, N,
# )


class Distributor(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str, sim_config: SimulationConfig):
        # importlib.reload(config)
        # from protocol.config import M
        self.sim_config = sim_config
        
        super().__init__(
            sim_context=sim_context,
            ports= [self.sim_config.COMMANDER_NAME] + [name for name in self.sim_config.LIEUTENANT_NAMES],
            name=name
        )

        self.qmemory = aqnsim.QMemory(
            sim_context=self.sim_context,
            n=self.sim_config.NUM_PLAYERS,
            ports= [self.sim_config.COMMANDER_NAME] + [name for name in self.sim_config.LIEUTENANT_NAMES], 
            name=f"QMemory-{name}",
        )
        
        self.qmemory.ports[self.sim_config.COMMANDER_NAME].forward_output_to_output(self.ports[self.sim_config.COMMANDER_NAME])
        for lieutenant in self.sim_config.LIEUTENANT_NAMES:
            self.qmemory.ports[lieutenant].forward_output_to_output(self.ports[lieutenant])
        
        # Try using circuits instead looking at the quantum networks and protocols

    @aqnsim.process
    def create_epr_pair(self, q1_idx, q2_idx):
        yield self.qmemory.operate(aqnsim.ops.H, qpos=q1_idx)
        yield self.qmemory.operate(aqnsim.ops.X, qpos=q2_idx)
        yield self.qmemory.operate(aqnsim.ops.CNOT, qpos=[q1_idx, q2_idx])

    @aqnsim.process
    def create_plus_state(self, q_idx):
        yield self.qmemory.operate(aqnsim.ops.H, qpos=q_idx)

class DistributorProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node):
        super().__init__(sim_context=sim_context, node=node, name=node.name)
        self.distributor = node

    @aqnsim.process
    def run(self):
        current_tuple = 0
        while (current_tuple < self.node.sim_config.M):

            for j in range(self.node.sim_config.NUM_LIEUTENANTS):
                ### Distribute EPR Pair ###
                alice_idx = self.node.sim_config.COMMANDER_QMEMORY_ADDR  # Distributor prepares Alice's qubit in the N'th qmemory slot 
                player_j_idx = j % self.node.sim_config.NUM_LIEUTENANTS # Distributor prepares the Lieutenant's qubits in the first (N-1) qmemory slots
                player_name = self.node.sim_config.LIEUTENANT_NAMES[player_j_idx]
                yield self.distributor.create_epr_pair(alice_idx, player_j_idx)
                self.distributor.qmemory.positions[alice_idx].pop_replace(self.node.sim_config.COMMANDER_NAME)
                self.distributor.qmemory.positions[player_j_idx].pop_replace(player_name)
                # self.simlogger.info(f"EPR Pair ready for {COMMANDER_NAME} and {player_name} at indices {alice_idx} and {player_j_idx}")
                
                ### Distribute |+> States ###
                for player_k_idx in range(self.node.sim_config.NUM_LIEUTENANTS):
                    if player_k_idx == player_j_idx:
                        continue
                    yield self.distributor.create_plus_state(player_k_idx)
                    player_name = self.node.sim_config.LIEUTENANT_NAMES[player_k_idx]
                    self.distributor.qmemory.positions[player_k_idx].pop_replace(player_name)
                    
                yield self.wait(1)  # TODO: Can parameterize wait time

            ### Wait for each player to receive and measure their qubit ###
            current_tuple += 1
