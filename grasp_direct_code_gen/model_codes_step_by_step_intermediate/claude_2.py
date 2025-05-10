def solve_grid(grid, start_position, max_actions, diagonals_allowed=False, carry_limit=float('inf')):
    """
    Solves the energy collection game.
    
    Args:
        grid: 2D list representing the game grid ('A' is agent, 'E' is energy)
        start_position: Tuple (row, col) of the starting position
        max_actions: Maximum number of actions allowed
        diagonals_allowed: Boolean indicating whether diagonal moves are allowed
        carry_limit: Maximum number of energy tokens that can be carried at once
        
    Returns:
        List of actions to take: "UP", "DOWN", "LEFT", "RIGHT", "UPLEFT", "UPRIGHT", 
                                "DOWNLEFT", "DOWNRIGHT", "TAKE", "DROP"
    """
    # Find all energy token positions
    energy_positions = find_all_energy_positions(grid)
    
    # Initialize variables
    current_position = start_position
    actions_taken = []
    actions_used = 0
    carrying_energy = 0
    
    while actions_used < max_actions:
        # If we've reached the carry limit, return to start to drop
        if carrying_energy >= carry_limit:
            # Return to starting position if not already there
            if current_position != start_position:
                path_to_start = find_shortest_path(current_position, start_position, diagonals_allowed)
                for move in path_to_start:
                    actions_taken.append(move)
                    actions_used += 1
                    current_position = get_new_position(current_position, move)
                    if actions_used >= max_actions:
                        return actions_taken
            
            # Drop energy
            actions_taken.append("DROP")
            carrying_energy = 0
            actions_used += 1
            if actions_used >= max_actions:
                return actions_taken
            
            # Continue collecting if possible
            continue
            
        # If no energy tokens remain or can't complete another cycle, return to start and drop
        if len(energy_positions) == 0 or not can_complete_another_cycle(
                current_position, energy_positions, start_position, 
                max_actions - actions_used, diagonals_allowed):
                
            # Return to starting position if not already there
            if current_position != start_position:
                path_to_start = find_shortest_path(current_position, start_position, diagonals_allowed)
                for move in path_to_start:
                    actions_taken.append(move)
                    actions_used += 1
                    current_position = get_new_position(current_position, move)
                    if actions_used >= max_actions:
                        return actions_taken
            
            # Drop energy if carrying any
            if carrying_energy > 0:
                actions_taken.append("DROP")
                carrying_energy = 0
                actions_used += 1
                if actions_used >= max_actions:
                    return actions_taken
            
            # If no more energy tokens to collect, we're done
            if len(energy_positions) == 0:
                return actions_taken
        
        # Find the nearest energy token and go collect it
        nearest_energy = find_nearest_energy(current_position, energy_positions, diagonals_allowed)
        path_to_energy = find_shortest_path(current_position, nearest_energy, diagonals_allowed)
        
        # Follow path to the nearest energy
        for move in path_to_energy:
            actions_taken.append(move)
            actions_used += 1
            current_position = get_new_position(current_position, move)
            if actions_used >= max_actions:
                return actions_taken
        
        # Take the energy
        actions_taken.append("TAKE")
        actions_used += 1
        carrying_energy += 1
        energy_positions.remove(nearest_energy)
        
        # Check if we should return to drop off
        if should_return_to_drop(
                current_position, energy_positions, start_position, 
                carrying_energy, max_actions - actions_used, diagonals_allowed, carry_limit):
                
            # Path to starting position
            path_to_start = find_shortest_path(current_position, start_position, diagonals_allowed)
            for move in path_to_start:
                actions_taken.append(move)
                actions_used += 1
                current_position = get_new_position(current_position, move)
                if actions_used >= max_actions:
                    return actions_taken
            
            # Drop energy
            actions_taken.append("DROP")
            carrying_energy = 0
            actions_used += 1
            if actions_used >= max_actions:
                return actions_taken
    
    return actions_taken


def find_all_energy_positions(grid):
    """Find all cells with energy tokens."""
    energy_positions = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 'E':
                energy_positions.append((row, col))
    return energy_positions


def get_new_position(position, move):
    """Get the new position after making a move."""
    row, col = position
    if move == "UP":
        return (row - 1, col)
    elif move == "DOWN":
        return (row + 1, col)
    elif move == "LEFT":
        return (row, col - 1)
    elif move == "RIGHT":
        return (row, col + 1)
    elif move == "UPLEFT":
        return (row - 1, col - 1)
    elif move == "UPRIGHT":
        return (row - 1, col + 1)
    elif move == "DOWNLEFT":
        return (row + 1, col - 1)
    elif move == "DOWNRIGHT":
        return (row + 1, col + 1)
    return position


