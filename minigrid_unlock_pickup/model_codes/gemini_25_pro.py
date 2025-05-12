import collections
import copy

# --- Constants ---
WALL = "WALL"
DOOR = "DOOR"
KEY = "KEY"
BOX = "BOX"
AGENT = "AGENT"
EMPTY = ""

# Directions (using complex numbers for easy rotation/movement)
# (row, col) corresponds to (-imag, real)
DIRECTIONS = {
    "UP": -1j,
    "DOWN": 1j,
    "LEFT": -1,
    "RIGHT": 1,
}
# Map complex direction back to string name
DIR_NAMES = {v: k for k, v in DIRECTIONS.items()}

# Actions
A_LEFT = "LEFT"
A_RIGHT = "RIGHT"
A_MOVE = "MOVE"
A_PICKUP = "PICKUP"
A_DROP = "DROP"
A_UNLOCK = "UNLOCK"

# --- Data Structures ---
AgentState = collections.namedtuple("AgentState", ["row", "col", "direction", "holding"])
# Using complex numbers: pos = col + row * 1j
# direction = complex number (-1j, 1j, -1, 1)

# --- Helper Functions ---

def find_object_location(grid, object_type):
    """Searches grid, returns (row, col) of objectType, or None."""
    for r, row_list in enumerate(grid):
        for c, cell in enumerate(row_list):
            if cell == object_type:
                return r, c
    return None

def get_pos_in_front(pos, direction):
    """Calculates position (r, c) in front."""
    dr, dc = 0, 0
    if direction == DIRECTIONS["UP"]: dr = -1
    elif direction == DIRECTIONS["DOWN"]: dr = 1
    elif direction == DIRECTIONS["LEFT"]: dc = -1
    elif direction == DIRECTIONS["RIGHT"]: dc = 1
    return pos[0] + dr, pos[1] + dc

def turn(direction, turn_action):
    """Calculates new direction after turning LEFT or RIGHT."""
    current_complex = direction
    if turn_action == A_LEFT:
        new_complex = current_complex * (-1j) # Rotate 90 degrees counter-clockwise
    elif turn_action == A_RIGHT:
        new_complex = current_complex * (1j)  # Rotate 90 degrees clockwise
    else:
        # Should not happen if called correctly
        return direction

    # Normalize floating point inaccuracies if any (e.g., turning back)
    if abs(new_complex.real) > abs(new_complex.imag):
        return int(round(new_complex.real)) # Becomes -1 or 1
    else:
        return int(round(new_complex.imag)) * 1j # Becomes -1j or 1j


def is_valid_for_move(grid, r, c):
    """Checks if agent can MOVE into cell (r, c)."""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    if not (0 <= r < height and 0 <= c < width):
        return False # Out of bounds
    cell_content = grid[r][c]
    # Can only move into empty cells (or previously unlocked doors now marked empty)
    return cell_content == EMPTY

def is_adjacent(pos1, pos2):
    """Checks if two (row, col) positions are adjacent (not diagonally)."""
    r1, c1 = pos1
    r2, c2 = pos2
    return abs(r1 - r2) + abs(c1 - c2) == 1

