import collections
import copy
import math

# Helper type for Position
Position = collections.namedtuple("Position", ["r", "c"])

# Helper type for Trip Information Dictionary Keys (for clarity)
# Not strictly necessary but helps readability
TRIP_TARGETS = 'targets'                 # List of target dicts {'pos': Position, 'path_from_previous': list[str]}
TRIP_PATH_BACK = 'path_back_to_start'    # list[str]
TRIP_ACTIONS_COUNT = 'actions'           # int (total actions for the trip)
TRIP_NET_GAIN = 'net_gain'               # float (energy gained - move cost)
TRIP_NUM_TOKENS = 'num_tokens'           # int

# --- Pathfinding (BFS) ---

def get_valid_neighbors(pos: Position, height: int, width: int, is_diagonals_allowed: bool):
    """Gets valid neighboring positions and the action to reach them."""
    neighbors = []
    r, c = pos.r, pos.c
    possible_moves = {
        # Action: (dr, dc)
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1),
    }
    if is_diagonals_allowed:
        possible_moves.update({
            "UPLEFT":   (-1, -1),
            "UPRIGHT":  (-1, 1),
            "DOWNLEFT": (1, -1),
            "DOWNRIGHT":(1, 1),
        })

    for action, (dr, dc) in possible_moves.items():
        nr, nc = r + dr, c + dc
        if 0 <= nr < height and 0 <= nc < width:
             neighbors.append((Position(nr, nc), action))
    return neighbors

def bfs_get_path(grid: list[list[str]], start: Position, end: Position, is_diagonals_allowed: bool):
    """
    Performs Breadth-First Search to find the shortest path.
    Returns a dictionary {'actions': list[str], 'destination': Position} or None if not reachable.
    Obstacles 'O' block paths.
    """
    height = len(grid)
    width = len(grid[0])
    queue = collections.deque([(start, [])])  # Store (position, path_actions_list)
    visited = {start}

    while queue:
        current_pos, path = queue.popleft()

        if current_pos == end:
            return {'actions': path, 'destination': end}

        for neighbor_pos, action in get_valid_neighbors(current_pos, height, width, is_diagonals_allowed):
            # Check if walkable (not visited and not an obstacle)
            if neighbor_pos not in visited and grid[neighbor_pos.r][neighbor_pos.c] != 'O':
                visited.add(neighbor_pos)
                new_path = path + [action]
                queue.append((neighbor_pos, new_path))

    return None # Target not reachable

# --- Trip Evaluation ---

def calculate_trip_metrics(start_pos: Position, targets_info: list[dict], path_back_actions: list[str], cost_per_step: float):
    """Calculates actions, move distance, cost, and net gain for a potential trip."""
    num_tokens = len(targets_info)
    if num_tokens == 0:
        return 0, 0.0 # Actions, Net Gain

    total_move_dist = 0
    # Sum distances between targets
    for target_data in targets_info:
        total_move_dist += len(target_data['path_from_previous'])
    # Add distance from last target back to start
    total_move_dist += len(path_back_actions)

    trip_actions = total_move_dist + num_tokens + 1  # Moves + TAKE actions + 1 DROP action
    trip_move_cost = total_move_dist * cost_per_step
    trip_net_gain = float(num_tokens) - trip_move_cost

    return trip_actions, trip_net_gain


def evaluate_single_token_trip(grid: list[list[str]], start_pos: Position, target_pos: Position, cost_per_step: float, is_diagonals_allowed: bool):
    """Evaluates a simple Start -> E -> Start trip."""
    path_to_target_info = bfs_get_path(grid, start_pos, target_pos, is_diagonals_allowed)
    if path_to_target_info is None:
        return None

    path_from_target_to_start_info = bfs_get_path(grid, target_pos, start_pos, is_diagonals_allowed)
    if path_from_target_to_start_info is None:
        # Should technically be reachable if path_to_target exists, but check anyway
        return None

    path_to_target_actions = path_to_target_info['actions']
    path_back_actions = path_from_target_to_start_info['actions']

    targets_info = [{'pos': target_pos, 'path_from_previous': path_to_target_actions}]
    trip_actions, trip_net_gain = calculate_trip_metrics(start_pos, targets_info, path_back_actions, cost_per_step)

    return {
        TRIP_TARGETS: targets_info,
        TRIP_PATH_BACK: path_back_actions,
        TRIP_ACTIONS_COUNT: trip_actions,
        TRIP_NET_GAIN: trip_net_gain,
        TRIP_NUM_TOKENS: 1
    }

