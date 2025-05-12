import collections
import math

# --- Helper Functions (assumed unchanged, ensure they are present) ---

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

def find_path_bfs(from_coord, to_coord, grid_for_bfs, move_directions):
    """
    Finds the shortest path using Breadth-First Search (BFS).
    Returns (list_of_move_names, num_move_actions) or (None, float('inf')).
    Each move action costs 1.
    """
    grid_height = len(grid_for_bfs)
    grid_width = len(grid_for_bfs[0])
    
    if from_coord == to_coord:
        return [], 0

    queue = collections.deque([(from_coord, [])]) 
    visited = {from_coord}

    while queue:
        current_coord, path_moves = queue.popleft()

        for neighbor_coord, move_name in get_neighbors(current_coord, grid_height, grid_width, grid_for_bfs, move_directions):
            if neighbor_coord == to_coord:
                return path_moves + [move_name], len(path_moves) + 1
            
            if neighbor_coord not in visited:
                visited.add(neighbor_coord)
                new_path_moves = path_moves + [move_name]
                queue.append((neighbor_coord, new_path_moves))

    return None, float('inf')

# --- Main Solver Function ---

def solve_grid(grid, start_pos_param, max_actions, capacity, cost_per_step=1, move_directions=4):
    if not grid or not grid[0]:
        return []
        
    grid_height = len(grid)
    grid_width = len(grid[0])

    agent_actual_start_pos = None
    initial_energy_coords = set()
    grid_copy = [list(row) for row in grid] 

    for r in range(grid_height):
        for c in range(grid_width):
            if grid[r][c] == 'A': 
                if agent_actual_start_pos is None:
                    agent_actual_start_pos = (r, c)
                grid_copy[r][c] = ' ' 
            elif grid[r][c] == 'E': 
                initial_energy_coords.add((r, c))

    if agent_actual_start_pos is None:
        if 0 <= start_pos_param[0] < grid_height and \
           0 <= start_pos_param[1] < grid_width and \
           grid[start_pos_param[0]][start_pos_param[1]] != 'O':
            agent_actual_start_pos = start_pos_param
            if grid[agent_actual_start_pos[0]][agent_actual_start_pos[1]] == 'E' and agent_actual_start_pos not in initial_energy_coords:
                initial_energy_coords.add(agent_actual_start_pos) 
            grid_copy[agent_actual_start_pos[0]][agent_actual_start_pos[1]] = ' ' 
        else:
            return [] 
    
    start_pos = agent_actual_start_pos
    current_pos = start_pos
    remaining_actions = max_actions
    current_holding = 0
    score = 0

    if start_pos in initial_energy_coords:
        score = 1 
        initial_energy_coords.remove(start_pos)

    action_list = []
    energy_coords_on_grid = initial_energy_coords.copy()

    while remaining_actions > 0:
        if current_holding > 0 and current_pos == start_pos and remaining_actions >= 1:
            action_list.append("DROP")
            remaining_actions -= 1
            score += current_holding
            current_holding = 0
            if remaining_actions <= 0: break
        
        initial_holding_for_this_trip_plan = current_holding 

        best_trip_plan = None
        max_net_gain_for_this_round = 0 

        sorted_initial_targets = list(energy_coords_on_grid)
        sorted_initial_targets.sort(key=lambda e_coord: find_path_bfs(current_pos, e_coord, grid_copy, move_directions)[1])

        for first_e_target_coord in sorted_initial_targets:
            if initial_holding_for_this_trip_plan >= capacity:
                break 

            path_to_first_e, actions_to_first_e = find_path_bfs(current_pos, first_e_target_coord, grid_copy, move_directions)

            if path_to_first_e is None:
                continue

            current_sequence_path_objects = [] 
            current_sequence_total_actions = 0   
            current_sequence_total_move_actions = 0 
            current_sequence_energy_collected = 0 
            
            current_sequence_path_objects.append({'moves': path_to_first_e, 'actions': actions_to_first_e, 'target': first_e_target_coord})
            current_sequence_total_actions += actions_to_first_e + 1 
            current_sequence_total_move_actions += actions_to_first_e
            current_sequence_energy_collected += 1
            
            temp_pos_in_sequence = first_e_target_coord
            temp_available_e_for_sequence = energy_coords_on_grid.copy()
            if first_e_target_coord in temp_available_e_for_sequence:
                 temp_available_e_for_sequence.remove(first_e_target_coord)

            # MODIFICATION STARTS HERE: Change in how trips are extended
            while initial_holding_for_this_trip_plan + current_sequence_energy_collected < capacity:
                if not temp_available_e_for_sequence: 
                    break

                potential_next_extensions_with_heuristic = []
                for candidate_e_coord_loop in temp_available_e_for_sequence: 
                    path_curr_to_cand, actions_curr_to_cand = find_path_bfs(temp_pos_in_sequence, candidate_e_coord_loop, grid_copy, move_directions)
                    if path_curr_to_cand is None:
                        continue

                    path_cand_to_start_base, actions_cand_to_start_base = find_path_bfs(candidate_e_coord_loop, start_pos, grid_copy, move_directions)
                    if path_cand_to_start_base is None: 
                        continue
                    
                    # New heuristic: (actions from current E to next E) + (actions from next E to base)
                    heuristic_value = actions_curr_to_cand + actions_cand_to_start_base

                    potential_next_extensions_with_heuristic.append({
                        'coord': candidate_e_coord_loop,
                        'path_moves_from_curr': path_curr_to_cand,
                        'actions_from_curr': actions_curr_to_cand,
                        'path_moves_to_start_base': path_cand_to_start_base, 
                        'actions_to_start_base': actions_cand_to_start_base,
                        'heuristic_value': heuristic_value
                    })
                
                if not potential_next_extensions_with_heuristic:
                    break 

                potential_next_extensions_with_heuristic.sort(key=lambda x: x['heuristic_value'])

                added_an_e_this_iteration = False
                for next_e_package in potential_next_extensions_with_heuristic:
                    cand_coord_ext = next_e_package['coord']
                    path_to_cand_ext = next_e_package['path_moves_from_curr']
                    actions_to_cand_ext = next_e_package['actions_from_curr']
                    
                    # This is actions from this candidate to start base, if it were the *last* E
                    actions_cand_ext_to_start_base = next_e_package['actions_to_start_base']
                    
                    # Total actions if this candidate is chosen AND IS THE LAST ONE IN THE TRIP:
                    # current_sequence_total_actions = (actions for current seq up to prev E + their TAKE actions)
                    # actions_to_cand_ext = (actions from prev E to this candidate E)
                    # +1 for TAKE candidate E
                    # actions_cand_ext_to_start_base = (actions from candidate E to Start Base)
                    # +1 for DROP
                    trip_actions_if_cand_is_last = current_sequence_total_actions + \
                                                   actions_to_cand_ext + 1 + \
                                                   actions_cand_ext_to_start_base + 1 
                
                    if trip_actions_if_cand_is_last <= remaining_actions:
                        current_sequence_path_objects.append({
                            'moves': path_to_cand_ext, 
                            'actions': actions_to_cand_ext, 
                            'target': cand_coord_ext
                        })
                        current_sequence_total_actions += actions_to_cand_ext + 1 
                        current_sequence_total_move_actions += actions_to_cand_ext 
                        current_sequence_energy_collected += 1
                        
                        temp_pos_in_sequence = cand_coord_ext
                        if cand_coord_ext in temp_available_e_for_sequence:
                            temp_available_e_for_sequence.remove(cand_coord_ext)
                        added_an_e_this_iteration = True
                        break # Commit to this extension (best by new heuristic that fits budget)
                
                if not added_an_e_this_iteration:
                    break 
            # MODIFICATION ENDS HERE

            final_path_to_start, final_actions_to_start = find_path_bfs(temp_pos_in_sequence, start_pos, grid_copy, move_directions)

            if final_path_to_start is not None:
                # current_sequence_total_actions already includes all path actions BETWEEN Es and all TAKE actions
                # final_actions_to_start is path from LAST E in sequence to start_pos
                # +1 is for the final DROP action
                complete_trip_actions = current_sequence_total_actions + final_actions_to_start + 1 
                complete_trip_move_actions = current_sequence_total_move_actions + final_actions_to_start
                
                net_energy_gain_this_trip = (initial_holding_for_this_trip_plan + current_sequence_energy_collected) - \
                                            initial_holding_for_this_trip_plan - \
                                            (complete_trip_move_actions * cost_per_step) 
                                            # This simplifies to: current_sequence_energy_collected - (move_actions * cost)
                                            # which is correct for *newly collected* energy vs cost of this trip.

                # The actual energy delivered is current_sequence_energy_collected (new) + initial_holding (if any from prev partial trip)
                # The score gain from *this trip* is current_sequence_energy_collected (new tokens) minus cost.
                # The "score" variable tracks total dropped. Here we evaluate prospective gain.

                # Effective net gain for *this specific collection run*
                net_gain_for_tokens_collected_this_run = current_sequence_energy_collected - (complete_trip_move_actions * cost_per_step)


                if complete_trip_actions <= remaining_actions and net_gain_for_tokens_collected_this_run > 0:
                    if net_gain_for_tokens_collected_this_run > max_net_gain_for_this_round:
                        max_net_gain_for_this_round = net_gain_for_tokens_collected_this_run
                        best_trip_plan = {
                            "trip_path_segments": current_sequence_path_objects,
                            "return_path_moves": final_path_to_start,
                            "return_path_actions": final_actions_to_start,
                            "total_actions": complete_trip_actions, 
                            "num_collected_this_trip": current_sequence_energy_collected, # Energy collected *during this candidate trip*
                            "total_moves_this_trip": complete_trip_move_actions,
                            "net_gain": net_gain_for_tokens_collected_this_run 
                        }
                    elif net_gain_for_tokens_collected_this_run == max_net_gain_for_this_round: 
                        if best_trip_plan and complete_trip_actions < best_trip_plan["total_actions"]:
                            best_trip_plan = {
                                "trip_path_segments": current_sequence_path_objects,
                                "return_path_moves": final_path_to_start,
                                "return_path_actions": final_actions_to_start,
                                "total_actions": complete_trip_actions,
                                "num_collected_this_trip": current_sequence_energy_collected,
                                "total_moves_this_trip": complete_trip_move_actions,
                                "net_gain": net_gain_for_tokens_collected_this_run
                            }
        
        if best_trip_plan:
            trip_failed_execution = False
            # Execute collection part of the trip
            for i, segment in enumerate(best_trip_plan['trip_path_segments']):
                target_coord = segment['target']
                for move in segment['moves']:
                    if remaining_actions < 1: trip_failed_execution = True; break
                    action_list.append(move)
                    current_pos = update_position(current_pos, move)
                    remaining_actions -= 1
                if trip_failed_execution: break

                if remaining_actions >= 1 and current_pos == target_coord and target_coord in energy_coords_on_grid:
                    action_list.append("TAKE")
                    remaining_actions -= 1
                    current_holding += 1 
                    energy_coords_on_grid.remove(target_coord) 
                else: 
                    # This case implies target_coord was not on grid or no actions left.
                    # Or target was already collected by a concurrent plan (not possible in this single agent setup).
                    # Or current_pos != target_coord (path execution error, should not happen with BFS if grid static)
                    trip_failed_execution = True; break 
            
            if trip_failed_execution: 
                # If trip execution failed partway, actions were spent, current_pos updated.
                # current_holding might have some items. Loop will restart planning.
                # This is a failsafe; ideally, a well-planned trip doesn't fail execution.
                continue 

            # Execute return part of the trip
            for move in best_trip_plan['return_path_moves']:
                if remaining_actions < 1: trip_failed_execution = True; break
                action_list.append(move)
                current_pos = update_position(current_pos, move)
                remaining_actions -= 1
            if trip_failed_execution: continue # Similar to above.

            # Drop at start if successful
            if remaining_actions >= 1 and current_pos == start_pos and current_holding > 0:
                action_list.append("DROP")
                remaining_actions -= 1
                score += current_holding
                current_holding = 0
            # else: if not at start or no actions, holding energy might be carried to next planning iteration.
        else: 
            break # No beneficial trip found, stop trying.

    # Final Return/Drop if Holding Energy and not at start (or at start but didn't drop in loop)
    if current_holding > 0 : 
        if current_pos == start_pos:
            if remaining_actions >= 1: 
                action_list.append("DROP")
                # remaining_actions -= 1 # Not strictly necessary to decrement if it's the last possible action
                score += current_holding
                # current_holding = 0
        else: 
            path_home, actions_home = find_path_bfs(current_pos, start_pos, grid_copy, move_directions)
            # Check if path home + drop is possible
            if path_home is not None and (actions_home + 1) <= remaining_actions : 
                for move in path_home:
                    # No need to check remaining_actions per move if total check passed,
                    # but good for safety if intermediate checks are desired.
                    # if remaining_actions < 1: break 
                    action_list.append(move)
                    # current_pos = update_position(current_pos, move) # current_pos not used after this
                    # remaining_actions -= 1
                
                # if remaining_actions >= 1: # Redundant if (actions_home + 1) <= remaining_actions check was fine
                action_list.append("DROP")
                # remaining_actions -=1
                score += current_holding
                # current_holding = 0
    
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