from collections import deque

# Constants for directions
DIRECTIONS = ["UP", "RIGHT", "DOWN", "LEFT"]
DELTAS = {
    "UP": (-1, 0),
    "DOWN": (1, 0),
    "LEFT": (0, -1),
    "RIGHT": (0, 1)
}

# Define turn actions
TURN_LEFT = {"UP": "LEFT", "LEFT": "DOWN", "DOWN": "RIGHT", "RIGHT": "UP"}
TURN_RIGHT = {"UP": "RIGHT", "RIGHT": "DOWN", "DOWN": "LEFT", "LEFT": "UP"}

def solve(grid, start_direction):
    def find_position(grid, target):
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell == target:
                    return (r, c)
        return None

    def bfs(grid, start, goal):
        queue = deque([(start, [])])
        visited = set()
        visited.add(start)
        while queue:
            (x, y), path = queue.popleft()
            if (x, y) == goal:
                return path
            for direction, (dx, dy) in DELTAS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and (nx, ny) not in visited:
                    if grid[nx][ny] not in ["WALL", "DOOR"]:
                        queue.append(((nx, ny), path + [(direction, (nx, ny))]))
                        visited.add((nx, ny))
        return []

    def turn_towards(current_direction, target_direction):
        actions = []
        while current_direction != target_direction:
            if DIRECTIONS.index(target_direction) == (DIRECTIONS.index(current_direction) + 1) % 4:
                actions.append("RIGHT")
                current_direction = TURN_RIGHT[current_direction]
            else:  # Assuming left turn otherwise
                actions.append("LEFT")
                current_direction = TURN_LEFT[current_direction]
        return actions, current_direction

    def move_to(position_sequence):
        nonlocal current_position, current_direction
        actions = []
        for target_position in position_sequence:
            tx, ty = target_position
            cx, cy = current_position
            if cx > tx:
                target_direction = "UP"
            elif cx < tx:
                target_direction = "DOWN"
            elif cy > ty:
                target_direction = "LEFT"
            else:
                target_direction = "RIGHT"

            turn_action, current_direction = turn_towards(current_direction, target_direction)
            actions.extend(turn_action)
            actions.append("MOVE")
            current_position = (tx, ty)
        return actions

    def pickup_key():
        return ["PICKUP"]

    def unlock_door():
        return ["UNLOCK"]

    key_position = find_position(grid, "KEY")
    door_position = find_position(grid, "DOOR")
    start_position = find_position(grid, "AGENT")
    current_position = start_position
    current_direction = start_direction
    actions = []

    # Move to the KEY
    if key_position:
        path_to_key = [pos for direction, pos in bfs(grid, start_position, key_position)]
        actions.extend(move_to(path_to_key))
        actions.extend(pickup_key())

    # Move to the DOOR with the key
    if door_position:
        path_to_door = [pos for direction, pos in bfs(grid, key_position, door_position)]
        actions.extend(move_to(path_to_door))
        actions.extend(unlock_door())

    return actions

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