from typing import List, Union, Dict, Any
import simpy
import numpy as np
import pandas as pd
import aqnsim
import random
import matplotlib.pyplot as plt
from aqnsim.components.models.qnoise_models import depolar_noise_model
from aqnsim.quantum_simulator import qubit_noise
import mpltern
import matplotlib.colors as mcolors
import time
from EPR_verification_algs import checkAlice, checkWBV, checkWCV



"""
This code implements the Quantum Byzantine Agreement Using EPR Pairs, specifically the Phi+ State.
Without traitors, all nodes end in agreement with sufficient M
With traitors, there are four considerations:
A is traitor and isConsistent. Then A sends different bits to B and C, each with a consistent command vector. This results in both B and C aborting.
A is traitor and is not Consistent. Then A sends a consistent bit and vector to B and an inconsistent vector to C. B convinces C its results are correct, and both nodes end in agreement.
WLOG B is a traitor and isConsistent. Then B says he received the opposite bit he actually did, and claims he has consistent data. He must send that data over, and C verifies it is inconsistent and sticks with its original command, agreeing with A.
WLOG B is a traitor and is not Consistent. Then B says he received inconsistent data, but C sticks with their consistent data and agrees with A.
"""

# constants
CHANNEL_DELAY = 1e-6 * aqnsim.SECOND
NUM_SHOTS = 1
M = 64
e = 2 * np.sqrt(M / 4)
p0, p1, p2, p3 = (-1,)*4


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
        sim_context,
        n: int = 3,
        op_delays: Dict[str, Dict[int, Union[int, float, aqnsim.DelayModel]]] = None,
        meas_delay: Dict[str, Union[int, float, aqnsim.DelayModel]] = None,
        name=None,
        params=None,
    ):
        super().__init__(
            env=sim_context.env, ports=["cport1", "cport2", "qport1", "qport2"], name=name
        )

        self.qs = sim_context.qs
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
        
        self.params = params
        
        # Only collect data for C because A is truthful and B is the traitor
        # Only other case to consider is A is unfaithful
        if (self.name == "C"):
            self.datacollector = sim_context.datacollector
            self.datacollector.register_attribute(f"{self.name} isSuccess")
            # print(f"{self.name} isSuccess")
            self.datacollector.register_attribute("noiseProbs")


        
    

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
        self.node.ports["cport1"].add_rx_input_handler(self.cport_handler)
        self.node.ports["cport2"].add_rx_input_handler(self.cport_handler)

        self.node.ports["qport1"].add_rx_input_handler(self.qport_handler)
        self.node.ports["qport2"].add_rx_input_handler(self.qport_handler)
        self.tx = tx
        self.traitor = traitor
        self.isConsistent = isConsistent
        self.noise_probs = noise_probs

        # Track correction information gathered from repeater messages
        self.measurement_times = []
        self.measurement_results = []
        self.decision = -1 # initially you are undecided
        self.command_vector = []
        
        if (self.node.name == "C"):
            self.node.datacollector.update_attribute("noiseProbs", noise_probs)
        

    def cport_handler(self, msg: aqnsim.CMessage):
        """Handler for correction messages that are distributed by the repeaters.  Collects all expected messages
        before performing a correction on the local qubit.

        :param msg: A message containing the measurement results for a repeater's swap
        """

        print(f"Node {self.node.name} received a message from Node {msg.sender}")
        if (msg.sender == "A"):
            self.command_vector = msg.content["command vector"]
            # self.measurement_results.reverse()
            if self.node.name == "B":
                # If B, verify A's sent data, then send your decision to C
                checkA = checkAlice(1, msg.content["bit"], msg.content["command vector"], self.measurement_results)
                print("CheckA", checkA)
                self.decision = msg.content["bit"] if checkA else -1
                if (self.traitor): # If you're a traitor you must adjust your decision to be incorrect
                    if (self.isConsistent):
                        self.decision = (self.decision+1)%2 # You lie and say that your data is consistent, but flip your bit
                        self.measurement_results = [0] * M + [1] * M
                        random.shuffle(self.measurement_results)
                    else:
                        self.decision = -1 # You lie and say that your data is inconsistent
                print(f"{self.node.name} has decided on {self.decision}")
                
                # Send your decision to C
                msgC = aqnsim.CMessage(
                    sender=self.node.name,
                    action="SEND BIT",
                    status=aqnsim.StatusMessages.SUCCESS,
                    content={
                        "bit": self.decision,
                        "command vector2": msg.content["command vector"],
                    },
                )
                self.node.ports["cport1"].rx_output(msgC)
                
            # If you're C, do the exact same thing as B but mirrored, and send your decision to B of course.
            elif self.node.name == "C":
                checkA = checkAlice(0, msg.content["bit"], msg.content["command vector"], self.measurement_results)
                print("CheckA", checkA)
                self.decision = msg.content["bit"] if checkA else -1
                if (self.traitor):
                    if (self.isConsistent):
                        self.decision = (self.decision+1)%2 # You lie and say that your data is consistent, but flip your bit
                    else:
                        self.decision = -1 # You lie and say that your data is inconsistent
                
                msgB = aqnsim.CMessage(
                    sender=self.node.name,
                    action="SEND BIT",
                    status=aqnsim.StatusMessages.SUCCESS,
                    content={
                        "bit": self.decision,
                        "command vector2": msg.content["command vector"],
                    },
                )
                self.node.ports["cport2"].rx_output(msgB)
                
        else: # Now considering round 3, where (self.node.name == "B" and msg.sender == "C"):
            i = 1 if self.node.name == "B" else 0
            j = 0 if self.node.name == "B" else 1
            # They both match or you have consistent data and they don't -> keep your decision
            if (msg.content["bit"] == self.decision or (self.decision != -1 and msg.content["bit"] == -1)): # Rule 3,1 and 3,2
                print("BROADCAST ACHIEVED, DECISION", self.decision)
            elif (self.decision != -1 and msg.content["bit"] != -1 and self.decision != msg.content["bit"]): # Both consistent but different
                    checkC = checkWCV(i, j, msg.content["bit"], msg.content["command vector2"], self.command_vector)
                    if (checkC): # Rule 3,3 -> If no inconsistencies, abort
                        self.decision = -1
                        print("PROTOCOL ABORTED", self.decision)
                    # else statement here (unnecesary so not included) is Rule 3,4 -> stick to your initial decision and terminate
            elif (self.decision == -1 and msg.content["bit"] != -1 and not self.traitor): # You can't change a traitor's mind, since they won't be logical and helpful
                checkC = checkWBV(i, j, msg.content["bit"], msg.content["command vector2"], self.measurement_results) # Check the received command vector against your own bit vector
                if (checkC): # Rule 3,5 -> If no inconsistencies, switch decision and terminate
                    self.decision = msg.content["bit"]
                    print(f"{self.node.name} changed their decision to {self.decision}")
                # Otherwise keep initial decision (abort) and terminate
                
        if (self.node.name == "C"):
            print("Decision", self.decision)
            self.node.datacollector.update_attribute("C isSuccess", self.decision)
                    

    @aqnsim.process
    def qport_handler(self, msg):
        """Handles incoming qubits.

        :param msg: A `Qubit` received via the quantum channel.
        
        """
        if (self.noise_probs[0] == 0):
            qubit_noise.apply_pauli_noise(self.qs, self.noise_probs[0], self.noise_probs[1], self.noise_probs[2], self.noise_probs[3], msg)
        
        # place the qubit into the memory
        self.qmem.put(msg, 0)
        meas_result = yield self.qmem.measure(0)
        # if I am the unreliable node, generate a random quantity - Bernoulli
        # Constant function - send all 0's or 1's if you're the attacker
        # Balanced function - half 0's, half 1's
        # Random data of 0's and 1's with some distributions Binomial/Exponential/Poisson? Mean number of 1's sent
        # 

        # record measurement result
        self.measurement_results.append(meas_result)
        self.measurement_times.append(self.env.now)
        
        # This is for the hardcoded example in the paper to verify all functions work properly
        # if (self.node.name == "A"):
        #     self.measurement_results = [1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 1]
        # elif (self.node.name == "B"):
        #     self.measurement_results = [0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1]
        # elif (self.node.name == "C"):
        #     self.measurement_results = [0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0]
        
    # This function generates a command vector for any bit and any recipient
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
    def sendCommand(self, bit): # This function is verified to be correct
        if (self.traitor):
            self.decision = -2 # So that you know the sender is the traitor
        else:
            self.decision = bit
        
        commandVecB = self.generateCommand(bit, 1)
        commandVecC = self.generateCommand(bit, 0)
        # print("A")
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
                
                for x in range(2*M):
                    self.qmem.create_new(0)
                    self.qmem.create_new(1)
                    yield self.qmem.operate(aqnsim.ops.H, qpos=0)
                    yield self.qmem.operate(aqnsim.ops.CNOT, qpos=[0, 1])
                    yield self.qmem.operate(aqnsim.ops.X, qpos=0)
                    
                    self.qmem.create_new(2)
                    yield self.qmem.operate(aqnsim.ops.H, qpos=2)
                                        
                    meas_result = yield self.qmem.measure(0)
                    self.measurement_results.append(meas_result)
                    self.measurement_times.append(self.env.now)
                    
                    if (x % 2 == 0):
                        self.qmem.pop(2, port_name="mem_qport1")
                        self.qmem.pop(1, port_name="mem_qport2")
                    else:
                        self.qmem.pop(2, port_name="mem_qport2")
                        self.qmem.pop(1, port_name="mem_qport1")
                        
                # Wait to make sure distribution is over before sending commands
                yield self.wait(1)
                self.sendCommand(1) # Adjust here if you'd like to send a 0 or 1 command.                

