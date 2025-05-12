def solve(grid, start_direction):
    # Define helper data structures.
    DIRECTIONS = ["UP", "RIGHT", "DOWN", "LEFT"]
    DIR_VECTORS = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
    actions = []
    
    # --- Helpers ---
    def in_bounds(pos):
        r, c = pos
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])
    
    def is_empty(pos):
        # A cell is empty only if it is exactly ""
        if not in_bounds(pos):
            return False
        return grid[pos[0]][pos[1]] == ""
    
    # Find first occurrence of an object type.
    def find_object(object_type):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == object_type:
                    return (r, c)
        return None

    def find_agent():
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == "AGENT":
                    return (r, c)
        return None

    # Given a position, return adjacent (up/down/left/right) positions.
    def adjacent_positions(pos):
        r, c = pos
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nxt = (r+dr, c+dc)
            if in_bounds(nxt):
                yield nxt

    # Instead of returning one adjacent empty cell, return all candidates.
    def get_empty_adjacent_cells(targetPos):
        candidates = []
        for nbr in adjacent_positions(targetPos):
            if is_empty(nbr):
                candidates.append(nbr)
        return candidates

    # We want to plan a route where the goal is to stand on some empty cell adjacent to the target.
    def plan_to_adjacent(start, target):
        candidates = get_empty_adjacent_cells(target)
        best_route = None
        best_length = None
        for candidate in candidates:
            route = path_planner(start, candidate)
            if route is not None:
                if best_route is None or len(route) < best_length:
                    best_route = route
                    best_length = len(route)
        return best_route

    # For drop targets: get any adjacent empty cell to current position.
    def get_drop_candidates(agentPos):
        return [nbr for nbr in adjacent_positions(agentPos) if is_empty(nbr)]
    
    # Given two adjacent positions, return the direction to go from pos1 to pos2.
    def direction_from(pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        if r2 == r1 - 1 and c2 == c1:
            return "UP"
        elif r2 == r1 + 1 and c2 == c1:
            return "DOWN"
        elif r2 == r1 and c2 == c1 - 1:
            return "LEFT"
        elif r2 == r1 and c2 == c1 + 1:
            return "RIGHT"
        else:
            return None

    # Rotate from current_dir to desired_dir using minimal rotation commands.
    def get_rotation_commands(current_dir, desired_dir):
        cmds = []
        current_index = DIRECTIONS.index(current_dir)
        desired_index = DIRECTIONS.index(desired_dir)
        diff = (desired_index - current_index) % 4
        if diff == 0:
            return cmds, current_dir  # Already facing that direction.
        elif diff == 1:
            cmds.append("RIGHT")
            current_dir = DIRECTIONS[(current_index+1) % 4]
        elif diff == 3:
            cmds.append("LEFT")
            current_dir = DIRECTIONS[(current_index-1) % 4]
        elif diff == 2:
            # Two turns required (choose two RIGHT turns).
            cmds.extend(["RIGHT", "RIGHT"])
            current_dir = DIRECTIONS[(current_index+2)%4]
        return cmds, current_dir

    # Given a route (list of positions to step through), return a list of rotation and MOVE commands.
    def execute_route(route, agent_pos, agent_dir):
        route_actions = []
        cur_pos = agent_pos
        cur_dir = agent_dir
        for next_pos in route:
            desired_dir = direction_from(cur_pos, next_pos)
            rot_cmds, cur_dir = get_rotation_commands(cur_dir, desired_dir)
            route_actions.extend(rot_cmds)
            route_actions.append("MOVE")
            cur_pos = next_pos
        return route_actions, cur_pos, cur_dir

    # BFS path planner (only through cells that are empty).
    def path_planner(start, goal):
        from collections import deque
        queue = deque()
        queue.append(start)
        came_from = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                neighbor = (current[0]+dr, current[1]+dc)
                if in_bounds(neighbor) and (is_empty(neighbor) or neighbor==goal) and neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)
        if goal not in came_from:
            return None
        path = []
        cur = goal
        while cur != start:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path

    # Rotate the agent so that it faces from pos to targetPos.
    def rotate_to_face(targetPos, agent_pos, agent_dir):
        desired = direction_from(agent_pos, targetPos)
        if desired is None: 
            return [], agent_dir
        rot_cmds, new_dir = get_rotation_commands(agent_dir, desired)
        return rot_cmds, new_dir

    # ----- Main Routine -----
    # Get initial positions.
    agent_pos = find_agent()
    if agent_pos is None:
        return []
    cur_dir = start_direction
    key_pos = find_object("KEY")
    door_pos = find_object("DOOR")
    box_pos = find_object("BOX")
    if key_pos is None or door_pos is None or box_pos is None:
        return []
    
    hasKey = False

    # PHASE 1: Navigate to the KEY.
    # Find a reachable cell adjacent to the KEY.
    route = plan_to_adjacent(agent_pos, key_pos)
    if route is None:
        return []
    cmds, agent_pos, cur_dir = execute_route(route, agent_pos, cur_dir)
    actions.extend(cmds)
    # Face the KEY.
    rot_cmds, cur_dir = rotate_to_face(key_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)
    actions.append("PICKUP")
    hasKey = True

    # PHASE 2: Carry the KEY to the DOOR.
    route = plan_to_adjacent(agent_pos, door_pos)
    if route is None:
        return []
    cmds, agent_pos, cur_dir = execute_route(route, agent_pos, cur_dir)
    actions.extend(cmds)
    # Face the door.
    rot_cmds, cur_dir = rotate_to_face(door_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)
    if hasKey:
        actions.append("UNLOCK")
        # Mark door as unlocked (set to empty).
        r, c = door_pos
        grid[r][c] = ""
    else:
        return []

    # PHASE 3: Approach the BOX.
    route = plan_to_adjacent(agent_pos, box_pos)
    if route is None:
        return []
    cmds, agent_pos, cur_dir = execute_route(route, agent_pos, cur_dir)
    actions.extend(cmds)
    # Now face the box.
    rot_cmds, cur_dir = rotate_to_face(box_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)

    # PHASE 4: Drop the KEY (we must free our hand to pick up the BOX).
    drop_candidates = get_drop_candidates(agent_pos)
    # We choose one candidate that does not coincide with the direction of the box.
    # (Since the cell being dropped into must be in front of us when we issue DROP.)
    drop_cell = None
    for candidate in drop_candidates:
        # If facing the candidate gives the same direction as the box,
        # then candidate might be used improperly. So skip if it is exactly in
        # the same direction as box relative to agent.
        if direction_from(agent_pos, candidate) != direction_from(agent_pos, box_pos):
            drop_cell = candidate
            break
    # If none found, then simply use the first candidate.
    if drop_cell is None and drop_candidates:
        drop_cell = drop_candidates[0]
    if drop_cell is None:
        return []
    rot_cmds, cur_dir = rotate_to_face(drop_cell, agent_pos, cur_dir)
    actions.extend(rot_cmds)
    actions.append("DROP")
    hasKey = False

    rot_cmds, cur_dir = rotate_to_face(box_pos, agent_pos, cur_dir)
    actions.extend(rot_cmds)

    # PHASE 5: Now that our hand is free and we are facing the BOX,
    # the box is an adjacent object – so we pick it up.
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