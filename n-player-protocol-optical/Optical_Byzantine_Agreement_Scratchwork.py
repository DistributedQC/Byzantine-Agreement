import aqnsim
from functools import partial
from protocol.config import (
    COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER,
    LIEUTENANT_NAMES, TRAITOR_INDICES,
    DISTRIBUTOR_NAME,
    CHANNEL_LENGTH, ATTENUATION,
    CLASSICAL_CHANNEL_DELAY,
)

# 5 Players
# Each player receives 2 partial bell states, and 8 |+> states
# Constants
NUM_PLAYERS = 5
NUM_ROUNDS = 2
SEC = aqnsim.SECOND
CHANNEL_LENGTH = 10000
ATTENUATION = 0.00001

COMMANDER_NAME = 'Alice'
LIEUTENANT_NAMES = ['Bob', 'Charlie', 'David', 'Esther']
class Player(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports=[DISTRIBUTOR_NAME],
            name=name
        )
        self.data_collector.register_attribute(self.name)
        self.bit_vector = []

        # Create a polarizing beam splitter.
        self.pbs = aqnsim.PolarizingBeamSplitter(sim_context=sim_context, name="pbs")
        self.add_subcomponent(self.pbs)

        # Create a photon detector for each output of the PBS. 
        self.detector0 = aqnsim.PhotonDetector(sim_context=sim_context, name="detector0")
        self.detector1 = aqnsim.PhotonDetector(sim_context=sim_context, name="detector1")
        self.add_subcomponent(self.detector0)
        self.add_subcomponent(self.detector1)

        # Connect the port of the player to the port of polarizing beam splitter.
        self.ports[DISTRIBUTOR_NAME].forward_input_to_input(self.pbs.ports["qin0"])

        # The PBS has two outputs each going to an independent detector.
        self.pbs.ports["qout0"].forward_output_to_input(self.detector0.ports["qin0"])
        self.pbs.ports["qout1"].forward_output_to_input(self.detector1.ports["qin0"])

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
        for i, name in enumerate(LIEUTENANT_NAMES):
            self.optical_switch.ports[f"m{i + 1}"].forward_output_to_output(self.ports[name])

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
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node, name: str = None):
        super().__init__(sim_context=sim_context, node=node, name=name)
        self.distributor = node
    
    @aqnsim.process
    def run(self):
        """
        Distribute the qubits as described by the protocol.
        """
        current_round = 0
        while (current_round < NUM_ROUNDS):
            base_forwarding_list=list(range(NUM_PLAYERS))
            for k in range(1, NUM_PLAYERS): 
                forwarding_list = base_forwarding_list[::k] + [x for x in base_forwarding_list if x not in base_forwarding_list[::k]]
                self.distributor.emit_qubits(n_port_forwarding_list=forwarding_list)
                yield self.wait(1)  
            current_round += 1
            self.sim_context.simlogger.info(f"Finished round {current_round}")

class PlayerProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node, name: str = None):
        super().__init__(sim_context=sim_context, node=node, name=name)
        self.player = node

        # Set up measurement handlers to process results from the photon detectors.
        measurement_handler_HV_0 = partial(self._measurement_handler, detection=0)
        measurement_handler_HV_1 = partial(self._measurement_handler, detection=1)

        # Generate photon detector port handlers.
        self.player.detector0.ports["cout0"].add_rx_output_handler(measurement_handler_HV_0)
        self.player.detector1.ports["cout0"].add_rx_output_handler(measurement_handler_HV_1)


    def _measurement_handler(self, msg, detection):
        """
        Measurement handler to process measurement results from the photon detectors.
        """
        self.simlogger.info(f"measurement_handler at node {self.node.name}, msg: {msg}")
        self.player.bit_vector.append(detection)
        self.data_collector.update_attribute(self.player.name, value = self.player.bit_vector)

