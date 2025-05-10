def solve(grid, start_direction):
    from collections import deque
    
    # Helper functions
    def find_position(grid, item):
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                if cell == item:
                    return (i, j)
        return None
    
    def search_shortest_path(start, target, consider_doors=False):
        # consider_doors: Flag for considering unlocked doors as passable
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
            if current == target:
                return path
            # Explore neighbors
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]):
                    if grid[nx][ny] != "WALL":
                        # Allow passage if it's a door and we're considering doors passable or if it's an empty cell
                        if grid[nx][ny] == "" or (grid[nx][ny] == "DOOR" and consider_doors):
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
    key_position = find_position(grid, "KEY")
    path_to_key = search_shortest_path(agent_position, key_position)
    if path_to_key:
        path_actions, agent_position, start_direction = execute_path(path_to_key, agent_position, start_direction)
        actions.extend(path_actions)
        actions.append("PICKUP")
        current_held_object = "KEY"
    
    # Get path to door and unlock it
    door_position = find_position(grid, "DOOR")
    path_to_door = search_shortest_path(agent_position, door_position)
    if path_to_door:
        path_actions, agent_position, start_direction = execute_path(path_to_door, agent_position, start_direction)
        actions.extend(path_actions)
        actions.append("UNLOCK")
        # Consider the door now as an empty cell for future pathfinding
        grid[door_position[0]][door_position[1]] = ""
    
    # Get path to box
    box_position = find_position(grid, "BOX")
    path_to_box = search_shortest_path(agent_position, box_position, consider_doors=True)
    if path_to_box:
        # If holding key, find a place to drop it
        if current_held_object == "KEY":
            # Look for the adjacent place to drop the key
            found = False
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = agent_position[0] + dx, agent_position[1] + dy
                if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]):
                    if grid[nx][ny] == "":
                        dir_to_empty = direction_from_to(agent_position, (nx, ny))
                        actions.extend(turn_to_face(start_direction, dir_to_empty))
                        actions.append("DROP")
                        start_direction = dir_to_empty
                        current_held_object = None
                        found = True
                        break
            if not found:
                raise Exception("No valid adjacent cell found to drop the KEY")
        
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