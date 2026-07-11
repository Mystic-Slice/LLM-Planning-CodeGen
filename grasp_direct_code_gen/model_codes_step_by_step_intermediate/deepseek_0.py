def manhattan(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def solve_grid(grid, start_position, max_actions):
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    tokens_set = set()
    for i in range(rows):
        for j in range(cols):
            if grid[i][j] == 'E':
                tokens_set.add((i, j))
    
    current = start_position
    carried = 0
    actions = []
    remaining_actions = max_actions
    
    while remaining_actions > 0 and tokens_set:
        min_dist = float('inf')
        nearest_token = None
        for token in tokens_set:
            d = manhattan(current, token)
            if d < min_dist:
                min_dist = d
                nearest_token = token
        
        if nearest_token is None:
            break
        
        d_return = manhattan(nearest_token, start_position)
        if min_dist + d_return + 1 > remaining_actions:
            break
        
        while current != nearest_token and remaining_actions > 0:
            r, c = current
            tr, tc = nearest_token
            move_dir = None
            if r < tr:
                move_dir = "DOWN"
            elif r > tr:
                move_dir = "UP"
            elif c < tc:
                move_dir = "RIGHT"
            elif c > tc:
                move_dir = "LEFT"
            else:
                break
                
            new_r, new_c = r, c
            if move_dir == "DOWN":
                new_r = r + 1
            elif move_dir == "UP":
                new_r = r - 1
            elif move_dir == "RIGHT":
                new_c = c + 1
            elif move_dir == "LEFT":
                new_c = c - 1
                
            if new_r < 0 or new_r >= rows or new_c < 0 or new_c >= cols:
                break
                
            actions.append(move_dir)
            remaining_actions -= 1
            current = (new_r, new_c)
            
            if current in tokens_set and remaining_actions > 0:
                actions.append("TAKE")
                remaining_actions -= 1
                tokens_set.remove(current)
                carried += 1
                
        if current == nearest_token and current in tokens_set and remaining_actions > 0:
            actions.append("TAKE")
            remaining_actions -= 1
            tokens_set.remove(current)
            carried += 1
            
    while current != start_position and remaining_actions > 0:
        r, c = current
        sr, sc = start_position
        move_dir = None
        if r < sr:
            move_dir = "DOWN"
        elif r > sr:
            move_dir = "UP"
        elif c < sc:
            move_dir = "RIGHT"
        elif c > sc:
            move_dir = "LEFT"
        else:
            break
            
        new_r, new_c = r, c
        if move_dir == "DOWN":
            new_r = r + 1
        elif move_dir == "UP":
            new_r = r - 1
        elif move_dir == "RIGHT":
            new_c = c + 1
        elif move_dir == "LEFT":
            new_c = c - 1
            
        if new_r < 0 or new_r >= rows or new_c < 0 or new_c >= cols:
            break
            
        actions.append(move_dir)
        remaining_actions -= 1
        current = (new_r, new_c)
        
        if current in tokens_set and remaining_actions > 0:
            actions.append("TAKE")
            remaining_actions -= 1
            tokens_set.remove(current)
            carried += 1
            
    if current == start_position and carried > 0 and remaining_actions > 0:
        actions.append("DROP")
        remaining_actions -= 1
        carried = 0
        
    return actions

    
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
    actions = solve_grid(grid, tuple(start_pos), max_actions)
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
    actions = solve_grid(sample_grid, start_position, max_actions=20)

    # Output the actions
    print("Actions to take:", len(actions))
    print(actions)

if __name__ == "__main__":
    main()