import random

def generate_board(mines):
    board = ['💎'] * 25
    mine_positions = random.sample(range(25), mines)
    for pos in mine_positions:
        board[pos] = '💣'
    return board, mine_positions

def get_button_grid(revealed, board):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = []
    for i in range(5):
        row = []
        for j in range(5):
            index = i * 5 + j
            text = board[index] if index in revealed else '▫️'
            callback_data = f"reveal:{index}"
            row.append(InlineKeyboardButton(text, callback_data=callback_data))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)
