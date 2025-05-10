def solve_energy_collection_game(grid_str, start_pos, movement_dirs, carry_limit, move_cost, max_actions=20):
    grid, _, _ = parse_grid(grid_str)
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
            
        # If at capacity or no more energy tokens to collect, return to start
        if energy_carried == carry_limit or len(energy_positions) == 0:
            # Plan path back to starting position
            return_path = plan_path(current_position, start_position, grid, movement_dirs)
            
            # If no valid path or not enough actions left, drop energy and end
            if len(return_path) == 0 or actions_used + len(return_path) + 1 > max_actions:
                # Move towards start as much as possible
                remaining_actions = max_actions - actions_used - 1  # Save 1 action for DROP
                partial_return_path = return_path[:remaining_actions] if remaining_actions > 0 else []
                planned_actions.extend(partial_return_path)
                actions_used += len(partial_return_path)
                
                # Drop energy if we made it back to start
                if len(partial_return_path) == len(return_path):
                    planned_actions.append("DROP")
                break
                
            # Execute return path
            planned_actions.extend(return_path)
            actions_used += len(return_path)
            current_position = start_position
            continue
        
        # Find the best energy token to collect next
        next_target = find_best_energy_target(current_position, energy_positions, grid, 
                                             start_position, energy_carried, carry_limit,
                                             max_actions - actions_used, movement_dirs)
        
        # If no valid target found, return to start
        if next_target is None:
            # Plan path back to starting position
            return_path = plan_path(current_position, start_position, grid, movement_dirs)
            
            # If can make it back in time, go back and drop
            if len(return_path) + 1 <= max_actions - actions_used:
                planned_actions.extend(return_path)
                planned_actions.append("DROP")
                actions_used += len(return_path) + 1
            else:
                # Move as close to start as possible
                remaining_actions = max_actions - actions_used
                partial_path = return_path[:remaining_actions]
                planned_actions.extend(partial_path)
                actions_used += len(partial_path)
            break
            
        # Plan path to the best target
        path_to_target = plan_path(current_position, next_target, grid, movement_dirs)
        
        # Check if we have enough actions to collect the energy and go back
        path_back_to_start = plan_path(next_target, start_position, grid, movement_dirs)
        if actions_used + len(path_to_target) + 1 + len(path_back_to_start) + 1 > max_actions:
            # Not enough actions to collect and return, head back to start
            return_path = plan_path(current_position, start_position, grid, movement_dirs)
            
            # If can make it back in time, go back and drop
            if len(return_path) + 1 <= max_actions - actions_used:
                planned_actions.extend(return_path)
                planned_actions.append("DROP")
                actions_used += len(return_path) + 1
            else:
                # Move as close to start as possible
                remaining_actions = max_actions - actions_used
                partial_path = return_path[:remaining_actions]
                planned_actions.extend(partial_path)
                actions_used += len(partial_path)
            break
            
        # Execute path to target
        planned_actions.extend(path_to_target)
        planned_actions.append("TAKE")
        
        actions_used += len(path_to_target) + 1
        current_position = next_target
        energy_carried += 1
        energy_positions.remove(next_target)
        
        # If at max capacity, return to start
        if energy_carried == carry_limit:
            continue  # This will trigger the return-to-start logic in the next iteration
    
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


def plan_path(start, end, grid, allowed_directions):
    # Implement A* pathfinding algorithm to find the shortest path from start to end
    # Returns a list of directions ("UP", "DOWN", "LEFT", "RIGHT", etc.)
    # This is a simplified version - a real implementation would use a priority queue
    
    # Define possible moves based on allowed directions
    if len(allowed_directions) == 4:
        moves = [("UP", -1, 0), ("DOWN", 1, 0), ("LEFT", 0, -1), ("RIGHT", 0, 1)]
    else:  # 8 directions
        moves = [
            ("UP", -1, 0), ("DOWN", 1, 0), ("LEFT", 0, -1), ("RIGHT", 0, 1),
            ("UPLEFT", -1, -1), ("UPRIGHT", -1, 1), ("DOWNLEFT", 1, -1), ("DOWNRIGHT", 1, 1)
        ]
    
    # Use breadth-first search for simplicity
    visited = set()
    queue = [(start, [])]  # (position, path_so_far)
    
    while queue:
        (row, col), path = queue.pop(0)
        
        if (row, col) == end:
            return path
            
        if (row, col) in visited:
            continue
            
        visited.add((row, col))
        
        for direction, dr, dc in moves:
            new_row, new_col = row + dr, col + dc
            
            # Check if the new position is valid
            if (0 <= new_row < len(grid) and 0 <= new_col < len(grid[0]) and 
                grid[new_row][new_col] != 'O' and (new_row, new_col) not in visited):
                queue.append(((new_row, new_col), path + [direction]))
    
    return []  # No path found

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


