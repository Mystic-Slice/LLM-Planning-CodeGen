import heapq
from collections import deque

def solve_grid(grid, start_pos, carry_limit, cost_per_step, is_diagonals_allowed, max_actions):
    """
    Solve the energy collection game.
    
    Args:
        grid (list): 2D grid representing the game state ('A' for agent, 'E' for energy, 'O' for obstacles)
        start_pos (tuple): Starting position of the agent (row, col)
        carry_limit (int): Maximum number of energy tokens that can be carried at once
        cost_per_step (int): Energy cost for each movement step
        is_diagonals_allowed (bool): Whether diagonal movements are allowed
        max_actions (int): Maximum number of actions that can be performed
        
    Returns:
        list: List of actions to perform in the game
    """
    actions = []
    current_pos = start_pos
    actions_remaining = max_actions
    current_load = 0
    
    # Find all energy positions in the grid
    energy_positions = []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == 'E':
                energy_positions.append((r, c))
    
    # Compute distance matrix between all positions
    distance_matrix = compute_distance_matrix(grid, energy_positions, start_pos, is_diagonals_allowed)
    
    while actions_remaining > 0 and energy_positions:
        # Check if we're at carrying capacity
        if current_load >= carry_limit:
            # Return to start and drop
            path_to_start = find_path(grid, current_pos, start_pos, is_diagonals_allowed)
            if not path_to_start or len(path_to_start) + 1 > actions_remaining:  # +1 for DROP
                break  # Can't return in time
            
            for direction in path_to_start:
                actions.append(direction)
                actions_remaining -= 1
            
            actions.append("DROP")
            actions_remaining -= 1
            current_pos = start_pos
            current_load = 0
            continue
        
        # Find best next energy position
        best_next_pos, best_path = find_best_next_energy(
            grid, current_pos, energy_positions, start_pos, is_diagonals_allowed,
            actions_remaining, current_load, carry_limit, distance_matrix, cost_per_step
        )
        
        if best_next_pos is None:
            # No viable energy token can be reached and returned from
            # Return to start if carrying energy
            if current_load > 0:
                path_to_start = find_path(grid, current_pos, start_pos, is_diagonals_allowed)
                if path_to_start and len(path_to_start) + 1 <= actions_remaining:  # +1 for DROP
                    for direction in path_to_start:
                        actions.append(direction)
                        actions_remaining -= 1
                    actions.append("DROP")
                    actions_remaining -= 1
            break
        
        # Move to the best energy position and take it
        for direction in best_path:
            actions.append(direction)
            actions_remaining -= 1
        
        actions.append("TAKE")
        actions_remaining -= 1
        current_load += 1
        current_pos = best_next_pos
        energy_positions.remove(best_next_pos)
        
        # Check if we have enough actions to reach more energy and return
        steps_to_start = len(find_path(grid, current_pos, start_pos, is_diagonals_allowed))
        if steps_to_start + 1 >= actions_remaining:  # +1 for DROP
            path_to_start = find_path(grid, current_pos, start_pos, is_diagonals_allowed)
            if path_to_start:  # Make sure we have a valid path
                for direction in path_to_start:
                    actions.append(direction)
                    actions_remaining -= 1
                actions.append("DROP")
                actions_remaining -= 1
            break
    
    # Return to start with any remaining energy if possible
    if current_load > 0 and current_pos != start_pos:
        path_to_start = find_path(grid, current_pos, start_pos, is_diagonals_allowed)
        if path_to_start and len(path_to_start) + 1 <= actions_remaining:  # +1 for DROP
            for direction in path_to_start:
                actions.append(direction)
                actions_remaining -= 1
            actions.append("DROP")
            actions_remaining -= 1
    
    return actions

