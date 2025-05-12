def solve(grid, start_direction):
    # Define movement vectors and turning maps.
    DIRECTIONS = {
        "UP":    (-1,  0),
        "DOWN":  ( 1,  0),
        "LEFT":  ( 0, -1),
        "RIGHT": ( 0,  1)
    }
    LEFT_TURN = {
        "UP": "LEFT",
        "LEFT": "DOWN",
        "DOWN": "RIGHT",
        "RIGHT": "UP"
    }
    RIGHT_TURN = {
        "UP": "RIGHT",
        "RIGHT": "DOWN",
        "DOWN": "LEFT",
        "LEFT": "UP"
    }
    
    # Check if a position is within grid bounds.
    def in_bounds(pos):
        r, c = pos
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])
    
    # Given a position and an orientation, compute the next cell.
    def compute_next_position(pos, orient):
        dr, dc = DIRECTIONS[orient]
        r, c = pos
        return (r + dr, c + dc)
    
    # A cell is traversable if it is empty ("") or contains "AGENT" (the starting marker).
    def is_cell_traversable(pos):
        if not in_bounds(pos):
            return False
        cell = grid[pos[0]][pos[1]]
        return cell == "" or cell == "AGENT"
    
    # Find first occurrence of a given object type on the grid.
    def find_position(objectType):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == objectType:
                    return (r, c)
        return None

    # For an object at objectPos, any agent state is acceptable if standing in a cell (r,c)
    # from where a MOVE would bring the agent exactly onto objectPos.
    # We generate all such (r, c, orient) states that are within bounds and whose cell is traversable.
    def generate_target_states(objectPos):
        targets = []
        for orient, (dr, dc) in DIRECTIONS.items():
            agent_r = objectPos[0] - dr
            agent_c = objectPos[1] - dc
            agent_pos = (agent_r, agent_c)
            if in_bounds(agent_pos) and is_cell_traversable(agent_pos):
                targets.append((agent_r, agent_c, orient))
        return targets

    # Use BFS to find a sequence of basic moves ("MOVE", "LEFT", "RIGHT")
    # that bring the agent (starting from start_state which is (r, c, orient, actions_so_far))
    # to any of the (r, c, orient) in targets.
    def find_optimal_plan(start_state, targets):
        from collections import deque
        visited = set()
        queue = deque()
        r0, c0, orient0, actions0 = start_state
        queue.append(start_state)
        visited.add((r0, c0, orient0))
        while queue:
            r, c, orient, actions = queue.popleft()
            # Check if we have reached any target state (using equality).
            for (tr, tc, torient) in targets:
                if r == tr and c == tc and orient == torient:
                    return actions  # Found a valid plan.
                    
            # Action "LEFT": turn left in place.
            new_orient = LEFT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append((r, c, new_orient, actions + ["LEFT"]))
                
            # Action "RIGHT": turn right in place.
            new_orient = RIGHT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append((r, c, new_orient, actions + ["RIGHT"]))
                
            # Action "MOVE": try to move forward if the next cell is traversable.
            next_pos = compute_next_position((r, c), orient)
            if is_cell_traversable(next_pos):
                state_id = (next_pos[0], next_pos[1], orient)
                if state_id not in visited:
                    visited.add(state_id)
                    queue.append((next_pos[0], next_pos[1], orient, actions + ["MOVE"]))
        return None  # No valid plan found.
    
    # Locate AGENT, KEY, and DOOR on the grid.
    agentPos = find_position("AGENT")
    keyPos   = find_position("KEY")
    doorPos  = find_position("DOOR")
    if agentPos is None or keyPos is None or doorPos is None:
        return []  # Required items not found.
    
    # Starting state (row, col, orientation, actions_so_far)
    start_state = (agentPos[0], agentPos[1], start_direction, [])
    
    # Step 1: Plan a path to a state adjacent to the KEY that faces the KEY.
    key_targets = generate_target_states(keyPos)
    key_plan_actions = find_optimal_plan(start_state, key_targets)
    if key_plan_actions is None:
        return []  # No valid plan to reach the KEY.
    # Append the PICKUP action.
    key_plan_actions = key_plan_actions + ["PICKUP"]
    
    # Simulate the path so far to update the agent's state.
    def simulate(state, actions):
        r, c, orient = state[0], state[1], state[2]
        for act in actions:
            if act == "LEFT":
                orient = LEFT_TURN[orient]
            elif act == "RIGHT":
                orient = RIGHT_TURN[orient]
            elif act == "MOVE":
                r, c = compute_next_position((r, c), orient)
            # PICKUP and UNLOCK do not change position or orientation.
        return (r, c, orient)
    
    key_state = simulate(start_state, key_plan_actions[:-1])
    
    # After picking up the KEY, remove it from the grid so that its cell becomes empty.
    grid[keyPos[0]][keyPos[1]] = ""
    
    # Step 2: Plan a path to a state adjacent to the DOOR that faces the DOOR.
    door_targets = generate_target_states(doorPos)
    door_plan_actions = find_optimal_plan((key_state[0], key_state[1], key_state[2], []), door_targets)
    if door_plan_actions is None:
        return []  # No valid plan to reach the DOOR.
    # Append the UNLOCK action.
    door_plan_actions = door_plan_actions + ["UNLOCK"]
    
    # Return the overall plan (first get the KEY, then go to the door and unlock it):
    full_plan = key_plan_actions + door_plan_actions
    return full_plan

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