def manhattan(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def chebyshev(pos1, pos2):
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))

def solve_grid(grid, start_position, max_actions, carry_limit, cost_per_step, is_diagonals_allowed=False):
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    tokens_set = set()
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 'E':
                tokens_set.add((i, j))
    
    current = start_position
    carried = 0
    actions = []
    remaining_actions = max_actions
    
    distance_metric = chebyshev if is_diagonals_allowed else manhattan
    
    tokens_net_info = {}
    for token in tokens_set:
        d2 = distance_metric(token, start_position)
        tokens_net_info[token] = d2
    
    move_directions = []
    if is_diagonals_allowed:
        move_directions.extend([
            ("UPLEFT", (-1, -1)),
            ("UPRIGHT", (-1, 1)),
            ("DOWNLEFT", (1, -1)),
            ("DOWNRIGHT", (1, 1))
        ])
    move_directions.extend([
        ("UP", (-1, 0)),
        ("DOWN", (1, 0)),
        ("LEFT", (0, -1)),
        ("RIGHT", (0, 1))
    ])
    
    def get_next_move(cur, goal):
        min_dist = float('inf')
        best_move = None
        for move_name, (dx, dy) in move_directions:
            nr = cur[0] + dx
            nc = cur[1] + dy
            if 0 <= nr < rows and 0 <= nc < cols:
                new_pos = (nr, nc)
                d = distance_metric(new_pos, goal)
                if d < min_dist:
                    min_dist = d
                    best_move = move_name
        return best_move
    
    while remaining_actions > 0:
        if current == start_position and carried > 0:
            actions.append("DROP")
            carried = 0
            remaining_actions -= 1
            continue
            
        if carried == carry_limit:
            move = get_next_move(current, start_position)
            if move is None:
                break
            dx, dy = 0, 0
            for name, (dxx, dyy) in move_directions:
                if name == move:
                    dx, dy = dxx, dyy
                    break
            new_r = current[0] + dx
            new_c = current[1] + dy
            if new_r < 0 or new_r >= rows or new_c < 0 or new_c >= cols:
                break
            actions.append(move)
            remaining_actions -= 1
            current = (new_r, new_c)
            continue
            
        if not tokens_set:
            if carried > 0:
                move = get_next_move(current, start_position)
                if move is None:
                    break
                dx, dy = 0, 0
                for name, (dxx, dyy) in move_directions:
                    if name == move:
                        dx, dy = dxx, dyy
                        break
                new_r = current[0] + dx
                new_c = current[1] + dy
                if new_r < 0 or new_r >= rows or new_c < 0 or new_c >= cols:
                    break
                actions.append(move)
                remaining_actions -= 1
                current = (new_r, new_c)
                continue
            else:
                break
                
        if current in tokens_set:
            token_here = current
            d2 = tokens_net_info[token_here]
            net_gain = 1 - d2 * cost_per_step
            if net_gain > 0 and (1 + d2) <= remaining_actions:
                actions.append("TAKE")
                tokens_set.remove(token_here)
                carried += 1
                remaining_actions -= 1
                continue
            else:
                tokens_set.remove(token_here)
                continue
                
        candidate = None
        min_total_movement = float('inf')
        for token in tokens_set:
            d1 = distance_metric(current, token)
            d2 = tokens_net_info[token]
            total_movement = d1 + d2
            net_gain = 1 - total_movement * cost_per_step
            if net_gain <= 0:
                continue
            if total_movement + 1 > remaining_actions:
                continue
            if total_movement < min_total_movement:
                min_total_movement = total_movement
                candidate = token
                
        if candidate is None:
            if carried > 0:
                move = get_next_move(current, start_position)
                if move is None:
                    break
                dx, dy = 0, 0
                for name, (dxx, dyy) in move_directions:
                    if name == move:
                        dx, dy = dxx, dyy
                        break
                new_r = current[0] + dx
                new_c = current[1] + dy
                if new_r < 0 or new_r >= rows or new_c < 0 or new_c >= cols:
                    break
                actions.append(move)
                remaining_actions -= 1
                current = (new_r, new_c)
                continue
            else:
                break
                
        move = get_next_move(current, candidate)
        if move is None:
            break
            
        dx, dy = 0, 0
        for name, (dxx, dyy) in move_directions:
            if name == move:
                dx, dy = dxx, dyy
                break
        new_r = current[0] + dx
        new_c = current[1] + dy
        if new_r < 0 or new_r >= rows or new_c < 0 or new_c >= cols:
            break
            
        actions.append(move)
        remaining_actions -= 1
        current = (new_r, new_c)
        
    if current == start_position and carried > 0 and remaining_actions > 0:
        actions.append("DROP")
        carried = 0
        remaining_actions -= 1
        
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
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == 'eight'), carry_limit, cost_per_step)
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
    actions = solve_grid(sample_grid, start_position, 20, diagonals_allowed, carry_limit, cost_per_step)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()