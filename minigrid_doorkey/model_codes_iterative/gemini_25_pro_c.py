import collections
from typing import List, Tuple, Optional, Dict, Set

# Constants for directions and actions
UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
MOVE = "MOVE"
PICKUP = "PICKUP"
DROP = "DROP"
UNLOCK = "UNLOCK"

# Type Aliases for clarity
Grid = List[List[str]]
Position = Tuple[int, int]
Direction = str
State = Tuple[int, int, Direction] # (x, y, direction)
Path = List[str]

# --- Helper Function Definitions ---

def calculate_turn(current_direction: Direction, turn_type: str) -> Direction:
    """ Calculates the new direction after a turn. """
    dirs = [UP, RIGHT, DOWN, LEFT]  # Clockwise order
    current_index = dirs.index(current_direction)
    if turn_type == RIGHT:
        new_index = (current_index + 1) % 4
    elif turn_type == LEFT:
        new_index = (current_index - 1 + 4) % 4
    else:
         raise ValueError(f"Invalid turn type: {turn_type}")
    return dirs[new_index]

def calculate_front_cell(x: int, y: int, direction: Direction) -> Position:
    """ Calculates the coordinates of the cell directly in front. """
    if direction == UP:
        return (x, y - 1)
    if direction == DOWN:
        return (x, y + 1)
    if direction == LEFT:
        return (x - 1, y)
    if direction == RIGHT:
        return (x + 1, y)
    raise ValueError(f"Invalid direction: {direction}") # Should not happen

# *** MODIFIED is_cell_walkable FUNCTION ***
def is_cell_walkable(x: int, y: int, height: int, width: int, grid: Grid,
                     current_door_unlocked: bool,
                     current_has_key: bool, # Added: Know if agent holds key
                     original_key_pos: Position # Added: Know where key was
                    ) -> bool:
    """ Checks if a cell is valid to move into, considering key pickup. """
    # Check boundaries
    if not (0 <= y < height and 0 <= x < width):
        return False

    # Check if it's the key location AFTER key is picked up
    # Crucial for allowing movement onto the key's original spot
    if current_has_key and (x, y) == original_key_pos:
         return True # Key spot is now walkable after pickup

    # Check content based on the original grid state
    cell_content = grid[y][x]
    if cell_content == "WALL":
        return False
    # Cannot walk onto Key location BEFORE pickup (handled by state check above for post-pickup)
    if cell_content == "KEY":
        return False
    if cell_content == "DOOR":
        # Can only pass through door if it's unlocked
        return current_door_unlocked
    # "" (empty), "GOAL", "AGENT" (initial pos) are walkable.
    return True

# *** MODIFIED find_adjacent_cell_facing_target FUNCTION ***
def find_adjacent_cell_facing_target(
    target_x: int, target_y: int,
    height: int, width: int,
    initial_grid: Grid,
    key_original_pos: Position,
    is_finding_spot_for_door: bool # True if finding spot for door unlock, False for key pickup
) -> Optional[Position]:
    """
    Finds a valid cell adjacent to the target to stand on, facing the target.
    Considers that the key's original position becomes available ONLY for unlocking the door.
    """
    potential_adj_spots = [
        (target_x, target_y - 1), # Below target (Agent needs to face UP)
        (target_x, target_y + 1), # Above target (Agent needs to face DOWN)
        (target_x - 1, target_y), # Right of target (Agent needs to face LEFT)
        (target_x + 1, target_y)  # Left of target (Agent needs to face RIGHT)
    ]
    valid_spots = []
    for spot_x, spot_y in potential_adj_spots:
        # 1. Check bounds
        if not (0 <= spot_y < height and 0 <= spot_x < width):
            continue

        # 2. Check if the potential standing spot is the key's original location
        is_key_spot = (spot_x == key_original_pos[0] and spot_y == key_original_pos[1]) # Corrected logical check

        if is_key_spot:
            # Can only stand on key spot if finding the spot FOR THE DOOR (meaning key is already picked up)
            if is_finding_spot_for_door:
                valid_spots.append((spot_x, spot_y))
                # Continue checking other spots, maybe this isn't the optimal one to reach
            else:
                # Cannot stand on the key spot to pick up the key itself
                continue # Skip this spot
        else:
            # 3. If not the key spot, check for other obstacles in the initial grid
            cell_content = initial_grid[spot_y][spot_x]
            if cell_content == "WALL" or cell_content == "DOOR":
                continue # Cannot stand on Wall or Door

            # 4. If not the key spot and not Wall/Door, it's a valid empty/goal/agent spot
            valid_spots.append((spot_x, spot_y))

    # Return the first valid spot found. BFS will find the shortest path *to* this spot.
    # If multiple valid spots exist, BFS from the current position will naturally find
    # the one reachable with the fewest actions.
    if valid_spots:
        return valid_spots[0]
    return None # No suitable adjacent spot found


