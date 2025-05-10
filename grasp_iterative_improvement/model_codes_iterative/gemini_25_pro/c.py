
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
    
    if from_coord == to_coord: # Path to self is 0 moves, empty path
        return [], 0

    queue = collections.deque([(from_coord, [])])  # (coordinate, path_list_of_moves)
    visited = {from_coord}

    while queue:
        current_coord, path_moves = queue.popleft()

        for neighbor_coord, move_name in get_neighbors(current_coord, grid_height, grid_width, grid, move_directions):
            if neighbor_coord == to_coord:
                return path_moves + [move_name], len(path_moves) + 1
            
            if neighbor_coord not in visited:
                visited.add(neighbor_coord)
                new_path_moves = path_moves + [move_name]
                queue.append((neighbor_coord, new_path_moves))

    return None, float('inf') # No path found

# --- Main Solver Function ---

def solve_grid(grid, start_pos_param, max_actions, capacity, cost_per_step=1, move_directions=4):
    if not grid or not grid[0]:
        # print("Error: Empty or invalid grid.")
        return []
        
    grid_height = len(grid)
    grid_width = len(grid[0])

    agent_actual_start_pos = None
    initial_energy_coords = set()
    # grid_copy is used for BFS pathfinding, reflects dynamic state (e.g., 'A' becomes traversable)
    grid_copy = [list(row) for row in grid] 

    for r in range(grid_height):
        for c in range(grid_width):
            if grid_copy[r][c] == 'A':
                if agent_actual_start_pos is not None:
                    # print("Warning: Multiple 'A's found. Using the first one.")
                    pass
                else:
                    agent_actual_start_pos = (r, c)
                grid_copy[r][c] = ' ' # Agent location is traversable
            elif grid_copy[r][c] == 'E':
                initial_energy_coords.add((r, c))

    if agent_actual_start_pos is None:
        # If 'A' not in grid, trust start_pos_param
        # Check validity against the original grid's obstacles
        if 0 <= start_pos_param[0] < grid_height and \
           0 <= start_pos_param[1] < grid_width and \
           grid[start_pos_param[0]][start_pos_param[1]] != 'O':
            agent_actual_start_pos = start_pos_param
            # If start_pos_param was 'E', it's already in initial_energy_coords.
            # Mark this starting cell as traversable in grid_copy.
            grid_copy[start_pos_param[0]][start_pos_param[1]] = ' ' 
        else:
            # print("Error: Agent 'A' not found in grid and start_pos_param is invalid or an obstacle.")
            return []
    
    start_pos = agent_actual_start_pos
    current_pos = start_pos
    remaining_actions = max_actions
    current_holding = 0 # Actual energy tokens currently held by the agent
    score = 0 # Energy successfully dropped at start_pos

    # Handle energy initially at the agent's starting position
    if start_pos in initial_energy_coords:
        # print(f"Info: Agent started on an energy token at {start_pos}. This counts towards score.")
        score = 1 
        initial_energy_coords.remove(start_pos)
        # The location in grid_copy is already ' ' if 'A' was there or made ' ' above.

    action_list = []
    # energy_coords_on_grid tracks E's still available for collection on the map
    energy_coords_on_grid = initial_energy_coords.copy()

    # print(f"Starting Game: Max Actions={max_actions}, Capacity={capacity}, Start={start_pos}, CostPerStep={cost_per_step}")
    # print(f"Initial Energy on Grid (excluding start, if any): {len(energy_coords_on_grid)}, Score from start: {score}")

    while remaining_actions > 0:
        # 1. Pre-emptive DROP if at base and holding energy
        if current_holding > 0 and current_pos == start_pos and remaining_actions >= 1:
            action_list.append("DROP")
            remaining_actions -= 1
            score += current_holding
            # print(f"  Pre-emptive DROP at {start_pos}. Holding: 0. Score: {score}. Actions left: {remaining_actions}")
            current_holding = 0
            if remaining_actions <= 0: break
        
        # This variable captures what the agent is holding *before planning this potential trip*
        initial_holding_for_this_trip_plan = current_holding 

        best_trip_plan = None
        max_trip_value_efficiency = 0 

        # Sort available E's to explore potentially better initial targets first (heuristic)
        # This is optional; current BFS-based trip evaluation is exhaustive for sequences.
        sorted_initial_targets = list(energy_coords_on_grid)
        # sorted_initial_targets.sort(key=lambda e_coord: find_path_bfs(current_pos, e_coord, grid_copy, move_directions)[1])


        for first_e_target_coord in sorted_initial_targets:
            # If agent is already at full capacity, it cannot pick up 'first_e_target_coord'.
            if initial_holding_for_this_trip_plan >= capacity:
                break 

            path_to_first_e, actions_to_first_e = find_path_bfs(current_pos, first_e_target_coord, grid_copy, move_directions)

            if path_to_first_e is None:
                continue

            # --- Plan a sequence starting with first_e_target_coord ---
            # current_sequence_... variables track the properties of the *newly planned collection part* of the trip
            current_sequence_path_objects = [] 
            current_sequence_total_actions = 0    # Actions for moves in seq + TAKE actions in seq
            current_sequence_total_move_actions = 0 # Only move actions within the seq
            current_sequence_energy_collected = 0 # Number of NEW E's in this planned sequence
            
            # Add first E to this sequence plan
            current_sequence_path_objects.append({'moves': path_to_first_e, 'actions': actions_to_first_e, 'target': first_e_target_coord})
            current_sequence_total_actions += actions_to_first_e + 1 # +1 for TAKE for this first E
            current_sequence_total_move_actions += actions_to_first_e
            current_sequence_energy_collected += 1 # One new E in this plan
            
            temp_pos_in_sequence = first_e_target_coord
            temp_available_e_for_sequence = energy_coords_on_grid.copy()
            if first_e_target_coord in temp_available_e_for_sequence:
                 temp_available_e_for_sequence.remove(first_e_target_coord)

            # MODIFIED LOGIC FOR SEQUENCE EXTENSION
            # Keep adding to sequence as long as total carried (initial + new) < capacity
            while initial_holding_for_this_trip_plan + current_sequence_energy_collected < capacity:
                if not temp_available_e_for_sequence: # No more E's on grid to pick up
                    break

                potential_next_extensions = []
                for candidate_e in temp_available_e_for_sequence: # Consider all remaining E's
                    path, num_actions_to_cand = find_path_bfs(temp_pos_in_sequence, candidate_e, grid_copy, move_directions)
                    if path is not None:
                        potential_next_extensions.append({
                            'coord': candidate_e, 
                            'path_moves': path, 
                            'actions_to_reach': num_actions_to_cand 
                        })
                
                # Sort candidates by shortest path to reach them
                potential_next_extensions.sort(key=lambda x: x['actions_to_reach'])

                added_an_e_this_iteration = False
                for next_e_info in potential_next_extensions:
                    cand_coord = next_e_info['coord']
                    path_to_cand = next_e_info['path_moves']
                    actions_to_cand = next_e_info['actions_to_reach']

                    # Check if trip is viable if cand_coord is the *last* E collected in sequence
                    path_cand_to_start, actions_cand_to_start = find_path_bfs(cand_coord, start_pos, grid_copy, move_directions)
                    
                    if path_cand_to_start is None: 
                        # This candidate cannot return home if it's the last one. Skip it.
                        continue 

                    # Total actions for the *entire trip* if this candidate is added,
                    # including moves from current_pos to first_e, then through sequence, then to start.
                    # current_sequence_total_actions already includes moves to previous E + TAKE.
                    # So, add moves to current candidate + TAKE for current candidate.
                    # Then, add moves from current candidate to start + DROP.
                    
                    # Actions for the collection phase part:
                    # (Path to first_E + TAKE) -> (Path to E_2 + TAKE_2) ... -> (Path to cand_E + TAKE_cand)
                    # This is: (current_sequence_total_actions_so_far - (TAKEs_so_far)) + path_to_cand + (TAKEs_so_far + 1)
                    # Simpler: current_sequence_total_actions (moves to prev E + all previous TAKE)
                    #          + actions_to_cand (moves to current cand) + 1 (TAKE current cand)
                    #          + actions_cand_to_start (moves to base) + 1 (DROP)
                    
                    # Let's recalculate full trip actions based on segments for clarity
                    # Total moves: moves to 1st E + moves between Es in sequence + moves to cand_coord + moves cand_coord to start
                    # Total non-moves: number of items in sequence (incl. cand_coord) for TAKEs + 1 DROP
                    
                    # current_sequence_total_actions already has moves_to_prev_E_in_seq + N_TAKES_in_seq
                    # actions_cand_to_start are only moves
                    
                    # This is the total actions for the *whole trip* being planned
                    # (moves to first E + first TAKE) + (moves between Es up to current + their TAKEs) + (moves to cand_E + its TAKE) + (moves from cand_E to base + DROP)
                    # This is: actions_to_first_e + 1 (for first E)
                    #         + sum(seg['actions'] + 1 for seg in current_sequence_path_objects[1:]) (for intermediate Es already in plan)
                    #         + actions_to_cand + 1 (for the candidate E)
                    #         + actions_cand_to_start + 1 (for return and DROP)
                    # This can be simplified:
                    # current_sequence_total_actions (covers up to previous E and its TAKE)
                    # + actions_to_cand (moves to new cand) + 1 (TAKE new cand)
                    # + actions_cand_to_start (moves from new cand to base) + 1 (DROP)
                    
                    potential_full_trip_actions = current_sequence_total_actions + \
                                                  actions_to_cand + 1 + \
                                                  actions_cand_to_start + 1
                
                    if potential_full_trip_actions <= remaining_actions:
                        # Add this candidate to the current sequence plan
                        current_sequence_path_objects.append({
                            'moves': path_to_cand, 
                            'actions': actions_to_cand, 
                            'target': cand_coord
                        })
                        current_sequence_total_actions += actions_to_cand + 1 # Add moves to cand and its TAKE
                        current_sequence_total_move_actions += actions_to_cand # Add only moves
                        current_sequence_energy_collected += 1 # One more NEW E in this plan
                        
                        temp_pos_in_sequence = cand_coord
                        if cand_coord in temp_available_e_for_sequence:
                            temp_available_e_for_sequence.remove(cand_coord)
                        added_an_e_this_iteration = True
                        break # Added a viable E, break from iterating candidates, continue extending sequence
                
                if not added_an_e_this_iteration:
                    break # No viable E could be added from remaining options, stop extending this current sequence.

            # --- Sequence built (or attempted). Now evaluate this complete trip plan. ---
            # temp_pos_in_sequence is the location of the last E collected in the planned sequence.
            final_path_to_start, final_actions_to_start = find_path_bfs(temp_pos_in_sequence, start_pos, grid_copy, move_directions)

            if final_path_to_start is not None:
                # current_sequence_total_actions = (moves up to last_E_in_seq + all TAKE actions for seq)
                # current_sequence_total_move_actions = (moves up to last_E_in_seq)
                
                complete_trip_actions = current_sequence_total_actions + final_actions_to_start + 1 # +1 for DROP
                complete_trip_move_actions = current_sequence_total_move_actions + final_actions_to_start
                
                # current_sequence_energy_collected is the number of NEW items this trip would yield.
                # Total energy that would be dropped: initial_holding_for_this_trip_plan + current_sequence_energy_collected
                # Net gain is based on *newly collected* energy vs cost of *this entire trip from current_pos*
                # If agent already holds items, their "collection cost" is sunk.
                # The decision is whether *this trip* is worth it to get *more* energy.
                # The problem seems to imply net_energy_gain is for items collected *in this trip*.
                
                net_energy_gain_this_trip = current_sequence_energy_collected - (complete_trip_move_actions * cost_per_step)
                
                if complete_trip_actions <= remaining_actions and net_energy_gain_this_trip > 0:
                    # Efficiency: net new energy from this trip / actions for this trip
                    trip_value_eff = net_energy_gain_this_trip / (complete_trip_actions + 1e-9) # Add epsilon for safety
                    
                    if trip_value_eff > max_trip_value_efficiency:
                        max_trip_value_efficiency = trip_value_eff
                        best_trip_plan = {
                            "trip_path_segments": current_sequence_path_objects, # Path segments for NEWLY collected E's
                            "return_path_moves": final_path_to_start,
                            "return_path_actions": final_actions_to_start,
                            "total_actions": complete_trip_actions, # For the whole trip from current_pos
                            "num_collected_this_trip": current_sequence_energy_collected, # NEW E's this trip
                            "total_moves_this_trip": complete_trip_move_actions # Moves for the whole trip
                        }
                        # print(f"  Found potential trip. StartHold: {initial_holding_for_this_trip_plan}, NewCollect: {current_sequence_energy_collected}, Targets: {[s['target'] for s in current_sequence_path_objects]}. Actions: {complete_trip_actions}. NetGain: {net_energy_gain_this_trip}. ValueEff: {trip_value_eff:.3f}")

        # --- Execute Best Trip or Finish ---
        if best_trip_plan:
            targets_str = ", ".join([str(s['target']) for s in best_trip_plan['trip_path_segments']])
            # print(f"Executing best trip to {targets_str} (Collects {best_trip_plan['num_collected_this_trip']} new E, TotalTripActions: {best_trip_plan['total_actions']}, CurrentRemActions: {remaining_actions}, CurrentHold: {current_holding})")

            trip_failed_execution = False
            # Execute path segments to collect E's specified in the plan
            for i, segment in enumerate(best_trip_plan['trip_path_segments']):
                target_coord = segment['target']
                # Move to E_i
                for move in segment['moves']:
                    if remaining_actions < 1:
                        # print("  Ran out of actions during move to target E. Aborting trip.")
                        trip_failed_execution = True; break
                    action_list.append(move)
                    current_pos = update_position(current_pos, move)
                    remaining_actions -= 1
                if trip_failed_execution: break

                # TAKE Action at E_i
                if remaining_actions >= 1 and current_pos == target_coord and target_coord in energy_coords_on_grid:
                    action_list.append("TAKE")
                    remaining_actions -= 1
                    current_holding += 1 # Actual holding increases
                    energy_coords_on_grid.remove(target_coord) # Remove E from available targets on map
                    # print(f"  TAKE at {target_coord}. Holding: {current_holding}. Actions left: {remaining_actions}. Energy on map: {len(energy_coords_on_grid)}")
                else:
                    # print(f"  ERROR: Failed to TAKE at {target_coord}. Pos:{current_pos}, E_available:{target_coord in energy_coords_on_grid}, Actions:{remaining_actions}")
                    trip_failed_execution = True; break
            
            if trip_failed_execution:
                # print("  Trip execution aborted during collection phase.")
                continue # To the start of the while remaining_actions > 0 loop

            # All E's in sequence collected, now return to base
            for move in best_trip_plan['return_path_moves']:
                if remaining_actions < 1:
                    # print("  Ran out of actions during return to base. Aborting trip return.")
                    trip_failed_execution = True; break
                action_list.append(move)
                current_pos = update_position(current_pos, move)
                remaining_actions -= 1
            if trip_failed_execution:
                #  print("  Trip execution aborted during return phase.")
                 continue

            # DROP Action at base (should happen if trip was successful and ended at base)
            if remaining_actions >= 1 and current_pos == start_pos and current_holding > 0:
                action_list.append("DROP")
                remaining_actions -= 1
                score += current_holding
                # print(f"  DROP at {start_pos} after trip. Score: {score}. Holding: 0. Actions left: {remaining_actions}")
                current_holding = 0
            # else: # Warnings for unexpected state after a trip that wasn't aborted
            #     if current_pos != start_pos: print(f"  Warning: Arrived at {current_pos} instead of start {start_pos} after trip return path.")
            #     if current_holding == 0 and best_trip_plan["num_collected_this_trip"] > 0 : print(f"  Warning: Holding 0 after collecting items and not dropping (should have dropped).")
            #     elif current_holding > 0 and remaining_actions < 1: print(f"  Warning: No actions left to DROP after trip, holding {current_holding}.")
            #     elif current_holding > 0 and current_pos != start_pos : print(f"  Warning: Holding {current_holding} but not at base to drop after trip.")
        else: # No best_trip_plan found
            # print("No more beneficial trips found or possible with current state/actions.")
            break # Exit main loop, proceed to final return/drop if needed

    # --- Final Return/Drop if Holding Energy and game loop exited ---
    if current_holding > 0 : # Check if holding anything, regardless of actions initially
        if current_pos == start_pos:
            if remaining_actions >= 1: 
                # print(f"Performing final DROP at start (Actions left: {remaining_actions}, Holding: {current_holding})")
                action_list.append("DROP")
                remaining_actions -= 1
                score += current_holding
                current_holding = 0
            #     print(f"  Final DROP successful. Score: {score}. Actions left: {remaining_actions}")
            # else: # At start, holding, but no actions to drop
            #     print(f"  Final DROP at start failed: no actions left. Energy {current_holding} not scored.")
        else: # Holding energy, not at base
            # print(f"Attempting final return to base with {current_holding} energy (Actions left: {remaining_actions}) from {current_pos}")
            path_home, actions_home = find_path_bfs(current_pos, start_pos, grid_copy, move_directions)

            if path_home is not None and (actions_home + 1) <= remaining_actions : # +1 for DROP
                # print(f"  Executing final return path (Move Actions: {actions_home}, DROP: 1)")
                for move in path_home:
                    if remaining_actions < 1: # Should be covered by (actions_home + 1) check, but safeguard
                        # print(f"    Ran out of actions during final return move. Energy {current_holding} likely lost.")
                        break 
                    action_list.append(move)
                    current_pos = update_position(current_pos, move)
                    remaining_actions -= 1
                
                if remaining_actions >= 1 and current_pos == start_pos: # Re-check after moves
                    action_list.append("DROP")
                    remaining_actions -= 1
                    score += current_holding
                    current_holding = 0
                    # print(f"  Final return DROP successful. Score: {score}. Actions left: {remaining_actions}")
                # else: # Failed to drop after final return moves
                    # print(f"  Final return failed to Drop (Actions left: {remaining_actions}, Position: {current_pos}, Expected Start: {start_pos}). Energy {current_holding} likely lost from score.")
            # else: # Cannot execute final return (no path or not enough actions)
            #     if path_home is None:
            #         # print(f"  Cannot execute final return: No path found from {current_pos} to {start_pos}. Energy {current_holding} lost.")
            #     else: 
                    # print(f"  Cannot execute final return: Not enough actions (Need {actions_home} moves + 1 DROP, Have {remaining_actions}). Energy {current_holding} lost.")
    elif current_holding == 0 and remaining_actions <=0: # No energy held, no actions left
         pass # Game ended cleanly or no way to score more.
    # elif current_holding > 0 and remaining_actions <=0: # Holding energy but no actions to do anything
        #  print(f"Game ended holding {current_holding} energy but no actions left to return or drop it. This energy is not scored.")
    
    total_moves_overall = sum(1 for action in action_list if action not in ["TAKE", "DROP"])
    final_net_score = score - (total_moves_overall * cost_per_step) #This is for external calculation.

    # print(f"--- Game Over ---")
    # print(f"Final Position: {current_pos}, Actions Remaining: {remaining_actions}, Energy Held: {current_holding}")
    # print(f"Gross Score (Energy at Base {start_pos}): {score}")
    # print(f"Total Moves Made: {total_moves_overall}, Cost Per Step: {cost_per_step}")
    # print(f"Projected Net Score (for verification): {final_net_score}") # The function returns action_list.
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