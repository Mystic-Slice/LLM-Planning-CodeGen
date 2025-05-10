def solve_grid(grid, start_position, max_actions, is_diagonals_allowed, carry_limit, cost_per_step):
    """
    Collect energy tokens ('E') from the grid and drop them at the starting cell.
    
    Parameters:
       grid: 2D list of strings. Each cell contains "E" for energy, "A" for the starting cell/agent, or " " for empty.
       start_position: Tuple (row, col) for the starting position (where 'A' is located).
       max_actions: Total number of allowed actions (each move, TAKE, or DROP counts as one).
       is_diagonals_allowed: Boolean indicating if diagonal moves are permitted.
       carry_limit: Maximum number of tokens the agent can carry at once.
       cost_per_step: A float cost that is incurred per movement (each directional step).
       
    Returns:
       A tuple (actions, net_tokens) where:
         - actions is the list of actions taken (e.g., "UP", "DOWNRIGHT", "TAKE", "DROP", etc.),
         - net_tokens is the final net energy tokens deposited at the base,
           computed as (number of tokens dropped) - (cost_per_step * number of movement steps).
    """
    actions = []
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Counters for movement (which incur cost) and tokens deposited.
    step_count = 0   # counts each move action that is a directional step.
    drop_count = 0   # number of tokens dropped (banked).

    # Helper: Given a position and a move string, return the new position.
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

    # Helper: Check if a position is inside the grid.
    def is_within_bounds(position):
        r, c = position
        return 0 <= r < rows and 0 <= c < cols

    # Helper: Return a list of moves (path) from start to target.
    # If diagonals are allowed, uses them optimally; otherwise, uses Manhattan moves.
    def get_path(start, target):
        path = []
        r_current, c_current = start
        r_target, c_target = target

        if is_diagonals_allowed:
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
            # Without diagonals: move vertically then horizontally.
            if r_target > r_current:
                path += ["DOWN"] * (r_target - r_current)
            elif r_target < r_current:
                path += ["UP"] * (r_current - r_target)
            if c_target > c_current:
                path += ["RIGHT"] * (c_target - c_current)
            elif c_target < c_current:
                path += ["LEFT"] * (c_current - c_target)
        return path

    # Create a list of all energy token positions (cells with "E") that are not at the starting cell.
    energy_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "E" and (r, c) != start_position:
                energy_locations.append((r, c))

    current = start_position
    remaining_actions = max_actions

    # Main loop: Repeat until actions run out or no tokens remain.
    while remaining_actions > 0 and energy_locations:
        # Always start a batch at the base.
        if current != start_position:
            path_home = get_path(current, start_position)
            if len(path_home) > remaining_actions:
                break
            for move in path_home:
                new_pos = update_position(current, move)
                if not is_within_bounds(new_pos):
                    break  # safety check; should not occur.
                actions.append(move)
                current = new_pos
                step_count += 1  # movement step incurred.
            remaining_actions -= len(path_home)

        # Begin a batch: pick tokens until reaching carry_limit.
        batch_actions = []    # temporary list for this batch's actions.
        batch_cost = 0        # cost (in actions) used within this batch so far.
        batch_carried = 0     # number of tokens collected in current batch.
        batch_current = current  # current position during the batch (starts at base).

        # Continue adding tokens to the batch if there is room.
        while batch_carried < carry_limit and energy_locations:
            best_candidate = None
            best_candidate_additional_cost = float("inf")
            best_candidate_path = None

            # Evaluate each available token for feasibility.
            for token in energy_locations:
                path_to_token = get_path(batch_current, token)
                travel_cost = len(path_to_token)
                take_cost = 1  # one action for TAKE
                # After taking the token, we must return home.
                path_home_from_candidate = get_path(token, start_position)
                return_cost = len(path_home_from_candidate)
                # In finishing the batch, we need one DROP per token in the batch (after adding this token).
                drop_cost = batch_carried + 1

                candidate_extra = travel_cost + take_cost + return_cost + drop_cost
                # Check whether after adding this candidate, the overall cost of this batch
                # (batch_cost so far + candidate extra cost) fits into the remaining_actions.
                if batch_cost + candidate_extra <= remaining_actions:
                    # Choose candidate with smallest travel cost (simple heuristic).
                    if travel_cost < best_candidate_additional_cost:
                        best_candidate = token
                        best_candidate_additional_cost = travel_cost
                        best_candidate_path = path_to_token

            if best_candidate is None:
                break  # no candidate can be added to this batch safely.
            
            # Add the candidate: move along the best_candidate_path.
            for move in best_candidate_path:
                batch_actions.append(move)
                batch_current = update_position(batch_current, move)
            batch_actions.append("TAKE")
            # Update cost: movement steps + TAKE.
            batch_cost += len(best_candidate_path) + 1
            batch_carried += 1
            energy_locations.remove(best_candidate)

        # If tokens were collected in this batch, finish by returning home and dropping them.
        if batch_carried > 0:
            path_to_home = get_path(batch_current, start_position)
            finish_cost = len(path_to_home) + batch_carried  # return steps plus one DROP per token.
            if batch_cost + finish_cost <= remaining_actions:
                for move in path_to_home:
                    batch_actions.append(move)
                for _ in range(batch_carried):
                    batch_actions.append("DROP")
                total_batch_cost = batch_cost + finish_cost
                remaining_actions -= total_batch_cost
                # Append this batch’s actions to the overall actions.
                for act in batch_actions:
                    actions.append(act)
                    # Increment step_count for each movement action in the batch.
                    if act in ["UP", "DOWN", "LEFT", "RIGHT", 
                               "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"]:
                        step_count += 1
                    # Count DROP actions to know number of tokens banked.
                    if act == "DROP":
                        drop_count += 1
                current = start_position  # batch ends at home.
            else:
                break  # not enough remaining actions to finish this batch.
        else:
            break  # no token could be added to a new batch.
    
    # Compute the net tokens:
    # net tokens = tokens dropped (banked) minus (cost_per_step * number_of_movement_steps)
    net_tokens = drop_count - (cost_per_step * step_count)
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