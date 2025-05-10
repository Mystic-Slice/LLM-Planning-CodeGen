def solve_grid(grid, start_position, max_actions):
    """
    Solves the energy collection game.
    
    Args:
        grid: 2D list representing the game grid ('A' is agent, 'E' is energy)
        start_position: Tuple (row, col) of the starting position
        max_actions: Maximum number of actions allowed
        
    Returns:
        List of actions to take: "UP", "DOWN", "LEFT", "RIGHT", "TAKE", "DROP"
    """
    # Find all energy token positions
    energy_positions = find_all_energy_positions(grid)
    
    # Initialize variables
    current_position = start_position
    actions_taken = []
    actions_used = 0
    carrying_energy = 0
    
    while actions_used < max_actions:
        # If no energy tokens remain or can't complete another cycle, return to start and drop
        if len(energy_positions) == 0 or not can_complete_another_cycle(current_position, energy_positions, start_position, max_actions - actions_used):
            # Return to starting position if not already there
            if current_position != start_position:
                path_to_start = find_shortest_path(current_position, start_position)
                for move in path_to_start:
                    actions_taken.append(move)
                    actions_used += 1
                    if actions_used >= max_actions:
                        return actions_taken
                current_position = start_position
            
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
        nearest_energy = find_nearest_energy(current_position, energy_positions)
        path_to_energy = find_shortest_path(current_position, nearest_energy)
        
        # Follow path to the nearest energy
        for move in path_to_energy:
            actions_taken.append(move)
            actions_used += 1
            if actions_used >= max_actions:
                return actions_taken
        
        # Take the energy
        actions_taken.append("TAKE")
        actions_used += 1
        carrying_energy += 1
        current_position = nearest_energy
        energy_positions.remove(nearest_energy)
        
        # Check if we should return to drop off (based on distance to start vs. continuing)
        if should_return_to_drop(current_position, energy_positions, start_position, carrying_energy, max_actions - actions_used):
            # Path to starting position
            path_to_start = find_shortest_path(current_position, start_position)
            for move in path_to_start:
                actions_taken.append(move)
                actions_used += 1
                if actions_used >= max_actions:
                    return actions_taken
            
            # Drop energy
            actions_taken.append("DROP")
            carrying_energy = 0
            actions_used += 1
            current_position = start_position
    
    return actions_taken


def find_all_energy_positions(grid):
    """Find all cells with energy tokens."""
    energy_positions = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 'E':
                energy_positions.append((row, col))
    return energy_positions


def find_nearest_energy(current_pos, energy_positions):
    """Find the nearest energy token position using Manhattan distance."""
    if not energy_positions:
        return None
        
    nearest = None
    min_distance = float('inf')
    
    for pos in energy_positions:
        dist = manhattan_distance(current_pos, pos)
        if dist < min_distance:
            min_distance = dist
            nearest = pos
            
    return nearest


def manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def find_shortest_path(start, end):
    """
    Find the shortest path from start to end using Manhattan distance.
    Returns list of moves: "UP", "DOWN", "LEFT", "RIGHT"
    """
    path = []
    current = start
    
    while current != end:
        if current[0] < end[0]:
            path.append("DOWN")
            current = (current[0] + 1, current[1])
        elif current[0] > end[0]:
            path.append("UP")
            current = (current[0] - 1, current[1])
        elif current[1] < end[1]:
            path.append("RIGHT")
            current = (current[0], current[1] + 1)
        elif current[1] > end[1]:
            path.append("LEFT")
            current = (current[0], current[1] - 1)
    
    return path


def can_complete_another_cycle(current_pos, energy_positions, start_pos, remaining_actions):
    """Check if there are enough actions left to collect another energy and return to start."""
    if not energy_positions:
        return False
        
    # Minimum actions: go to nearest energy, take it, return to start, drop it
    nearest_energy = find_nearest_energy(current_pos, energy_positions)
    min_actions_needed = manhattan_distance(current_pos, nearest_energy) + 1 + manhattan_distance(nearest_energy, start_pos) + 1
    return min_actions_needed <= remaining_actions


def should_return_to_drop(current_pos, energy_positions, start_pos, carrying_energy, remaining_actions):
    """Determine if agent should return to the start to drop collected energy."""
    # Calculate if it's better to return now or get more energy
    distance_to_start = manhattan_distance(current_pos, start_pos)
    
    # If we can't make it back to start with our current energy, return now
    if distance_to_start + 1 >= remaining_actions:
        return True
    
    # If we're carrying a significant amount of energy, return to drop it off
    if carrying_energy >= 5:
        return True
        
    # If there are no more energy tokens, return
    if len(energy_positions) == 0:
        return True
    
    # Check if we can get another energy and still return
    nearest_energy = find_nearest_energy(current_pos, energy_positions)
    actions_for_one_more = manhattan_distance(current_pos, nearest_energy) + 1 + manhattan_distance(nearest_energy, start_pos) + 1
    
    return actions_for_one_more >= remaining_actions

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