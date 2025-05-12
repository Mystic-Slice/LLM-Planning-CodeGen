def solve(grid, start_direction):
    # Define directions and helper rotation maps.
    DIRECTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
    }
    
    # Rotation maps:
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
    
    # Basic helper functions:
    def in_bounds(pos):
        r, c = pos
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])
    
    def compute_next_position(pos, orient):
        dr, dc = DIRECTIONS[orient]
        r, c = pos
        return (r + dr, c + dc)
    
    def is_cell_traversable(pos):
        # Allowed cells for moving: empty string or the cell that originally had AGENT.
        # We assume that WALL, KEY, DOOR are obstacles.
        if not in_bounds(pos):
            return False
        cell = grid[pos[0]][pos[1]]
        return cell == "" or cell == "AGENT"
    
    def find_position(objectType):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == objectType:
                    return (r, c)
        return None

    # Given an object position (for KEY or DOOR) generate all target states:
    # A target state is a tuple (r, c, orientation) such that if the agent stands there,
    # then the cell immediately in front (according to orientation) is the object.
    def generate_target_states(objectPos):
        targets = []
        for orient, (dr, dc) in DIRECTIONS.items():
            # For the object to be in front, the agent must be one cell opposite:
            agent_r = objectPos[0] - dr
            agent_c = objectPos[1] - dc
            agent_pos = (agent_r, agent_c)
            if in_bounds(agent_pos):
                # In planning, we need to stand on a traversable cell.
                if is_cell_traversable(agent_pos):
                    targets.append( (agent_r, agent_c, orient) )
        return targets

    # Breadth-first search: state is represented as (row, col, orientation, actions_so_far).
    # Allowed actions: "MOVE", "LEFT", "RIGHT".
    # Return the list of actions if a target state is found,
    # where a state (r, c, orient) matches if it is in the targets.
    def find_optimal_plan(start_state, targets):
        from collections import deque
        
        # We use a set of (row, col, orientation) to mark visited states.
        visited = set()
        queue = deque()
        # start_state: (row, col, orientation, actions)
        queue.append(start_state)
        visited.add( (start_state[0], start_state[1], start_state[2]) )
        
        while queue:
            r, c, orient, actions = queue.popleft()
            # Check if current state matches any target state.
            for (tr, tc, torient) in targets:
                if r == tr and c == tc and orient == torient:
                    return actions  # Found a plan.
            # Try all actions.
            # a) Action "LEFT" (turn left in place)
            new_orient = LEFT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append( (r, c, new_orient, actions + ["LEFT"]) )
            # b) Action "RIGHT" (turn right in place)
            new_orient = RIGHT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append( (r, c, new_orient, actions + ["RIGHT"]) )
            # c) Action "MOVE" (move forward in current orientation)
            next_pos = compute_next_position((r, c), orient)
            if is_cell_traversable(next_pos):
                state_id = (next_pos[0], next_pos[1], orient)
                if state_id not in visited:
                    visited.add(state_id)
                    queue.append( (next_pos[0], next_pos[1], orient, actions + ["MOVE"]) )
        return None   # Failure if no path is found.
    
    # ------------------------------------------------------------
    # MAIN PLANNING:
    # Step 1: Find positions of AGENT, KEY, and DOOR.
    agentPos = find_position("AGENT")
    keyPos   = find_position("KEY")
    doorPos  = find_position("DOOR")
    
    if agentPos is None or keyPos is None or doorPos is None:
        return []  # Missing required objects.
    
    # Starting state: (row, col, orientation, actions_so_far)
    start_state = (agentPos[0], agentPos[1], start_direction, [])
    
    # Step 2: Generate target states for key.
    key_targets = generate_target_states(keyPos)
    key_plan_actions = find_optimal_plan(start_state, key_targets)
    if key_plan_actions is None:
        return []   # No valid plan to reach KEY.
    # Append PICKUP (assuming key is directly ahead when in correct orientation)
    key_plan_actions = key_plan_actions + ["PICKUP"]
    
    # Determine new state after picking up the key.
    # Since PICKUP does not move the agent, the current position and orientation remain as before.
    # We need to compute what state we ended in in our key planning.
    # For that, simulate the actions in key_plan_actions (except the final PICKUP).
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
    
    # Step 3: Generate target states for door.
    door_targets = generate_target_states(doorPos)
    door_plan_actions = find_optimal_plan( (key_state[0], key_state[1], key_state[2], []), door_targets)
    if door_plan_actions is None:
        return []  # No valid plan to reach DOOR.
    # Append UNLOCK.
    door_plan_actions = door_plan_actions + ["UNLOCK"]
    
    # Step 4: Combine plans.
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