import collections
import heapq
from typing import List, Tuple, Dict, Set, Optional

# Define types for clarity
Grid = List[List[str]]
Position = Tuple[int, int]
Action = str
ActionList = List[Action]
PathData = Tuple[Optional[ActionList], int] # (path_actions, cost = number of steps)

# Define all possible moves and their deltas
ALL_MOVES: Dict[Action, Tuple[int, int]] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
    "UPLEFT": (-1, -1),
    "UPRIGHT": (-1, 1),
    "DOWNLEFT": (1, -1),
    "DOWNRIGHT": (1, 1),
}

CARDINAL_MOVES: Dict[Action, Tuple[int, int]] = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1),
}


def bfs(grid: Grid, start_coord: Position, end_coord: Position, is_diagonals_allowed: bool) -> PathData:
    """
    Performs Breadth-First Search to find the shortest path in terms of moves,
    avoiding obstacles ('O') and optionally allowing diagonal movement.

    Args:
        grid: The 2D grid, potentially containing 'O' for obstacles.
        start_coord: The starting (row, col) tuple.
        end_coord: The target (row, col) tuple.
        is_diagonals_allowed: If True, allow diagonal moves.

    Returns:
        A tuple containing:
        - A list of actions representing the shortest path, or None if no path exists.
        - The cost (number of moves) of the path, or float('inf') if no path.
    """
    rows = len(grid)
    if rows == 0: return None, float('inf')
    cols = len(grid[0])
    if cols == 0: return None, float('inf')

    # Check if start or end are obstacles themselves (shouldn't happen if E/A are placed correctly)
    if grid[start_coord[0]][start_coord[1]] == 'O' or grid[end_coord[0]][end_coord[1]] == 'O':
         return None, float('inf')

    queue = collections.deque([(start_coord, [])])
    visited: Set[Position] = {start_coord}
    possible_moves = ALL_MOVES if is_diagonals_allowed else CARDINAL_MOVES

    while queue:
        current_coord, path_actions = queue.popleft()

        if current_coord == end_coord:
            return path_actions, len(path_actions) # Cost is number of steps

        for action, (dr, dc) in possible_moves.items():
            next_r, next_c = current_coord[0] + dr, current_coord[1] + dc
            next_coord = (next_r, next_c)

            # Check grid bounds
            if 0 <= next_r < rows and 0 <= next_c < cols:
                # --- Obstacle Check ---
                if grid[next_r][next_c] != 'O':
                    if next_coord not in visited:
                        visited.add(next_coord)
                        new_path = path_actions + [action]
                        queue.append((next_coord, new_path))
                # --- End Obstacle Check ---

    # Target not reachable
    return None, float('inf')

def find_energy_locations(grid: Grid) -> Set[Position]:
    """Finds all coordinates containing energy 'E'."""
    # (Code identical to previous version)
    locations: Set[Position] = set()
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 'E':
                locations.add((r, c))
    return locations

def solve_grid(grid: Grid, start_position: Position, max_actions: int, is_diagonals_allowed: bool, carry_limit: int, cost_per_step: float) -> ActionList:
    """
    Calculates a sequence of actions to maximize score (E dropped - steps * cost_per_step),
    respecting action limit, carry limit, and avoiding obstacles ('O').
    Uses a greedy strategy based on score contribution.

    Args:
        grid: The 2D grid, may contain 'O' obstacles.
        start_position: The agent's start (row, col).
        max_actions: The maximum number of total actions allowed.
        is_diagonals_allowed: Boolean indicating if diagonal moves are permitted.
        carry_limit: Maximum number of energy tokens the agent can hold.
        cost_per_step: Penalty subtracted from score for each movement action taken.

    Returns:
        A list of actions.
    """
    # Input validation (ensure start position is not an obstacle)
    if grid[start_position[0]][start_position[1]] == 'O':
        print("Error: Start position is on an obstacle.")
        return []

    rows = len(grid)
    if rows == 0: return []
    cols = len(grid[0])
    if cols == 0: return []
    if carry_limit <= 0: return []

    # 1. Initialization
    initial_energy_locations = find_energy_locations(grid)
    current_actions = 0
    collected_e_locations: Set[Position] = set()
    final_action_list: ActionList = []
    currently_carrying = 0

    # 2. Calculate Potential SINGLE-E Round Trips and their Score Value
    # This part now uses the obstacle-aware BFS
    potential_trips_data = []
    for e_loc in initial_energy_locations:
        # Ensure target E is not an obstacle itself (defensive check)
        if grid[e_loc[0]][e_loc[1]] == 'O':
            continue

        path_to_e_actions, cost_to_e = bfs(grid, start_position, e_loc, is_diagonals_allowed)

        if path_to_e_actions is not None: # Path exists considering obstacles
            path_from_e_actions, cost_from_e = bfs(grid, e_loc, start_position, is_diagonals_allowed)

            if path_from_e_actions is not None: # Return path exists considering obstacles
                trip_step_count = cost_to_e + cost_from_e
                trip_action_cost = trip_step_count + 1
                score_penalty = trip_step_count * cost_per_step
                net_score_contribution = 1.0 - score_penalty

                trip_data = {
                    "e_loc": e_loc,
                    "path_to": path_to_e_actions,
                    "path_from": path_from_e_actions,
                    "cost_to": cost_to_e,
                    "cost_from": cost_from_e,
                    "step_count": trip_step_count,
                    "action_cost_no_drop": trip_action_cost,
                    "net_score_contribution": net_score_contribution
                }
                potential_trips_data.append(trip_data)

    # 3. Filter and Sort Trips based on Score Contribution and Cost
    # (Logic identical to previous version)
    viable_trips = []
    if cost_per_step > 0:
        viable_trips = [trip for trip in potential_trips_data if trip["net_score_contribution"] > 0]
        viable_trips.sort(key=lambda x: (-x["net_score_contribution"], x["action_cost_no_drop"]))
    else:
        viable_trips = potential_trips_data
        viable_trips.sort(key=lambda x: x["action_cost_no_drop"])


    # 4. Execute Trips Greedily, considering limits
    # (Logic identical to previous version)
    for trip in viable_trips:
        e_loc = trip["e_loc"]
        cost_to_e = trip["cost_to"]
        cost_from_e = trip["cost_from"]
        path_to_e = trip["path_to"]
        path_from_e = trip["path_from"]
        action_cost_no_drop = trip["action_cost_no_drop"]

        if e_loc in collected_e_locations:
            continue

        actions_needed = action_cost_no_drop
        drop_needed_after_this_trip = (currently_carrying + 1 == carry_limit)
        if drop_needed_after_this_trip:
            actions_needed += 1

        if current_actions + actions_needed <= max_actions:
            final_action_list.extend(path_to_e)
            final_action_list.append("TAKE")
            collected_e_locations.add(e_loc)
            currently_carrying += 1
            final_action_list.extend(path_from_e)
            current_actions += action_cost_no_drop

            if currently_carrying == carry_limit:
                if current_actions + 1 <= max_actions:
                    final_action_list.append("DROP")
                    current_actions += 1
                    currently_carrying = 0
                else:
                    # print(f"WARNING: Could not afford DROP after reaching carry limit at {e_loc}")
                    pass
        else:
            continue

    # 5. Final Drop
    # (Logic identical to previous version)
    if currently_carrying > 0:
        if current_actions + 1 <= max_actions:
            final_action_list.append("DROP")
            current_actions += 1

    # 6. Return
    return final_action_list

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
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == "eight"), carry_limit, cost_per_step)
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