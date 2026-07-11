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
    Performs Breadth-First Search to find the shortest path in terms of moves.
    (Code identical to previous version)
    """
    rows = len(grid)
    if rows == 0: return None, float('inf')
    cols = len(grid[0])
    if cols == 0: return None, float('inf')
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
            if 0 <= next_r < rows and 0 <= next_c < cols:
                if next_coord not in visited:
                    visited.add(next_coord)
                    new_path = path_actions + [action]
                    queue.append((next_coord, new_path))
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
    respecting action limit and carry limit. Uses a greedy strategy based on score contribution.

    Args:
        grid: The 2D grid.
        start_position: The agent's start (row, col).
        max_actions: The maximum number of total actions (move, take, drop) allowed.
        is_diagonals_allowed: Boolean indicating if diagonal moves are permitted.
        carry_limit: Maximum number of energy tokens the agent can hold.
        cost_per_step: Penalty subtracted from score for each movement action taken.

    Returns:
        A list of actions.
    """
    rows = len(grid)
    if rows == 0: return []
    cols = len(grid[0])
    if cols == 0: return []
    if carry_limit <= 0: return [] # Cannot carry anything

    # 1. Initialization
    initial_energy_locations = find_energy_locations(grid)
    current_actions = 0
    collected_e_locations: Set[Position] = set()
    final_action_list: ActionList = []
    currently_carrying = 0

    # --- Strategy Adjustment: Focusing on Score Contribution ---

    # 2. Calculate Potential SINGLE-E Round Trips and their Score Value
    potential_trips_data = []
    for e_loc in initial_energy_locations:
        path_to_e_actions, cost_to_e = bfs(grid, start_position, e_loc, is_diagonals_allowed)

        if path_to_e_actions is not None:
            path_from_e_actions, cost_from_e = bfs(grid, e_loc, start_position, is_diagonals_allowed)

            if path_from_e_actions is not None:
                # Calculate costs for this trip
                trip_step_count = cost_to_e + cost_from_e # Total movement steps
                trip_action_cost = trip_step_count + 1   # Steps + 1 TAKE action
                score_penalty = trip_step_count * cost_per_step
                # Net score gain from THIS trip, assuming it's completed (1 E gained)
                net_score_contribution = 1.0 - score_penalty

                trip_data = {
                    "e_loc": e_loc,
                    "path_to": path_to_e_actions,
                    "path_from": path_from_e_actions,
                    "cost_to": cost_to_e,
                    "cost_from": cost_from_e,
                    "step_count": trip_step_count,
                    "action_cost_no_drop": trip_action_cost, # Base cost without forced drop
                    "net_score_contribution": net_score_contribution
                }
                potential_trips_data.append(trip_data)

    # 3. Filter and Sort Trips based on Score Contribution and Cost
    viable_trips = []
    if cost_per_step > 0:
        # Only consider trips that actually increase the score
        viable_trips = [trip for trip in potential_trips_data if trip["net_score_contribution"] > 0]
        # Sort: Highest score contribution first. If tied, prefer lower action cost.
        viable_trips.sort(key=lambda x: (-x["net_score_contribution"], x["action_cost_no_drop"]))
    else: # cost_per_step is 0 or negative (steps are free or beneficial)
        # All valid trips are viable. Prioritize by lowest action cost to maximize # of trips.
        viable_trips = potential_trips_data
        viable_trips.sort(key=lambda x: x["action_cost_no_drop"])


    # 4. Execute Trips Greedily (based on the new sorting), considering limits
    for trip in viable_trips:
        e_loc = trip["e_loc"]
        cost_to_e = trip["cost_to"]
        cost_from_e = trip["cost_from"]
        path_to_e = trip["path_to"]
        path_from_e = trip["path_from"]
        action_cost_no_drop = trip["action_cost_no_drop"] # Steps + TAKE

        # Skip if already collected
        if e_loc in collected_e_locations:
            continue

        # Estimate total actions needed for THIS attempt, including potential drop
        actions_needed = action_cost_no_drop # Moves_there + TAKE + Moves_back
        drop_needed_after_this_trip = (currently_carrying + 1 == carry_limit)
        if drop_needed_after_this_trip:
            actions_needed += 1 # Add cost for the mandatory DROP at the end

        # Check if this sequence fits the action budget
        if current_actions + actions_needed <= max_actions:
            # Execute: Move to energy
            final_action_list.extend(path_to_e)

            # Execute: Take energy
            final_action_list.append("TAKE")
            collected_e_locations.add(e_loc)
            currently_carrying += 1

            # Execute: Move back to start
            final_action_list.extend(path_from_e)

            # Update total actions used for this sequence *before* potential drop
            current_actions += action_cost_no_drop

            # Execute: Drop if carry limit reached
            if currently_carrying == carry_limit:
                 # Redundant check? Should always fit if initial check passed. Check anyway.
                if current_actions + 1 <= max_actions:
                    final_action_list.append("DROP")
                    current_actions += 1
                    currently_carrying = 0 # Reset carry count
                else:
                    # Logically shouldn't happen if the initial check `current_actions + actions_needed <= max_actions` was correct
                    # print(f"WARNING: Could not afford DROP after reaching carry limit at {e_loc}")
                    pass # If it somehow occurs, the energy remains held but not dropped.

        else:
            # This trip is too expensive w.r.t action budget.
            # Since we sorted by score contribution (or action cost if steps are free),
            # continue to check the next best trip.
            continue

    # 5. Final Drop (if needed and possible)
    # After trying all viable/affordable trips, drop remaining E if possible.
    if currently_carrying > 0:
        if current_actions + 1 <= max_actions:
            # Assume agent ended last successful move segment at start_position
            final_action_list.append("DROP")
            current_actions += 1
            # No need to reset currently_carrying as the process ends

    # 6. Return the calculated action list
    # The score calculation (E_dropped - steps*cost) happens outside based on simulating these actions.
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