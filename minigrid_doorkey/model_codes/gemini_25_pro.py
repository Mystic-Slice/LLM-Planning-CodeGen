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

    # --- Helper Function Definitions (nested or defined outside) ---

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

    def is_cell_walkable(x: int, y: int, current_door_unlocked: bool) -> bool:
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
        # "" (empty), "GOAL" are walkable. Agent starts somewhere else.
        return True

    def find_adjacent_cell_facing_target(target_x: int, target_y: int) -> Optional[Position]:
        """ Finds a valid empty cell adjacent to the target to stand on. """
        potential_adj_spots = [
            (target_x, target_y - 1), # Adjacent spot Below, facing UP
            (target_x, target_y + 1), # Adjacent spot Above, facing DOWN
            (target_x - 1, target_y), # Adjacent spot Right, facing LEFT
            (target_x + 1, target_y)  # Adjacent spot Left, facing RIGHT
        ]
        for adj_x, adj_y in potential_adj_spots:
             # Check if the adjacent spot itself is within bounds and initially empty
             if (0 <= adj_y < height and 0 <= adj_x < width and
                 grid[adj_y][adj_x] == "" and not (adj_x == start_pos[0] and adj_y == start_pos[1])): # Check if empty AND not the agent start pos initially
                 return (adj_x, adj_y)
        return None # No suitable adjacent spot found


    def find_path(start_x: int, start_y: int, start_dir: Direction,
                  target_x: int, target_y: int,
                  facing_target_x: int, facing_target_y: int, # Use -1, -1 if just reaching the cell
                  current_has_key: bool, current_door_unlocked: bool
                  ) -> Optional[Tuple[Path, int, int, Direction]]:
        """
        Performs Breadth-First Search to find the shortest action path.

        Args:
            start_x, start_y, start_dir: Starting state.
            target_x, target_y: Target coordinates to stand on.
            facing_target_x, facing_target_y: Coordinates the agent must be facing upon arrival at target_x, target_y.
                                              Set to -1, -1 if only reaching the cell matters.
            current_has_key: Whether the agent currently holds the key.
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
            if is_cell_walkable(front_x, front_y, current_door_unlocked):
                next_state_move: State = (front_x, front_y, curr_dir)
                if next_state_move not in visited:
                    visited.add(next_state_move)
                    new_path_move = current_path + [MOVE]
                    queue.append((front_x, front_y, curr_dir, new_path_move))

        return None # Path not found

    # --- 2. Phase 1: Navigate to and pick up the Key ---
    key_adj_target = find_adjacent_cell_facing_target(key_pos[0], key_pos[1])
    if key_adj_target is None:
        raise RuntimeError("Cannot find valid adjacent spot to stand for picking up KEY.")

    path_result_key = find_path(current_x, current_y, current_dir,
                                key_adj_target[0], key_adj_target[1],
                                key_pos[0], key_pos[1], # Must face the key
                                has_key, door_unlocked)

    if path_result_key is None:
        raise RuntimeError("Cannot find path to the KEY.")

    path_to_key, current_x, current_y, current_dir = path_result_key
    overall_action_list.extend(path_to_key)
    overall_action_list.append(PICKUP)
    has_key = True
    # Conceptually: grid[key_pos[1]][key_pos[0]] = "" # Update state (key is gone)

    # --- 3. Phase 2: Navigate to and unlock the Door ---
    door_adj_target = find_adjacent_cell_facing_target(door_pos[0], door_pos[1])
    if door_adj_target is None:
         raise RuntimeError("Cannot find valid adjacent spot to stand for unlocking DOOR.")

    path_result_door = find_path(current_x, current_y, current_dir,
                                 door_adj_target[0], door_adj_target[1],
                                 door_pos[0], door_pos[1], # Must face the door
                                 has_key, door_unlocked)

    if path_result_door is None:
        raise RuntimeError("Cannot find path to the DOOR after getting key.")

    path_to_door, current_x, current_y, current_dir = path_result_door
    overall_action_list.extend(path_to_door)
    overall_action_list.append(UNLOCK)
    door_unlocked = True
    # Conceptually: Door cell is now treated as walkable by is_cell_walkable

    # --- 4. Phase 3: Navigate to the Goal ---
    # Target is the goal cell itself, no specific facing direction needed upon arrival
    path_result_goal = find_path(current_x, current_y, current_dir,
                                 goal_pos[0], goal_pos[1],
                                 -1, -1, # -1 indicates no facing requirement
                                 has_key, door_unlocked)

    if path_result_goal is None:
        raise RuntimeError("Cannot find path to the GOAL after unlocking door.")

    path_to_goal, final_x, final_y, final_dir = path_result_goal # Final state stored but not needed after this
    overall_action_list.extend(path_to_goal)

    # --- 5. Return the final action list ---
    return overall_action_list


# --- Example Usage with the sample grid ---
if __name__ == '__main__':
    sample_grid = [
        ["WALL", "WALL", "WALL", "WALL", "WALL", "WALL", "WALL", "WALL"],
        ["WALL", "", "", "", "DOOR", "", "", "WALL"],
        ["WALL", "", "", "", "WALL", "", "", "WALL"],
        ["WALL", "", "", "", "WALL", "", "", "WALL"],
        ["WALL", "", "", "KEY", "WALL", "", "", "WALL"],
        ["WALL", "AGENT", "", "", "WALL", "", "", "WALL"],
        ["WALL", "", "", "", "WALL", "", "GOAL", "WALL"],
        ["WALL", "WALL", "WALL", "WALL", "WALL", "WALL", "WALL", "WALL"]
    ]
    sample_start_direction = DOWN # As per sample text, assuming agent starts facing DOWN

    # Note: The corrected sample solution implies the agent starts FACING RIGHT
    # Let's try the provided start direction first, then the implied one.
    
    print("--- Solving with provided start_direction = DOWN ---")
    try:
        solution_down = solve(sample_grid, DOWN)
        print("Solution found:")
        print(solution_down)
        print(f"Number of actions: {len(solution_down)}")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        
    print("\n--- Solving with implied start_direction = RIGHT (from sample solution) ---")
    # Need to modify the grid slightly if agent starts elsewhere, but let's assume
    # the sample solution analysis just means IF the agent was facing right...
    # Or maybe the initial direction in the text was different from the trace?
    # Let's manually set start direction to RIGHT and see if it matches the sample better.
    
    # Rerun initialization logic conceptually for the RIGHT start:
    # Agent starts at (1, 5), initial_dir = RIGHT
    try:
        solution_right = solve(sample_grid, RIGHT)
        print("Solution found:")
        print(solution_right)
        print(f"Number of actions: {len(solution_right)}")

        # Compare with sample (adjusting for slight path differences maybe)
        sample_solution = [
          "LEFT", "MOVE", "MOVE", "LEFT", # Move to (5, 3) facing UP to face the KEY at (4, 3)
          "PICKUP", # Pick up the KEY
          "MOVE", "MOVE", "MOVE", "MOVE", "RIGHT", # Move to (1, 3) facing RIGHT to face the DOOR at (1, 4)
          "UNLOCK", # Unlock the DOOR
          "MOVE", "MOVE", "MOVE", "RIGHT", "MOVE", "MOVE", "MOVE", "MOVE", "MOVE" # Move to (6, 6) which is the GOAL cell
        ]
        print(f"\nSample solution actions: {len(sample_solution)}")
        # Note: BFS finds shortest paths, which might differ slightly from manual solutions
        # if multiple shortest paths exist, but the length should be minimal.
        # Let's analyze the sample output:
        # Start (1,5) Facing RIGHT
        # LEFT -> Facing UP @ (1,5)
        # MOVE -> @ (1,4)
        # MOVE -> @ (1,3)
        # LEFT -> Facing LEFT @ (1,3)
        # Hmm, the sample solution description seems inconsistent with its own steps/target pos.
        # "Move to (5, 3) facing UP to face the KEY at (4, 3)" - If agent is at (5,3), grid value is WALL.
        # If agent is at col 3, row 5, this is (3, 5). Key is at (3, 4).
        # Let's re-read the sample start: "Starting at (5, 1) facing RIGHT"
        # Grid indices are [row][col]. So (5, 1) means row 5, col 1. This is AGENT. OK.
        # Key is at (4, 3) -> row 4, col 3. OK.
        # Door is at (1, 4) -> row 1, col 4. OK.
        # Goal is at (6, 6) -> row 6, col 6. OK.
        # Now Trace Sample Solution from (1, 5) Facing RIGHT:
        # LEFT -> (1, 5) Facing UP
        # MOVE -> (1, 4) Facing UP
        # MOVE -> (1, 3) Facing UP
        # LEFT -> (1, 3) Facing LEFT
        # Now agent is at (1, 3), facing LEFT. Key is at (3, 4). This doesn't match sample text.
        
        # Let's trust the grid and the code, assuming the Sample *Text* might be wrong,
        # but the *Grid* and *Start Position* are correct.
        # The provided sample solution trace seems flawed relative to the grid coords.
        # Our code should find *a* shortest path based on the BFS logic.

    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")


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