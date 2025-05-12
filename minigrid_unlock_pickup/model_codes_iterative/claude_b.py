def solve(grid, start_direction):
    """
    Solve the grid-based game by returning a sequence of actions to pickup the BOX.
    Args:
        grid: 2D list representing the environment
        start_direction: String representing initial direction ("UP", "DOWN", "LEFT", or "RIGHT")
    Returns:
        List of action strings to solve the task
    """
    # Initialize variables
    actions = []
    known_objects = {}
    currently_holding = None
    
    # Find agent's starting position
    agent_pos = find_agent_position(grid)
    current_pos = agent_pos
    current_direction = start_direction
    
    # Find all objects in grid
    find_all_objects(grid, known_objects)
    
    # Phase 1: Get KEY
    if "KEY" in known_objects:
        key_pos = known_objects["KEY"]
        nav_results = navigate_to(grid, current_pos, current_direction, key_pos)
        actions.extend(nav_results["actions"])
        current_pos = nav_results["final_pos"]
        current_direction = nav_results["final_direction"]
        
        # Orient to face the KEY
        orient_results = orient_to_face(current_pos, current_direction, key_pos)
        actions.extend(orient_results["actions"])
        current_direction = orient_results["final_direction"]
        
        # Pick up KEY
        actions.append("PICKUP")
        currently_holding = "KEY"
    
    # Phase 2: Go to DOOR and unlock it
    if "DOOR" in known_objects:
        door_pos = known_objects["DOOR"]
        nav_results = navigate_to(grid, current_pos, current_direction, door_pos)
        actions.extend(nav_results["actions"])
        current_pos = nav_results["final_pos"]
        current_direction = nav_results["final_direction"]
        
        # Orient to face the DOOR
        orient_results = orient_to_face(current_pos, current_direction, door_pos)
        actions.extend(orient_results["actions"])
        current_direction = orient_results["final_direction"]
        
        # Unlock DOOR
        actions.append("UNLOCK")
        
        # Move through the door
        actions.append("MOVE")
        current_pos = get_position_after_move(current_pos, current_direction)
    
    # Phase 3: Navigate to BOX
    if "BOX" in known_objects:
        box_pos = known_objects["BOX"]
        
        # Navigate to a position adjacent to the BOX
        nav_results = navigate_to(grid, current_pos, current_direction, box_pos)
        actions.extend(nav_results["actions"])
        current_pos = nav_results["final_pos"]
        current_direction = nav_results["final_direction"]
        
        # If holding KEY, find empty adjacent cell and drop it
        if currently_holding == "KEY":
            # Find an empty cell nearby
            empty_pos = find_empty_cell_near(grid, current_pos)
            if empty_pos:
                # Navigate to the empty position
                nav_to_empty = navigate_to(grid, current_pos, current_direction, empty_pos)
                actions.extend(nav_to_empty["actions"])
                current_pos = nav_to_empty["final_pos"]
                current_direction = nav_to_empty["final_direction"]
                
                # Drop KEY
                actions.append("DROP")
                currently_holding = None
                
                # Navigate back to box
                nav_to_box = navigate_to(grid, current_pos, current_direction, box_pos)
                actions.extend(nav_to_box["actions"])
                current_pos = nav_to_box["final_pos"]
                current_direction = nav_to_box["final_direction"]
        
        # Orient to face the BOX
        orient_results = orient_to_face(current_pos, current_direction, box_pos)
        actions.extend(orient_results["actions"])
        current_direction = orient_results["final_direction"]
        
        # Pick up BOX
        actions.append("PICKUP")
    
    return actions

def find_agent_position(grid):
    """Find the agent's position in the grid."""
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == "AGENT":
                return (i, j)
    return None

def find_all_objects(grid, known_objects):
    """Find all important objects in the grid and add them to known_objects."""
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] in ["KEY", "DOOR", "BOX"]:
                known_objects[grid[i][j]] = (i, j)

