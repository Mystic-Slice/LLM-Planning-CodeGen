import collections

def solve_grid(grid, start_position, max_actions, carry_limit, cost_per_step, is_diagonals_allowed=False):
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    tokens_set = set()
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 'E':
                tokens_set.add((i, j))
    
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
    
    INF = 10**9
    dist_to_start = [[INF] * cols for _ in range(rows)]
    queue = collections.deque()
    sr, sc = start_position
    if grid[sr][sc] != 'O':
        dist_to_start[sr][sc] = 0
        queue.append((sr, sc))
    while queue:
        r, c = queue.popleft()
        for move_name, (dx, dy) in move_directions:
            nr, nc = r + dx, c + dy
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 'O':
                if dist_to_start[nr][nc] > dist_to_start[r][c] + 1:
                    dist_to_start[nr][nc] = dist_to_start[r][c] + 1
                    queue.append((nr, nc))
    
    tokens_set = { token for token in tokens_set 
                  if dist_to_start[token[0]][token[1]] < INF and 
                  dist_to_start[token[0]][token[1]] * cost_per_step < 1 }
    
    current = start_position
    carried = 0
    actions = []
    remaining_actions = max_actions
    
    while remaining_actions > 0:
        if current == start_position and carried > 0:
            actions.append("DROP")
            carried = 0
            remaining_actions -= 1
            continue
            
        if carried == carry_limit or (not tokens_set and carried > 0):
            r, c = current
            current_dist = dist_to_start[r][c]
            best_move = None
            for move_name, (dx, dy) in move_directions:
                nr = r + dx
                nc = c + dy
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 'O':
                    if dist_to_start[nr][nc] == current_dist - 1:
                        best_move = move_name
                        break
            if best_move is None:
                break
            actions.append(best_move)
            remaining_actions -= 1
            current = (nr, nc)
            continue
            
        if not tokens_set and carried == 0:
            break
            
        if current in tokens_set:
            d2 = dist_to_start[current[0]][current[1]]
            net_gain = 1 - d2 * cost_per_step
            if net_gain > 0 and (d2 + 1) <= remaining_actions:
                actions.append("TAKE")
                tokens_set.remove(current)
                carried += 1
                remaining_actions -= 1
                continue
            else:
                tokens_set.remove(current)
                continue
                
        dist_from_current = [[INF] * cols for _ in range(rows)]
        parent_map = {}
        queue_bfs = collections.deque()
        r_cur, c_cur = current
        dist_from_current[r_cur][c_cur] = 0
        queue_bfs.append((r_cur, c_cur))
        parent_map[(r_cur, c_cur)] = None
        while queue_bfs:
            r, c = queue_bfs.popleft()
            for move_name, (dx, dy) in move_directions:
                nr = r + dx
                nc = c + dy
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 'O':
                    if dist_from_current[nr][nc] > dist_from_current[r][c] + 1:
                        dist_from_current[nr][nc] = dist_from_current[r][c] + 1
                        parent_map[(nr, nc)] = (r, c)
                        queue_bfs.append((nr, nc))
        
        candidate = None
        best_total = INF
        for token in tokens_set:
            tr, tc = token
            if dist_from_current[tr][tc] == INF:
                continue
            total_steps = dist_from_current[tr][tc] + dist_to_start[tr][tc]
            net_gain = 1 - total_steps * cost_per_step
            if net_gain > 0 and (total_steps + 1) <= remaining_actions:
                if total_steps < best_total:
                    best_total = total_steps
                    candidate = token
        
        if candidate is None:
            if carried > 0:
                r, c = current
                current_dist = dist_to_start[r][c]
                best_move = None
                for move_name, (dx, dy) in move_directions:
                    nr = r + dx
                    nc = c + dy
                    if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 'O':
                        if dist_to_start[nr][nc] == current_dist - 1:
                            best_move = move_name
                            break
                if best_move is None:
                    break
                actions.append(best_move)
                remaining_actions -= 1
                current = (nr, nc)
                continue
            else:
                break
                
        path_node = candidate
        while parent_map.get(path_node) != current and parent_map.get(path_node) is not None:
            path_node = parent_map[path_node]
        if parent_map.get(path_node) != current:
            break
        
        next_node = path_node
        dr = next_node[0] - current[0]
        dc = next_node[1] - current[1]
        move_dir = None
        if dr == -1 and dc == -1: move_dir = "UPLEFT"
        elif dr == -1 and dc == 0: move_dir = "UP"
        elif dr == -1 and dc == 1: move_dir = "UPRIGHT"
        elif dr == 0 and dc == -1: move_dir = "LEFT"
        elif dr == 0 and dc == 1: move_dir = "RIGHT"
        elif dr == 1 and dc == -1: move_dir = "DOWNLEFT"
        elif dr == 1 and dc == 0: move_dir = "DOWN"
        elif dr == 1 and dc == 1: move_dir = "DOWNRIGHT"
        else:
            break
        
        actions.append(move_dir)
        remaining_actions -= 1
        current = next_node
        
        if current in tokens_set:
            d2 = dist_to_start[current[0]][current[1]]
            net_gain = 1 - d2 * cost_per_step
            if net_gain > 0 and (d2 + 1) <= remaining_actions:
                actions.append("TAKE")
                tokens_set.remove(current)
                carried += 1
                remaining_actions -= 1
    
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
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == "eight"), carry_limit, cost_per_step)
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