def setup_network(
    sim_context: aqnsim.SimulationContext,
    parameters: List[Any],
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
    general_a = General(sim_context, op_delays=op_delays, meas_delay=meas_delay, name="A")
    general_b = General(sim_context, op_delays=op_delays, meas_delay=meas_delay, name="B")
    general_c = General(sim_context, op_delays=op_delays, meas_delay=meas_delay, name="C")

    # Initialize the network.
    network = aqnsim.Network(sim_context.env, sim_context.qs, nodes=[general_a, general_b, general_c])

    # Add the quantum and classical channels to the network.
    for gen_x, gen_y in [
        (general_a, general_b),
        (general_b, general_c),
        (general_c, general_a),
    ]:
        clink = aqnsim.ClassicalLink(
            env=sim_context.env, delay=CHANNEL_DELAY, name=f"clink_{gen_x.name}_{gen_y.name}"
        )
        qlink = aqnsim.QuantumLink(
            env=sim_context.env, qs=sim_context.qs, delay=CHANNEL_DELAY, noise=0, name=f"qlink_{gen_x.name}_{gen_y.name}" # depolar_noise_model.DepolarNoiseModel(qs, 0.5, "depolarizing")
        )
        network.add_link(clink, gen_x, gen_y, "cport1", "cport2")
        network.add_link(qlink, gen_x, gen_y, "qport1", "qport2")

    # Equip protocols and set general A to be the sender.
    general_a_protocol = GeneralProtocol(env=sim_context.env, qs=sim_context.qs, node=general_a, noise_probs=parameters, tx=True)
    general_b_protocol = GeneralProtocol(env=sim_context.env, qs=sim_context.qs, node=general_b, noise_probs=parameters, traitor=True, isConsistent=True) # traitor=True, isConsistent=True
    general_c_protocol = GeneralProtocol(env=sim_context.env, qs=sim_context.qs, node=general_c, noise_probs=parameters)

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
            a_protocol.measurement_results,
        )
    )
    b_results = list(
        zip(
            b_protocol.measurement_times,
            b_protocol.measurement_results,
        )
    )
    c_results = list(
        zip(
            c_protocol.measurement_times,
            c_protocol.measurement_results,
        )
    )
    print("A", a_protocol.decision)
    print("B", b_protocol.decision)
    print("C", c_protocol.decision)
    return (a_protocol, b_protocol, c_protocol)
    # print(a_protocol.measurement_results)
    # print(b_protocol.measurement_results)
    # print(c_protocol.measurement_results)
    # df = pd.DataFrame([[a_results[i][1], b_results[i][1], c_results[i][1]] for i in range(len(a_results))])
    # print(df)

