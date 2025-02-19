# EPR-ByzantineAgreement

This repository contains an implementation of [an EPR-based Quantum Detectable Byzantine Agreement protocol](https://arxiv.org/pdf/2306.10825) using aqnsim.

## Setup

Activate the conda environment and install in editable mode:

    conda activate aqnsim-dev
    pip install -e .

## Verification

Run the tests from the repository root:

    pytest

## Configuration

Adjust protocol settings in:

    eprq_dba/config.py

## Running the Simulation

Run the simulation to see protocol output based on the config:

    python eprq_dba/simulation.py
