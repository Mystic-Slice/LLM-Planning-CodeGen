import collections
from typing import List, Tuple, Optional, Dict, Set

# Constants for directions and actions
UP = "UP"
DOWN = "DOWN"
LEFT = "LEFT"
RIGHT = "RIGHT"
MOVE = "MOVE"
PICKUP = "PICKUP"
DROP = "DROP"  # Included for completeness, but not needed for this specific problem
UNLOCK = "UNLOCK"

# Type Aliases for clarity
Grid = List[List[str]]
Position = Tuple[int, int]
Direction = str
State = Tuple[int, int, Direction] # (x, y, direction)
Path = List[str]

# --- Helper Function Definitions --- (Moved outside solve for clarity)

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

def is_cell_walkable(x: int, y: int, height: int, width: int, grid: Grid, current_door_unlocked: bool) -> bool:
    """ Checks if a cell is valid to move into. """
    # Check boundaries
    if not (0 <= y < height and 0 <= x < width):
        return False
    cell_content = grid[y][x]
    if cell_content == "WALL":
        return False
    if cell_content == "KEY":  # Cannot walk onto Key cell
        return False
    if cell_content == "DOOR":
        return current_door_unlocked # Can only pass if door is unlocked
    # "" (empty), "GOAL", "AGENT" (initial pos is technically empty after agent moves) are walkable.
    return True

# *** MODIFIED FUNCTION ***
def find_adjacent_cell_facing_target(
    target_x: int, target_y: int,
    height: int, width: int, # Grid dimensions
    initial_grid: Grid, # Use original grid for reference
    key_original_pos: Position, # Need the original key loc
    is_finding_spot_for_door: bool # Flag to know if key is gone
) -> Optional[Position]:
    """
    Finds a valid cell adjacent to the target to stand on, facing the target.
    It considers that the key's original position becomes available after pickup.
    """
    potential_adj_spots = [
        (target_x, target_y - 1), # Below, facing UP
        (target_x, target_y + 1), # Above, facing DOWN
        (target_x - 1, target_y), # Right, facing LEFT
        (target_x + 1, target_y)  # Left, facing RIGHT
    ]
    valid_spots = []

    for spot_x, spot_y in potential_adj_spots:
        # Check bounds
        if not (0 <= spot_y < height and 0 <= spot_x < width):
            continue

        # Is this the spot where the key originally was?
        is_original_key_spot = (spot_x == key_original_pos[0] and spot_y == key_original_pos[1])

        # If we are finding the spot for the door, the original key spot is now valid to stand on.
        if is_finding_spot_for_door and is_original_key_spot:
            # Check if the key spot itself wasn't blocked by a wall etc. (though shouldn't happen for key)
            if initial_grid[spot_y][spot_x] != "WALL" and initial_grid[spot_y][spot_x] != "DOOR":
                 valid_spots.append((spot_x, spot_y))
            continue # Check next potential spot

        cell_content = initial_grid[spot_y][spot_x]

        # Cannot stand on WALL or DOOR regardless (unless it's the key spot handled above)
        if cell_content == "WALL" or cell_content == "DOOR":
            continue

        # Cannot stand on the KEY spot if we are going for the key
        # (This check is technically redundant if cell_content == "KEY")
        if cell_content == "KEY":
            continue

        # Otherwise, the cell is valid initiale state ("", "AGENT", "GOAL")
        valid_spots.append((spot_x, spot_y))


    # Prefer spots closest to the target first? BFS pathfinding handles optimality,
    # so just returning the first valid one found is fine.
    if valid_spots:
         # Simple heuristic: maybe prefer the spot that requires fewer turns from common approach angles?
         # Or just return the first one, BFS will find the shortest path TO it.
        return valid_spots[0]

    return None # No suitable adjacent spot found


