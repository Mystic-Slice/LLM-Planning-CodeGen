from collections import deque
import math

def compute_shortest_path(start, end, movement_type, grid, obstacles=None):
    rows, cols = len(grid), len(grid[0])
    if obstacles is None:
        obstacles = set()
    directions = []
    if movement_type == "four":
        directions = [(-1, 0, "UP"), (1, 0, "DOWN"), (0, -1, "LEFT"), (0, 1, "RIGHT")]
    elif movement_type == "eight":
        directions = [
            (-1, 0, "UP"), (1, 0, "DOWN"), (0, -1, "LEFT"), (0, 1, "RIGHT"),
            (-1, -1, "UPLEFT"), (-1, 1, "UPRIGHT"), (1, -1, "DOWNLEFT"), (1, 1, "DOWNRIGHT")
        ]
    queue = deque()
    queue.append((start[0], start[1], []))
    visited = set()
    visited.add((start[0], start[1]))
    while queue:
        row, col, path = queue.popleft()
        if (row, col) == end:
            return path, len(path)
        for dr, dc, move in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < rows and 0 <= new_col < cols:
                if (new_row, new_col) not in visited and grid[new_row][new_col] != 'O':
                    visited.add((new_row, new_col))
                    queue.append((new_row, new_col, path + [move]))
    return None, math.inf

def solve_game(grid, movement_type, carry_limit, cost_per_step, max_actions):
    start_pos = None
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == 'A':
                start_pos = (i, j)
                break
        if start_pos:
            break
    if not start_pos:
        return []
    e_list = [(i, j) for i in range(len(grid)) for j in range(len(grid[i])) if grid[i][j] == 'E']
    valid_es = []
    for e in e_list:
        path_to, cost_to = compute_shortest_path(start_pos, e, movement_type, grid)
        path_back, cost_back = compute_shortest_path(e, start_pos, movement_type, grid)
        if path_to is not None and path_back is not None:
            valid_es.append((e, cost_to + cost_back))
    e_net = []
    for e, round_cost in valid_es:
        net = 1 - (round_cost * cost_per_step)
        if net > 0:
            e_net.append((e, round_cost, net))
    e_net_sorted = sorted(e_net, key=lambda x: (x[1], x[0]))
    sorted_es = [e for e, _, _ in e_net_sorted]
    remaining_actions = max_actions
    actions = []
    current_pos = start_pos
    collected = 0

    def find_best_group(es, max_group_size, start, max_cost):
        best = None
        best_net = -math.inf
        best_steps = math.inf
        max_group_size = min(max_group_size, len(es))
        path_cache = {}
        dp_table = {}

        def get_path(a, b):
            if (a, b) not in path_cache:
                path, cost = compute_shortest_path(a, b, movement_type, grid)
                path_cache[(a, b)] = (path, cost)
            return path_cache[(a, b)]

        for group_size in range(1, max_group_size + 1):
            for i in range(len(es) - group_size + 1):
                group = es[i:i+group_size]
                all_perms = [group]
                for perm in all_perms:
                    current = start
                    total_steps = 0
                    valid = True
                    for e in perm:
                        path, cost = get_path(current, e)
                        if path is None:
                            valid = False
                            break
                        total_steps += cost
                        current = e
                    if valid:
                        path_back, cost_back = get_path(current, start)
                        if path_back is None:
                            continue
                        total_steps += cost_back
                        actions_needed = total_steps + group_size + 1
                        net_gain = group_size - (total_steps) * cost_per_step
                        if net_gain <= 0:
                            continue
                        if actions_needed > max_cost:
                            continue
                        net_per_action = net_gain
                        if net_per_action > best_net or (net_per_action == best_net and total_steps < best_steps):
                            best = perm
                            best_net = net_per_action
                            best_steps = total_steps
                if best is not None:
                    break
            if best is not None:
                break
        if best is not None:
            total_actions_used = best_steps + len(best) + 1
            return best, total_actions_used, best_net
        return None, None, None

    while remaining_actions > 0 and sorted_es:
        best_group = None
        group_actions = math.inf
        best_net = -math.inf
        max_group_size = min(carry_limit, len(sorted_es))
        for group_size in range(max_group_size, 0, -1):
            group, actions_used, net = find_best_group(sorted_es, group_size, current_pos, remaining_actions)
            if group is not None and (net > best_net or (net == best_net and actions_used < group_actions)):
                best_group = group
                group_actions = actions_used
                best_net = net
                if net > 0:
                    break
        if best_group:
            temp_pos = current_pos
            path_log = []
            for e in best_group:
                path_to_e, _ = compute_shortest_path(temp_pos, e, movement_type, grid)
                path_log.extend(path_to_e)
                path_log.append("TAKE")
                temp_pos = e
            path_back, _ = compute_shortest_path(temp_pos, start_pos, movement_type, grid)
            path_log.extend(path_back)
            path_log.append("DROP")
            if len(path_log) > remaining_actions:
                continue
            remaining_actions -= len(path_log)
            actions.extend(path_log)
            collected += len(best_group)
            sorted_es = [e for e in sorted_es if e not in best_group]
            current_pos = start_pos
        else:
            break

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
    actions = solve_game(grid, movement_type, carry_limit, cost_per_step, max_actions)
    return actions

if __name__ == "__main__":
    # Example usage
    grid = [
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

    movement_type = "four"  # 4-direction movement
    carry_limit = 3    # Can carry up to 3 energy tokens at a time
    max_actions = 20   # Maximum number of actions

    actions = solve_game(grid, movement_type, carry_limit, 0.3, max_actions)
    print("Actions taken:", actions)
    print(len(actions))