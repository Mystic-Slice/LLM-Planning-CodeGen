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
    return pos

def find_path_bfs(from_coord, to_coord, grid, move_directions):
    """
    Finds the shortest path using Breadth-First Search (BFS).
    Returns (list_of_move_names, num_move_actions) or (None, float('inf')).
    Each move action costs 1.
    """
    grid_height = len(grid)
    grid_width = len(grid[0])
    queue = collections.deque([(from_coord, [])])  # (coordinate, path_list_of_moves)
    visited = {from_coord}

    while queue:
        current_coord, path_moves = queue.popleft()

        if current_coord == to_coord:
            return path_moves, len(path_moves) # Number of moves = number of actions

        for neighbor_coord, move_name in get_neighbors(current_coord, grid_height, grid_width, grid, move_directions):
            if neighbor_coord not in visited:
                visited.add(neighbor_coord)
                new_path_moves = path_moves + [move_name]
                queue.append((neighbor_coord, new_path_moves))

    return None, float('inf') # No path found

# --- Main Solver Function ---

def solve_grid(grid, start_pos_param, max_actions, capacity, cost_per_step=1, move_directions=4):
    """
    Solves the energy collection game.

    Args:
        grid (2-D list): The game grid represented as a 2D list of strings.
        start_pos_param (tuple): The (row, col) starting position of the agent.
                                (Note: Agent 'A' in grid is also located for robustness)
        max_actions (int): Maximum number of actions allowed.
        capacity (int): Maximum energy tokens the agent can carry.
        cost_per_step (int): Scoring penalty per move action (default 1).
        move_directions (int): 4 or 8 directional movement (default 4).

    Returns:
        list: A list of action strings performed by the agent.
    """
    if not grid or not grid[0]:
        # print("Error: Empty or invalid grid.")
        return []
        
    grid_height = len(grid)
    grid_width = len(grid[0])

    # Find agent 'A' and initial energy 'E'
    # Allow start_pos_param to be the primary, but find 'A' if start_pos_param is not where 'A' is.
    # This code prioritizes 'A' in grid if it exists.
    agent_actual_start_pos = None
    initial_energy_coords = set()
    grid_copy = [list(row) for row in grid] # Work on a copy for modifications like 'A' -> ' '

    for r in range(grid_height):
        for c in range(grid_width):
            if grid_copy[r][c] == 'A':
                if agent_actual_start_pos is not None:
                    # print("Warning: Multiple 'A's found. Using the first one.")
                    pass
                else:
                    agent_actual_start_pos = (r, c)
                grid_copy[r][c] = ' ' # Agent location is not a permanent fixture
            elif grid_copy[r][c] == 'E':
                 initial_energy_coords.add((r, c))

    if agent_actual_start_pos is None:
        # If 'A' not in grid, trust start_pos_param
        if is_valid(start_pos_param, grid_height, grid_width, grid_copy): # check against original grid state
            agent_actual_start_pos = start_pos_param
            if grid_copy[start_pos_param[0]][start_pos_param[1]] == 'O': # Should not happen if is_valid
                #  print("Error: start_pos_param is an obstacle.")
                 return []
            # If start_pos_param was 'E', it's handled below by initial_energy_coords
            grid_copy[start_pos_param[0]][start_pos_param[1]] = ' ' # Treat start like empty after agent moves
        else:
            # print("Error: Agent 'A' not found in grid and start_pos_param is invalid.")
            return []
    
    start_pos = agent_actual_start_pos


    current_pos = start_pos
    remaining_actions = max_actions
    current_holding = 0
    # Score tracks gross energy dropped at base.
    score = 0
    if start_pos in initial_energy_coords:
        score = 1 # Energy initially at the start counts.
        initial_energy_coords.remove(start_pos) # Don't try to collect it.

    action_list = []
    # Use a copy of coordinates to track remaining energy available for collection
    energy_coords_on_grid = initial_energy_coords.copy()

    # print(f"Starting Game: Max Actions={max_actions}, Capacity={capacity}, Start={start_pos}, CostPerStep={cost_per_step}")
    # print(f"Initial Energy (excluding start): {len(energy_coords_on_grid)}, Score from start: {score}")

    # --- Main Loop ---
    while remaining_actions > 0:
        # If at base and holding energy, DROP it first
        if current_holding > 0 and current_pos == start_pos and remaining_actions >= 1:
            action_list.append("DROP")
            remaining_actions -= 1
            score += current_holding
            # print(f"  Pre-emptive DROP at {start_pos}. Holding: 0. Score: {score}. Actions left: {remaining_actions}")
            current_holding = 0
            if remaining_actions <= 0: break
        
        # if current_holding >= capacity: # Cannot pick up more, must return to base
        #      if current_pos != start_pos:
        #         print(f"  Capacity full ({current_holding}), must return to base from {current_pos}.")
        #         # This case will be handled by "No feasible trips" -> final return logic
        #      else: # Already at base and full, implies a drop should have happened or will happen
        #         pass # Drop should occur via above check or if loop breaks


        best_trip_plan = None
        # Maximize (net_energy_gain / total_actions). Net_energy can be negative.
        # Initialize to a very small number, or 0 if only positive net gain trips are desired.
        # We will only consider trips with net_energy_gain > 0.
        max_trip_value_efficiency = 0

        # Consider each available E as a *potential first stop* in a multi-token trip
        for first_e_target_coord in list(energy_coords_on_grid):
            if current_holding >= capacity: # Should be 0 if at start of planning a new collection spree
                break

            # Path from current agent position to this first_e_target_coord
            path_to_first_e, actions_to_first_e = find_path_bfs(current_pos, first_e_target_coord, grid_copy, move_directions)

            if path_to_first_e is None:
                continue

            # --- Try to build a multi-token sequence starting with first_e_target_coord ---
            current_sequence_path_objects = [] # list of dicts {'moves':[], 'actions':num, 'target':coord}
            current_sequence_total_actions = 0
            current_sequence_total_move_actions = 0
            current_sequence_energy_collected = 0
            
            # Leg to the first E
            current_sequence_path_objects.append({'moves': path_to_first_e, 'actions': actions_to_first_e, 'target': first_e_target_coord})
            current_sequence_total_actions += actions_to_first_e + 1 # +1 for TAKE
            current_sequence_total_move_actions += actions_to_first_e
            current_sequence_energy_collected += 1
            
            # State for sequence building
            temp_pos_in_sequence = first_e_target_coord
            temp_available_e_for_sequence = energy_coords_on_grid.copy()
            temp_available_e_for_sequence.remove(first_e_target_coord)

            # Greedily add more E's to the sequence
            while current_sequence_energy_collected < capacity and len(temp_available_e_for_sequence) > 0:
                best_next_e_in_sequence = None
                min_actions_to_next_e = float('inf')
                path_to_best_next_e_in_sequence = None

                for candidate_e in temp_available_e_for_sequence:
                    path, num_actions = find_path_bfs(temp_pos_in_sequence, candidate_e, grid_copy, move_directions)
                    if path is not None and num_actions < min_actions_to_next_e:
                        min_actions_to_next_e = num_actions
                        best_next_e_in_sequence = candidate_e
                        path_to_best_next_e_in_sequence = path
                
                if best_next_e_in_sequence is None: # No more reachable E's to extend sequence
                    break

                # Check if adding this E and then being able to return home is feasible action-wise
                # Path from this candidate (if it were the last) back to start
                path_cand_to_start, actions_cand_to_start = find_path_bfs(best_next_e_in_sequence, start_pos, grid_copy, move_directions)
                
                if path_cand_to_start is None: # Cannot return home from this candidate
                    temp_available_e_for_sequence.remove(best_next_e_in_sequence) # Don't try it again for this sequence build
                    continue # Try finding another 'next E'

                # Tentative total actions if this 'best_next_e_in_sequence' is added,
                # and then the trip ends (return home + DROP)
                # current_sequence_total_actions = (moves to prev E + TAKE prev E) + (moves to prev2 E + TAKE prev2 E)...
                # So, add (moves to current candidate + TAKE current candidate)
                # Then (moves from current candidate to start + DROP)
                potential_actions_if_added = (current_sequence_total_actions + 
                                             min_actions_to_next_e + 1 + # moves to next E + TAKE
                                             actions_cand_to_start + 1)    # moves to start + DROP
                
                if potential_actions_if_added <= remaining_actions:
                    # It's feasible to add this E and still complete a trip
                    current_sequence_path_objects.append({'moves': path_to_best_next_e_in_sequence, 
                                                          'actions': min_actions_to_next_e, 
                                                          'target': best_next_e_in_sequence})
                    current_sequence_total_actions += min_actions_to_next_e + 1 # +1 for TAKE
                    current_sequence_total_move_actions += min_actions_to_next_e
                    current_sequence_energy_collected += 1
                    
                    temp_pos_in_sequence = best_next_e_in_sequence
                    temp_available_e_for_sequence.remove(best_next_e_in_sequence)
                else:
                    # Cannot afford to add this E (and path home), so stop extending this sequence
                    break
            
            # Sequence built (1 to capacity Es). Now, formalize the path from last E to start.
            # temp_pos_in_sequence is the location of the last E collected in this sequence.
            final_path_to_start, final_actions_to_start = find_path_bfs(temp_pos_in_sequence, start_pos, grid_copy, move_directions)

            if final_path_to_start is not None:
                # current_sequence_total_actions includes all moves between Es and all TAKE actions
                # current_sequence_total_move_actions includes all moves between Es
                
                complete_trip_total_actions = current_sequence_total_actions + final_actions_to_start + 1 # +1 for DROP
                complete_trip_total_move_actions = current_sequence_total_move_actions + final_actions_to_start
                
                if complete_trip_total_actions <= remaining_actions:
                    net_energy_gain = current_sequence_energy_collected - (complete_trip_total_move_actions * cost_per_step)
                    
                    if net_energy_gain > 0: # Only consider trips with positive net energy gain
                        trip_value_eff = net_energy_gain / (complete_trip_total_actions + 1e-9) # Add epsilon for safety
                        
                        if trip_value_eff > max_trip_value_efficiency:
                            max_trip_value_efficiency = trip_value_eff
                            best_trip_plan = {
                                "trip_path_segments": current_sequence_path_objects, # List of segment dicts
                                "return_path_moves": final_path_to_start,
                                "return_path_actions": final_actions_to_start,
                                "total_actions": complete_trip_total_actions,
                                "num_collected_this_trip": current_sequence_energy_collected,
                                "total_moves_this_trip": complete_trip_total_move_actions
                            }
                            # print(f"  Found potential multi-trip. Targets: {[s['target'] for s in current_sequence_path_objects]}. Energy: {current_sequence_energy_collected}. Actions: {complete_trip_total_actions}. NetGain: {net_energy_gain}. ValueEff: {trip_value_eff:.3f}")

        # --- Execute Best Trip or Finish ---
        if best_trip_plan:
            targets_str = ", ".join([str(s['target']) for s in best_trip_plan['trip_path_segments']])
            # print(f"Executing best trip to {targets_str} (Collected: {best_trip_plan['num_collected_this_trip']}, TotalActions: {best_trip_plan['total_actions']}, CurrentRemActions: {remaining_actions})")

            # Execute path segments to collect E's
            for i, segment in enumerate(best_trip_plan['trip_path_segments']):
                target_coord = segment['target']
                # Move to E_i
                for move in segment['moves']:
                    # This check should ideally not be needed if plan is feasible, but good for safety
                    if remaining_actions < 1: # Cost of move action is 1
                        # print("  Ran out of actions during move to target E. Aborting trip.")
                        # State: current_pos, current_holding, remaining_actions might be messy. Loop will re-evaluate or end.
                        # Break from executing this trip, outer loop will decide next step (e.g., final return)
                        best_trip_plan = None # Mark trip as failed
                        break 
                    action_list.append(move)
                    current_pos = update_position(current_pos, move)
                    remaining_actions -= 1
                if not best_trip_plan: break # Aborted

                # TAKE Action at E_i
                if remaining_actions >= 1 and current_pos == target_coord and target_coord in energy_coords_on_grid:
                    action_list.append("TAKE")
                    remaining_actions -= 1
                    current_holding += 1
                    energy_coords_on_grid.remove(target_coord) # Remove E from available targets
                    # print(f"  TAKE at {target_coord}. Holding: {current_holding}. Actions left: {remaining_actions}")
                else:
                    # This case indicates a logic flaw in planning or an unexpected state change
                    # print(f"  ERROR: Failed to TAKE at {target_coord}. Pos:{current_pos}, E_available:{target_coord in energy_coords_on_grid}, Actions:{remaining_actions}")
                    best_trip_plan = None # Mark trip as failed
                    break # Abort this trip
            
            if not best_trip_plan: # Trip aborted mid-collection
                 # The agent might be holding some energy and not at base.
                 # The main loop will re-evaluate. If no more trips, final return logic will apply.
                #  print("  Trip execution aborted.")
                 continue # To the start of the while remaining_actions > 0 loop

            # All E's in sequence collected, now return to base
            for move in best_trip_plan['return_path_moves']:
                if remaining_actions < 1:
                    # print("  Ran out of actions during return to base. Aborting trip.")
                    best_trip_plan = None 
                    break
                action_list.append(move)
                current_pos = update_position(current_pos, move)
                remaining_actions -= 1
            if not best_trip_plan: # Trip aborted during return
                #  print("  Trip return aborted.")
                 continue

            # DROP Action at base
            if remaining_actions >= 1 and current_pos == start_pos and current_holding > 0:
                action_list.append("DROP")
                remaining_actions -= 1
                score += current_holding
                # print(f"  DROP at {start_pos}. Score: {score}. Holding: 0. Actions left: {remaining_actions}")
                current_holding = 0
            # else:
                # if current_pos != start_pos: print(f"  Warning: Arrived at {current_pos} instead of start after return path.")
                # if current_holding == 0 : print(f"  Warning: Nothing to DROP, holding is 0.")
                # elif remaining_actions < 1: print(f"  Warning: No actions left to DROP.")
                # If drop failed, energy is still held. Loop will re-evaluate.
        else:
            # No feasible (positive net gain) trips found
            # print("No more beneficial trips found.")
            break # Exit main loop, proceed to final return/drop if needed

    # --- Final Return/Drop if Holding Energy ---
    if current_holding > 0 and remaining_actions > 0:
        if current_pos == start_pos:
            if remaining_actions >= 1: # Check for DROP action
                # print(f"Performing final DROP at start (Actions left: {remaining_actions})")
                action_list.append("DROP")
                remaining_actions -= 1
                score += current_holding
                current_holding = 0
                # print(f"  Final DROP successful. Score: {score}. Actions left: {remaining_actions}")
        else: # Holding energy, not at base
            # print(f"Attempting final return to base with {current_holding} energy (Actions left: {remaining_actions}) from {current_pos}")
            path_home, actions_home = find_path_bfs(current_pos, start_pos, grid_copy, move_directions)

            if path_home is not None and (actions_home + 1) <= remaining_actions: # +1 for DROP
                # print(f"  Executing final return path (Move Actions: {actions_home}, DROP: 1)")
                for move in path_home:
                    if remaining_actions < 1: break # Should be covered by (actions_home + 1) check
                    action_list.append(move)
                    current_pos = update_position(current_pos, move)
                    remaining_actions -= 1
                
                if remaining_actions >= 1 and current_pos == start_pos: # Re-check after moves
                    action_list.append("DROP")
                    remaining_actions -= 1
                    score += current_holding
                    current_holding = 0
                    # print(f"  Final return DROP successful. Score: {score}. Actions left: {remaining_actions}")
                # else:
                    #  print(f"  Final return failed to Drop (Actions left: {remaining_actions}, Position: {current_pos}). Energy {current_holding} likely lost from score.")
            # else:
            #     print(f"  Cannot execute final return (Not enough actions or no path). Energy {current_holding} likely lost from score.")
    
    # Calculate total moves for final score adjustment (though function only returns actions)
    total_moves_overall = sum(1 for action in action_list if action not in ["TAKE", "DROP"])
    final_net_score = score - (total_moves_overall * cost_per_step)

    # print(f"--- Game Over ---")
    # print(f"Final Position: {current_pos}, Actions Remaining: {remaining_actions}, Energy Held: {current_holding}")
    # print(f"Gross Score (Energy at Base {start_pos}): {score}")
    # print(f"Total Moves Made: {total_moves_overall}, Cost Per Step: {cost_per_step}")
    # print(f"Projected Net Score: {final_net_score}")
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
    actions = solve_grid(grid, tuple(start_pos), max_actions, carry_limit, cost_per_step, 4 if movement_type == "four" else 8)
    return actions

