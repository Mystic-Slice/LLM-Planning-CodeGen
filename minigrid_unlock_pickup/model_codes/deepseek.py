from collections import deque

def solve(grid, start_direction):
    # Find initial positions of agent, key, and box
    agent_pos = None
    key_pos = None
    box_pos = None
    door_positions = []
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == 'AGENT':
                agent_pos = (i, j)
            elif grid[i][j] == 'KEY':
                key_pos = (i, j)
            elif grid[i][j] == 'BOX':
                box_pos = (i, j)
            elif grid[i][j] == 'DOOR':
                door_positions.append((i, j))
    
    # Function to find the room accessible from a position considering current grid state
    def find_room(pos, blocked_cells):
        room = set()
        queue = deque([pos])
        visited = set()
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            room.add((x, y))
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]):
                    cell = grid[nx][ny]
                    if (nx, ny) not in visited and (nx, ny) not in blocked_cells and cell != 'WALL':
                        if cell == 'DOOR' and (nx, ny) in blocked_cells:
                            continue
                        queue.append((nx, ny))
        return room
    
    # Find connecting door
    agent_room = find_room(agent_pos, set(door_positions))
    box_room = find_room(box_pos, set(door_positions))
    connecting_door = None
    for door in door_positions:
        temp_blocked = set(door_positions) - {door}
        agent_room_test = find_room(agent_pos, temp_blocked)
        if box_pos in agent_room_test:
            connecting_door = door
            break
    
    # Directions: UP, DOWN, LEFT, RIGHT. Order is important for turning.
    dirs = ['UP', 'RIGHT', 'DOWN', 'LEFT']  # Clockwise order
    dir_to_vec = {
        'UP': (-1, 0),
        'DOWN': (1, 0),
        'LEFT': (0, -1),
        'RIGHT': (0, 1)
    }
    
    # State: (x, y), dir, holding (None, 'KEY', 'BOX'), doors_unlocked, key_dropped, box_dropped
    initial_holding = None
    initial_doors = set()
    # Also track the key's and box's current positions (if not held)
    initial_key_pos = key_pos
    initial_box_pos = box_pos
    initial_state = (agent_pos[0], agent_pos[1], start_direction, initial_holding, frozenset(initial_doors), initial_key_pos, initial_box_pos)
    
    queue = deque()
    queue.append((initial_state, []))
    visited = set()
    
    # Helper functions to compute next direction and positions
    def turn_left(d):
        idx = dirs.index(d)
        return dirs[(idx - 1) % 4]
    
    def turn_right(d):
        idx = dirs.index(d)
        return dirs[(idx + 1) % 4]
    
    def move_pos(x, y, d):
        dx, dy = dir_to_vec[d]
        return (x + dx, y + dy)
    
    while queue:
        state, actions = queue.popleft()
        x, y, d, holding, doors, key_p, box_p = state
        if (x, y, d, holding, doors, key_p, box_p) in visited:
            continue
        visited.add((x, y, d, holding, doors, key_p, box_p))
        
        # Check if holding BOX
        if holding == 'BOX':
            return actions
        
        # Generate all possible actions
        for action in ['LEFT', 'RIGHT', 'MOVE', 'PICKUP', 'DROP', 'UNLOCK']:
            new_x, new_y, new_d, new_holding = x, y, d, holding
            new_doors = set(doors)
            new_key_p = key_p
            new_box_p = box_p
            new_act = actions + [action]
            
            valid = True
            if action == 'LEFT':
                new_d = turn_left(d)
            elif action == 'RIGHT':
                new_d = turn_right(d)
            elif action == 'MOVE':
                nx, ny = move_pos(x, y, new_d)
                # Check if the next cell is valid
                if nx < 0 or ny < 0 or nx >= len(grid) or ny >= len(grid[0]):
                    valid = False
                else:
                    cell = grid[nx][ny]
                    if (nx, ny) == key_p:
                        cell = 'KEY'  # Key is here if not picked up
                    elif (nx, ny) == box_p:
                        cell = 'BOX'  # Box is here if not picked up
                    # Can't move into a cell with an object unless it's been picked up
                    if cell == 'WALL':
                        valid = False
                    elif cell == 'DOOR':
                        if (nx, ny) not in new_doors:
                            valid = False  # Door is closed
                    elif cell in ['KEY', 'BOX', 'AGENT'] and (nx, ny) != (x, y):
                        valid = False  # Can't move into a cell with an object unless picked up
                if valid:
                    new_x, new_y = nx, ny
            elif action == 'PICKUP':
                # Check cell in front
                fx, fy = move_pos(x, y, d)
                if (fx, fy) == key_p:
                    if holding is None:
                        new_holding = 'KEY'
                        new_key_p = None  # Key is picked up
                    else:
                        valid = False
                elif (fx, fy) == box_p:
                    if holding is None:
                        new_holding = 'BOX'
                        new_box_p = None
                    else:
                        valid = False
                else:
                    valid = False  # No object to pick up
            elif action == 'DROP':
                if holding is None:
                    valid = False
                else:
                    # Check cell in front
                    fx, fy = move_pos(x, y, d)
                    if 0 <= fx < len(grid) and 0 <= fy < len(grid[0]):
                        cell = grid[fx][fy]
                        if (fx, fy) in [key_p, box_p]:
                            valid = False  # Target cell has an object
                        elif cell == 'WALL' or cell == 'DOOR':
                            valid = False
                        else:
                            if holding == 'KEY':
                                new_key_p = (fx, fy)
                            elif holding == 'BOX':
                                new_box_p = (fx, fy)
                            new_holding = None
                    else:
                        valid = False
            elif action == 'UNLOCK':
                # Check if holding KEY and there's a door in front
                fx, fy = move_pos(x, y, d)
                if holding == 'KEY' and (fx, fy) == connecting_door:
                    new_doors = set(doors) | {(fx, fy)}
                else:
                    valid = False
            
            if valid:
                new_state = (
                    new_x, new_y, 
                    new_d, 
                    new_holding, 
                    frozenset(new_doors), 
                    new_key_p, 
                    new_box_p
                )
                if new_state not in visited:
                    queue.append((new_state, new_act))
    
    return []  # In case of error

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