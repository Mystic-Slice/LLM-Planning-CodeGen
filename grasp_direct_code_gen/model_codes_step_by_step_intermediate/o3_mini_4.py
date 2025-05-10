def solve_grid(grid, start_position, max_actions, is_diagonals_allowed, carry_limit, cost_per_step):
    """
    Collect energy tokens ('E') from the grid and drop them at the starting cell,
    while avoiding obstacles ('O').

    Parameters:
       grid: 2D list of strings. Each cell contains:
             "E" for an energy token,
             "A" for the starting cell / agent,
             "O" for an obstacle, or
             " " for an empty cell.
       start_position: Tuple (row, col) for the starting position (where 'A' is located).
       max_actions: Total number of allowed actions (each move, TAKE, or DROP counts as one).
       is_diagonals_allowed: Boolean indicating if diagonal moves are permitted.
       carry_limit: Maximum number of tokens the agent can carry at once.
       cost_per_step: A float cost incurred per movement step.
       
    Returns:
       A tuple (actions, net_tokens) where:
         - actions is the list of actions taken (e.g., "UP", "DOWN", "TAKE", "DROP", etc.),
         - net_tokens is the final net energy tokens deposited at the base,
           computed as (number of tokens dropped) - (cost_per_step * number of movement steps).
    """
    from collections import deque

    actions = []
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Count movement steps (each directional move incurs cost) and tokens dropped.
    step_count = 0
    drop_count = 0

    # Allowed movement directions.
    if is_diagonals_allowed:
        MOVES = [
            ("UP", -1, 0),
            ("DOWN", 1, 0),
            ("LEFT", 0, -1),
            ("RIGHT", 0, 1),
            ("UPLEFT", -1, -1),
            ("UPRIGHT", -1, 1),
            ("DOWNLEFT", 1, -1),
            ("DOWNRIGHT", 1, 1),
        ]
    else:
        MOVES = [
            ("UP", -1, 0),
            ("DOWN", 1, 0),
            ("LEFT", 0, -1),
            ("RIGHT", 0, 1),
        ]

    # Helper function to update a position given a move.
    def update_position(position, move):
        r, c = position
        # Find dx, dy for the given move.
        for m, dx, dy in MOVES:
            if m == move:
                return (r + dx, c + dy)
        return position

    # Helper function: Check if position is in grid bounds and not an obstacle.
    def is_valid(position):
        r, c = position
        return (0 <= r < rows) and (0 <= c < cols) and (grid[r][c] != "O")

    # BFS function to get a valid path (list of moves) from start to target avoiding obstacles.
    # Returns None if no such path exists.
    def get_path_bfs(start, target):
        # Queue items are: (current_position, path_so_far)
        queue = deque()
        queue.append((start, []))
        visited = set()
        visited.add(start)

        while queue:
            current, path = queue.popleft()
            if current == target:
                return path
            for move, dx, dy in MOVES:
                next_pos = (current[0] + dx, current[1] + dy)
                if next_pos in visited:
                    continue
                if not is_valid(next_pos):
                    continue
                visited.add(next_pos)
                queue.append((next_pos, path + [move]))
        return None  # target unreachable

    # For convenience, define get_path as get_path_bfs.
    def get_path(start, target):
        path = get_path_bfs(start, target)
        # If no valid path exists, we return an empty list (caller should check for feasibility).
        return path if path is not None else []

    # Build list of energy tokens.
    energy_locations = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "E" and (r, c) != start_position:
                energy_locations.append((r, c))

    current = start_position
    remaining_actions = max_actions

    # Main loop: perform batches until actions run out or tokens exhausted.
    while remaining_actions > 0 and energy_locations:
        # Ensure the agent is at home.
        if current != start_position:
            path_home = get_path(current, start_position)
            if not path_home or len(path_home) > remaining_actions:
                break  # cannot return home
            for move in path_home:
                new_pos = update_position(current, move)
                # Safety check (should be valid since get_path avoided obstacles).
                if not is_valid(new_pos):
                    break
                actions.append(move)
                current = new_pos
                step_count += 1
            remaining_actions -= len(path_home)

        # Begin a batch from home.
        batch_actions = []    # actions for this batch
        batch_cost = 0        # cost in actions spent within this batch (movement + TAKE)
        batch_carried = 0     # tokens currently carried
        batch_current = current  # current position within batch (starts at home)

        # Try to collect tokens until carry_limit reached.
        while batch_carried < carry_limit and energy_locations:
            best_candidate = None
            best_candidate_additional_cost = float("inf")
            best_candidate_path = None

            # For each candidate token that remains, 
            # check the cost (in actions) to go from current batch position to candidate,
            # TAKE it, then return home, and drop all tokens carried.
            for token in energy_locations:
                path_to_token = get_path(batch_current, token)
                if not path_to_token:  # no valid path to candidate
                    continue
                travel_cost = len(path_to_token)
                take_cost = 1  # TAKE action
                path_home_from_candidate = get_path(token, start_position)
                if not path_home_from_candidate:
                    continue  # cannot return home from this token
                return_cost = len(path_home_from_candidate)
                # DROP cost: If we add this token, we will have (batch_carried + 1) tokens to drop.
                drop_cost = batch_carried + 1
                candidate_extra = travel_cost + take_cost + return_cost + drop_cost

                if batch_cost + candidate_extra <= remaining_actions:
                    if travel_cost < best_candidate_additional_cost:
                        best_candidate = token
                        best_candidate_additional_cost = travel_cost
                        best_candidate_path = path_to_token

            if best_candidate is None:
                break  # cannot add any token safely.
            
            # Add best_candidate.
            for move in best_candidate_path:
                batch_actions.append(move)
                batch_current = update_position(batch_current, move)
            batch_actions.append("TAKE")
            batch_cost += len(best_candidate_path) + 1
            batch_carried += 1
            energy_locations.remove(best_candidate)

        # If any tokens were picked up in this batch, return home and drop them.
        if batch_carried > 0:
            path_to_home = get_path(batch_current, start_position)
            if not path_to_home:
                break  # cannot return home; abort batch.
            finish_cost = len(path_to_home) + batch_carried  # moves + DROP cost
            if batch_cost + finish_cost <= remaining_actions:
                for move in path_to_home:
                    batch_actions.append(move)
                for _ in range(batch_carried):
                    batch_actions.append("DROP")
                total_batch_cost = batch_cost + finish_cost
                remaining_actions -= total_batch_cost
                # Append this batch's actions to the overall actions.
                for act in batch_actions:
                    actions.append(act)
                    if act in [m for m,_,_ in MOVES]:
                        step_count += 1
                    if act == "DROP":
                        drop_count += 1
                current = start_position
            else:
                break  # not enough actions left to finish the batch.
        else:
            break  # no token added in this batch; exit.

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