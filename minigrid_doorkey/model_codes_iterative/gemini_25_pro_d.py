import collections
from typing import List, Tuple, Optional, Dict, Set

# Constants for directions and actions
UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
MOVE = "MOVE"
PICKUP = "PICKUP"
DROP = "DROP" # Not used in this specific problem, but part of potential actions
UNLOCK = "UNLOCK"

# Type Aliases for clarity
Grid = List[List[str]]
Position = Tuple[int, int] # (x, y) coordinate system
Direction = str
State = Tuple[int, int, Direction] # State representation for BFS: (x, y, direction)
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
    """ Calculates the coordinates of the cell directly in front (x, y). """
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
                     current_has_key: bool,       # Added: Know if agent holds key
                     original_key_pos: Position   # Added: Know where key was originally
                    ) -> bool:
    """
    Checks if a cell (x, y) is valid to move into, considering grid boundaries,
    walls, locked doors, and whether the key has been picked up.

    Args:
        x: Target cell x-coordinate.
        y: Target cell y-coordinate.
        height: Grid height.
        width: Grid width.
        grid: The static initial grid layout.
        current_door_unlocked: Boolean indicating if the door is currently unlocked.
        current_has_key: Boolean indicating if the agent currently holds the key.
        original_key_pos: The (x, y) coordinates of the key's starting position.

    Returns:
        True if the cell is walkable in the current state, False otherwise.
    """
    # 1. Check boundaries
    if not (0 <= y < height and 0 <= x < width):
        return False

    # 2. Check if it's the key location *AFTER* key is picked up
    # This is the crucial fix: Allow movement onto the key's spot if we have the key.
    if current_has_key and (x, y) == original_key_pos:
         return True # Key spot is now empty and walkable after pickup

    # 3. Check content based on the original grid state (for Walls, Doors, initial Key)
    cell_content = grid[y][x]

    if cell_content == "WALL":
        return False

    # 4. Cannot walk onto Key location *BEFORE* pickup
    # (The case AFTER pickup is handled in step 2)
    if cell_content == "KEY":
        # Implicitly, if we reach here and cell_content is KEY, current_has_key must be False
        return False

    if cell_content == "DOOR":
        # Can only pass through door if it's unlocked
        return current_door_unlocked

    # 5. "" (empty), "GOAL", "AGENT" (initial pos) are walkable by default.
    return True

# *** MODIFIED find_adjacent_cell_facing_target FUNCTION ***
def find_adjacent_cell_facing_target(
    target_x: int, target_y: int,
    height: int, width: int,
    initial_grid: Grid,           # Use initial grid for obstacles like walls
    key_original_pos: Position,   # Need to know where the key was
    is_finding_spot_for_door: bool # True if finding spot for door, False for key
) -> Optional[Tuple[Position, Direction]]:
    """
    Finds a valid, reachable cell adjacent to the target (x, y) from which
    the agent can perform an interaction (PICKUP/UNLOCK).

    Returns the required standing position (x, y) and the direction the agent
    must face from that position. Considers that the key's original position
    becomes available ONLY AFTER the key is picked up (i.e., when finding
    a spot for the door).

    Args:
        target_x: x-coordinate of the target object (Key or Door).
        target_y: y-coordinate of the target object.
        height: Grid height.
        width: Grid width.
        initial_grid: The static initial grid layout.
        key_original_pos: The (x, y) coordinates of the key's starting position.
        is_finding_spot_for_door: True if searching for a spot to unlock the door,
                                 False if searching for a spot to pick up the key.

    Returns:
        A tuple ((stand_x, stand_y), facing_direction) if a valid spot is found,
        otherwise None.
    """
    potential_adj_spots = [
        # (stand_x, stand_y, required_facing_direction)
        (target_x, target_y + 1, UP),    # Stand below target, face UP
        (target_x, target_y - 1, DOWN),  # Stand above target, face DOWN
        (target_x + 1, target_y, LEFT),  # Stand right of target, face LEFT
        (target_x - 1, target_y, RIGHT) # Stand left of target, face RIGHT
    ]

    valid_spots = []

    for spot_x, spot_y, facing_dir in potential_adj_spots:
        # 1. Check bounds for the *standing* spot
        if not (0 <= spot_y < height and 0 <= spot_x < width):
            continue

        # 2. Check if the potential standing spot *is* the key's original location
        is_key_spot = (spot_x, spot_y) == key_original_pos

        if is_key_spot:
            # Can only stand on key spot IF we are finding the spot FOR THE DOOR
            # (meaning key is already picked up and the spot is conceptually empty)
            if is_finding_spot_for_door:
                valid_spots.append(((spot_x, spot_y), facing_dir))
                # Continue checking other spots, maybe they are reachable faster
            else:
                # Cannot stand on the key spot to pick up the key itself
                continue # Skip this spot

        else:
            # 3. If not the key spot, check for other obstacles (Wall, Door)
            # based on the *initial* grid state at the standing spot.
            # Agent cannot stand on a Wall or a (potentially locked) Door.
            cell_content = initial_grid[spot_y][spot_x]
            if cell_content == "WALL" or cell_content == "DOOR":
                # NOTE: Agent can stand on Goal or their own starting position.
                continue # Cannot stand on Wall or Door

            # 4. If not the key spot and not Wall/Door, it's a valid spot
            # (empty, goal, or agent's initial position).
            valid_spots.append(((spot_x, spot_y), facing_dir))

    # If multiple valid spots exist, BFS will implicitly find the path to the
    # one reachable with the fewest actions from the agent's current state.
    # We return the first one found in our check order (e.g., prioritize UP/DOWN facing).
    # This doesn't guarantee optimality of *which adjacent spot* is chosen if multiple
    # are valid, but BFS guarantees the path *to* the chosen spot is optimal.
    # For this problem, any valid adjacent spot should lead to a solution.
    if valid_spots:
        return valid_spots[0]

    return None # No suitable adjacent spot found