def run_simulation(noise_probs=(0, 0, 0, 0)):
    """Main run method"""
    # Instantiate environment and QuantumSimulator
    env = simpy.Environment()
    qs = aqnsim.QuantumSimulator()

    # Configure logger
    aqnsim.simlogger.configure(env=env, level=0)
    aqnsim.eventlogger.configure(env=env, level=0)

    # Setup network and protocols, and run sim until the given time
    _, general_a_protocol, general_b_protocol, general_c_protocol = setup_network(
        env, qs, noise_probs
    )
    
    env.run()
    
    ce = check_example(general_a_protocol, general_b_protocol, general_c_protocol)
    
    
    # Nothing down here is reached
    
    # general_a_protocol.node.datacollector.update_attribute("A isSuccess", 1 if general_a_protocol.decision == 1 else 0)
    # general_b_protocol.node.datacollector.update_attribute("B isSuccess", 1 if general_b_protocol.decision == 1 else 0)
    print("Decision:", general_a_protocol.decision)
    general_c_protocol.node.datacollector.update_attribute("C isSuccess", 1 if general_c_protocol.decision == 1 else 0)
    print("jfklajfklajdfkljaklfgjdsklgjkladjgklfdjkladsjklfdsklfasdjfkgjklafdj")
    return ce
    
