def solve(grid, start_direction):
    from collections import deque

    # Helper functions
    def find_position(grid, item):
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                if cell == item:
                    return (i, j)
        return None

    def search_shortest_path(start, target):
        queue = deque([(start, [])])
        visited = set()
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        while queue:
            (current, path) = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            x, y = current
            
            # Check if target is reached
            if grid[x][y] == target:
                return path
            
            # Explore neighbors
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and grid[nx][ny] != "WALL":
                    queue.append(((nx, ny), path + [(nx, ny)]))
        
        return None
    
    def direction_from_to(start, end):
        sx, sy = start
        ex, ey = end
        if ex == sx and ey == sy + 1:
            return "RIGHT"
        if ex == sx and ey == sy - 1:
            return "LEFT"
        if ex == sx + 1 and ey == sy:
            return "DOWN"
        if ex == sx - 1 and ey == sy:
            return "UP"
        return None

    def turn_to_face(current_direction, target_direction):
        directions = ["UP", "RIGHT", "DOWN", "LEFT"]
        ci = directions.index(current_direction)
        ti = directions.index(target_direction)
        
        if ci == ti:
            return []
        
        turns = (ti - ci) % 4
        if turns == 1:
            return ["RIGHT"]
        elif turns == 2:
            return ["RIGHT", "RIGHT"]
        elif turns == 3:
            return ["LEFT"]
    
    def execute_path(path, start, start_direction):
        actions = []
        current_position = start
        current_direction = start_direction
        
        for next_step in path:
            target_direction = direction_from_to(current_position, next_step)
            actions.extend(turn_to_face(current_direction, target_direction))
            actions.append("MOVE")
            current_position = next_step
            current_direction = target_direction
        
        return actions, current_position, current_direction
    
    # Initialize
    agent_position = find_position(grid, "AGENT")
    has_key = False
    current_held_object = None
    actions = []

    # Get path to key and execute it
    path_to_key = search_shortest_path(agent_position, "KEY")
    if path_to_key:
        path_actions, agent_position, start_direction = execute_path(path_to_key, agent_position, start_direction)
        actions.extend(path_actions)
        actions.append("PICKUP")
        current_held_object = "KEY"

    # Get path to door and unlock it
    path_to_door = search_shortest_path(agent_position, "DOOR")
    if path_to_door:
        path_actions, agent_position, start_direction = execute_path(path_to_door, agent_position, start_direction)
        actions.extend(path_actions)
        actions.append("UNLOCK")
        # Consider the door now as an empty cell for future pathfinding
        door_position = path_to_door[-1]
        grid[door_position[0]][door_position[1]] = ""
    
    # Get path to box
    path_to_box = search_shortest_path(agent_position, "BOX")
    if path_to_box:
        # If holding key, find a place to drop it
        if current_held_object == "KEY":
            for x, y in path_to_box:
                if x == agent_position[0] and abs(y - agent_position[1]) == 1 or \
                   y == agent_position[1] and abs(x - agent_position[0]) == 1:
                    if grid[x][y] == "":
                        dir_to_empty = direction_from_to(agent_position, (x, y))
                        actions.extend(turn_to_face(start_direction, dir_to_empty))
                        actions.append("DROP")
                        start_direction = dir_to_empty
                        current_held_object = None
                        break
        
        # Move to box
        path_actions, _, start_direction = execute_path(path_to_box, agent_position, start_direction)
        actions.extend(path_actions)
        actions.append("PICKUP")
        current_held_object = "BOX"

    return actions

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