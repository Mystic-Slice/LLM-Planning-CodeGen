from collections import deque

def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions):
    rows = len(grid)
    if rows == 0:
        return []
    cols = len(grid[0])
    
    tokens_initial = []
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 'E':
                tokens_initial.append((i, j))
    
    if is_diagonals_allowed:
        directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]
        direction_names = {(0,1): 'RIGHT', (1,0): 'DOWN', (0,-1): 'LEFT', (-1,0): 'UP',
                         (1,1): 'DOWNRIGHT', (-1,-1): 'UPLEFT', (1,-1): 'DOWNLEFT', (-1,1): 'UPRIGHT'}
    else:
        directions = [(0,1), (1,0), (0,-1), (-1,0)]
        direction_names = {(0,1): 'RIGHT', (1,0): 'DOWN', (0,-1): 'LEFT', (-1,0): 'UP'}
    
    nodes = [start_pos] + tokens_initial
    dist_map = {}
    
    for node in nodes:
        dist_from_node = {}
        q = deque()
        dist_from_node[node] = 0
        q.append(node)
        while q:
            x, y = q.popleft()
            current_dist = dist_from_node[(x, y)]
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols:
                    if grid[nx][ny] == 'O':
                        continue
                    if (nx, ny) not in dist_from_node:
                        dist_from_node[(nx, ny)] = current_dist + 1
                        q.append((nx, ny))
        for other in nodes:
            if other in dist_from_node:
                dist_map[(node, other)] = dist_from_node[other]
            else:
                dist_map[(node, other)] = float('inf')
    
    available_tokens = set(tokens_initial)
    actions_list = []
    remaining_actions = max_actions
    
    def get_path_sequence(start, end):
        if start == end:
            return []
        visited = set()
        parent = {}
        q = deque()
        q.append(start)
        visited.add(start)
        parent[start] = None
        
        found = False
        while q:
            x, y = q.popleft()
            if (x, y) == end:
                found = True
                break
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < rows and 0 <= ny < cols:
                    if grid[nx][ny] == 'O':
                        continue
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        action_taken = direction_names[(dx, dy)]
                        parent[(nx, ny)] = (x, y, action_taken)
                        q.append((nx, ny))
        if not found:
            return []
        
        path_actions = []
        current = end
        while parent[current] is not None:
            x_prev, y_prev, action_name = parent[current]
            path_actions.append(action_name)
            current = (x_prev, y_prev)
        path_actions.reverse()
        return path_actions
    
    while remaining_actions > 0 and available_tokens:
        base_token = None
        min_round_trip = float('inf')
        for token in available_tokens:
            d1 = dist_map.get((start_pos, token), float('inf'))
            d2 = dist_map.get((token, start_pos), float('inf'))
            round_trip = d1 + d2
            if round_trip < min_round_trip:
                min_round_trip = round_trip
                base_token = token
        if base_token is None:
            break
        base_net_energy = 1 - min_round_trip * cost_per_step
        base_trip_actions = min_round_trip + 2
        if base_net_energy <= 0 or base_trip_actions > remaining_actions:
            break
        tokens_in_trip = [base_token]
        candidate_set = available_tokens - {base_token}
        trip_nodes = [start_pos, base_token, start_pos]
        total_distance = min_round_trip
        while len(tokens_in_trip) < carry_limit and candidate_set:
            best_extra = float('inf')
            best_token_to_add = None
            best_insert_idx = None
            for token in candidate_set:
                for i in range(len(trip_nodes) - 1):
                    a = trip_nodes[i]
                    b = trip_nodes[i+1]
                    d_ab = dist_map.get((a, b), float('inf'))
                    d_a_token = dist_map.get((a, token), float('inf'))
                    d_token_b = dist_map.get((token, b), float('inf'))
                    if d_ab == float('inf') or d_a_token == float('inf') or d_token_b == float('inf'):
                        continue
                    extra_dist = d_a_token + d_token_b - d_ab
                    if extra_dist < best_extra:
                        best_extra = extra_dist
                        best_token_to_add = token
                        best_insert_idx = i
            if best_token_to_add is None:
                break
            new_total_distance = total_distance + best_extra
            new_num_tokens = len(tokens_in_trip) + 1
            net_energy = new_num_tokens - new_total_distance * cost_per_step
            total_trip_actions = new_total_distance + new_num_tokens + 1
            if net_energy > 0 and total_trip_actions <= remaining_actions:
                tokens_in_trip.append(best_token_to_add)
                candidate_set.remove(best_token_to_add)
                trip_nodes.insert(best_insert_idx+1, best_token_to_add)
                total_distance = new_total_distance
            else:
                break
        current_pos = start_pos
        trip_actions = []
        for i in range(1, len(trip_nodes)):
            next_node = trip_nodes[i]
            path = get_path_sequence(current_pos, next_node)
            trip_actions.extend(path)
            if next_node != start_pos:
                trip_actions.append('TAKE')
            current_pos = next_node
        trip_actions.append('DROP')
        if len(trip_actions) > remaining_actions:
            break
        actions_list.extend(trip_actions)
        remaining_actions -= len(trip_actions)
        available_tokens -= set(tokens_in_trip)
    return actions_list


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