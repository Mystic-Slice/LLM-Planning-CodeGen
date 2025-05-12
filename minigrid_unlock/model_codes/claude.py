from collections import deque

def solve(grid, start_direction):
    """
    Solve the grid-based door unlocking game.
    
    Args:
        grid: 2D list representing the environment
        start_direction: Starting direction of the agent (UP, DOWN, LEFT, RIGHT)
        
    Returns:
        List of actions to complete the task
    """
    # Initialize agent state
    agent_position = find_agent(grid)
    agent_direction = start_direction
    actions = []
    
    # Create a copy of the grid for pathfinding (replace AGENT with empty space)
    grid_copy = [row[:] for row in grid]
    grid_copy[agent_position[0]][agent_position[1]] = ""
    
    # Find key and door positions
    key_position = find_object(grid, "KEY")
    door_position = find_object(grid, "DOOR")
    
    # Current position of the agent (after removing from grid for path finding)
    current_position = agent_position
    
    # PHASE 1: Navigate to a cell adjacent to the key
    if key_position:
        # Find adjacent cells to the key
        adjacent_positions = find_adjacent_cells(grid_copy, key_position)
        
        # Find path to position adjacent to key
        path_to_key_adjacency = find_path(grid_copy, current_position, adjacent_positions)
        
        if path_to_key_adjacency:
            # Navigate to the position adjacent to key
            for next_pos in path_to_key_adjacency:
                direction_to_move = determine_direction(current_position, next_pos)
                
                # Turn to face the right direction
                turn_actions = turn_to_direction(agent_direction, direction_to_move)
                actions.extend(turn_actions)
                agent_direction = direction_to_move
                
                # Move forward
                actions.append("MOVE")
                current_position = next_pos
            
            # Face the key
            key_direction = determine_direction(current_position, key_position)
            turn_actions = turn_to_direction(agent_direction, key_direction)
            actions.extend(turn_actions)
            agent_direction = key_direction
            
            # Pick up the key
            actions.append("PICKUP")
    
    # PHASE 2: Navigate to a cell adjacent to the door
    if door_position:
        # Find adjacent cells to the door
        adjacent_positions = find_adjacent_cells(grid_copy, door_position)
        
        # Find path to position adjacent to door
        path_to_door_adjacency = find_path(grid_copy, current_position, adjacent_positions)
        
        if path_to_door_adjacency:
            # Navigate to the position adjacent to door
            for next_pos in path_to_door_adjacency:
                direction_to_move = determine_direction(current_position, next_pos)
                
                # Turn to face the right direction
                turn_actions = turn_to_direction(agent_direction, direction_to_move)
                actions.extend(turn_actions)
                agent_direction = direction_to_move
                
                # Move forward
                actions.append("MOVE")
                current_position = next_pos
            
            # Face the door
            door_direction = determine_direction(current_position, door_position)
            turn_actions = turn_to_direction(agent_direction, door_direction)
            actions.extend(turn_actions)
            agent_direction = door_direction
            
            # Unlock the door
            actions.append("UNLOCK")
    
    return actions

def find_agent(grid):
    """Find the agent's position in the grid."""
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == "AGENT":
                return [i, j]
    return None

def find_object(grid, object_type):
    """Find the position of a specific object in the grid."""
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] == object_type:
                return [i, j]
    return None

def find_adjacent_cells(grid, position):
    """Find all valid empty cells adjacent to a position."""
    adjacent_cells = []
    directions = [[-1, 0], [0, 1], [1, 0], [0, -1]]  # Up, Right, Down, Left
    
    for dx, dy in directions:
        new_x, new_y = position[0] + dx, position[1] + dy
        if is_valid_empty_cell(grid, [new_x, new_y]):
            adjacent_cells.append([new_x, new_y])
    
    return adjacent_cells

def is_valid_empty_cell(grid, position):
    """Check if a cell is within grid bounds and is empty."""
    row, col = position
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[0]):
        return False
    return grid[row][col] == ""

def find_path(grid, start, targets):
    """
    Use BFS to find shortest path from start to any of the target positions.
    
    Args:
        grid: The game grid
        start: Starting position [row, col]
        targets: List of potential target positions
        
    Returns:
        Path from start to the closest target (excluding the target itself)
    """
    if not targets:
        return []
    
    queue = deque([start])
    visited = {tuple(start): None}  # Maps positions to their parent
    target_set = {tuple(pos) for pos in targets}
    
    while queue:
        current = queue.popleft()
        current_tuple = tuple(current)
        
        # Check if current position is a target
        if current_tuple in target_set:
            # Reconstruct path from start to target
            path = []
            while current_tuple != tuple(start):
                path.append(list(current_tuple))
                current_tuple = visited[current_tuple]
            return path[::-1]  # Reverse path to get start -> target
        
        # Explore all four directions
        directions = [[-1, 0], [0, 1], [1, 0], [0, -1]]  # Up, Right, Down, Left
        
        for dx, dy in directions:
            new_pos = [current[0] + dx, current[1] + dy]
            new_pos_tuple = tuple(new_pos)
            
            if (is_valid_empty_cell(grid, new_pos) and 
                new_pos_tuple not in visited):
                queue.append(new_pos)
                visited[new_pos_tuple] = current_tuple
    
    return []  # No path found

def determine_direction(current_pos, target_pos):
    """Determine the direction from current position to target position."""
    if target_pos[0] < current_pos[0]:
        return "UP"
    elif target_pos[0] > current_pos[0]:
        return "DOWN"
    elif target_pos[1] < current_pos[1]:
        return "LEFT"
    elif target_pos[1] > current_pos[1]:
        return "RIGHT"
    return None

def turn_to_direction(current_direction, target_direction):
    """Generate turning actions to change from current direction to target direction."""
    if current_direction == target_direction:
        return []
    
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    current_idx = directions.index(current_direction)
    target_idx = directions.index(target_direction)
    
    # Calculate the number of turns needed in each direction
    left_turns = (4 + current_idx - target_idx) % 4
    right_turns = (4 + target_idx - current_idx) % 4
    
    # Choose the shorter turning direction
    if left_turns <= right_turns:
        return ["LEFT"] * left_turns
    else:
        return ["RIGHT"] * right_turns

if __name__ == "__main__":
    # Example grid and direction
    grid = [
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"],
["WALL","","","","KEY","WALL","","","","","WALL"],
["WALL","","","AGENT","","WALL","","","","","WALL"],
["WALL","","","","","DOOR","","","","","WALL"],
["WALL","","","","","WALL","","","","","WALL"],
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"]
    ]
    direction = "RIGHT"
    
    actions = solve(grid, direction)
    print("Actions to solve the game:", actions)