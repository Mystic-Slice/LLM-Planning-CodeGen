def solve(grid, start_direction):
    import heapq
    import copy

    # Define possible directions and their movement vectors
    directions = ['UP', 'RIGHT', 'DOWN', 'LEFT']
    move_vectors = {
        'UP': (-1, 0),
        'RIGHT': (0, 1),
        'DOWN': (1, 0),
        'LEFT': (0, -1)
    }

    # First, find the agent's starting position
    for i, row in enumerate(grid):
        for j, cell in enumerate(row):
            if cell == 'AGENT':
                start_position = (i, j)
                break
        else:
            continue
        break
    else:
        raise ValueError("Agent not found in the grid")

    from heapq import heappush, heappop

    # Create the starting state
    grid_state = [row.copy() for row in grid]
    grid_state[start_position[0]][start_position[1]] = ''  # Remove 'AGENT' from grid

    start_state = State(
        position=start_position,
        direction=start_direction,
        held_object=None,
        actions=[],
        cost=0,
        grid_state=grid_state
    )

    open_list = []
    heappush(open_list, (0, start_state))

    closed_set = set()

    while open_list:
        current_cost, current_state = heappop(open_list)

        if current_state in closed_set:
            continue
        closed_set.add(current_state)

        # Check if goal is reached (holding the BOX)
        if current_state.held_object == 'BOX':
            return current_state.actions  # Return the sequence of actions

        # Generate possible actions from current state
        for action in ['MOVE', 'LEFT', 'RIGHT', 'PICKUP', 'DROP', 'UNLOCK']:
            new_state = copy.deepcopy(current_state)
            new_state.actions = current_state.actions + [action]
            new_state.cost = current_state.cost + 1

            # Handle actions
            if action == 'MOVE':
                # Calculate next position
                dx, dy = move_vectors[new_state.direction]
                nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                if is_valid_move(new_state.grid_state, nx, ny):
                    new_state.position = (nx, ny)
                    heappush(open_list, (new_state.cost, new_state))
            elif action == 'LEFT':
                idx = (directions.index(new_state.direction) - 1) % 4
                new_state.direction = directions[idx]
                heappush(open_list, (new_state.cost, new_state))
            elif action == 'RIGHT':
                idx = (directions.index(new_state.direction) + 1) % 4
                new_state.direction = directions[idx]
                heappush(open_list, (new_state.cost, new_state))
            elif action == 'PICKUP':
                if new_state.held_object is None:
                    dx, dy = move_vectors[new_state.direction]
                    nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                    if is_within_grid(nx, ny, new_state.grid_state):
                        cell_content = new_state.grid_state[nx][ny]
                        if cell_content in ['KEY', 'BOX']:
                            new_state.held_object = cell_content
                            new_state.grid_state[nx][ny] = ''
                            heappush(open_list, (new_state.cost, new_state))
            elif action == 'DROP':
                if new_state.held_object is not None:
                    dx, dy = move_vectors[new_state.direction]
                    nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                    if is_within_grid(nx, ny, new_state.grid_state):
                        if new_state.grid_state[nx][ny] == '':
                            new_state.grid_state[nx][ny] = new_state.held_object
                            new_state.held_object = None
                            heappush(open_list, (new_state.cost, new_state))
            elif action == 'UNLOCK':
                if new_state.held_object == 'KEY':
                    dx, dy = move_vectors[new_state.direction]
                    nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                    if is_within_grid(nx, ny, new_state.grid_state):
                        if new_state.grid_state[nx][ny] == 'DOOR':
                            new_state.grid_state[nx][ny] = ''  # Remove door
                            # Key is retained after unlocking
                            heappush(open_list, (new_state.cost, new_state))
    # If goal not found
    return []  # Return empty list if no solution found

def is_within_grid(x, y, grid):
    return 0 <= x < len(grid) and 0 <= y < len(grid[0])

def is_valid_move(grid, x, y):
    if not is_within_grid(x, y, grid):
        return False
    cell = grid[x][y]
    if cell == '':
        return True
    # Cannot move into cells with any object
    return False

class State:
    def __init__(self, position, direction, held_object, actions, cost, grid_state):
        self.position = position  # (x, y)
        self.direction = direction  # 'UP', 'DOWN', 'LEFT', 'RIGHT'
        self.held_object = held_object  # None, 'KEY', 'BOX'
        self.actions = actions  # list of actions taken to reach this state
        self.cost = cost  # total cost (number of steps)
        self.grid_state = grid_state  # the current grid state (2D list)
    
    def __lt__(self, other):
        # For priority queue, compare cost.
        return self.cost < other.cost

    def __hash__(self):
        # We need a unique hash for the state to store in the visited set
        # Let's define state key based on position, direction, held_object, and grid signature
        return hash((self.position, self.direction, self.held_object, self.grid_signature()))

    def __eq__(self, other):
        return (self.position == other.position and
                self.direction == other.direction and
                self.held_object == other.held_object and
                self.grid_signature() == other.grid_signature())

    def grid_signature(self):
        # Return a tuple representing the positions of KEY, BOX, and DOOR statuses
        key_positions = []
        box_positions = []
        door_positions = []
        for i, row in enumerate(self.grid_state):
            for j, cell in enumerate(row):
                if cell == 'KEY':
                    key_positions.append((i, j))
                elif cell == 'BOX':
                    box_positions.append((i, j))
                elif cell == 'DOOR':
                    door_positions.append((i, j))
        return (tuple(key_positions), tuple(box_positions), tuple(door_positions))


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