import glob
import re

from grasp.check_energy import check_energy_result
from grasp.util import load_jsonl

RESULT_FILES = glob.glob(f"grasp_results/*/*.json")

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
    method = split_file[1]

    filename = split_file[-1].split(".")[0]
    dataset_name = "_".join(filename.split("_")[:-1])

    d = load_jsonl(result_file)[0]
    d['dataset_name'] = dataset_name
    d['method'] = method

    try:
        grid_string = d['grid']
        agent_solution = extract_final_answer(d['response'])

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