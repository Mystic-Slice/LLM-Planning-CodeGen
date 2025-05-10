def solve_grid(grid, start_position, max_actions, is_diagonals_allowed):
    """
    Collect energy tokens ('E') and drop them at the starting cell.
    
    Parameters:
       grid: A 2D list of strings (e.g., " ", "E", "A").
       start_position: A tuple (row, col) indicating the agent's starting position.
       max_actions: The total number of allowed moves/actions.
       is_diagonals_allowed: Boolean; if True, diagonal moves are allowed.
    
    Returns:
       A list of actions. Moves are strings such as:
         "UP", "DOWN", "LEFT", "RIGHT", "TAKE", "DROP"
         and if diagonals are allowed: "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT".
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
        elif move == "UPLEFT":
            return (r - 1, c - 1)
        elif move == "UPRIGHT":
            return (r - 1, c + 1)
        elif move == "DOWNLEFT":
            return (r + 1, c - 1)
        elif move == "DOWNRIGHT":
            return (r + 1, c + 1)
        else:
            return position

    # Helper function: check if position is within grid bounds.
    def is_within_bounds(position):
        r, c = position
        return 0 <= r < rows and 0 <= c < cols

    # Helper function: get a path from one cell to another.
    # If diagonals are allowed, then use them when both coordinates differ.
    # Otherwise, use Manhattan (vertical then horizontal) moves.
    def get_path(start, target):
        path = []
        r_current, c_current = start
        r_target, c_target = target

        if is_diagonals_allowed:
            # While both row and col are not yet correct, try diagonal move.
            while (r_current != r_target) or (c_current != c_target):
                dr = r_target - r_current
                dc = c_target - c_current

                move = None
                # Use diagonal if possible:
                if dr > 0 and dc > 0:
                    move = "DOWNRIGHT"
                elif dr > 0 and dc < 0:
                    move = "DOWNLEFT"
                elif dr < 0 and dc > 0:
                    move = "UPRIGHT"
                elif dr < 0 and dc < 0:
                    move = "UPLEFT"
                else:
                    # If one coordinate is already aligned
                    if dr > 0:
                        move = "DOWN"
                    elif dr < 0:
                        move = "UP"
                    elif dc > 0:
                        move = "RIGHT"
                    elif dc < 0:
                        move = "LEFT"
                
                if move is None:
                    break   # should not happen, but safety break

                path.append(move)
                # Update current position.
                r_current, c_current = update_position((r_current, c_current), move)
        else:
            # Without diagonals, first adjust rows then cols.
            if r_target > r_current:
                path += ["DOWN"] * (r_target - r_current)
            elif r_target < r_current:
                path += ["UP"] * (r_current - r_target)
            if c_target > c_current:
                path += ["RIGHT"] * (c_target - c_current)
            elif c_target < c_current:
                path += ["LEFT"] * (c_current - c_target)
        
        return path

    # Set current position and remaining actions.
    current = start_position
    remaining_actions = max_actions

    # Build list of energy token locations (grid cell equals "E") that are not in the start cell.
    energy_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "E" and (r, c) != start_position:
                energy_locations.append((r, c))

    # Main loop: while there are actions remaining, pick up and bank a token.
    while remaining_actions > 0:
        # If agent is not at the base, go back home.
        if current != start_position:
            path_home = get_path(current, start_position)
            if len(path_home) <= remaining_actions:
                for move in path_home:
                    new_pos = update_position(current, move)
                    if not is_within_bounds(new_pos):
                        break   # this should not happen if our path is correct.
                    actions.append(move)
                    current = new_pos
                remaining_actions -= len(path_home)
            else:
                break  # not enough moves to return home

        # Find a token that can be collected and banked with remaining actions.
        best_token = None
        best_cost = float("inf")
        for token in energy_locations:
            path_to_token = get_path(current, token)
            path_back = get_path(token, start_position)
            total_cost = len(path_to_token) + len(path_back) + 2  # +2 for TAKE and DROP actions
            if total_cost <= remaining_actions and total_cost < best_cost:
                best_cost = total_cost
                best_token = token

        # If no token can be picked up with the remaining actions, then break.
        if best_token is None:
            break

        # Move to the token.
        path_to_token = get_path(current, best_token)
        if len(path_to_token) > remaining_actions:
            break  # safeguard check
        for move in path_to_token:
            new_pos = update_position(current, move)
            if not is_within_bounds(new_pos):
                break
            actions.append(move)
            current = new_pos
        remaining_actions -= len(path_to_token)

        # TAKE the energy token.
        if remaining_actions >= 1:
            actions.append("TAKE")
            remaining_actions -= 1
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

        # DROP the energy token at the base.
        if current == start_position and remaining_actions >= 1:
            actions.append("DROP")
            remaining_actions -= 1
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
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == 'eight'))
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
    actions = solve_grid(sample_grid, start_position, 20, diagonals_allowed)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()