def find_best_energy_target(current_pos, energy_positions, grid, start_pos, 
                          energy_carried, max_capacity, actions_left, allowed_directions):
    """
    Find the best energy token to collect next.
    Strategy: Use a utility function that balances:
    1. Distance to the energy token
    2. Distance from energy token to start position
    3. Clusters of energy tokens (prefer areas with high energy density)
    """
    if len(energy_positions) == 0:
        return None
        
    # Calculate utility for each energy position
    best_utility = float('-inf')
    best_target = None
    
    for energy_pos in energy_positions:
        # Path to energy token
        path_to_energy = plan_path(current_pos, energy_pos, grid, allowed_directions)
        if not path_to_energy:
            continue  # Skip if no path exists
            
        # Path from energy token to start
        path_to_start = plan_path(energy_pos, start_pos, grid, allowed_directions)
        if not path_to_start:
            continue  # Skip if no path to start exists
            
        # Check if we have enough actions left to collect and return
        total_actions_needed = len(path_to_energy) + 1 + len(path_to_start) + 1  # +1 for TAKE and +1 for DROP
        if total_actions_needed > actions_left:
            continue  # Skip this target if we can't make it back in time
            
        # Calculate energy density (number of nearby energy tokens)
        nearby_energy = 0
        for r in range(-2, 3):  # Check a 5x5 area
            for c in range(-2, 3):
                nearby_pos = (energy_pos[0] + r, energy_pos[1] + c)
                if nearby_pos in energy_positions:
                    nearby_energy += 1
                    
        # Calculate utility (customize weights as needed)
        distance_to_energy = len(path_to_energy)
        distance_to_start = len(path_to_start)
        
        # Utility function: prioritize closer energy tokens and those with higher nearby density
        # We also consider how easy it is to return to start from the energy token
        utility = (
            nearby_energy * 3 -               # Prioritize clusters
            distance_to_energy * 2 -          # Prefer closer energy tokens
            distance_to_start * 1             # Consider return trip
        )
        
        if utility > best_utility:
            best_utility = utility
            best_target = energy_pos
            
    return best_target

# def main():
#     # Sample grid as provided.
#     sample_grid = """
#     0   1   2   3   4   5   6   7   8   9   10
#   +---+---+---+---+---+---+---+---+---+---+---+
#  0|   | E | E |   |   |   | E | E |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  1| E | E | E |   | E | E |   | E | E |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  2| E |   |   | E |   | E | E | E | E |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  3|   | E | E |   |   | E | E | E |   | E | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  4| E | E |   | E | E | E | E | E | E |   | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  5|   | E |   |   |   |   |   | E |   | E | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  6| E |   |   | E | E | E | E | E |   |   |   |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  7|   | E |   |   |   | A | E | E | E | E | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  8| E | E |   | E |   |   | E | E | E |   | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
#  9| E |   | E | E | E |   | E | E |   | E | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
# 10|   | E |   | E | E |   |   |   |   |   | E |
#   +---+---+---+---+---+---+---+---+---+---+---+
#     """
#     # grid, agent_pos, energy_positions = parse_grid(sample_grid)
#     # print("Parsed grid:")
#     # for row in grid:
#     #     print(row)
    
#     # print("Agent position:", agent_pos)
#     # print("Energy positions:", energy_positions)

#     # Define parameters
#     start_position = (7, 5)
#     # start_position = [7, 5]
#     movement_directions = ["four", "eight"]
#     carry_limit = 100
#     move_cost = 0
#     max_actions = 20

#     # Solve the energy collection game
#     actions = solve_energy_collection_game(sample_grid, start_position, "eight", 
#                                            carry_limit, move_cost)
    
#     print("Planned actions:", actions)
#     print("Total actions:", len(actions))

# if __name__ == "__main__":
#     main()