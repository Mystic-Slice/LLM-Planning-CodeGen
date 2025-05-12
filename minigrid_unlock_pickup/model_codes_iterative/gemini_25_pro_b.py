import collections
import copy
import math # For complex number rounding checks

# --- Constants ---
WALL = "WALL"
DOOR = "DOOR"
KEY = "KEY"
BOX = "BOX"
AGENT = "AGENT"
EMPTY = ""

# Directions (using complex numbers for easy rotation/movement)
# (row, col) corresponds to (-imag, real)
# Complex numbers for directions: UP=-1j, DOWN=1j, LEFT=-1, RIGHT=1
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

# --- Helper Functions ---

def find_object_location(grid, object_type):
    """Searches grid, returns (row, col) of objectType, or None."""
    for r, row_list in enumerate(grid):
        for c, cell in enumerate(row_list):
            if cell == object_type:
                return r, c
    return None

def get_pos_in_front(pos, direction_complex):
    """Calculates position (r, c) in front using complex numbers."""
    # Ensure direction_complex is a complex number representation
    # Convert position to complex: complex_pos = col + row * 1j
    r, c = pos
    current_complex_pos = c + r * 1j
    # Add direction complex number: move corresponds to adding direction vector
    new_complex_pos = current_complex_pos + direction_complex
    # Convert back to (row, col): r = -imag, c = real
    return int(round(new_complex_pos.imag)), int(round(new_complex_pos.real))

def turn(direction_complex, turn_action):
    """Calculates new direction (complex) after turning LEFT or RIGHT."""
    if turn_action == A_LEFT:
        new_complex = direction_complex * (-1j) # Rotate 90 degrees counter-clockwise
    elif turn_action == A_RIGHT:
        new_complex = direction_complex * (1j)  # Rotate 90 degrees clockwise
    else:
        return direction_complex # Should not happen

    # Normalize due to potential floating point inaccuracies
    real_part = round(new_complex.real)
    imag_part = round(new_complex.imag)

    if abs(real_part) > abs(imag_part): # Primarily horizontal
        return complex(real_part, 0)
    else: # Primarily vertical
        return complex(0, imag_part)


def is_valid_for_move(grid, r, c):
    """Checks if agent can MOVE into cell (r, c)."""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    if not (0 <= r < height and 0 <= c < width):
        return False # Out of bounds
    cell_content = grid[r][c]
    # Can only move into empty cells (or previously unlocked doors now marked empty)
    return cell_content == EMPTY

# Function is_adjacent is no longer needed for primary pathfinding goal
# def is_adjacent(pos1, pos2):
#     """Checks if two (row, col) positions are adjacent (not diagonally)."""
#     r1, c1 = pos1
#     r2, c2 = pos2
#     return abs(r1 - r2) + abs(c1 - c2) == 1