def find_path(grid, start_pos, start_direction, target_pos):
    """
    Finds shortest path actions (MOVE, LEFT, RIGHT) to reach a cell
    *adjacent* to target_pos.
    Uses BFS on state (row, col, direction_complex).
    Returns (list_of_actions, final_state) or (None, None) if no path.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    start_state = (start_pos[0], start_pos[1], start_direction)

    queue = collections.deque([(start_state, [])]) # ( (r, c, dir), path_list )
    visited = {start_state}

    while queue:
        (r, c, direction), path = queue.popleft()
        current_pos = (r, c)

        # Goal condition: adjacent to target
        if is_adjacent(current_pos, target_pos):
            final_agent_state = AgentState(r, c, direction, None) # Holding state not tracked here
            return path, final_agent_state

        # Explore actions: LEFT, RIGHT, MOVE
        for action in [A_LEFT, A_RIGHT, A_MOVE]:
            new_r, new_c, new_direction = r, c, direction
            next_path = path + [action]

            if action == A_LEFT or action == A_RIGHT:
                new_direction = turn(direction, action)
            elif action == A_MOVE:
                front_r, front_c = get_pos_in_front(current_pos, direction)
                if is_valid_for_move(grid, front_r, front_c):
                    new_r, new_c = front_r, front_c
                else:
                    continue # Cannot move forward

            new_state = (new_r, new_c, new_direction)
            if new_state not in visited:
                visited.add(new_state)
                queue.append((new_state, next_path))

    return None, None # No path found

def orient_towards(current_pos, current_direction, target_pos):
    """
    Calculates shortest LEFT/RIGHT turns to face target_pos from current_pos.
    Returns (list_of_turn_actions, final_direction).
    """
    r, c = current_pos
    tr, tc = target_pos
    dr, dc = tr - r, tc - c

    if abs(dr) + abs(dc) != 1:
        # Target not adjacent, cannot orient directly
        return [], current_direction

    target_direction_complex = None
    if dr == -1: target_direction_complex = DIRECTIONS["UP"]
    elif dr == 1: target_direction_complex = DIRECTIONS["DOWN"]
    elif dc == -1: target_direction_complex = DIRECTIONS["LEFT"]
    elif dc == 1: target_direction_complex = DIRECTIONS["RIGHT"]

    if target_direction_complex is None or current_direction == target_direction_complex:
        return [], current_direction # Already facing or invalid target

    actions = []
    temp_direction = current_direction

    # Try turning left twice vs right twice
    left1 = turn(temp_direction, A_LEFT)
    left2 = turn(left1, A_LEFT)
    right1 = turn(temp_direction, A_RIGHT)
    right2 = turn(right1, A_RIGHT)

    if left1 == target_direction_complex:
        actions = [A_LEFT]
        final_direction = left1
    elif right1 == target_direction_complex:
        actions = [A_RIGHT]
        final_direction = right1
    elif left2 == target_direction_complex: # or right2, should be same
        actions = [A_LEFT, A_LEFT] # Could also be [A_RIGHT, A_RIGHT]
        final_direction = left2
    else:
         # Should not happen if target is adjacent
         return [], current_direction

    return actions, final_direction


def find_empty_adjacent_cell(grid, pos):
    """Finds an empty adjacent cell to pos (r, c)."""
    r, c = pos
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Right, Left, Down, Up
        nr, nc = r + dr, c + dc
        if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == EMPTY:
            return (nr, nc)
    return None


# --- Main Algorithm ---

def solve(grid, start_direction_str):
    """
    Solves the grid navigation task.
    Returns a list of actions.
    """
    grid_copy = copy.deepcopy(grid) # Work on a mutable copy
    height = len(grid_copy)
    width = len(grid_copy[0]) if height > 0 else 0

    # 1. Initialize State
    agent_start_loc = find_object_location(grid_copy, AGENT)
    if not agent_start_loc: return ["ERROR: Agent not found"]

    key_location = find_object_location(grid_copy, KEY)
    if not key_location: return ["ERROR: Key not found"]

    door_location = find_object_location(grid_copy, DOOR)
    if not door_location: return ["ERROR: Door not found"]

    box_location = find_object_location(grid_copy, BOX)
    if not box_location: return ["ERROR: Box not found"]

    # Initial agent state using complex numbers for direction
    start_direction_complex = DIRECTIONS[start_direction_str]
    agent_pos = agent_start_loc
    agent_direction = start_direction_complex
    agent_holding = None
    grid_copy[agent_pos[0]][agent_pos[1]] = EMPTY # Agent leaves starting cell

    action_list = []

    # --- Helper to update state and list ---
    def perform_actions(actions):
        nonlocal agent_pos, agent_direction, agent_holding, grid_copy, action_list
        action_list.extend(actions)
        # Simulate the effect of these actions on agent state
        # (This simplified simulation assumes FindPath and OrientTowards return correct sequences)
        for action in actions:
            if action == A_LEFT or action == A_RIGHT:
                agent_direction = turn(agent_direction, action)
            elif action == A_MOVE:
                front_r, front_c = get_pos_in_front(agent_pos, agent_direction)
                if is_valid_for_move(grid_copy, front_r, front_c):
                     agent_pos = (front_r, front_c)
                # No 'else' needed here as pathfinding should guarantee validity

    # --- Main Logic ---

    # 2. Pathfind to and Pickup the Key
    # print(f"Phase 1: Get Key at {key_location}")
    path_actions, final_state = find_path(grid_copy, agent_pos, agent_direction, key_location)
    if path_actions is None: return ["ERROR: Path to Key not found"]
    perform_actions(path_actions)
    agent_pos = (final_state.row, final_state.col) # Update pos based on BFS end state
    agent_direction = final_state.direction # Update direction based on BFS end state

    orient_actions, final_dir = orient_towards(agent_pos, agent_direction, key_location)
    perform_actions(orient_actions)
    agent_direction = final_dir

    perform_actions([A_PICKUP])
    agent_holding = KEY
    grid_copy[key_location[0]][key_location[1]] = EMPTY
    # print(f"  Key picked up. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")


    # 3. Pathfind to and Unlock the Door
    # print(f"Phase 2: Unlock Door at {door_location}")
    # Pathfind again *after* picking up key (grid is potentially different if key was blocking)
    path_actions, final_state = find_path(grid_copy, agent_pos, agent_direction, door_location)
    if path_actions is None: return ["ERROR: Path to Door not found"]
    perform_actions(path_actions)
    agent_pos = (final_state.row, final_state.col)
    agent_direction = final_state.direction

    orient_actions, final_dir = orient_towards(agent_pos, agent_direction, door_location)
    perform_actions(orient_actions)
    agent_direction = final_dir

    perform_actions([A_UNLOCK])
    # Update grid: Door is now open (treat as empty for pathfinding)
    grid_copy[door_location[0]][door_location[1]] = EMPTY
    # print(f"  Door unlocked. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")


    # 4. Pathfind to the Box
    # print(f"Phase 3: Go to Box at {box_location}")
    # Pathfind with the door now open
    path_actions, final_state = find_path(grid_copy, agent_pos, agent_direction, box_location)
    if path_actions is None: return ["ERROR: Path to Box not found"]
    perform_actions(path_actions)
    agent_pos = (final_state.row, final_state.col)
    agent_direction = final_state.direction
    # print(f"  Reached adjacent to Box. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")


    # 5. Drop the Key
    # print(f"Phase 4: Drop Key")
    drop_loc = find_empty_adjacent_cell(grid_copy, agent_pos)
    if drop_loc is None:
        # This might happen if the box is in a 1x1 corridor corner.
        # A more robust solution might need to backtrack slightly to find space.
        # For now, we assume valid configurations allow dropping.
         return ["ERROR: Cannot find empty cell to drop key!"]

    orient_actions, final_dir = orient_towards(agent_pos, agent_direction, drop_loc)
    perform_actions(orient_actions)
    agent_direction = final_dir

    perform_actions([A_DROP])
    grid_copy[drop_loc[0]][drop_loc[1]] = KEY # Place key on grid
    agent_holding = None
    # print(f"  Key dropped at {drop_loc}. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")


    # 6. Pickup the Box
    # print(f"Phase 5: Pickup Box")
    # Agent should still be adjacent to the Box location
    orient_actions, final_dir = orient_towards(agent_pos, agent_direction, box_location)
    perform_actions(orient_actions)
    agent_direction = final_dir

    perform_actions([A_PICKUP])
    agent_holding = BOX
    grid_copy[box_location[0]][box_location[1]] = EMPTY
    # print(f"  Box picked up. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")


    # 7. Return the final sequence of actions
    # print("Objective Complete.")
    return action_list

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