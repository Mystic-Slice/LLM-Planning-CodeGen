import heapq

# Main function
def solve(grid, start_direction):
    # Find positions of key objects
    agent_pos = find_cell(grid, "AGENT")
    key_pos = find_cell(grid, "KEY")
    door_pos = find_cell(grid, "DOOR")
    goal_pos = find_cell(grid, "GOAL")
    actions = []
    current_direction = start_direction
    current_pos = agent_pos
    agent_has_key = False

    # If a key exists and agent does not yet have it, plan to pick it up.
    if key_pos is not None:
        # Compute an approach cell and the desired facing direction so that the KEY lies ahead.
        approach, desired_dir = compute_approach_cell(key_pos, grid, agent_has_key=False)
        # Find a path from current_pos to the approach cell.
        path = a_star_search(current_pos, approach, grid, agent_has_key)
        # Convert the computed path into turning and move actions.
        path_cmds, current_direction = path_to_actions(path, current_direction)
        actions.extend(path_cmds)
        current_pos = approach
        # Adjust current direction so that the KEY is directly in front.
        turn_cmds, current_direction = adjust_heading_for_target(current_direction, desired_dir)
        actions.extend(turn_cmds)
        # Pick up the key.
        actions.append("PICKUP")
        agent_has_key = True
        # Remove the key from the grid so that subsequent path searches treat that cell as open.
        grid[key_pos[0]][key_pos[1]] = ""
    
    # Plan a route to the door.
    approach, desired_dir = compute_approach_cell(door_pos, grid, agent_has_key)
    path = a_star_search(current_pos, approach, grid, agent_has_key)
    path_cmds, current_direction = path_to_actions(path, current_direction)
    actions.extend(path_cmds)
    current_pos = approach
    turn_cmds, current_direction = adjust_heading_for_target(current_direction, desired_dir)
    actions.extend(turn_cmds)
    # Unlock the door.
    actions.append("UNLOCK")
    # Remove the door from the grid after unlocking.
    grid[door_pos[0]][door_pos[1]] = ""
    
    # Finally, plan a route to the goal cell.
    path = a_star_search(current_pos, goal_pos, grid, agent_has_key)
    path_cmds, current_direction = path_to_actions(path, current_direction)
    actions.extend(path_cmds)
    return actions

# Helper: Find the cell that contains the given object.
def find_cell(grid, obj):
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == obj:
                return (row, col)
    return None

# A* search to find a path from start to goal, returning a list of cells.
def a_star_search(start, goal, grid, agent_has_key):
    rows = len(grid)
    cols = len(grid[0])
    # Define movement directions (cardinal): mapping name to (dr, dc)
    directions = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    def heuristic(cell):
        # Simple Manhattan distance
        return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])
    open_set = []
    heapq.heappush(open_set, (heuristic(start), 0, start))
    came_from = {}
    g_score = {start: 0}
    while open_set:
        _, current_cost, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)
        # Explore neighbors (up, down, left, right)
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
    # If no path found, return an empty list.
    return []

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

# Helper: compute an approach cell and desired facing direction for a target (KEY or DOOR).
def compute_approach_cell(target_pos, grid, agent_has_key):
    # For each of the four directions, check if the cell opposite to where the target would be relative
    # to that direction is accessible. That is, if the agent stands on approach_cell and faces 'dir',
    # then the target_pos is directly in front.
    directions = ["UP", "RIGHT", "DOWN", "LEFT"]
    # Mapping direction to offset vector: if agent is facing d, the cell in front is current + delta[d].
    deltas = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    rows = len(grid)
    cols = len(grid[0])
    for d in directions:
        # To have target_pos in front, the agent must be one cell behind the target with respect to direction d.
        dr, dc = deltas[d]
        approach = (target_pos[0] - dr, target_pos[1] - dc)
        if in_bounds(approach, rows, cols) and is_accessible(approach, grid, agent_has_key):
            return approach, d
    # Fallback (should not happen on a valid grid)
    raise Exception("No valid approach cell found for target at " + str(target_pos))

# Convert a path (list of grid cells) to action commands,
# considering the agent's current facing direction.
def path_to_actions(path, current_direction):
    commands = []
    # For each step in the path, determine desired direction and plan turns then a move.
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
    # Rotate until current_direction equals desired_direction.
    while current_direction != desired_direction:
        # Determine minimal turn: here we simply choose to turn left if that gets us closer.
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

# Check if a cell is accessible (the agent can enter it).
# For example, walls and closed doors (if no key) are not accessible.
def is_accessible(cell, grid, agent_has_key):
    rows = len(grid)
    cols = len(grid[0])
    r, c = cell
    if not in_bounds(cell, rows, cols):
        return False
    content = grid[r][c]
    if content == "WALL":
        return False
    # If the cell contains a DOOR and the agent does not have the key,
    # then we consider it blocking.
    if content == "DOOR" and not agent_has_key:
        return False
    # If the cell contains a KEY, we treat it as blocked.
    # (When planning to pick up the key, we deliberately target an adjacent cell,
    # so this does not interfere with our plan.)
    if content == "KEY":
        return False
    # GOAL, empty cells, or the initial AGENT position are accessible.
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