def try_extend_trip(grid: list[list[str]], start_pos: Position, base_trip: dict,
                      all_energy_locations: set[Position], actions_remaining: int, carry_limit: int,
                      cost_per_step: float, is_diagonals_allowed: bool):
    """
    Tries to greedily add more tokens to a base trip, up to carry_limit,
    optimizing for overall trip efficiency.
    """
    current_best_trip = base_trip
    visited_targets_pos = {t['pos'] for t in base_trip[TRIP_TARGETS]}

    for _ in range(current_best_trip[TRIP_NUM_TOKENS], carry_limit): # Try adding tokens until limit
        last_target_pos = current_best_trip[TRIP_TARGETS][-1]['pos']
        best_next_token_info = None
        best_potential_trip_efficiency = -1.0 # Efficiency of the *new overall trip*

        # --- Find the best *next* token to add ---
        for next_e_pos in all_energy_locations:
            if next_e_pos not in visited_targets_pos:
                # Path from the last target of the current best trip to the potential next target
                path_last_to_next_info = bfs_get_path(grid, last_target_pos, next_e_pos, is_diagonals_allowed)
                if path_last_to_next_info is None:
                    continue

                # Path from the potential next target back to the start
                path_next_to_start_info = bfs_get_path(grid, next_e_pos, start_pos, is_diagonals_allowed)
                if path_next_to_start_info is None:
                    continue

                # --- Construct the potential new trip details ---
                new_targets_list = current_best_trip[TRIP_TARGETS] + \
                                   [{'pos': next_e_pos, 'path_from_previous': path_last_to_next_info['actions']}]
                new_path_back_actions = path_next_to_start_info['actions']

                # Calculate metrics for this potential extended trip
                new_trip_actions, new_trip_net_gain = calculate_trip_metrics(
                    start_pos, new_targets_list, new_path_back_actions, cost_per_step
                )

                # Check feasibility
                if new_trip_actions <= actions_remaining and new_trip_net_gain > 0:
                    new_efficiency = new_trip_net_gain / new_trip_actions if new_trip_actions > 0 else 0

                    # Is this the best way to add *one more token* found so far?
                    if new_efficiency > best_potential_trip_efficiency:
                        best_potential_trip_efficiency = new_efficiency
                        # Store the details needed to potentially adopt this extension
                        best_next_token_info = {
                            'next_pos': next_e_pos,
                            'potential_new_trip': {
                                TRIP_TARGETS: new_targets_list,
                                TRIP_PATH_BACK: new_path_back_actions,
                                TRIP_ACTIONS_COUNT: new_trip_actions,
                                TRIP_NET_GAIN: new_trip_net_gain,
                                TRIP_NUM_TOKENS: current_best_trip[TRIP_NUM_TOKENS] + 1
                            }
                        }
        # --- Finished checking all possible next tokens for this step ---

        if best_next_token_info is not None:
            # Compare the efficiency of the best *extended* trip with the current best trip
            current_best_efficiency = current_best_trip[TRIP_NET_GAIN] / current_best_trip[TRIP_ACTIONS_COUNT] \
                                       if current_best_trip[TRIP_ACTIONS_COUNT] > 0 else 0.0

            if best_potential_trip_efficiency > current_best_efficiency:
                 # Adopt the extension: update the current best trip for the *next* iteration
                 current_best_trip = best_next_token_info['potential_new_trip']
                 visited_targets_pos.add(best_next_token_info['next_pos'])
            else:
                 # Adding the best possible next token didn't improve overall efficiency, stop extending
                 break
        else:
            # No beneficial or reachable token found to add
            break

    # Return the best trip found (could be the original base_trip or an extended one)
    return current_best_trip


