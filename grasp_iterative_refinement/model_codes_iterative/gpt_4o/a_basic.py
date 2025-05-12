from collections import deque
import heapq

def within_bounds(position, grid_width, grid_height):
    return 0 <= position[0] < grid_height and 0 <= position[1] < grid_width

def calculate_path_to(target_position, start_position, grid, move_cost, grid_width, grid_height, movement_type):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    directions = {
        "four": {"LEFT": (0, -1), "RIGHT": (0, 1), "UP": (-1, 0), "DOWN": (1, 0)},
        "eight": {
            "LEFT": (0, -1), "RIGHT": (0, 1), "UP": (-1, 0), "DOWN": (1, 0),
            "UPLEFT": (-1, -1), "UPRIGHT": (-1, 1),
            "DOWNLEFT": (1, -1), "DOWNRIGHT": (1, 1)
        }
    }

    current_directions = directions[movement_type]
    frontier = []
    heapq.heappush(frontier, (0, start_position))
    came_from = {start_position: None}
    cost_so_far = {start_position: 0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == target_position:
            break

        for direction, (dx, dy) in current_directions.items():
            next_position = (current[0] + dx, current[1] + dy)
            if within_bounds(next_position, grid_width, grid_height) and grid[next_position[0]][next_position[1]] != 'O':
                new_cost = cost_so_far[current] + move_cost
                if next_position not in cost_so_far or new_cost < cost_so_far[next_position]:
                    cost_so_far[next_position] = new_cost
                    priority = new_cost + heuristic(target_position, next_position)
                    heapq.heappush(frontier, (priority, next_position))
                    came_from[next_position] = (current, direction)

    path = []
    while target_position and target_position != start_position:
        target_position, direction = came_from[target_position]
        path.append(direction)
    
    path.reverse()
    return path

def find_closest_energy(current_position, grid, grid_width, grid_height, movement_type):
    directions = {
        "four": {"LEFT": (0, -1), "RIGHT": (0, 1), "UP": (-1, 0), "DOWN": (1, 0)},
        "eight": {
            "LEFT": (0, -1), "RIGHT": (0, 1), "UP": (-1, 0), "DOWN": (1, 0),
            "UPLEFT": (-1, -1), "UPRIGHT": (-1, 1),
            "DOWNLEFT": (1, -1), "DOWNRIGHT": (1, 1)
        }
    }
    
    current_directions = directions[movement_type]
    queue = deque([current_position])
    visited = set()
    visited.add(current_position)
    
    while queue:
        position = queue.popleft()
        if within_bounds(position, grid_width, grid_height) and grid[position[0]][position[1]] == 'E':
            return position
        
        for dx, dy in current_directions.values():
            next_position = (position[0] + dx, position[1] + dy)
            if (within_bounds(next_position, grid_width, grid_height) and 
                next_position not in visited and 
                grid[next_position[0]][next_position[1]] != 'O'):
                visited.add(next_position)
                queue.append(next_position)
    
    return None

def game_strategy(grid, start_position, energy_limit, move_cost, movement_type):
    start_position = tuple(start_position)
    grid_height = len(grid)
    grid_width = len(grid[0]) if grid else 0
    current_position = start_position
    energy_collected = 0
    moves = []
    
    while len(moves) < 20:
        if within_bounds(current_position, grid_width, grid_height) and grid[current_position[0]][current_position[1]] == 'E' and energy_collected < energy_limit:
            energy_collected += 1
            moves.append("TAKE")
            grid[current_position[0]][current_position[1]] = ' '
        
        if energy_collected == energy_limit:
            path_to_start = calculate_path_to(start_position, current_position, grid, move_cost, grid_width, grid_height, movement_type)
            moves.extend(path_to_start)
            current_position = start_position
            
            moves.append("DROP")
            energy_collected = 0
            
            if len(moves) >= 20:
                break
            continue

        next_position = find_closest_energy(current_position, grid, grid_width, grid_height, movement_type)

        if next_position:
            path_to_next = calculate_path_to(next_position, current_position, grid, move_cost, grid_width, grid_height, movement_type)
            moves.extend(path_to_next)
            if path_to_next:
                direction = path_to_next[-1]
                dx, dy = {
                    "LEFT": (0, -1), "RIGHT": (0, 1), "UP": (-1, 0), "DOWN": (1, 0),
                    "UPLEFT": (-1, -1), "UPRIGHT": (-1, 1),
                    "DOWNLEFT": (1, -1), "DOWNRIGHT": (1, 1)}[direction]
                current_position = (current_position[0] + dx, current_position[1] + dy)

    return moves


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
    actions = game_strategy(grid, start_pos, carry_limit, cost_per_step, movement_type)
    return actions

# Sample main function
def main():
    sample_grid = [
        [" ", " ", "E", "E", "E", "E", " ", "E", "E", "E", "E"],
        [" ", " ", "E", "E", "E", " ", " ", " ", " ", "E", " "],
        ["E", " ", " ", " ", "E", " ", " ", "E", "E", " ", " "],
        ["E", "E", "E", "E", " ", "E", "E", "E", " ", "E", "E"],
        [" ", "E", " ", "A", "E", " ", "E", " ", "E", "E", " "],
        ["E", " ", "E", " ", "E", "E", " ", "E", " ", "E", " "],
        ["E", " ", "E", " ", " ", " ", " ", "E", "E", "E", "E"],
        ["E", "E", " ", " ", " ", " ", "E", " ", "E", "E", " "],
        ["E", " ", "E", "E", "E", " ", " ", " ", "E", "E", " "],
        [" ", " ", "E", "E", "E", " ", "E", " ", " ", " ", " "],
        [" ", "E", "E", " ", "E", "E", " ", "E", " ", "E", "E"]
    ]
    start_pos = (4, 3)  # Starting position of 'A'
    energy_limit = 3    # Carrying limit for energy tokens
    move_cost = 1       # Movement cost for any direction
    movement_type = "eight"  # Can be "four" or "eight"

    moves = game_strategy(sample_grid, start_pos, energy_limit, move_cost, movement_type)
    print(moves)

if __name__ == "__main__":
    main()