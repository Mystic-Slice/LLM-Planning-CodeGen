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
                        queue.append(((nx, ny), path + [(direction, nx, ny)]))
                        visited.add((nx, ny))
        return []

    def adjust_direction(current_direction, target_position):
        actions = []
        cx, cy = current_position
        tx, ty = target_position
        if cx > tx:
            target_direction = "UP"
        elif cx < tx:
            target_direction = "DOWN"
        elif cy > ty:
            target_direction = "LEFT"
        else:
            target_direction = "RIGHT"
        
        while current_direction != target_direction:
            actions.append("LEFT")
            current_direction = TURN_LEFT[current_direction]

        return actions

    def execute_path(path):
        actions = []
        for direction, nx, ny in path:
            actions.extend(adjust_direction(current_direction, (nx, ny)))
            actions.append("MOVE")
            current_position[0], current_position[1] = nx, ny
        return actions

    def pickup_key():
        actions = ["PICKUP"]
        return actions

    def unlock_door():
        actions = ["UNLOCK"]
        return actions

    key_position = find_position(grid, "KEY")
    door_position = find_position(grid, "DOOR")
    start_position = find_position(grid, "AGENT")

    current_position = list(start_position)
    current_direction = start_direction
    actions = []

    # Move to the KEY
    if key_position:
        path_to_key = bfs(grid, start_position, key_position)
        actions.extend(execute_path(path_to_key))
        actions.extend(adjust_direction(current_direction, key_position))
        actions.extend(pickup_key())

    # Move to the DOOR with the key
    if door_position:
        path_to_door = bfs(grid, key_position, door_position)
        actions.extend(execute_path(path_to_door))
        actions.extend(adjust_direction(current_direction, door_position))
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