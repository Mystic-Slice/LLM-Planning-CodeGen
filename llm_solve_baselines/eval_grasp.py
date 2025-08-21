import glob
import re

from grasp.check_energy import check_energy_result
from grasp.util import load_jsonl

RESULT_FILES = glob.glob(f"grasp_results/*/*/*.json")

df = []

def extract_final_answer(response):
        
    match = re.search(r"<final_answer>(.*?)</final_answer>", response, re.DOTALL)

    if not match:
        return "ERROR: Response is invalid. Does not contain <final_answer>."

    final_answer_str = match.group(1).strip().replace("[", "").replace("]", "")
    final_answer = [x.strip().replace("\"", "").replace("\'", "") for x in final_answer_str.split(",")]

    return final_answer

for i, result_file in enumerate(RESULT_FILES):
    print(f"Processing {i+1}/{len(RESULT_FILES)}: {result_file}\r", end="")
    split_file = result_file.split("\\")
    model_name = split_file[1]
    method = split_file[2]

    filename = split_file[-1].split(".")[0]
    dataset_name = "_".join(filename.split("_")[:-1])


    # print(f"Model: {model_name}")
    # print(f"Dataset: {dataset_name}")
    # print(f"Prompt: {prompt_type}")
    # print(f"Movement: {movement_dir}")
    # print(f"Carry Limit: {carry_limit}")
    # print(f"Cost per Step: {cost_per_step}")
    # print(f"Index: {grid_index}")
    # print("Results: ")

    d = load_jsonl(result_file)[0]
    d['dataset_name'] = dataset_name
    d['method'] = method
    d['model_name'] = model_name

    try:
        grid_string = d['grid']
        agent_solution = extract_final_answer(d['response'])
        # print(len(agent_solution))
        # print(agent_solution)
        if not isinstance(agent_solution, list):
            raise Exception("Invalid solution")
        energy, returns_to_start, invalid_move = check_energy_result(
            grid_string,
            d['start'],
            agent_solution,
            1,
            2,
            0.3
        )

        # print(f"Energy: {energy}")
        # print(f"Returns to start: {returns_to_start}")
        # print(f"Invalid move: {invalid_move}")

        d['energy'] = energy
        d['returns_to_start'] = returns_to_start
        d['invalid_move'] = invalid_move
        d['valid'] = True

    except:
        print(f"Error: Invalid solution for index: {d['index']}")
        d['energy'] = float('NaN')
        d['returns_to_start'] = float('NaN')
        d['invalid_move'] = float('NaN')
        d['valid'] = False

    if 'messages' in d:
        del d['messages']
    del d['grid']
    if 'sys_prompt' in d:
        del d['sys_prompt']

    if 'prompt' in d:
        del d['prompt']
    del d['start']
    # del d['actions']

    df.append(d)

import pandas as pd
import os

df = pd.DataFrame(df)
df.to_csv(f"grasp_results/results.csv", index=False)