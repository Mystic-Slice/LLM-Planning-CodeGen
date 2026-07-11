import collections
from typing import List, Tuple, Dict, Set, Optional

# Define types for clarity
Grid = List[List[str]]
Position = Tuple[int, int]
Action = str
ActionList = List[Action]
PathData = Tuple[Optional[ActionList], int] # (path_actions, cost)

def bfs(grid: Grid, start_coord: Position, end_coord: Position) -> PathData:
    """
    Performs Breadth-First Search to find the shortest path in terms of moves.

    Args:
        grid: The 2D grid.
        start_coord: The starting (row, col) tuple.
        end_coord: The target (row, col) tuple.

    Returns:
        A tuple containing:
        - A list of actions ("UP", "DOWN", "LEFT", "RIGHT") representing the
          shortest path, or None if no path exists.
        - The cost (number of moves) of the path, or float('inf') if no path.
    """
    rows = len(grid)
    if rows == 0:
        return None, float('inf')
    cols = len(grid[0])
    if cols == 0:
        return None, float('inf')

    queue = collections.deque([(start_coord, [])]) # Store (coord, path_actions_list)
    visited: Set[Position] = {start_coord}

    moves: Dict[Action, Tuple[int, int]] = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1),
    }

    while queue:
        current_coord, path_actions = queue.popleft()

        if current_coord == end_coord:
            return path_actions, len(path_actions)

        for action, (dr, dc) in moves.items():
            next_r, next_c = current_coord[0] + dr, current_coord[1] + dc
            next_coord = (next_r, next_c)

            # Check grid bounds
            if 0 <= next_r < rows and 0 <= next_c < cols:
                if next_coord not in visited:
                    visited.add(next_coord)
                    new_path = path_actions + [action]
                    queue.append((next_coord, new_path))

    # Target not reachable
    return None, float('inf')

def find_energy_locations(grid: Grid) -> Set[Position]:
    """Finds all coordinates containing energy 'E'."""
    locations: Set[Position] = set()
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 'E':
                locations.add((r, c))
    return locations

def solve_grid(grid: Grid, start_position: Position, max_actions: int) -> ActionList:
    """
    Calculates the optimal sequence of actions to collect energy and drop it
    at the start position within the action limit using a greedy strategy.

    Args:
        grid: The 2D grid represented as a list of lists of characters.
        start_position: A tuple (row, col) indicating the agent's start.
        max_actions: The maximum number of actions allowed.

    Returns:
        A list of actions ("UP", "DOWN", "LEFT", "RIGHT", "TAKE", "DROP").
    """
    rows = len(grid)
    if rows == 0: return []
    cols = len(grid[0])
    if cols == 0: return []

    # 1. Initialization
    initial_energy_locations = find_energy_locations(grid)
    current_actions = 0
    collected_e_locations: Set[Position] = set() # Track collected E locations
    final_action_list: ActionList = []
    collected_count_overall = 0 # Track if any energy was successfully taken

    # 2. Calculate Potential Trips
    potential_trips = []
    for e_loc in initial_energy_locations:
        # Check if start position itself has energy initially - treat it slightly differently later if needed?
        # For now, standard BFS applies. A trip cost of 1 if start == e_loc.
        path_to_e_actions, cost_to_e = bfs(grid, start_position, e_loc)

        if path_to_e_actions is not None: # Check if reachable
            path_from_e_actions, cost_from_e = bfs(grid, e_loc, start_position)

            if path_from_e_actions is not None: # Check if return path exists
                # Cost: Move there + 1 TAKE + Move back
                trip_cost = cost_to_e + 1 + cost_from_e
                trip_data = (trip_cost, e_loc, path_to_e_actions, path_from_e_actions)
                potential_trips.append(trip_data)

    # 3. Sort Trips by cost (ascending)
    potential_trips.sort(key=lambda x: x[0])

    # 4. Execute Trips Greedily
    for trip_cost, e_loc, path_to_e, path_from_e in potential_trips:

        # Don't collect from the same spot twice
        if e_loc in collected_e_locations:
            continue

        # Check if this trip fits within the remaining action budget
        if current_actions + trip_cost <= max_actions:
            # Execute the trip
            final_action_list.extend(path_to_e)    # Move to E
            final_action_list.append("TAKE")       # Take E
            final_action_list.extend(path_from_e)  # Move back to Start

            # Update state
            current_actions += trip_cost
            collected_e_locations.add(e_loc)
            collected_count_overall += 1
            # Agent is implicitly back at start_position after a full trip

        # If the trip doesn't fit, we just continue to the next (potentially cheaper if available)
        # If it fits, we execute and move on. Since they are sorted, we prioritize cheapest.

    # 5. Final Drop
    # If we collected at least one energy token and have one action left
    if collected_count_overall > 0 and current_actions + 1 <= max_actions:
         # Check if we are indeed at the start position.
         # According to trip logic, we should always end at start after a successful trip.
        final_action_list.append("DROP")
        current_actions += 1 # Optional: track final action count

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
    actions = solve_grid(grid, tuple(start_pos), max_actions)
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
    actions = solve_grid(sample_grid, start_position, max_actions=20)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()