# *** MODIFIED find_path FUNCTION ***
def find_path(start_x: int, start_y: int, start_dir: Direction,
              target_x: int, target_y: int, # Target coordinates to stand _on_
              target_facing_dir: Optional[Direction], # Direction agent must face (-1 or None if N/A)
              height: int, width: int, grid: Grid, # Static grid info
              current_door_unlocked: bool, # Dynamic state
              current_has_key: bool,       # Dynamic state (NEW)
              original_key_pos: Position   # Static info (NEW)
              ) -> Optional[Tuple[Path, int, int, Direction]]:
    """
    Performs Breadth-First Search to find the shortest action path (LEFT, RIGHT, MOVE)
    to reach a target cell (target_x, target_y) potentially facing a specific direction.
    Considers current game state (key possession, door status) for walkability.

    Args:
        start_x, start_y, start_dir: Agent's starting state for this path segment.
        target_x, target_y: The coordinates of the cell the agent needs to *be on*.
        target_facing_dir: The direction the agent must be facing upon reaching the target cell.
                           If None, direction doesn't matter (e.g., reaching GOAL).
        height, width, grid: Grid dimensions and static layout.
        current_door_unlocked: Whether the door is currently unlocked.
        current_has_key: Whether the agent currently has the key.
        original_key_pos: The initial coordinates of the key.

    Returns:
        A tuple (Path, final_x, final_y, final_dir) if a path is found,
        otherwise None.
    """
    queue = collections.deque([(start_x, start_y, start_dir, [])]) # (x, y, dir, path_so_far)
    visited: Set[State] = set([(start_x, start_y, start_dir)]) # State: (x, y, dir)

    while queue:
        curr_x, curr_y, curr_dir, current_path = queue.popleft()

        # --- Goal Check ---
        is_goal = False
        if curr_x == target_x and curr_y == target_y:
            if target_facing_dir is None or curr_dir == target_facing_dir:
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

        # Use the MODIFIED helper function with all necessary state arguments
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

