def get_game_intro_prompt(movement_dirs, carry_limit, cost_of_step):
    GAME_INTRO_PROMPT = f"""
    You are a game playing agent. This game involves a 2-D grid which you have to traverse and get as many energy tokens as possible within 20 actions and put the collected energy back in the cell where you started. Positions in the grid will be in the format [row, column] and the numbering starts from zero. [0, 0] denotes top left corner. You are denoted by the letter 'A', the energy tokens are denoted by the letter 'E' and obstacles if any are denoted by the letter 'O'. You can move in {
        '4 directions: "LEFT", "RIGHT", "UP" and "DOWN"' 
        if movement_dirs == 'four' 
        else '8 directions: "LEFT", "RIGHT", "UP", "DOWN", "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT"'
    }. You can also perform two additional actions on the cell you are in currently: "TAKE" (take the energy in the current cell) and "DROP" (drop the energy you are carrying on to the current cell). {f"At any point you can carry only {carry_limit} energy tokens." if carry_limit > 0 else ""} {f"Each step costs you {cost_of_step} energy tokens." if cost_of_step > 0 else ""} Your task is to collect as many energy tokens as possible and drop them back in the cell where you started. The energy tokens you are holding onto do not count towards your score. Only the tokens dropped or already present in your starting cell count towards your score.
    """
    return GAME_INTRO_PROMPT

def get_final_instructions(movement_dirs, carry_limit, cost_of_step):
    FINAL_INSTRUCTIONS = f"""
    Your final answer must be a list of actions where each action is one of the following:
    - a direction to move in {'("LEFT", "RIGHT", "UP", "DOWN")' if movement_dirs == 'four' else '("LEFT", "RIGHT", "UP", "DOWN", "UPLEFT", "UPRIGHT", "DOWNLEFT", "DOWNRIGHT")'}
    - "TAKE" to take the energy token
    - "DROP" to drop the energy token

    Make sure to check the following in your final answer:
    - You must not move out of the grid.
    - You must not take energy from a cell that does not have energy.
    - You must not use more than 20 actions (includes movement, take and drop). 
    - You must not use any other actions than the ones specified above.
    - After all the actions, only the tokens dropped or already present in your starting cell count towards your score. Tokens you are holding onto do not count.
    {f"- At any point you can carry only {carry_limit} energy tokens" if carry_limit > 0 else ""}
    {f"- Each step costs you {cost_of_step} energy tokens" if cost_of_step > 0 else ""}
    Adhering to these rules is VERY IMPORTANT.

    Think about this before writing your output. Use only xml tags for formatting your output. Do not use json.
    """
    return FINAL_INSTRUCTIONS


def get_plain_prompt(movement_dirs, carry_limit, cost_of_step):
    PLAIN_PROMPT = f"""
    {get_game_intro_prompt(movement_dirs, carry_limit, cost_of_step)}

    And finally when you are ready to give your final answer, you can output in this form:
    <final_answer>
        ["RIGHT", "TAKE", ..., "DROP"]
    </final_answer>

    {get_final_instructions(movement_dirs, carry_limit, cost_of_step)}
    """
    return PLAIN_PROMPT