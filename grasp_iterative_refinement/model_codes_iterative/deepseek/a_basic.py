from collections import deque
import math

# Helper function to compute the shortest path using BFS
def compute_shortest_path(start, end, movement_type, grid, obstacles):
    rows, cols = len(grid), len(grid[0])
    directions = []
    if movement_type == "four":
        directions = [(-1, 0, "UP"), (1, 0, "DOWN"), (0, -1, "LEFT"), (0, 1, "RIGHT")]
    elif movement_type == "eight":
        directions = [
            (-1, 0, "UP"), (1, 0, "DOWN"), (0, -1, "LEFT"), (0, 1, "RIGHT"),
            (-1, -1, "UPLEFT"), (-1, 1, "UPRIGHT"), (1, -1, "DOWNLEFT"), (1, 1, "DOWNRIGHT")
        ]
    
    queue = deque()
    queue.append((start[0], start[1], []))  # (row, col, path)
    visited = set()
    visited.add((start[0], start[1]))
    
    while queue:
        row, col, path = queue.popleft()
        if (row, col) == end:
            return path, len(path)  # Return path and cost (number of steps)
        for dr, dc, move in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < rows and 0 <= new_col < cols:
                if (new_row, new_col) not in visited and grid[new_row][new_col] != 'O':
                    visited.add((new_row, new_col))
                    queue.append((new_row, new_col, path + [move]))
    return None, math.inf  # No path found

# Main algorithm
def solve_game(grid, movement_type, carry_limit, max_actions):
    # Find starting position and list of energy tokens
    start_pos = None
    e_list = []
    for i in range(len(grid)):
        for j in range(len(grid[i])):
            if grid[i][j] == 'A':
                start_pos = (i, j)
            elif grid[i][j] == 'E':
                e_list.append((i, j))
    
    if not start_pos:
        return []  # No starting position found
    
    remaining_actions = max_actions
    actions = []
    current_pos = start_pos
    
    while remaining_actions > 0 and e_list:
        best_group = None
        best_actions_used = math.inf
        best_collected = 0
        
        # Check groups from carry_limit down to 1
        for group_size in range(min(carry_limit, len(e_list)), 0, -1):
            # Sort E's by distance to start_pos
            sorted_es = sorted(e_list, key=lambda e: abs(e[0] - start_pos[0]) + abs(e[1] - start_pos[1]))
            for i in range(len(sorted_es) - group_size + 1):
                candidate_group = sorted_es[i:i + group_size]
                total_moves = []
                temp_pos = start_pos
                total_cost = 0
                valid = True
                
                for e in candidate_group:
                    path, cost = compute_shortest_path(temp_pos, e, movement_type, grid, obstacles=set())
                    if not path:
                        valid = False
                        break
                    total_moves.extend(path)
                    total_cost += cost
                    temp_pos = e
                
                if valid:
                    # Return to start after collecting all
                    return_path, return_cost = compute_shortest_path(temp_pos, start_pos, movement_type, grid, obstacles=set())
                    if return_path:
                        total_cost += return_cost
                        total_actions = total_cost + group_size + 1  # group_size TAKEs + 1 DROP
                        if total_actions <= remaining_actions and (group_size / total_actions) > (best_collected / best_actions_used):
                            best_group = candidate_group
                            best_actions_used = total_actions
                            best_collected = group_size
                            break  # Prefer larger groups first
        
        if best_group:
            # Collect best_group
            temp_pos = start_pos
            for e in best_group:
                path_to_e, _ = compute_shortest_path(temp_pos, e, movement_type, grid, obstacles=set())
                actions.extend(path_to_e)
                actions.append("TAKE")
                remaining_actions -= (len(path_to_e) + 1)
                temp_pos = e
            path_back, _ = compute_shortest_path(temp_pos, start_pos, movement_type, grid, obstacles=set())
            actions.extend(path_back)
            actions.append("DROP")
            remaining_actions -= (len(path_back) + 1)
            e_list = [e for e in e_list if e not in best_group]
            current_pos = start_pos
        else:
            # Collect closest single E
            closest_e = None
            min_cost = math.inf
            for e in e_list:
                path_to_e, cost_to = compute_shortest_path(start_pos, e, movement_type, grid, obstacles=set())
                path_back, cost_back = compute_shortest_path(e, start_pos, movement_type, grid, obstacles=set())
                if not path_to_e or not path_back:
                    continue
                total_cost = cost_to + cost_back + 2  # +TAKE and DROP
                if total_cost < min_cost:
                    closest_e = e
                    min_cost = total_cost
            if closest_e and min_cost <= remaining_actions:
                path_to_e, _ = compute_shortest_path(start_pos, closest_e, movement_type, grid, obstacles=set())
                actions.extend(path_to_e)
                actions.append("TAKE")
                path_back, _ = compute_shortest_path(closest_e, start_pos, movement_type, grid, obstacles=set())
                actions.extend(path_back)
                actions.append("DROP")
                remaining_actions -= (len(path_to_e) + len(path_back) + 2)
                e_list.remove(closest_e)
                current_pos = start_pos
            else:
                break  # No feasible actions left
    
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
    actions = solve_game(grid, movement_type, carry_limit, max_actions)
    return actions

if __name__ == "__main__":
    # Example usage
    grid = [
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

    movement_type = "four"  # 4-direction movement
    carry_limit = 3    # Can carry up to 3 energy tokens at a time
    max_actions = 20   # Maximum number of actions

    actions = solve_game(grid, movement_type, carry_limit, max_actions)
    print("Actions taken:", actions)
    print(len(actions))