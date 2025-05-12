def solve(grid, start_direction):
    # Define directions and helper rotation maps.
    DIRECTIONS = {
        "UP":    (-1, 0),
        "DOWN":  (1, 0),
        "LEFT":  (0, -1),
        "RIGHT": (0, 1)
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

    # Helper: Check if the position is within bounds.
    def in_bounds(pos):
        r, c = pos
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])
    
    # Compute the cell one step ahead given a direction.
    def compute_next_position(pos, orient):
        dr, dc = DIRECTIONS[orient]
        r, c = pos
        return (r + dr, c + dc)
    
    # Helper: Check if a cell is traversable.
    # We consider it traversable if the cell is "" (empty) or "AGENT" (starting point)
    def is_cell_traversable(pos):
        if not in_bounds(pos):
            return False
        cell = grid[pos[0]][pos[1]]
        return cell == "" or cell == "AGENT"

    # Find the first occurrence of an object on the grid.
    def find_position(objectType):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == objectType:
                    return (r, c)
        return None

    # Given an object position, determine all target states.
    # A valid target state means that if the agent stands at (r, c) with a particular orientation,
    # then the cell immediately in front of it (one step in that direction) is the object's location.
    def generate_target_states(objectPos):
        targets = []
        for orient, (dr, dc) in DIRECTIONS.items():
            agent_r = objectPos[0] - dr
            agent_c = objectPos[1] - dc
            agent_pos = (agent_r, agent_c)
            if in_bounds(agent_pos) and is_cell_traversable(agent_pos):
                targets.append((agent_r, agent_c, orient))
        return targets

    # This BFS search state is (row, col, orientation, actions_so_far)
    # We only allow the actions "MOVE", "LEFT", and "RIGHT". When a target state is reached, we return
    # the list of actions needed.
    def find_optimal_plan(start_state, targets):
        from collections import deque
        visited = set()
        queue = deque()
        r0, c0, orient0, actions0 = start_state
        queue.append(start_state)
        visited.add((r0, c0, orient0))
        while queue:
            r, c, orient, actions = queue.popleft()
            # Check if the current state matches any target state.
            for (tr, tc, torient) in targets:
                if r == tr and c == tc and orient == torient:
                    return actions  # Found a plan.
            # Try "LEFT": turning left in place.
            new_orient = LEFT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append((r, c, new_orient, actions + ["LEFT"]))
            # Try "RIGHT": turning right in place.
            new_orient = RIGHT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append((r, c, new_orient, actions + ["RIGHT"]))
            # Try "MOVE": move forward if the next cell is traversable.
            next_pos = compute_next_position((r, c), orient)
            if is_cell_traversable(next_pos):
                state_id = (next_pos[0], next_pos[1], orient)
                if state_id not in visited:
                    visited.add(state_id)
                    queue.append((next_pos[0], next_pos[1], orient, actions + ["MOVE"]))
        return None  # No path found.

    # MAIN PLANNING:
    # Step 1: Locate AGENT, KEY, and DOOR.
    agentPos = find_position("AGENT")
    keyPos   = find_position("KEY")
    doorPos  = find_position("DOOR")
    if agentPos is None or keyPos is None or doorPos is None:
        return []  # One or more required objects not found.
    
    start_state = (agentPos[0], agentPos[1], start_direction, [])

    # Step 2: Plan a path so that the agent stands in a position adjacent to the KEY and is facing it.
    key_targets = generate_target_states(keyPos)
    key_plan_actions = find_optimal_plan(start_state, key_targets)
    if key_plan_actions is None:
        return []   # No valid plan to reach the KEY.
    # Append "PICKUP" to pick up the key.
    key_plan_actions = key_plan_actions + ["PICKUP"]

    # Helper: simulate the movement to update the agent's state.
    def simulate(state, actions):
        r, c, orient = state[0], state[1], state[2]
        for act in actions:
            if act == "LEFT":
                orient = LEFT_TURN[orient]
            elif act == "RIGHT":
                orient = RIGHT_TURN[orient]
            elif act == "MOVE":
                r, c = compute_next_position((r, c), orient)
            # "PICKUP" and "UNLOCK" do not affect orientation/position.
        return (r, c, orient)

    # Compute the agent's new state after picking up the KEY.
    key_state = simulate(start_state, key_plan_actions[:-1])
    # IMPORTANT: update the grid to remove the KEY. This ensures any cell that contained the key 
    # now becomes empty (and traversable) for the subsequent door planning.
    grid[keyPos[0]][keyPos[1]] = ""

    # Step 3: Now plan a path so that you stand in a cell adjacent to the DOOR and face it.
    door_targets = generate_target_states(doorPos)
    door_plan_actions = find_optimal_plan((key_state[0], key_state[1], key_state[2], []), door_targets)
    if door_plan_actions is None:
        return []  # No valid plan to reach the DOOR.
    # Append "UNLOCK" to complete the plan.
    door_plan_actions = door_plan_actions + ["UNLOCK"]

    # Return the full plan: first get the key, then head to and unlock the door.
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