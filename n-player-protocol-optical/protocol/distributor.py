import aqnsim
from protocol.config import (
    COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER, COMMANDER_QMEMORY_ADDR,
    LIEUTENANT_NAMES, TRAITOR_INDICES,
    DISTRIBUTOR_NAME,
    NUM_PLAYERS, NUM_LIEUTENANTS, M, N,
)


class Distributor(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports= [COMMANDER_NAME] + [name for name in LIEUTENANT_NAMES],
            name=name
        )

        # Create an optical switch to dynamically route qubits and connect the output ports.
        self.optical_switch = aqnsim.OpticalSwitch(
        sim_context=sim_context, 
        num_n_ports=NUM_PLAYERS, 
        num_m_ports=NUM_PLAYERS, 
        name="OpticalSwitch")
        
        self.optical_switch.ports[f"m{0}"].forward_output_to_output(self.ports[COMMANDER_NAME])
        for i, lieutenant_name in enumerate(LIEUTENANT_NAMES):
            self.optical_switch.ports[f"m{i + 1}"].forward_output_to_output(self.ports[lieutenant_name])

        # Set up the entangled photon source and connect the output ports.
        state_distribution = [(1, aqnsim.BELL_STATES_DENSITY["psi_plus"])]  
        state_model = aqnsim.StateModel(
        state_distribution=state_distribution, formalism=aqnsim.StateFormalisms.DENSITY_MATRIX
        )
        
        self.entangled_photon_source = aqnsim.EntangledPolarizationSource(
        sim_context=sim_context,
        state_model=state_model,
        name="entangled_photon_source",
        mode_shape=aqnsim.GaussianModeShape(frequency=2.1 * aqnsim.GIGAHERTZ, frequency_width=0.1 * aqnsim.GIGAHERTZ),
        )
        for i in range (2):
            self.entangled_photon_source.ports[f"qout{i}"].forward_output_to_input(self.optical_switch.ports[f"n{i}"])

        # Create the single photon sources and connect the output ports.
        state_distribution =  [(1, aqnsim.X_BASIS_DENSITY_STATES["plus"])] 
        state_model = aqnsim.StateModel(
        state_distribution=state_distribution, formalism=aqnsim.StateFormalisms.DENSITY_MATRIX
        )
        
        self.photon_source_list=[]
        for i in range(NUM_PLAYERS-2):
            photon_source = aqnsim.PolarizationSource(
            sim_context=sim_context,
            state_model=state_model,
            name=f"photon_source_{i}",
            mode_shape=aqnsim.GaussianModeShape(2.1 * aqnsim.GIGAHERTZ, frequency_width=0.1 * aqnsim.GIGAHERTZ),
            )
            self.photon_source_list.append(photon_source)
            self.photon_source_list[i].ports["qout0"].forward_output_to_input(self.optical_switch.ports[f"n{i+2}"])
    
    def emit_qubits(self, n_port_forwarding_list):
        """
        Set the optical switch's port mapping and trigger each photon source.
        """
        self.optical_switch.set_port_mapping(n_port_forwarding_list)
        self.sim_context.simlogger.info("Trigger entangled photon source")
        self.entangled_photon_source.trigger()
        self.sim_context.simlogger.info("Trigger single photon sources")
        for i in range (NUM_PLAYERS-2):
            self.photon_source_list[i].trigger()
class DistributorProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node):
        super().__init__(sim_context=sim_context, node=node, name=node.name)
        self.distributor = node

    @aqnsim.process
    def run(self):
        current_round = 0
        while (current_round < M):
            base_forwarding_list=list(range(NUM_PLAYERS))
            for k in range(1, NUM_PLAYERS): 
                forwarding_list = base_forwarding_list[::k] + [x for x in base_forwarding_list if x not in base_forwarding_list[::k]]
                self.distributor.emit_qubits(n_port_forwarding_list=forwarding_list)
                yield self.wait(1)  
            current_round += 1
            self.sim_context.simlogger.info(f"Finished round {current_round}")

