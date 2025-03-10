import aqnsim
from protocol.distributor import Distributor, DistributorProtocol
from protocol.lieutenants import Lieutenant, LieutenantProtocol
from protocol.commander import Commander, CommanderProtocol
from protocol.config import (
    COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER,
    LIEUTENANT_NAMES, TRAITOR_INDICES,
    DISTRIBUTOR_NAME,
    QUANTUM_CHANNEL_DELAY, QUANTUM_CHANNEL_NOISE, CLASSICAL_CHANNEL_DELAY
)

def print_game_stats(results):
    print("\n================ Game Summary ================")
    print(f"Commander: {COMMANDER_NAME}")
    print(f"Commander's orders: {latest_results[COMMANDER_NAME][0]['orders']}")
    print(f"Commander is {'TRAITOR' if latest_results[COMMANDER_NAME][0]['is_traitor'] else 'loyal'}")
    print("-----------------------------------------------")
    print("Lieutenant Results:")
    for key, value in latest_results.items(): # PRINT LIEUTENANT INFO
        if "orders" not in latest_results[key][0]: 
            print(f"\nLieutenant: {key}")
            print(f"  Traitor: {'Yes' if latest_results[key][0]['is_traitor'] else 'No'}")
            print(f"  Received Order: {latest_results[key][0]['received_order']}")
            print(f"  Initial decision: {latest_results[key][0]['initial_decision']}")
            print(f"  Intermediate decision: {latest_results[key][0]['intermediate_decision']}")
            print(f"  Final decision: {latest_results[key][0]['final_decision']}")
    print("===============================================\n")


def create_commander(sim_context: aqnsim.SimulationContext):
    if COMMANDER_IS_TRAITOR:
        orders = [aqnsim.random_utilities.choice([True, False]) for _ in LIEUTENANT_NAMES]
    else:
        orders = [LOYAL_COMMANDER_ORDER] * len(LIEUTENANT_NAMES)
    
    return Commander(sim_context, COMMANDER_NAME, orders, COMMANDER_IS_TRAITOR)


def create_lieutenants(sim_context: aqnsim.SimulationContext):
    return [
        Lieutenant(
            sim_context = sim_context, 
            name = name, 
            lieutenant_index = idx, 
            is_traitor = (idx in TRAITOR_INDICES)
        )
        for idx, name in enumerate(LIEUTENANT_NAMES)
    ]

    
def setup_network(sim_context: aqnsim.SimulationContext) -> aqnsim.Network:
    distributor = Distributor(sim_context = sim_context, name = DISTRIBUTOR_NAME)
    commander = create_commander(sim_context)
    lieutenants = create_lieutenants(sim_context)

    network = aqnsim.Network(sim_context=sim_context, nodes=[distributor, commander] + lieutenants)

    players = lieutenants + [commander]

    for player in players:
        qlink = aqnsim.QuantumLink(
            sim_context = sim_context,
            delay = QUANTUM_CHANNEL_DELAY,
            noise = QUANTUM_CHANNEL_NOISE,
            name=f"Q_Link_{player.name}_{DISTRIBUTOR_NAME}"       
        )
        network.add_link(qlink, distributor, player, player.name, DISTRIBUTOR_NAME)

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
    CommanderProtocol(sim_context = sim_context, node = commander)
    for lieutenant in lieutenants:
        LieutenantProtocol(sim_context = sim_context, node = lieutenant)
        
    return network

if __name__ == "__main__":
    run_simulation = aqnsim.generate_run_simulation_fn(setup_sim_fn=setup_network, logging_level=20, log_to_file=False)
    results = run_simulation()
    latest_results = {k: v[-1] if v else None for k, v in results.items()}
    print_game_stats(latest_results)