def find_best_next_energy(grid, current_pos, energy_positions, start_pos, is_diagonals_allowed, 
                          actions_remaining, current_load, carry_limit, distance_matrix, cost_per_step):
    """
    Find the best next energy token to collect based on optimized path planning.
    
    Returns:
        tuple: (best_position, best_path)
    """
    best_position = None
    best_path = None
    best_score = float('-inf')
    
    for energy_pos in energy_positions:
        # Skip if we're already at capacity
        if current_load >= carry_limit:
            break
        
        # Get the path to this energy token
        path_to_energy = find_path(grid, current_pos, energy_pos, is_diagonals_allowed)
        if not path_to_energy:
            continue  # Skip if no path exists
        
        # Get path from energy back to start
        path_from_energy_to_start = find_path(grid, energy_pos, start_pos, is_diagonals_allowed)
        if not path_from_energy_to_start:
            continue  # Skip if cannot return to start
            
        total_actions_needed = len(path_to_energy) + len(path_from_energy_to_start) + 2  # +2 for TAKE and DROP
        
        if total_actions_needed > actions_remaining:
            continue  # Not enough actions to reach this energy and return to start
        
        # Calculate score metrics
        distance_to_energy = len(path_to_energy)
        distance_factor = 1.0 / max(1, distance_to_energy)
        
        # Estimate potential for additional collection
        additional_collection_potential = min(
            carry_limit - current_load - 1,  # -1 since we're picking up this token
            count_tokens_on_return_path(energy_pos, start_pos, energy_positions, distance_matrix)
        )
        
        # Calculate overall score
        score = distance_factor * (1 + 0.5 * additional_collection_potential) - (distance_to_energy * cost_per_step / 10)
        
        if score > best_score:
            best_score = score
            best_position = energy_pos
            best_path = path_to_energy
    
    return best_position, best_path

def count_tokens_on_return_path(energy_pos, start_pos, energy_positions, distance_matrix):
    """Estimate how many energy tokens are roughly along the path from energy_pos to start_pos"""
    count = 0
    
    if energy_pos not in distance_matrix or start_pos not in distance_matrix.get(energy_pos, {}):
        return 0
        
    direct_distance = distance_matrix[energy_pos][start_pos]
    
    for pos in energy_positions:
        if pos == energy_pos:
            continue
        
        # Check if position is in our distance matrix
        if (pos in distance_matrix.get(energy_pos, {}) and 
            pos in distance_matrix.get(start_pos, {})):
            
            # If this position is roughly on the way back (within 30% extra distance)
            if (distance_matrix[energy_pos][pos] + distance_matrix[pos][start_pos] <= 
                direct_distance * 1.3):
                count += 1
    
    return count

def compute_distance_matrix(grid, energy_positions, start_position, is_diagonals_allowed):
    """Compute a matrix of shortest path distances between all energy positions and start position"""
    all_positions = energy_positions + [start_position]
    distance_matrix = {}
    
    for pos_i in all_positions:
        distance_matrix[pos_i] = {}
        for pos_j in all_positions:
            if pos_i == pos_j:
                distance_matrix[pos_i][pos_j] = 0
            else:
                path = find_path(grid, pos_i, pos_j, is_diagonals_allowed)
                distance_matrix[pos_i][pos_j] = len(path) if path else float('inf')
    
    return distance_matrix

def find_path(grid, from_pos, to_pos, is_diagonals_allowed):
    """Find the shortest path between two positions using A* search"""
    if from_pos == to_pos:
        return []
    
    rows, cols = len(grid), len(grid[0])
    
    # Define possible directions
    directions = [("UP", -1, 0), ("RIGHT", 0, 1), ("DOWN", 1, 0), ("LEFT", 0, -1)]
    if is_diagonals_allowed:
        directions.extend([
            ("UPLEFT", -1, -1), ("UPRIGHT", -1, 1), 
            ("DOWNLEFT", 1, -1), ("DOWNRIGHT", 1, 1)
        ])
    
    # A* search
    open_set = [(manhattan_distance(from_pos, to_pos), 0, from_pos, [])]  # (f_score, g_score, position, path)
    visited = set()
    
    while open_set:
        _, g_score, current, path = heapq.heappop(open_set)
        
        if current == to_pos:
            return path
        
        if current in visited:
            continue
            
        visited.add(current)
        
        for direction, dr, dc in directions:
            next_r, next_c = current[0] + dr, current[1] + dc
            
            # Check bounds and obstacles
            if (0 <= next_r < rows and 0 <= next_c < cols and 
                grid[next_r][next_c] != 'O' and (next_r, next_c) not in visited):
                
                new_g = g_score + 1
                new_f = new_g + manhattan_distance((next_r, next_c), to_pos)
                new_path = path + [direction]
                
                heapq.heappush(open_set, (new_f, new_g, (next_r, next_c), new_path))
    
    return []  # No path found

def manhattan_distance(pos1, pos2):
    """Calculate Manhattan distance between two positions"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


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