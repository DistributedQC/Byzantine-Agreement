from typing import List, Union, Dict
import simpy
import numpy as np
import pandas as pd
import aqnsim


"""

"""

# constants
CHANNEL_DELAY = 1e-6 * aqnsim.SECOND
NUM_SHOTS = 1
M = 12

# used to verify the produced entangled state
# expected_state = np.array([0, 0, 0, 2, 0, -1, -1, 0, 0, -1, -1, 0, 2, 0, 0, 0]) / (
#     2 * np.sqrt(3)
# )
# expected_density_matrix = np.outer(expected_state, expected_state)


class General(aqnsim.Node):
    """A basic network node equipped with a quantum memory (`QMemory`) component.
    The node has two classical ports and two quantum ports that are used to connect with
    the two other nodes in the network.

    :param env: A simpy Environment
    :param qs: A QuantumSimulator object
    :param n: The number of qubit positions in node's qmemory
    :param op_delays: A dictionary specifying how much time operations take on the qmem
    :param meas_delay: How much time a measurement takes on the qmem
    :param name: The name of the node
    """

    def __init__(
        self,
        env: simpy.Environment,
        qs: aqnsim.QuantumSimulator,
        n: int = 3,
        op_delays: Dict[str, Dict[int, Union[int, float, aqnsim.DelayModel]]] = None,
        meas_delay: Dict[str, Union[int, float, aqnsim.DelayModel]] = None,
        name=None,
    ):
        super().__init__(
            env=env, ports=["cport1", "cport2", "qport1", "qport2"], name=name
        )

        self.qs = qs
        self.n = 3

        self.qmemory = aqnsim.QMemory(
            env=self.env,
            qs=self.qs,
            n=self.n,
            ports=["mem_qport1", "mem_qport2"],
            meas_delay=meas_delay,
            name=f"QMemory-{name}",
        )
        self.qmemory.set_op_delays(op_delays=op_delays)
        self.qmemory.ports["mem_qport1"].forward_output_to_output(self.ports["qport1"])
        self.qmemory.ports["mem_qport2"].forward_output_to_output(self.ports["qport2"])


