import aqnsim
import simpy
from typing import List, Union, Dict
import simpy
from aqnsim.quantum_simulator import qubit_noise


from config import CHANNEL_DELAY, NUM_SHOTS, M, N, E, p0, p1, p2, p3, NoiseType

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
        n: int = 3, # number of qubits you can hold at a time
        op_delays: Dict[str, Dict[int, Union[int, float, aqnsim.DelayModel]]] = None,
        meas_delay: Dict[str, Union[int, float, aqnsim.DelayModel]] = None,
        name=None,
    ):
        ports = [] # This will hold all the ports of this General node
        mem_qports = [] # This will hold the ports that attach to this General node's QMemory
        for i in range(N):
            # You add a classical and quantum port for every general other than yourself.
            # These are named accordingly to all other generals' index/names
            if (str(i) != name):
                ports.append(f"cport{i}")
                ports.append(f"qport{i}")
                mem_qports.append(f"mem_qport{i}")
                
        super().__init__(
            env=env, ports=ports, name=name
        )

        self.qs = qs
        self.n = n
        self.qmemory = aqnsim.QMemory(
            env=self.env,
            qs=self.qs,
            n=self.n,
            ports=mem_qports,
            meas_delay=meas_delay,
            name=f"QMemory-{name}",
        )
        self.qmemory.set_op_delays(op_delays=op_delays)
        for i in range(N):
            # Attach all your QMem ports to your quantum ports.
            if (str(i) != name):
                self.qmemory.ports[f"mem_qport{i}"].forward_output_to_output(self.ports[f"qport{i}"])    

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
        noise_probs, 
        noise_type,
        env: simpy.Environment,
        qs: aqnsim.QuantumSimulator,
        node: aqnsim.Node,
        name: str = "GeneralProtocol",
        tx: bool = False,
        traitor: bool = False,
        isConsistent: bool = False,
    ):
        super().__init__(env=env, node=node, name=name)

        self.qs = qs
        self.qmem = self.node.qmemory
        for i in range(N):
            # For all of your ports, add the qport or cport handler
            if (str(i) != self.node.name):
                self.node.ports[f"cport{i}"].add_rx_input_handler(self.cport_handler)
                self.node.ports[f"qport{i}"].add_rx_input_handler(self.qport_handler)
        self.tx = tx
        self.traitor = traitor
        self.isConsistent = isConsistent
        self.noise_probs = noise_probs
        self.noise_type = noise_type

        # Track correction information gathered from repeater messages
        self.measurement_times = []
        self.measurement_results = []
        self.decision = -1 # initially you are undecided
        self.command_vector = []
        

    def cport_handler(self, msg: aqnsim.CMessage):
        """Handler for correction messages that are distributed by the repeaters.  Collects all expected messages
        before performing a correction on the local qubit.

        :param msg: A message containing the measurement results for a repeater's swap
        """

        print(f"Node {self.node.name} received a message from Node {msg.sender}")
        # This is just testing
        
        # msgC = aqnsim.CMessage(
        #             sender=self.node.name,
        #             action="SEND BIT",
        #             status=aqnsim.StatusMessages.SUCCESS,
        #             content={
        #                 "bit": "hi",
        #             },
        #         )
        # for port in self.node.ports:
        #     if port[0] == "c":
        #         self.node.ports[port].rx_output(msgC)
        
        
        # TODO Generalize this to N players! (It still works if you set N = 3)
        
        # if (msg.sender == str(0)):
        #     self.command_vector = msg.content["command vector"]
        #     # self.measurement_results.reverse()
        #     if self.node.name == str(1):
        #         # If B, verify A's sent data, then send your decision to C
        #         checkA = checkAlice(1, msg.content["bit"], msg.content["command vector"], self.measurement_results)
        #         print("CheckA", checkA)
        #         self.decision = msg.content["bit"] if checkA else -1
        #         if (self.traitor): # If you're a traitor you must adjust your decision to be incorrect
        #             if (self.isConsistent):
        #                 self.decision = (self.decision+1)%2 # You lie and say that your data is consistent, but flip your bit
        #                 self.measurement_results = [0] * M + [1] * M
        #                 random.shuffle(self.measurement_results)
        #             else:
        #                 self.decision = -1 # You lie and say that your data is inconsistent
        #         print(f"{self.node.name} has decided on {self.decision}")
                
        #         # Send your decision to C
        #         msgC = aqnsim.CMessage(
        #             sender=self.node.name,
        #             action="SEND BIT",
        #             status=aqnsim.StatusMessages.SUCCESS,
        #             content={
        #                 "bit": self.decision,
        #                 "command vector2": msg.content["command vector"],
        #             },
        #         )
        #         self.node.ports["cport2"].rx_output(msgC)
                
        #     # If you're C, do the exact same thing as B but mirrored, and send your decision to B of course.
        #     elif self.node.name == str(2):
        #         checkA = checkAlice(0, msg.content["bit"], msg.content["command vector"], self.measurement_results)
        #         print("CheckA", checkA)
        #         self.decision = msg.content["bit"] if checkA else -1
        #         if (self.traitor):
        #             if (self.isConsistent):
        #                 self.decision = (self.decision+1)%2 # You lie and say that your data is consistent, but flip your bit
        #             else:
        #                 self.decision = -1 # You lie and say that your data is inconsistent
                
        #         msgB = aqnsim.CMessage(
        #             sender=self.node.name,
        #             action="SEND BIT",
        #             status=aqnsim.StatusMessages.SUCCESS,
        #             content={
        #                 "bit": self.decision,
        #                 "command vector2": msg.content["command vector"],
        #             },
        #         )
        #         self.node.ports["cport1"].rx_output(msgB)
                
        # else: # Now considering round 3, where (self.node.name == str(1) and msg.sender == str(2)):
        #     i = 1 if self.node.name == str(1) else 0
        #     j = 0 if self.node.name == str(1) else 1
        #     # They both match or you have consistent data and they don't -> keep your decision
        #     if (msg.content["bit"] == self.decision or (self.decision != -1 and msg.content["bit"] == -1)): # Rule 3,1 and 3,2
        #         print("BROADCAST ACHIEVED, DECISION", self.decision)
        #     elif (self.decision != -1 and msg.content["bit"] != -1 and self.decision != msg.content["bit"]): # Both consistent but different
        #             checkC = checkWCV(i, j, msg.content["bit"], msg.content["command vector2"], self.command_vector)
        #             if (checkC): # Rule 3,3 -> If no inconsistencies, abort
        #                 self.decision = -1
        #                 print("PROTOCOL ABORTED", self.decision)
        #             # else statement here (unnecesary so not included) is Rule 3,4 -> stick to your initial decision and terminate
        #     elif (self.decision == -1 and msg.content["bit"] != -1 and not self.traitor): # You can't change a traitor's mind, since they won't be logical and helpful
        #         checkC = checkWBV(i, j, msg.content["bit"], msg.content["command vector2"], self.measurement_results) # Check the received command vector against your own bit vector
        #         if (checkC): # Rule 3,5 -> If no inconsistencies, switch decision and terminate
        #             self.decision = msg.content["bit"]
        #             print(f"{self.node.name} changed their decision to {self.decision}")
        #         # Otherwise keep initial decision (abort) and terminate
                    

    @aqnsim.process
    def qport_handler(self, msg):
        """Handles incoming qubits.

        :param msg: A `Qubit` received via the quantum channel.
        
        """
        if (self.noise_type == NoiseType.Pauli and sum(self.noise_probs) > 0):
            qubit_noise.apply_pauli_noise(self.qs, self.noise_probs[0], self.noise_probs[1], self.noise_probs[2], self.noise_probs[3], msg)
        elif (self.noise_type == NoiseType.Depolarizing and self.noise_probs[0] > 0):
            qubit_noise.apply_depolarizing_noise(self.qs, self.noise_probs[0], msg)
        elif (self.noise_type == NoiseType.Dephasing and self.noise_probs[0] > 0):
            qubit_noise.apply_dephasing_noise(self.qs, self.noise_probs[0], msg)
        
        # place the qubit into the memory
        self.qmem.put(msg, 0)
        meas_result = yield self.qmem.measure(0)
        # if I am the unreliable node, generate a random quantity - Bernoulli
        # Constant function - send all 0's or 1's if you're the attacker
        # Balanced function - half 0's, half 1's
        # Random data of 0's and 1's with some distributions Binomial/Exponential/Poisson? Mean number of 1's sent

        # record measurement result
        self.measurement_results.append(meas_result)
        self.measurement_times.append(self.env.now)
        
        # This is for the hardcoded example in the paper to verify all functions work properly
        # if (self.node.name == str(0)):
        #     self.measurement_results = [1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1]
        # elif (self.node.name == str(1)):
        #     self.measurement_results = [0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1]
        # elif (self.node.name == str(2)):
        #     self.measurement_results = [0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0]
        
    # This function generates a command vector for any bit and any recipient
    # TODO update this to send to 
    def generateCommand(self, bit, i): # i is 1 if B, 0 if C
        commandVecB = []
        commandVecC = []
        for k in range(M):
            mes = list(reversed(self.measurement_results))
            if (mes[2*k+1] == bit):
                commandVecB.append(mes[2*k])
                commandVecB.append(mes[2*k+1])
            else:
                commandVecB.append(2)
                commandVecB.append(2)
            
            if (mes[2*k] == bit):
                commandVecC.append(mes[2*k])
                commandVecC.append(mes[2*k+1])
            else:
                commandVecC.append(2)
                commandVecC.append(2)
        commandVecB.reverse()
        commandVecC.reverse()
        
        return commandVecB if i else commandVecC
        

    # This function is used by A to send commands to B and C in round 1 of the protocol
    # TODO update this to generate and send to N players
    def sendCommand(self, bit): # This function is verified to be correct
        if (self.traitor):
            self.decision = -2 # So that you know the sender is the traitor
        else:
            self.decision = bit
        
        commandVecB = self.generateCommand(bit, 1)
        commandVecC = self.generateCommand(bit, 0)
        # print(str(0))
        # print(self.measurement_results)
        # print(commandVecB)
        # print(commandVecC)
                
        # Send bit and command vec over classical channel
        msgB = aqnsim.CMessage(
            sender=self.node.name,
            action="SEND BIT",
            status=aqnsim.StatusMessages.SUCCESS,
            content={
                "bit": bit,
                "command vector": commandVecB,
            },
        )
        self.node.ports["cport1"].rx_output(msgB)
        
        msgC = aqnsim.CMessage(
            sender=self.node.name,
            action="SEND BIT",
            status=aqnsim.StatusMessages.SUCCESS,
            content={
                "bit": bit if not self.traitor else (bit+1)%2, # If traitor, send wrong info to C WLOG
                "command vector": commandVecC if not self.isConsistent else self.generateCommand((bit+1)%2, 0), # if not consistent, send old data with new bit, otherwise send new data with new bit
            },
        )
        self.node.ports["cport2"].rx_output(msgC)
                
        
    def run(self):
        """Main run method for the protocol"""
        for i in range(NUM_SHOTS):
            # yield self.wait(1)

            if self.tx:
                # Once again hardcoded bit vector for A from the paper
                # self.measurement_results = [1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1]
                
                # wait some time before beginning shot sequence
                # yield self.wait(1)

                # Entanglement Distribution
               # TODO This gives each player M qubits, instead of M (n-1) tuples of qubits, need to update this
               # Each node has M tuples of size n-1 (there are n-1 general nodes outside of the receiver)
                for tuple in range(M):
                    phi_plus_general = tuple % (N-1)
                    for qubit in range(N-1):
                        if (qubit == phi_plus_general):
                            self.qmem.create_new(0)
                            self.qmem.create_new(1)
                            yield self.qmem.operate(aqnsim.ops.H, qpos=0)
                            yield self.qmem.operate(aqnsim.ops.CNOT, qpos=[0, 1])
                            yield self.qmem.operate(aqnsim.ops.X, qpos=0)
                            # Now I have a Phi+ state
                            
                            # Keep the first index
                            meas_result = yield self.qmem.measure(0)
                            self.measurement_results.append(meas_result)
                            self.measurement_times.append(self.env.now)
                            
                            # Give the second index away, you add one to qport becuase qubit is indexed from 0 but the non-sender nodes start at 1
                            self.qmem.pop(1, port_name=f"mem_qport{qubit+1}")
                        else:
                            # If you're not the special node you receive a plus state
                            self.qmem.create_new(0)
                            yield self.qmem.operate(aqnsim.ops.H, qpos=0)
                            # I now have a plus state
                            self.qmem.pop(0, port_name=f"mem_qport{qubit+1}")
                        yield self.wait(1) # You need this wait or Qmems are busy while receiving more data
                                           
                            
            
            # all of this commented code is the old entanglement distribution, I haven't deleted it yet in case it's useful to update the above entanglement dist
                        # else:
                        #     self.qmem.create_new(qubit)
                        #     self.qmem.create_new(qubit+1)
                        #     yield self.qmem.operate(aqnsim.ops.H, qpos=qubit)
                        #     yield self.qmem.operate(aqnsim.ops.CNOT, qpos=[qubit, qubit+1])
                        #     yield self.qmem.operate(aqnsim.ops.X, qpos=qubit)
                            # I now have a phi+ state in the positions qubit, qubit+1
                    
                            
                    
                
                # for x in range(2*M):
                #     self.qmem.create_new(0)
                #     self.qmem.create_new(1)
                #     yield self.qmem.operate(aqnsim.ops.H, qpos=0)
                #     yield self.qmem.operate(aqnsim.ops.CNOT, qpos=[0, 1])
                #     yield self.qmem.operate(aqnsim.ops.X, qpos=0)
                    
                #     self.qmem.create_new(2)
                #     yield self.qmem.operate(aqnsim.ops.H, qpos=2)
                                        
                #     meas_result = yield self.qmem.measure(0)
                #     self.measurement_results.append(meas_result)
                #     self.measurement_times.append(self.env.now)
                    
                #     if (x % 2 == 0):
                #         self.qmem.pop(2, port_name="mem_qport1")
                #         self.qmem.pop(1, port_name="mem_qport2")
                #     else:
                #         self.qmem.pop(2, port_name="mem_qport2")
                #         self.qmem.pop(1, port_name="mem_qport1")
                        
                # Wait to make sure distribution is over before sending commands
                yield self.wait(1)
                # self.sendCommand(0) # Adjust here if you'd like to send a 0 or 1 command.               