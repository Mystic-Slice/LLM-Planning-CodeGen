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
    
    # Helper function to find positions of objects
    def find_positions(grid, obj):
        positions = []
        for i, row in enumerate(grid):
            for j, cell in enumerate(row):
                if cell == obj:
                    positions.append((i, j))
        return positions

    # Find the agent's starting position
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
    
    # Find the positions of the BOX(es)
    box_positions = find_positions(grid, 'BOX')
    if not box_positions:
        raise ValueError("No BOX found in the grid")
    goal_position = box_positions[0]  # Assuming one BOX
    
    # Create the starting state
    grid_state = [row.copy() for row in grid]
    grid_state[start_position[0]][start_position[1]] = ''  # Remove 'AGENT' from grid
    
    start_state = State(
        position=start_position,
        direction=start_direction,
        held_object=None,
        actions=[],
        cost=0,
        grid_state=grid_state,
        goal_position=goal_position
    )
    
    open_list = []
    heapq.heappush(open_list, (start_state.total_cost(), start_state))
    closed_set = set()
    while open_list:
        _, current_state = heapq.heappop(open_list)
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
                    heapq.heappush(open_list, (new_state.total_cost(), new_state))
            elif action == 'LEFT':
                idx = (directions.index(new_state.direction) - 1) % 4
                new_state.direction = directions[idx]
                heapq.heappush(open_list, (new_state.total_cost(), new_state))
            elif action == 'RIGHT':
                idx = (directions.index(new_state.direction) + 1) % 4
                new_state.direction = directions[idx]
                heapq.heappush(open_list, (new_state.total_cost(), new_state))
            elif action == 'PICKUP':
                if new_state.held_object is None:
                    dx, dy = move_vectors[new_state.direction]
                    nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                    if is_within_grid(nx, ny, new_state.grid_state):
                        cell_content = new_state.grid_state[nx][ny]
                        if cell_content in ['KEY', 'BOX']:
                            new_state.held_object = cell_content
                            new_state.grid_state[nx][ny] = ''
                            heapq.heappush(open_list, (new_state.total_cost(), new_state))
            elif action == 'DROP':
                if new_state.held_object is not None:
                    dx, dy = move_vectors[new_state.direction]
                    nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                    if is_within_grid(nx, ny, new_state.grid_state):
                        if new_state.grid_state[nx][ny] == '':
                            new_state.grid_state[nx][ny] = new_state.held_object
                            new_state.held_object = None
                            heapq.heappush(open_list, (new_state.total_cost(), new_state))
            elif action == 'UNLOCK':
                if new_state.held_object == 'KEY':
                    dx, dy = move_vectors[new_state.direction]
                    nx, ny = new_state.position[0] + dx, new_state.position[1] + dy
                    if is_within_grid(nx, ny, new_state.grid_state):
                        if new_state.grid_state[nx][ny] == 'DOOR':
                            new_state.grid_state[nx][ny] = ''  # Remove door
                            # Key is retained after unlocking
                            heapq.heappush(open_list, (new_state.total_cost(), new_state))
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
    # Can move into a door cell if the door has been unlocked (now empty)
    return False

class State:
    def __init__(self, position, direction, held_object, actions, cost, grid_state, goal_position):
        self.position = position  # (x, y)
        self.direction = direction  # 'UP', 'DOWN', 'LEFT', 'RIGHT'
        self.held_object = held_object  # None, 'KEY', 'BOX'
        self.actions = actions  # list of actions taken to reach this state
        self.cost = cost  # total cost (number of steps)
        self.grid_state = grid_state  # the current grid state (2D list)
        self.goal_position = goal_position  # position of the BOX
        self.heuristic = self.calculate_heuristic()
        
    def total_cost(self):
        # Total estimated cost (f = g + h)
        return self.cost + self.heuristic
    
    def calculate_heuristic(self):
        # Heuristic: Manhattan distance to the goal (position of the BOX)
        # If already holding the BOX, heuristic is 0
        if self.held_object == 'BOX':
            return 0
        x1, y1 = self.position
        x2, y2 = self.goal_position
        return abs(x1 - x2) + abs(y1 - y2)
    
    def __lt__(self, other):
        # For priority queue, compare total estimated cost.
        return self.total_cost() < other.total_cost()
    
    def __hash__(self):
        # Create a unique hash for the state
        grid_signature = tuple(tuple(row) for row in self.grid_state)
        return hash((self.position, self.direction, self.held_object, grid_signature))
    
    def __eq__(self, other):
        return (self.position == other.position and
                self.direction == other.direction and
                self.held_object == other.held_object and
                self.grid_state == other.grid_state)

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