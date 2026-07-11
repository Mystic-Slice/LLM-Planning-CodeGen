from collections import deque

def bfs_find_path(grid, start, target):
    """ Performs BFS to find the shortest path from start to target position. """
    directions = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}
    queue = deque([(start, [])])
    visited = set()
    visited.add(start)

    while queue:
        position, path = queue.popleft()
        if position == target:
            return path
            
        for direction, (dr, dc) in directions.items():
            next_position = (position[0] + dr, position[1] + dc)
            if (0 <= next_position[0] < len(grid) and 0 <= next_position[1] < len(grid[0])
                and next_position not in visited):
                    queue.append((next_position, path + [direction]))
                    visited.add(next_position)

    return []

def find_closest_energy(grid, start):
    """ Finds the closest energy token 'E' from the start position using BFS. """
    directions = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}
    queue = deque([(start, [])])
    visited = set()
    visited.add(start)
    
    while queue:
        position, path = queue.popleft()
        if grid[position[0]][position[1]] == 'E':
            return path

        for direction, (dr, dc) in directions.items():
            next_position = (position[0] + dr, position[1] + dc)
            if (0 <= next_position[0] < len(grid) and 0 <= next_position[1] < len(grid[0])
                and next_position not in visited):
                    queue.append((next_position, path + [direction]))
                    visited.add(next_position)

    return []

def solve_grid(grid, start_position, max_actions):
    current_position = start_position
    starting_position = start_position
    actions_taken = 0
    collected_tokens = 0
    action_list = []

    while actions_taken < max_actions:
        if current_position == starting_position and collected_tokens > 0:
            action_list.append("DROP")
            actions_taken += 1
            collected_tokens = 0
            if actions_taken >= max_actions:
                break

        closest_energy_path = find_closest_energy(grid, current_position)
        
        if not closest_energy_path and current_position == starting_position:
            break  # No more tokens and already at start

        for direction in closest_energy_path:
            if actions_taken < max_actions:
                action_list.append(direction)
                actions_taken += 1
                if direction == "UP":
                    current_position = (current_position[0] - 1, current_position[1])
                elif direction == "DOWN":
                    current_position = (current_position[0] + 1, current_position[1])
                elif direction == "LEFT":
                    current_position = (current_position[0], current_position[1] - 1)
                elif direction == "RIGHT":
                    current_position = (current_position[0], current_position[1] + 1)

            if grid[current_position[0]][current_position[1]] == 'E' and actions_taken < max_actions:
                action_list.append("TAKE")
                collected_tokens += 1
                actions_taken += 1

        if collected_tokens > 0:
            path_to_start = bfs_find_path(grid, current_position, starting_position)
            for direction in path_to_start:
                if actions_taken < max_actions:
                    action_list.append(direction)
                    actions_taken += 1
                    if direction == "UP":
                        current_position = (current_position[0] - 1, current_position[1])
                    elif direction == "DOWN":
                        current_position = (current_position[0] + 1, current_position[1])
                    elif direction == "LEFT":
                        current_position = (current_position[0], current_position[1] - 1)
                    elif direction == "RIGHT":
                        current_position = (current_position[0], current_position[1] + 1)

            if current_position == starting_position:
                action_list.append("DROP")
                actions_taken += 1
                collected_tokens = 0

    return action_list

def parse_grid(grid_string):
    """Parse the grid string into a 2D grid and locate agent, energy tokens."""
    lines = grid_string.strip().split('\n')
    # Skip header lines and extract rows with actual grid data
    grid_lines = [line for line in lines if '|' in line]
    
    # Extract grid data
    grid = []
    for line in grid_lines:
        # Split by | and remove empty cells
        cells = line.split('|')
        row = []
        for cell in cells[1:-1]:  # Skip first and last empty elements
            if 'A' in cell:
                row.append('A')
            elif 'E' in cell:
                row.append('E')
            elif 'O' in cell:
                row.append('O')
            else:
                row.append(' ')
        grid.append(row)
    
    # Find agent position
    agent_pos = None
    energy_positions = []
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == 'A':
                agent_pos = (i, j)
            elif grid[i][j] == 'E':
                energy_positions.append((i, j))
    
    return grid, agent_pos, energy_positions

def solve(grid_str, start_pos, movement_type, carry_limit, cost_per_step, max_actions=20):
    grid, _, _ = parse_grid(grid_str)
    actions = solve_grid(grid, tuple(start_pos), max_actions)
    return actions

def main():
    # Example usage:
    # Define the sample grid
    sample_grid = [
        [' ', ' ', 'E', 'E', 'E', 'E', ' ', 'E', 'E', 'E', 'E'],
        [' ', ' ', 'E', 'E', 'E', ' ', ' ', ' ', ' ', 'E', ' '],
        ['E', ' ', ' ', ' ', 'E', ' ', ' ', 'E', 'E', ' ', ' '],
        ['E', 'E', 'E', 'E', ' ', 'E', 'E', 'E', ' ', 'E', 'E'],
        [' ', 'E', ' ', 'A', 'E', ' ', 'E', ' ', 'E', 'E', ' '],
        ['E', ' ', 'E', ' ', 'E', 'E', ' ', 'E', ' ', 'E', ' '],
        ['E', ' ', 'E', ' ', ' ', ' ', ' ', 'E', 'E', 'E', 'E'],
        ['E', 'E', ' ', ' ', ' ', ' ', 'E', ' ', 'E', 'E', ' '],
        ['E', ' ', 'E', 'E', 'E', ' ', ' ', ' ', 'E', 'E', ' '],
        [' ', ' ', 'E', 'E', 'E', ' ', 'E', ' ', ' ', ' ', ' '],
        [' ', 'E', 'E', ' ', 'E', 'E', ' ', 'E', ' ', 'E', 'E']
    ]

    # Starting position (4, 3)
    start_position = (4, 3)

    # Carry limit
    carry_limit = 3

    # Cost per step
    cost_per_step = 0.3  # Assuming each movement costs 1 action

    # Diagonals allowed
    diagonals_allowed = True

    # Actions to take
    actions = solve_grid(sample_grid, start_position, max_actions=20)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()