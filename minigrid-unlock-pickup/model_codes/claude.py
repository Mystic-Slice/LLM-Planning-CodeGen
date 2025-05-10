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
    
    # Phase 1: Initial exploration to find KEY and DOOR
    explore_results = explore_current_room(grid, current_pos, current_direction)
    actions.extend(explore_results["actions"])
    current_pos = explore_results["final_pos"]
    current_direction = explore_results["final_direction"]
    update_known_objects(known_objects, explore_results["discovered_objects"])
    
    # Phase 2: Get KEY
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
    
    # Phase 3: Go to DOOR and unlock it
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
    
    # Phase 4: Explore second room to find BOX
    explore_results = explore_current_room(grid, current_pos, current_direction)
    actions.extend(explore_results["actions"])
    current_pos = explore_results["final_pos"]
    current_direction = explore_results["final_direction"]
    update_known_objects(known_objects, explore_results["discovered_objects"])
    
    # Phase 5: Navigate to BOX
    if "BOX" in known_objects:
        box_pos = known_objects["BOX"]
        nav_results = navigate_to(grid, current_pos, current_direction, box_pos)
        actions.extend(nav_results["actions"])
        current_pos = nav_results["final_pos"]
        current_direction = nav_results["final_direction"]
        
        # If holding KEY, find empty adjacent cell and drop it
        if currently_holding == "KEY":
            empty_cell_dir = find_empty_adjacent_cell(grid, current_pos)
            if empty_cell_dir:
                # Orient to face empty cell
                orient_results = orient_to_direction(current_direction, empty_cell_dir)
                actions.extend(orient_results["actions"])
                current_direction = empty_cell_dir
                
                # Drop KEY
                actions.append("DROP")
                currently_holding = None
        
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


def explore_current_room(grid, start_pos, start_direction):
    """
    Explore the current room using wall-following algorithm.
    
    Returns:
        Dict containing discovered objects, final position, final direction, 
        and actions taken
    """
    actions = []
    discovered_objects = {}
    current_pos = start_pos
    current_direction = start_direction
    visited = set([current_pos])
    
    # Simple BFS to explore the room
    queue = [(current_pos, current_direction, [])]
    while queue:
        pos, direction, path = queue.pop(0)
        
        # Check surrounding cells for objects
        for d in ["UP", "RIGHT", "DOWN", "LEFT"]:
            orient_results = orient_to_direction(direction, d)
            new_direction = orient_results["final_direction"]
            new_pos = get_position_after_move(pos, new_direction)
            
            # Check if position is valid and within room (not a wall)
            if is_valid_position(grid, new_pos):
                cell_content = grid[new_pos[0]][new_pos[1]]
                if cell_content in ["KEY", "DOOR", "BOX"] and cell_content not in discovered_objects:
                    discovered_objects[cell_content] = new_pos
        
        # Try moving in all four directions
        for d in ["UP", "RIGHT", "DOWN", "LEFT"]:
            orient_results = orient_to_direction(direction, d)
            new_direction = orient_results["final_direction"]
            new_pos = get_position_after_move(pos, new_direction)
            
            # Check if position is valid, not visited, and not a wall or door
            if (is_valid_position(grid, new_pos) and 
                new_pos not in visited and 
                grid[new_pos[0]][new_pos[1]] not in ["WALL", "DOOR"]):
                
                new_path = path.copy()
                new_path.extend(orient_results["actions"])
                new_path.append("MOVE")
                
                visited.add(new_pos)
                queue.append((new_pos, new_direction, new_path))
    
        # If we found all objects (KEY, DOOR, BOX), we can stop
        if len(discovered_objects) == 3 or (len(discovered_objects) == 2 and "BOX" in discovered_objects):
            break
    
    # Return the shortest valid path if any
    if queue:
        actions = queue[0][2]
        final_pos = queue[0][0]
        final_direction = queue[0][1]
    else:
        # If no path was found, return original position and direction
        actions = []
        final_pos = start_pos
        final_direction = start_direction
    
    return {
        "discovered_objects": discovered_objects,
        "final_pos": final_pos,
        "final_direction": final_direction,
        "actions": actions
    }


def navigate_to(grid, current_pos, current_direction, target_pos):
    """
    Find the shortest path from current_pos to adjacent cell of target_pos.
    
    Returns:
        Dict containing actions, final position and direction
    """
    # Implementation of A* pathfinding
    from heapq import heappush, heappop
    
    def heuristic(pos1, pos2):
        # Manhattan distance
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    # Find positions adjacent to target
    adjacent_positions = []
    for d in ["UP", "RIGHT", "DOWN", "LEFT"]:
        adj_pos = get_adjacent_position(target_pos, d)
        if is_valid_position(grid, adj_pos) and grid[adj_pos[0]][adj_pos[1]] not in ["WALL", "DOOR", "BOX", "KEY"]:
            adjacent_positions.append(adj_pos)
    
    if not adjacent_positions:
        return {
            "actions": [],
            "final_pos": current_pos,
            "final_direction": current_direction
        }
    
    # Start A* search
    open_set = []
    heappush(open_set, (0, current_pos, current_direction, []))
    closed_set = set()
    
    while open_set:
        _, pos, direction, path = heappop(open_set)
        
        if pos in closed_set:
            continue
            
        closed_set.add(pos)
        
        # If we've reached an adjacent position to target, return the path
        if pos in adjacent_positions:
            return {
                "actions": path,
                "final_pos": pos,
                "final_direction": direction
            }
        
        # Try all four directions
        for d in ["UP", "RIGHT", "DOWN", "LEFT"]:
            orient_results = orient_to_direction(direction, d)
            new_direction = orient_results["final_direction"]
            new_pos = get_position_after_move(pos, new_direction)
            
            if (is_valid_position(grid, new_pos) and 
                new_pos not in closed_set and 
                grid[new_pos[0]][new_pos[1]] not in ["WALL", "DOOR", "BOX", "KEY"]):
                
                new_path = path.copy()
                new_path.extend(orient_results["actions"])
                new_path.append("MOVE")
                
                priority = len(new_path) + heuristic(new_pos, target_pos)
                heappush(open_set, (priority, new_pos, new_direction, new_path))
    
    # If no path is found, return empty
    return {
        "actions": [],
        "final_pos": current_pos,
        "final_direction": current_direction
    }


def orient_to_face(current_pos, current_direction, target_pos):
    """
    Determine the actions needed to face the target position.
    
    Returns:
        Dict containing actions and final direction
    """
    # Calculate the direction to face
    row_diff = target_pos[0] - current_pos[0]
    col_diff = target_pos[1] - current_pos[1]
    
    target_direction = None
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
        # Turn right twice or left twice
        actions.extend(["RIGHT", "RIGHT"])
    elif diff == 3:
        # Turn left once
        actions.append("LEFT")
    
    return {
        "actions": actions,
        "final_direction": target_direction
    }


def find_empty_adjacent_cell(grid, pos):
    """
    Find an empty cell adjacent to the current position.
    
    Returns:
        Direction to the empty cell or None if not found
    """
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    
    for direction in directions:
        adjacent_pos = get_adjacent_position(pos, direction)
        if is_valid_position(grid, adjacent_pos) and grid[adjacent_pos[0]][adjacent_pos[1]] == "":
            return direction
    
    return None


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


def update_known_objects(known_objects, discovered_objects):
    """Update the known_objects dictionary with new discoveries."""
    for obj_type, pos in discovered_objects.items():
        known_objects[obj_type] = pos

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