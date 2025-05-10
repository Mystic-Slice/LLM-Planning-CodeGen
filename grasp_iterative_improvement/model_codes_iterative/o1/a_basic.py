from collections import deque

def find_A_position(grid):
    """
    Finds the (row, col) position of 'A' in the grid.
    Assumes exactly one 'A' is present.
    """
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 'A':
                return (r, c)
    return None  # If not found, though the problem states there will always be one 'A'

def find_all_E_positions(grid):
    """
    Returns a list of all (row, col) positions marked 'E' in the grid.
    """
    positions = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 'E':
                positions.append((r, c))
    return positions

def is_valid(r, c, grid):
    """
    Checks if a given (row, col) is within bounds and not an obstacle 'O'.
    """
    rows = len(grid)
    cols = len(grid[0])
    if r < 0 or r >= rows or c < 0 or c >= cols:
        return False
    if grid[r][c] == 'O':
        return False
    return True

def get_neighbors(r, c, grid, allow_diagonal=False):
    """
    Returns valid neighbor cells from (r, c). If allow_diagonal is True, 
    it will return up to 8 directions. Otherwise, it returns 4 directions.
    """
    directions_4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    directions_8 = [
        (-1, 0), (1, 0), (0, -1), (0, 1), 
        (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]
    result = []
    moves = directions_8 if allow_diagonal else directions_4
    for dr, dc in moves:
        nr, nc = r + dr, c + dc
        if is_valid(nr, nc, grid):
            result.append((nr, nc))
    return result

def bfs_find_path(start, goal, grid, allow_diagonal=False):
    """
    Performs a BFS to find the shortest path from start to goal.
    Returns the path as a list of directions (e.g. ["UP", "RIGHT", ...]).
    If no path is found, returns None.
    """
    # For reconstructing the path, we keep track of (row, col) -> (prev_row, prev_col)
    # and also which move we made to get there.
    directions_map = {
        (-1, 0): "UP",
         (1, 0): "DOWN",
         (0, -1): "LEFT",
         (0, 1): "RIGHT",
         (-1, -1): "UPLEFT",
         (-1, 1): "UPRIGHT",
         (1, -1): "DOWNLEFT",
         (1, 1): "DOWNRIGHT"
    }
    
    queue = deque()
    visited = set()
    
    start_r, start_c = start
    goal_r, goal_c = goal
    
    queue.append(start)
    visited.add(start)
    
    # To reconstruct the path
    parent = dict()
    parent[start] = None  # No parent for start

    # BFS
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        cur_r, cur_c = current
        
        for nxt in get_neighbors(cur_r, cur_c, grid, allow_diagonal):
            if nxt not in visited:
                visited.add(nxt)
                parent[nxt] = current
                queue.append(nxt)
    
    # If goal not reached, return None
    if goal not in parent:
        return None

    # Reconstruct path by traversing parent dict backward from goal to start
    path_cells = []
    curr = goal
    while curr != start:
        path_cells.append(curr)
        curr = parent[curr]
    path_cells.reverse()
    
    # Now translate cell-to-cell moves into directions
    directions = []
    previous = start
    for cell in path_cells:
        dr = cell[0] - previous[0]
        dc = cell[1] - previous[1]
        directions.append(directions_map[(dr, dc)])
        previous = cell
    
    return directions

def path_cost(start, goal, grid, allow_diagonal=False):
    """
    Returns the number of moves in the shortest path from start to goal, 
    or a large number if no path exists.
    """
    path = bfs_find_path(start, goal, grid, allow_diagonal)
    if path is None:
        return float('inf')
    return len(path)

def sort_by_round_trip_cost(energy_positions, start_row, start_col, grid, allow_diagonal=False):
    """
    Sort tokens by their round-trip cost from (start_row, start_col) -> E -> Home.
    That cost includes the path to 'E' and back.
    """
    home = (start_row, start_col)
    round_trip_costs = []
    for e_pos in energy_positions:
        to_e = path_cost(home, e_pos, grid, allow_diagonal)
        back_home = path_cost(e_pos, home, grid, allow_diagonal)
        cost = to_e + back_home  # ignoring TAKE and DROP for sorting, we'll add them later
        round_trip_costs.append((cost, e_pos))
    
    # Sort by cost ascending
    round_trip_costs.sort(key=lambda x: x[0])
    # Return positions in ascending order of cost
    return [pos for _, pos in round_trip_costs]

def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions):
    """
    Returns a list of actions (strings) to collect as many 'E' as possible
    and drop them at 'A' (the starting cell).

    Parameters:
    - grid: 2D list representing the game board (strings)
    - max_actions: integer, the total number of actions allowed
    - max_capacity: the maximum number of tokens the agent can carry
    - allow_diagonal: whether diagonal moves are allowed (bool)

    This code follows a general strategy:
    1) Find 'A'.
    2) Gather 'E' positions.
    3) Sort them by round-trip cost.
    4) Visit them in priority order as time and capacity permit.
    5) Return to 'A' to DROP tokens.
    """
    actions_taken = 0
    action_list = []
    
    # 1. Find 'A' (Home) position
    start_pos = find_A_position(grid)
    if not start_pos:
        return []  # No 'A' found, return empty
    
    start_row, start_col = start_pos
    current_position = start_pos
    
    # 2. Find all 'E' positions
    energy_positions = find_all_E_positions(grid)
    
    # 3. Sort energy tokens by priority (shortest round-trip distance)
    sorted_tokens = sort_by_round_trip_cost(
        energy_positions, start_row, start_col, grid, is_diagonals_allowed
    )
    
    carried_tokens = 0

    # Helper function: move agent along a path of directions
    def follow_path(path):
        nonlocal actions_taken
        for step in path:
            action_list.append(step)
            actions_taken += 1
            if actions_taken >= max_actions:
                break
    
    for token_pos in sorted_tokens:
        if actions_taken >= max_actions:
            break
        
        # Estimate cost: to E, TAKE, back home, DROP
        move_cost_to_E = path_cost(current_position, token_pos, grid, is_diagonals_allowed)
        move_cost_to_home = path_cost(token_pos, start_pos, grid, is_diagonals_allowed)
        # +2 for TAKE and DROP
        total_trip_cost = move_cost_to_E + move_cost_to_home + 2
        
        # Check if we have enough actions left
        if actions_taken + total_trip_cost > max_actions:
            continue
        
        # 6. Go to the token
        path_to_E = bfs_find_path(current_position, token_pos, grid, is_diagonals_allowed)
        if path_to_E is None:
            # No path to this token, skip it
            continue
        
        follow_path(path_to_E)
        if actions_taken >= max_actions:
            break
        
        # TAKE
        action_list.append("TAKE")
        actions_taken += 1
        carried_tokens += 1
        current_position = token_pos
        if actions_taken >= max_actions:
            break
        
        # If capacity is reached or we want to ensure we score
        # go home and drop immediately for simplicity
        path_to_home = bfs_find_path(current_position, start_pos, grid, is_diagonals_allowed)
        if path_to_home is None:
            # No path home, skip dropping. 
            # In a real scenario, we'd handle differently, but for now we end.
            break
        
        follow_path(path_to_home)
        if actions_taken >= max_actions:
            break
        
        # DROP
        action_list.append("DROP")
        actions_taken += 1
        carried_tokens -= 1
        current_position = start_pos
    
    # If we still carry tokens (in a scenario we had multi-token logic),
    # drop them if we have actions left. This code ensures no tokens stay in hand.
    while carried_tokens > 0 and actions_taken < max_actions:
        action_list.append("DROP")
        actions_taken += 1
        carried_tokens -= 1
    
    return action_list
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