def navigate_to(grid, current_pos, current_direction, target_pos):
    """
    Find a path to a position adjacent to target_pos.
    Returns:
        Dict containing actions, final position and direction
    """
    # If we're already at the target position
    if current_pos == target_pos:
        return {
            "actions": [],
            "final_pos": current_pos,
            "final_direction": current_direction
        }
    
    # If target_pos is not a position we want to move onto (like KEY, BOX), 
    # find positions adjacent to target
    adjacent_positions = []
    obj_at_target = grid[target_pos[0]][target_pos[1]] if is_valid_position(grid, target_pos) else None
    
    if obj_at_target in ["KEY", "BOX", "DOOR"]:
        for d in ["UP", "RIGHT", "DOWN", "LEFT"]:
            adj_pos = get_adjacent_position(target_pos, d)
            if (is_valid_position(grid, adj_pos) and 
                grid[adj_pos[0]][adj_pos[1]] not in ["WALL", "DOOR", "BOX", "KEY"] and
                adj_pos != current_pos):
                adjacent_positions.append(adj_pos)
        if not adjacent_positions and current_pos != target_pos:
            # If no valid adjacent position found for objects, try the closest navigable position
            adjacent_positions = [current_pos]  # Default to current position
    else:
        # Target is a position to move to (like an empty cell for dropping)
        adjacent_positions = [target_pos]
    
    # If no adjacent positions, return current position
    if not adjacent_positions:
        return {
            "actions": [],
            "final_pos": current_pos,
            "final_direction": current_direction
        }
    
    # Use BFS to find the shortest path
    from collections import deque
    
    queue = deque([(current_pos, current_direction, [])])  # (pos, direction, actions)
    visited = {(current_pos, current_direction)}
    
    while queue:
        pos, direction, actions_so_far = queue.popleft()
        
        # If we've reached any of the adjacent positions to target, return the path
        if pos in adjacent_positions:
            return {
                "actions": actions_so_far,
                "final_pos": pos,
                "final_direction": direction
            }
        
        # Try all four directions
        for new_dir in ["UP", "RIGHT", "DOWN", "LEFT"]:
            orient_results = orient_to_direction(direction, new_dir)
            new_direction = orient_results["final_direction"]
            new_pos = get_position_after_move(pos, new_direction)
            
            # Generate action sequence for this move
            new_actions = actions_so_far.copy()
            new_actions.extend(orient_results["actions"])
            
            if (is_valid_position(grid, new_pos) and 
                grid[new_pos[0]][new_pos[1]] not in ["WALL", "DOOR", "BOX", "KEY"]):
                new_actions.append("MOVE")
                if (new_pos, new_direction) not in visited:
                    visited.add((new_pos, new_direction))
                    queue.append((new_pos, new_direction, new_actions))
    
    # If no path is found, return empty
    return {
        "actions": [],
        "final_pos": current_pos,
        "final_direction": current_direction
    }

def find_empty_cell_near(grid, current_pos):
    """Find the nearest empty cell in the grid."""
    from collections import deque
    
    queue = deque([current_pos])
    visited = {current_pos}
    
    while queue:
        pos = queue.popleft()
        
        # Check all adjacent positions
        for direction in ["UP", "RIGHT", "DOWN", "LEFT"]:
            new_pos = get_adjacent_position(pos, direction)
            
            if (is_valid_position(grid, new_pos) and 
                grid[new_pos[0]][new_pos[1]] == "" and 
                new_pos not in visited):
                return new_pos
            
            if (is_valid_position(grid, new_pos) and 
                grid[new_pos[0]][new_pos[1]] not in ["WALL", "DOOR", "BOX", "KEY"] and 
                new_pos not in visited):
                visited.add(new_pos)
                queue.append(new_pos)
    
    return None

def orient_to_face(current_pos, current_direction, target_pos):
    """
    Determine the actions needed to face the target position.
    Returns:
        Dict containing actions and final direction
    """
    # Calculate the direction to face
    row_diff = target_pos[0] - current_pos[0]
    col_diff = target_pos[1] - current_pos[1]
    
    if abs(row_diff) == 0 and abs(col_diff) == 0:
        # Already at the target position
        return {
            "actions": [],
            "final_direction": current_direction
        }
    
    # Determine principal direction based on which difference is larger
    if abs(row_diff) > abs(col_diff):
        # Vertical orientation
        if row_diff < 0:
            target_direction = "UP"
        else:
            target_direction = "DOWN"
    else:
        # Horizontal orientation
        if col_diff < 0:
            target_direction = "LEFT"
        else:
            target_direction = "RIGHT"
    
    return orient_to_direction(current_direction, target_direction)

def orient_to_direction(current_direction, target_direction):
    """
    Determine the actions needed to change from current to target direction.
    Returns:
        Dict containing actions and final direction
    """
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    current_idx = directions.index(current_direction)
    target_idx = directions.index(target_direction)
    
    # Calculate the number of turns needed
    diff = (target_idx - current_idx) % 4
    
    actions = []
    if diff == 0:
        # Already facing the target direction
        pass
    elif diff == 1:
        # Turn right once
        actions.append("RIGHT")
    elif diff == 2:
        # Turn right twice or left twice (right twice is more consistent)
        actions.extend(["RIGHT", "RIGHT"])
    elif diff == 3:
        # Turn left once
        actions.append("LEFT")
    
    return {
        "actions": actions,
        "final_direction": target_direction
    }

def get_position_after_move(pos, direction):
    """Calculate the new position after moving in the given direction."""
    if direction == "UP":
        return (pos[0] - 1, pos[1])
    elif direction == "DOWN":
        return (pos[0] + 1, pos[1])
    elif direction == "LEFT":
        return (pos[0], pos[1] - 1)
    elif direction == "RIGHT":
        return (pos[0], pos[1] + 1)
    return pos

def get_adjacent_position(pos, direction):
    """Get the adjacent position in the given direction without moving."""
    return get_position_after_move(pos, direction)

def is_valid_position(grid, pos):
    """Check if a position is within the grid boundaries and not a wall."""
    return (0 <= pos[0] < len(grid) and
            0 <= pos[1] < len(grid[0]) and
            grid[pos[0]][pos[1]] != "WALL")

if __name__ == "__main__":
    # Example grid and direction
    grid = [
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"],
["WALL","","","","","DOOR","","","","","WALL"],
["WALL","","","","","WALL","","","","","WALL"],
["WALL","","AGENT","","KEY","WALL","","","","","WALL"],
["WALL","","","","","WALL","","","","BOX","WALL"],
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"]
]
    direction = "DOWN"
    
    actions = solve(grid, direction)
    print("Actions to solve the game:", actions)