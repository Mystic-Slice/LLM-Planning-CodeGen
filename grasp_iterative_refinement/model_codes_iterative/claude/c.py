def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions=20):
    start_pos = tuple(start_pos)
    # Find agent's starting position
    if start_pos is not None:
        start_position = start_pos
    else:
        start_position = find_agent_position(grid)
    
    # Initialize variables
    actions_used = 0
    energy_carried = 0
    current_position = start_position
    energy_positions = find_all_energy_positions(grid)
    planned_actions = []
    
    # Main strategy loop
    while actions_used < max_actions:
        # If at starting position and carrying energy, drop it
        if current_position == start_position and energy_carried > 0:
            planned_actions.append("DROP")
            energy_carried = 0
            actions_used += 1
            continue
            
        # Calculate remaining actions
        remaining_actions = max_actions - actions_used
        
        # If almost out of actions, try to get back to base
        if remaining_actions <= 3 and energy_carried > 0:
            return_path = plan_path(current_position, start_position, grid, is_diagonals_allowed)
            if return_path and len(return_path) + 1 <= remaining_actions:
                planned_actions.extend(return_path)
                planned_actions.append("DROP")
                break
            else:
                # Can't make it back, move as far as possible toward start
                moves_possible = remaining_actions
                partial_path = return_path[:moves_possible] if moves_possible > 0 and return_path else []
                planned_actions.extend(partial_path)
                break
                
        # If carrying at capacity or no more energy tokens to collect, return to start
        if energy_carried >= carry_limit or not energy_positions:
            # Plan path back to starting position
            return_path = plan_path(current_position, start_position, grid, is_diagonals_allowed)
            
            # If no valid path or not enough actions left, optimize what we can do
            if not return_path or len(return_path) + 1 > remaining_actions:
                # Move towards start as much as possible
                partial_return_path = return_path[:remaining_actions] if remaining_actions > 0 and return_path else []
                planned_actions.extend(partial_return_path)
                # If we made it back by chance, drop energy
                if partial_return_path and get_position_after_moves(current_position, partial_return_path, grid) == start_position and energy_carried > 0:
                    if remaining_actions > len(partial_return_path):
                        planned_actions.append("DROP")
                break
                
            # Execute return path and drop
            planned_actions.extend(return_path)
            if energy_carried > 0:
                planned_actions.append("DROP")
                actions_used += 1
            actions_used += len(return_path)
            current_position = start_position
            energy_carried = 0
            continue
            
        # Plan the next multi-energy collection trip
        best_trip = plan_efficient_energy_collection(
            current_position, energy_positions, grid, start_position,
            energy_carried, carry_limit, remaining_actions, cost_per_step,
            is_diagonals_allowed
        )
        
        if not best_trip:
            # No viable trips, return to start if possible
            return_path = plan_path(current_position, start_position, grid, is_diagonals_allowed)
            if not return_path or len(return_path) + 1 > remaining_actions:
                # Can't make it back, move as far as possible toward start
                moves_possible = remaining_actions
                partial_path = return_path[:moves_possible] if moves_possible > 0 and return_path else []
                planned_actions.extend(partial_path)
                break
            else:
                # Can make it back, return and drop
                planned_actions.extend(return_path)
                if energy_carried > 0:
                    planned_actions.append("DROP")
                break
                
        # Execute the planned trip
        visited_energy_positions = set()
        
        for action in best_trip:
            if action == "TAKE":
                energy_carried += 1
                # Mark this position for removal from energy_positions
                visited_energy_positions.add(current_position)
            elif action in ["UP", "DOWN", "LEFT", "RIGHT", "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"]:
                # Update current position based on the move
                current_position = move_position(current_position, action, grid)
            elif action == "DROP":
                energy_carried = 0
                
            planned_actions.append(action)
            actions_used += 1
            
            if actions_used >= max_actions:
                break
                
        # Remove collected energy positions from available positions
        energy_positions = [pos for pos in energy_positions if pos not in visited_energy_positions]
        
    return planned_actions

def find_agent_position(grid):
    # Find and return the position (row, col) of the agent 'A' in the grid
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == 'A':
                return (i, j)
    return None

def find_all_energy_positions(grid):
    # Find and return a list of positions of all energy tokens 'E' in the grid
    energy_positions = []
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == 'E':
                energy_positions.append((i, j))
    return energy_positions

def plan_path(start, end, grid, is_diagonals_allowed):
    # A* pathfinding algorithm
    if start == end:
        return []
        
    # Define possible moves based on allowed directions
    if not is_diagonals_allowed:
        moves = [("UP", -1, 0), ("DOWN", 1, 0), ("LEFT", 0, -1), ("RIGHT", 0, 1)]
    else:  # 8 directions
        moves = [
            ("UP", -1, 0), ("DOWN", 1, 0), ("LEFT", 0, -1), ("RIGHT", 0, 1),
            ("UPLEFT", -1, -1), ("UPRIGHT", -1, 1), ("DOWNLEFT", 1, -1), ("DOWNRIGHT", 1, 1)
        ]
        
    # Manhattan distance heuristic function
    def heuristic(pos):
        return abs(pos[0] - end[0]) + abs(pos[1] - end[1])
        
    # Priority queue using list
    open_set = [(heuristic(start), 0, start, [])]  # (f_score, g_score, position, path)
    visited = set()
    
    while open_set:
        open_set.sort()  # Sort by f_score
        _, g_score, current, path = open_set.pop(0)
        
        if current == end:
            return path
            
        if current in visited:
            continue
            
        visited.add(current)
        
        for direction, dr, dc in moves:
            row, col = current
            new_row, new_col = row + dr, col + dc
            new_pos = (new_row, new_col)
            
            # Check if the new position is valid
            if (0 <= new_row < len(grid) and 0 <= new_col < len(grid[0]) and
                grid[new_row][new_col] != 'O' and new_pos not in visited):
                new_g = g_score + 1
                new_f = new_g + heuristic(new_pos)
                open_set.append((new_f, new_g, new_pos, path + [direction]))
                
    return []  # No path found

