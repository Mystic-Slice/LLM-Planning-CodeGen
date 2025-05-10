import heapq

def solve_grid(grid, start_position, max_actions, is_diagonals_allowed, carry_limit, cost_per_step):
    """
    Solves the energy collection game with obstacles, optional diagonal movements, carry limit, and cost per step.
    
    Parameters:
    - grid: A 2D list representing the grid. Each cell can be:
        - 'E' for an energy token
        - ' ' for an empty cell
        - 'A' for the agent's starting position
        - 'O' for an obstacle
    - start_position: A tuple (x, y) representing the agent's starting position.
    - max_actions: The maximum number of actions the agent can perform.
    - is_diagonals_allowed: Boolean indicating if diagonal moves are allowed.
    - carry_limit: The maximum number of energy tokens the agent can carry.
    - cost_per_step: The cost associated with a step in any direction.
    
    Returns:
    - A list of actions representing the agent's moves.
    """
    # Define the possible moves
    if is_diagonals_allowed:
        move_actions = [
            ("UP", (-1, 0)),
            ("DOWN", (1, 0)),
            ("LEFT", (0, -1)),
            ("RIGHT", (0, 1)),
            ("UPLEFT", (-1, -1)),
            ("UPRIGHT", (-1, 1)),
            ("DOWNLEFT", (1, -1)),
            ("DOWNRIGHT", (1, 1))
        ]
    else:
        move_actions = [
            ("UP", (-1, 0)),
            ("DOWN", (1, 0)),
            ("LEFT", (0, -1)),
            ("RIGHT", (0, 1))
        ]
    moves = dict(move_actions)
    
    # Helper function: Heuristic function for A*
    def heuristic(a, b):
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        if is_diagonals_allowed:
            # Chebyshev distance
            return max(dx, dy)
        else:
            # Manhattan distance
            return dx + dy
    
    # Helper function: A* pathfinding algorithm
    def astar(start, goal):
        open_set = []
        heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start, []))
        closed_set = set()
        
        while open_set:
            est_total_cost, cost_so_far, current, path = heapq.heappop(open_set)
            
            if current == goal:
                return path  # Return the path to goal
            
            if current in closed_set:
                continue
            closed_set.add(current)
            
            for action, (dx, dy) in move_actions:
                neighbor = (current[0] + dx, current[1] + dy)
                x, y = neighbor
                # Check if neighbor is within grid bounds
                if 0 <= x < grid_height and 0 <= y < grid_width:
                    cell = grid[x][y]
                    if cell != 'O':  # Check if not an obstacle
                        # Add neighbor to open set
                        new_cost = cost_so_far + 1  # Assume cost per move is 1
                        est_total = new_cost + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (est_total, new_cost, neighbor, path + [action]))
        return None  # No path found
    
    # Get the dimensions of the grid
    grid_height = len(grid)
    grid_width = len(grid[0]) if grid_height > 0 else 0
    
    # Initialize variables
    current_position = start_position  # Agent's current position as (x, y)
    carried_tokens = 0                 # Number of energy tokens the agent is carrying
    total_score = 0                    # Tokens dropped at starting position
    actions_remaining = max_actions    # Remaining actions
    action_list = []                   # List of actions to perform
    total_steps_taken = 0              # Total movement steps taken
    
    # Find positions of all energy tokens (excluding starting cell)
    uncollected_tokens = set()
    for x in range(grid_height):
        for y in range(grid_width):
            cell = grid[x][y]
            if cell == 'E':
                pos = (x, y)
                if pos != start_position:
                    uncollected_tokens.add(pos)
                else:
                    total_score += 1  # Include any tokens at the starting position
            elif cell == 'A':
                # Ensure the starting position is updated if 'A' is in the grid
                start_position = (x, y)
                current_position = start_position
    
    # Main loop
    while actions_remaining > 0:
        # Check if we have reached the carry limit
        if carried_tokens >= carry_limit:
            # Need to return to starting position to drop off tokens
            if current_position != start_position:
                # Find path back to starting position
                path_to_start = astar(current_position, start_position)
                if path_to_start is None:
                    break  # Cannot return to start due to obstacles
                actions_needed = len(path_to_start) + 1  # +1 for DROP action
    
                if actions_remaining >= actions_needed:
                    action_list.extend(path_to_start)
                    total_steps_taken += len(path_to_start)
                    actions_remaining -= len(path_to_start)
                    current_position = start_position
    
                    # Drop all carried tokens
                    action_list.append("DROP")
                    actions_remaining -= 1
                    total_score += carried_tokens
                    carried_tokens = 0
                else:
                    break  # Not enough actions to return and drop off tokens
            else:
                # Already at starting position, drop off tokens
                if actions_remaining >= 1:
                    action_list.append("DROP")
                    actions_remaining -= 1
                    total_score += carried_tokens
                    carried_tokens = 0
                else:
                    break  # No actions left
    
        # Calculate the total movement cost to return home if we proceed further
        path_back = astar(current_position, start_position)
        if path_back is None:
            total_return_cost = float('inf')
        else:
            return_cost = len(path_back)
            drop_action_cost = 1 if carried_tokens > 0 else 0
            total_return_cost = return_cost + drop_action_cost
    
        # If we must return now due to action limit
        if actions_remaining <= total_return_cost:
            if carried_tokens > 0 and current_position != start_position:
                # Move back to starting position
                if path_back is None:
                    break  # Cannot return to start
                actions_needed = len(path_back) + drop_action_cost
    
                if actions_remaining >= actions_needed:
                    action_list.extend(path_back)
                    total_steps_taken += len(path_back)
                    actions_remaining -= len(path_back)
                    current_position = start_position
    
                    # Drop all carried tokens
                    if drop_action_cost > 0:
                        action_list.append("DROP")
                        actions_remaining -= 1
                        total_score += carried_tokens
                        carried_tokens = 0
                else:
                    break  # Not enough actions to return
            else:
                break  # No actions left or nothing to drop
            continue  # Move to next iteration
    
        # Calculate net gain for reachable tokens
        token_options = []
        for token_pos in uncollected_tokens:
            # Check if we have space to carry more tokens
            if carried_tokens >= carry_limit:
                break  # Cannot carry more tokens
    
            # Find path to the token
            path_to_token = astar(current_position, token_pos)
            if path_to_token is None:
                continue  # Cannot reach token due to obstacles

            path_from_token_to_start = astar(token_pos, start_position)
            if path_from_token_to_start is None:
                continue  # Cannot return to start after collecting token

            to_token_cost = len(path_to_token)
            take_action_cost = 1  # Cost for "TAKE"
            to_home_cost = len(path_from_token_to_start)
            drop_action_cost = 1 if carried_tokens + 1 >= carry_limit or carried_tokens + 1 >= 1 else 0

            total_movement_steps = to_token_cost + to_home_cost
            movement_cost = total_movement_steps * cost_per_step
            net_gain = 1 - movement_cost

            total_actions_needed = to_token_cost + take_action_cost + to_home_cost + drop_action_cost

            # Ensure we have enough actions
            if actions_remaining >= total_actions_needed and net_gain > 0:
                token_options.append((token_pos, net_gain, path_to_token, path_from_token_to_start))
        
        if not token_options:
            # No tokens with positive net gain or reachable within remaining actions
            if carried_tokens > 0 and current_position != start_position:
                # Return to start and drop off tokens
                if path_back is None:
                    break  # Cannot return to start
                actions_needed = len(path_back) + drop_action_cost

                if actions_remaining >= actions_needed:
                    action_list.extend(path_back)
                    total_steps_taken += len(path_back)
                    actions_remaining -= len(path_back)
                    current_position = start_position

                    # Drop all carried tokens
                    if drop_action_cost > 0:
                        action_list.append("DROP")
                        actions_remaining -= 1
                        total_score += carried_tokens
                        carried_tokens = 0
                break
            else:
                break  # No actions left or nothing to collect
            continue  # Move to next iteration

        # Select the token with the highest net gain
        next_token_data = max(token_options, key=lambda x: x[1])
        next_token = next_token_data[0]
        net_gain = next_token_data[1]
        path_to_token = next_token_data[2]
        path_from_token_to_start = next_token_data[3]

        # Move to the next token
        actions_needed = len(path_to_token) + 1  # +1 for TAKE action

        if actions_remaining >= actions_needed:
            # Move and take the token
            action_list.extend(path_to_token)
            total_steps_taken += len(path_to_token)
            actions_remaining -= len(path_to_token)
            current_position = next_token

            # Take the energy token
            action_list.append("TAKE")
            actions_remaining -= 1
            carried_tokens += 1
            uncollected_tokens.remove(next_token)
        else:
            # Not enough actions to move and take the token
            break
    
    # After loop, drop any carried tokens if possible
    if carried_tokens > 0:
        if current_position != start_position:
            # Move back to starting position
            path_back = astar(current_position, start_position)
            if path_back is None:
                pass  # Cannot return to start
            else:
                actions_needed = len(path_back) + 1  # +1 for DROP action

                if actions_remaining >= actions_needed:
                    action_list.extend(path_back)
                    total_steps_taken += len(path_back)
                    actions_remaining -= len(path_back)
                    current_position = start_position

                    # Drop all carried tokens
                    action_list.append("DROP")
                    actions_remaining -= 1
                    total_score += carried_tokens
                    carried_tokens = 0
        elif actions_remaining >= 1:
            # Already at starting position, drop off tokens
            action_list.append("DROP")
            actions_remaining -= 1
            total_score += carried_tokens
            carried_tokens = 0

    # Calculate the net gain
    total_movement_cost = total_steps_taken * cost_per_step
    net_gain = total_score - total_movement_cost

    # You can print the net gain if needed
    # print(f"Net Gain: {net_gain}")
    
    return action_list

