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

def solve_grid(grid, max_actions, token_capacity, diagonals_allowed):
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
    tokens_in_hand = 0

    allowed_moves = getAllowedMoves(diagonals_allowed)

    # Gather all token locations from the grid (cells with 'E')
    token_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 'E':
                token_locations.append((r, c))
    collected_tokens = set()

    while actions_taken < max_actions:
        # If at starting cell and carrying tokens, drop them
        if current_cell == starting_cell and tokens_in_hand > 0:
            actions.append("DROP")
            actions_taken += 1
            tokens_in_hand = 0

        # Choose the nearest token (not yet collected) that can be reached and returned
        best_token = None
        best_path = None
        min_total_cost = float('inf')

        for token in token_locations:
            if token in collected_tokens:
                continue
            path_to_token = getShortestPath(current_cell, token, grid, allowed_moves)
            path_token_to_start = getShortestPath(token, starting_cell, grid, allowed_moves)
            if path_to_token is None or path_token_to_start is None:
                continue  # Token unreachable or no safe return path
            # Total cost: moves to token + TAKE (1) + moves back + DROP (1)
            total_cost = len(path_to_token) + 1 + len(path_token_to_start) + 1
            if total_cost < min_total_cost:
                min_total_cost = total_cost
                best_token = token
                best_path = path_to_token

        # If no token can be collected within remaining actions, break out.
        if best_token is None or (actions_taken + min_total_cost) > max_actions:
            break

        # Move along the best path toward the selected token
        for move in best_path:
            if actions_taken >= max_actions:
                break
            actions.append(move)
            current_cell = updatePosition(current_cell, move, allowed_moves)
            actions_taken += 1

        if actions_taken >= max_actions:
            break

        # Collect the token
        actions.append("TAKE")
        tokens_in_hand += 1
        actions_taken += 1
        collected_tokens.add(best_token)
        # Update the grid to simulate token collection
        r, c = best_token
        grid[r][c] = " "

        # If token capacity is reached, return to starting cell to drop tokens.
        if tokens_in_hand == token_capacity:
            path_to_start = getShortestPath(current_cell, starting_cell, grid, allowed_moves)
            if path_to_start is None or (actions_taken + len(path_to_start) + 1) > max_actions:
                break
            for move in path_to_start:
                if actions_taken >= max_actions:
                    break
                actions.append(move)
                current_cell = updatePosition(current_cell, move, allowed_moves)
                actions_taken += 1
            if actions_taken < max_actions:
                actions.append("DROP")
                actions_taken += 1
                tokens_in_hand = 0

    # Endgame: If still carrying tokens and not at the starting cell, return and drop them.
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
    actions = solve_grid(grid, max_actions, carry_limit, diagonals_allowed=(movement_type == "eight"))
    return actions

def print_actions(actions):
    print("Actions taken:")
    for action in actions:
        print(action)

if __name__ == "__main__":
    # Sample grid as provided in the pseudocode
    grid = [
        [" ", " ", "E", "E", "E", "E", " ", "E", "E", "E", "E"],
        [" ", " ", "E", "E", "E", " ", " ", " ", " ", "E", " "],
        ["E", " ", " ", " ", "E", " ", " ", "E", "E", " ", " "],
        ["E", "E", "E", "E", " ", "E", "E", "E", " ", "E", "E"],
        [" ", "E", " ", "A", "E", " ", "E", " ", "E", "E", " "],
        ["E", " ", "E", " ", "E", "E", " ", "E", " ", "E", " "],
        ["E", " ", "E", " ", " ", " ", " ", "E", "E", "E", "E"],
        ["E", "E", " ", " ", " ", " ", "E", " ", "E", "E", " "],
        ["E", " ", "E", "E", "E", " ", " ", " ", "E", "E", " "],
        [" ", " ", "E", "E", "E", " ", "E", " ", " ", " ", " "],
        [" ", "E", "E", " ", "E", "E", " ", "E", " ", "E", "E"]
    ]
    
    max_actions = 20       # Maximum number of allowed actions
    token_capacity = 3     # Maximum number of tokens that can be carried at once
    
    actions = solve_grid(grid, max_actions, token_capacity, diagonals_allowed=False)
    print_actions(actions)
