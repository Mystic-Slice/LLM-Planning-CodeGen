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
    
    # Create a copy of the grid for tracking state changes
    current_grid = [row[:] for row in grid]
    current_grid[agent_pos[0]][agent_pos[1]] = ""  # Remove agent from tracking grid
    
    # Find all objects in grid
    find_all_objects(grid, known_objects)

    # Phase 1: Get KEY
    if "KEY" in known_objects:
        key_pos = known_objects["KEY"]
        
        # Navigate to a position adjacent to the KEY
        nav_results = navigate_to_adjacent(current_grid, current_pos, current_direction, key_pos, door_unlocked=False)
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
        current_grid[key_pos[0]][key_pos[1]] = ""  # Remove key from tracking grid

    # Phase 2: Go to DOOR and unlock it
    if "DOOR" in known_objects:
        door_pos = known_objects["DOOR"]
        
        # Navigate to a position adjacent to the DOOR
        nav_results = navigate_to_adjacent(current_grid, current_pos, current_direction, door_pos, door_unlocked=False)
        actions.extend(nav_results["actions"])
        current_pos = nav_results["final_pos"]
        current_direction = nav_results["final_direction"]
        
        # Orient to face the DOOR
        orient_results = orient_to_face(current_pos, current_direction, door_pos)
        actions.extend(orient_results["actions"])
        current_direction = orient_results["final_direction"]
        
        # Unlock DOOR
        actions.append("UNLOCK")
        current_grid[door_pos[0]][door_pos[1]] = ""  # Mark door as unlocked
        
        # Move through the door
        actions.append("MOVE")
        current_pos = get_position_after_move(current_pos, current_direction)

    # Phase 3: Navigate to BOX
    if "BOX" in known_objects:
        box_pos = known_objects["BOX"]
        
        # Navigate to a position adjacent to the BOX
        nav_results = navigate_to_adjacent(current_grid, current_pos, current_direction, box_pos, door_unlocked=True)
        actions.extend(nav_results["actions"])
        current_pos = nav_results["final_pos"]
        current_direction = nav_results["final_direction"]
        
        # If holding KEY, find empty adjacent cell and drop it
        if currently_holding == "KEY":
            # Find an empty cell nearby
            empty_pos = find_empty_cell_near(current_grid, current_pos)
            if empty_pos:
                # Orient to face the empty cell
                orient_results = orient_to_face(current_pos, current_direction, empty_pos)
                actions.extend(orient_results["actions"])
                current_direction = orient_results["final_direction"]
                
                # Drop KEY
                actions.append("DROP")
                currently_holding = None
                
                # Orient back to BOX
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

def navigate_to_adjacent(grid, current_pos, current_direction, target_pos, door_unlocked=False):
    """
    Find a path to a position adjacent to target_pos.
    Returns:
        Dict containing actions, final position and direction
    """
    # If we're already adjacent to the target
    if is_adjacent(current_pos, target_pos):
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
        
        # Check if we're adjacent to target
        if is_adjacent(pos, target_pos):
            return {
                "actions": actions_so_far,
                "final_pos": pos,
                "final_direction": direction
            }
        
        # Try all possible movements from current position
        for turn_action, new_dir in [
            ([], direction),
            (["RIGHT"], turn_right(direction)),
            (["LEFT"], turn_left(direction)),
            (["RIGHT", "RIGHT"], turn_right(turn_right(direction))),
        ]:
            # Apply turn
            new_actions = actions_so_far.copy()
            new_actions.extend(turn_action)
            
            # Check if we can move forward
            new_pos = get_position_after_move(pos, new_dir)
            
            # Check if the move is valid
            is_valid_move = (
                is_valid_position(grid, new_pos) and
                (grid[new_pos[0]][new_pos[1]] == "" or 
                 (door_unlocked and grid[new_pos[0]][new_pos[1]] == "DOOR"))
            )
            
            # If valid, add move action
            if is_valid_move:
                move_actions = new_actions.copy()
                move_actions.append("MOVE")
                if (new_pos, new_dir) not in visited:
                    visited.add((new_pos, new_dir))
                    queue.append((new_pos, new_dir, move_actions))
    
    # If no path is found, return empty
    return {
        "actions": [],
        "final_pos": current_pos,
        "final_direction": current_direction
    }

def find_empty_cell_near(grid, current_pos):
    """Find an empty cell adjacent to the current position."""
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    
    # First check immediate adjacent cells
    for direction in directions:
        new_pos = get_adjacent_position(current_pos, direction)
        if (is_valid_position(grid, new_pos) and grid[new_pos[0]][new_pos[1]] == ""):
            return new_pos
    
    # If no immediately adjacent cell, do BFS to find closest empty cell
    from collections import deque
    queue = deque([current_pos])
    visited = {current_pos}
    
    while queue:
        pos = queue.popleft()
        
        # Check all adjacent positions
        for direction in directions:
            new_pos = get_adjacent_position(pos, direction)
            
            if new_pos in visited:
                continue
                
            if (is_valid_position(grid, new_pos)):
                if grid[new_pos[0]][new_pos[1]] == "":
                    return new_pos
                
                if grid[new_pos[0]][new_pos[1]] not in ["WALL", "DOOR", "BOX", "KEY"]:
                    visited.add(new_pos)
                    queue.append(new_pos)
    
    return None

def is_adjacent(pos1, pos2):
    """Check if two positions are adjacent."""
    return (abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])) == 1

def orient_to_face(current_pos, current_direction, target_pos):
    """
    Determine the actions needed to face the target position.
    Returns:
        Dict containing actions and final direction
    """
    row_diff = target_pos[0] - current_pos[0]
    col_diff = target_pos[1] - current_pos[1]
    
    # Determine the direction to face
    if row_diff < 0 and col_diff == 0:
        target_direction = "UP"
    elif row_diff > 0 and col_diff == 0:
        target_direction = "DOWN"
    elif row_diff == 0 and col_diff < 0:
        target_direction = "LEFT"
    elif row_diff == 0 and col_diff > 0:
        target_direction = "RIGHT"
    else:
        # Default to current direction if not clearly horizontally or vertically aligned
        return {
            "actions": [],
            "final_direction": current_direction
        }
    
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
        # Turn right twice
        actions.extend(["RIGHT", "RIGHT"])
    elif diff == 3:
        # Turn left once
        actions.append("LEFT")
    
    return {
        "actions": actions,
        "final_direction": target_direction
    }

def turn_right(direction):
    """Return the direction after turning right."""
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    idx = directions.index(direction)
    return directions[(idx + 1) % 4]

def turn_left(direction):
    """Return the direction after turning left."""
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    idx = directions.index(direction)
    return directions[(idx - 1) % 4]

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
    """Check if a position is within the grid boundaries."""
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