import json
import os
from minigrid_prompts import *
from openrouter import call_openrouter
import gymnasium as gym
from minigrid.wrappers import *
import re

def to_string(messages):
    return "\n".join([f"{m['role']}: {m['content']}" for m in messages])

def run_direct_prompt(base_prompt, env, _):
    grid, start_direction = get_inputs(env)
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": base_prompt.format(grid=grid, start_direction=start_direction),
        }
    ]

    response = call_openrouter(MODEL, messages)

    input_prompt = to_string(messages)

    return input_prompt, response

def run_cot_prompt(base_prompt, env, _):
    grid, start_direction = get_inputs(env)
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": base_prompt.format(grid=grid, start_direction=start_direction) + "\nLet's think step by step."
        }
    ]

    response = call_openrouter(MODEL, messages)

    input_prompt = to_string(messages)

    return input_prompt, response

def extract_final_answer(response):
        
    match = re.search(r"<actions>(.*?)</actions>", response, re.DOTALL)

    if not match:
        return None

    final_answer_str = match.group(1).strip().replace("[", "").replace("]", "")
    final_answer = [x.strip().replace("\"", "").replace("\'", "") for x in final_answer_str.split(",")]

    return final_answer

def run_2_step_prompt(base_prompt, env, first_step_prompt):
    grid, start_direction = get_inputs(env)
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": base_prompt.format(grid=grid, start_direction=start_direction) + "\n" + first_step_prompt,
        }
    ]

    response = call_openrouter(MODEL, messages)

    messages.append({
        "role": "assistant",
        "content": response
    })

    # Get updated grid from the response
    actions = extract_final_answer(response)
    holding_item = None
    direction = start_direction
    if actions is not None:
        ACTIONS_MAP = {
            'LEFT': 0,
            'RIGHT': 1,
            'MOVE': 2,
            'PICKUP': 3,
            'DROP': 4,
            'UNLOCK': 5,
        }
        for action in actions:
            env.step(ACTIONS_MAP[action])

        grid, direction = get_inputs(env)

        import minigrid
        if env.unwrapped.carrying is None:
            holding_item = None
        elif isinstance(env.unwrapped.carrying, minigrid.core.world_object.Key):
            holding_item = "KEY"
        elif isinstance(env.unwrapped.carrying, minigrid.core.world_object.Box):
            holding_item = "BOX"

    messages.append({
        "role": "user",
        "content": f"""
            The updated grid is:
            <updated_grid>
            {grid}
            </updated_grid>
            After those moves, you are facing {direction}{"" if holding_item is None else f" holding the {holding_item}"}. Now complete your actions and give your entire actions sequence.
        """
    })

    response = call_openrouter(MODEL, messages)

    input_prompt = to_string(messages)
    return input_prompt, response

def get_inputs(env):
    # convert to np array
    grid = env.get_wrapper_attr('pprint_grid')()
    split_rows = grid.split('\n')
    grid_cells = [[line[i:i+2] for i in range(0, len(line), 2)] for line in split_rows]

    OBJ_IDX_TO_TYPE = {
        'W': "WALL",
        'D': "DOOR",
        '_': "",
        'K': "KEY",
        'A': "BALL",
        'B': "BOX",
        'L': "DOOR",
        'V': 'AGENT',
        '^': 'AGENT',
        '>': 'AGENT',
        '<': 'AGENT',
        ' ': "",
        'G': "GOAL",
    }
    input_grid = [[OBJ_IDX_TO_TYPE[c[0]] for c in row] for row in grid_cells]

    direction = None
    if 'V' in grid:
        direction = 'DOWN'
    elif '^' in grid:
        direction = 'UP'
    elif '<' in grid:
        direction = 'LEFT'
    elif '>' in grid:
        direction = 'RIGHT'

    grid_str = "\n".join(["[" + ", ".join([f'"{cell}"' for cell in row]) + "]" for row in input_grid])
    input_grid = grid_str.replace("'", '"')
    return input_grid, direction

TASKS = {
    "unlock": {
        "task_name": "MiniGrid-Unlock-v0",
        "base_prompt": UNLOCK_PROMPT,
        "first_step_prompt": "First provide only the actions until you pickup the key. Based on those actions, an updated grid will be given to you, after which you will have to give your entire action sequence."
    },
    "door_key": {
        "task_name": "MiniGrid-DoorKey-8x8-v0",
        "base_prompt": DOOR_KEY_PROMPT,
        "first_step_prompt": "First provide only the actions until you unlock the door. Based on those actions, an updated grid will be given to you, after which you will have to give your entire action sequence."
    },
    "unlock_pickup": {
        "task_name": "MiniGrid-UnlockPickup-v0",
        "base_prompt": UNLOCK_PICKUP_PROMPT,
        "first_step_prompt": "First provide only the actions until you unlock the door. Based on those actions, an updated grid will be given to you, after which you will have to give your entire action sequence."
    }
}

NUM_GRIDS = 100
GRID_SEEDS = list(range(NUM_GRIDS))

MODEL = 'openai/o3-mini'

METHODS = {
    "direct": run_direct_prompt,
    "cot": run_cot_prompt,
    "2_step": run_2_step_prompt,
}


for task, task_info in TASKS.items():
    task_name = task_info["task_name"]
    base_prompt = task_info["base_prompt"]
    first_step_prompt = task_info["first_step_prompt"]

    print(f"Running task: {task_name}")
    env = gym.make(task_name)

    for seed in GRID_SEEDS:
        print(f"Processing grid {seed+1}/{NUM_GRIDS}")
        env.reset(seed=seed)

        grid, start_direction = get_inputs(env)

        for method_name, method_func in METHODS.items():
            print(f"Running method: {method_name}")
            output_dir = f"minigrid_results/{task}/{method_name}"
            output_file_name = f"{output_dir}/{seed}.json"

            # check if file already exists
            if os.path.exists(output_file_name):
                print(f"File {output_file_name} already exists. Skipping.")
                continue

            input_prompt, response = method_func(base_prompt, env, first_step_prompt)

            d = {
                "task": task,
                "seed": seed,
                "method": method_name,
                "model": MODEL,
                "grid": grid,
                "start_direction": start_direction,
                "input_prompt": input_prompt,
                "response": response
            }

            os.makedirs(output_dir, exist_ok=True)
            with open(output_file_name, 'w') as f:
                f.write(json.dumps(d))