def find_path(start_x: int, start_y: int, start_dir: Direction,
              target_x: int, target_y: int,
              facing_target_x: int, facing_target_y: int, # Use -1, -1 if just reaching the cell
              height: int, width: int, grid: Grid, # Pass grid info
              current_door_unlocked: bool
              ) -> Optional[Tuple[Path, int, int, Direction]]:
    """
    Performs Breadth-First Search to find the shortest action path.
    Args:
        start_x, start_y, start_dir: Starting state.
        target_x, target_y: Target coordinates to stand on.
        facing_target_x, facing_target_y: Coordinates the agent must be facing upon arrival at target_x, target_y.
                                          Set to -1, -1 if only reaching the cell matters.
        height, width, grid: Grid details.
        current_door_unlocked: Whether the door is currently unlocked.
    Returns:
        A tuple containing (path, final_x, final_y, final_dir) if found, else None.
    """
    queue = collections.deque([(start_x, start_y, start_dir, [])]) # (x, y, dir, path_so_far)
    visited: Set[State] = set([(start_x, start_y, start_dir)]) # State: (x, y, dir)

    while queue:
        curr_x, curr_y, curr_dir, current_path = queue.popleft()

        # --- Goal Check ---
        is_goal = False
        if facing_target_x != -1: # Target requires specific facing direction (PICKUP/UNLOCK)
            fx, fy = calculate_front_cell(curr_x, curr_y, curr_dir)
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
        # Use the helper function with all necessary arguments
        if is_cell_walkable(front_x, front_y, height, width, grid, current_door_unlocked):
            next_state_move: State = (front_x, front_y, curr_dir)
            if next_state_move not in visited:
                visited.add(next_state_move)
                new_path_move = current_path + [MOVE]
                queue.append((front_x, front_y, curr_dir, new_path_move))

    return None # Path not found

# --- Main Solve Function ---
def solve(grid: Grid, start_direction: Direction) -> Path:
    """
    Finds the sequence of actions to pick up the key, unlock the door,
    and reach the goal in the grid environment.
    Args:
        grid: The 2D list representing the game environment.
        start_direction: The initial direction the agent is facing.
    Returns:
        A list of action strings, or raises an error if no solution found.
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
        is_finding_spot_for_door=False # We are finding spot for KEY
    )
    if key_adj_target is None:
        raise RuntimeError(f"Cannot find valid adjacent spot to stand for picking up KEY at {key_pos}.")

    path_result_key = find_path(
        current_x, current_y, current_dir,
        key_adj_target[0], key_adj_target[1],
        key_pos[0], key_pos[1], # Must face the key
        height, width, grid, # Pass grid info
        door_unlocked # Door is initially locked
    )

    if path_result_key is None:
        raise RuntimeError(f"Cannot find path to the KEY adjacent spot {key_adj_target}.")
    path_to_key, current_x, current_y, current_dir = path_result_key
    overall_action_list.extend(path_to_key)
    overall_action_list.append(PICKUP)
    has_key = True
    # grid[key_pos[1]][key_pos[0]] = "" # Key is gone - grid is read-only, state tracked by has_key for pathfinding

    # --- 3. Phase 2: Navigate to and unlock the Door ---
     # Find adjacent spot for DOOR unlock, considering KEY spot is now empty
    door_adj_target = find_adjacent_cell_facing_target(
        door_pos[0], door_pos[1],
        height, width, grid,
        key_original_pos=key_pos, # Pass key pos for context
        is_finding_spot_for_door=True # We are finding spot for DOOR
    )
    if door_adj_target is None:
         raise RuntimeError(f"Cannot find valid adjacent spot to stand for unlocking DOOR at {door_pos} (considering key at {key_pos} is gone).")

    path_result_door = find_path(
        current_x, current_y, current_dir,
        door_adj_target[0], door_adj_target[1],
        door_pos[0], door_pos[1], # Must face the door
        height, width, grid, # Pass grid info
        door_unlocked # Door is still locked before UNLOCK action
    )

    if path_result_door is None:
        raise RuntimeError(f"Cannot find path to the DOOR adjacent spot {door_adj_target} after getting key.")
    path_to_door, current_x, current_y, current_dir = path_result_door
    overall_action_list.extend(path_to_door)
    overall_action_list.append(UNLOCK)
    door_unlocked = True # State change: door is now unlocked

    # --- 4. Phase 3: Navigate to the Goal ---
    # Target is the goal cell itself, no specific facing direction needed upon arrival
    path_result_goal = find_path(
        current_x, current_y, current_dir,
        goal_pos[0], goal_pos[1],
        -1, -1, # -1 indicates no facing requirement
        height, width, grid, # Pass grid info
        door_unlocked # Door is now unlocked
    )
    if path_result_goal is None:
        raise RuntimeError("Cannot find path to the GOAL after unlocking door.")
    path_to_goal, final_x, final_y, final_dir = path_result_goal # Final state stored but not needed after this
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