from protocol.players import Lieutenant, Commander, InitialEvidence, IntermediaryEvidence, EvidenceBundle
from protocol.distributor import Distributor
from protocol.config import NUM_PLAYERS, NUM_ROUNDS, COMMANDER_NAME, LIEUTENANT_NAMES, NUM_LIEUTENANTS, M, N, TRAITOR_INDICES, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER, ALICE_QMEMORY_ADDR
import aqnsim

SEC = aqnsim.SECOND
OP_DELAYS = {aqnsim.H: 1 * SEC, aqnsim.X: 1 * SEC, aqnsim.Z: 1 * SEC, aqnsim.CNOT: 1 * SEC}
MEAS_DELAY = 1 * SEC
PHI_PLUS_STATE_DENSITY = aqnsim.BELL_STATES_DENSITY["phi_plus"]
QSOURCE_STATE_DISTRIBUTION = [(1, PHI_PLUS_STATE_DENSITY)]
QSOURCE_NOISE_MODEL = None
QUANTUM_CHANNEL_DELAY = 1 * SEC
QUANTUM_CHANNEL_NOISE = 0.0
CLASSICAL_CHANNEL_DELAY = 1 * SEC

SEND_ORDER_ACTION = "SEND_ORDER"
SEND_CV_ACTION = "SEND_CV"
ROUND2_ACTION = "ROUND2_ACTION"

class DistributorProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: aqnsim.Node, name: str = None):
        super().__init__(sim_context=sim_context, node=node, name=name)
        self.distributor = node

    @aqnsim.process
    def run(self):
        current_tuple = 0
        while (current_tuple < M):

            for j in range(NUM_LIEUTENANTS):
                ### Distribute EPR Pair ###
                alice_idx = ALICE_QMEMORY_ADDR  # Distributor prepares Alice's qubit in the N'th qmemory slot 
                player_j_idx = j % NUM_LIEUTENANTS # Distributor prepares the Lieutenant's qubits in the first (N-1) qmemory slots
                player_name = LIEUTENANT_NAMES[player_j_idx]
                yield self.distributor.create_epr_pair(alice_idx, player_j_idx)
                self.distributor.qmemory.positions[alice_idx].pop_replace(COMMANDER_NAME)
                self.distributor.qmemory.positions[player_j_idx].pop_replace(player_name)
                # self.simlogger.info(f"EPR Pair ready for {COMMANDER_NAME} and {player_name} at indices {alice_idx} and {player_j_idx}")
                
                ### Distribute |+> States ###
                for player_k_idx in range(NUM_LIEUTENANTS):
                    if player_k_idx == player_j_idx:
                        continue
                    yield self.distributor.create_plus_state(player_k_idx)
                    player_name = LIEUTENANT_NAMES[player_k_idx]
                    self.distributor.qmemory.positions[player_k_idx].pop_replace(player_name)
                    
                yield self.wait(1)  # TODO: Can parameterize wait time

            ### Wait for each player to receive and measure their qubit ###
            current_tuple += 1



class CommanderProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: Commander):
        super().__init__(sim_context=sim_context, node=node, name=node.name)

        self.player = node
        self.player.ports["distributor"].add_rx_input_handler(
            handler=lambda msg: self.quantum_port_source_handler(msg=msg)
        )

        # Don't need a classical port handler because don't recieve any communication clasically

    @aqnsim.process
    def quantum_port_source_handler(self, msg: aqnsim.Qubit):
        
        if isinstance(msg, aqnsim.Qubit):
            self.player.qmemory.positions[0].put(qubit=msg)
            yield self.player.measure_qubit() 


    @aqnsim.process
    def run(self):

        entanglement_distribution_wait_time = M * NUM_LIEUTENANTS * 1 # Assuming 1 unit of time per round of distributing single qubits
        yield self.wait(entanglement_distribution_wait_time + 5)  # Tune this to start after entanglement distribution. TODO: Parameterize further if entanglement time parameterized 

        # Round 1-2: Send
        self.node.construct_command_vectors()

        for idx, lieutenant_name in enumerate(LIEUTENANT_NAMES):

            order = self.node.memory.orders[idx]
            order_message = aqnsim.CMessage(
                sender=self.node.name, action=SEND_ORDER_ACTION, content=order
            )
            self.node.ports[lieutenant_name].rx_output(order_message)

            command_vector = self.node.memory.command_vectors[idx]
            cv_message = aqnsim.CMessage(
                sender=self.node.name, action=SEND_CV_ACTION, content=command_vector
            )
            self.node.ports[lieutenant_name].rx_output(cv_message)

            # All done!


class LieutenantProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: Lieutenant):
        super().__init__(sim_context=sim_context, node=node, name=node.name)

        self.node.ports["distributor"].add_rx_input_handler(
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
                    self.node.initial_decision = self.node.memory.received_order
                else:
                    self.node.initial_decision = None

                # SHARE COMMAND VECTOR WITH OTHERS 
                first_evidence_bundle = EvidenceBundle(
                    initial=InitialEvidence(
                        decision=self.node.initial_decision,
                        command_vector=self.node.memory.command_vector
                    ),
                    # No intermediary evidence is sent yet
                    intermediary=IntermediaryEvidence())
                self.node.memory.proofs[self.node.memory.lieutenant_index] = first_evidence_bundle  # Save your own initial evidence
                for idx, lieutenant_name in enumerate(LIEUTENANT_NAMES):
                    cv_message = aqnsim.CMessage(
                        sender=self.node.memory.lieutenant_index, action=ROUND2_ACTION, status=aqnsim.StatusMessages.SUCCESS, content=first_evidence_bundle
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
                    received_decisions = [
                        bundle.initial.decision 
                        for sender_idx, bundle in self.node.memory.proofs.items()
                    ]
                    if all(d == d_i for d in received_decisions):
                        self.node.memory.intermediate_decision = d_i
                        # TODO: Continue writing rule 3 out! I think the rest of the way forward will just take 1-2 hours of quick work.



                    # Implement Round 3 down here


                yield self.wait(0) 






def setup_network(sim_context: aqnsim.SimulationContext) -> aqnsim.Network:

    if COMMANDER_IS_TRAITOR:
        orders = [random.choice([True, False]) for _ in LIEUTENANT_NAMES]
    else:
        orders = [LOYAL_COMMANDER_ORDER] * len(LIEUTENANT_NAMES)

    alice = Commander(
        sim_context = sim_context,
        name=COMMANDER_NAME,
        orders=orders,
        is_traitor = COMMANDER_IS_TRAITOR)


    lieutenants = [
        Lieutenant(
            sim_context = sim_context,
            name=name, 
            lieutenant_index=i,
            is_traitor=(i in TRAITOR_INDICES)
        )
        for i, name in enumerate(LIEUTENANT_NAMES)
    ]

    players = lieutenants + [alice]

    distributor = Distributor(sim_context = sim_context, name="ent_src")

    network = aqnsim.Network(sim_context=sim_context, nodes=[distributor]+players)

    for player in players:
        qlink = aqnsim.QuantumLink(
            sim_context = sim_context,
            delay = QUANTUM_CHANNEL_DELAY,
            noise = QUANTUM_CHANNEL_NOISE,
            name=f"Q_Link_{player.name}_distributor"       
        )
        network.add_link(qlink, distributor, player, player.name, "distributor")

    for player1 in players:
        for player2 in players:
            if player1 == player2:
                continue
            clink = aqnsim.ClassicalLink(
                sim_context = sim_context,
                delay = CLASSICAL_CHANNEL_DELAY,
                name=f"C_Link_{player1.name}_{player2.name}"       
            )
            network.add_link(clink, player1, player2, player2.name, player1.name)

    DistributorProtocol(sim_context = sim_context, node = distributor)
    CommanderProtocol(sim_context = sim_context, node = alice)
    for lieutenant in lieutenants:
        LieutenantProtocol(sim_context = sim_context, node = lieutenant)

    # Add C-link between players
        
    return network

if __name__ == "__main__":
    run_simulation = aqnsim.generate_run_simulation_fn(
        setup_sim_fn=setup_network, logging_level=20, log_to_file=False
    )
    results = run_simulation()
    for key, value in results.items():
        print(value, key)

