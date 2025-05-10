def solve_grid(grid, start_position, max_actions, is_diagonals_allowed):
    """
    Solves the energy collection game with optional diagonal movements.

    Parameters:
    - grid: A 2D list representing the grid. Each cell can be:
        - 'E' for an energy token
        - ' ' for an empty cell
        - 'A' for the agent's starting position
    - start_position: A tuple (x, y) representing the agent's starting position.
    - max_actions: The maximum number of actions the agent can perform.
    - is_diagonals_allowed: Boolean indicating if diagonal moves are allowed.

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
    
    from collections import deque

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

            if is_diagonals_allowed:
                # Determine diagonal movement
                if dx > 0 and dy > 0:
                    path.append("DOWNRIGHT")
                    current_x += 1
                    current_y += 1
                    move_made = True
                elif dx > 0 and dy < 0:
                    path.append("DOWNLEFT")
                    current_x += 1
                    current_y -= 1
                    move_made = True
                elif dx < 0 and dy > 0:
                    path.append("UPRIGHT")
                    current_x -= 1
                    current_y += 1
                    move_made = True
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

    # Find positions of all energy tokens (excluding starting cell)
    uncollected_tokens = set()
    for x in range(grid_height):
        for y in range(grid_width):
            cell = grid[x][y]
            if cell == 'E':
                pos = (x, y)
                if pos != start_position:
                    uncollected_tokens.add(pos)
            elif cell == 'A':
                # Ensure the starting position is updated if 'A' is in the grid
                start_position = (x, y)
                current_position = start_position

    # Include any tokens at the starting position to the score
    if grid[start_position[0]][start_position[1]] == 'E':
        total_score += 1

    # Main loop
    while actions_remaining > 0:

        # Calculate the cost to return to starting position and drop tokens
        return_cost = calculate_distance(current_position, start_position)
        drop_action_cost = 1 if carried_tokens > 0 else 0
        total_return_cost = return_cost + drop_action_cost

        # If we must return now
        if actions_remaining <= total_return_cost:
            if carried_tokens > 0 and current_position != start_position:
                # Move back to starting position
                path_to_start = find_path(current_position, start_position)
                action_list.extend(path_to_start)
                actions_remaining -= number_of_steps_in(path_to_start)
                current_position = start_position

                # Drop all carried tokens
                if actions_remaining > 0:
                    action_list.append("DROP")
                    actions_remaining -= 1
                    total_score += carried_tokens
                    carried_tokens = 0
            break  # No actions left or must wait to accumulate actions

        # Find the nearest token we can collect and return
        reachable_tokens = []
        for token_pos in uncollected_tokens:
            to_token_cost = calculate_distance(current_position, token_pos)
            take_action_cost = 1  # Cost to "TAKE"
            to_home_cost = calculate_distance(token_pos, start_position)
            total_cost = to_token_cost + take_action_cost + to_home_cost + drop_action_cost

            if actions_remaining >= total_cost:
                reachable_tokens.append((token_pos, total_cost))

        # If no reachable tokens, return to start if carrying tokens
        if not reachable_tokens:
            if carried_tokens > 0 and current_position != start_position:
                # Move back to starting position
                path_to_start = find_path(current_position, start_position)
                action_list.extend(path_to_start)
                actions_remaining -= number_of_steps_in(path_to_start)
                current_position = start_position

                # Drop all carried tokens
                if actions_remaining > 0:
                    action_list.append("DROP")
                    actions_remaining -= 1
                    total_score += carried_tokens
                    carried_tokens = 0
            break

        # Select the nearest reachable token
        next_token = min(reachable_tokens, key=lambda x: calculate_distance(current_position, x[0]))[0]

        # Move to the next token
        path_to_token = find_path(current_position, next_token)
        action_list.extend(path_to_token)
        actions_remaining -= number_of_steps_in(path_to_token)
        current_position = next_token

        # Take the energy token
        if actions_remaining > 0:
            action_list.append("TAKE")
            actions_remaining -= 1
            carried_tokens += 1
            uncollected_tokens.remove(next_token)
        else:
            break

    # After loop, drop any carried tokens if possible
    if carried_tokens > 0:
        if current_position != start_position and actions_remaining >= (calculate_distance(current_position, start_position) + 1):
            # Move back to starting position
            path_to_start = find_path(current_position, start_position)
            action_list.extend(path_to_start)
            actions_remaining -= number_of_steps_in(path_to_start)
            current_position = start_position

            # Drop all carried tokens
            if actions_remaining > 0:
                action_list.append("DROP")
                actions_remaining -= 1
                total_score += carried_tokens
                carried_tokens = 0
        elif current_position == start_position and actions_remaining > 0:
            # Drop all carried tokens
            action_list.append("DROP")
            actions_remaining -= 1
            total_score += carried_tokens
            carried_tokens = 0

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
    actions = solve_grid(grid, tuple(start_pos), max_actions, (movement_type == 'eight'))
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
    actions = solve_grid(sample_grid, start_position, 20, diagonals_allowed)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()