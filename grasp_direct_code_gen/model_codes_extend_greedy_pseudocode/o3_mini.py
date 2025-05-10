def solve_grid(grid, start_position, carry_limit, cost_per_step, is_diagonals_allowed, max_actions):
    """
    grid: a list of lists representing the 2D grid (grid[row][col]).
    start_position: tuple (row, col) representing initial starting position.
    carry_limit: maximum number of tokens that can be carried.
    cost_per_step: energy cost per movement step (not deducted during movements – can be used to compute final score).
    is_diagonals_allowed: boolean.
    max_actions: maximum number of actions allowed.
    
    Returns:
      A list of actions (each is either a movement direction, "TAKE" or "DROP") that if executed will have
      the agent collect energy tokens and deposit them in the start cell.
    """
    actions_list = []
    current_position = start_position
    actions_remaining = max_actions
    current_carry = 0

    # Create a copy of the grid so that when we "collect" tokens we'll mark them as empty.
    grid = [row[:] for row in grid]

    # Main loop: keep trying until no actions remain.
    while actions_remaining > 0:
        # If bag is full, return to start to drop tokens.
        if current_carry == carry_limit:
            path_to_start = bfs_path(grid, current_position, start_position, is_diagonals_allowed)
            if path_to_start is None:
                break  # no valid path back to start
            if len(path_to_start) + 1 > actions_remaining:
                # Not enough actions to return and drop, so break.
                break
            # Follow the path to go back to start.
            for move in path_to_start:
                actions_list.append(move)
                current_position = move_agent(current_position, move, grid)
                actions_remaining -= 1
            # At the start, drop tokens.
            actions_list.append("DROP")
            current_carry = 0
            actions_remaining -= 1
            continue

        # Find the nearest energy token.
        token_info = find_nearest_token(grid, current_position, is_diagonals_allowed)
        if token_info is None:
            # No further tokens found; if not at start then return home.
            if current_position != start_position:
                path_to_start = bfs_path(grid, current_position, start_position, is_diagonals_allowed)
                if path_to_start is not None and len(path_to_start) <= actions_remaining:
                    for move in path_to_start:
                        actions_list.append(move)
                        current_position = move_agent(current_position, move, grid)
                        actions_remaining -= 1
            if current_carry > 0 and current_position == start_position and actions_remaining > 0:
                actions_list.append("DROP")
                current_carry = 0
                actions_remaining -= 1
            break

        token_position, path_to_token = token_info
        steps_to_token = len(path_to_token)
        # Compute path from token cell back to start.
        path_token_to_start = bfs_path(grid, token_position, start_position, is_diagonals_allowed)
        if path_token_to_start is None:
            # Mark token as unreachable if no return path available,
            # and remove token from grid.
            remove_token(grid, token_position)
            continue
        steps_to_return = len(path_token_to_start)
        # One extra action will be needed to "TAKE" the token.
        total_actions_for_token = steps_to_token + 1 + steps_to_return
        if total_actions_for_token > actions_remaining:
            # Not enough actions to collect this token.
            if current_position != start_position:
                path_to_start = bfs_path(grid, current_position, start_position, is_diagonals_allowed)
                if path_to_start is not None and len(path_to_start) <= actions_remaining:
                    for move in path_to_start:
                        actions_list.append(move)
                        current_position = move_agent(current_position, move, grid)
                        actions_remaining -= 1
            if current_carry > 0 and current_position == start_position and actions_remaining > 0:
                actions_list.append("DROP")
                current_carry = 0
                actions_remaining -= 1
            break

        # Follow the path to the token.
        for move in path_to_token:
            if actions_remaining <= 0:
                break
            actions_list.append(move)
            current_position = move_agent(current_position, move, grid)
            actions_remaining -= 1

        # Perform the TAKE action, if token is present.
        if is_token_at(grid, current_position):
            actions_list.append("TAKE")
            current_carry += 1
            # Remove token from grid cell.
            grid[current_position[0]][current_position[1]] = ""
            actions_remaining -= 1

    # End main loop.
    # Final step: if not at the start cell, try to return.
    if current_position != start_position and actions_remaining > 0:
        path_to_start = bfs_path(grid, current_position, start_position, is_diagonals_allowed)
        if path_to_start is not None and len(path_to_start) <= actions_remaining:
            for move in path_to_start:
                actions_list.append(move)
                current_position = move_agent(current_position, move, grid)
                actions_remaining -= 1

    if current_carry > 0 and current_position == start_position and actions_remaining > 0:
        actions_list.append("DROP")
        current_carry = 0
        actions_remaining -= 1

    return actions_list

# Helper function: Check if there is a token "E" at a given cell.
def is_token_at(grid, cell):
    r, c = cell
    # Assuming the token is represented by "E"
    return grid[r][c] == "E"

