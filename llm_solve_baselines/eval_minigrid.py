import glob
import re

from grasp.util import *

import gymnasium as gym
from minigrid.wrappers import *

ACTIONS_MAP = {
    'LEFT': 0,
    'RIGHT': 1,
    'MOVE': 2,
    'PICKUP': 3,
    'DROP': 4,
    'UNLOCK': 5,
}
def eval(env, actions):
    action_ids = [ACTIONS_MAP[action] for action in actions if action in ACTIONS_MAP]

    reward = 0
    done = False

    for action in action_ids:
        obs, reward, done, _, _ = env.step(action)

    return reward, done
    

TASK_NAMES = {
    "unlock": "MiniGrid-Unlock-v0",
    "door_key": "MiniGrid-DoorKey-8x8-v0",
    "unlock_pickup": "MiniGrid-UnlockPickup-v0",
}

RESULT_FILES = glob.glob(f"minigrid_results/*/*/*/*.json")

df = []

def extract_final_answer(response):
        
    match = re.search(r"<actions>(.*?)</actions>", response, re.DOTALL)

    if not match:
        return "ERROR: Response is invalid. Does not contain <final_answer>."

    final_answer_str = match.group(1).strip().replace("[", "").replace("]", "")
    final_answer = [x.strip().replace("\"", "").replace("\'", "") for x in final_answer_str.split(",")]

    return final_answer

for i, result_file in enumerate(RESULT_FILES):
    print(f"Processing {i+1}/{len(RESULT_FILES)}: {result_file}")
    split_file = result_file.split("\\")
    model_name = split_file[1]
    task_name = split_file[2]
    method = split_file[3]

    d = load_jsonl(result_file)[0]
    d['task'] = task_name
    d['method'] = method
    d['model_name'] = model_name

    # try:
    grid_string = d['grid']
    start_dir = d['start_direction']
    agent_solution = extract_final_answer(d['response'])
    # print(len(agent_solution))
    # print(agent_solution)
    if not isinstance(agent_solution, list):
        # raise Exception("Invalid solution")
        print(f"Invalid solution for index: {d['seed']} by {model_name} with method {method} - {agent_solution}")
        agent_solution = []
    
    env = gym.make(TASK_NAMES[task_name])
    env.reset(seed=d['seed'])

    reward, done = eval(env, agent_solution)

    d['reward'] = reward
    d['done'] = done
    d['valid'] = True

    # except:
    #     print(f"Error: Invalid solution for index: {d['seed']}")
    #     d['reward'] = float('NaN')
    #     d['done'] = False
    #     d['valid'] = False

    if 'messages' in d:
        del d['messages']
    del d['grid']
    if 'sys_prompt' in d:
        del d['sys_prompt']

    if 'prompt' in d:
        del d['prompt']

    df.append(d)

import pandas as pd
import os

df = pd.DataFrame(df)
df.to_csv(f"minigrid_results/results.csv", index=False)