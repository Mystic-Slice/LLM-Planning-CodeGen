import heapq

def solve(grid, start_direction):
    # Find positions of key objects.
    agent_pos = find_cell(grid, "AGENT")
    key_pos = find_cell(grid, "KEY")
    door_pos = find_cell(grid, "DOOR")
    goal_pos = find_cell(grid, "GOAL")
    
    actions = []
    current_direction = start_direction
    current_pos = agent_pos
    agent_has_key = False

    # --- If there is a key, plan to pick it up ---
    if key_pos is not None:
        # Instead of simply picking the first approach cell for the key, we try all possible
        # approach candidates and choose the one that gives the shortest A* route.
        approach, desired_dir = choose_best_approach(current_pos, key_pos, grid, agent_has_key=False)
        if approach is None:
            raise Exception("No valid approach for KEY found!")
        path = a_star_search(current_pos, approach, grid, agent_has_key)
        path_cmds, current_direction = path_to_actions(path, current_direction)
        actions.extend(path_cmds)
        current_pos = approach

        # now adjust so that the KEY is exactly in front
        turn_cmds, current_direction = adjust_heading_for_target(current_direction, desired_dir)
        actions.extend(turn_cmds)

        # pick up the key
        actions.append("PICKUP")
        agent_has_key = True
        # remove the key from the grid (to make future path planning easier)
        grid[key_pos[0]][key_pos[1]] = ""
    
    # --- Now approach the door ---
    if door_pos is not None:
        approach, desired_dir = choose_best_approach(current_pos, door_pos, grid, agent_has_key)
        if approach is None:
            raise Exception("No valid approach for DOOR found!")
        path = a_star_search(current_pos, approach, grid, agent_has_key)
        path_cmds, current_direction = path_to_actions(path, current_direction)
        actions.extend(path_cmds)
        current_pos = approach

        # adjust heading so door is just ahead
        turn_cmds, current_direction = adjust_heading_for_target(current_direction, desired_dir)
        actions.extend(turn_cmds)

        # unlock door
        actions.append("UNLOCK")
        # remove door from grid after unlocking
        grid[door_pos[0]][door_pos[1]] = ""

    # --- Finally plan a route to the goal cell ---
    path = a_star_search(current_pos, goal_pos, grid, agent_has_key)
    path_cmds, current_direction = path_to_actions(path, current_direction)
    actions.extend(path_cmds)

    return actions

# Helper: find the cell that contains the given object.
def find_cell(grid, obj):
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == obj:
                return (r, c)
    return None

# New helper: Given current position and target cell (KEY or DOOR),
# consider all 4 directions where standing one cell away (the "approach" cell)
# would have the target directly in front. For each candidate that is accessible,
# compute the A* cost from the current position. Choose the candidate with the lowest cost.
def choose_best_approach(curr_pos, target_pos, grid, agent_has_key):
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    deltas = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    best_candidate = None
    best_dir = None
    best_cost = float('inf')
    for d in directions:
        dr, dc = deltas[d]
        approach = (target_pos[0] - dr, target_pos[1] - dc)
        if in_bounds(approach, len(grid), len(grid[0])) and is_accessible(approach, grid, agent_has_key):
            # Try to find path cost from curr_pos to this candidate approach.
            path = a_star_search(curr_pos, approach, grid, agent_has_key)
            if path and len(path) < best_cost:
                best_candidate = approach
                best_dir = d
                best_cost = len(path)
    return best_candidate, best_dir

# A* search to find a path from start to goal, returning a list of cells.
def a_star_search(start, goal, grid, agent_has_key):
    rows = len(grid)
    cols = len(grid[0])
    directions = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    def heuristic(cell):
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])
    open_set = []
    heapq.heappush(open_set, (heuristic(start), 0, start))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current_cost, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)
        for move in directions.values():
            neighbor = (current[0] + move[0], current[1] + move[1])
            if not in_bounds(neighbor, rows, cols):
                continue    
            if not is_accessible(neighbor, grid, agent_has_key):
                continue
            tentative_cost = current_cost + 1
            if neighbor not in g_score or tentative_cost < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_cost
                f_score = tentative_cost + heuristic(neighbor)
                heapq.heappush(open_set, (f_score, tentative_cost, neighbor))
    return []  # if no path found

# Helper: Reconstruct path from the A* search.
def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path

def in_bounds(cell, rows, cols):
    r, c = cell
    return 0 <= r < rows and 0 <= c < cols

# Convert a path (list of grid cells) to action commands,
# considering the agent's current facing direction.
def path_to_actions(path, current_direction):
    commands = []
    for i in range(1, len(path)):
        prev = path[i-1]
        curr = path[i]
        desired_direction = get_direction(prev, curr)
        turn_cmds, current_direction = adjust_heading_for_target(current_direction, desired_direction)
        commands.extend(turn_cmds)
        commands.append("MOVE")
    return commands, current_direction

# Compute the direction (UP, DOWN, LEFT, RIGHT) that moves from cell1 to cell2.
def get_direction(cell1, cell2):
    r1, c1 = cell1
    r2, c2 = cell2
    if r2 < r1:
        return "UP"
    elif r2 > r1:
        return "DOWN"
    elif c2 < c1:
        return "LEFT"
    elif c2 > c1:
        return "RIGHT"
    return None

# Adjust heading so that current_direction becomes desired_direction.
# Return a list of turn commands and the updated current_direction.
def adjust_heading_for_target(current_direction, desired_direction):
    commands = []
    while current_direction != desired_direction:
        # We choose a minimal turn strategy.
        if rotate_left(current_direction) == desired_direction:
            commands.append("LEFT")
            current_direction = rotate_left(current_direction)
        else:
            commands.append("RIGHT")
            current_direction = rotate_right(current_direction)
    return commands, current_direction

def rotate_left(direction):
    if direction == "UP":
        return "LEFT"
    if direction == "LEFT":
        return "DOWN"
    if direction == "DOWN":
        return "RIGHT"
    if direction == "RIGHT":
        return "UP"

def rotate_right(direction):
    if direction == "UP":
        return "RIGHT"
    if direction == "RIGHT":
        return "DOWN"
    if direction == "DOWN":
        return "LEFT"
    if direction == "LEFT":
        return "UP"

# Check if a cell is accessible.
# Walls are never accessible.
# If the cell contains a DOOR and the agent does not have the key, it is blocked.
# Also a cell containing a KEY is blocked (so that we plan our approach cell separately).
def is_accessible(cell, grid, agent_has_key):
    rows = len(grid)
    cols = len(grid[0])
    r, c = cell
    if not in_bounds(cell, rows, cols):
        return False
    content = grid[r][c]
    if content == "WALL":
        return False
    if content == "DOOR" and not agent_has_key:
        return False
    if content == "KEY":
        return False
    return True

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