# *** MODIFIED find_path FUNCTION ***
def find_path(start_x: int, start_y: int, start_dir: Direction,
              target_x: int, target_y: int, # Target coordinates to stand *on*
              facing_target_x: int, facing_target_y: int, # Coords agent must face (-1 if N/A)
              height: int, width: int, grid: Grid, # Static grid info
              current_door_unlocked: bool, # Dynamic state
              current_has_key: bool,       # Dynamic state (NEW)
              original_key_pos: Position   # Static info (NEW)
              ) -> Optional[Tuple[Path, int, int, Direction]]:
    """
    Performs Breadth-First Search to find the shortest action path.
    Now considers if the agent has the key for walkability checks.
    """
    queue = collections.deque([(start_x, start_y, start_dir, [])]) # (x, y, dir, path_so_far)
    visited: Set[State] = set([(start_x, start_y, start_dir)]) # State: (x, y, dir)

    while queue:
        curr_x, curr_y, curr_dir, current_path = queue.popleft()

        # --- Goal Check ---
        is_goal = False
        if facing_target_x != -1: # Target requires specific facing direction (PICKUP/UNLOCK)
            fx, fy = calculate_front_cell(curr_x, curr_y, curr_dir)
            # Must be on the target spot AND facing the correct adjacent cell
            if curr_x == target_x and curr_y == target_y and fx == facing_target_x and fy == facing_target_y:
                is_goal = True
        else: # Target is just reaching the cell (GOAL)
            if curr_x == target_x and curr_y == target_y:
                is_goal = True

        if is_goal:
            return (current_path, curr_x, curr_y, curr_dir)

        # --- Explore Neighbors (Actions) ---
        # 1. Try LEFT turn
        next_dir_l = calculate_turn(curr_dir, LEFT)
        next_state_l: State = (curr_x, curr_y, next_dir_l)
        if next_state_l not in visited:
            visited.add(next_state_l)
            new_path_l = current_path + [LEFT]
            queue.append((curr_x, curr_y, next_dir_l, new_path_l))

        # 2. Try RIGHT turn
        next_dir_r = calculate_turn(curr_dir, RIGHT)
        next_state_r: State = (curr_x, curr_y, next_dir_r)
        if next_state_r not in visited:
            visited.add(next_state_r)
            new_path_r = current_path + [RIGHT]
            queue.append((curr_x, curr_y, next_dir_r, new_path_r))

        # 3. Try MOVE forward
        front_x, front_y = calculate_front_cell(curr_x, curr_y, curr_dir)
        # Use the MODIFIED helper function with all necessary arguments
        if is_cell_walkable(front_x, front_y, height, width, grid,
                            current_door_unlocked,
                            current_has_key, # Pass key status
                            original_key_pos  # Pass key original location
                           ):
            next_state_move: State = (front_x, front_y, curr_dir)
            if next_state_move not in visited:
                visited.add(next_state_move)
                new_path_move = current_path + [MOVE]
                queue.append((front_x, front_y, curr_dir, new_path_move))

    return None # Path not found