def noise_sweep(p0: float):
    num_trials = 1
    p1_vals = []
    p2_vals = []
    p3_vals = []
    success_vals = []
    for pct1 in np.arange(0, 1.05, .5):
        for pct2 in np.arange(0, 1.05 - pct1, .5):
            p1 =  (1-p0) * pct1
            p2 = (1-p0-p1) * pct2
            p3 = (1-p0-p1-p2)
            pct3 = (1 - pct1 - pct2)
            
            num_fails = 0
            num_successful_traitors = 0
            for t in range(num_trials):
                a_p, b_p, c_p = run_simulation((p0, p1, p2, p3))
                if (c_p.decision == 0):
                    num_successful_traitors += 1
                if (c_p.decision == -1):
                    num_fails += 1
            success_vals.append(1.0 - (float(num_fails + num_successful_traitors) / num_trials))
            p1_vals.append(pct1)
            p2_vals.append(pct2)
            p3_vals.append(pct3)
            
            
    print(success_vals)
    print(pct1)
    fig = plt.figure()
    ax = plt.subplot(projection="ternary")
    tricontourf = ax.tricontourf(p1_vals, p2_vals, p3_vals, success_vals)  # Plot pct instead?
    colorbar = fig.colorbar(tricontourf, ax=ax, orientation='vertical')
    colorbar.set_label('Success Values')
    ax.set_tlabel('P1')
    ax.set_llabel('P2')
    ax.set_rlabel('P3')
    plt.show()

def _postprocessing(sim_data):
    """
    Compute the fidelity of the channel by comparing the sent qubit to the received qubit.
    """
    # tx_qubit = sim_data["alice_protocol_tx_qubit"][0][0]
    # rx_qubit = sim_data["bob_protocol_rx_qubit"][0][0]
    res = 1 if sim_data["C isSuccess"] == 1 else 0

    return {
        "result": res,
        "noiseProbs": sim_data["noiseProbs"]
    }
            
