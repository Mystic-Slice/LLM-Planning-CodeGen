from grasp.util import load_jsonl
import json
import os
from pathlib import Path

from model_codes_iterative.claude.a_basic import solve as solve_claude_a_basic
from model_codes_iterative.claude.b import solve as solve_claude_b
from model_codes_iterative.claude.c import solve as solve_claude_c
from model_codes_iterative.claude.d import solve as solve_claude_d

from model_codes_iterative.o3_mini.a_basic import solve as solve_o3_mini_a_basic
from model_codes_iterative.o3_mini.b import solve as solve_o3_mini_b
from model_codes_iterative.o3_mini.c import solve as solve_o3_mini_c

from model_codes_iterative.o1.a_basic import solve as solve_o1_a_basic
from model_codes_iterative.o1.b import solve as solve_o1_b
from model_codes_iterative.o1.c import solve as solve_o1_c

from model_codes_iterative.deepseek.a_basic import solve as solve_deepseek_a_basic
from model_codes_iterative.deepseek.b import solve as solve_deepseek_b

from model_codes_iterative.gemini_25_pro.a_basic import solve as solve_gemini_25_a_basic
from model_codes_iterative.gemini_25_pro.b import solve as solve_gemini_25_b
from model_codes_iterative.gemini_25_pro.c import solve as solve_gemini_25_c
from model_codes_iterative.gemini_25_pro.d import solve as solve_gemini_25_d
from model_codes_iterative.gemini_25_pro.e import solve as solve_gemini_25_e

from model_codes_iterative.gpt_4o.a_basic import solve as solve_gpt_4o_a_basic
from model_codes_iterative.gpt_4o.b import solve as solve_gpt_4o_b
from model_codes_iterative.gpt_4o.c import solve as solve_gpt_4o_c
from model_codes_iterative.gpt_4o.d import solve as solve_gpt_4o_d
from model_codes_iterative.gpt_4o.e import solve as solve_gpt_4o_e
from model_codes_iterative.gpt_4o.f import solve as solve_gpt_4o_f

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
    "iterative": {
        "claude_a_basic": solve_claude_a_basic,
        "claude_b": solve_claude_b,
        "claude_c": solve_claude_c,
        "claude_d": solve_claude_d,
        "o3_mini_a_basic": solve_o3_mini_a_basic,
        "o3_mini_b": solve_o3_mini_b,
        "o3_mini_c": solve_o3_mini_c,
        "o1_a_basic": solve_o1_a_basic,
        "o1_b": solve_o1_b,
        "o1_c": solve_o1_c,
        "gemini_25_a_basic": solve_gemini_25_a_basic,
        "gemini_25_b": solve_gemini_25_b,
        "gemini_25_c": solve_gemini_25_c,
        "gemini_25_d": solve_gemini_25_d,
        "gemini_25_e": solve_gemini_25_e,
        "gpt_4o_a_basic": solve_gpt_4o_a_basic,
        "gpt_4o_b": solve_gpt_4o_b,
        "gpt_4o_c": solve_gpt_4o_c,
        "gpt_4o_d": solve_gpt_4o_d,
        "gpt_4o_e": solve_gpt_4o_e,
        "gpt_4o_f": solve_gpt_4o_f,
        "deepseek_a_basic": solve_deepseek_a_basic,
        "deepseek_b": solve_deepseek_b,
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