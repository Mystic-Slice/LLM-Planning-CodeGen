def solve(grid, start_direction):
    """
    Solve the grid puzzle by finding the key, unlocking the door, and reaching the goal.
    Args:
        grid (List[List[str]]): 2D grid representing the environment
        start_direction (str): Initial facing direction of the agent ("UP", "DOWN", "LEFT", or "RIGHT")
    Returns:
        List[str]: List of actions to solve the puzzle
    """
    # Initialize variables
    agent_position = find_agent_position(grid)
    current_direction = start_direction
    all_actions_taken = []
    holding_key = False
    door_is_locked = True
    
    # Create a copy of the grid for path planning
    planning_grid = [row[:] for row in grid]
    
    # Map out key objects
    key_position = find_object(grid, "KEY")
    door_position = find_object(grid, "DOOR")
    goal_position = find_object(grid, "GOAL")
    
    # 1. GET THE KEY
    if not holding_key:
        # Check if agent is already adjacent to the key
        if is_adjacent(agent_position, key_position):
            # Face the key
            current_direction = face_object(agent_position, key_position, current_direction, all_actions_taken)
            # Pick up the key
            all_actions_taken.append("PICKUP")
            holding_key = True
            # Update planning grid to mark key as picked up
            planning_grid[key_position[0]][key_position[1]] = ""
        else:
            # Find a position adjacent to the key
            key_adjacent_positions = find_all_adjacent_positions(key_position, planning_grid)
            
            # Try each adjacent position until we find a valid path
            for key_adjacent in key_adjacent_positions:
                path = find_path(agent_position, key_adjacent, planning_grid, door_is_locked)
                if path:
                    # Execute path to position adjacent to key
                    agent_position, current_direction = execute_path(
                        path,
                        agent_position,
                        current_direction,
                        all_actions_taken
                    )
                    # Face the key
                    current_direction = face_object(agent_position, key_position, current_direction, all_actions_taken)
                    # Pick up the key
                    all_actions_taken.append("PICKUP")
                    holding_key = True
                    # Update planning grid to mark key as picked up
                    planning_grid[key_position[0]][key_position[1]] = ""
                    break
    
    # 2. UNLOCK THE DOOR
    if door_is_locked:
        # Check if agent is already adjacent to the door
        if is_adjacent(agent_position, door_position):
            # Face the door
            current_direction = face_object(agent_position, door_position, current_direction, all_actions_taken)
            # Unlock the door
            all_actions_taken.append("UNLOCK")
            door_is_locked = False
            # Update planning grid to mark door as passable
            planning_grid[door_position[0]][door_position[1]] = ""
        else:
            # Find positions adjacent to the door
            door_adjacent_positions = find_all_adjacent_positions(door_position, planning_grid)
            
            # Try each adjacent position until we find a valid path
            for door_adjacent in door_adjacent_positions:
                path = find_path(agent_position, door_adjacent, planning_grid, door_is_locked)
                if path:
                    # Execute path to position adjacent to door
                    agent_position, current_direction = execute_path(
                        path,
                        agent_position,
                        current_direction,
                        all_actions_taken
                    )
                    # Face the door
                    current_direction = face_object(agent_position, door_position, current_direction, all_actions_taken)
                    # Unlock the door
                    all_actions_taken.append("UNLOCK")
                    door_is_locked = False
                    # Update planning grid to mark door as passable
                    planning_grid[door_position[0]][door_position[1]] = ""
                    break
    
    # 3. REACH THE GOAL
    path = find_path(agent_position, goal_position, planning_grid, door_is_locked)
    if path:
        # Execute path to goal
        agent_position, current_direction = execute_path(
            path,
            agent_position,
            current_direction,
            all_actions_taken
        )
    
    return all_actions_taken

def find_agent_position(grid):
    """Find the position of the agent in the grid."""
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == "AGENT":
                return [row, col]
    return None

def find_object(grid, object_type):
    """Find the position of an object in the grid."""
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == object_type:
                return [row, col]
    return None

def find_all_adjacent_positions(target_position, grid):
    """Find all valid positions adjacent to the target."""
    row, col = target_position
    adjacent_positions = []
    
    # Check all four adjacent positions
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_row, new_col = row + dr, col + dc
        # Check if position is valid and empty or contains AGENT
        if (0 <= new_row < len(grid) and
            0 <= new_col < len(grid[0]) and
            (grid[new_row][new_col] == "" or grid[new_row][new_col] == "AGENT")):
            adjacent_positions.append([new_row, new_col])
    
    return adjacent_positions