def setup_network(sim_context: aqnsim.SimulationContext) -> aqnsim.Network:
    """
    Set up the network and attach the node protocols.
    """
    # Instantiate the players, distributor, and network.

    players = [
        Player(sim_context = sim_context, name=COMMANDER_NAME)
    ]
    for name in LIEUTENANT_NAMES:
        players.append(Player(sim_context = sim_context, name=name))

    distributor = Distributor(sim_context = sim_context, name="ent_src")

    network = aqnsim.Network(sim_context=sim_context, nodes=[distributor]+players)

    # Set up the fiber links.
    # fiber_link_alice = aqnsim.FiberLink(
    #     sim_context=sim_context, 
    #     length=CHANNEL_LENGTH, 
    #     attenuation_coeff=ATTENUATION,
    #     noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
    #     name="Fiber_Link_Alice"
    # )

    # fiber_link_bob = aqnsim.FiberLink(
    #     sim_context=sim_context,
    #     length=CHANNEL_LENGTH, 
    #     attenuation_coeff=ATTENUATION,
    #     noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
    #     name="Fiber_Link_Bob"
    # )

    # fiber_link_charlie = aqnsim.FiberLink(
    #     sim_context=sim_context, 
    #     length=CHANNEL_LENGTH, 
    #     attenuation_coeff=ATTENUATION,
    #     noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
    #     name="Fiber_Link_Charlie"
    # )

    # fiber_link_david = aqnsim.FiberLink(
    #     sim_context=sim_context, 
    #     length=CHANNEL_LENGTH, 
    #     attenuation_coeff=ATTENUATION,
    #     noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
    #     name="Fiber_Link_David"
    # )

    # fiber_link_esther = aqnsim.FiberLink(
    #     sim_context=sim_context,
    #     length=CHANNEL_LENGTH, 
    #     attenuation_coeff=ATTENUATION,
    #     noise_model=aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
    #     name="Fiber_Link_Esther"
    # )

    # network.add_link(fiber_link_alice, distributor, players[0], players[0].name, DISTRIBUTOR_NAME)
    # network.add_link(fiber_link_bob, distributor, players[1], players[1].name, DISTRIBUTOR_NAME)
    # network.add_link(fiber_link_charlie, distributor, players[2], players[2].name, DISTRIBUTOR_NAME)
    # network.add_link(fiber_link_david, distributor, players[3], players[3].name, DISTRIBUTOR_NAME)
    # network.add_link(fiber_link_esther, distributor, players[4], players[4].name, DISTRIBUTOR_NAME)

    for player in players:
        fiber = aqnsim.FiberLink(
            sim_context = sim_context,
            length=CHANNEL_LENGTH,
            attenuation_coeff=ATTENUATION,
            noise_model= aqnsim.AmplitudeDampNoiseModel(sim_context.qs),
            name=f"Fiber_Link_{player.name}_{DISTRIBUTOR_NAME}"       
        )
        network.add_link(fiber, distributor, player, player.name, DISTRIBUTOR_NAME)

    # Attach the node protocols.
    DistributorProtocol(sim_context = sim_context, node = distributor)
    for player in players:
        PlayerProtocol(sim_context = sim_context, node = player)
        
    return network

def loss_handling(simulation_results):
    """
    For each timestamp, if at least one player experienced photon loss, the corresponding bit is removed
    from the bit vectors of all players who did not experience photon loss at that timestamp.
    """
    # Step 1: Round timestamps for each player
    rounded_data = {
        player: [(bit_vector, round(ts)) for bit_vector, ts in updates]
        for player, updates in simulation_results.items()
    }

    # Step 2: Collect all possible timestamps
    all_timestamps = list(range(0,(NUM_PLAYERS-1)*NUM_ROUNDS))

    # Step 3: Collect all collected timestamps from players
    player_timestamps = {player: {ts for _, ts in updates} for player, updates in rounded_data.items()}

    # Step 4: Identify timestamps that must be removed
    missing_timestamps = [ts for ts in all_timestamps if not all(ts in player_timestamps[player] for player in rounded_data)]

    # Step 5: For each missing timestamp, remove the bit with that index from players who have that timestamp
    for ts in missing_timestamps:
        for player, updates in rounded_data.items():
            # Track how many bits have been removed so far for each player
            bits_removed = 0
            updated_player_data = []
            
            for idx, (bit_vector, timestamp) in enumerate(updates):
                if timestamp == ts:
                    # Remove the bit at the correct index adjusted for previously removed bits
                    bit_vector.pop(idx - bits_removed) 
                    bits_removed += 1
                else:
                    updated_player_data.append((bit_vector, timestamp))
            
            # Update the player's data (after removing the bit corresponding to the missing timestamp)
            rounded_data[player] = updated_player_data
    return rounded_data

# Run the simulation(s).
if __name__ == "__main__":

    run_simulation = aqnsim.generate_run_simulation_fn(
        setup_sim_fn=setup_network, logging_level=20, log_to_file=False
    )

    # sim_results = aqnsim.run_simulations(
    # run_simulation_fn=run_simulation
    # )

    results = run_simulation()

    loss_handling(results)