def parse_grid(grid_string):
    """Parse the grid string into a 2D grid and locate agent, energy tokens."""
    lines = grid_string.strip().split('\n')
    # Skip header lines and extract rows with actual grid data
    grid_lines = [line for line in lines if '|' in line]
    
    # Extract grid data
    grid = []
    for line in grid_lines:
        # Split by | and remove empty cells
        cells = line.split('|')
        row = []
        for cell in cells[1:-1]:  # Skip first and last empty elements
            if 'A' in cell:
                row.append('A')
            elif 'E' in cell:
                row.append('E')
            elif 'O' in cell:
                row.append('O')
            else:
                row.append(' ')
        grid.append(row)
    
    # Find agent position
    agent_pos = None
    energy_positions = []
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == 'A':
                agent_pos = (i, j)
            elif grid[i][j] == 'E':
                energy_positions.append((i, j))
    
    return grid, agent_pos, energy_positions

def solve(grid_str, start_pos, movement_type, carry_limit, cost_per_step, max_actions=20):
    grid, _, _ = parse_grid(grid_str)
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == 'eight'), carry_limit, cost_per_step)
    return actions

def main():
    # Example usage:
    # Define the sample grid
    sample_grid = [
        [' ', ' ', 'E', 'E', 'E', 'E', ' ', 'E', 'E', 'E', 'E'],
        [' ', ' ', 'E', 'E', 'E', ' ', ' ', ' ', ' ', 'E', ' '],
        ['E', ' ', ' ', ' ', 'E', ' ', ' ', 'E', 'E', ' ', ' '],
        ['E', 'E', 'E', 'E', ' ', 'E', 'E', 'E', ' ', 'E', 'E'],
        [' ', 'E', ' ', 'A', 'E', ' ', 'E', ' ', 'E', 'E', ' '],
        ['E', ' ', 'E', ' ', 'E', 'E', ' ', 'E', ' ', 'E', ' '],
        ['E', ' ', 'E', ' ', ' ', ' ', ' ', 'E', 'E', 'E', 'E'],
        ['E', 'E', ' ', ' ', ' ', ' ', 'E', ' ', 'E', 'E', ' '],
        ['E', ' ', 'E', 'E', 'E', ' ', ' ', ' ', 'E', 'E', ' '],
        [' ', ' ', 'E', 'E', 'E', ' ', 'E', ' ', ' ', ' ', ' '],
        [' ', 'E', 'E', ' ', 'E', 'E', ' ', 'E', ' ', 'E', 'E']
    ]

    # Starting position (4, 3)
    start_position = (4, 3)

    # Carry limit
    carry_limit = 3

    # Cost per step
    cost_per_step = 0.3  # Assuming each movement costs 1 action

    # Diagonals allowed
    diagonals_allowed = True

    # Actions to take
    actions = solve_grid(sample_grid, start_position, 20, diagonals_allowed, carry_limit, cost_per_step)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()