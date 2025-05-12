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
    
    dirs = {"UP": (-1,0), "DOWN": (1,0), "LEFT": (0,-1), "RIGHT": (0,1)}
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
            return door_unlocked and front == door_pos
        if cell in ["KEY", "AGENT", "GOAL"]:
            return True
        return True

    def navigate(start_pos, start_dir, check_condition, max_steps=None, has_key_initial=False, door_unlocked_initial=False):
        queue = deque([(start_pos, start_dir, [], has_key_initial, door_unlocked_initial)])
        visited = set()
        while queue:
            pos, d, path, has_key, door_unlocked = queue.popleft()
            if (pos, d, has_key, door_unlocked) in visited:
                continue
            visited.add((pos, d, has_key, door_unlocked))
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
                    if can_move(pos, d, has_key, door_unlocked):
                        new_pos = get_front_pos(pos, d)
                    else:
                        continue
                new_path.append(action)
                cell = grid[new_pos[0]][new_pos[1]] if new_pos != pos else None
                if cell == "KEY" and not has_key and get_front_pos(pos, d) == new_pos and action == "MOVE":
                    pass
                queue.append((new_pos, new_dir, new_path, new_has_key, new_door_unlocked))
        return None
    
    def pick_key_condition(pos, d, has_key, door_unlocked, path):
        front = get_front_pos(pos, d)
        return not has_key and front == key_pos
    
    phase1 = navigate(agent_pos, start_direction, pick_key_condition)
    if not phase1:
        return []
    phase1.append("PICKUP")
    current_dir = start_direction
    current_pos = agent_pos
    has_key = False
    for a in phase1:
        if a == "LEFT":
            current_dir = turn_left[current_dir]
        elif a == "RIGHT":
            current_dir = turn_right[current_dir]
        elif a == "MOVE":
            front = get_front_pos(current_pos, current_dir)
            if can_move(current_pos, current_dir, has_key, False):
                current_pos = front
        elif a == "PICKUP":
            has_key = True
    
    def unlock_door_condition(pos, d, has_key, door_unlocked, path):
        front = get_front_pos(pos, d)
        return has_key and front == door_pos
    
    phase2 = navigate(current_pos, current_dir, unlock_door_condition, has_key_initial=has_key)
    if not phase2:
        return []
    phase2.append("UNLOCK")
    door_unlocked = False
    for a in phase2:
        if a == "LEFT":
            current_dir = turn_left[current_dir]
        elif a == "RIGHT":
            current_dir = turn_right[current_dir]
        elif a == "MOVE":
            front = get_front_pos(current_pos, current_dir)
            if can_move(current_pos, current_dir, has_key, door_unlocked):
                current_pos = front
        elif a == "UNLOCK":
            door_unlocked = True
    
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