# --- Main Solve Function (Updated Calls to find_path) ---
def solve(grid: Grid, start_direction: Direction) -> Path:
    """
    Finds the sequence of actions to pick up the key, unlock the door,
    and reach the goal in the grid environment.
    """
    height = len(grid)
    if height == 0:
        raise ValueError("Grid cannot be empty")
    width = len(grid[0])
    if width == 0:
        raise ValueError("Grid rows cannot be empty")

    # --- 1. Initialization: Find object locations and initial state ---
    start_pos: Optional[Position] = None
    key_pos: Optional[Position] = None
    door_pos: Optional[Position] = None
    goal_pos: Optional[Position] = None
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == "AGENT":
                start_pos = (c, r) # Store as (x, y)
            elif cell == "KEY":
                key_pos = (c, r)
            elif cell == "DOOR":
                door_pos = (c, r)
            elif cell == "GOAL":
                goal_pos = (c, r)

    if not all([start_pos, key_pos, door_pos, goal_pos]):
        raise ValueError("Required objects (AGENT, KEY, DOOR, GOAL) not found in grid.")

    current_x, current_y = start_pos
    current_dir = start_direction
    has_key = False
    door_unlocked = False
    overall_action_list: Path = []

    # --- 2. Phase 1: Navigate to and pick up the Key ---
    # Find adjacent spot for KEY pickup
    key_adj_target = find_adjacent_cell_facing_target(
        key_pos[0], key_pos[1],
        height, width, grid,
        key_original_pos=key_pos, # Pass key pos for context
        is_finding_spot_for_door=False # We are finding spot for KEY pickup
    )
    if key_adj_target is None:
        raise RuntimeError(f"Cannot find valid adjacent spot to stand for picking up KEY at {key_pos}.")

    # Pathfind to the spot needed to pick up the key
    path_result_key = find_path(
        current_x, current_y, current_dir,
        key_adj_target[0], key_adj_target[1], # Stand on this spot
        key_pos[0], key_pos[1], # Must face the key
        height, width, grid,
        current_door_unlocked=door_unlocked, # Door is initially locked
        current_has_key=has_key,             # Key is not yet held (NEW)
        original_key_pos=key_pos             # Location of key (NEW)
    )
    if path_result_key is None:
        raise RuntimeError(f"Cannot find path to the KEY adjacent spot {key_adj_target}.")

    path_to_key, current_x, current_y, current_dir = path_result_key
    overall_action_list.extend(path_to_key)
    overall_action_list.append(PICKUP)
    has_key = True # State change: Agent now has the key

    # --- 3. Phase 2: Navigate to and unlock the Door ---
    # Find adjacent spot for DOOR unlock, considering KEY spot is now potentially empty
    door_adj_target = find_adjacent_cell_facing_target(
        door_pos[0], door_pos[1],
        height, width, grid,
        key_original_pos=key_pos, # Pass key pos for context
        is_finding_spot_for_door=True # We ARE finding spot for DOOR unlock now
    )
    if door_adj_target is None:
         raise RuntimeError(f"Cannot find valid adjacent spot to stand for unlocking DOOR at {door_pos} (considering key at {key_pos} is gone).")

    # Pathfind to the spot needed to unlock the door
    path_result_door = find_path(
        current_x, current_y, current_dir,
        door_adj_target[0], door_adj_target[1], # Stand on this spot
        door_pos[0], door_pos[1],               # Must face the door
        height, width, grid,
        current_door_unlocked=door_unlocked, # Door is still locked before UNLOCK action
        current_has_key=has_key,             # Agent HAS the key now (NEW)
        original_key_pos=key_pos             # Location of key (NEW)
    )
    if path_result_door is None:
        raise RuntimeError(f"Cannot find path from key pickup location {current_x, current_y} to the DOOR adjacent spot {door_adj_target} after getting key.")

    path_to_door, current_x, current_y, current_dir = path_result_door
    overall_action_list.extend(path_to_door)
    overall_action_list.append(UNLOCK)
    door_unlocked = True # State change: door is now unlocked

    # --- 4. Phase 3: Navigate to the Goal ---
    # Target is the goal cell itself, no specific facing direction needed upon arrival
    path_result_goal = find_path(
        current_x, current_y, current_dir,
        goal_pos[0], goal_pos[1],       # Stand ON the goal cell
        -1, -1,                         # -1 indicates no facing requirement
        height, width, grid,
        current_door_unlocked=door_unlocked, # Door IS unlocked now
        current_has_key=has_key,             # Agent still has key (doesn't matter for goal) (NEW)
        original_key_pos=key_pos             # Location of key (NEW)
    )
    if path_result_goal is None:
        raise RuntimeError(f"Cannot find path from door unlock location {current_x, current_y} to the GOAL {goal_pos} after unlocking door.")

    path_to_goal, final_x, final_y, final_dir = path_result_goal # Final state stored but not needed
    overall_action_list.extend(path_to_goal)

    # --- 5. Return the final action list ---
    return overall_action_list

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