class GeneralProtocol(aqnsim.NodeProtocol):
    """Protocol that we will attach to each of the network nodes.

    :param env: A simpy Environment.
    :param qs: A QuantumSimulator object.
    :param node: The node on which the protocol acts.
    :param name: Name of the protocol.
    :param tx: If `True`, the General prepares and sends the entangled state.
    """

    def __init__(
        self,
        env: simpy.Environment,
        qs: aqnsim.QuantumSimulator,
        node: aqnsim.Node,
        name: str = "GeneralProtocol",
        tx: bool = False,
    ):
        super().__init__(env=env, node=node, name=name)

        self.qs = qs
        self.qmem = self.node.qmemory
        self.node.ports["cport1"].add_rx_input_handler(self.cport_handler)
        self.node.ports["cport2"].add_rx_input_handler(self.cport_handler)

        self.node.ports["qport1"].add_rx_input_handler(self.qport_handler)
        self.node.ports["qport2"].add_rx_input_handler(self.qport_handler)
        self.tx = tx

        # Track correction information gathered from repeater messages
        self.measurement_times = []
        self.measurement_results = []
        self.measurement_bases = []

    def cport_handler(self, msg: aqnsim.CMessage):
        """Handler for correction messages that are distributed by the repeaters.  Collects all expected messages
        before performing a correction on the local qubit.

        :param msg: A message containing the measurement results for a repeater's swap
        """
        # TODO: write classical message handler
        print("cport handler")

    @aqnsim.process
    def qport_handler(self, msg):
        """Handles incoming qubits.

        :param msg: A `Qubit` received via the quantum channel.
        """
        
        # aqnsim.simlogger.info("I RECEIVED SOMETHING")
        # place the qubit into the memory
        self.qmem.put(msg, 0)

        # select measurment basis
        rand_x = np.random.choice([0, 1], p=[0.5, 0.5])
        # if rand_x:
        #     yield self.qmem.run_circuit(self._hadamard_basis_circuit([0]))
            
        meas_result = yield self.qmem.measure(0)
        

        # record measurement result
        self.measurement_results.append(meas_result)
        self.measurement_times.append(self.env.now)
        self.measurement_bases.append(rand_x)

    def _hadamard_basis_circuit(self, qpos: List[int]):
        """Apply the Hadamard gate to all local qubits to rotate the measurement
        basis from Z to X.
        """
        circuit = aqnsim.QCircuit(n=self.qmem.num_positions)
        for qp in qpos:
            circuit.add_op(aqnsim.ops.H, qp)

        return circuit

    def sendCommand(self, bit):
        commandVecB = []
        commandVecC = []
        for k in range(M-1, -1, -1):
            if (self.measurement_results[2*k+1] == bit):
                commandVecB.append(self.measurement_results[2*k+1])
                commandVecB.append(self.measurement_results[2*k])
            else:
                commandVecB.append(2)
                commandVecB.append(2)
            
            if (self.measurement_results[2*k] == bit):
                commandVecC.append(self.measurement_results[2*k+1])
                commandVecC.append(self.measurement_results[2*k])
            else:
                commandVecC.append(2)
                commandVecC.append(2)
                
        
    
    
    
    # def _entanglement_circuit(self):
        """Creates the quantum circuit object (`QCircuit`) used to
        prepare the tripartite entangled state in Eq. 1 of https://arxiv.org/pdf/0710.0290.
        """
        circuit = aqnsim.QCircuit(n=self.qmem.num_positions)

        # first hadamard
        circuit.add_op(aqnsim.ops.H, 4)

        # first controlled H
        circuit.add_op(aqnsim.ops.RY(np.pi / 4), 0)
        circuit.add_op(aqnsim.ops.CNOT, [4, 0])
        circuit.add_op(aqnsim.ops.RY(-np.pi / 4), 0)

        # CCNot cascade
        circuit.add_op(aqnsim.CCNOT, [4, 0, 1])
        circuit.add_op(aqnsim.CCNOT, [4, 1, 2])
        circuit.add_op(aqnsim.CCNOT, [4, 2, 3])

        circuit.add_op(aqnsim.ops.CNOT, [4, 0])
        circuit.add_op(aqnsim.ops.CNOT, [4, 1])
        circuit.add_op(aqnsim.ops.X, [4])
        circuit.add_op(aqnsim.ops.CNOT, [4, 1])

        # second controlled H
        circuit.add_op(aqnsim.ops.RY(np.pi / 4), 0)
        circuit.add_op(aqnsim.ops.CNOT, [4, 0])
        circuit.add_op(aqnsim.ops.RY(-np.pi / 4), 0)

        circuit.add_op(aqnsim.CCNOT, [4, 0, 1])
        circuit.add_op(aqnsim.CNOT, [4, 3])

        # third controlled H
        circuit.add_op(aqnsim.ops.RY(np.pi / 4), 2)
        circuit.add_op(aqnsim.ops.CNOT, [4, 2])
        circuit.add_op(aqnsim.ops.RY(-np.pi / 4), 2)

        circuit.add_op(aqnsim.CCNOT, [4, 2, 3])

        circuit.add_op(aqnsim.ops.RY(1.2309594173407747), 4)
        circuit.add_op(aqnsim.ops.Z, 4)

        return circuit


    # def epr_generation(self):
    #     # Generates 2*M Phi+ EPR Pairs
    #     circuit = aqnsim.QCircuit(n=self.qmem.num_positions)

    #     # Hadamard to get to |+>
    #     for i in range(0, self.qmem.num_positions, 2):
    #         circuit.add_op(aqnsim.ops.H, i)
    #     # CNOT to get to |Phi+>
    #     for i in range(1, self.qmem.num_positions, 2):
    #         circuit.add_op(aqnsim.ops.CNOT, [i-1, i])
    #     # X to get to |Psi+>
    #     for i in range(0, self.qmem.num_positions, 2):
    #         circuit.add_op(aqnsim.ops.X, i)
    #     return circuit
        
    def run(self):
        """Main run method for the protocol"""
        for i in range(NUM_SHOTS):
            yield self.wait(1)

            if self.tx:
                # Each shot of entanglement preparation begins here
                aqnsim.simlogger.info(f"Shot : {i} / {NUM_SHOTS}")

                # wait some time before beginning shot sequence
                yield self.wait(1)

                # reset the qubits in the v
                # for qpos in range(self.qmem.num_positions):
                #     self.qmem.create_new(qpos)

                # prepare the 5-qubit entanglement circuit
                # yield self.qmem.run_circuit(self.epr_generation())
                
                # for k in range(M):
                # 
                # 3 qubit reg = [0, 1] EPR + [2] + state
                # for qpos in range(3):
                #     self.qmem.create_new(qpos)
                #
                #  # Create plus state
                #  yield self.qmem.operate(aqnsim.ops.H, qpos=2)
                #
                #  # Send the plus state
                #
                #  def _epr_create(...)
                # 
                # yeild self.qmem.run_circuit(_epr_create)
                # 
                # # Distribute the EPR
                
                for x in range(2*M):
                    self.qmem.create_new(0)
                    self.qmem.create_new(1)
                    yield self.qmem.operate(aqnsim.ops.H, qpos=0)
                    yield self.qmem.operate(aqnsim.ops.CNOT, qpos=[0, 1])
                    yield self.qmem.operate(aqnsim.ops.X, qpos=0)
                    
                    self.qmem.create_new(2)
                    yield self.qmem.operate(aqnsim.ops.H, qpos=2)
                    
                    
                    
                    rand_x = np.random.choice([0, 1], p=[0.5, 0.5])
                    # if rand_x:
                    #     yield self.qmem.run_circuit(self._hadamard_basis_circuit([0]))
                        
                    meas_result = yield self.qmem.measure(0)
                    self.measurement_results.append(meas_result)
                    self.measurement_times.append(self.env.now)
                    self.measurement_bases.append(rand_x)   
                    
                    if (x % 2 == 0):
                        self.qmem.pop(2, port_name="mem_qport1")
                        self.qmem.pop(1, port_name="mem_qport2")
                    else:
                        self.qmem.pop(2, port_name="mem_qport2")
                        self.qmem.pop(1, port_name="mem_qport1")
                
                # for x in range(2*M):
                #     # send a plus state
                #     self.qmem.create_new(x)
                #     yield self.qmem.operate(aqnsim.ops.H, qpos=x)
                    
                #     if (x % 2 == 0):
                #         self.qmem.pop(x, port_name="mem_qport1")
                #     else:
                #         self.qmem.pop(x, port_name="mem_qport2")
                #     yield self.wait(.25)
                    
                #     # generate bell pair
                #     self.qmem.create_new(x)
                #     self.qmem.create_new(x+1)
                #     yield self.qmem.operate(aqnsim.ops.H, qpos=x)
                #     yield self.qmem.operate(aqnsim.ops.CNOT, qpos=[x, x+1])
                #     yield self.qmem.operate(aqnsim.ops.X, qpos=x)
                    
                #     if (x % 2 == 0):
                #         self.qmem.pop(x+1, port_name="mem_qport2")
                #     else:
                #         self.qmem.pop(x+1, port_name="mem_qport1")
                    # yield self.wait(.25)
                    
                    # print(self.qmem.measure(0))
                    # yield self.wait(1)
                
                # for x in range(2*M-1, -1, -2):
                #     if (x % 4 == 3):
                #         self.qmem.pop(x, port_name="mem_qport1")
                #     elif (x % 4 == 1):
                #         self.qmem.pop(x, port_name="mem_qport2")
                #     yield self.wait(1)

                # measure the ancilla qubit to verify whether the correct state was produced
                # ancilla_result = yield self.qmem.measure(4)

                # The correct state has been prepared if
                # if ancilla_result == 0:
                #     # verify the state
                #     check_entangled_state = self.qmem.positions[0].qubit.state.state
                #     for x in range(check_entangled_state.shape[0]):
                #         for y in range(check_entangled_state.shape[1]):
                #             if not np.isclose(
                #                 check_entangled_state[x, y],
                #                 expected_density_matrix[x, y],
                #             ):
                #                 aqnsim.simlogger.warning(
                #                     f"({x}, {y}), not close found : {check_entangled_state[x,y]} should be : {expected_density_matrix[x,y]}"
                #                 )

                #     # send qubits 2 and 3 to their respective general
                #     self.qmem.pop(2, port_name="mem_qport1")
                #     self.qmem.pop(3, port_name="mem_qport2")

                # select random basis choice
                # rand_x = np.random.choice([0, 1], p=[0.5, 0.5])
                # if rand_x:
                #     yield self.qmem.run_circuit(
                #         self._hadamard_basis_circuit([0, 1])
                #     )

                # # measure the two remaining qubits
                # tx_meas_val0 = yield self.qmem.measure(0)
                # tx_meas_val1 = yield self.qmem.measure(1)

                # # map the measurement result to a trit
                # if tx_meas_val0 == 1 and tx_meas_val1 == 1:
                #     meas_result = 0
                # elif tx_meas_val0 == 0 and tx_meas_val1 == 0:
                #     meas_result = 1
                # elif tx_meas_val0 != tx_meas_val1:
                #     meas_result = 2

                # # record the measurement result, time, and basis
                # self.measurement_results.append(meas_result)
                # self.measurement_times.append(self.env.now)
                # self.measurement_bases.append(rand_x)


