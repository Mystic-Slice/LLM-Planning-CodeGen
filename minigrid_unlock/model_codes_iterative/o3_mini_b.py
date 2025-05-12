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
    
    # Helper: Check if the position is within bounds.
    def in_bounds(pos):
        r, c = pos
        return 0 <= r < len(grid) and 0 <= c < len(grid[0])
    
    # Helper: Given a position and orientation, compute the cell one step ahead.
    def compute_next_position(pos, orient):
        dr, dc = DIRECTIONS[orient]
        r, c = pos
        return (r + dr, c + dc)
    
    # Helper: Check if a cell is traversable. The agent can only move into cells that are empty
    # or contain only the original "AGENT" (so that we can start there).
    def is_cell_traversable(pos):
        if not in_bounds(pos):
            return False
        cell = grid[pos[0]][pos[1]]
        return cell == "" or cell == "AGENT"
    
    # Find a cell containing a particular object.
    def find_position(objectType):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == objectType:
                    return (r, c)
        return None

    # Given an object position (for KEY or DOOR), generate all target states.
    # A target state is (r, c, orientation) so that the cell immediately in front of you (in that orientation)
    # is exactly the object’s position.
    def generate_target_states(objectPos):
        targets = []
        for orient, (dr, dc) in DIRECTIONS.items():
            agent_r = objectPos[0] - dr
            agent_c = objectPos[1] - dc
            agent_pos = (agent_r, agent_c)
            if in_bounds(agent_pos) and is_cell_traversable(agent_pos):
                targets.append((agent_r, agent_c, orient))
        return targets

    # Breadth-first search: the state is (row, col, orientation, actions_so_far).
    # Allowed actions are "MOVE", "LEFT", and "RIGHT". We return the list of actions once
    # a target state (one adjacent to the object with the proper orientation) is reached.
    def find_optimal_plan(start_state, targets):
        from collections import deque
        visited = set()
        queue = deque()
        queue.append(start_state)
        visited.add((start_state[0], start_state[1], start_state[2]))
        while queue:
            r, c, orient, actions = queue.popleft()
            # Check if current state matches any target state.
            for (tr, tc, torient) in targets:
                if r == tr and c == tc and orient == torient:
                    return actions  # Found a plan.
            # Try all actions.
            # a) "LEFT": turn left without changing position.
            new_orient = LEFT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append((r, c, new_orient, actions + ["LEFT"]))
            # b) "RIGHT": turn right without changing position.
            new_orient = RIGHT_TURN[orient]
            state_id = (r, c, new_orient)
            if state_id not in visited:
                visited.add(state_id)
                queue.append((r, c, new_orient, actions + ["RIGHT"]))
            # c) "MOVE": move forward if the next cell is traversable.
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
    # Step 2: Find a plan so that we face the KEY.
    key_targets = generate_target_states(keyPos)
    key_plan_actions = find_optimal_plan(start_state, key_targets)
    if key_plan_actions is None:
        return []   # No valid plan to reach the KEY.
    # Append "PICKUP" because when adjacent and facing, we pick the KEY.
    key_plan_actions = key_plan_actions + ["PICKUP"]

    # Helper to simulate movement (for state update).
    def simulate(state, actions):
        r, c, orient = state[0], state[1], state[2]
        for act in actions:
            if act == "LEFT":
                orient = LEFT_TURN[orient]
            elif act == "RIGHT":
                orient = RIGHT_TURN[orient]
            elif act == "MOVE":
                r, c = compute_next_position((r, c), orient)
            # "PICKUP" and "UNLOCK" do not change position/orientation.
        return (r, c, orient)
    
    # The state after picking up the KEY (position and orientation do not change).
    key_state = simulate(start_state, key_plan_actions[:-1])
    
    # Step 3: Now plan movement so that we face the DOOR.
    door_targets = generate_target_states(doorPos)
    door_plan_actions = find_optimal_plan((key_state[0], key_state[1], key_state[2], []), door_targets)
    if door_plan_actions is None:
        return []  # No valid plan to reach the DOOR.
    # Append "UNLOCK" since we have the KEY and now are adjacent to the door facing it.
    door_plan_actions = door_plan_actions + ["UNLOCK"]

    # Step 4: The full solution is getting the KEY then unlocking the DOOR.
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

#     grid = [
#         ["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"],
# ["WALL","","","","","WALL","","","","","WALL"],
# ["WALL","AGENT","","","","WALL","","","","","WALL"],
# ["WALL","","","","","WALL","","","","","WALL"],
# ["WALL","","","","KEY","DOOR","","","","","WALL"],
# ["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"]
#     ]
    direction = "RIGHT"
    
    actions = solve(grid, direction)
    print("Actions to solve the game:", actions)