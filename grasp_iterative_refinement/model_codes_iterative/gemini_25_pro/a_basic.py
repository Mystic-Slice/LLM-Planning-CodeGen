import collections
import math

# --- Helper Functions ---

def is_valid(coord, grid_height, grid_width, grid):
    """Checks if a coordinate is within bounds and not an obstacle."""
    r, c = coord
    return 0 <= r < grid_height and 0 <= c < grid_width and grid[r][c] != 'O'

def get_neighbors(coord, grid_height, grid_width, grid, move_directions):
    """Gets valid neighboring coordinates based on move directions."""
    r, c = coord
    potential_moves = []
    # 4 directions
    potential_moves.extend([
        ((r - 1, c), "UP"),
        ((r + 1, c), "DOWN"),
        ((r, c - 1), "LEFT"),
        ((r, c + 1), "RIGHT"),
    ])
    # 8 directions (add diagonals)
    if move_directions == 8:
        potential_moves.extend([
            ((r - 1, c - 1), "UPLEFT"),
            ((r - 1, c + 1), "UPRIGHT"),
            ((r + 1, c - 1), "DOWNLEFT"),
            ((r + 1, c + 1), "DOWNRIGHT"),
        ])

    valid_neighbors = []
    for neighbor_coord, move_name in potential_moves:
        if is_valid(neighbor_coord, grid_height, grid_width, grid):
            valid_neighbors.append((neighbor_coord, move_name))
    return valid_neighbors

def update_position(pos, move):
    """Calculates the new position based on a move action."""
    r, c = pos
    if move == "UP": return (r - 1, c)
    if move == "DOWN": return (r + 1, c)
    if move == "LEFT": return (r, c - 1)
    if move == "RIGHT": return (r, c + 1)
    if move == "UPLEFT": return (r - 1, c - 1)
    if move == "UPRIGHT": return (r - 1, c + 1)
    if move == "DOWNLEFT": return (r + 1, c - 1)
    if move == "DOWNRIGHT": return (r + 1, c + 1)
    return pos # Should not happen if move is valid

def find_path_bfs(from_coord, to_coord, grid, move_directions, move_cost):
    """
    Finds the shortest path using Breadth-First Search (BFS).
    Returns (list_of_moves, total_cost) or (None, float('inf')).
    """
    grid_height = len(grid)
    grid_width = len(grid[0])
    queue = collections.deque([(from_coord, [])])  # (coordinate, path_list_of_moves)
    visited = {from_coord}

    while queue:
        current_coord, path = queue.popleft()

        if current_coord == to_coord:
            return path, len(path) * move_cost

        for neighbor_coord, move_name in get_neighbors(current_coord, grid_height, grid_width, grid, move_directions):
            if neighbor_coord not in visited:
                visited.add(neighbor_coord)
                new_path = path + [move_name]
                queue.append((neighbor_coord, new_path))

    return None, float('inf') # No path found

# --- Main Solver Function ---

