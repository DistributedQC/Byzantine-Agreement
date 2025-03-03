import simpy
import numpy as np
import aqnsim
import matplotlib.pyplot as plt
import mpltern
# from EPR_verification_algs import checkAlice, checkWBV, checkWCV
import time
from enum import Enum, auto
from itertools import combinations  

from config import CHANNEL_DELAY, NUM_SHOTS, M, N, E, p0, p1, p2, p3, NoiseType
from players import General, GeneralProtocol


"""
This code implements the Quantum Byzantine Agreement Using EPR Pairs, specifically the Phi+ State.
Without traitors, all nodes end in agreement with sufficient M
With traitors, there are four considerations:
A is traitor and isConsistent. Then A sends different bits to B and C, each with a consistent command vector. This results in both B and C aborting.
A is traitor and is not Consistent. Then A sends a consistent bit and vector to B and an inconsistent vector to C. B convinces C its results are correct, and both nodes end in agreement.
WLOG B is a traitor and isConsistent. Then B says he received the opposite bit he actually did, and claims he has consistent data. He must send that data over, and C verifies it is inconsistent and sticks with its original command, agreeing with A.
WLOG B is a traitor and is not Consistent. Then B says he received inconsistent data, but C sticks with their consistent data and agrees with A.
Author: Shaan Doshi
"""
 

