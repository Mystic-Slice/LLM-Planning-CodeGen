def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions):
    from collections import deque

    # Define possible moves
    DIRECTIONS_4 = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'LEFT': (-1, 0),
        'RIGHT': (1, 0),
    }
    DIRECTIONS_8 = {
        'UPLEFT': (-1, -1),
        'UPRIGHT': (1, -1),
        'DOWNLEFT': (-1, 1),
        'DOWNRIGHT': (1, 1),
    }
    if is_diagonals_allowed:
        DIRECTIONS = {**DIRECTIONS_4, **DIRECTIONS_8}
    else:
        DIRECTIONS = DIRECTIONS_4

    rows = len(grid)
    cols = len(grid[0])
    grid_dict = {}
    for y in range(rows):
        for x in range(cols):
            grid_dict[(x, y)] = grid[y][x]

    def is_valid_position(pos):
        x, y = pos
        if 0 <= x < cols and 0 <= y < rows and grid_dict.get((x, y)) != 'O':
            return True
        return False

    def get_neighbors(pos):
        neighbors = []
        for move, (dx, dy) in DIRECTIONS.items():
            new_pos = (pos[0] + dx, pos[1] + dy)
            if is_valid_position(new_pos):
                neighbors.append((new_pos, move))
        return neighbors

    def heuristic_distance(pos1, pos2):
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        if is_diagonals_allowed:
            return max(dx, dy)
        else:
            return dx + dy

    def find_shortest_path(start, goal):
        from heapq import heappush, heappop
        heap = []
        heappush(heap, (0, start, []))
        visited = set()
        while heap:
            cost, current, path = heappop(heap)
            if current == goal:
                return path
            if current in visited:
                continue
            visited.add(current)
            for neighbor_pos, move in get_neighbors(current):
                if neighbor_pos not in visited:
                    heappush(heap, (cost + 1, neighbor_pos, path + [move]))
        return None  # No path found

    def plan_path_to_collect(current_position, actions_remaining, energy_carried):
        # The state is represented as (position, energy_collected, actions_used, path)
        from heapq import heappush, heappop

        heap = []
        visited = set()
        initial_state = (0, current_position, 0, 0, [])
        heappush(heap, initial_state)

        while heap:
            priority, pos, energy_collected, actions_used, path = heappop(heap)
            state_id = (pos, energy_collected)
            if state_id in visited:
                continue
            visited.add(state_id)

            # Estimate actions needed to return to start
            steps_to_start = heuristic_distance(pos, start_pos)
            total_actions_needed = actions_used + steps_to_start + 1  # +1 for 'DROP' action

            if total_actions_needed > actions_remaining:
                continue

            if energy_collected >= carry_limit:
                # Return path to current position
                path_to_start = find_shortest_path(pos, start_pos)
                if path_to_start is None:
                    continue
                full_path = path + path_to_start + ['DROP']
                return full_path

            if grid_dict.get(pos) == 'E':
                # Take the energy
                new_energy_collected = energy_collected + 1
                new_actions_used = actions_used + 1  # 'TAKE'
                new_priority = new_actions_used + heuristic_distance(pos, start_pos)
                new_path = path + ['TAKE']
                # Temporarily remove energy from grid_dict
                grid_dict[pos] = ' '
                heappush(heap, (new_priority, pos, new_energy_collected, new_actions_used, new_path))
                # Restore energy for other paths
                grid_dict[pos] = 'E'

            for neighbor_pos, move in get_neighbors(pos):
                if neighbor_pos not in visited:
                    new_actions_used = actions_used + 1  # Move action
                    new_priority = new_actions_used + heuristic_distance(neighbor_pos, start_pos)
                    new_path = path + [move]
                    heappush(heap, (new_priority, neighbor_pos, energy_collected, new_actions_used, new_path))
        return None

    actions = []
    current_position = start_pos
    actions_remaining = max_actions
    energy_carried = 0

    while actions_remaining > 0:
        plan = plan_path_to_collect(current_position, actions_remaining, energy_carried)
        if plan is None:
            if current_position != start_pos:
                # Return to start position
                path_to_start = find_shortest_path(current_position, start_pos)
                if path_to_start is None:
                    break
                for move in path_to_start:
                    if actions_remaining <= 0:
                        break
                    actions.append(move)
                    current_position = (
                        current_position[0] + DIRECTIONS[move][0],
                        current_position[1] + DIRECTIONS[move][1]
                    )
                    actions_remaining -= 1
                # Drop any carried energy at start position
                if energy_carried > 0 and actions_remaining > 0:
                    actions.append('DROP')
                    actions_remaining -= 1
                    energy_carried = 0
            break
        # Execute the planned path
        for action in plan:
            if actions_remaining <= 0:
                break
            if action in DIRECTIONS:
                actions.append(action)
                current_position = (
                    current_position[0] + DIRECTIONS[action][0],
                    current_position[1] + DIRECTIONS[action][1]
                )
                actions_remaining -= 1
            elif action == 'TAKE':
                actions.append('TAKE')
                grid_dict[current_position] = ' '  # Remove energy from grid
                energy_carried += 1
                actions_remaining -= 1
            elif action == 'DROP':
                actions.append('DROP')
                energy_carried = 0
                actions_remaining -= 1
        if energy_carried == 0 and current_position == start_pos:
            continue
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