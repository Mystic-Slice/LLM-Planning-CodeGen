UNLOCK_PROMPT = """
You are a game-playing agent in a 2D grid-based environment. Your objective is to unlock a `DOOR`.

### Environment Description:
- The grid is represented as a 2D array, with the top-left corner at `[0][0]`. Each cell can contain one of the following objects:
  - `WALL`, `DOOR`, `KEY`, `AGENT` (You), or an empty string (`""`).
- You start in a specific cell facing one of four directions: `UP`, `DOWN`, `LEFT`, or `RIGHT` (this will be provided).
- Two rooms are separated by `WALL`s, with a single `DOOR` connecting them.

### Actions:
You can perform the following actions:
- `LEFT`: Turn 90° to the left.
- `RIGHT`: Turn 90° to the right.
- `MOVE`: Move one step forward in the direction you're facing.
- `PICKUP`: Pick up an object located in the cell *directly in front* of you.
- `DROP`: Drop the object you're holding into the cell *directly in front* of you.
- `UNLOCK`: Unlock the door located *directly in front* of you, if you are holding the `KEY`.

### Rules:
- Before picking up a new object, you must `DROP` the one you’re holding into an **empty adjacent cell** (no `WALL`, `DOOR`, or object).
- You can only `PICKUP` or `UNLOCK` if:
  - The target cell is directly in front of you (i.e., one step in the direction you're facing).
  - You are adjacent to that cell.
- You cannot enter a cell that contains any object unless it’s been picked up.

### Input:
You will be provided:
- The complete 2D grid as a list of lists (example below).
- Your starting facing direction.

### Output:
Your output should be a list of actions in the following format:
<actions>
    ["LEFT", "RIGHT", "MOVE", ...]
</actions>
Make sure to use <actions> and </actions> XML tags for your output.

Below is a sample input grid and starting direction.

<grid>
{grid}
</grid>
<start_direction>
{start_direction}
</start_direction>
"""

DOOR_KEY_PROMPT = """
You are a game-playing agent in a 2D grid-based environment. Your objective is to unlock a `DOOR` and reach a `GOAL` which is located in a different room than the one you start in.

### Environment Description:
- The grid is represented as a 2D array, with the top-left corner at `[0][0]`. Each cell can contain one of the following objects:
  - `WALL`, `DOOR`, `KEY`, `GOAL`, `AGENT` (You), or an empty string (`""`).
- You start in a specific cell facing one of four directions: `UP`, `DOWN`, `LEFT`, or `RIGHT` (this will be provided).
- Two rooms are separated by `WALL`s, with a single `DOOR` connecting them.

### Actions:
You can perform the following actions:
- `LEFT`: Turn 90° to the left.
- `RIGHT`: Turn 90° to the right.
- `MOVE`: Move one step forward in the direction you're facing.
- `PICKUP`: Pick up an object located in the cell *directly in front* of you.
- `DROP`: Drop the object you're holding into the cell *directly in front* of you.
- `UNLOCK`: Unlock the door located *directly in front* of you, if you are holding the `KEY`.

### Rules:
- You can only `PICKUP` or `UNLOCK` if:
  - The target cell is directly in front of you (i.e., one step in the direction you're facing).
  - You are adjacent to that cell.
- You cannot enter a cell that contains any object unless it’s been picked up.
- You must stand on the goal cell to complete the game.

### Input:
You will be provided:
- The complete 2D grid as a list of lists (example below).
- Your starting facing direction.

### Output:
Your output should be a list of actions in the following format:
<actions>
    ["LEFT", "RIGHT", "MOVE", ...]
</actions>
Make sure to use <actions> and </actions> XML tags for your output.

Below is a sample input grid and starting direction.

<grid>
{grid}
</grid>
<start_direction>
{start_direction}
</start_direction>
"""

UNLOCK_PICKUP_PROMPT = """
You are a game-playing agent in a 2D grid-based environment. Your objective is to pick up a `BOX` that is located in a different room than your starting position.

### Environment Description:
- The grid is represented as a 2D array, with the top-left corner at `[0][0]`. Each cell can contain one of the following objects:
  - `WALL`, `DOOR`, `KEY`, `BOX`, `AGENT` (You), or an empty string (`""`).
- You start in a specific cell facing one of four directions: `UP`, `DOWN`, `LEFT`, or `RIGHT` (this will be provided).
- Two rooms are separated by `WALL`s, with a single `DOOR` connecting them.

### Actions:
You can perform the following actions:
- `LEFT`: Turn 90° to the left.
- `RIGHT`: Turn 90° to the right.
- `MOVE`: Move one step forward in the direction you're facing.
- `PICKUP`: Pick up an object located in the cell *directly in front* of you.
- `DROP`: Drop the object you're holding into the cell *directly in front* of you.
- `UNLOCK`: Unlock the door located *directly in front* of you, if you are holding the `KEY`.

### Rules:
- You may only hold **one object at a time** (`KEY` or `BOX`).
- Before picking up a new object, you must `DROP` the one you’re holding into an **empty adjacent cell** (no `WALL`, `DOOR`, or object).
- You can only `PICKUP` or `UNLOCK` if:
  - The target cell is directly in front of you (i.e., one step in the direction you're facing).
  - You are adjacent to that cell.
- You cannot:
  - Enter a cell that contains any object unless it’s been picked up or is a now-empty `DOOR` cell.
  - Drop objects into non-empty cells or into a `WALL` or `DOOR` cell.
  - Pick up an object (e.g. `BOX`) when you are already holding one (e.g. `KEY`).

### Input:
You will be provided:
- The complete 2D grid as a list of lists (example below).
- Your starting facing direction.

### Output:
Your output should be a list of actions in the following format:
<actions>
    ["LEFT", "RIGHT", "MOVE", ...]
</actions>
Make sure to use <actions> and </actions> XML tags for your output.

Below is a sample input grid and starting direction.

<grid>
{grid}
</grid>
<start_direction>
{start_direction}
</start_direction>
"""