def find_nearest_energy(current_pos, energy_positions, diagonals_allowed):
    """Find the nearest energy token position."""
    if not energy_positions:
        return None
        
    nearest = None
    min_distance = float('inf')
    
    for pos in energy_positions:
        if diagonals_allowed:
            dist = chebyshev_distance(current_pos, pos)
        else:
            dist = manhattan_distance(current_pos, pos)
            
        if dist < min_distance:
            min_distance = dist
            nearest = pos
            
    return nearest


def manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def chebyshev_distance(pos1, pos2):
    """
    Calculate Chebyshev distance between two positions.
    This is appropriate when diagonal moves are allowed.
    """
    return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))


def estimate_path_length(start, end, diagonals_allowed):
    """Estimate the path length between two positions."""
    if diagonals_allowed:
        return chebyshev_distance(start, end)
    else:
        return manhattan_distance(start, end)


def find_shortest_path(start, end, diagonals_allowed):
    """
    Find the shortest path from start to end.
    Returns list of moves: "UP", "DOWN", "LEFT", "RIGHT" and optionally diagonal moves
    """
    path = []
    current = start
    
    while current != end:
        row_diff = end[0] - current[0]
        col_diff = end[1] - current[1]
        
        # Determine the best move
        if diagonals_allowed and row_diff != 0 and col_diff != 0:
            # Use diagonal moves when possible
            if row_diff < 0 and col_diff < 0:
                move = "UPLEFT"
                current = (current[0] - 1, current[1] - 1)
            elif row_diff < 0 and col_diff > 0:
                move = "UPRIGHT"
                current = (current[0] - 1, current[1] + 1)
            elif row_diff > 0 and col_diff < 0:
                move = "DOWNLEFT"
                current = (current[0] + 1, current[1] - 1)
            else:  # row_diff > 0 and col_diff > 0
                move = "DOWNRIGHT"
                current = (current[0] + 1, current[1] + 1)
        else:
            # Use cardinal directions
            if row_diff < 0:
                move = "UP"
                current = (current[0] - 1, current[1])
            elif row_diff > 0:
                move = "DOWN"
                current = (current[0] + 1, current[1])
            elif col_diff < 0:
                move = "LEFT"
                current = (current[0], current[1] - 1)
            elif col_diff > 0:
                move = "RIGHT"
                current = (current[0], current[1] + 1)
            else:
                break  # We've reached the destination
        
        path.append(move)
    
    return path


def can_complete_another_cycle(current_pos, energy_positions, start_pos, remaining_actions, diagonals_allowed):
    """Check if there are enough actions left to collect another energy and return to start."""
    if not energy_positions:
        return False
        
    # Minimum actions: go to nearest energy, take it, return to start, drop it
    nearest_energy = find_nearest_energy(current_pos, energy_positions, diagonals_allowed)
    path_to_energy = find_shortest_path(current_pos, nearest_energy, diagonals_allowed)
    path_to_start = find_shortest_path(nearest_energy, start_pos, diagonals_allowed)
    
    min_actions_needed = len(path_to_energy) + 1 + len(path_to_start) + 1
    return min_actions_needed <= remaining_actions


def should_return_to_drop(current_pos, energy_positions, start_pos, carrying_energy, remaining_actions, diagonals_allowed, carry_limit):
    """Determine if agent should return to the start to drop collected energy."""
    # If we're at the carry limit, we must return
    if carrying_energy >= carry_limit:
        return True
    
    # Calculate the path back to start
    path_to_start = find_shortest_path(current_pos, start_pos, diagonals_allowed)
    distance_to_start = len(path_to_start)
    
    # If we can't make it back to start with our current energy, return now
    if distance_to_start + 1 >= remaining_actions:
        return True
    
    # If we're carrying a significant amount of energy, return to drop it off
    # (but less than the carry limit, which we already checked)
    if carrying_energy >= min(5, carry_limit):
        return True
        
    # If there are no more energy tokens, return
    if len(energy_positions) == 0:
        return True
    
    # Check how many more energy tokens we could collect before reaching the carry limit
    remaining_capacity = carry_limit - carrying_energy
    
    # Check if we can get another energy and still return
    nearest_energy = find_nearest_energy(current_pos, energy_positions, diagonals_allowed)
    path_to_energy = find_shortest_path(current_pos, nearest_energy, diagonals_allowed)
    path_from_energy_to_start = find_shortest_path(nearest_energy, start_pos, diagonals_allowed)
    
    actions_for_one_more = len(path_to_energy) + 1 + len(path_from_energy_to_start) + 1
    
    # If we have only one spot left in capacity, check if we can fit one more trip
    if remaining_capacity == 1 and actions_for_one_more <= remaining_actions:
        return False  # Go get that one last energy before returning
    
    # If we can't fit another trip in the remaining actions, return now
    return actions_for_one_more > remaining_actions

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