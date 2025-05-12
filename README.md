# Code-Driven Planning in Grid Worlds with Large Language Models

This repository contains all the model-generated code, data and code to reproduce the experiments in the paper.

The code and data for each of the tasks are found in the respective folders:
1. GRASP: `grasp_direct_code_gen`, `grasp_iterative_refinement`
    - `run.py` contains the code to run the model codes
    - `eval.py` contains the code to evaluate the model codes
2. MiniGrid Unlock: `minigrid_unlock`
    - `run.ipynb` contains the code to run and evaluate the model codes
3. MiniGrid DoorKey: `minigrid_doorkey`
    - `run.ipynb` contains the code to run and evaluate the model codes
4. MiniGrid Unlock Pickup: `minigrid_unlock_pickup`
    - `run.ipynb` contains the code to run and evaluate the model codes

`llm_solves_baselines` contains code to run and evaluate direct prompt based planning baselines which include CoT and 2-step CoT.

## Requirements:
- [minigrid](https://minigrid.farama.org/content/basic_usage/#installation)
- pandas
- matplotlib
- numpy
- glob
- openai