def solve(grid, start_direction):
    # Define helper structures.
    DIRECTIONS = ["UP", "RIGHT", "DOWN", "LEFT"]
    DIR_VECTORS = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}

    actions = []

    # Helper: Check bounds.
    def in_bounds(pos):
        r, c = pos
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])

    # Helper: Check if cell is empty (allowed to move into).
    def is_empty(pos):
        # A cell is considered empty only if grid[r][c] is "".
        if not in_bounds(pos):
            return False
        return grid[pos[0]][pos[1]] == ""

    # Finds the first occurrence of an object.
    def find_object(object_type):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == object_type:
                    return (r, c)
        return None

    # Finds the AGENT start position.
    def find_agent():
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == "AGENT":
                    return (r, c)
        return None

    # For an object at pos, return an adjacent cell that is empty.
    def find_adjacent_empty_cell(targetPos):
        r, c = targetPos
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # UP, DOWN, LEFT, RIGHT order
            pos = (r + dr, c + dc)
            if in_bounds(pos) and is_empty(pos):
                return pos
        return None

    # For dropping an object, find any adjacent empty cell from agent’s position.
    def find_valid_drop_cell(agentPos):
        r, c = agentPos
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            pos = (r + dr, c + dc)
            if in_bounds(pos) and is_empty(pos):
                return pos
        return None

    # Helper: Given two adjacent positions, return the direction to move from pos1 to pos2.
    def direction_from(pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        if r2 == r1 - 1 and c2 == c1:  # move UP
            return "UP"
        elif r2 == r1 + 1 and c2 == c1:  # move DOWN
            return "DOWN"
        elif r2 == r1 and c2 == c1 - 1:  # move LEFT
            return "LEFT"
        elif r2 == r1 and c2 == c1 + 1:  # move RIGHT
            return "RIGHT"
        else:
            return None

    # Rotate from current_dir to desired_dir using minimal rotation commands.
    def get_rotation_commands(current_dir, desired_dir):
        cmds = []
        current_index = DIRECTIONS.index(current_dir)
        desired_index = DIRECTIONS.index(desired_dir)
        # Compute difference modulo 4.
        diff = (desired_index - current_index) % 4
        if diff == 0:
            return cmds, current_dir  # already facing
        elif diff == 1:
            cmds.append("RIGHT")
            current_dir = DIRECTIONS[(current_index+1) % 4]
        elif diff == 3:
            cmds.append("LEFT")
            current_dir = DIRECTIONS[(current_index-1) % 4]
        elif diff == 2:
            # Could rotate either way; choose two RIGHT commands.
            cmds.extend(["RIGHT", "RIGHT"])
            current_dir = DIRECTIONS[(current_index+2) % 4]
        return cmds, current_dir

    # Given a route (a list of positions the agent will step through),
    # output a sequence of rotation and MOVE commands.
    def execute_route(route, agent_pos, agent_dir):
        route_actions = []
        cur_pos = agent_pos
        cur_dir = agent_dir
        for next_pos in route:
            desired_dir = direction_from(cur_pos, next_pos)
            # Compute rotation commands if needed.
            rot_cmds, cur_dir = get_rotation_commands(cur_dir, desired_dir)
            route_actions.extend(rot_cmds)
            # Issue MOVE.
            route_actions.append("MOVE")
            cur_pos = next_pos
        return route_actions, cur_pos, cur_dir

    # Basic BFS based path planner over empty cells.
    def path_planner(start, goal):
        from collections import deque
        queue = deque()
        queue.append(start)
        came_from = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dr, current[1] + dc)
                if in_bounds(neighbor) and is_empty(neighbor) and neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)
        # Reconstruct path.
        if goal not in came_from:
            return None  # no path found
        path = []
        curr = goal
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

    # Rotate the agent so that it faces from pos to targetPos.
    def rotate_to_face(targetPos, agent_pos, agent_dir):
        desired = direction_from(agent_pos, targetPos)
        rot_cmds, new_dir = get_rotation_commands(agent_dir, desired)
        return rot_cmds, new_dir

    # ----- Main Routine -----
    # Get initial positions.
    agent_pos = find_agent()
    if agent_pos is None:
        return []
        # raise ValueError("AGENT not found in grid.")
    cur_dir = start_direction

    key_pos = find_object("KEY")
    door_pos = find_object("DOOR")
    box_pos = find_object("BOX")

    if key_pos is None or door_pos is None or box_pos is None:
        return []
        # raise ValueError("One of the required objects (KEY, DOOR, BOX) is missing.")

    hasKey = False
    # Phase 1: Navigate to the KEY.
    key_target = find_adjacent_empty_cell(key_pos)
    if key_target is None:
        return []
        # raise ValueError("No adjacent empty cell found for KEY pickup.")
    route = path_planner(agent_pos, key_target)
    if route is None:
        return []
        # raise ValueError("No route found to KEY target.")
    cmds, agent_pos, cur_dir = execute_route(route, agent_pos, cur_dir)
    actions.extend(cmds)
    # Rotate to face the KEY.
    rot_cmds, cur_dir = rotate_to_face(key_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)
    actions.append("PICKUP")
    hasKey = True

    # Phase 2: Carry KEY to the DOOR.
    door_target = find_adjacent_empty_cell(door_pos)
    if door_target is None:
        return []
        # raise ValueError("No adjacent empty cell found for DOOR unlock position.")
    route = path_planner(agent_pos, door_target)
    if route is None:
        return []
        # raise ValueError("No route found to DOOR target.")
    cmds, agent_pos, cur_dir = execute_route(route, agent_pos, cur_dir)
    actions.extend(cmds)
    # Rotate to face the DOOR.
    rot_cmds, cur_dir = rotate_to_face(door_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)
    # Unlock the door (requires holding key).
    if hasKey:
        actions.append("UNLOCK")
        # Mark door as unlocked.
        r, c = door_pos
        grid[r][c] = ""
    else:
        return []
        # raise ValueError("Tried to unlock door without key.")

    # Phase 3: Cross the door and approach the BOX.
    box_target = find_adjacent_empty_cell(box_pos)
    if box_target is None:
        return []
        # raise ValueError("No adjacent empty cell found for BOX pickup.")
    route = path_planner(agent_pos, box_target)
    if route is None:
        return []
        # raise ValueError("No route found to BOX target.")
    cmds, agent_pos, cur_dir = execute_route(route, agent_pos, cur_dir)
    actions.extend(cmds)
    # Rotate to face the BOX.
    rot_cmds, cur_dir = rotate_to_face(box_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)

    # Phase 4: Drop the KEY to free up our hand.
    drop_cell = find_valid_drop_cell(agent_pos)
    if drop_cell is None:
        return []
        # raise ValueError("No valid cell to drop the KEY.")
    rot_cmds, cur_dir = rotate_to_face(drop_cell, agent_pos, cur_dir)
    actions.extend(rot_cmds)
    actions.append("DROP")
    hasKey = False

    # Phase 5: Pickup the BOX.
    # Assuming that by facing the BOX, the object is in the adjacent cell.
    actions.append("PICKUP")

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