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
        
        # If carrying at capacity or no more energy tokens to collect, return to start
        if energy_carried >= carry_limit or len(energy_positions) == 0:
            # Plan path back to starting position
            return_path = plan_path(current_position, start_position, grid, is_diagonals_allowed)
            
            # If no valid path or not enough actions left, optimize what we can do
            if not return_path or len(return_path) + 1 > remaining_actions:
                # Move towards start as much as possible
                partial_return_path = return_path[:remaining_actions] if remaining_actions > 0 else []
                planned_actions.extend(partial_return_path)
                
                # If we made it back by chance, drop energy
                if partial_return_path and get_position_after_moves(current_position, partial_return_path, grid) == start_position:
                    if remaining_actions > len(partial_return_path):
                        planned_actions.append("DROP")
                
                break
            
            # Execute return path and drop
            planned_actions.extend(return_path)
            planned_actions.append("DROP")
            actions_used += len(return_path) + 1
            current_position = start_position
            energy_carried = 0
            continue
        
        # Plan the next trip - evaluate if we should collect more or return now
        best_trip = plan_best_trip(current_position, energy_positions, grid, start_position, 
                                   energy_carried, carry_limit, remaining_actions, cost_per_step, 
                                   is_diagonals_allowed)
        
        if not best_trip:
            # No viable trips, return to start if possible
            return_path = plan_path(current_position, start_position, grid, is_diagonals_allowed)
            
            if not return_path or len(return_path) + 1 > remaining_actions:
                # Can't make it back, move as far as possible toward start
                moves_possible = remaining_actions
                partial_path = return_path[:moves_possible] if moves_possible > 0 else []
                planned_actions.extend(partial_path)
                break
            else:
                # Can make it back, return and drop
                planned_actions.extend(return_path)
                if energy_carried > 0:
                    planned_actions.append("DROP")
                break
        
        # Execute the planned trip
        for action in best_trip:
            if action == "TAKE":
                energy_carried += 1
                # Remove this position from available energy positions
                energy_positions.remove(current_position)
            elif action in ["UP", "DOWN", "LEFT", "RIGHT", "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"]:
                # Update current position based on the move
                current_position = move_position(current_position, action, grid)
            elif action == "DROP":
                energy_carried = 0
            
            planned_actions.append(action)
            actions_used += 1
            
            if actions_used >= max_actions:
                break
    
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
    
    # Priority queue using list for simplicity
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
        position = move_position(position, move, grid)
    return position

def plan_best_trip(current_pos, energy_positions, grid, start_pos, energy_carried, carry_limit, 
                   actions_left, cost_per_step, allowed_directions):
    """
    Plan the optimal trip to collect energy and return to base.
    Returns a list of actions for the best trip.
    """
    if not energy_positions or energy_carried >= carry_limit or actions_left <= 1:
        return None
    
    # Try trips with increasing numbers of energy tokens
    best_trip = None
    best_net_energy = -1  # Net energy gain (after accounting for movement costs)
    
    # Find nearest energy tokens first
    sorted_energy_positions = sorted(energy_positions, 
                                   key=lambda pos: len(plan_path(current_pos, pos, grid, allowed_directions)))
    
    # Try collecting up to the carry limit
    tokens_to_try = min(carry_limit - energy_carried, len(sorted_energy_positions), actions_left // 3)
    
    # Generate combinations of energy tokens to collect in this trip
    # We'll start with greedy approach for efficiency
    for target_tokens in range(1, tokens_to_try + 1):
        path_so_far = []
        position = current_pos
        tokens_collected = 0
        actions_used = 0
        visited_positions = set()
        
        # Try to find a good path collecting exactly target_tokens
        remaining_tokens = list(sorted_energy_positions)  # Make a copy
        
        # While we can still collect tokens and have actions left
        while tokens_collected < target_tokens and remaining_tokens and actions_used < actions_left - 3:
            # Find nearest token
            best_next_token = min(remaining_tokens, 
                                key=lambda pos: len(plan_path(position, pos, grid, allowed_directions)))
            
            # Path to this token
            next_path = plan_path(position, best_next_token, grid, allowed_directions)
            
            if not next_path or actions_used + len(next_path) + 1 >= actions_left:
                break  # Can't reach this token within constraints
            
            # Add path to this token
            path_so_far.extend(next_path)
            actions_used += len(next_path) + 1  # +1 for TAKE
            tokens_collected += 1
            
            # Update position and remove this token
            position = best_next_token
            visited_positions.add(best_next_token)
            remaining_tokens.remove(best_next_token)
            path_so_far.append("TAKE")
        
        # If we collected some tokens, try to return to base
        if tokens_collected > 0:
            return_path = plan_path(position, start_pos, grid, allowed_directions)
            
            if return_path and actions_used + len(return_path) + 1 <= actions_left:
                # We can make it back
                complete_trip = path_so_far + return_path + ["DROP"]
                
                # Calculate net energy gain
                path_cost = (len(complete_trip) - tokens_collected - 1) * cost_per_step  # -1 for the DROP action
                net_energy = tokens_collected - path_cost
                
                if net_energy > best_net_energy:
                    best_net_energy = net_energy
                    best_trip = complete_trip
    
    # If no good multi-token trip found, try a simpler approach with just the nearest token
    if best_trip is None and sorted_energy_positions:
        nearest_token = sorted_energy_positions[0]
        path_to_token = plan_path(current_pos, nearest_token, grid, allowed_directions)
        
        if path_to_token:
            path_to_start = plan_path(nearest_token, start_pos, grid, allowed_directions)
            
            if path_to_start and len(path_to_token) + 1 + len(path_to_start) + 1 <= actions_left:
                simple_trip = path_to_token + ["TAKE"] + path_to_start + ["DROP"]
                
                # Check if this simple trip is worthwhile
                path_cost = (len(simple_trip) - 2) * cost_per_step  # -2 for TAKE and DROP
                net_energy = 1 - path_cost  # We collect 1 token
                
                if net_energy > 0:
                    best_trip = simple_trip
    
    return best_trip


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