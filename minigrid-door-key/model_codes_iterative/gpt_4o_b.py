from collections import deque

# Constants to represent directions and their mapping to coordinate changes.
DIRECTIONS = ["UP", "RIGHT", "DOWN", "LEFT"]
DELTA = {
    "UP": (-1, 0),
    "RIGHT": (0, 1),
    "DOWN": (1, 0),
    "LEFT": (0, -1)
}

# Function to identify the opposite direction.
def opposite_direction(direction):
    return DIRECTIONS[(DIRECTIONS.index(direction) + 2) % 4]

# Function to detect the turn direction.
def direction_to_turn(start, end):
    start_index = DIRECTIONS.index(start)
    end_index = DIRECTIONS.index(end)
    diff = (end_index - start_index) % 4
    if diff == 1:
        return "RIGHT"
    elif diff == 3:
        return "LEFT"
    return None 

# Function to locate the requested object in the grid.
def find_object(grid, obj):
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == obj:
                return (r, c)
    return None

# Function to discover a path to a target using BFS.
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

# Function to navigate and execute moves and turns.
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

# Main solution function orchestrating actions.
def solve(grid, start_direction):
    key_pos = find_object(grid, "KEY")
    door_pos = find_object(grid, "DOOR")
    goal_pos = find_object(grid, "GOAL")
    start_pos = find_object(grid, "AGENT")
    actions_list = []
    
    # Find and navigate path to KEY
    path_to_key = find_path(grid, start_pos, key_pos)
    actions, current_pos, current_direction = navigate(start_pos, path_to_key, start_direction)
    actions_list.extend(actions)
    
    # Pick up the KEY
    if path_to_key:
        key_direction = path_to_key[-1]  # Last step's direction leads to the key
        if current_direction != key_direction:
            actions_list.append(direction_to_turn(current_direction, key_direction))
        actions_list.append("PICKUP")

    # Find and navigate path to DOOR
    path_to_door = find_path(grid, current_pos, door_pos)
    actions, current_pos, current_direction = navigate(current_pos, path_to_door, current_direction)
    actions_list.extend(actions)
    
    # Unlock the DOOR
    if path_to_door:
        door_direction = path_to_door[-1]  # Last step's direction leads to the door
        if current_direction != door_direction:
            actions_list.append(direction_to_turn(current_direction, door_direction))
        actions_list.append("UNLOCK")

    # Find and navigate path to GOAL
    path_to_goal = find_path(grid, current_pos, goal_pos)
    actions, current_pos, current_direction = navigate(current_pos, path_to_goal, current_direction)
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