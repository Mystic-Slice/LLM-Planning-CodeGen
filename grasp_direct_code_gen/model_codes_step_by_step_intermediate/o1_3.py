def solve_grid(grid, start_position, max_actions, is_diagonals_allowed, carry_limit, cost_per_step):
    """
    Solves the energy collection game with optional diagonal movements, carry limit, and cost per step.
    
    Parameters:
    - grid: A 2D list representing the grid. Each cell can be:
        - 'E' for an energy token
        - ' ' for an empty cell
        - 'A' for the agent's starting position
    - start_position: A tuple (x, y) representing the agent's starting position.
    - max_actions: The maximum number of actions the agent can perform.
    - is_diagonals_allowed: Boolean indicating if diagonal moves are allowed.
    - carry_limit: The maximum number of energy tokens the agent can carry.
    - cost_per_step: The cost associated with a step in any direction.
    
    Returns:
    - A list of actions representing the agent's moves.
    """
    # Define the possible moves
    moves = {
        "UP": (-1, 0),
        "DOWN": (1, 0),
        "LEFT": (0, -1),
        "RIGHT": (0, 1)
    }
    
    if is_diagonals_allowed:
        # Add diagonal moves
        moves.update({
            "UPLEFT": (-1, -1),
            "UPRIGHT": (-1, 1),
            "DOWNLEFT": (1, -1),
            "DOWNRIGHT": (1, 1)
        })
    
    # Helper function: Calculate distance between two positions
    def calculate_distance(pos1, pos2):
        dx = abs(pos1[0] - pos2[0])
        dy = abs(pos1[1] - pos2[1])
        if is_diagonals_allowed:
            # Chebyshev distance
            return max(dx, dy)
        else:
            # Manhattan distance
            return dx + dy

    # Helper function: Find path from start to end position
    def find_path(start, end):
        # Generate path using diagonal moves if allowed
        path = []
        current_x, current_y = start
        end_x, end_y = end

        while (current_x, current_y) != (end_x, end_y):
            move_made = False
            dx = end_x - current_x
            dy = end_y - current_y

            if is_diagonals_allowed and dx != 0 and dy != 0:
                # Determine diagonal movement
                if dx > 0 and dy > 0:
                    path.append("DOWNRIGHT")
                    current_x += 1
                    current_y += 1
                elif dx > 0 and dy < 0:
                    path.append("DOWNLEFT")
                    current_x += 1
                    current_y -= 1
                elif dx < 0 and dy > 0:
                    path.append("UPRIGHT")
                    current_x -= 1
                    current_y += 1
                elif dx < 0 and dy < 0:
                    path.append("UPLEFT")
                    current_x -= 1
                    current_y -= 1
                move_made = True

            if not move_made:
                # If no diagonal move made, move horizontally or vertically
                if dx > 0:
                    path.append("DOWN")
                    current_x += 1
                elif dx < 0:
                    path.append("UP")
                    current_x -= 1
                elif dy > 0:
                    path.append("RIGHT")
                    current_y += 1
                elif dy < 0:
                    path.append("LEFT")
                    current_y -= 1

        return path

    # Helper function: Counts the number of steps in a path
    def number_of_steps_in(path):
        return len(path)

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
                # Move back to starting position
                path_to_start = find_path(current_position, start_position)
                actions_needed = number_of_steps_in(path_to_start) + 1  # +1 for DROP action

                if actions_remaining >= actions_needed:
                    action_list.extend(path_to_start)
                    total_steps_taken += number_of_steps_in(path_to_start)
                    actions_remaining -= number_of_steps_in(path_to_start)
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
        return_cost = calculate_distance(current_position, start_position)
        drop_action_cost = 1 if carried_tokens > 0 else 0
        total_return_cost = return_cost + drop_action_cost

        # If we must return now due to action limit
        if actions_remaining <= total_return_cost:
            if carried_tokens > 0 and current_position != start_position:
                # Move back to starting position
                path_to_start = find_path(current_position, start_position)
                actions_needed = number_of_steps_in(path_to_start) + drop_action_cost

                if actions_remaining >= actions_needed:
                    action_list.extend(path_to_start)
                    total_steps_taken += number_of_steps_in(path_to_start)
                    actions_remaining -= number_of_steps_in(path_to_start)
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

            to_token_cost = calculate_distance(current_position, token_pos)
            take_action_cost = 1  # Cost for "TAKE"
            to_home_cost = calculate_distance(token_pos, start_position)
            drop_action_cost = 1 if carried_tokens + 1 >= carry_limit or carried_tokens + 1 >= 1 else 0

            total_movement_steps = to_token_cost + to_home_cost
            movement_cost = total_movement_steps * cost_per_step
            total_actions_needed = to_token_cost + take_action_cost + to_home_cost + drop_action_cost

            # Net gain is the token value minus movement cost
            net_gain = 1 - movement_cost

            # Ensure we have enough actions
            if actions_remaining >= total_actions_needed and net_gain > 0:
                token_options.append((token_pos, net_gain))

        if not token_options:
            # No tokens with positive net gain or reachable within remaining actions
            if carried_tokens > 0 and current_position != start_position:
                # Return to start and drop off tokens
                path_to_start = find_path(current_position, start_position)
                actions_needed = number_of_steps_in(path_to_start) + drop_action_cost

                if actions_remaining >= actions_needed:
                    action_list.extend(path_to_start)
                    total_steps_taken += number_of_steps_in(path_to_start)
                    actions_remaining -= number_of_steps_in(path_to_start)
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
        next_token = max(token_options, key=lambda x: x[1])[0]

        # Move to the next token
        path_to_token = find_path(current_position, next_token)
        actions_needed = number_of_steps_in(path_to_token) + 1  # +1 for TAKE action

        if actions_remaining >= actions_needed:
            # Move and take the token
            action_list.extend(path_to_token)
            total_steps_taken += number_of_steps_in(path_to_token)
            actions_remaining -= number_of_steps_in(path_to_token)
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
            path_to_start = find_path(current_position, start_position)
            actions_needed = number_of_steps_in(path_to_start) + 1  # +1 for DROP action

            if actions_remaining >= actions_needed:
                action_list.extend(path_to_start)
                total_steps_taken += number_of_steps_in(path_to_start)
                actions_remaining -= number_of_steps_in(path_to_start)
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