# --- Main Trip Finding Logic ---

def find_best_trip(grid: list[list[str]], start_pos: Position, actions_remaining: int,
                   carry_limit: int, cost_per_step: float, is_diagonals_allowed: bool):
    """
    Finds the best feasible trip (single or multi-token) to execute next.
    Returns the trip dictionary or None.
    """
    height = len(grid)
    width = len(grid[0])
    all_energy_locations = set()
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 'E':
                all_energy_locations.add(Position(r, c))

    if not all_energy_locations:
        return None # No energy left

    candidate_trips = []

    # 1. Evaluate all single-token trips
    for e_pos in all_energy_locations:
        trip_info = evaluate_single_token_trip(grid, start_pos, e_pos, cost_per_step, is_diagonals_allowed)
        if trip_info is not None and trip_info[TRIP_ACTIONS_COUNT] <= actions_remaining and trip_info[TRIP_NET_GAIN] > 0:
            candidate_trips.append(trip_info)

    # 2. Try to extend single-token trips if carry_limit allows
    if carry_limit > 1 and candidate_trips:
        # Sort single trips by efficiency to start extensions from promising ones
        # Handle division by zero for efficiency calculation if actions is 0 (shouldn't happen for valid trips)
        candidate_trips.sort(key=lambda t: t[TRIP_NET_GAIN] / t[TRIP_ACTIONS_COUNT] if t[TRIP_ACTIONS_COUNT] > 0 else 0.0,
                         reverse=True)

        extended_trip_candidates = []
        # Keep track of base trips already successfully extended to avoid re-adding simple versions
        processed_base_targets = set()

        for base_trip in candidate_trips:
            # Don't try extending if this single target was part of a already found longer successful trip
            base_target_pos = base_trip[TRIP_TARGETS][0]['pos']
            if base_target_pos in processed_base_targets:
                continue

            extended_trip = try_extend_trip(
                grid, start_pos, base_trip, all_energy_locations,
                actions_remaining, carry_limit, cost_per_step, is_diagonals_allowed
            )

            # If extension resulted in a multi-token trip (and is still valid)
            if extended_trip[TRIP_NUM_TOKENS] > 1:
                 # Basic check if still valid after potential extension logic
                 if extended_trip[TRIP_ACTIONS_COUNT] <= actions_remaining and extended_trip[TRIP_NET_GAIN] > 0:
                    extended_trip_candidates.append(extended_trip)
                    # Mark all targets in this successful multi-trip as processed
                    for target_info in extended_trip[TRIP_TARGETS]:
                        processed_base_targets.add(target_info['pos'])
                # else: the extension made it invalid, discard

        # Add the successful extended trips to the list of candidates
        # The original single trips are already in candidate_trips
        candidate_trips.extend(extended_trip_candidates)

    # 3. Select the best overall feasible trip from all candidates (single and multi)
    best_overall_trip = None
    max_efficiency = -1.0 # Use -1 to ensure any positive efficiency trip is chosen initially

    # Use a set to store unique trip identifiers (e.g., tuple of target positions) to avoid duplicates
    # This is important if TRY_EXTEND_TRIP could return the original single trip sometimes
    # A simple way is to use frozenset of target positions as key
    evaluated_trip_configs = set()

    for trip in candidate_trips:
        # Check feasibility again (should be okay, but belt-and-suspenders)
        if trip[TRIP_ACTIONS_COUNT] <= actions_remaining and trip[TRIP_NET_GAIN] > 0:
             # Create a unique identifier for this trip's target set
             target_positions = frozenset(t['pos'] for t in trip[TRIP_TARGETS])
             if target_positions in evaluated_trip_configs:
                 continue # Already evaluated an equivalent trip route possibly via different extension path
             evaluated_trip_configs.add(target_positions)

             # Calculate efficiency
             efficiency = trip[TRIP_NET_GAIN] / trip[TRIP_ACTIONS_COUNT] if trip[TRIP_ACTIONS_COUNT] > 0 else 0.0

             if efficiency > max_efficiency:
                 max_efficiency = efficiency
                 best_overall_trip = trip

    return best_overall_trip


