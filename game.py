import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def generate_board(mines):
    positions = random.sample(range(25), mines)
    board = ['💎'] * 25
    for i in positions:
        board[i] = '💣'
    return board, positions

def get_button_grid(revealed, board):
    keyboard = []
    for row in range(5):
        row_buttons = []
        for col in range(5):
            idx = row * 5 + col
            text = board[idx] if idx in revealed else "⬜"
            row_buttons.append(InlineKeyboardButton(text, callback_data=f"reveal:{idx}"))
        keyboard.append(row_buttons)
    return InlineKeyboardMarkup(keyboard)