def setup_network(
    env: simpy.Environment,
    qs: aqnsim.QuantumSimulator,
    noise_probs=(0,0,0,0),
    noise_type=NoiseType.Pauli,
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

    # Initialize your N nodes.
    generals = []
    for i in range(N):
        generals.append(General(env, qs, op_delays=op_delays, meas_delay=meas_delay, name=str(i)))

    # Initialize the network.
    network = aqnsim.Network(env, qs, nodes=generals)

    # Add the quantum and classical channels to the network.
    # This takes every pairwise combination of generals in the network to connect classically and quantum-ly
    for pair in list(combinations(generals, 2)):
        gen_x = pair[0]
        gen_y = pair[1]
    
        clink = aqnsim.ClassicalLink(
            env=env, delay=CHANNEL_DELAY, name=f"clink_{gen_x.name}_{gen_y.name}"
        )
        qlink = aqnsim.QuantumLink(
            env=env, qs=qs, delay=CHANNEL_DELAY, noise=0, name=f"qlink_{gen_x.name}_{gen_y.name}" # depolar_noise_model.DepolarNoiseModel(qs, 0.5, "depolarizing")
        )
        # each general has a classical and quantum numbered port for every other general, so you connect them to each other
        # To clarify further, gen_x has a port for every possible gen_y, and gen_y has a port for every possible gen_x, so you connect gen_x's port named gen_y with gen_y's named gen_x
        network.add_link(clink, gen_x, gen_y, f"cport{gen_y.name}", f"cport{gen_x.name}")
        network.add_link(qlink, gen_x, gen_y, f"qport{gen_y.name}", f"qport{gen_x.name}")

    # Equip protocols and set general A to be the sender.
    general_protocols = []
    for i in range(N):
        # If you are the General indexed at 0, you are the sender
        if (i == 0):
            sender_protocol = GeneralProtocol(env=env, qs=qs, node=generals[i], noise_probs=noise_probs, noise_type=noise_type, tx=True)
            general_protocols.append(sender_protocol)
        # Otherwise you are a receiver
        else:
            # TODO add better functionality for making nodes traitors
            lieutenant_protocol = GeneralProtocol(env=env, qs=qs, node=generals[i], noise_probs=noise_probs, noise_type=noise_type) # traitor=False, isConsistent=True
            general_protocols.append(lieutenant_protocol)
            
    return network, general_protocols

# Run a simulation with the given noise type and parameters.
# If the noise is not Pauli, only noise_probs[0] is evaluated.
def run_simulation(noise_probs=(0, 0, 0, 0), noise_type=NoiseType.Pauli):
    """Main run method"""
    # Instantiate environment and QuantumSimulator
    env = simpy.Environment()
    qs = aqnsim.QuantumSimulator()

    # Configure logger
    aqnsim.simlogger.configure(env=env, level=0)
    aqnsim.eventlogger.configure(env=env, level=0)

    # Setup network and protocols, and run sim until the given time
    _, general_protocols = setup_network(
        env, qs, noise_probs, noise_type
    )

    env.run()
    # general_protocols holds all the data for every single node in the network
    return general_protocols
    
# these obviusly don't work yet since the protocol isn't fully implemented
def run_pauli_noise_sweep(p0: float, num_trials: int):
    start_time = time.time()
    env = simpy.Environment()
    qs = aqnsim.QuantumSimulator()
    _, general_a_protocol, general_b_protocol, general_c_protocol = setup_network(
        env, qs
    )
    
    p1_vals = []
    p2_vals = []
    p3_vals = []
    success_vals = []
    for pct1 in np.arange(0, 1.01, .1):
        for pct2 in np.arange(0, 1.01, .1):
            p1 =  (1-p0) * pct1
            p2 = (1-p0-p1) * pct2
            p3 = (1-p0-p1-p2)
            
            num_fails = 0
            num_successful_traitors = 0

            for t in range(num_trials):
                a_p, b_p, c_p = run_simulation((p0, p1, p2, p3))
                env.run()
                
                print(p0, p1, p2, p3)
                print(a_p.decision, b_p.decision, c_p.decision)
                print()
                
                if (c_p.decision == 0):
                    num_successful_traitors += 1
                if (c_p.decision == -1):
                    num_fails += 1
            success_vals.append(1.0 - (float(num_fails + num_successful_traitors) / num_trials))
            p1_vals.append(p1)
            p2_vals.append(p2)
            p3_vals.append(p3)
    
    writeToFile("pauli_noise_sweeps.txt", [("p0", [p0]), ("p1", p1_vals), ("p2", p2_vals), ("p3", p3_vals)], success_vals, "Pauli", num_trials, time.time()-start_time)
    
    fig = plt.figure()
    ax = plt.subplot(projection="ternary")
    tricontourf = ax.tricontourf(p1_vals, p2_vals, p3_vals, success_vals)  # Plot pct instead?
    colorbar = fig.colorbar(tricontourf, ax=ax, orientation='vertical')
    colorbar.set_label('Success Rate')
    ax.set_tlabel('P1')
    ax.set_llabel('P2')
    ax.set_rlabel('P3')
    ax.set_title(f"Pauli Noise, p0={p0}")
    plt.show()
    
def run_depolarizing_noise_sweep(num_trials: int):
    start_time = time.time()
    env = simpy.Environment()
    qs = aqnsim.QuantumSimulator()
    _, general_a_protocol, general_b_protocol, general_c_protocol = setup_network(
        env, qs, noise_type=NoiseType.Depolarizing
    )
    p_vals = []
    success_vals = []
    
    for p in np.arange(0, .21, .01):
        num_fails = 0
        num_successful_traitors = 0

        for t in range(num_trials):
            a_p, b_p, c_p = run_simulation((p, p, p, p), NoiseType.Depolarizing)
            env.run()
            
            print(p)
            print(a_p.decision, b_p.decision, c_p.decision)
            print()
            
            if (c_p.decision == 0):
                num_successful_traitors += 1
            if (c_p.decision == -1):
                num_fails += 1
        success_vals.append(1.0 - (float(num_fails + num_successful_traitors) / num_trials))
        p_vals.append(p)
    
    writeToFile("depolarizing_noise_sweeps.txt", [("p", p_vals)], success_vals, "Depolarizing", num_trials, time.time()-start_time)
    
    plt.xlabel("Noise Probability (p)")
    plt.ylabel("Success Rate")
    plt.title("Depolarizing Noise")
    plt.plot(p_vals, success_vals)
    plt.show()
    
def writeToFile(file_name, param_sweeps, success_vals, title, num_trials, time):
    with open (file_name, "a") as f:
        f.write(title + "\n")
        f.write("Time: " + str(time) + "\n")
        f.write("Trials: " + str(num_trials) + "\n")
        for param in param_sweeps:
            f.write(param[0] + "\n")
            for num in param[1]:
                f.write(str(num) + "\t")
            f.write("\n")
        f.write("Success\n")
        for num in success_vals:
            f.write(str(num) + "\t")
        f.write("\n\n")
                
            
if __name__ == "__main__":
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
    # run_dephasing_noise_sweep(75)
    # a_p, b_p, c_p = run_simulation()
    # print(len(a_p.measurement_results))
    
    # These are the only functions you really need to run, 100 is the number of simulations you run at each parameter
    # run_pauli_noise_sweep(.95, 1)
    # run_depolarizing_noise_sweep(1)  
    res = run_simulation()
    alice_qubits = res[0].measurement_results
    bad = False
    # print(alice_qubits)
    for prot in res:
        if (prot.node.name == "0"):
            continue
        lieutenant_qubits = prot.measurement_results
        for i in range(len(lieutenant_qubits)):
            if (i % (N-1) == int(prot.node.name)-1):
                if (lieutenant_qubits[i] == alice_qubits[i]):
                    print("FAILED")
                    bad = True
    if (not bad):
        print("Entanglement Distribution Success!")
        print(len(alice_qubits))
                    
        # print("General:", prot.node.name)
        # print("Decision:", prot.decision)
        # print()