def solve_energy_game(grid, start_pos, max_actions, capacity, move_cost=1, move_directions=4):
    """
    Solves the energy collection game.

    Args:
        grid (2-D list): The game grid represented as a 2D list of strings.
        max_actions (int): Maximum number of actions allowed.
        capacity (int): Maximum energy tokens the agent can carry.
        move_cost (int): Cost per move action (default 1).
        move_directions (int): 4 or 8 directional movement (default 4).

    Returns:
        list: A list of action strings performed by the agent.
              Returns an empty list if the input grid is invalid.
    """
    # --- Grid Parsing and Initialization ---
    # try:
    #     grid_lines = grid_str.strip().split('\n')[1::2] # Skip separators, take rows
    #     grid = [list(line[1::4]) for line in grid_lines] # Extract cells
    #     grid_height = len(grid)
    #     grid_width = len(grid[0])
    # except (IndexError, TypeError):
    #     print("Error: Invalid grid string format.")
    #     return []
    
    grid_height = len(grid)
    grid_width = len(grid[0]) if grid else 0


    start_pos = None
    initial_energy_coords = set()
    for r in range(grid_height):
        for c in range(grid_width):
            if grid[r][c] == 'A':
                start_pos = (r, c)
                grid[r][c] = ' ' # Agent location is not a permanent fixture
            elif grid[r][c] == 'E':
                 initial_energy_coords.add((r, c))

    if start_pos is None:
        print("Error: Agent 'A' not found in the grid.")
        return []

    current_pos = start_pos
    remaining_actions = max_actions
    current_holding = 0
    # Score only counts energy at the start location (initially or dropped)
    score = 1 if (start_pos in initial_energy_coords) else 0
    action_list = []
    # Use a copy of coordinates to track remaining energy
    energy_coords = initial_energy_coords.copy()
    if start_pos in energy_coords:
        energy_coords.remove(start_pos) # Don't try to collect from start location initially


    # print(f"Starting Game: Max Actions={max_actions}, Capacity={capacity}, Start={start_pos}")
    # print(f"Initial Energy Count: {len(initial_energy_coords)}")
    # --- Main Loop ---
    while remaining_actions > 0:
        best_trip_plan = None
        max_trip_value = -1 # Using -1 to ensure any valid trip is better

        # --- Evaluate Potential Trips ---
        potential_targets = list(energy_coords) # Convert set to list for iteration

        for e_coord in potential_targets:
            # Check capacity *before* calculating paths
            if current_holding >= capacity:
                continue

            # 1. Calculate cost from current position to energy E
            path_to_e, cost_to_e = find_path_bfs(current_pos, e_coord, grid, move_directions, move_cost)

            if path_to_e is not None:
                # 2. Calculate cost from energy E back to start position
                path_to_start, cost_to_start = find_path_bfs(e_coord, start_pos, grid, move_directions, move_cost)

                if path_to_start is not None:
                    actions_take = 1 # Cost of TAKE action
                    actions_drop = 1 # Cost of DROP action
                    num_e_collected = 1 # Evaluating single E trips here
                    total_trip_actions = cost_to_e + actions_take + cost_to_start + actions_drop

                    # 3. Check Feasibility (Actions)
                    if total_trip_actions <= remaining_actions:
                        # Simple value: E's collected per action. Higher is better.
                        # Add small epsilon to avoid division by zero if total_actions is 0 (shouldn't happen here)
                        trip_value = num_e_collected / (total_trip_actions + 1e-9)

                        # 4. Select Best Feasible Trip
                        if trip_value > max_trip_value:
                            max_trip_value = trip_value
                            best_trip_plan = {
                                "target_e": e_coord,
                                "path_to_target": path_to_e,
                                "cost_to_target": cost_to_e,
                                "path_to_start": path_to_start,
                                "cost_to_start": cost_to_start,
                                "total_actions": total_trip_actions,
                                "collect_count": num_e_collected
                            }
                            # print(f"  Found potential trip to {e_coord}: Cost={total_trip_actions}, Value={trip_value:.2f}")


        # --- Execute Best Trip or Finish ---
        if best_trip_plan:
            # print(f"Executing trip to {best_trip_plan['target_e']} (Cost: {best_trip_plan['total_actions']}, Current Actions: {remaining_actions})")
            target_coord = best_trip_plan['target_e']

            # Move to Target E
            for move in best_trip_plan['path_to_target']:
                if remaining_actions < move_cost: break # Cannot afford next move
                action_list.append(move)
                current_pos = update_position(current_pos, move)
                remaining_actions -= move_cost
            if remaining_actions < move_cost and current_pos != target_coord: # Check if ran out before reaching target
                #  print("  Ran out of actions before reaching target.")
                 break # Exit main loop if cannot complete action sequence

            # TAKE Action (Check actions first)
            if remaining_actions >= 1 and current_pos == target_coord and target_coord in energy_coords:
                action_list.append("TAKE")
                remaining_actions -= 1
                current_holding += 1
                energy_coords.remove(target_coord) # Remove E from available targets
                # print(f"  TAKE at {target_coord}. Holding: {current_holding}. Actions left: {remaining_actions}")

                # Move back to Start
                for move in best_trip_plan['path_to_start']:
                    if remaining_actions < move_cost: break # Cannot afford next move
                    action_list.append(move)
                    current_pos = update_position(current_pos, move)
                    remaining_actions -= move_cost
                if remaining_actions < move_cost and current_pos != start_pos: # Check if ran out before reaching start
                    # print("  Ran out of actions before returning to start.")
                    break # Exit main loop

                # DROP Action (Check actions and position first)
                if remaining_actions >= 1 and current_pos == start_pos and current_holding > 0:
                    action_list.append("DROP")
                    remaining_actions -= 1
                    score += current_holding # SCORE UPDATED HERE
                    # print(f"  DROP at {start_pos}. Score: {score}. Actions left: {remaining_actions}")
                    current_holding = 0
                else:
                    # Could happen if ran out of actions exactly when arriving at start, or wasn't at start
                    #  if current_pos != start_pos: print(f"  Warning: Arrived somewhere else ({current_pos}) instead of start after return path.")
                    #  if current_holding > 0: print(f"  Warning: Failed to DROP {current_holding} energy.")
                     # Continue loop if actions remain, but energy wasn't dropped.
                     # Or break if no actions left
                     if remaining_actions <= 0:
                         break


            else:
                 # Failed TAKE (no actions, or not at target, or E already gone somehow)
                #  if remaining_actions < 1: print(f"  Cannot TAKE at {target_coord}, no actions left.")
                #  elif current_pos != target_coord: print(f"  Cannot TAKE, not at target {target_coord} (at {current_pos}).")
                #  elif target_coord not in energy_coords: print(f"  Cannot TAKE at {target_coord}, E is already gone.")
                 break # Critical failure in trip execution


        else:
            # No feasible trips found with remaining actions
            # print("No more feasible trips found.")
            break # Exit main loop

    # --- Final Return if Holding Energy ---
    if current_holding > 0 and remaining_actions > 0 and current_pos != start_pos:
        # print(f"Attempting final return to base with {current_holding} energy (Actions left: {remaining_actions})")
        path_home, cost_home = find_path_bfs(current_pos, start_pos, grid, move_directions, move_cost)

        if path_home is not None and (cost_home + 1) <= remaining_actions: # +1 for DROP
            # print(f"  Executing final return path (Cost: {cost_home + 1})")
             # Execute return path
            for move in path_home:
                if remaining_actions < move_cost: break
                action_list.append(move)
                current_pos = update_position(current_pos, move)
                remaining_actions -= move_cost

            # Final Drop (Check position and actions again)
            if remaining_actions >= 1 and current_pos == start_pos:
                action_list.append("DROP")
                remaining_actions -= 1
                score += current_holding
                # print(f"  Final DROP successful. Final Score: {score}. Actions left: {remaining_actions}")
                current_holding = 0
            else:
                #  print(f"  Final return failed (Actions left: {remaining_actions}, Position: {current_pos}). Energy lost.")
                pass
        else:
            # print(f"  Cannot execute final return (Not enough actions or no path).")
            pass
            
    elif current_holding > 0 and current_pos == start_pos and remaining_actions >=1 :
        # If ended loop at start but still holding, perform final drop if possible
        # print(f"Performing final DROP at start (Actions left: {remaining_actions})")
        action_list.append("DROP")
        remaining_actions -= 1
        score += current_holding
        # print(f"  Final DROP successful. Final Score: {score}. Actions left: {remaining_actions}")
        current_holding = 0


    # print(f"--- Game Over ---")
    # print(f"Final Position: {current_pos}")
    # print(f"Final Actions Remaining: {remaining_actions}")
    # print(f"Final Energy Held: {current_holding}")
    # print(f"Final Score (Energy at {start_pos}): {score}")
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
    actions = solve_energy_game(
        grid,
        start_pos=start_pos,
        max_actions=max_actions,
        capacity=carry_limit,
        move_cost=cost_per_step,
        move_directions=4 if movement_type == "four" else 8
    )
    return actions