def move_position(position, direction, grid):
    row, col = position
    if direction == "UP":
        return (row - 1, col)
    elif direction == "DOWN":
        return (row + 1, col)
    elif direction == "LEFT":
        return (row, col - 1)
    elif direction == "RIGHT":
        return (row, col + 1)
    elif direction == "UPLEFT":
        return (row - 1, col - 1)
    elif direction == "UPRIGHT":
        return (row - 1, col + 1)
    elif direction == "DOWNLEFT":
        return (row + 1, col - 1)
    elif direction == "DOWNRIGHT":
        return (row + 1, col + 1)
    return position

def get_position_after_moves(start_position, moves, grid):
    position = start_position
    for move in moves:
        if move in ["UP", "DOWN", "LEFT", "RIGHT", "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"]:
            position = move_position(position, move, grid)
    return position

def evaluate_trip_value(trip_actions, energy_collected, cost_per_step):
    # Count movement actions (excluding TAKE and DROP)
    movement_actions = sum(1 for action in trip_actions 
                          if action not in ["TAKE", "DROP"])
    # Calculate the net energy gain
    cost = movement_actions * cost_per_step
    return energy_collected - cost

def plan_efficient_energy_collection(current_pos, energy_positions, grid, start_pos, 
                                   energy_carried, carry_limit, actions_left, 
                                   cost_per_step, allowed_directions):
    """
    Plans an efficient multi-token collection trip using a greedy approach with lookahead.
    """
    if not energy_positions or energy_carried >= carry_limit or actions_left <= 3:
        return None
        
    # Maximum number of additional tokens we can collect
    max_collectable = min(carry_limit - energy_carried, len(energy_positions))
    if max_collectable <= 0:
        return None
        
    # Calculate distance metric for each energy token
    energy_with_distance = []
    for pos in energy_positions:
        path = plan_path(current_pos, pos, grid, allowed_directions)
        if path:  # Only consider reachable positions
            distance = len(path)
            energy_with_distance.append((pos, distance))
    
    # Sort by distance
    energy_with_distance.sort(key=lambda x: x[1])
    
    best_trip = None
    best_value = -float('inf')  # Start with negative infinity
    
    # Try different trip lengths
    for num_tokens in range(1, min(max_collectable + 1, 10)):  # Limit to avoid excessive computation
        # Try to construct a trip collecting exactly num_tokens
        trip_actions = []
        position = current_pos
        collected = 0
        remaining_energy = list(energy_with_distance)
        
        # Collect tokens greedily by distance
        while collected < num_tokens and remaining_energy and len(trip_actions) < actions_left - 5:
            # Always sort remaining_energy by distance from current position
            for i, (pos, _) in enumerate(remaining_energy):
                path = plan_path(position, pos, grid, allowed_directions)
                if path:
                    remaining_energy[i] = (pos, len(path))
                else:
                    remaining_energy[i] = (pos, float('inf'))
            
            remaining_energy.sort(key=lambda x: x[1])
            
            # Take the closest energy token
            if remaining_energy and remaining_energy[0][1] != float('inf'):
                next_pos, distance = remaining_energy[0]
                path_to_next = plan_path(position, next_pos, grid, allowed_directions)
                
                # Check if we have enough actions to collect this token and potentially return
                if len(trip_actions) + len(path_to_next) + 1 >= actions_left - 5:
                    break
                    
                # Add the path to this token and take action
                trip_actions.extend(path_to_next)
                trip_actions.append("TAKE")
                
                # Update state
                position = next_pos
                collected += 1
                remaining_energy.pop(0)
            else:
                break
        
        # If we collected some tokens, try to return to base
        if collected > 0:
            return_path = plan_path(position, start_pos, grid, allowed_directions)
            
            if return_path and len(trip_actions) + len(return_path) + 1 <= actions_left:
                complete_trip = trip_actions + return_path + ["DROP"]
                
                # Evaluate this trip
                trip_value = evaluate_trip_value(complete_trip, collected, cost_per_step)
                
                # Update best trip if this one is better
                if trip_value > best_value:
                    best_value = trip_value
                    best_trip = complete_trip
    
    # If we found a valuable trip, return it
    if best_trip and best_value > 0:
        return best_trip
        
    # If no multi-token trip is valuable, try a single nearest token
    if energy_with_distance:
        nearest_pos, distance = energy_with_distance[0]
        path_to_nearest = plan_path(current_pos, nearest_pos, grid, allowed_directions)
        
        if path_to_nearest:
            path_to_start = plan_path(nearest_pos, start_pos, grid, allowed_directions)
            
            if path_to_start and len(path_to_nearest) + 1 + len(path_to_start) + 1 <= actions_left:
                simple_trip = path_to_nearest + ["TAKE"] + path_to_start + ["DROP"]
                
                # Check if this simple trip is worthwhile
                trip_value = evaluate_trip_value(simple_trip, 1, cost_per_step)
                
                if trip_value > 0:
                    return simple_trip
    
    return None

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