def print_actions(actions):
    print("Actions taken:")
    for action in actions:
        print(action)

if __name__ == "__main__":
    # Sample grid as provided in the pseudocode
    grid = [
        [" ", " ", "E", "E", "E", "E", " ", "E", "E", "E", "E"],
        [" ", " ", "E", "E", "E", " ", " ", " ", " ", "E", " "],
        ["E", " ", " ", " ", "E", " ", " ", "E", "E", " ", " "],
        ["E", "E", "E", "E", " ", "E", "E", "E", " ", "E", "E"],
        [" ", "E", " ", "A", "E", " ", "E", " ", "E", "E", " "],
        ["E", " ", "E", " ", "E", "E", " ", "E", " ", "E", " "],
        ["E", " ", "E", " ", " ", " ", " ", "E", "E", "E", "E"],
        ["E", "E", " ", " ", " ", " ", "E", " ", "E", "E", " "],
        ["E", " ", "E", "E", "E", " ", " ", " ", "E", "E", " "],
        [" ", " ", "E", "E", "E", " ", "E", " ", " ", " ", " "],
        [" ", "E", "E", " ", "E", "E", " ", "E", " ", "E", "E"]
    ]
    
    max_actions = 20       # Maximum number of allowed actions
    token_capacity = 3     # Maximum number of tokens that can be carried at once
    
    actions = solve_grid(grid, (4, 3), max_actions, token_capacity, 0.3, 8)
    print_actions(actions)