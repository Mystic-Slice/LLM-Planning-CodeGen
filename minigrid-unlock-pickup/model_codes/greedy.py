
def find_object(grid, object):
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == object:
                return (r, c)
    return None

def move_to_object(grid, start_pos, target_pos):

    q = [(start_pos, [start_pos])]  # queue of (position, path)
    visited = set()
    visited.add(start_pos)

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up

    while q:
        current_pos, path = q.pop(0)

        if current_pos == target_pos:
            return path

        for d in directions:
            new_pos = (current_pos[0] + d[0], current_pos[1] + d[1])

            if (0 <= new_pos[0] < len(grid) and
                0 <= new_pos[1] < len(grid[0]) and
                grid[new_pos[0]][new_pos[1]] != "WALL" and
                new_pos not in visited):

                visited.add(new_pos)
                q.append((new_pos, path + [new_pos]))

    return []

def add_direction_changes(path, start_direction):
    current_direction = start_direction

    direction_map = {
        "LEFT": [0, -1],
        "UP": [-1, 0],
        "RIGHT": [0, 1],
        "DOWN": [1, 0]
    }

    action_list = []

    for i in range(1, len(path)):
        required_direction = None
        for dir, delta in direction_map.items():
            if (path[i-1][0] + delta[0] == path[i][0] and
                path[i-1][1] + delta[1] == path[i][1]):
                required_direction = dir
                break

        if required_direction != current_direction:
            directions = list(direction_map.keys())
            current_direction_index = directions.index(current_direction)
            required_direction_index = directions.index(required_direction)

            turns = (required_direction_index - current_direction_index) % 4

            if turns == 1:
                action_list.append("RIGHT")
            elif turns == 2:
                action_list.append("RIGHT")
                action_list.append("RIGHT")
            elif turns == 3:
                action_list.append("LEFT")
            current_direction = required_direction

        action_list.append("MOVE")

    return action_list, current_direction, path[-2]

def solve(grid, start_direction):
    direction = start_direction
    curr_pos = find_object(grid, "AGENT")
    if not curr_pos:
        return []

    # get location of key
    key_pos = find_object(grid, "KEY")

    if not key_pos:
        return []

    # move to key
    path_to_key = move_to_object(grid, curr_pos, key_pos)
    if not path_to_key:
        return []
    
    # add direction changes to path
    action_list, direction, curr_pos = add_direction_changes(path_to_key, direction)
    action_list = action_list[:-1]  # remove last move to key

    # pick up key
    action_list.append("PICKUP")  # pick up key

    # move to door
    door_pos = find_object(grid, "DOOR")
    if not door_pos:
        return []
    
    path_to_door = move_to_object(grid, curr_pos, door_pos)
    if not path_to_door:
        return []
    
    # add direction changes to path
    action_list_door, direction, curr_pos = add_direction_changes(path_to_door, direction)
    action_list_door = action_list_door[:-1]  # remove last move to door

    action_list.extend(action_list_door)

    # unlock door
    action_list.append("UNLOCK")  # unlock door

    box_pos = find_object(grid, "BOX")
    if not box_pos:
        return []
    
    # move to goal
    path_to_box = move_to_object(grid, curr_pos, box_pos)
    if not path_to_box:
        return []
    
    action_list_goal, direction, curr_pos = add_direction_changes(path_to_box, direction)
    action_list_goal = action_list_goal[:-1]

    action_list.extend(action_list_goal)

    if action_list[-1] == "MOVE":
        action_list.extend(['RIGHT', 'RIGHT', 'DROP', 'RIGHT', 'RIGHT', 'PICKUP'])
    else:
        if action_list[-1] == "RIGHT":
            action_list.extend(['RIGHT', 'DROP', 'LEFT', 'PICKUP'])
        elif action_list[-1] == "LEFT":
            action_list.extend(['LEFT', 'DROP', 'RIGHT', 'PICKUP'])

    return action_list


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