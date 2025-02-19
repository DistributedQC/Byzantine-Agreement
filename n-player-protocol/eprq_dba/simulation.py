import random
from eprq_dba.players import Commander, Lieutenant, EvidenceBundle, InitialEvidence, IntermediaryEvidence
from eprq_dba.config import COMMANDER_NAME, LIEUTENANT_NAMES, M, N, COMMANDER_IS_TRAITOR, TRAITOR_INDICES, LOYAL_COMMANDER_ORDER

def print_game_stats(alice, lieutenants):    
    print("\n================ Game Summary ================")
    print(f"Commander: {alice.name}")
    print(f"Commander's orders: {alice.orders}")
    print(f"Commander is {'TRAITOR' if alice.is_traitor else 'loyal'}")
    print("-----------------------------------------------")
    print("Lieutenant Results:")
    for lt in lieutenants:
        print(f"\nLieutenant: {lt.name}")
        print(f"  Traitor: {'Yes' if lt.is_traitor else 'No'}")
        print(f"  Received Order: {lt.received_order}")
        print(f"  Initial decision: {lt.initial_decision}")
        print(f"  Intermediate decision: {lt.intermediate_decision}")
        print(f"  Final decision: {lt.final_decision}")
    print("===============================================\n")

def run_simulation():

    if COMMANDER_IS_TRAITOR:
        orders = [random.choice([True, False]) for _ in LIEUTENANT_NAMES]
    else:
        orders = [LOYAL_COMMANDER_ORDER] * len(LIEUTENANT_NAMES)

    alice = Commander(
        name=COMMANDER_NAME,
        orders=orders,
        is_traitor = COMMANDER_IS_TRAITOR)

    lieutenants = [
        Lieutenant(
            name=name, 
            lieutenant_index=i,
            is_traitor=(i in TRAITOR_INDICES)
        )
        for i, name in enumerate(LIEUTENANT_NAMES)
    ]
    
    """
    Phase 1: Entanglement Distribution
    
    Let M be a sufficiently large number of EPR pairs to distribute (TODO: Quantify/Qualify)
    Label EPR pairs 0..M-1. Each pair connects Alice with one lieutenant
    Distribute qubits such that:
        - Alice recieves the first qubit of every EPR pair k (k=0..m-1)
        - Each lieutenant LT_j recieves the second qubit of the pair if that pair is designated for LT_j (e.g, alternating)
          otherwise LT_j gets a filler qubit in a known state |+>.
    """
    
    alice.distribute_entanglement(lieutenants)

    """
    Phase 2: Entanglement Verification
    
    Before proceeding, verify that the dstributed entangment is intact.
    This phase is not meant to be overlooked, but we skip it for now (noiseless)
    """

    """
    Phase 3: Agreement Phase
    
    All players now measure their qubit registers to obtain classical bit vectors.
    Four phases to agreement. Players can abort the protocol by ending with final_decision = None.
    
    """

    # TODO: Split this up into many functions for readability.
    # TODO: (After above) Implement random actions for traitor lieutenants

    alice.measure_qubits()

    for lieutenant in lieutenants:
        lieutenant.measure_qubits()

    # Round 1-2: Send/Recieve
    for idx, lieutenant in enumerate(lieutenants):
        lieutenant.command_vector = alice.construct_command_vector(idx)  # Sent and recieved
        lieutenant.received_order = alice.orders[idx]  # Sent and recieved

    # Round 2: Update
    for idx, lieutenant in enumerate(lieutenants):
        if lieutenant.check_alice(tolerance = M//10):
            lieutenant.initial_decision = lieutenant.received_order
        else:
            lieutenant.initial_decision = None

    # Round 2/3: Send/Receive
    for sender_idx, sender in enumerate(lieutenants):
        # Note that the sender also sends the evidence to themselves for future reference
        
        if sender.is_traitor: # Insert simple traitor logic
            tuple_length = N - 1
            random_decision = random.choice([True, False, None])
            # TODO: instead of overriding previous work, avoid doing previous work if traitor
            lieutenant.initial_decision = random_decision
            random_CV = [random.choice([True, False, None]) for _ in range(tuple_length * M)]
            for receiver_idx, receiver in enumerate(lieutenants):
                receiver.proofs[sender_idx] = EvidenceBundle(
                    initial=InitialEvidence(
                        decision=random_decision,
                        command_vector=random_CV
                    ),
                    # No intermediary evidence is sent yet
                    intermediary=IntermediaryEvidence()
                )
        else:
            for receiver_idx, receiver in enumerate(lieutenants):
                receiver.proofs[sender_idx] = EvidenceBundle(
                    initial=InitialEvidence(
                        decision=sender.initial_decision,
                        command_vector=sender.command_vector
                    ),
                    # No intermediary evidence is sent yet
                    intermediary=IntermediaryEvidence()
                )

    # Round 3/4: Update/Send/Receieve
    for i, lieutenant in enumerate(lieutenants):
        d_i = lieutenant.initial_decision
        collected_proofs = []  
    
        received_decisions = [
            bundle.initial.decision 
            for sender_idx, bundle in lieutenant.proofs.items()
        ]

        # Rule 3.1
        if all(d == d_i for d in received_decisions):
            lieutenant.intermediate_decision = d_i
        elif d_i in (0, 1):
            # Rule 3.2
            if all(d == None for d in received_decisions):
                lieutenant.intermediate_decision = d_i
            
            else:
                conflict_found = False
                for sender_idx, bundle in lieutenant.proofs.items():
                    if bundle.initial.decision == (not d_i):
                        if lieutenant.check_lieutenant_by_command_vector(
                            sender_idx,
                            bundle.initial.decision,
                            bundle.initial.command_vector,
                            tolerance = M//10
                        ):
                            conflict_found = True
                            collected_proofs.append(bundle.initial.command_vector)
                # Rule 3.3/3.4
                if conflict_found:
                    lieutenant.intermediate_decision = None
                else:
                    lieutenant.intermediate_decision = d_i
        else:  # d_i is None
            valid_decisions = []
            valid_proofs = []
            for sender_idx, bundle in lieutenant.proofs.items():
                if bundle.initial.decision is not None:
                    if lieutenant.check_lieutenant_by_bit_vector(
                        sender_idx,
                        bundle.initial.decision,
                        bundle.initial.command_vector,
                        tolerance = M//10
                    ):
                        valid_decisions.append(bundle.initial.decision)
                        valid_proofs.append(bundle.initial.command_vector)
            # Rule 3.5/3.6
            if valid_decisions and all(d == valid_decisions[0] for d in valid_decisions):
                lieutenant.intermediate_decision = valid_decisions[0]
                collected_proofs.append(valid_proofs[0])  # Send 1 CV as proof
            else:
                lieutenant.intermediate_decision = d_i
                unique_proofs = dict(zip(valid_decisions, valid_proofs))
                contradicting_proofs = list(unique_proofs.values())[:2]  # Guarenteed to have exactly 2 values
                collected_proofs.extend(contradicting_proofs)  # Send 2 contradicting CVs as proof

        # Send/Receive with collected_proofs

        if lieutenant.is_traitor: # Insert simple traitor logic
            tuple_length = N - 1
            random_decision = random.choice([True, False, None])
            lieutenant.intermediate_decision = random_decision
            num_CV = random.choice([0,1,2])
            random_CV = [[random.choice([True, False, None]) for _ in range(tuple_length * M)] for __ in range(num_CV)]
            for receiver_idx, receiver in enumerate(lieutenants):
                sender_idx = i
                # Note that the sender also sends the evidence to themselves for future reference
                receiver.proofs[sender_idx].intermediary = IntermediaryEvidence(
                    decision=lieutenant.intermediate_decision,
                    command_vectors = collected_proofs
                )
        else:
            for receiver_idx, receiver in enumerate(lieutenants):
                sender_idx = i
                # Note that the sender also sends the evidence to themselves for future reference
                receiver.proofs[sender_idx].intermediary = IntermediaryEvidence(
                    decision=lieutenant.intermediate_decision,
                    command_vectors = collected_proofs
                )

    # Round 4: Update
    # TODO: What if d_i = None but Rules 4.1/4.2 don't apply? Rules 4.3-4.6 wouldn't apply either. Ask Santiago

    for i, lieutenant in enumerate(lieutenants):
        d_i = lieutenant.intermediate_decision

        # Rule 4.1
        if (d_i == None and len(lieutenant.proofs[i].intermediary.command_vectors) == 2):
            lieutenant.final_decision = d_i
            continue

        received_decisions = [
            bundle.intermediary.decision 
            for sender_idx, bundle in lieutenant.proofs.items()
        ]

        # Rule 4.2
        if all(d == d_i for d in received_decisions):
            lieutenant.final_decision = d_i
            continue

        if d_i in (0, 1):
            conflict_found = False
            if any(bundle.intermediary.decision is None and bundle.initial.decision is not None
                   for sender_idx, bundle in lieutenant.proofs.items()):
                for sender_idx, bundle in lieutenant.proofs.items():
                    # Verifying consistent application of Rule 3.3
                    if bundle.intermediary.decision is None and bundle.initial.decision is not None:
    
                        if (bundle.intermediary.command_vectors and
                            lieutenant.check_lieutenant_by_command_vector(
                                sender_idx,
                                bundle.initial.decision,
                                bundle.intermediary.command_vectors[0],
                                tolerance=M//10
                            )):
                            conflict_found = True
                            break
                # Rule 4.3/4.4
                if conflict_found:
                    lieutenant.final_decision = None
                else:
                    lieutenant.final_decision = d_i
                continue 

            conflict_found = False
            for sender_idx, bundle in lieutenant.proofs.items():
                if bundle.intermediary.decision == (not d_i):
                    if (bundle.intermediary.command_vectors and
                        lieutenant.check_lieutenant_by_command_vector(
                            sender_idx,
                            bundle.intermediary.decision,
                            bundle.intermediary.command_vectors[0],
                            tolerance=M//10
                        )):
                            conflict_found = True
                            break
            
            # Rule 4.5/4.6
            if conflict_found:
                lieutenant.final_decision = None
            else:
                lieutenant.final_decision = d_i
            continue 

    results = {
        "alice": alice,
        "lieutenants": lieutenants
    }
    return results

if __name__ == "__main__":
    results = run_simulation()
    print_game_stats(results["alice"], results["lieutenants"])
