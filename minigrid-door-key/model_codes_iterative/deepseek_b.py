from collections import deque

def solve(grid, start_direction):
    def find_position(target):
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == target:
                    return (r, c)
        return None
    
    agent_pos = find_position("AGENT")
    key_pos = find_position("KEY")
    door_pos = find_position("DOOR")
    goal_pos = find_position("GOAL")
    
    dirs = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
    turn_left = {"UP": "LEFT", "LEFT": "DOWN", "DOWN": "RIGHT", "RIGHT": "UP"}
    turn_right = {"UP": "RIGHT", "RIGHT": "DOWN", "DOWN": "LEFT", "LEFT": "UP"}
    
    def get_front_pos(pos, d):
        dr, dc = dirs[d]
        return (pos[0] + dr, pos[1] + dc)
    
    def can_move(pos, d, has_key, door_unlocked):
        front = get_front_pos(pos, d)
        if front[0] < 0 or front[0] >= len(grid) or front[1] < 0 or front[1] >= len(grid[0]):
            return False
        cell = grid[front[0]][front[1]]
        if cell == "WALL":
            return False
        if cell == "DOOR":
            return door_unlocked
        if cell == "KEY":
            return False
        if cell == "AGENT":
            return False  # Cannot move into the starting position where another agent is
        return True
    
    def navigate(start_pos, start_dir, check_condition, max_steps=None, has_key_initial=False, door_unlocked_initial=False):
        queue = deque([(start_pos, start_dir, [], has_key_initial, door_unlocked_initial)])
        visited = set()
        
        while queue:
            pos, d, path, has_key, door_unlocked = queue.popleft()
            state_key = (pos, d, has_key, door_unlocked)
            if state_key in visited:
                continue
            visited.add(state_key)
            
            if check_condition(pos, d, has_key, door_unlocked, path):
                return path
            
            if max_steps is not None and len(path) >= max_steps:
                continue
            
            for action in ["LEFT", "RIGHT", "MOVE"]:
                new_pos, new_dir = pos, d
                new_has_key = has_key
                new_door_unlocked = door_unlocked
                new_path = path.copy()
                
                if action == "LEFT":
                    new_dir = turn_left[d]
                elif action == "RIGHT":
                    new_dir = turn_right[d]
                elif action == "MOVE":
                    if not can_move(pos, d, has_key, door_unlocked):
                        continue
                    new_pos = get_front_pos(pos, d)
                
                new_path.append(action)
                queue.append((new_pos, new_dir, new_path, new_has_key, new_door_unlocked))
        
        return None
    
    # Phase 1: Navigate to and pick up the key
    def pick_key_condition(pos, d, has_key, door_unlocked, path):
        if has_key:
            return False
        front = get_front_pos(pos, d)
        return front == key_pos
    
    phase1 = navigate(agent_pos, start_direction, pick_key_condition)
    if not phase1:
        return []
    
    phase1.append("PICKUP")
    
    # Compute state after phase1
    current_pos = agent_pos
    current_dir = start_direction
    has_key = False
    door_unlocked = False
    for action in phase1:
        if action == "LEFT":
            current_dir = turn_left[current_dir]
        elif action == "RIGHT":
            current_dir = turn_right[current_dir]
        elif action == "MOVE":
            current_pos = get_front_pos(current_pos, current_dir)
        elif action == "PICKUP":
            has_key = True
            # Update grid state (logically remove the key)
            if current_pos == key_pos:
                pass
            else:
                front_pos = get_front_pos(current_pos, current_dir)
                if front_pos == key_pos:
                    grid[key_pos[0]][key_pos[1]] = ""
    
    # Phase 2: Navigate to and unlock the door
    def unlock_door_condition(pos, d, has_key, door_unlocked, path):
        front = get_front_pos(pos, d)
        return has_key and front == door_pos
    
    phase2 = navigate(current_pos, current_dir, unlock_door_condition, has_key_initial=has_key)
    if not phase2:
        return []
    
    phase2.append("UNLOCK")
    
    # Compute state after phase2
    for action in phase2:
        if action == "LEFT":
            current_dir = turn_left[current_dir]
        elif action == "RIGHT":
            current_dir = turn_right[current_dir]
        elif action == "MOVE":
            current_pos = get_front_pos(current_pos, current_dir)
        elif action == "UNLOCK":
            door_unlocked = True
    
    # Phase 3: Navigate to the goal
    def reach_goal_condition(pos, d, has_key, door_unlocked, path):
        return pos == goal_pos
    
    phase3 = navigate(current_pos, current_dir, reach_goal_condition, door_unlocked_initial=door_unlocked)
    if not phase3:
        return []
    
    return phase1 + phase2 + phase3

if __name__ == "__main__":
    # Example grid and direction
    grid = [["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"],
["WALL","","","","DOOR","","","WALL"],
["WALL","","","","WALL","","","WALL"],
["WALL","","","","WALL","","","WALL"],
["WALL","","","KEY","WALL","","","WALL"],
["WALL","AGENT","","","WALL","","","WALL"],
["WALL","","","","WALL","","GOAL","WALL"],
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"]]
    direction = "DOWN"
    
    actions = solve(grid, direction)
    print("Actions to solve the game:", actions)