def find_adjacent_position(target_position, grid):
    """Find a valid position adjacent to the target."""
    adjacent_positions = find_all_adjacent_positions(target_position, grid)
    if adjacent_positions:
        return adjacent_positions[0]
    return None

def is_adjacent(pos1, pos2):
    """Check if two positions are adjacent."""
    row1, col1 = pos1
    row2, col2 = pos2
    
    # Two positions are adjacent if they differ by 1 in exactly one coordinate
    return (abs(row1 - row2) == 1 and col1 == col2) or (abs(col1 - col2) == 1 and row1 == row2)

def find_path(start, end, grid, door_is_locked):
    """Find the shortest path from start to end using BFS."""
    if start == end:
        return [start]
    
    queue = [[start]]
    visited = set(tuple(start))
    
    while queue:
        path = queue.pop(0)
        current = path[-1]
        
        for neighbor in get_neighbors(current, grid, door_is_locked):
            neighbor_tuple = tuple(neighbor)
            if neighbor_tuple not in visited:
                new_path = path + [neighbor]
                if neighbor == end:
                    return new_path
                queue.append(new_path)
                visited.add(neighbor_tuple)
    
    return None  # No path found

def get_neighbors(position, grid, door_is_locked):
    """Get valid neighboring positions."""
    row, col = position
    neighbors = []
    
    # Check all four adjacent cells
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        new_row, new_col = row + dr, col + dc
        
        # Check if position is within bounds
        if 0 <= new_row < len(grid) and 0 <= new_col < len(grid[0]):
            cell_content = grid[new_row][new_col]
            
            # Valid moves are to empty cells, the goal, or unlocked doors
            if (cell_content == "" or
                cell_content == "GOAL" or
                (cell_content == "DOOR" and not door_is_locked)):
                neighbors.append([new_row, new_col])
    
    return neighbors

def get_direction(from_pos, to_pos):
    """Determine the direction from one position to another."""
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    if to_row < from_row:
        return "UP"
    elif to_row > from_row:
        return "DOWN"
    elif to_col < from_col:
        return "LEFT"
    else:
        return "RIGHT"

def turn_to_direction(current_direction, target_direction, actions):
    """
    Turn from current direction to target direction, adding the turning actions.
    Returns the new direction after turning.
    """
    while current_direction != target_direction:
        if ((current_direction == "UP" and target_direction == "RIGHT") or
            (current_direction == "RIGHT" and target_direction == "DOWN") or
            (current_direction == "DOWN" and target_direction == "LEFT") or
            (current_direction == "LEFT" and target_direction == "UP")):
            actions.append("RIGHT")
            current_direction = get_next_direction(current_direction, "RIGHT")
        else:
            actions.append("LEFT")
            current_direction = get_next_direction(current_direction, "LEFT")
    
    return current_direction

def get_next_direction(current, turn):
    """Get the new direction after turning left or right."""
    if turn == "RIGHT":
        if current == "UP": return "RIGHT"
        if current == "RIGHT": return "DOWN"
        if current == "DOWN": return "LEFT"
        if current == "LEFT": return "UP"
    else:  # turn == "LEFT"
        if current == "UP": return "LEFT"
        if current == "LEFT": return "DOWN"
        if current == "DOWN": return "RIGHT"
        if current == "RIGHT": return "UP"

def face_object(agent_position, object_position, current_direction, actions):
    """Make the agent face the object."""
    target_direction = get_direction(agent_position, object_position)
    return turn_to_direction(current_direction, target_direction, actions)

def execute_path(path, agent_position, current_direction, actions):
    """Execute a path by adding the appropriate actions."""
    if len(path) <= 1:
        return agent_position, current_direction
    
    for i in range(1, len(path)):
        current = path[i-1]
        next_pos = path[i]
        
        # Determine which direction to face
        target_direction = get_direction(current, next_pos)
        
        # Turn to face the correct direction
        current_direction = turn_to_direction(current_direction, target_direction, actions)
        
        # Move forward
        actions.append("MOVE")
    
    return path[-1], current_direction

if __name__ == "__main__":
    # Example grid and direction
    grid = [["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"],
["WALL","","","","DOOR","","","WALL"],
["WALL","","","","WALL","","","WALL"],
["WALL","","","","WALL","","","WALL"],
["WALL","","","KEY","WALL","","","WALL"],
["WALL","AGENT","","","WALL","","","WALL"],
["WALL","","","","WALL","","GOAL","WALL"],
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"]]
    direction = "DOWN"
    
    actions = solve(grid, direction)
    print("Actions to solve the game:", actions)