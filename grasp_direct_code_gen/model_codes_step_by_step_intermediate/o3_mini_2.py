def solve_grid(grid, start_position, max_actions, is_diagonals_allowed, carry_limit):
    """
    Collect energy tokens ('E') from the grid and drop them at the starting cell.
    
    Parameters:
      grid: A 2D list of strings. A cell may be "E" (energy), "A" (agent, at start) or " " (empty).
      start_position: A tuple (row, col) indicating the agent's starting position.
      max_actions: The total number of allowed actions (each movement, TAKE or DROP counts as one).
      is_diagonals_allowed: Boolean. If True, the agent can move diagonally ("UPLEFT","UPRIGHT","DOWNLEFT","DOWNRIGHT") as well as
                            the four cardinal directions.
      carry_limit: The maximum number of tokens the agent may carry at once.
    
    Returns:
      A list of action strings (for example, "UP", "DOWN", "TAKE", "DROP", etc.) describing the moves.
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

    # Helper function: check if a position is within grid bounds.
    def is_within_bounds(position):
        r, c = position
        return 0 <= r < rows and 0 <= c < cols

    # Helper function: get a path (list of moves) from start to target.
    # If diagonals are allowed, the path uses them when both coordinates can change;
    # otherwise, the path first moves vertically then horizontally.
    def get_path(start, target):
        path = []
        r_current, c_current = start
        r_target, c_target = target

        if is_diagonals_allowed:
            # While either coordinate differs, choose a diagonal if possible.
            while (r_current != r_target) or (c_current != c_target):
                dr = r_target - r_current
                dc = c_target - c_current
                move = None
                if dr > 0 and dc > 0:
                    move = "DOWNRIGHT"
                elif dr > 0 and dc < 0:
                    move = "DOWNLEFT"
                elif dr < 0 and dc > 0:
                    move = "UPRIGHT"
                elif dr < 0 and dc < 0:
                    move = "UPLEFT"
                else:
                    # When one coordinate is already in line
                    if dr > 0:
                        move = "DOWN"
                    elif dr < 0:
                        move = "UP"
                    elif dc > 0:
                        move = "RIGHT"
                    elif dc < 0:
                        move = "LEFT"
                if move is None:
                    break
                path.append(move)
                r_current, c_current = update_position((r_current, c_current), move)
        else:
            # Without diagonals: vertical moves, then horizontal.
            if r_target > r_current:
                path += ["DOWN"] * (r_target - r_current)
            elif r_target < r_current:
                path += ["UP"] * (r_current - r_target)
            if c_target > c_current:
                path += ["RIGHT"] * (c_target - c_current)
            elif c_target < c_current:
                path += ["LEFT"] * (c_current - c_target)
        return path

    # Build list of energy tokens (cells with "E") that are not already at the starting cell.
    energy_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "E" and (r, c) != start_position:
                energy_locations.append((r, c))

    current = start_position
    remaining_actions = max_actions

    # Main loop: as long as we have actions and tokens to collect.
    while remaining_actions > 0 and energy_locations:
        # Always start a batch at the home base.
        if current != start_position:
            path_home = get_path(current, start_position)
            if len(path_home) > remaining_actions:
                break
            for move in path_home:
                new_pos = update_position(current, move)
                if not is_within_bounds(new_pos):
                    break  # Safety check.
                actions.append(move)
                current = new_pos
            remaining_actions -= len(path_home)

        # Begin a batch collection.
        batch_actions = []       # Actions for this batch (will be appended to main actions once complete).
        batch_cost = 0           # The cost (in actions) consumed inside this batch so far.
        batch_carried = 0        # Tokens picked up in the current batch.
        batch_current = current  # Batch starting point (should be home).

        # Attempt to pick up tokens until we hit the carrying limit.
        while batch_carried < carry_limit and energy_locations:
            best_candidate = None
            best_candidate_additional_cost = float("inf")
            best_candidate_path = None

            # For each candidate token, check if adding it (plus eventual return and drop) fits into remaining actions.
            for token in energy_locations:
                # Moves from current batch position to token.
                path_to_token = get_path(batch_current, token)
                travel_cost = len(path_to_token)
                take_cost = 1  # one action for TAKE
                # If we take this candidate, then after that we must return home.
                path_home_from_candidate = get_path(token, start_position)
                return_cost = len(path_home_from_candidate)
                # When finishing the batch, we will need one DROP per token carried in the batch (after adding this one).
                drop_cost = batch_carried + 1

                # The extra cost if we add this candidate now:
                candidate_extra = travel_cost + take_cost + return_cost + drop_cost
                # Total batch cost if we add this candidate: cost already spent in batch + the extra cost.
                if batch_cost + candidate_extra <= remaining_actions:
                    # Choose the candidate with the smallest travel-cost (can be adapted to more complex heuristics).
                    if travel_cost < best_candidate_additional_cost:
                        best_candidate = token
                        best_candidate_additional_cost = travel_cost
                        best_candidate_path = path_to_token

            if best_candidate is None:
                # No candidate can be collected and still finish the batch.
                break

            # Add the moves for best candidate to the batch.
            for move in best_candidate_path:
                batch_actions.append(move)
                batch_current = update_position(batch_current, move)
            batch_actions.append("TAKE")
            # Update batch cost: travel + TAKE.
            batch_cost += len(best_candidate_path) + 1
            batch_carried += 1
            energy_locations.remove(best_candidate)

        # If we collected any tokens in this batch, finish by returning home and dropping them.
        if batch_carried > 0:
            path_to_home = get_path(batch_current, start_position)
            finish_cost = len(path_to_home) + batch_carried  # each DROP is an action.
            if batch_cost + finish_cost <= remaining_actions:
                for move in path_to_home:
                    batch_actions.append(move)
                # Append one DROP per token carried.
                for _ in range(batch_carried):
                    batch_actions.append("DROP")
                total_batch_cost = batch_cost + finish_cost
                remaining_actions -= total_batch_cost
                actions.extend(batch_actions)
                current = start_position  # batch finished at home.
            else:
                # Not enough actions left to finish this batch.
                break
        else:
            # Could not collect any token in a new batch.
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
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == 'eight'), carry_limit)
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
    actions = solve_grid(sample_grid, start_position, 20, diagonals_allowed, carry_limit)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()