def solve(grid, start_direction):
    # 1. Initialize Variables
    # Directions
    UP = 'UP'
    DOWN = 'DOWN'
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'
    directions_list = [UP, RIGHT, DOWN, LEFT]

    # Rotations
    LEFT_TURN = 'LEFT'   # 90 degrees to the left
    RIGHT_TURN = 'RIGHT' # 90 degrees to the right

    # Movement Deltas
    direction_to_delta = {
        UP: (-1, 0),
        DOWN: (1, 0),
        LEFT: (0, -1),
        RIGHT: (0, 1)
    }

    # Grid Dimensions
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Agent Variables
    agent_pos = None
    agent_direction = start_direction

    # Object Positions
    key_pos = None
    door_pos = None
    goal_pos = None

    # Obstacles
    walls = set()

    # 2. Locate All Objects in the Grid
    for row in range(rows):
        for col in range(cols):
            cell = grid[row][col]
            if cell == 'AGENT':
                agent_pos = (row, col)
            elif cell == 'KEY':
                key_pos = (row, col)
            elif cell == 'DOOR':
                door_pos = (row, col)
            elif cell == 'GOAL':
                goal_pos = (row, col)
            elif cell == 'WALL':
                walls.add((row, col))
            else:
                pass  # empty cell

    # Helper function to get adjacent positions
    def get_adjacent_positions(pos):
        adj_positions = []
        for delta in direction_to_delta.values():
            adj_row = pos[0] + delta[0]
            adj_col = pos[1] + delta[1]
            if 0 <= adj_row < rows and 0 <= adj_col < cols:
                adj_positions.append((adj_row, adj_col))
        return adj_positions

    # BFS function
    from collections import deque
    def bfs(start_pos, goal_pos, walls, avoid_positions=set(), allow_goal_in_avoid=False):
        queue = deque()
        queue.append((start_pos, []))
        visited = set()
        visited.add(start_pos)
        while queue:
            current_pos, path = queue.popleft()
            if current_pos == goal_pos:
                return path + [current_pos]
            for direction in [UP, DOWN, LEFT, RIGHT]:
                delta = direction_to_delta[direction]
                next_row = current_pos[0] + delta[0]
                next_col = current_pos[1] + delta[1]
                next_pos = (next_row, next_col)
                if (0 <= next_row < rows) and (0 <= next_col < cols):
                    if next_pos not in visited and next_pos not in walls:
                        if next_pos not in avoid_positions or (allow_goal_in_avoid and next_pos == goal_pos):
                            queue.append((next_pos, path + [current_pos]))
                            visited.add(next_pos)
        return None  # No path found

    # get_direction function
    def get_direction(current_pos, next_pos):
        curr_row, curr_col = current_pos
        next_row, next_col = next_pos
        if next_row == curr_row - 1 and next_col == curr_col:
            return UP
        elif next_row == curr_row + 1 and next_col == curr_col:
            return DOWN
        elif next_row == curr_row and next_col == curr_col - 1:
            return LEFT
        elif next_row == curr_row and next_col == curr_col + 1:
            return RIGHT
        else:
            return None  # Not a valid adjacent move

    # get_rotation function
    def get_rotation(current_direction, required_direction):
        current_index = directions_list.index(current_direction)
        required_index = directions_list.index(required_direction)
        delta = (required_index - current_index) % 4
        if delta == 0:
            return []
        elif delta == 1:
            return [RIGHT_TURN]
        elif delta == 2:
            # Can choose left-left or right-right
            return [RIGHT_TURN, RIGHT_TURN]
        elif delta == 3:
            return [LEFT_TURN]

    # update_direction function
    def update_direction(current_direction, rotation):
        index = directions_list.index(current_direction)
        if rotation == LEFT_TURN:
            current_direction = directions_list[(index - 1) % 4]
        elif rotation == RIGHT_TURN:
            current_direction = directions_list[(index + 1) % 4]
        return current_direction

    # face_target function
    def face_target(current_position, current_direction, target_position):
        required_direction = get_direction(current_position, target_position)
        if required_direction is None:
            return []  # Cannot face the target (not adjacent)
        else:
            return get_rotation(current_direction, required_direction)

    # generate_actions function
    def generate_actions(path, start_direction):
        actions = []
        current_direction = start_direction
        for i in range(1, len(path)):
            current_pos = path[i - 1]
            next_pos = path[i]
            required_direction = get_direction(current_pos, next_pos)
            if required_direction is None:
                continue  # Or raise an error
            rotations = get_rotation(current_direction, required_direction)
            actions.extend(rotations)
            current_direction = required_direction
            actions.append('MOVE')
        return actions, current_direction

    # Initialize actions and current position
    actions = []
    current_position = agent_pos
    current_direction = agent_direction

    # 3. Plan Path to the Key

    # Check if the agent can pick up the key immediately
    if key_pos in get_adjacent_positions(current_position):
        # Face the key
        rotations_to_face_key = face_target(current_position, current_direction, key_pos)
        for rotation in rotations_to_face_key:
            actions.append(rotation)
            current_direction = update_direction(current_direction, rotation)
        # Pick up the key
        actions.append('PICKUP')
    else:
        # Find adjacent positions to key
        key_adjacent_positions = get_adjacent_positions(key_pos)
        accessible_key_adjacent_positions = [
            pos for pos in key_adjacent_positions if pos not in walls
        ]

        # If there are no accessible adjacent positions, allow moving onto the key position
        if not accessible_key_adjacent_positions:
            # Plan path directly to the key position
            path_to_key = bfs(current_position, key_pos, walls, allow_goal_in_avoid=True)
            if path_to_key is None:
                return []  # No path to key
            # Generate actions to reach the key
            actions_to_key, current_direction = generate_actions(path_to_key, current_direction)
            actions.extend(actions_to_key)
            current_position = key_pos
            # Pick up the key (no need to face—it’s on the same cell)
            actions.append('PICKUP')
        else:
            # Find the shortest path to an accessible adjacent position
            shortest_key_path = None
            key_pickup_pos = None
            shortest_length = None
            for position in accessible_key_adjacent_positions:
                path = bfs(current_position, position, walls, avoid_positions={key_pos})
                if path is not None:
                    path_length = len(path)
                    if shortest_key_path is None or path_length < shortest_length:
                        shortest_key_path = path
                        key_pickup_pos = position
                        shortest_length = path_length
            if shortest_key_path is None:
                return []  # No path to key
            # Generate actions to reach the key
            actions_to_key, current_direction = generate_actions(shortest_key_path, current_direction)
            actions.extend(actions_to_key)
            current_position = key_pickup_pos
            # Face the key
            rotations_to_face_key = face_target(current_position, current_direction, key_pos)
            for rotation in rotations_to_face_key:
                actions.append(rotation)
                current_direction = update_direction(current_direction, rotation)
            # Pick up the key
            actions.append('PICKUP')

    # Update agent's position if it moved onto the key
    if current_position != key_pos and key_pos == current_position:
        current_position = key_pos

    # 4. Plan Path to the Door

    # Check if the agent can unlock the door immediately
    if door_pos in get_adjacent_positions(current_position):
        # Face the door
        rotations_to_face_door = face_target(current_position, current_direction, door_pos)
        for rotation in rotations_to_face_door:
            actions.append(rotation)
            current_direction = update_direction(current_direction, rotation)
        # Unlock the door
        actions.append('UNLOCK')
    else:
        # Find adjacent positions to door
        door_adjacent_positions = get_adjacent_positions(door_pos)
        accessible_door_adjacent_positions = [
            pos for pos in door_adjacent_positions if pos not in walls
        ]

        # If there are no accessible adjacent positions, allow moving onto the door position
        if not accessible_door_adjacent_positions:
            # Plan path directly to the door position
            path_to_door = bfs(current_position, door_pos, walls, allow_goal_in_avoid=True)
            if path_to_door is None:
                return []  # No path to door
            # Generate actions to reach the door
            actions_to_door, current_direction = generate_actions(path_to_door, current_direction)
            actions.extend(actions_to_door)
            current_position = door_pos
            # Unlock the door (no need to face—it’s on the same cell)
            actions.append('UNLOCK')
        else:
            # Find the shortest path to an accessible adjacent position
            shortest_door_path = None
            door_unlock_pos = None
            shortest_length = None
            for position in accessible_door_adjacent_positions:
                path = bfs(current_position, position, walls, avoid_positions={door_pos})
                if path is not None:
                    path_length = len(path)
                    if shortest_door_path is None or path_length < shortest_length:
                        shortest_door_path = path
                        door_unlock_pos = position
                        shortest_length = path_length
            if shortest_door_path is None:
                return []  # No path to door
            # Generate actions to reach the door
            actions_to_door, current_direction = generate_actions(shortest_door_path, current_direction)
            actions.extend(actions_to_door)
            current_position = door_unlock_pos
            # Face the door
            rotations_to_face_door = face_target(current_position, current_direction, door_pos)
            for rotation in rotations_to_face_door:
                actions.append(rotation)
                current_direction = update_direction(current_direction, rotation)
            # Unlock the door
            actions.append('UNLOCK')

    # Update walls to remove the door
    walls.discard(door_pos)

    # 5. Plan Path to the Goal

    path_to_goal = bfs(current_position, goal_pos, walls)
    if path_to_goal is None:
        return []  # No path to goal
    # Generate actions to reach the goal
    actions_to_goal, current_direction = generate_actions(path_to_goal, current_direction)
    actions.extend(actions_to_goal)
    # No need to face the goal; the game completes when standing on it

    return actions

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