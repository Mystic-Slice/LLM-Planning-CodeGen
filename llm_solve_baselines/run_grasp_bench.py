import os
from grasp.util import *
from openrouter import call_openrouter
from baselines.grasp_prompts import get_plain_prompt
import re
import glob

data = []
NUM_GRIDS_PER_DATASET = 10
for datafile in glob.glob("grasp/data/grids/inner_*.jsonl"):
    print(f"Found data file: {datafile}")
    data += load_jsonl(datafile)[:NUM_GRIDS_PER_DATASET]

MODEL = 'openai/o3-mini'

base_prompt = get_plain_prompt("eight", 2, 0.3)

def to_string(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages])

def run_direct_prompt(grid_str):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": base_prompt + "\n" + f"<grid>\n{grid_str}\n</grid>"
        }
    ]

    response = call_openrouter(MODEL, messages)

    input_prompt = to_string(messages)

    return input_prompt, response

def run_cot_prompt(grid_str):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": base_prompt + "\n" + f"<grid>\n{grid_str}\n</grid>" + "\n" + "Let's think step by step." 
        }
    ]

    response = call_openrouter(MODEL, messages)

    input_prompt = to_string(messages)

    return input_prompt, response

def extract_final_answer(response):
        
    match = re.search(r"<final_answer>(.*?)</final_answer>", response, re.DOTALL)

    if not match:
        return "ERROR: Response is invalid. Does not contain <final_answer>."

    final_answer_str = match.group(1).strip().replace("[", "").replace("]", "")
    final_answer = [x.strip().replace("\"", "").replace("\'", "") for x in final_answer_str.split(",")]

    return final_answer

def run_2_step_prompt(grid_str):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": base_prompt + "\n" + "You should first give your first 10 actions. Based on those actions, an updated grid will be given to you, after which you will have to give your entire action sequence." + "\n" + f"<grid>\n{grid_str}\n</grid>"
        }
    ]

    response = call_openrouter(MODEL, messages)

    messages.append({
        "role": "assistant",
        "content": response
    })

    # Get updated grid from the response
    actions = extract_final_answer(response)
    num_energy_collected = 0
    if actions is not None:
        grid_str, num_energy_collected = get_grid_after_actions(grid_str, actions)
        
    messages.append({
        "role": "user",
        "content": f"""
            The updated grid is:
            <updated_grid>
            {grid_str}
            </updated_grid>
            So far, you have collected {num_energy_collected} energy tokens and you have incurred a cost of {len(actions) * 0.3} for using {len(actions)} moves (0.3 each). Now complete your actions and give your entire actions sequence.
        """
    })

    response = call_openrouter(MODEL, messages)

    input_prompt = to_string(messages)
    return input_prompt, response

METHODS = {
    "direct": run_direct_prompt,
    "cot": run_cot_prompt,
    "2_step": run_2_step_prompt,
}

results = []
for i, d in enumerate(data):
    print(f"Processing grid {i+1}/{len(data)}")
    dataset = f"{d['start_position']}_{d['energy']}_{d['obstacle']}"
    for method, func in METHODS.items():
        print(f"Running {method} method")
        output_dir = f"grasp_results/{method}"
        output_file_name = f"{output_dir}/{dataset}_{d['index']}.json"

        # check if file already exists
        if os.path.exists(output_file_name):
            print(f"File {output_file_name} already exists. Skipping.")
            continue

        grid_str = d['grid']
        input_prompt, response = func(grid_str)

        d['input_prompt'] = input_prompt
        d['response'] = response
        d['method'] = method
        d['model'] = MODEL

        os.makedirs(output_dir, exist_ok=True)

        # Write to json
        with open(output_file_name, "w") as f:
            f.write(json.dumps(d))