import collections
import heapq # Using heapq might be slightly more efficient for getting cheapest if we regenerate options
from typing import List, Tuple, Dict, Set, Optional

# Define types for clarity
Grid = List[List[str]]
Position = Tuple[int, int]
Action = str
ActionList = List[Action]
PathData = Tuple[Optional[ActionList], int] # (path_actions, cost)

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
    optionally allowing diagonal movement.
    (Code identical to previous version)
    """
    rows = len(grid)
    if rows == 0:
        return None, float('inf')
    cols = len(grid[0])
    if cols == 0:
        return None, float('inf')

    queue = collections.deque([(start_coord, [])]) # Store (coord, path_actions_list)
    visited: Set[Position] = {start_coord}

    possible_moves = ALL_MOVES if is_diagonals_allowed else CARDINAL_MOVES

    while queue:
        current_coord, path_actions = queue.popleft()

        if current_coord == end_coord:
            return path_actions, len(path_actions)

        for action, (dr, dc) in possible_moves.items():
            next_r, next_c = current_coord[0] + dr, current_coord[1] + dc
            next_coord = (next_r, next_c)

            # Check grid bounds
            if 0 <= next_r < rows and 0 <= next_c < cols:
                if next_coord not in visited:
                    visited.add(next_coord)
                    new_path = path_actions + [action]
                    queue.append((next_coord, new_path))

    return None, float('inf')

def find_energy_locations(grid: Grid) -> Set[Position]:
    """Finds all coordinates containing energy 'E'."""
    locations: Set[Position] = set()
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 'E':
                locations.add((r, c))
    return locations

def solve_grid(grid: Grid, start_position: Position, max_actions: int, is_diagonals_allowed: bool, carry_limit: int) -> ActionList:
    """
    Calculates a sequence of actions to collect energy and drop it
    at the start position within the action limit and carry limit,
    using a greedy strategy based on single-E round trips.

    Args:
        grid: The 2D grid.
        start_position: The agent's start (row, col).
        max_actions: The maximum number of actions allowed.
        is_diagonals_allowed: Boolean indicating if diagonal moves are permitted.
        carry_limit: Maximum number of energy tokens the agent can hold.

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
    collected_e_locations: Set[Position] = set() # Track E locations successfully TAKEN
    final_action_list: ActionList = []
    currently_carrying = 0 # Number of E tokens currently held

    # 2. Calculate Potential SINGLE-E Round Trips
    # We still pre-calculate the cost of individual round trips (Start->E->Start)
    # as a basis for our greedy prioritization.
    potential_trips = []
    for e_loc in initial_energy_locations:
        path_to_e_actions, cost_to_e = bfs(grid, start_position, e_loc, is_diagonals_allowed)

        if path_to_e_actions is not None:
            path_from_e_actions, cost_from_e = bfs(grid, e_loc, start_position, is_diagonals_allowed)

            if path_from_e_actions is not None:
                # Base cost: Move there + 1 TAKE + Move back
                trip_cost = cost_to_e + 1 + cost_from_e
                trip_data = (trip_cost, e_loc, path_to_e_actions, path_from_e_actions, cost_to_e, cost_from_e)
                potential_trips.append(trip_data)

    # 3. Sort Trips by base cost (ascending)
    potential_trips.sort(key=lambda x: x[0])

    # 4. Execute Trips Greedily, considering carry_limit
    # We loop as long as we have potential trips AND actions left
    # This needs restructuring slightly - cannot just iterate once.
    # We need to potentially re-evaluate trips or keep trying cheaper ones
    # if a previous attempt failed due to budget constraints changing subtly
    # with forced drops.

    # Let's stick to the simpler loop through sorted trips. If a trip is chosen,
    # it's executed fully (including potential drop) if budget allows.
    trips_considered_indices = set() # Keep track of attempts if needed, simpler: just use collected_e_locations

    # Loop through the pre-calculated, sorted potential trips
    for idx, (base_trip_cost, e_loc, path_to_e, path_from_e, cost_to_e, cost_from_e) in enumerate(potential_trips):

        # Skip if already collected
        if e_loc in collected_e_locations:
            continue

        # Estimate cost for THIS specific trip attempt
        actions_needed = cost_to_e + 1 + cost_from_e # Moves_there + TAKE + Moves_back
        drop_needed_after_this_trip = (currently_carrying + 1 == carry_limit)
        if drop_needed_after_this_trip:
            actions_needed += 1 # Add cost for DROP

        # Check if this sequence (move, take, return, maybe drop) fits budget
        if current_actions + actions_needed <= max_actions:
            # Execute: Move to energy
            final_action_list.extend(path_to_e)
            # current_actions += cost_to_e # Update action count progressively

            # Execute: Take energy
            final_action_list.append("TAKE")
            # current_actions += 1
            collected_e_locations.add(e_loc) # Mark as collected
            currently_carrying += 1

            # Execute: Move back to start
            final_action_list.extend(path_from_e)
            # current_actions += cost_from_e

            # Update total actions used for this sequence *before* potential drop
            current_actions += (cost_to_e + 1 + cost_from_e)

            # Execute: Drop if carry limit reached
            if currently_carrying == carry_limit:
                # Check if the drop action itself fits (should always if previous check passed)
                if current_actions + 1 <= max_actions:
                    final_action_list.append("DROP")
                    current_actions += 1
                    # IMPORTANT: Reset carry count after dropping
                    currently_carrying = 0
                else:
                    # This case should ideally not happen if the initial check was correct.
                    # It means we could collect and return, but not drop.
                    # The collected item is stuck with the agent.
                    # For score purposes, it won't count.
                    # Log or handle this edge case if necessary.
                    # print(f"Warning: Collected E at {e_loc} reaching limit, but couldn't afford final DROP.")
                    pass # Action list is already updated, just don't reset carry count? No, reset is correct logically.

            # If we completed a trip, we might be able to do more.
            # Continue to the next cheapest trip in the sorted list.

        else:
            # This trip (including potential forced drop) is too expensive with remaining actions.
            # Continue to the next cheapest trip, maybe it's shorter and fits.
            continue

    # 5. Final Drop (if needed and possible)
    # After trying all possible trips, if agent is still carrying items.
    if currently_carrying > 0:
        # Check if we have actions left for one last DROP
        if current_actions + 1 <= max_actions:
            # We assume the agent ended the last successful trip segment at start_position
            final_action_list.append("DROP")
            current_actions += 1
            currently_carrying = 0 # Reset for consistency, though game ends here

    # 6. Return the calculated action list
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