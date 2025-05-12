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

def solve_grid(grid, start_pos=None, carry_limit=5, cost_per_step=0.1, is_diagonals_allowed=False, max_actions=50):
    """
    Revised strategy:
    – First, locate the starting cell (the one with 'A'). If a start_pos is given, use that.
    – Build the set of token cells (cells marked 'E').
    – In the main loop, first if you are on a token cell, take it; then scan your immediate neighbors.
    – Otherwise, evaluate all candidate token positions using a cluster bonus: for each token, count how many tokens
      lie within Manhattan distance 2 (including itself) from that candidate. Then compute a net gain:
           net_gain = (1 + cluster_bonus) - (steps_to_candidate + steps_from_candidate_to_home)*cost_per_step.
    – If a candidate’s net gain is positive and there is capacity, plan a route to the candidate.
    – Once no “profitable” move exists (or you reach your carry limit), return to the starting cell and DROP.
    – At all times, ensure that the complete planned route (plus any required TAKE/DROP actions) fits in max_actions.
    """
    actions = []
    rows = len(grid)
    cols = len(grid[0])
    
    # Locate starting cell.
    starting_cell = None
    if start_pos is not None:
        starting_cell = start_pos
    else:
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 'A':
                    starting_cell = (r, c)
                    break
            if starting_cell is not None:
                break
    if starting_cell is None:
        # No starting cell found.
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
    
    # A helper to check if we have enough remaining actions to complete the route.
    def canCompleteRoute(path_to, path_back, extra_actions=0):
        return (actions_taken + len(path_to) + len(path_back) + extra_actions) <= max_actions

    # Given a cell, count tokens in token_locations within Manhattan distance <= radius.
    def cluster_count(cell, radius=2):
        count = 0
        for token in token_locations:
            if abs(token[0] - cell[0]) + abs(token[1] - cell[1]) <= radius:
                count += 1
        return count

    # Check immediate neighbors: if any neighbor cell (allowed move) has a token, try to grab it.
    def take_adjacent_tokens():
        nonlocal current_cell, actions_taken, tokens_in_hand
        found = True
        while found and tokens_in_hand < carry_limit and actions_taken < max_actions:
            found = False
            for move, (dr, dc) in allowed_moves.items():
                nxt = (current_cell[0] + dr, current_cell[1] + dc)
                if nxt in token_locations:
                    # Check feasibility: moving there, TAKE, and returning home.
                    path_to_nxt = [move]  # one step
                    path_home = getShortestPath(nxt, starting_cell, grid, allowed_moves)
                    if path_home is None:
                        continue
                    # Need one extra action for TAKE.
                    if (actions_taken + len(path_to_nxt) + 1 + len(path_home) + 1) > max_actions:
                        continue
                    # Do the move
                    actions.append(move)
                    current_cell = nxt
                    actions_taken += 1
                    # Take token
                    actions.append("TAKE")
                    tokens_in_hand += 1
                    actions_taken += 1
                    token_locations.remove(nxt)
                    grid[nxt[0]][nxt[1]] = " "  # update grid
                    found = True
                    break  # break out to re-scan from new current_cell

    # Main loop: try to pick up tokens then eventually return home.
    while actions_taken < max_actions:
        # If we are at starting_cell and have tokens, drop them.
        if current_cell == starting_cell and tokens_in_hand > 0:
            actions.append("DROP")
            actions_taken += 1
            tokens_in_hand = 0

        # If a token exists at the current cell, TAKE it.
        if current_cell in token_locations:
            if actions_taken < max_actions:
                actions.append("TAKE")
                tokens_in_hand += 1
                actions_taken += 1
                token_locations.remove(current_cell)
                grid[current_cell[0]][current_cell[1]] = " "
            continue

        # First, try to collect tokens on adjacent cells if possible.
        take_adjacent_tokens()
        # If after collecting adjacent tokens we filled capacity, return home.
        if tokens_in_hand >= carry_limit:
            if current_cell != starting_cell:
                path_home = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
                if path_home is None or not canCompleteRoute(path_home, [] , extra_actions=1):
                    break
                for move in path_home:
                    if actions_taken >= max_actions:
                        break
                    actions.append(move)
                    current_cell = updatePosition(current_cell, move, allowed_moves)
                    actions_taken += 1
                if actions_taken < max_actions:
                    actions.append("DROP")
                    actions_taken += 1
                    tokens_in_hand = 0
            continue

        # Now, evaluate candidate tokens among remaining ones.
        candidate_token = None
        candidate_path = None
        candidate_return = None
        best_total_moves = None
        best_net_gain = -10e9
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
            # Make sure that after including TAKE and eventual DROP we still are within max_actions.
            if not canCompleteRoute(path_to_token, path_back, extra_actions=2):
                continue
            bonus = cluster_count(token, radius=2) - 1  # bonus counts extra tokens near token
            # Compute net gain: the token itself gives +1 and bonus tokens add value, subtract cost.
            net_gain = (1 + bonus) - (total_moves * cost_per_step)
            if net_gain > best_net_gain:
                best_net_gain = net_gain
                candidate_token = token
                candidate_path = path_to_token
                candidate_return = path_back
                best_total_moves = total_moves
        # Proceed if a candidate with positive net_gain is found.
        if candidate_token is not None and best_net_gain > 0:
            # Follow the candidate path
            for move in candidate_path:
                if actions_taken >= max_actions:
                    break
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
                # If along the way we see a token at the new cell, TAKE it.
                if current_cell in token_locations and tokens_in_hand < carry_limit:
                    if actions_taken < max_actions:
                        actions.append("TAKE")
                        tokens_in_hand += 1
                        actions_taken += 1
                        token_locations.remove(current_cell)
                        grid[current_cell[0]][current_cell[1]] = " "
                    # Also try to grab tokens adjacent
                    take_adjacent_tokens()
            # After reaching the candidate token, if not already taken, take it.
            if current_cell in token_locations and actions_taken < max_actions and tokens_in_hand < carry_limit:
                actions.append("TAKE")
                tokens_in_hand += 1
                actions_taken += 1
                token_locations.remove(current_cell)
                grid[current_cell[0]][current_cell[1]] = " "
            continue

        # If no candidate is worthwhile or capacity full, return home.
        if current_cell != starting_cell:
            path_home = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
            if path_home is None or (actions_taken + len(path_home) + 1) > max_actions:
                break
            for move in path_home:
                if actions_taken >= max_actions:
                    break
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            # Once home, if carrying tokens, drop them.
            if current_cell == starting_cell and tokens_in_hand > 0 and actions_taken < max_actions:
                actions.append("DROP")
                actions_taken += 1
                tokens_in_hand = 0
        else:
            # At home with nothing worthwhile – break.
            break

    # Endgame: if tokens remain and we have time, try to return home and DROP.
    if tokens_in_hand > 0 and current_cell != starting_cell:
        path_home = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
        if path_home and (actions_taken + len(path_home) + 1) <= max_actions:
            for move in path_home:
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