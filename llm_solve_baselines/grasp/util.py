import json
from .environment import GridEnvironment
from .agent import Agent

def load_jsonl(input_path) -> list:
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.rstrip('\n|\r')))
    return data

def get_grid_after_actions(grid_str, actions):
    env = GridEnvironment(start=False)
    agent_start_position = env.load_grid(grid_str, return_agent_position=True)

    agent = Agent(agent_start_position[0], agent_start_position[1])

    allowed_action_list = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'UPLEFT', 'UPRIGHT', 'DOWNLEFT', 'DOWNRIGHT']
    carry_limit = 2

    for action in actions:
        action = action.upper()

        if action in allowed_action_list:
            if not env.move_agent(agent, action.lower()):
                # print("Invalid move")
                invalid_move = True
        elif action == 'TAKE':
            if agent.energy < carry_limit:
                env.take_energy(agent)
        elif action == 'DROP':
            env.drop_all_energy(agent)

    grid_str = env.to_string(agent.position, agent_start_position)

    num_energy_collected = env.grid[agent_start_position[0]][agent_start_position[1]].energy

    return grid_str, num_energy_collected