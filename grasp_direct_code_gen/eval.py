import glob

from grasp.check_energy import check_energy_result
from grasp.util import load_jsonl

# METHOD = 'baseline'
# METHOD = 'greedy_extend_pseudocode'
# METHOD = 'step_by_step_intermediate'
METHOD = 'direct_code_gen'
RESULT_FILES = glob.glob(f"all_results\\{METHOD}/*/*/*/*.jsonl")

df = []

for i, result_file in enumerate(RESULT_FILES):
    print(f"Processing {i+1}/{len(RESULT_FILES)}: {result_file}\r", end="")
    split_file = result_file.split("\\")
    # print(split_file)

    model_name = split_file[1]
    if model_name == "other":
        model_name = "No Model"
    dataset_name = split_file[2]
    prompt_type = split_file[3]
    movement_dir, carry_limit, cost_per_step = split_file[4].split("_")
    grid_index = split_file[5].split(".")[0]

    d = load_jsonl(result_file)[0]

    d['model'] = model_name
    d['dataset'] = dataset_name
    d['prompt_type'] = prompt_type
    d['movement_dir'] = movement_dir
    d['carry_limit'] = carry_limit
    d['cost_per_step'] = cost_per_step

    try:
        grid_string = d['grid']
        agent_solution = d['actions']

        if not isinstance(agent_solution, list):
            raise Exception("Invalid solution")
        energy, returns_to_start, invalid_move = check_energy_result(
            grid_string,
            d['start'],
            agent_solution,
            0 if movement_dir == "four" else 1,
            100 if float(carry_limit) == 0 else float(carry_limit),
            float(cost_per_step)
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

    df.append(d)

import pandas as pd

df = pd.DataFrame(df)
df.to_csv(f"all_results/results_{METHOD}.csv", index=False)