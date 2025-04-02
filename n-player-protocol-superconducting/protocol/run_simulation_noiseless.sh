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
  M_values=$3
  traitors=$4
  commander_is_traitor=$5
  loyal_commander_order=$6
  runs_per_M=$7

  lieutenants=$(generate_lieutenants_array $num_lieutenants)

  for M in $M_values; do
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

NOISE_TIME = 0 * SEC
T1_TIME = 1 * SEC

N = 1 + len(LIEUTENANT_NAMES)
COMMANDER_QMEMORY_ADDR = N - 1

NUM_PLAYERS = N
NUM_LIEUTENANTS = N - 1
EOL

    sleep 0.1
    
    for ((i=1; i<=runs_per_M; i++)); do
      python run_simulation_noiseless.py
    done
  done
}

# Example calls:
# run_simulation "Alice" 2 "1 5 10" '[0]' False True 50
# run_simulation "Alice" 5 "1 5 10" '[0,1]' False True 50
# run_simulation "Alice" 8 "1 5 10" '[0,1,2]' False True 50
# run_simulation "Alice" 17 "1 5 10" '[0,1,2,3,4,5]' False True 50
# run_simulation "Alice" 35 "1 5 10" '[0,1,2,3,4,5,6,7,8,9,10,11]' False True 50

# run_simulation "Alice" 2 "5" '[0]' False True 50 
run_simulation "Alice" 4 "5" '[0,1]' False True 50
# run_simulation "Alice" 6 "5" '[0,1,2]' False True 50
# run_simulation "Alice" 12 "5" '[0,1,2,3,4,5]' False True 50
