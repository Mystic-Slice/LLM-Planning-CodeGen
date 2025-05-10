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
    holding_key = False
    
    # PHASE 1: Navigate to key and pick it up
    if key_position:
        # Find path to position from which to pick up the key
        paths_to_key = []
        
        # Check all four adjacent positions to the key
        directions = [[-1, 0], [0, 1], [1, 0], [0, -1]]  # Up, Right, Down, Left
        direction_names = ["DOWN", "LEFT", "UP", "RIGHT"]  # Opposite direction to face the key
        
        for i, (dx, dy) in enumerate(directions):
            adjacent_pos = [key_position[0] + dx, key_position[1] + dy]
            if is_valid_empty_cell(grid_copy, adjacent_pos):
                path = find_path(grid_copy, current_position, [adjacent_pos])
                if path:
                    paths_to_key.append((path, direction_names[i]))
        
        # Choose shortest path
        if paths_to_key:
            paths_to_key.sort(key=lambda x: len(x[0]))
            best_path, face_direction = paths_to_key[0]
            
            # Navigate to the position adjacent to key
            for next_pos in best_path:
                direction_to_move = determine_direction(current_position, next_pos)
                # Turn to face the right direction
                turn_actions = turn_to_direction(agent_direction, direction_to_move)
                actions.extend(turn_actions)
                agent_direction = direction_to_move
                # Move forward
                actions.append("MOVE")
                current_position = next_pos
            
            # Face the key
            turn_actions = turn_to_direction(agent_direction, face_direction)
            actions.extend(turn_actions)
            agent_direction = face_direction
            
            # Pick up the key
            actions.append("PICKUP")
            holding_key = True
    
    # PHASE 2: Navigate to door and unlock it
    if door_position and holding_key:
        # Similar approach for the door
        paths_to_door = []
        
        # Check all four adjacent positions to the door
        directions = [[-1, 0], [0, 1], [1, 0], [0, -1]]  # Up, Right, Down, Left
        direction_names = ["DOWN", "LEFT", "UP", "RIGHT"]  # Opposite direction to face the door
        
        for i, (dx, dy) in enumerate(directions):
            adjacent_pos = [door_position[0] + dx, door_position[1] + dy]
            if is_valid_empty_cell(grid_copy, adjacent_pos):
                path = find_path(grid_copy, current_position, [adjacent_pos])
                if path:
                    paths_to_door.append((path, direction_names[i]))
        
        # Choose shortest path
        if paths_to_door:
            paths_to_door.sort(key=lambda x: len(x[0]))
            best_path, face_direction = paths_to_door[0]
            
            # Navigate to the position adjacent to door
            for next_pos in best_path:
                direction_to_move = determine_direction(current_position, next_pos)
                # Turn to face the right direction
                turn_actions = turn_to_direction(agent_direction, direction_to_move)
                actions.extend(turn_actions)
                agent_direction = direction_to_move
                # Move forward
                actions.append("MOVE")
                current_position = next_pos
            
            # Face the door
            turn_actions = turn_to_direction(agent_direction, face_direction)
            actions.extend(turn_actions)
            agent_direction = face_direction
            
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