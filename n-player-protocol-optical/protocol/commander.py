import aqnsim
from dataclasses import dataclass, field
from protocol.players import Player
from protocol.config import (
    COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER, COMMANDER_QMEMORY_ADDR,
    LIEUTENANT_NAMES, TRAITOR_INDICES,
    DISTRIBUTOR_NAME,
    NUM_PLAYERS, NUM_LIEUTENANTS, M, N,
    SEND_ORDER_ACTION, SEND_CV_ACTION, ROUND2_ACTION, ROUND3_ACTION
)

@dataclass
class CommanderCMemory:
    name: str
    orders: list[bool]
    is_traitor: bool = False
    bit_vector: list[bool | None] = field(default_factory=list)
    command_vectors:  dict[int, list[bool | None]] = field(default_factory=dict)


class Commander(Player):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str, orders: list[bool], is_traitor: bool):
        super().__init__(sim_context=sim_context, name=name)

        # Quantum Memory is initialized by the parent Player class

        # Setup Classical Memory
        self.memory = CommanderCMemory(name=name, orders=orders, is_traitor=is_traitor, bit_vector = self.bit_vector)  # Shared reference for bit_vector!

    def construct_command_vectors(self):
        for idx in range(NUM_LIEUTENANTS):
            self.memory.command_vectors[idx] = self._construct_command_vector(idx)

    def _construct_command_vector(self, lieutenant_index: int) -> list[bool | None]:
        """
        Construct a command vector for a given lieutenant based on Alice's bit string.
        This function uses a simple scheme: reveal tuples that correspond to this lieutenant's entangled positions, 
        hide others with placeholders.
        """
        command_vector = []
        tuple_length = N - 1
        
        if lieutenant_index >= len(self.memory.orders):
            raise IndexError(f"No order specified for lieutenant {lieutenant_index}")
            
        order_for_lieutenant = self.memory.orders[lieutenant_index]
        
        for k in range(M):
            start_index = k * tuple_length
            end_index = (k + 1) * tuple_length
            tuple_k = self.memory.bit_vector[start_index:end_index]
            if self.memory.bit_vector[k*(NUM_LIEUTENANTS) + lieutenant_index] == order_for_lieutenant:
                command_vector.extend(tuple_k)
            else:
                command_vector.extend(tuple_length * [None])
        
        return command_vector

class CommanderProtocol(aqnsim.NodeProtocol):
    def __init__(self, sim_context: aqnsim.SimulationContext, node: Commander):
        super().__init__(sim_context=sim_context, node=node, name=node.name)

        self.player = node

        # Don't need a classical port handler because don't recieve any communication clasically


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

            self.node.data_collector.update_attribute(self.name, {"is_traitor":self.node.memory.is_traitor, "orders":self.node.memory.orders})
            # All done!