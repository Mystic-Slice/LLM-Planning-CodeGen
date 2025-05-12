from collections import deque

# Constants to represent directions
DIRECTIONS = ["UP", "RIGHT", "DOWN", "LEFT"]

# Mapping of directions to coordinate changes
DELTA = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1)
}

def opposite_direction(direction):
    return DIRECTIONS[(DIRECTIONS.index(direction) + 2) % 4]

def direction_to_turn(start, end):
    start_index = DIRECTIONS.index(start)
    end_index = DIRECTIONS.index(end)
    diff = (end_index - start_index) % 4
    if diff == 1:
        return "RIGHT"
    elif diff == 3:
        return "LEFT"
    return None  # Should not occur if start != end

def find_object(grid, obj):
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == obj:
                return (r, c)
    return None

def find_path(grid, start, end):
    rows, cols = len(grid), len(grid[0])
    queue = deque([(start, [])])
    visited = set()
    visited.add(start)
    
    while queue:
        current, path = queue.popleft()
        if current == end:
            return path
        
        r, c = current
        for direction in DIRECTIONS:
            dr, dc = DELTA[direction]
            new_pos = (r + dr, c + dc)
            if (0 <= new_pos[0] < rows and 0 <= new_pos[1] < cols
                and grid[new_pos[0]][new_pos[1]] not in ["WALL", "DOOR"]
                and new_pos not in visited):
                visited.add(new_pos)
                queue.append((new_pos, path + [direction]))
    return []

def navigate(current_pos, path, current_direction):
    actions = []
    r, c = current_pos
    for step in path:
        target_r, target_c = r + DELTA[step][0], c + DELTA[step][1]
        
        if current_direction != step:
            turn = direction_to_turn(current_direction, step)
            if turn:
                actions.append(turn)
            current_direction = step
        
        actions.append("MOVE")
        r, c = target_r, target_c
    
    return actions, (r, c), current_direction

def solve(grid, start_direction):
    key_pos = find_object(grid, "KEY")
    door_pos = find_object(grid, "DOOR")
    goal_pos = find_object(grid, "GOAL")
    start_pos = find_object(grid, "AGENT")
    
    actions_list = []

    # Find path to KEY
    path_to_key = find_path(grid, start_pos, key_pos)
    actions, current_pos, current_direction = navigate(start_pos, path_to_key, start_direction)
    actions_list.extend(actions)

    # Pick up the KEY
    if current_direction != "UP":
        actions_list.append(direction_to_turn(current_direction, "UP"))
    actions_list.append("PICKUP")

    # Move to DOOR
    path_to_door = find_path(grid, current_pos, door_pos)
    actions, current_pos, current_direction = navigate(current_pos, path_to_door, "UP")
    actions_list.extend(actions)

    # Unlock the DOOR
    door_direction = opposite_direction("UP")  # Assuming door opens opposite to current agent direction
    if current_direction != door_direction:
        actions_list.append(direction_to_turn(current_direction, door_direction))
    actions_list.append("UNLOCK")

    # Move to GOAL
    path_to_goal = find_path(grid, current_pos, goal_pos)
    actions, current_pos, current_direction = navigate(current_pos, path_to_goal, door_direction)
    actions_list.extend(actions)

    return actions_list

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