# --- Main Solve Function (Updated Calls to find_path/find_adjacent) ---
def solve(grid: Grid, start_direction: Direction) -> Path:
    """
    Finds the sequence of actions to pick up the key, unlock the door,
    and reach the goal in the grid environment. Incorporates logic to handle
    moving over/standing on the key's original location after pickup.
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
            pos = (c, r) # Use (x, y) convention
            if cell == "AGENT":
                start_pos = pos
            elif cell == "KEY":
                key_pos = pos
            elif cell == "DOOR":
                door_pos = pos
            elif cell == "GOAL":
                goal_pos = pos

    if not all([start_pos, key_pos, door_pos, goal_pos]):
        raise ValueError("Required objects (AGENT, KEY, DOOR, GOAL) not found in grid.")

    # --- Initial State ---
    current_x, current_y = start_pos
    current_dir = start_direction
    has_key = False
    door_unlocked = False
    overall_action_list: Path = []
    # Store key's original position separately as it's needed even after pickup
    original_key_pos = key_pos

    # print(f"Start: {start_pos} facing {start_direction}")
    # print(f"Key: {key_pos}")
    # print(f"Door: {door_pos}")
    # print(f"Goal: {goal_pos}")

    # --- 2. Phase 1: Navigate to and pick up the Key ---
    # print("\n--- Phase 1: Path to Key ---")
    # Find adjacent spot & required facing direction for KEY pickup
    key_pickup_target = find_adjacent_cell_facing_target(
        key_pos[0], key_pos[1],
        height, width, grid,
        key_original_pos=original_key_pos, # Pass key pos for context
        is_finding_spot_for_door=False      # CRITICAL: False, we are finding spot for KEY pickup
    )
    if key_pickup_target is None:
        raise RuntimeError(f"Cannot find valid adjacent spot to stand for picking up KEY at {key_pos}.")

    key_adj_pos, key_facing_dir = key_pickup_target
    # print(f"Target spot for key pickup: Stand at {key_adj_pos}, face {key_facing_dir}")

    # Pathfind to the spot needed to pick up the key
    path_result_key = find_path(
        current_x, current_y, current_dir,
        key_adj_pos[0], key_adj_pos[1],    # Stand on this spot
        key_facing_dir,                   # Must face the key direction
        height, width, grid,
        current_door_unlocked=door_unlocked, # Door is initially locked
        current_has_key=has_key,             # Key is not yet held (NEW)
        original_key_pos=original_key_pos    # Location of key (NEW)
    )

    if path_result_key is None:
        raise RuntimeError(f"Cannot find path from {current_x, current_y, current_dir} to the KEY adjacent spot {key_adj_pos} facing {key_facing_dir}.")

    path_to_key, current_x, current_y, current_dir = path_result_key
    overall_action_list.extend(path_to_key)
    overall_action_list.append(PICKUP)
    has_key = True # State change: Agent now has the key
    # print(f"Reached key pickup spot: Pos=({current_x},{current_y}), Dir={current_dir}")
    # print(f"Actions for Key: {path_to_key + [PICKUP]}")

    # --- 3. Phase 2: Navigate to and unlock the Door ---
    # print("\n--- Phase 2: Path to Door ---")
    # Find adjacent spot & required facing direction for DOOR unlock
    # Now, the key's original spot *is* potentially usable
    door_unlock_target = find_adjacent_cell_facing_target(
        door_pos[0], door_pos[1],
        height, width, grid,
        key_original_pos=original_key_pos, # Pass key pos for context
        is_finding_spot_for_door=True       # CRITICAL: True, we ARE finding spot for DOOR unlock
    )
    if door_unlock_target is None:
         raise RuntimeError(f"Cannot find valid adjacent spot to stand for unlocking DOOR at {door_pos} (considering key at {original_key_pos} is gone).")

    door_adj_pos, door_facing_dir = door_unlock_target
    # print(f"Target spot for door unlock: Stand at {door_adj_pos}, face {door_facing_dir}")


    # Pathfind to the spot needed to unlock the door
    path_result_door = find_path(
        current_x, current_y, current_dir,
        door_adj_pos[0], door_adj_pos[1],    # Stand on this spot
        door_facing_dir,                    # Must face the door direction
        height, width, grid,
        current_door_unlocked=door_unlocked, # Door is still locked before UNLOCK action
        current_has_key=has_key,             # Agent HAS the key now (NEW)
        original_key_pos=original_key_pos    # Location of key (NEW)
    )

    if path_result_door is None:
        # Debugging info
        # print(f"Failed pathfinding to door unlock spot.")
        # print(f"  Current State: Pos=({current_x},{current_y}), Dir={current_dir}, HasKey={has_key}, DoorUnlocked={door_unlocked}")
        # print(f"  Target State: Pos={door_adj_pos}, Facing={door_facing_dir}")
        # print(f"  Original Key Pos: {original_key_pos}")
        raise RuntimeError(f"Cannot find path from key pickup location ({current_x},{current_y}) facing {current_dir} to the DOOR adjacent spot {door_adj_pos} facing {door_facing_dir}.")

    path_to_door, current_x, current_y, current_dir = path_result_door
    overall_action_list.extend(path_to_door)
    overall_action_list.append(UNLOCK)
    door_unlocked = True # State change: door is now unlocked
    # print(f"Reached door unlock spot: Pos=({current_x},{current_y}), Dir={current_dir}")
    # print(f"Actions for Door: {path_to_door + [UNLOCK]}")


    # --- 4. Phase 3: Navigate to the Goal ---
    # print("\n--- Phase 3: Path to Goal ---")
    # print(f"Target spot for goal: Stand at {goal_pos}")
    # Target is the goal cell itself, no specific facing direction needed upon arrival
    path_result_goal = find_path(
        current_x, current_y, current_dir,
        goal_pos[0], goal_pos[1],       # Stand ON the goal cell
        None,                           # None indicates no facing requirement
        height, width, grid,
        current_door_unlocked=door_unlocked, # Door IS unlocked now
        current_has_key=has_key,             # Agent still has key (doesn't affect walkability here) (NEW)
        original_key_pos=original_key_pos    # Location of key (NEW)
    )

    if path_result_goal is None:
        # Debugging info
        # print(f"Failed pathfinding to goal.")
        # print(f"  Current State: Pos=({current_x},{current_y}), Dir={current_dir}, HasKey={has_key}, DoorUnlocked={door_unlocked}")
        # print(f"  Target State: Pos={goal_pos}")
        # print(f"  Original Key Pos: {original_key_pos}")
        raise RuntimeError(f"Cannot find path from door unlock location ({current_x},{current_y}) facing {current_dir} to the GOAL {goal_pos}.")

    path_to_goal, final_x, final_y, final_dir = path_result_goal # Final state stored
    overall_action_list.extend(path_to_goal)
    # print(f"Reached goal: Pos=({final_x},{final_y}), Dir={final_dir}")
    # print(f"Actions for Goal: {path_to_goal}")


    # --- 5. Return the final action list ---
    # print(f"\nFinal Action List: {overall_action_list}")
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