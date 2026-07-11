from collections import deque

def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions):
    directions = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    if is_diagonals_allowed:
        directions.update({
            "UPLEFT": (-1, -1),
            "UPRIGHT": (-1, 1),
            "DOWNLEFT": (1, -1),
            "DOWNRIGHT": (1, 1)
        })

    def find_nearest_energy_bfs(current_position):
        visited = set()
        queue = deque([(current_position, [])])
        while queue:
            position, path = queue.popleft()
            if position in visited:
                continue
            visited.add(position)
            if grid[position[0]][position[1]] == 'E':
                return position, path
            for dir_name, (dx, dy) in directions.items():
                new_pos = (position[0] + dx, position[1] + dy)
                if is_within_bounds(new_pos) and new_pos not in visited and grid[new_pos[0]][new_pos[1]] != 'O':
                    queue.append((new_pos, path + [dir_name]))
        return None, []

    def is_within_bounds(position):
        return 0 <= position[0] < len(grid) and 0 <= position[1] < len(grid[0])

    def return_to_start(actions, current_position):
        return_actions = []
        rev_actions = actions[::-1]
        for action in rev_actions:
            if action not in ['TAKE', 'DROP']:
                move_back = {
                    "UP": "DOWN", "DOWN": "UP",
                    "LEFT": "RIGHT", "RIGHT": "LEFT",
                    "UPLEFT": "DOWNRIGHT", "UPRIGHT": "DOWNLEFT",
                    "DOWNLEFT": "UPRIGHT", "DOWNRIGHT": "UPLEFT"
                }[action]
                return_actions.append(move_back)
        return return_actions

    def calculate_cost(path_length):
        return path_length * cost_per_step
    
    actions = []
    current_position = start_pos
    actions_remaining = max_actions
    current_energy_carried = 0

    while actions_remaining > 0:
        nearest_energy_position, path = find_nearest_energy_bfs(current_position)
        if nearest_energy_position is None:
            if current_position != start_pos:
                return_actions = return_to_start(actions, current_position)
                actions.extend(return_actions)
                actions.append('DROP')
            break

        path_length = len(path)
        total_cost = calculate_cost(path_length * 2) + 2

        if total_cost <= actions_remaining:
            if current_energy_carried + 1 >= carry_limit or not find_nearest_energy_bfs(nearest_energy_position)[0]:
                for direction in path:
                    actions.append(direction)
                    current_position = (
                        current_position[0] + directions[direction][0],
                        current_position[1] + directions[direction][1]
                    )
                actions.append('TAKE')
                current_energy_carried += 1

                return_actions = return_to_start(actions, current_position)
                actions.extend(return_actions)
                actions.append('DROP')

                actions_remaining -= total_cost
                current_energy_carried = 0
                current_position = start_pos
            else:
                for direction in path:
                    actions.append(direction)
                    current_position = (
                        current_position[0] + directions[direction][0],
                        current_position[1] + directions[direction][1]
                    )
                actions.append('TAKE')
                current_energy_carried += 1
                actions_remaining -= total_cost
        else:
            return_actions = return_to_start(actions, current_position)
            actions.extend(return_actions)
            actions.append('DROP')
            break

    if current_position != start_pos:
        return_actions = return_to_start(actions, current_position)
        actions.extend(return_actions)
    if current_energy_carried > 0:
        actions.append('DROP')

    return actions

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
    actions = solve_grid(grid, tuple(start_pos), carry_limit, cost_per_step, (movement_type == 'eight'), max_actions)
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
    actions = solve_grid(sample_grid, start_position, carry_limit, cost_per_step, diagonals_allowed, max_actions=20)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()