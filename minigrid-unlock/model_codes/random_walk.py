import numpy as np
ALLOWED_ACTIONS = ["LEFT", "RIGHT", "MOVE", "PICKUP", "DROP", "UNLOCK"]

NUM_MOVES = 100

def solve(grid, start_direction):
    return np.random.choice(ALLOWED_ACTIONS, NUM_MOVES).tolist()

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