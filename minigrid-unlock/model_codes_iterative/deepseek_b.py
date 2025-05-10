from collections import deque

def find_agent(grid):
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == "AGENT":
                return (i, j)
    return None

def find_key(grid):
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == "KEY":
                return (i, j)
    return None

def find_door(grid):
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == "DOOR":
                return (i, j)
    return None

def generate_options(target_pos, grid):
    options = []
    x, y = target_pos
    directions = [
        (-1, 0, 'DOWN'),   # Cell above the target, face DOWN to target
        (1, 0, 'UP'),      # Cell below the target, face UP to target
        (0, -1, 'RIGHT'),  # Cell to the left, face RIGHT to target
        (0, 1, 'LEFT')     # Cell to the right, face LEFT to target
    ]
    for dx, dy, req_dir in directions:
        adj_x = x + dx
        adj_y = y + dy
        if 0 <= adj_x < len(grid) and 0 <= adj_y < len(grid[adj_x]):
            if grid[adj_x][adj_y] == "":
                options.append(((adj_x, adj_y), req_dir))
    return options

def direction_to_delta(direction):
    if direction == "UP":
        return (-1, 0)
    elif direction == "DOWN":
        return (1, 0)
    elif direction == "LEFT":
        return (0, -1)
    elif direction == "RIGHT":
        return (0,1)
    else:
        raise ValueError("Invalid direction")

def turn_left(current_dir):
    if current_dir == "UP":
        return "LEFT"
    elif current_dir == "LEFT":
        return "DOWN"
    elif current_dir == "DOWN":
        return "RIGHT"
    elif current_dir == "RIGHT":
        return "UP"
    else:
        raise ValueError("Invalid direction")

def turn_right(current_dir):
    if current_dir == "UP":
        return "RIGHT"
    elif current_dir == "RIGHT":
        return "DOWN"
    elif current_dir == "DOWN":
        return "LEFT"
    elif current_dir == "LEFT":
        return "UP"
    else:
        raise ValueError("Invalid direction")

def plan_path(start_pos, start_dir, target_pos, target_dir, grid):
    queue = deque()
    visited = set()
    queue.append((start_pos, start_dir, []))
    visited.add((start_pos, start_dir))
    while queue:
        current_pos, current_dir, path = queue.popleft()
        if current_pos == target_pos and current_dir == target_dir:
            return path
        # Action: Turn LEFT
        new_dir = turn_left(current_dir)
        if (current_pos, new_dir) not in visited:
            visited.add((current_pos, new_dir))
            new_path = path + ["LEFT"]
            queue.append((current_pos, new_dir, new_path))
        # Action: Turn RIGHT
        new_dir = turn_right(current_dir)
        if (current_pos, new_dir) not in visited:
            visited.add((current_pos, new_dir))
            new_path = path + ["RIGHT"]
            queue.append((current_pos, new_dir, new_path))
        # Action: MOVE
        dx, dy = direction_to_delta(current_dir)
        new_x = current_pos[0] + dx
        new_y = current_pos[1] + dy
        if 0 <= new_x < len(grid) and 0 <= new_y < len(grid[new_x]):
            if grid[new_x][new_y] == "":
                new_pos = (new_x, new_y)
                if (new_pos, current_dir) not in visited:
                    visited.add((new_pos, current_dir))
                    new_path = path + ["MOVE"]
                    queue.append((new_pos, current_dir, new_path))
    return None

def solve(grid, start_direction):
    agent_pos = find_agent(grid)
    key_pos = find_key(grid)
    door_pos = find_door(grid)
    if agent_pos is None or key_pos is None or door_pos is None:
        return []
    # Plan path to pick up the key
    key_options = generate_options(key_pos, grid)
    best_key_info = None
    min_key_actions = float('inf')
    for target_pos, target_dir in key_options:
        path = plan_path(agent_pos, start_direction, target_pos, target_dir, grid)
        if path is not None and len(path) < min_key_actions:
            best_key_info = (target_pos, target_dir, path)
            min_key_actions = len(path)
    if not best_key_info:
        return []
    best_key_pos, best_key_dir, best_key_path = best_key_info
    # Create a modified grid where the key is removed
    modified_grid = [row.copy() for row in grid]
    modified_grid[key_pos[0]][key_pos[1]] = ""
    # Plan path to unlock the door
    door_options = generate_options(door_pos, modified_grid)
    best_door_info = None
    min_door_actions = float('inf')
    current_pos = best_key_pos
    current_dir = best_key_dir
    for target_pos, target_dir in door_options:
        path = plan_path(current_pos, current_dir, target_pos, target_dir, modified_grid)
        if path is not None and len(path) < min_door_actions:
            best_door_info = (path, target_pos, target_dir)
            min_door_actions = len(path)
    if not best_door_info:
        return []
    best_door_path, _, _ = best_door_info
    # Compile the total actions
    total_actions = []
    total_actions.extend(best_key_path)
    total_actions.append("PICKUP")
    total_actions.extend(best_door_path)
    total_actions.append("UNLOCK")
    return total_actions

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