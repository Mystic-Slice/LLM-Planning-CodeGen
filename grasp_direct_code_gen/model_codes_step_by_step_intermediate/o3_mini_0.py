def solve_grid(grid, start_position, max_actions):
    """
    Collect energy tokens ('E') and drop them at the starting cell.
    The grid is a 2D list of strings.
    start_position is a tuple (row, col) containing the starting position where 'A' is.
    max_actions is the total number of allowed moves/actions.
    
    Returns:
        A list of actions. Moves are the strings:
          "UP", "DOWN", "LEFT", "RIGHT", "TAKE", "DROP".
    """
    actions = []

    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Helper function: update position given a move.
    def update_position(position, move):
        r, c = position
        if move == "UP":
            return (r - 1, c)
        elif move == "DOWN":
            return (r + 1, c)
        elif move == "LEFT":
            return (r, c - 1)
        elif move == "RIGHT":
            return (r, c + 1)
        else:
            return position

    # Helper function: check if position is within grid bounds.
    def is_within_bounds(position):
        r, c = position
        return 0 <= r < rows and 0 <= c < cols

    # Helper function: get a simple Manhattan path from one cell to another.
    # We move vertically first then horizontally.
    def get_path(start, target):
        path = []
        r_start, c_start = start
        r_target, c_target = target
        
        # vertical moves
        if r_target > r_start:
            path += ["DOWN"] * (r_target - r_start)
        elif r_target < r_start:
            path += ["UP"] * (r_start - r_target)
            
        # horizontal moves
        if c_target > c_start:
            path += ["RIGHT"] * (c_target - c_start)
        elif c_target < c_start:
            path += ["LEFT"] * (c_start - c_target)
            
        return path

    # Initialize current position and remaining actions.
    current = start_position
    remaining_actions = max_actions

    # Build list of energy token locations (where grid cell equals "E")
    # We assume if a token is already at the starting cell, it’s considered banked.
    energy_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "E" and (r, c) != start_position:
                energy_locations.append((r, c))
    
    # Main loop: while there are actions remaining, try to pick up a token.
    while remaining_actions > 0:
        # If the agent is not at home, try to return to the start.
        if current != start_position:
            path_home = get_path(current, start_position)
            if len(path_home) <= remaining_actions:
                for move in path_home:
                    # Check new position bounds before making move.
                    new_pos = update_position(current, move)
                    if not is_within_bounds(new_pos):
                        # Something went wrong: break out.
                        break
                    actions.append(move)
                    current = new_pos
                remaining_actions -= len(path_home)
            else:
                break  # Not enough actions to get home.

        # Look for the token which is reachable (round trip plus TAKE and DROP) within remaining actions.
        best_token = None
        best_cost = float("inf")
        for token in energy_locations:
            # Path from current (which is at start) to token.
            path_to_token = get_path(current, token)
            # And from token back to start.
            path_back = get_path(token, start_position)
            # Plus one action each for TAKE and DROP.
            total_cost = len(path_to_token) + len(path_back) + 2
            if total_cost <= remaining_actions and total_cost < best_cost:
                best_cost = total_cost
                best_token = token

        if best_token is None:
            # No more tokens can be collected within remaining actions.
            break

        # Move to token.
        path_to_token = get_path(current, best_token)
        if len(path_to_token) > remaining_actions:
            break  # Should not happen since we already checked cost.
        for move in path_to_token:
            new_pos = update_position(current, move)
            # Check within bounds
            if not is_within_bounds(new_pos):
                # Should not happen if grid and path are computed correctly.
                break
            actions.append(move)
            current = new_pos
        remaining_actions -= len(path_to_token)

        # TAKE the token from the cell.
        if remaining_actions >= 1:
            actions.append("TAKE")
            remaining_actions -= 1
            # Remove the token from the list so it is not reselected.
            if best_token in energy_locations:
                energy_locations.remove(best_token)
        else:
            break

        # Return to starting cell.
        path_home = get_path(current, start_position)
        if len(path_home) > remaining_actions:
            break
        for move in path_home:
            new_pos = update_position(current, move)
            if not is_within_bounds(new_pos):
                break
            actions.append(move)
            current = new_pos
        remaining_actions -= len(path_home)

        # DROP the token at starting cell.
        if current == start_position and remaining_actions >= 1:
            actions.append("DROP")
            remaining_actions -= 1
        else:
            break  # Not at start or not enough actions.
    
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
    actions = solve_grid(grid, tuple(start_pos), max_actions)
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
    actions = solve_grid(sample_grid, start_position, 20)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()