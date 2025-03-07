import aqnsim

# 5 Players
# Each player receives 2 partial bell states, and 8 |+> states
# Constants
NUM_PLAYERS = 5
NUM_ROUNDS = 2
SEC = aqnsim.SECOND

class Player(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports=["distributor"],
            name=name
        )
        self.data_collector.register_attribute(self.name)
        self.bit_vector = []

        # Create polarizing beam splitter
        self.pbs = aqnsim.PolarizingBeamSplitter(sim_context=sim_context, name="pbs")

        # Create a photon detector for each output of the PBS. 
        self.detector0 = aqnsim.PhotonDetector(sim_context=sim_context, name="detector0")
        self.detector1 = aqnsim.PhotonDetector(sim_context=sim_context, name="detector1")
        
        # Do we need a hwp/qwp here? 

        # Connect the port of the node to the port of polarizing beam splitter
        self.ports["distributor"].forward_input_to_input(self.pbs.ports["qin0"])

        # The PBS has two outputs each going to an independent detector
        self.pbs.ports["qout0"].forward_output_to_input(self.detector0.ports["qin0"])
        self.pbs.ports["qout1"].forward_output_to_input(self.detector1.ports["qin0"])

class Distributor(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports=[f"player{i}" for i in range(NUM_PLAYERS)],
            name=name
        )
        self.data_collector.register_attribute(self.name)

        # create an optical switch to dynamically route qubits 

        self.optical_switch = aqnsim.OpticalSwitch(
            sim_context=sim_context, 
            num_n_ports=NUM_PLAYERS, 
            num_m_ports=NUM_PLAYERS, 
            name="OpticalSwitch")
        
        for i in range (NUM_PLAYERS):
            self.optical_switch.ports[f"m{i}"].forward_output_to_output(self.ports[f"player{i}"])

        # set up the entangled photon source and connect the output ports
        state_distribution = [(1, aqnsim.BELL_STATES_DENSITY["psi_plus"])]  # generate (1/sqrt(2))(|HV> + |VH>)
        state_model = aqnsim.StateModel(
        state_distribution=state_distribution, formalism=aqnsim.StateFormalisms.DENSITY_MATRIX
        )
        
        self.entangled_photon_source = aqnsim.EntangledPolarizationSource(
        sim_context=sim_context,
        state_model=state_model,
        name="entangled_photon_source",
        mode_shape=aqnsim.GaussianModeShape(frequency=2.1 * aqnsim.GIGAHERTZ, frequency_width=0.1 * aqnsim.GIGAHERTZ),
        )

        for i in range(2):
            self.entangled_photon_source.ports[f"qout{i}"].forward_output_to_input(self.optical_switch.ports[f"n{i}"])

        # create the single photon sources and connect the output ports

        state_distribution =  [(1, aqnsim.X_BASIS_DENSITY_STATES["plus"])] # generate (1/sqrt(2))(|H> + |V>)
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
            photon_source.ports["qout0"].forward_output_to_input(self.optical_switch.ports[f"n{i+2}"])

    def emit_qubits(self, n_port_forwarding_list):
        self.optical_switch.n_port_forwarding_list=n_port_forwarding_list
        self.sim_context.simlogger.info("EPR Pair cr")
        self.entangled_photon_source.trigger()
        self.sim_context.simlogger.info("Plus State cr")
        for i in range (NUM_PLAYERS-2):
            self.photon_source_list[i].trigger()

class DistributorProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node, name: str = None):
        super().__init__(sim_context=sim_context, node=node, name=name)
        self.distributor = node
    
    @aqnsim.process
    def run(self):
        current_round = 0
        while (current_round < NUM_ROUNDS):
            base_forwarding_list=list(range(NUM_PLAYERS))
            self.distributor.emit_qubits(base_forwarding_list)
            for k in range(1, NUM_PLAYERS): 
                forwarding_list = base_forwarding_list[::k] + [x for x in base_forwarding_list if x not in base_forwarding_list[::k]]
                self.distributor.emit_qubits(n_port_forwarding_list=forwarding_list)
            current_round += 1
            self.sim_context.simlogger.info(f"Finished round {current_round}")
            yield self.wait(1)  

class PlayerProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node, name: str = None):
        super().__init__(sim_context=sim_context, node=node, name=name)
        self.player = node

        # Generate cmsg probes and attach to detectors.
        peek_detector0_listener, detector0_outcomes = self.cmsg_listener_fn()
        peek_detector1_listener, detector1_outcomes = self.cmsg_listener_fn()

        self.player.detector0.ports["cout0"].add_rx_output_handler(peek_detector0_listener)
        self.player.detector1.ports["cout0"].add_rx_output_handler(peek_detector1_listener)
        self.player.bit_vector.append(detector0_outcomes)
        self.data_collector.update_attribute(self.player.name, value = self.player.bit_vector)
        self.player.bit_vector.append(detector1_outcomes)
        self.data_collector.update_attribute(self.player.name, value = self.player.bit_vector)

    def cmsg_listener_fn(self):
        """
        Capture CMessage data as it passes through a Port.
        This method is intended to be attached to a port that outputs CMessages.
        """

        captured_output = []

        def cmsg_listener(msg):
            nonlocal captured_output

            captured_output.append({
                "content": msg.content, 
            })         
        return cmsg_listener, captured_output

def setup_network(sim_context: aqnsim.SimulationContext, CHANNEL_LENGTH, attenuation) -> aqnsim.Network:
    alice = Player(sim_context = sim_context, name="Alice")
    bob = Player(sim_context = sim_context, name="Bob")
    charlie = Player(sim_context = sim_context, name="Charlie")
    david = Player(sim_context = sim_context, name="David")
    esther = Player(sim_context = sim_context, name="Esther")

    players = [alice, bob, charlie, david, esther]

    distributor = Distributor(sim_context = sim_context, name="ent_src")

    network = aqnsim.Network(sim_context=sim_context, nodes=[distributor]+players)

    # Setup the links

    fiber_link_alice = aqnsim.FiberLink(
        sim_context=sim_context, 
        length=CHANNEL_LENGTH, 
        attenuation_coeff=attenuation,
        noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
        name="Fiber_Link_Alice"
    )

    fiber_link_bob = aqnsim.FiberLink(
        sim_context=sim_context,
        length=CHANNEL_LENGTH, 
        attenuation_coeff=attenuation,
        noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
        name="Fiber_Link_Bob"
    )

    fiber_link_charlie = aqnsim.FiberLink(
        sim_context=sim_context, 
        length=CHANNEL_LENGTH, 
        attenuation_coeff=attenuation,
        noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
        name="Fiber_Link_Charlie"
    )

    fiber_link_david = aqnsim.FiberLink(
        sim_context=sim_context, 
        length=CHANNEL_LENGTH, 
        attenuation_coeff=attenuation,
        noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
        name="Fiber_Link_David"
    )

    fiber_link_esther = aqnsim.FiberLink(
        sim_context=sim_context,
        length=CHANNEL_LENGTH, 
        attenuation_coeff=attenuation,
        noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
        name="Fiber_Link_Esther"
    )

    network.add_link(fiber_link_alice, distributor, alice, "player0", "distributor")
    network.add_link(fiber_link_bob, distributor, bob, "player1", "distributor")
    network.add_link(fiber_link_charlie, distributor, charlie, "player2", "distributor")
    network.add_link(fiber_link_david, distributor, david, "player3", "distributor")
    network.add_link(fiber_link_esther, distributor, esther, "player4", "distributor")

    DistributorProtocol(sim_context = sim_context, node = distributor)
    for player in players:
        PlayerProtocol(sim_context = sim_context, node = player)
        
    return network

# Main entry point
if __name__ == "__main__":

    run_simulation = aqnsim.generate_run_simulation_fn(
        setup_sim_fn=setup_network, logging_level=20, log_to_file=False
    )

    sim_results = aqnsim.run_simulations(
    run_simulation_fn=run_simulation, batch_parameters=[[10000,.00001]]
    )

    print (sim_results)