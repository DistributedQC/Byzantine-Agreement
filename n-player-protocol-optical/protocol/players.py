import aqnsim
from dataclasses import dataclass, field
from functools import partial
from protocol.config import NUM_PLAYERS, COMMANDER_NAME, LIEUTENANT_NAMES, N, M, NUM_LIEUTENANTS, DISTRIBUTOR_NAME

"""
DEFINE BASE PLAYER CLASS
"""

class Player(aqnsim.Node):
    def __init__(self, sim_context: aqnsim.SimulationContext, name: str):
        super().__init__(
            sim_context=sim_context,
            ports=[DISTRIBUTOR_NAME] + [COMMANDER_NAME] + LIEUTENANT_NAMES, # All-to-all classical communication; port with your own name isn't used
            name=name
        )
        self.data_collector.register_attribute(self.name)
        self.bit_vector = []

        # Create a polarizing beam splitter.
        self.pbs = aqnsim.PolarizingBeamSplitter(sim_context=sim_context, name="pbs")
        self.add_subcomponent(self.pbs)

        # Create a photon detector for each output of the PBS. 
        self.detector0 = aqnsim.PhotonDetector(sim_context=sim_context, name="detector0")
        self.detector1 = aqnsim.PhotonDetector(sim_context=sim_context, name="detector1")
        self.add_subcomponent(self.detector0)
        self.add_subcomponent(self.detector1)

        # Connect the port of the player to the port of polarizing beam splitter.
        self.ports[DISTRIBUTOR_NAME].forward_input_to_input(self.pbs.ports["qin0"])

        # The PBS has two outputs each going to an independent detector.
        self.pbs.ports["qout0"].forward_output_to_input(self.detector0.ports["qin0"])
        self.pbs.ports["qout1"].forward_output_to_input(self.detector1.ports["qin0"])

        # Set up measurement handlers to process results from the photon detectors.
        measurement_handler_HV_0 = partial(self._measurement_handler, detection=0)
        measurement_handler_HV_1 = partial(self._measurement_handler, detection=1)

        # Generate photon detector port handlers.
        self.detector0.ports["cout0"].add_rx_output_handler(measurement_handler_HV_0)
        self.detector1.ports["cout0"].add_rx_output_handler(measurement_handler_HV_1)


    def _measurement_handler(self, msg, detection):
        """
        Measurement handler to process measurement results from the photon detectors.
        """
        self.simlogger.info(f"measurement_handler at node {self.name}, msg: {msg}")
        self.bit_vector.append(detection)
        self.data_collector.update_attribute(self.name, value = self.bit_vector)
