import aqnsim
from protocol.config import NUM_PLAYERS, NUM_ROUNDS, LIEUTENANT_NAMES, COMMANDER_NAME

class Distributor(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports= [COMMANDER_NAME] + [name for name in LIEUTENANT_NAMES],
            name=name
        )
        self.data_collector.register_attribute(self.name)

        self.qmemory = aqnsim.QMemory(
            sim_context=self.sim_context,
            n=NUM_PLAYERS,
            ports= [COMMANDER_NAME] + [name for name in LIEUTENANT_NAMES], 
            name=f"QMemory-{name}",
        )
        
        self.qmemory.ports[COMMANDER_NAME].forward_output_to_output(self.ports[COMMANDER_NAME])
        for lieutenant in LIEUTENANT_NAMES:
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