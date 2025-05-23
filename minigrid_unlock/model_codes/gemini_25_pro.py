import collections

# --- Helper Functions ---

def find_object_coordinates(grid, object_type):
    """Finds the (row, col) of the first occurrence of object_type."""
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == object_type:
                return (r, c)
    return None # Should not happen in valid inputs as per description

def turn_left(direction):
    """Calculates the new direction after turning left."""
    if direction == "UP": return "LEFT"
    if direction == "LEFT": return "DOWN"
    if direction == "DOWN": return "RIGHT"
    if direction == "RIGHT": return "UP"

def turn_right(direction):
    """Calculates the new direction after turning right."""
    if direction == "UP": return "RIGHT"
    if direction == "RIGHT": return "DOWN"
    if direction == "DOWN": return "LEFT"
    if direction == "LEFT": return "UP"

def calculate_forward_pos(pos, direction):
    """Calculates the coordinates of the cell in front."""
    r, c = pos
    if direction == "UP": return (r - 1, c)
    if direction == "DOWN": return (r + 1, c)
    if direction == "LEFT": return (r, c - 1)
    if direction == "RIGHT": return (r, c + 1)
    return pos # Should not happen

def is_valid_move(grid, pos):
    """Checks if moving to pos is valid (within bounds, not WALL)."""
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    r, c = pos

    # Check bounds
    if not (0 <= r < height and 0 <= c < width):
        return False

    # Check content (only WALL blocks movement entirely for pathfinding)
    # Note: We pathfind *around* KEY/DOOR/AGENT initially.
    # Empty strings "" are walkable.
    cell_content = grid[r][c]
    if cell_content == "WALL":
        return False

    return True

def apply_action_to_state(pos, direction, action):
    """Applies an action and returns the new (pos, direction) state."""
    if action == "LEFT":
        return pos, turn_left(direction)
    elif action == "RIGHT":
        return pos, turn_right(direction)
    elif action == "MOVE":
        new_pos = calculate_forward_pos(pos, direction)
        # We assume the path generated by BFS only contains valid moves
        return new_pos, direction
    else: # PICKUP, UNLOCK, DROP don't change position/direction
        return pos, direction


def find_path_to_adjacent(grid, start_pos, start_dir, target_pos):
    """
    Uses BFS to find the shortest action sequence (LEFT, RIGHT, MOVE)
    to reach a state adjacent to target_pos, facing target_pos.

    Returns:
        list: A list of actions, or None if no path found.
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0
    queue = collections.deque()
    # State: ((row, col), direction)
    # Queue item: ( state, path_list )
    start_state = (start_pos, start_dir)
    queue.append((start_state, []))
    # Visited: set of ((row, col), direction) tuples
    visited = {start_state}

    while queue:
        current_state, current_path = queue.popleft()
        current_pos, current_dir = current_state

        # --- Goal Check ---
        # Is the cell directly in front of the agent the target cell?
        pos_in_front = calculate_forward_pos(current_pos, current_dir)
        if pos_in_front == target_pos:
            return current_path # Found the path

        # --- Explore Neighbors (Actions) ---
        possible_actions = ["LEFT", "RIGHT", "MOVE"]

        for action in possible_actions:
            next_pos = current_pos
            next_dir = current_dir
            valid_action = True

            if action == "LEFT":
                next_dir = turn_left(current_dir)
            elif action == "RIGHT":
                next_dir = turn_right(current_dir)
            elif action == "MOVE":
                move_target_pos = calculate_forward_pos(current_pos, current_dir)
                if is_valid_move(grid, move_target_pos):
                    next_pos = move_target_pos
                else:
                    valid_action = False # Cannot move here

            if valid_action:
                next_state = (next_pos, next_dir)
                if next_state not in visited:
                    visited.add(next_state)
                    next_path = current_path + [action]
                    queue.append((next_state, next_path))

    return None # No path found

# --- Main Solver Function ---

def solve(grid, start_direction):
    """
    Calculates the sequence of actions to find the key and unlock the door.

    Args:
        grid (list[list[str]]): The 2D grid environment.
        start_direction (str): The agent's starting direction.

    Returns:
        list[str]: The sequence of actions, or None if no solution found.
    """
    agent_pos = find_object_coordinates(grid, "AGENT")
    key_pos = find_object_coordinates(grid, "KEY")
    door_pos = find_object_coordinates(grid, "DOOR")

    if not agent_pos or not key_pos or not door_pos:
        # print("Error: Could not find AGENT, KEY, or DOOR in the grid.")
        return None # Invalid setup

    agent_dir = start_direction
    # holding_item = None # Not explicitly needed for logic, but conceptually useful
    action_sequence = []

    # 1. Phase 1: Go to the KEY and PICKUP
    # print(f"Finding path from {agent_pos} facing {agent_dir} to adjacent of KEY {key_pos}")
    path_to_key_actions = find_path_to_adjacent(grid, agent_pos, agent_dir, key_pos)

    if path_to_key_actions is None:
        # print(f"Error: Cannot find path to Key at {key_pos}")
        return None

    # Execute path to Key
    for action in path_to_key_actions:
        action_sequence.append(action)
        agent_pos, agent_dir = apply_action_to_state(agent_pos, agent_dir, action)
        # print(f"  Action: {action}, New State: pos={agent_pos}, dir={agent_dir}") # Debug

    # Now adjacent to the key, facing it. Pick it up.
    action_sequence.append("PICKUP")
    # holding_item = "KEY"
    # print(f"Picked up KEY. Current state: pos={agent_pos}, dir={agent_dir}")


    # 2. Phase 2: Go to the DOOR (holding KEY) and UNLOCK
    # print(f"Finding path from {agent_pos} facing {agent_dir} to adjacent of DOOR {door_pos}")
    # Important: The grid state hasn't changed in this implementation,
    # the BFS operates on the original layout. If the key location being empty
    # mattered for pathfinding, the grid copy/modification would be needed.
    path_to_door_actions = find_path_to_adjacent(grid, agent_pos, agent_dir, door_pos)

    if path_to_door_actions is None:
        # print(f"Error: Cannot find path to Door at {door_pos} while holding KEY")
        return None

    # Execute path to Door
    for action in path_to_door_actions:
        action_sequence.append(action)
        agent_pos, agent_dir = apply_action_to_state(agent_pos, agent_dir, action)
        # print(f"  Action: {action}, New State: pos={agent_pos}, dir={agent_dir}") # Debug

    # Now adjacent to the door, facing it. Unlock it.
    action_sequence.append("UNLOCK")
    # holding_item = None
    # print(f"Unlocked DOOR. Final state: pos={agent_pos}, dir={agent_dir}")

    return action_sequence

if __name__ == "__main__":
    # Example grid and direction
    grid = [
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"],
["WALL","","","","KEY","WALL","","","","","WALL"],
["WALL","","","AGENT","","WALL","","","","","WALL"],
["WALL","","","","","DOOR","","","","","WALL"],
["WALL","","","","","WALL","","","","","WALL"],
["WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL","WALL"]
    ]
    direction = "RIGHT"
    
    actions = solve(grid, direction)
    print("Actions to solve the game:", actions)