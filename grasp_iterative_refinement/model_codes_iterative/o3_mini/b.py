import collections

def getAllowedMoves(diagonals_allowed):
    """
    Returns a dictionary of allowed moves.
    Cardinal directions are always allowed.
    Diagonal moves are added only if diagonals_allowed is True.
    """
    moves = {
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
        "UP": (-1, 0),
        "DOWN": (1, 0)
    }
    if diagonals_allowed:
        moves.update({
            "UPLEFT": (-1, -1),
            "UPRIGHT": (-1, 1),
            "DOWNLEFT": (1, -1),
            "DOWNRIGHT": (1, 1)
        })
    return moves

def isValid(cell, grid):
    """Return True if cell is within grid bounds and not an obstacle ('O')."""
    rows = len(grid)
    cols = len(grid[0])
    r, c = cell
    if r < 0 or r >= rows or c < 0 or c >= cols:
        return False
    if grid[r][c] == 'O':  # Obstacle check
        return False
    return True

def updatePosition(cell, move, allowed_moves):
    """Return new cell coordinates after applying the move."""
    dr, dc = allowed_moves[move]
    return (cell[0] + dr, cell[1] + dc)

def getShortestPath(start, goal, grid, allowed_moves):
    """
    Use BFS to compute the shortest path from start to goal.
    Returns a list of moves (e.g., "UP", "DOWNLEFT", etc.) or None if no path exists.
    Note: The grid cell contents (like 'E') do not block movement.
    """
    queue = collections.deque()
    queue.append((start, []))
    visited = set([start])
    while queue:
        current, path = queue.popleft()
        if current == goal:
            return path
        for move, (dr, dc) in allowed_moves.items():
            next_cell = (current[0] + dr, current[1] + dc)
            if isValid(next_cell, grid) and next_cell not in visited:
                visited.add(next_cell)
                queue.append((next_cell, path + [move]))
    return None

def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions=20):
    """
    Revised strategy:
    
    – First, find the starting cell ('A').
    – Gather the list of token cells (cells marked 'E').
    – While there are actions remaining, the agent greedily tries to add nearby tokens 
      as long as:
        (a) The number of moves to go there then return home fits in the remaining actions,
        (b) And the “profit” is positive, i.e. the energy tokens gained (1 per token)
            exceeds the energy cost incurred by extra moving.
    – When no “profitable” move is available (or the agent has reached its token_capacity)
      the agent returns to home to “DROP” collected tokens.
      
    This approach “chains” collections when tokens lie in clusters. It also uses the cost_per_step
    to help decide whether it is worth moving to a token.
    
    (Note: if cost_per_step is zero the algorithm reverts to a greedy approximation to collect as many tokens as possible.)
    """
    actions = []
    rows = len(grid)
    cols = len(grid[0])
    starting_cell = None
    # Locate starting cell where 'A' appears.
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 'A':
                starting_cell = (r, c)
                break
        if starting_cell is not None:
            break
            
    if starting_cell is None:
        print("No starting cell found.")
        return actions

    current_cell = starting_cell
    actions_taken = 0
    tokens_in_hand = 0
    allowed_moves = getAllowedMoves(is_diagonals_allowed)
    
    # Build a set of tokens from the grid.
    token_locations = set()
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 'E':
                token_locations.add((r, c))
                
    # Helper to check if we have enough remaining actions to complete the route:
    def canCompleteRoute(path_to, path_back, extra_actions=0):
        # extra_actions additional actions needed (like for DROP or TAKE)
        return (actions_taken + len(path_to) + len(path_back) + extra_actions) <= max_actions

    # Main loop: try to pick up tokens then eventually return home.
    while actions_taken < max_actions:
        # If we are at starting_cell and have tokens, drop them.
        if current_cell == starting_cell and tokens_in_hand > 0:
            actions.append("DROP")
            actions_taken += 1
            tokens_in_hand = 0
        
        # Try to see if there is any token at current cell.
        if current_cell in token_locations:
            # Immediately "take" the token.
            if actions_taken + 1 <= max_actions:
                actions.append("TAKE")
                tokens_in_hand += 1
                actions_taken += 1
                token_locations.remove(current_cell)
                grid[current_cell[0]][current_cell[1]] = " "  # update grid
            else:
                break
        
        # If carry capacity is not reached and tokens still exist,
        # try to find the nearest reachable token that is “profitable”.
        candidate_token = None
        candidate_path = None
        candidate_return = None
        best_total_moves = None
        
        for token in list(token_locations):
            # Compute path from current to token.
            path_to_token = getShortestPath(current_cell, token, grid, allowed_moves)
            if path_to_token is None:
                continue
            # Compute path from token back to starting cell.
            path_back = getShortestPath(token, starting_cell, grid, allowed_moves)
            if path_back is None:
                continue
            
            total_moves = len(path_to_token) + len(path_back)
            # Check that after including TAKE (1) and later DROP (1) we have enough actions.
            if not canCompleteRoute(path_to_token, path_back, extra_actions=2):
                continue
            
            # Use cost_per_step to “prune” moves that are not worth it.
            # Each token collected gives 1 energy. If (total_moves * cost_per_step) >= 1 then
            # the token wouldn’t be profitable.
            if cost_per_step > 0 and (total_moves * cost_per_step) >= 1:
                continue

            # Choose the token with the smallest total moves (greedy: “closest food”).
            if best_total_moves is None or total_moves < best_total_moves:
                best_total_moves = total_moves
                candidate_token = token
                candidate_path = path_to_token
                candidate_return = path_back

        # If we found a candidate token and we still have room to carry more tokens then go get it.
        if candidate_token is not None and tokens_in_hand < carry_limit:
            # Follow the path to candidate token.
            for move in candidate_path:
                if actions_taken >= max_actions:
                    break
                # Move and update current_cell.
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            # Safety check: if now standing on a token, perform TAKE.
            if current_cell in token_locations:
                if actions_taken < max_actions:
                    actions.append("TAKE")
                    tokens_in_hand += 1
                    actions_taken += 1
                    token_locations.remove(current_cell)
                    grid[current_cell[0]][current_cell[1]] = " "
            continue
        
        # Otherwise, either no candidate is reachable or capacity is full.
        # In either case we try to return to starting cell (if not already there)
        if current_cell != starting_cell:
            path_to_start = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
            if path_to_start is None or (actions_taken + len(path_to_start) + 1) > max_actions:
                break
            for move in path_to_start:
                if actions_taken >= max_actions:
                    break
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            if current_cell == starting_cell and tokens_in_hand > 0 and actions_taken < max_actions:
                actions.append("DROP")
                actions_taken += 1
                tokens_in_hand = 0
        else:
            # At home with no profitable token to collect.
            break

    # Endgame: if there are tokens held and we can still drop them, try to return home.
    if tokens_in_hand > 0 and current_cell != starting_cell:
        path_to_start = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
        if path_to_start and (actions_taken + len(path_to_start) + 1) <= max_actions:
            for move in path_to_start:
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            actions.append("DROP")
            actions_taken += 1
            tokens_in_hand = 0

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