def main():
    # --- Example Usage ---
    sample_grid_str = """
        0   1   2   3   4   5   6   7   8   9   10
    +---+---+---+---+---+---+---+---+---+---+---+
    0|   |   | E | E | E | E |   | E | E | E | E |
    +---+---+---+---+---+---+---+---+---+---+---+
    1|   |   | E | E | E |   |   |   |   | E |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    2| E |   |   |   | E |   |   | E | E |   |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    3| E | E | E | E |   | E | E | E |   | E | E |
    +---+---+---+---+---+---+---+---+---+---+---+
    4|   | E |   | A | E |   | E |   | E | E |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    5| E |   | E |   | E | E |   | E |   | E |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    6| E |   | E |   |   |   |   | E | E | E | E |
    +---+---+---+---+---+---+---+---+---+---+---+
    7| E | E |   |   |   |   | E |   | E | E |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    8| E |   | E | E | E |   |   |   | E | E |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    9|   |   | E | E | E |   | E |   |   |   |   |
    +---+---+---+---+---+---+---+---+---+---+---+
    10|   | E | E |   | E | E |   | E |   | E | E |
    +---+---+---+---+---+---+---+---+---+---+---+
    """

    # --- Run the simulation ---
    max_total_actions = 20
    agent_capacity = 3
    agent_move_cost = 1 # Cost per step
    agent_move_directions = 4 # Or 8

    grid, agent_pos, energy_positions = parse_grid(sample_grid_str)

    action_sequence = solve_energy_game(
        grid,
        start_pos=agent_pos,
        max_actions=max_total_actions,
        capacity=agent_capacity,
        move_cost=agent_move_cost,
        move_directions=agent_move_directions
    )

    print("\nGenerated Action Sequence:")
    print(action_sequence)
    print(f"\nTotal Actions Taken: {len(action_sequence)}")

    # Example with obstacle
    obstacle_grid_str = """
        0   1   2   3   4
    +---+---+---+---+---+
    0| A |   | E |   |   |
    +---+---+---+---+---+
    1|   | O | O | O | E |
    +---+---+---+---+---+
    2| E |   | E |   |   |
    +---+---+---+---+---+
    """
    grid, agent_pos, energy_positions = parse_grid(obstacle_grid_str)
    print("\n--- Running Obstacle Example ---")
    action_sequence_obstacle = solve_energy_game(
        grid,
        start_pos=agent_pos,
        max_actions=20,
        capacity=2,
        move_cost=1,
        move_directions=4
    )
    print("\nGenerated Action Sequence (Obstacle):")
    print(action_sequence_obstacle)
    print(f"\nTotal Actions Taken: {len(action_sequence_obstacle)}")

if __name__ == "__main__":
    main()