def setup_network(
    env: simpy.Environment,
    qs: aqnsim.QuantumSimulator,
):
    """Sets up the quantum network. Three general nodes are instantiated where each pair of nodes is connected
    by quantum and classical channel. These channels are noiseless, but have any associated `CHANNEL_DELAY`.

    :param env: A simpy Environment
    :param qs: A QuantumSimulator object
    """

    # Set each gate to take 10 nanoseconds to apply.
    op_delays = {
        aqnsim.ops.H: 1e-8 * aqnsim.SECOND,
        aqnsim.ops.X: 1e-8 * aqnsim.SECOND,
        aqnsim.ops.Z: 1e-8 * aqnsim.SECOND,
        aqnsim.ops.I: 1e-8 * aqnsim.SECOND,
        aqnsim.ops.RY(0): 1e-8 * aqnsim.SECOND,
        aqnsim.ops.CNOT: 1e-8 * aqnsim.SECOND,
        aqnsim.ops.CCNOT: 1e-8 * aqnsim.SECOND,
    }
    # Set each measurement to take 100 nanoseconds to apply.
    meas_delay = 1e-7 * aqnsim.SECOND

    # Initialize three nodes.
    general_a = General(env, qs, op_delays=op_delays, meas_delay=meas_delay, name="A")
    general_b = General(env, qs, op_delays=op_delays, meas_delay=meas_delay, name="B")
    general_c = General(env, qs, op_delays=op_delays, meas_delay=meas_delay, name="C")

    # Initialize the network.
    network = aqnsim.Network(env, qs, nodes=[general_a, general_b, general_c])

    # Add the quantum and classical channels to the network.
    for gen_x, gen_y in [
        (general_a, general_b),
        (general_b, general_c),
        (general_c, general_a),
    ]:
        clink = aqnsim.ClassicalLink(
            env=env, delay=CHANNEL_DELAY, name=f"clink_{gen_x.name}_{gen_y.name}"
        )
        qlink = aqnsim.QuantumLink(
            env=env, qs=qs, delay=CHANNEL_DELAY, name=f"qlink_{gen_x.name}_{gen_y.name}"
        )
        network.add_link(clink, gen_x, gen_y, "cport1", "cport2")
        network.add_link(qlink, gen_x, gen_y, "qport1", "qport2")

    # Equip protocols and set general A to be the sender.
    general_a_protocol = GeneralProtocol(env=env, qs=qs, node=general_a, tx=True)
    general_b_protocol = GeneralProtocol(env=env, qs=qs, node=general_b)
    general_c_protocol = GeneralProtocol(env=env, qs=qs, node=general_c)

    return network, general_a_protocol, general_b_protocol, general_c_protocol