# --- Main Solver Function ---

def solve_grid(grid: list[list[str]], start_pos_tuple: tuple[int, int], carry_limit: int,
          cost_per_step: float, is_diagonals_allowed: bool, max_actions: int):
    """
    Solves the energy collection game using the Iterative Best Trip strategy.

    Args:
        grid: The 2D grid (list of lists of strings: ' ', 'E', 'A', 'O').
        start_pos_tuple: The starting (row, col) of the agent 'A'.
        carry_limit: Maximum energy tokens the agent can hold.
        cost_per_step: Energy cost deducted for each move action.
        is_diagonals_allowed: Boolean indicating if diagonal moves are allowed.
        max_actions: Maximum number of actions allowed.

    Returns:
        A list of action strings (e.g., ["UP", "TAKE", "DOWN", "DROP"]).
    """
    actions_list = []
    actions_remaining = max_actions
    start_pos = Position(*start_pos_tuple) # Convert tuple to namedtuple

    # Create a mutable copy of the grid to track changes ('E' removal)
    grid_state = [list(row) for row in grid] # Ensure it's a list of lists

    # We don't need to track current_pos between trips, as each trip starts from start_pos
    # total_energy_at_start is implicitly tracked by the algorithm's goal (max score)

    while actions_remaining > 0:
        # Find the best trip to execute from the current grid state and remaining actions
        best_trip = find_best_trip(
            grid_state, start_pos, actions_remaining,
            carry_limit, cost_per_step, is_diagonals_allowed
        )

        # If no beneficial trip can be found or completed within remaining actions
        if best_trip is None:
            # print("No further beneficial trips found or possible.") # Optional debug
            break

        # --- Execute the best found trip ---
        # print(f"Executing trip: {best_trip[TRIP_NUM_TOKENS]} tokens, Actions: {best_trip[TRIP_ACTIONS_COUNT]}, Net Gain: {best_trip[TRIP_NET_GAIN]:.2f}") # Optional debug

        current_trip_action_count = 0 # Track actions used in *this* trip execution

        # 1. Move to targets and collect
        for target_info in best_trip[TRIP_TARGETS]:
            # Append move actions to reach this target
            path_to_target = target_info['path_from_previous']
            actions_list.extend(path_to_target)
            current_trip_action_count += len(path_to_target)

            # Append TAKE action
            actions_list.append("TAKE")
            current_trip_action_count += 1

            # Update grid state: remove the energy token
            target_pos = target_info['pos']
            if grid_state[target_pos.r][target_pos.c] == 'E':
                 grid_state[target_pos.r][target_pos.c] = ' ' # Mark as empty
            else:
                 # This shouldn't happen if logic is correct, but indicates a potential issue
                 print(f"Warning: Tried to TAKE from non-Energy cell {target_pos}")
                 pass # Continue anyway, maybe grid state was inconsistent

        # 2. Move back to start from the last target
        path_to_start_actions = best_trip[TRIP_PATH_BACK]
        actions_list.extend(path_to_start_actions)
        current_trip_action_count += len(path_to_start_actions)

        # 3. Drop energy at start
        actions_list.append("DROP")
        current_trip_action_count += 1

        # Ensure logic consistency
        if current_trip_action_count != best_trip[TRIP_ACTIONS_COUNT]:
             print(f"Warning: Action count mismatch! Calculated={best_trip[TRIP_ACTIONS_COUNT]}, Executed={current_trip_action_count}")
             # Use the executed count for safety, though it signals a potential bug in calculation/execution phase
             actions_remaining -= current_trip_action_count
        else:
             actions_remaining -= best_trip[TRIP_ACTIONS_COUNT]

        # Agent is conceptually back at start_pos, ready for the next FIND_BEST_TRIP call

        # print(f"Trip complete. Actions remaining: {actions_remaining}") # Optional debug

    # --- Simulation finished ---
    # print(f"Final actions list length: {len(actions_list)}") # Optional debug

    # Ensure we don't exceed max_actions due to potential off-by-one or edge cases
    return actions_list[:max_actions]

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