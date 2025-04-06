#!/bin/bash

generate_lieutenants_array() {
  length=$1
  lieutenants="["
  for ((i=1; i<=length; i++)); do
    if [[ $i -lt $length ]]; then
      lieutenants+="\"L$i\", "
    else
      lieutenants+="\"L$i\""
    fi
  done
  lieutenants+="]"
  echo "$lieutenants"
}

run_simulation() {
  commander_name=$1
  num_lieutenants=$2
  M=$3
  traitors=$4
  commander_is_traitor=$5
  loyal_commander_order=$6
  runs=$7

  lieutenants=$(generate_lieutenants_array $num_lieutenants)

    cat > config.py << EOL
import aqnsim

COMMANDER_NAME = "$commander_name"
LIEUTENANT_NAMES = $lieutenants
DISTRIBUTOR_NAME = "Distributor"

M = $M

COMMANDER_IS_TRAITOR = $commander_is_traitor
TRAITOR_INDICES = $traitors
LOYAL_COMMANDER_ORDER = $loyal_commander_order

SEND_ORDER_ACTION = "SEND_ORDER"
SEND_CV_ACTION = "SEND_CV"
ROUND2_ACTION = "ROUND2_ACTION"
ROUND3_ACTION = "ROUND3_ACTION"

SEC = aqnsim.SECOND
QSOURCE_NOISE_MODEL = None
QUANTUM_CHANNEL_DELAY = 0 * SEC 
QUANTUM_CHANNEL_NOISE = 0.0
CLASSICAL_CHANNEL_DELAY = 1 * SEC

T1_TIME = 0.00005 * SEC
NOISE_TIME = 0 * SEC

N = 1 + len(LIEUTENANT_NAMES)
COMMANDER_QMEMORY_ADDR = N - 1

NUM_PLAYERS = N
NUM_LIEUTENANTS = N - 1
EOL

    sleep 0.1

    for ((i=1; i<=runs; i++)); do
      python run_noiseless_loyal_commander_simulation.py #NOTE: Due to 6 cores, runs the simulation 16x per python call
    done
}


# Parameters:
#   commander_name=$1
#   num_lieutenants=$2
#   M=$3
#   traitors=$4
#   commander_is_traitor=$5
#   loyal_commander_order=$6
#   runs_per_t1_interval=$7
#   t1_intervals=$8


run_simulation "Alice" 2 1 '[]' False True 30 
run_simulation "Alice" 2 10 '[]' False True 30 
run_simulation "Alice" 2 20 '[]' False True 30 

run_simulation "Alice" 2 1 '[0]' False True 30 
run_simulation "Alice" 2 10 '[0]' False True 30 
run_simulation "Alice" 2 20 '[0]' False True 30 

run_simulation "Alice" 4 1 '[]' False True 30 
run_simulation "Alice" 4 10 '[]' False True 30 
run_simulation "Alice" 4 20 '[]' False True 30 

run_simulation "Alice" 4 1 '[0]' False True 30 
run_simulation "Alice" 4 10 '[0]' False True 30 
run_simulation "Alice" 4 20 '[0]' False True 30 

run_simulation "Alice" 4 1 '[0,1]' False True 30 
run_simulation "Alice" 4 10 '[0,1]' False True 30 
run_simulation "Alice" 4 20 '[0,1]' False True 30 

run_simulation "Alice" 4 1 '[0,1,2]' False True 30 
run_simulation "Alice" 4 10 '[0,1,2]' False True 30 
run_simulation "Alice" 4 20 '[0,1,2]' False True 30 

run_simulation "Alice" 9 1 '[]' False True 30 
run_simulation "Alice" 9 10 '[]' False True 30 
run_simulation "Alice" 9 20 '[]' False True 30 

run_simulation "Alice" 9 1 '[0]' False True 30 
run_simulation "Alice" 9 10 '[0]' False True 30 
run_simulation "Alice" 9 20 '[0]' False True 30 

run_simulation "Alice" 9 1 '[0,1,2]' False True 30 
run_simulation "Alice" 9 10 '[0,1,2]' False True 30 
run_simulation "Alice" 9 20 '[0,1,2]' False True 30 

run_simulation "Alice" 9 1 '[0,1,2,3,4]' False True 30 
run_simulation "Alice" 9 10 '[0,1,2,3,4]' False True 30 
run_simulation "Alice" 9 20 '[0,1,2,3,4]' False True 30 

run_simulation "Alice" 9 1 '[0,1,2,3,4,5,6]' False True 30 
run_simulation "Alice" 9 10 '[0,1,2,3,4,5,6]' False True 30 
run_simulation "Alice" 9 20 '[0,1,2,3,4,5,6]' False True 30 

run_simulation "Alice" 14 1 '[]' False True 30 
run_simulation "Alice" 14 10 '[]' False True 30 
run_simulation "Alice" 14 20 '[]' False True 30 

run_simulation "Alice" 14 1 '[0]' False True 30 
run_simulation "Alice" 14 10 '[0]' False True 30 
run_simulation "Alice" 14 20 '[0]' False True 30 

run_simulation "Alice" 14 1 '[0,1,2,3,4]' False True 30 
run_simulation "Alice" 14 10 '[0,1,2,3,4]' False True 30 
run_simulation "Alice" 14 20 '[0,1,2,3,4]' False True 30 

run_simulation "Alice" 14 1 '[0,1,2,3,4,5,6,7,8]' False True 30 
run_simulation "Alice" 14 10 '[0,1,2,3,4,5,6,7,8]' False True 30 
run_simulation "Alice" 14 20 '[0,1,2,3,4,5,6,7,8]' False True 30 

run_simulation "Alice" 14 1 '[0,1,2,3,4,5,6,7,8,9,10,11,12]' False True 30 
run_simulation "Alice" 14 10 '[0,1,2,3,4,5,6,7,8,9,10,11,12]' False True 30 
run_simulation "Alice" 14 20 '[0,1,2,3,4,5,6,7,8,9,10,11,12]' False True 30 