from grasp.agent import Agent
from grasp.environment import GridEnvironment


def run_greedy(grid_string, agent_start_position, movement_dir, carry_limit, cost_of_step):

    env = GridEnvironment(start=False)
    env.load_grid(grid_string)

    agent = Agent(agent_start_position[0], agent_start_position[1])

    actions = env.greedy_search(agent, 4 if movement_dir == "four" else 8)
    return actions

def run_random(grid_string, agent_start_position, movement_dir, carry_limit, cost_of_step):

    env = GridEnvironment(start=False)
    env.load_grid(grid_string)

    agent = Agent(agent_start_position[0], agent_start_position[1])

    actions = env.random_walk(agent, 4 if movement_dir == "four" else 8)
    return actions