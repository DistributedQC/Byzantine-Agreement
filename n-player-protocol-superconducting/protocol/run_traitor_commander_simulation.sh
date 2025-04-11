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
  runs_per_t1_interval=$7
  t1_intervals=$8

  lieutenants=$(generate_lieutenants_array $num_lieutenants)

  for t1_interval in $t1_intervals; do
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
NOISE_TIME = $t1_interval * T1_TIME

N = 1 + len(LIEUTENANT_NAMES)
COMMANDER_QMEMORY_ADDR = N - 1

NUM_PLAYERS = N
NUM_LIEUTENANTS = N - 1
EOL

    sleep 0.1

    for ((i=1; i<=runs_per_t1_interval; i++)); do
      python run_traitor_commander_simulation.py #NOTE: Due to 6 cores, runs the simulation 16x per python call
    done
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

#t1_intervals="0.000001 0.00001 0.0001 0.001 0.01 0.1 1"
t1_intervals="0.5"

run_simulation "Alice" 4 1 '[]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 10 '[]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 20 '[]' True True 30 "$t1_intervals"

run_simulation "Alice" 4 1 '[0]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 10 '[0]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 20 '[0]' True True 30 "$t1_intervals"

run_simulation "Alice" 4 1 '[0,1]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 10 '[0,1]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 20 '[0,1]' True True 30 "$t1_intervals"

run_simulation "Alice" 4 1 '[0,1,2]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 10 '[0,1,2]' True True 30 "$t1_intervals"
run_simulation "Alice" 4 20 '[0,1,2]' True True 30 "$t1_intervals"
