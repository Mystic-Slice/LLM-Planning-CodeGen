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

def plan_multi_token_trip(starting_cell, grid, allowed_moves, remaining_actions, token_capacity, collected_tokens, token_locations):
    """
    Starting at starting_cell, try to build a round-trip plan that picks up several tokens (up to token_capacity)
    and eventually returns to the starting_cell (to eventually DROP tokens).
    The function returns a list of planned actions (moves, TAKE, and final DROP) if a round trip is found within
    remaining_actions; otherwise, it returns an empty list.
    The planning proceeds by always considering the next best token from the current position,
    allowing the agent to collect multiple tokens before returning home.
    """
    plan = []
    current = starting_cell
    tokens_taken = 0
    actions_used = 0  # Actions used so far
    # Function to compute cost to return from cell to starting cell
    def cost_to_return(cell):
        path = getShortestPath(cell, starting_cell, grid, allowed_moves)
        return len(path) if path is not None else float('inf')
    while tokens_taken < token_capacity:
        # Estimate cost to return home from current position
        return_cost = cost_to_return(current)
        if return_cost == float('inf'):
            # Cannot return home
            break
        # Available actions for moving and taking tokens
        available_actions = remaining_actions - actions_used - return_cost - 1  # +1 for DROP
        if available_actions <= 0:
            break
        # Find the best next token to collect from current position
        min_total_cost = float('inf')
        best_token = None
        best_path_to_token = None
        for token in token_locations:
            if token in collected_tokens:
                continue
            path_to_token = getShortestPath(current, token, grid, allowed_moves)
            if path_to_token is None:
                continue
            cost_to_token = len(path_to_token)
            # Cost to return home from the token
            return_cost_from_token = cost_to_return(token)
            if return_cost_from_token == float('inf'):
                continue
            # Total actions if we go to token, take it, and return home
            total_cost = actions_used + cost_to_token + 1 + return_cost_from_token + 1  # +1 for TAKE, +1 for DROP
            if total_cost <= remaining_actions and total_cost < min_total_cost:
                min_total_cost = total_cost
                best_token = token
                best_path_to_token = path_to_token
        if best_token is None:
            # Cannot collect any more tokens within remaining actions
            break
        # Move to the best token
        for move in best_path_to_token:
            plan.append(move)
            current = updatePosition(current, move, allowed_moves)
            actions_used += 1
        # Take the token
        plan.append("TAKE")
        tokens_taken += 1
        collected_tokens.add(best_token)
        actions_used += 1
        grid[best_token[0]][best_token[1]] = " "
    # Return home
    path_back = getShortestPath(current, starting_cell, grid, allowed_moves)
    if path_back is None:
        return []
    for move in path_back:
        plan.append(move)
        actions_used += 1
    # Drop tokens
    plan.append("DROP")
    actions_used += 1
    if actions_used > remaining_actions:
        return []
    return plan

def solve_grid(grid, start_pos, token_capacity, cost_per_step, diagonals_allowed, max_actions=20):
    """
    Given a grid, a maximum number of actions, token capacity,
    and whether diagonal moves are allowed,
    returns a list of actions (moves, TAKE, and DROP) that collects energy tokens
    and drops them at the starting cell.
    """
    actions = []
    rows = len(grid)
    cols = len(grid[0])
    starting_cell = None
    # Locate the starting cell (where the agent 'A' is placed)
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
    tokens_in_hand = 0  # tokens currently held; note: when dropped they add to starting cell score
    allowed_moves = getAllowedMoves(diagonals_allowed)
    # Gather all token locations from the grid (cells with 'E')
    token_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 'E':
                token_locations.append((r, c))
    collected_tokens = set()  # tokens that have already been collected
    # Main loop: while we have actions left, try to plan a multi-token round trip.
    while actions_taken < max_actions:
        # If not at starting cell, try to return.
        if current_cell != starting_cell:
            path_to_start = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
            if path_to_start is None or (actions_taken + len(path_to_start) + 1) > max_actions:
                break
            for move in path_to_start:
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            # When home, drop tokens if any.
            if tokens_in_hand > 0 and actions_taken < max_actions:
                actions.append("DROP")
                actions_taken += 1
                tokens_in_hand = 0
        # Now the agent is at the starting cell. Attempt to plan a round trip to collect several tokens.
        remaining = max_actions - actions_taken
        round_trip = plan_multi_token_trip(starting_cell, grid, allowed_moves, remaining, token_capacity, collected_tokens, token_locations)
        # If no planned round trip is found, break.
        if not round_trip:
            break
        # Perform the round trip.
        for act in round_trip:
            # Before executing move we check for bounds etc. (getShortestPath ensures validity)
            actions.append(act)
            actions_taken += 1
            if act in allowed_moves:
                current_cell = updatePosition(current_cell, act, allowed_moves)
            elif act == "TAKE":
                tokens_in_hand += 1
            elif act == "DROP":
                tokens_in_hand = 0
            if actions_taken >= max_actions:
                break
        # If after the round trip we are no longer at start, try to return.
        if current_cell != starting_cell and actions_taken < max_actions:
            path_to_start = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
            if path_to_start is None or (actions_taken + len(path_to_start) + 1) > max_actions:
                break
            for move in path_to_start:
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            if tokens_in_hand > 0 and actions_taken < max_actions:
                actions.append("DROP")
                actions_taken += 1
                tokens_in_hand = 0
    # Endgame: if there are still tokens in hand and we have actions to return, return to starting cell and drop.
    if tokens_in_hand > 0 and current_cell != starting_cell:
        path_to_start = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
        if path_to_start is not None and (actions_taken + len(path_to_start) + 1) <= max_actions:
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