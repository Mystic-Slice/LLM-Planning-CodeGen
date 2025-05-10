from grasp.run_greedy_random import run_greedy, run_random
from grasp.util import load_jsonl
import json
import os
from pathlib import Path
from model_codes.claude import solve_energy_collection_game as solve_claude
from model_codes.o1 import solve as solve_o1
from model_codes.deepseek import solve as solve_deepseek
from model_codes.o3_mini import solve as solve_o3_mini
from model_codes.gpt_4o import solve as solve_gpt_4o
from model_codes.gemini_25_pro import solve as solve_gemini_25_pro

from model_codes_extend_greedy_pseudocode.o3_mini import solve as solve_o3_mini_greedy_pseudocode
from model_codes_extend_greedy_pseudocode.o1 import solve as solve_o1_greedy_pseudocode
from model_codes_extend_greedy_pseudocode.claude import solve as solve_claude_greedy_pseudocode

from model_codes_step_by_step_intermediate.claude_0 import solve as solve_claude_step_by_step_intermediate_0
from model_codes_step_by_step_intermediate.claude_1 import solve as solve_claude_step_by_step_intermediate_1
from model_codes_step_by_step_intermediate.claude_2 import solve as solve_claude_step_by_step_intermediate_2
from model_codes_step_by_step_intermediate.claude_3 import solve as solve_claude_step_by_step_intermediate_3
from model_codes_step_by_step_intermediate.claude_4 import solve as solve_claude_step_by_step_intermediate_4

from model_codes_step_by_step_intermediate.o1_0 import solve as solve_o1_step_by_step_intermediate_0
from model_codes_step_by_step_intermediate.o1_1 import solve as solve_o1_step_by_step_intermediate_1
from model_codes_step_by_step_intermediate.o1_2 import solve as solve_o1_step_by_step_intermediate_2
from model_codes_step_by_step_intermediate.o1_3 import solve as solve_o1_step_by_step_intermediate_3
from model_codes_step_by_step_intermediate.o1_4 import solve as solve_o1_step_by_step_intermediate_4

from model_codes_step_by_step_intermediate.o3_mini_0 import solve as solve_o3_mini_step_by_step_intermediate_0
from model_codes_step_by_step_intermediate.o3_mini_1 import solve as solve_o3_mini_step_by_step_intermediate_1
from model_codes_step_by_step_intermediate.o3_mini_2 import solve as solve_o3_mini_step_by_step_intermediate_2
from model_codes_step_by_step_intermediate.o3_mini_3 import solve as solve_o3_mini_step_by_step_intermediate_3
from model_codes_step_by_step_intermediate.o3_mini_4 import solve as solve_o3_mini_step_by_step_intermediate_4


DATASET_FILES = [x.split(".")[0] for x in os.listdir("GRASP\data\grids")]
print(DATASET_FILES)

MOVEMENT_DIRS = [
    "four",
    "eight",
]

CARRY_LIMITS = [
    100,
    2
]

COST_OF_STEP = [
    0,
    0.3,
]

# 20 datasets x 8 settings = 160
NUM_SAMPLES_PER_DATASET = 100

print(f"Running on {len(DATASET_FILES)} datasets")


METHODS = {
    "baseline": {
        "greedy": run_greedy,
        "random": run_random,
    },
    "direct_code_gen": {
        "claude": solve_claude,
        "deepseek": solve_deepseek,
        "gpt_4o": solve_gpt_4o,
        "o1": solve_o1,
        "o3_mini": solve_o3_mini,
        "gemini_25_pro": solve_gemini_25_pro,
    },
    "greedy_extend_pseudocode": {
        "o1": solve_o1_greedy_pseudocode,
        "claude": solve_claude_greedy_pseudocode,
        "o3_mini": solve_o3_mini_greedy_pseudocode,
    },
    "step_by_step_intermediate": {
        "claude_0": solve_claude_step_by_step_intermediate_0,
        "claude_1": solve_claude_step_by_step_intermediate_1,
        "claude_2": solve_claude_step_by_step_intermediate_2,
        "claude_3": solve_claude_step_by_step_intermediate_3,
        "claude_4": solve_claude_step_by_step_intermediate_4,
        "o1_0": solve_o1_step_by_step_intermediate_0,
        "o1_1": solve_o1_step_by_step_intermediate_1,
        "o1_2": solve_o1_step_by_step_intermediate_2,
        "o1_3": solve_o1_step_by_step_intermediate_3,
        "o1_4": solve_o1_step_by_step_intermediate_4,
        "o3_mini_0": solve_o3_mini_step_by_step_intermediate_0,
        "o3_mini_1": solve_o3_mini_step_by_step_intermediate_1,
        "o3_mini_2": solve_o3_mini_step_by_step_intermediate_2,
        "o3_mini_3": solve_o3_mini_step_by_step_intermediate_3,
        "o3_mini_4": solve_o3_mini_step_by_step_intermediate_4,
    },
}

count = 0

for dataset_file in DATASET_FILES:
    dataset_file = f"GRASP\data\grids\{dataset_file}.jsonl"
    print("Dataset: ", dataset_file)
    file_name = Path(dataset_file).stem
    data = load_jsonl(dataset_file)[:NUM_SAMPLES_PER_DATASET]

    for method_cls, methods_dict in METHODS.items():

        for method_name, method_func in methods_dict.items():
            print("Method: ", method_name)
            for movement_dir in MOVEMENT_DIRS:
                for carry_limit in CARRY_LIMITS:
                    for cost_of_step in COST_OF_STEP:
                        print(movement_dir, carry_limit, cost_of_step)
                        all_data = []
                        for d in data:
                            count += 1
                            output_dir = f"all_results/{method_cls}/{file_name}/{method_name}/{movement_dir}_{carry_limit}_{cost_of_step}"
                            output_file_name = f"{output_dir}/{d['index']}.jsonl"

                            # check if file already exists
                            if os.path.exists(output_file_name):
                                print(f"File {output_file_name} already exists. Skipping.")
                                continue

                            print(f"Index: {d['index']}/{NUM_SAMPLES_PER_DATASET}\r", end="")

                            d['method'] = method_name
                            grid_string = d['grid']

                            actions = method_func(grid_string, d['start'], movement_dir, carry_limit, cost_of_step)
                            actions = [action.upper() for action in actions]

                            d['actions'] = actions

                            os.makedirs(output_dir, exist_ok=True)

                            # Write to json
                            with open(output_file_name, "w") as f:
                                f.write(json.dumps(d))
                        print()

print("Total count: ", count)