def find_path_to_interact(grid, start_pos, start_direction_complex, target_pos):
    """
    MODIFIED: Finds shortest path actions (MOVE, LEFT, RIGHT) to reach a cell
    _adjacent_ to target_pos AND _facing_ target_pos.
    Uses BFS on state (row, col, direction_complex).
    Returns (list_of_actions, final_state) or (None, None) if no path.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    start_state_tuple = (start_pos[0], start_pos[1], start_direction_complex)
    queue = collections.deque([(start_state_tuple, [])]) # ( (r, c, dir_complex), path_list )
    visited = {start_state_tuple}

    # Determine valid goal states: (adjacent_row, adjacent_col, facing_direction_complex)
    goal_states = set()
    tr, tc = target_pos
    # Check potential adjacent cells and required facing direction
    potential_goals = [
        ((tr - 1, tc), DIRECTIONS["DOWN"]),  # From above, need to face DOWN
        ((tr + 1, tc), DIRECTIONS["UP"]),    # From below, need to face UP
        ((tr, tc - 1), DIRECTIONS["RIGHT"]), # From left, need to face RIGHT
        ((tr, tc + 1), DIRECTIONS["LEFT"]),  # From right, need to face LEFT
    ]

    for (adj_r, adj_c), required_dir_complex in potential_goals:
        # Check if the adjacent cell (ar, ac) is a valid position for the agent to be IN
        if 0 <= adj_r < height and 0 <= adj_c < width and grid[adj_r][adj_c] == EMPTY:
            # The goal state is being at (adj_r, adj_c) facing the required direction
            goal_states.add((adj_r, adj_c, required_dir_complex))

    if not goal_states:
        # This can happen if the target is completely surrounded by walls
        # or non-empty cells the agent can't occupy.
        # print(f"ERROR: No valid interaction locations found for target {target_pos}")
        return None, None

    # print(f"Debug: Starting BFS from {start_pos} facing {DIR_NAMES[start_direction_complex]} to interact with {target_pos}")
    # print(f"Debug: Goal states = {[(gs[0], gs[1], DIR_NAMES[gs[2]]) for gs in goal_states]}")


    while queue:
        (r, c, direction_complex), path = queue.popleft()
        current_state_tuple = (r, c, direction_complex)

        # *** MODIFIED GOAL CHECK ***
        if current_state_tuple in goal_states:
            # Found a path ending in a valid position and orientation for interaction
            # print(f"Debug: Reached goal state {current_state_tuple} via path {path}")
            final_agent_state = AgentState(r, c, direction_complex, None) # Holding state not tracked here
            return path, final_agent_state

        # Explore actions: LEFT, RIGHT, MOVE
        for action in [A_LEFT, A_RIGHT, A_MOVE]:
            new_r, new_c, new_direction_complex = r, c, direction_complex
            next_path = path + [action]

            if action == A_LEFT or action == A_RIGHT:
                new_direction_complex = turn(direction_complex, action)
            elif action == A_MOVE:
                front_r, front_c = get_pos_in_front((r, c), direction_complex)
                # Check if the move is valid (within bounds and into an EMPTY cell)
                if is_valid_for_move(grid, front_r, front_c):
                    new_r, new_c = front_r, front_c
                else:
                    continue # Cannot move forward in this direction

            new_state_tuple = (new_r, new_c, new_direction_complex)
            if new_state_tuple not in visited:
                visited.add(new_state_tuple)
                queue.append((new_state_tuple, next_path))

    # print(f"Debug: No path found from {start_pos} to interact with {target_pos}")
    return None, None # No path found

def orient_towards(current_pos, current_direction_complex, target_pos):
    """
    Calculates shortest LEFT/RIGHT turns to face target_pos from current_pos.
    Returns (list_of_turn_actions, final_direction_complex).
    This is now only needed for the DROP action.
    """
    r, c = current_pos
    tr, tc = target_pos
    dr, dc = tr - r, tc - c

    # Check if target is adjacent
    if abs(dr) + abs(dc) != 1:
        # Target not adjacent, cannot orient directly
        # print(f"Warning: orient_towards called with non-adjacent target {target_pos} from {current_pos}")
        return [], current_direction_complex

    # Determine target direction complex number based on relative position
    target_direction_complex = None
    if dc == 1: target_direction_complex = DIRECTIONS["RIGHT"]
    elif dc == -1: target_direction_complex = DIRECTIONS["LEFT"]
    elif dr == 1: target_direction_complex = DIRECTIONS["DOWN"]
    elif dr == -1: target_direction_complex = DIRECTIONS["UP"]

    # If already facing or target invalid, no actions needed
    if target_direction_complex is None or current_direction_complex == target_direction_complex:
        return [], current_direction_complex

    actions = []
    temp_direction = current_direction_complex
    # Try turning left sequence vs right sequence
    left1 = turn(temp_direction, A_LEFT)
    right1 = turn(temp_direction, A_RIGHT)

    if left1 == target_direction_complex:
        actions = [A_LEFT]
        final_direction = left1
    elif right1 == target_direction_complex:
        actions = [A_RIGHT]
        final_direction = right1
    else:
        # Must be 180 degrees turn (needs two turns)
        # We can use either L, L or R, R. Picking one arbitrarily.
        actions = [A_RIGHT, A_RIGHT] # Or [A_LEFT, A_LEFT]
        final_direction = turn(right1, A_RIGHT)
        # Sanity check: assert final_direction == target_direction_complex

    return actions, final_direction

def find_empty_adjacent_cell(grid, pos, occupied_target_pos=None):
    """
    Finds an empty adjacent cell to pos (r, c).
    Avoids occupied_target_pos (like the box location) even if the grid says empty,
    as we plan to drop there *before* picking up the target.
    """
    r, c = pos
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    # Check neighbors: Right, Left, Down, Up relative to current pos
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < height and 0 <= nc < width:
            # Check if the adjacent potential drop cell is actually empty in the grid
            if grid[nr][nc] == EMPTY:
                 # Crucially, ensure we don't try to drop INTO the cell
                 # that originally contained the object we *intend* to pick up next (the box).
                 if occupied_target_pos and (nr, nc) == occupied_target_pos:
                     continue # Skip this cell, it's where the box is/was.
                 # If it's empty and not the final target's location, it's usable
                 return (nr, nc)
    return None # No suitable empty adjacent cell found

# --- Main Algorithm ---
def solve(grid, start_direction_str):
    """
    Solves the grid navigation task using the modified pathfinding.
    Returns a list of actions.
    """
    grid_copy = copy.deepcopy(grid) # Work on a mutable copy
    height = len(grid_copy)
    if height == 0: return ["ERROR: Empty grid"]
    width = len(grid_copy[0]) if height > 0 else 0
    if width == 0: return ["ERROR: Empty grid row"]

    # 1. Initialize State
    agent_start_loc = find_object_location(grid_copy, AGENT)
    if not agent_start_loc: return ["ERROR: Agent not found"]
    key_location = find_object_location(grid_copy, KEY)
    if not key_location: return ["ERROR: Key not found"]
    door_location = find_object_location(grid_copy, DOOR)
    if not door_location: return ["ERROR: Door not found"]
    box_location_initial = find_object_location(grid_copy, BOX) # Store original box loc
    if not box_location_initial: return ["ERROR: Box not found"]

    start_direction_complex = DIRECTIONS[start_direction_str]
    agent_pos = agent_start_loc
    agent_direction = start_direction_complex
    agent_holding = None
    grid_copy[agent_pos[0]][agent_pos[1]] = EMPTY # Agent leaves starting cell

    action_list = []

    # --- Helper to update state and list ---
    def perform_actions(actions_to_perform):
        nonlocal agent_pos, agent_direction, agent_holding, grid_copy, action_list
        if not actions_to_perform: return

        action_list.extend(actions_to_perform)
        # Simulate state changes (simplified, relies on pathfinding correctness)
        for action in actions_to_perform:
            if action == A_LEFT or action == A_RIGHT:
                agent_direction = turn(agent_direction, action)
            elif action == A_MOVE:
                front_r, front_c = get_pos_in_front(agent_pos, agent_direction)
                # Pathfinding should guarantee validity, but double-check
                if is_valid_for_move(grid_copy, front_r, front_c):
                     agent_pos = (front_r, front_c)
                else:
                     # This indicates a problem in pathfinding or state if it occurs
                    #  print(f"ERROR: Tried to perform invalid MOVE action during simulation.")
                     # We might want to raise an exception or handle this error better
                     return # Stop simulation on error
            # PICKUP/DROP/UNLOCK simulation happens in main logic where grid/holding updated

    # --- Main Logic ---

    # 2. Pathfind to and Pickup the Key
    # print(f"Phase 1: Get Key at {key_location}")
    path_actions, final_state = find_path_to_interact(grid_copy, agent_pos, agent_direction, key_location)
    if path_actions is None: return ["ERROR: Path to Key not found"]
    perform_actions(path_actions)
    # Update state from the final state returned by pathfinder
    agent_pos = (final_state.row, final_state.col)
    agent_direction = final_state.direction
    # No orientation needed, find_path_to_interact guarantees we face the key
    perform_actions([A_PICKUP])
    agent_holding = KEY
    grid_copy[key_location[0]][key_location[1]] = EMPTY # Key removed from grid
    # print(f"  Key picked up. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")

    # 3. Pathfind to and Unlock the Door
    # print(f"Phase 2: Unlock Door at {door_location}")
    path_actions, final_state = find_path_to_interact(grid_copy, agent_pos, agent_direction, door_location)
    if path_actions is None: return ["ERROR: Path to Door not found"]
    perform_actions(path_actions)
    agent_pos = (final_state.row, final_state.col)
    agent_direction = final_state.direction
    # No orientation needed, find_path_to_interact guarantees we face the door
    perform_actions([A_UNLOCK])
    # Update grid: Door is now open (treat as empty for future pathfinding)
    grid_copy[door_location[0]][door_location[1]] = EMPTY
    # print(f"  Door unlocked. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")

    # 4. Pathfind to the Box location
    # print(f"Phase 3: Go to Box at {box_location_initial}")
    path_actions, final_state = find_path_to_interact(grid_copy, agent_pos, agent_direction, box_location_initial)
    if path_actions is None: return ["ERROR: Path to Box not found"]
    perform_actions(path_actions)
    agent_pos = (final_state.row, final_state.col)
    agent_direction = final_state.direction
    # Agent is now adjacent to the box location and facing it.
    # print(f"  Reached adjacent to Box. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")

    # 5. Drop the Key before picking up the Box
    # print(f"Phase 4: Drop Key")
    # Find an empty spot adjacent to the *current* agent position
    # Pass box_location_initial to prevent choosing that cell for dropping
    drop_loc = find_empty_adjacent_cell(grid_copy, agent_pos, box_location_initial)
    if drop_loc is None:
        # This might happen in very constrained spaces.
        return ["ERROR: Cannot find empty cell to drop key near box!"]

    # Orient towards the drop location
    orient_actions, final_dir = orient_towards(agent_pos, agent_direction, drop_loc)
    perform_actions(orient_actions)
    agent_direction = final_dir # Update direction after orienting

    # Perform the drop
    perform_actions([A_DROP])
    grid_copy[drop_loc[0]][drop_loc[1]] = KEY # Place key on grid in the chosen empty cell
    agent_holding = None
    # print(f"  Key dropped at {drop_loc}. State: {agent_pos}, Dir: {DIR_NAMES[agent_direction]}, Holding: {agent_holding}")

    # 6. Pickup the Box
    # print(f"Phase 5: Pickup Box")
    # Agent is still at the same position, but now facing the drop location.
    # Need to orient back towards the box location.
    orient_actions, final_dir = orient_towards(agent_pos, agent_direction, box_location_initial)
    perform_actions(orient_actions)
    agent_direction = final_dir # Update direction after orienting

    # Perform the pickup (agent should now be facing the box)
    perform_actions([A_PICKUP])
    agent_holding = BOX
    grid_copy[box_location_initial[0]][box_location_initial[1]] = EMPTY # Box removed from grid
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