# Helper function: remove token from grid (set cell to empty string).
def remove_token(grid, cell):
    r, c = cell
    grid[r][c] = ""

# Helper function: Move the agent given a move.
def move_agent(current_position, move, grid):
    new_position = get_neighbor(current_position, move)
    # Safety check: ensure new_position is within grid bounds and not an obstacle.
    if is_valid_cell(new_position, grid):
        return new_position
    return current_position

# Helper function: get neighbor cell from current cell and move.
def get_neighbor(cell, move):
    row, col = cell
    if move == "LEFT":
        return (row, col - 1)
    elif move == "RIGHT":
        return (row, col + 1)
    elif move == "UP":
        return (row - 1, col)
    elif move == "DOWN":
        return (row + 1, col)
    elif move == "UPLEFT":
        return (row - 1, col - 1)
    elif move == "UPRIGHT":
        return (row - 1, col + 1)
    elif move == "DOWNLEFT":
        return (row + 1, col - 1)
    elif move == "DOWNRIGHT":
        return (row + 1, col + 1)
    return (row, col)

# Helper function: Check if a cell is valid (within grid bounds and not an obstacle "O").
def is_valid_cell(cell, grid):
    row, col = cell
    num_rows = len(grid)
    num_cols = len(grid[0])
    if 0 <= row < num_rows and 0 <= col < num_cols:
        # Treat obstacle cell "O" as invalid.
        return grid[row][col] != "O"
    return False

# BFS to find the shortest path (a list of moves) from start to goal.
def bfs_path(grid, start, goal, is_diagonals_allowed):
    from collections import deque
    queue = deque()
    queue.append((start, []))
    visited = set()
    visited.add(start)
    
    moves_possible = ["LEFT", "RIGHT", "UP", "DOWN"]
    if is_diagonals_allowed:
        moves_possible += ["UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"]

    while queue:
        current_cell, path_so_far = queue.popleft()
        if current_cell == goal:
            return path_so_far
        for move in moves_possible:
            neighbor = get_neighbor(current_cell, move)
            if neighbor not in visited and is_valid_cell(neighbor, grid):
                visited.add(neighbor)
                queue.append((neighbor, path_so_far + [move]))
    return None  # No valid path found

# BFS to find the nearest token cell (with "E") from the starting cell.
def find_nearest_token(grid, start, is_diagonals_allowed):
    from collections import deque
    queue = deque()
    queue.append((start, []))
    visited = set()
    visited.add(start)
    
    moves_possible = ["LEFT", "RIGHT", "UP", "DOWN"]
    if is_diagonals_allowed:
        moves_possible += ["UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"]
    
    while queue:
        current_cell, path_so_far = queue.popleft()
        r, c = current_cell
        if grid[r][c] == "E":
            return (current_cell, path_so_far)
        for move in moves_possible:
            neighbor = get_neighbor(current_cell, move)
            if neighbor not in visited and is_valid_cell(neighbor, grid):
                visited.add(neighbor)
                queue.append((neighbor, path_so_far + [move]))
    return None  # No token found

# # Example of how you might call the function:
# if __name__ == '__main__':
#     # Example grid: a 2D list of strings.
#     grid = [
#         ["", "", "E", "E", "E", "E", "", "E", "E", "E", "E"],
#         ["", "", "E", "E", "E", "", "", "", "", "E", ""],
#         ["E", "", "", "", "E", "", "", "E", "E", "", ""],
#         ["E", "E", "E", "E", "", "E", "E", "E", "", "E", "E"],
#         ["", "E", "", "A", "E", "", "E", "", "E", "E", ""],
#         ["E", "", "E", "", "E", "E", "", "E", "", "E", ""],
#         ["E", "", "E", "", "", "", "", "E", "E", "E", "E"],
#         ["E", "E", "", "", "", "", "E", "", "E", "E", ""],
#         ["E", "", "E", "E", "E", "", "", "", "E", "E", ""],
#         ["", "", "E", "E", "E", "", "E", "", "", "", ""],
#         ["", "E", "E", "", "E", "E", "", "E", "", "E", "E"]
#     ]
#     # Find the starting position (cell containing "A")
#     start_position = None
#     for i, row in enumerate(grid):
#         for j, cell in enumerate(row):
#             if cell == "A":
#                 start_position = (i, j)
#                 break
#         if start_position is not None:
#             break

#     carry_limit = 3
#     cost_per_step = 1
#     is_diagonals_allowed = True
#     max_actions = 100

#     actions = solve(grid, start_position, carry_limit, cost_per_step, is_diagonals_allowed, max_actions)
#     print("Actions:", actions)

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