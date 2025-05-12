def solve(grid, start_direction):
    import heapq
    # Helper functions
    DIRECTIONS = ['UP', 'RIGHT', 'DOWN', 'LEFT']
    dir_to_vec = {'UP': (-1, 0), 'DOWN': (1, 0), 'LEFT': (0, -1), 'RIGHT': (0, 1)}
    turn_left = {'UP': 'LEFT', 'LEFT': 'DOWN', 'DOWN': 'RIGHT', 'RIGHT': 'UP'}
    turn_right = {'UP': 'RIGHT', 'RIGHT': 'DOWN', 'DOWN': 'LEFT', 'LEFT': 'UP'}

    # Define the AgentState class
    class AgentState:
        def __init__(self, position, facing_direction, holding, actions, steps, door_unlocked, key_position):
            self.position = position                  # (x, y)
            self.facing_direction = facing_direction  # 'UP', 'DOWN', 'LEFT', 'RIGHT'
            self.holding = holding                    # 'KEY' or None
            self.actions = actions                    # List of actions taken
            self.steps = steps                        # Number of steps taken
            self.door_unlocked = door_unlocked        # Boolean
            self.key_position = key_position          # (x, y) or None

        def __hash__(self):
            return hash((
                self.position,
                self.facing_direction,
                self.holding,
                self.door_unlocked,
                self.key_position
            ))

        def __eq__(self, other):
            return (
                self.position == other.position and
                self.facing_direction == other.facing_direction and
                self.holding == other.holding and
                self.door_unlocked == other.door_unlocked and
                self.key_position == other.key_position
            )

    def is_within_grid(position):
        x, y = position
        return 0 <= x < len(grid) and 0 <= y < len(grid[0])

    def get_position_in_direction(position, direction):
        dx, dy = dir_to_vec[direction]
        x, y = position
        return (x + dx, y + dy)

    def is_cell_traversable(position, state):
        if not is_within_grid(position):
            return False
        x, y = position
        cell = grid[x][y]
        # Check if door is unlocked
        if cell == 'DOOR':
            return state.door_unlocked
        # Cannot enter walls
        if cell == 'WALL':
            return False
        # Cannot enter a cell that contains an object unless it has been picked up
        if state.key_position == (x, y):
            return False
        return True  # Empty cell or cell where the key has been picked up

    def is_goal_state(state):
        return state.door_unlocked

    def heuristic(state):
        # Estimate the remaining distance
        if state.door_unlocked:
            return 0
        if state.holding == 'KEY':
            # Distance to door
            return manhattan_distance(state.position, door_position)
        else:
            # Distance to key plus distance from key to door
            return manhattan_distance(state.position, state.key_position) + estimated_key_to_door

    def manhattan_distance(pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def get_valid_actions(state):
        actions = ['LEFT', 'RIGHT']
        forward_pos = get_position_in_direction(state.position, state.facing_direction)
        # 'MOVE' action
        if is_cell_traversable(forward_pos, state):
            actions.append('MOVE')
        # 'PICKUP' action
        if state.holding is None and is_within_grid(forward_pos):
            x, y = forward_pos
            if grid[x][y] == 'KEY' and state.key_position == (x, y):
                actions.append('PICKUP')
        # 'DROP' action into any adjacent empty cell
        if state.holding is not None:
            for direction in DIRECTIONS:
                drop_pos = get_position_in_direction(state.position, direction)
                if is_within_grid(drop_pos):
                    x, y = drop_pos
                    if grid[x][y] == '' and state.key_position != (x, y):
                        if state.position != drop_pos:  # Ensure not dropping on own position
                            actions.append('DROP_' + direction)
        # 'UNLOCK' action
        if state.holding == 'KEY' and is_within_grid(forward_pos):
            x, y = forward_pos
            if grid[x][y] == 'DOOR':
                actions.append('UNLOCK')
        return actions

    def apply_action(state, action):
        from copy import deepcopy
        new_state = deepcopy(state)
        new_state.actions.append(action)
        new_state.steps += 1
        if action == 'LEFT':
            new_state.facing_direction = turn_left[state.facing_direction]
        elif action == 'RIGHT':
            new_state.facing_direction = turn_right[state.facing_direction]
        elif action == 'MOVE':
            new_state.position = get_position_in_direction(state.position, state.facing_direction)
        elif action == 'PICKUP':
            new_state.holding = 'KEY'
            new_state.key_position = None  # Key is now held
        elif action.startswith('DROP_'):
            drop_direction = action[5:]  # Get the direction part
            drop_pos = get_position_in_direction(state.position, drop_direction)
            new_state.holding = None
            new_state.key_position = drop_pos  # Key is dropped here
        elif action == 'UNLOCK':
            new_state.door_unlocked = True
        return new_state

    # Find initial positions and compute estimated distance from key to door
    agent_start_position = None
    key_position = None
    door_position = None
    for x in range(len(grid)):
        for y in range(len(grid[0])):
            if grid[x][y] == 'AGENT':
                agent_start_position = (x, y)
            elif grid[x][y] == 'KEY':
                key_position = (x, y)
            elif grid[x][y] == 'DOOR':
                door_position = (x, y)
    if agent_start_position is None or door_position is None or key_position is None:
        raise ValueError("Missing 'AGENT', 'KEY', or 'DOOR' in grid")
    estimated_key_to_door = manhattan_distance(key_position, door_position)

    # Initialize the starting state
    start_state = AgentState(
        position=agent_start_position,
        facing_direction=start_direction,
        holding=None,
        actions=[],
        steps=0,
        door_unlocked=False,
        key_position=key_position
    )

    # A* search initialization
    open_set = []
    counter = 0  # Unique counter to avoid comparing AgentState instances
    heapq.heappush(open_set, (heuristic(start_state), counter, start_state))
    closed_set = set()

    while open_set:
        _, _, current_state = heapq.heappop(open_set)
        if is_goal_state(current_state):
            return current_state.actions
        state_id = (
            current_state.position,
            current_state.facing_direction,
            current_state.holding,
            current_state.door_unlocked,
            current_state.key_position
        )
        if state_id in closed_set:
            continue
        closed_set.add(state_id)
        for action in get_valid_actions(current_state):
            new_state = apply_action(current_state, action)
            counter += 1  # Increment counter to ensure unique entries
            priority = new_state.steps + heuristic(new_state)
            heapq.heappush(open_set, (priority, counter, new_state))
    return []  # No solution found

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