# EPR-ByzantineAgreement

This repository contains an implementation of [an EPR-based Quantum Detectable Byzantine Agreement protocol](https://arxiv.org/pdf/2306.10825) using aqnsim discrete event simulation.

## Setup

Activate the conda environment and install in editable mode:

    conda activate aqnsim-dev
    pip install -e .

## Configuration

Adjust protocol settings in:

    protcol/config.py

## Running the Simulation

Run the simulation to see protocol output based on the config:

    python protocol/simulation.py