if __name__ == "__main__":
    data = dict()
    
    num_trials = 50
    p0 = .5
    
    t0 = time.time()
    
    for t in range(num_trials):
        p1_vals = []
        p2_vals = []
        p3_vals = []
        for pct1 in np.arange(0, 1.05, .05):
                for pct2 in np.arange(0, 1-pct1 + .05, .05):
                    pct3 = round(1 - pct1 - pct2, 8)
                    p1 =  round((1-p0) * pct1, 8)
                    p2 = round((1-p0-p1) * pct2, 8)
                    p3 = round(1-p0-p1-p2, 2)
                    # print(pct1, pct2, pct3)
                    
                    p1_vals.append(p1)
                    p2_vals.append(p2)
                    p3_vals.append(p3)
        
        batch_parameters = [
            [[p0, p_1, p_2, p_3]] for p_1, p_2, p_3 in zip(p1_vals, p2_vals, p3_vals)
        ]
        
        run_simulation = aqnsim.generate_run_simulation_fn(
            setup_sim_fn=setup_network, logging_level=40
        )
        
        t1 = time.time()
        sim_results = aqnsim.run_simulations(
            run_simulation_fn=run_simulation,
            batch_parameters=batch_parameters,
            n_workers=8,
            threads_per_worker=1,
        )
        
        for sim_result in sim_results:
            print("NoiseProbs:", sim_result["noiseProbs"], "C Decision:", sim_result["C isSuccess"])
            probs = (sim_result["noiseProbs"][0][0][1], sim_result["noiseProbs"][0][0][2], sim_result["noiseProbs"][0][0][3])
            if probs in data:
                data[probs] += (1 if sim_result["C isSuccess"][-1][0] == 1 else 0)
            else:
                data[probs] = (1 if sim_result["C isSuccess"][-1][0] == 1 else 0)
                
                
            # data[(sim_result["noiseProbs"][0][0][1], sim_result["noiseProbs"][0][0][2], sim_result["noiseProbs"][0][0][3])]
            # graph_p1.append(sim_result["noiseProbs"][0][0][1])
            # graph_p2.append(sim_result["noiseProbs"][0][0][2])
            # graph_p3.append(sim_result["noiseProbs"][0][0][3])
            # graph_s.append(1 if sim_result["C isSuccess"][-1][0] == 1 else 0)
            
        # print(graph_p1)


        print(f"computation time : {time.time() - t1}s")
    print(f"Total computation time : {time.time() - t0}s")
        
        
    graph_p1 = []
    graph_p2 = []
    graph_p3 = []
    graph_s = []
    
    print(data)
    for prob, successes in data.items():
        graph_p1.append(prob[0])
        graph_p2.append(prob[1])
        graph_p3.append(prob[2])
        graph_s.append(float(successes) / num_trials)


    
    fig = plt.figure()
    ax = plt.subplot(projection="ternary")
    tricontourf = ax.tricontourf(graph_p1, graph_p2, graph_p3, graph_s)  # Plot pct instead?
    colorbar = fig.colorbar(tricontourf, ax=ax, orientation='vertical')
    colorbar.set_label('Success Rate')
    ax.set_tlabel('P1')
    ax.set_llabel('P2')
    ax.set_rlabel('P3')
    ax.set_title(f"Pauli Noise, p0={p0}")
    plt.show()
    # print(f"Average Fidelity for Batch : {sim_results}")
    
    # print(batch_parameters)
    # print(batch_parameters)
    # M = 4
    # num_trials = 250
    # M_vals = []
    # success_vals = []
    # traitor_success_vals = []
    # failed_agreement_vals = []
    
    # while (M <= 64):
    #     M_vals.append(M)
    #     num_successful_traitors = 0
    #     num_runs = 0
    #     num_fails = 0
    #     for i in range(num_trials):
    #         a_p, b_p, c_p = run_simulation()
    #         num_runs += 1
    #         if (c_p.decision == 0):
    #             num_successful_traitors += 1
    #         if (c_p.decision == -1):
    #             num_fails += 1
    #     # print(num_fails)
    #     print("Success Rate", 1 - (float(num_successful_traitors) / num_runs) - (float(num_fails) / num_runs))
    #     success_vals.append(1 - (float(num_successful_traitors) / num_runs) - (float(num_fails) / num_runs))
    #     print("Successful Traitor Rate", (float(num_successful_traitors) / num_runs))
    #     traitor_success_vals.append((float(num_successful_traitors) / num_runs))
    #     print("Failed Agreement", (float(num_fails) / num_runs))
    #     failed_agreement_vals.append((float(num_fails) / num_runs))
    #     print()
    #     M += 4
        
    # plt.plot(M_vals, success_vals, label="Success Rate")
    # plt.plot(M_vals, traitor_success_vals, label="Traitor Success Rate")
    # plt.plot(M_vals, failed_agreement_vals, label="Failed Agreement Rate")
    # plt.title("EPRQDBA Success vs Number of Qubits M")
    # plt.xlabel("Number of Qubits per Node (M)")
    # plt.ylabel("Percentage")
    # plt.legend()
    # plt.show()
    # for i in range(1000):
    #     a_p, b_p, c_p = run_simulation()
    # noise_sweep(.33)
    
    
        
    # run_simulation()




# p1_vals = []
# p2_vals = []
# p3_vals = []
# for pct1 in np.arange(0, 1.05, .05):
#         for pct2 in np.arange(0, 1-pct1 + .05, .05):
#             pct3 = (1 - pct1 - pct2)
#             print(pct1, pct2, pct3)
            
#             p1_vals.append(10*pct1)
#             p2_vals.append(10*pct2)
#             p3_vals.append(10*pct3)
            
            
# heatmap_values = np.random.rand(len(p1_vals))

# fig = plt.figure()
# ax = plt.subplot(projection="ternary")
# # norm = mcolors.Normalize(vmin=0, vmax=1)
# tricontourf = ax.tripcolor(p1_vals, p2_vals, p3_vals, heatmap_values, shading="gouraud")  # Plot pct instead?

# colorbar = fig.colorbar(tricontourf, ax=ax, orientation='vertical')
# colorbar.set_label('Success Values')
# ax.set_tlabel('P1')
# ax.set_llabel('P2')
# ax.set_rlabel('P3')
# plt.show()