def check_example(
    a_protocol: GeneralProtocol,
    b_protocol: GeneralProtocol,
    c_protocol: GeneralProtocol,
):
    """Checks the data produced by each network node."""
    
    # aggregate the measurement results from each general
    a_results = list(
        zip(
            a_protocol.measurement_times,
            a_protocol.measurement_bases,
            a_protocol.measurement_results,
        )
    )
    b_results = list(
        zip(
            b_protocol.measurement_times,
            b_protocol.measurement_bases,
            b_protocol.measurement_results,
        )
    )
    c_results = list(
        zip(
            c_protocol.measurement_times,
            c_protocol.measurement_bases,
            c_protocol.measurement_results,
        )
    )

    # filter the results based on measurement
    # gen_list = []
    # for i in range(len(a_results)):
    #     if np.isclose(
    #         a_results[i][0] + CHANNEL_DELAY, b_results[i][0], atol=1e-2
    #     ) and np.isclose(b_results[i][0], c_results[i][0], atol=1e-2):
    #         if (
    #             a_results[i][1] == b_results[i][1]
    #             and b_results[i][1] == c_results[i][1]
    #         ):
    #             gen_list.append((a_results[i][2], b_results[i][2], c_results[i][2]))
                
    df = pd.DataFrame([[a_results[i][2], b_results[i][2], c_results[i][2]] for i in range(len(a_results))])
    print(df)
    # print(a_results)
    # print(gen_list)

    # lists_correct = True
    # for el in gen_list:
    #     if el[0] == 0:
    #         if el[1] != 0 or el[2] != 0:
    #             lists_correct = False
    #     elif el[0] == 1:
    #         if el[1] != 1 or el[2] != 1:
    #             lists_correct = False
    #     elif el[0] == 2:
    #         if el[1] == el[2]:
    #             lists_correct = False
    
    # print("list correct ? ", lists_correct)



def run_simulation():
    """Main run method"""
    # Instantiate environment and QuantumSimulator
    env = simpy.Environment()
    qs = aqnsim.QuantumSimulator()

    # Configure logger
    aqnsim.simlogger.configure(env=env)
    aqnsim.eventlogger.configure(env=env)

    # Setup network and protocols, and run sim until the given time
    _, general_a_protocol, general_b_protocol, general_c_protocol = setup_network(
        env, qs
    )

    env.run()

    check_example(general_a_protocol, general_b_protocol, general_c_protocol)


if __name__ == "__main__":
    run_simulation()
