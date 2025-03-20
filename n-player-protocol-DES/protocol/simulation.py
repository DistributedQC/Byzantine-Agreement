import aqnsim
from protocol.distributor import Distributor, DistributorProtocol
from protocol.lieutenants import Lieutenant, LieutenantProtocol
from protocol.commander import Commander, CommanderProtocol
from typing import List, Any
from protocol.config import SimulationConfig
# from protocol.config import (
#     COMMANDER_NAME, COMMANDER_IS_TRAITOR, LOYAL_COMMANDER_ORDER,
#     LIEUTENANT_NAMES, TRAITOR_INDICES,
#     DISTRIBUTOR_NAME,
#     QUANTUM_CHANNEL_DELAY, QUANTUM_CHANNEL_NOISE, CLASSICAL_CHANNEL_DELAY
# )

def print_game_stats(results, sim_config: SimulationConfig):
    print("\n================ Game Summary ================")
    print(f"Commander: {sim_config.COMMANDER_NAME}")
    print(f"Commander's orders: {latest_results[sim_config.COMMANDER_NAME][0]['orders']}")
    print(f"Commander is {'TRAITOR' if latest_results[sim_config.COMMANDER_NAME][0]['is_traitor'] else 'loyal'}")
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


def create_commander(sim_context: aqnsim.SimulationContext, sim_config: SimulationConfig):
    if sim_config.COMMANDER_IS_TRAITOR:
        orders = [aqnsim.random_utilities.choice([True, False]) for _ in sim_config.LIEUTENANT_NAMES]
    else:
        orders = [sim_config.LOYAL_COMMANDER_ORDER] * len(sim_config.LIEUTENANT_NAMES)
    
    return Commander(sim_context, sim_config.COMMANDER_NAME, orders, sim_config.COMMANDER_IS_TRAITOR, sim_config=sim_config)


def create_lieutenants(sim_context: aqnsim.SimulationContext, sim_config: SimulationConfig):
    return [
        Lieutenant(
            sim_context = sim_context, 
            name = name, 
            lieutenant_index = idx, 
            is_traitor = (idx in sim_config.TRAITOR_INDICES),
            sim_config=sim_config
        )
        for idx, name in enumerate(sim_config.LIEUTENANT_NAMES)
    ]

    
def setup_network(sim_context: aqnsim.SimulationContext, parameters: SimulationConfig) -> aqnsim.Network:
    
    
    distributor = Distributor(sim_context = sim_context, name = parameters.DISTRIBUTOR_NAME, sim_config=parameters)
    commander = create_commander(sim_context, parameters)
    lieutenants = create_lieutenants(sim_context, parameters)

    network = aqnsim.Network(sim_context=sim_context, nodes=[distributor, commander] + lieutenants)

    players = lieutenants + [commander]

    for player in players:
        qlink = aqnsim.QuantumLink(
            sim_context = sim_context,
            delay = parameters.QUANTUM_CHANNEL_DELAY,
            noise = parameters.QUANTUM_CHANNEL_NOISE,
            name=f"Q_Link_{player.name}_{parameters.DISTRIBUTOR_NAME}"       
        )
        network.add_link(qlink, distributor, player, player.name, parameters.DISTRIBUTOR_NAME)

    for player1 in players:
        for player2 in players:
            if player1 == player2:
                continue
            clink = aqnsim.ClassicalLink(
                sim_context = sim_context,
                delay = parameters.CLASSICAL_CHANNEL_DELAY,
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
    sim_config = SimulationConfig(COMMANDER_IS_TRAITOR=False)
    results = run_simulation(sim_config)
    latest_results = {k: v[-1] if v else None for k, v in results.items()}
    print_game_stats(latest_results, sim_config)
