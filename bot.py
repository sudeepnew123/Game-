import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, START_BALANCE, BONUS_AMOUNT, ADMIN_ID
from game import generate_board, get_button_grid

user_data = {}
logging.basicConfig(level=logging.INFO)

def get_cashout_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton("💸 Cashout", callback_data="cashout")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in user_data:
        user_data[uid] = {"balance": START_BALANCE, "game": None}
    await update.message.reply_text(f"Welcome to Mines Game Bot!\nBalance: ₹{user_data[uid]['balance']}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎮 *Mines Game Bot Help* 🎮\n\n"
        "/start - Initialize your account\n"
        "/help - Show this help message\n"
        "/balance - Check your balance\n"
        "/mine <amount> <mines> - Start a new game\n"
        "/bonus - Claim daily bonus\n"
        "/gift <amount> (in reply) - Gift Hiwa to another player\n"
        "\n*Admin Commands:*\n"
        "/broadcast <msg> - Send message to all users\n"
        "/resetdata - Reset all data\n"
        "/setbalance <user_id> <amount> - Set user balance"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Your balance: ₹{user_data.get(uid, {}).get('balance', 0)}")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_data.setdefault(uid, {"balance": START_BALANCE, "game": None})
    user_data[uid]["balance"] += BONUS_AMOUNT
    await update.message.reply_text(f"You received ₹{BONUS_AMOUNT} bonus!")

async def mine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    if len(args) != 2:
        return await update.message.reply_text("Usage: /mine <amount> <mines>")

    try:
        amount = int(args[0])
        mines = int(args[1])
    except:
        return await update.message.reply_text("Invalid input.")

    if not 1 <= mines < 25:
        return await update.message.reply_text("Mines must be between 1 and 24.")
    if user_data[uid]["balance"] < amount:
        return await update.message.reply_text("Insufficient balance.")

    board, mine_positions = generate_board(mines)
    user_data[uid]["game"] = {
        "amount": amount,
        "mines": mines,
        "board": board,
        "mine_positions": mine_positions,
        "revealed": [],
        "status": "active"
    }
    user_data[uid]["balance"] -= amount

    await update.message.reply_text(
        f"Game started with ₹{amount} and {mines} mines.\nClick to reveal gems!",
        reply_markup=get_button_grid([], board)
    )

async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    game = user_data[uid].get("game")

    if not game or game["status"] != "active":
        return await update.message.reply_text("No active game.")
    revealed = len(game["revealed"])
    if revealed == 0:
        return await update.message.reply_text("Reveal at least 1 cell to cash out!")

    reward = int(game["amount"] + game["amount"] * (revealed * 0.3))
    user_data[uid]["balance"] += reward
    game["status"] = "cashed"

    await update.message.reply_text(f"Cashout successful! You won ₹{reward}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    if data == "cashout":
        return await cashout(update, context)

    if not data.startswith("reveal:"):
        return

    index = int(data.split(":")[1])
    game = user_data.get(uid, {}).get("game")
    if not game or game["status"] != "active":
        return await query.edit_message_text("No active game.")

    if index in game["revealed"]:
        return

    if game["board"][index] == '💣':
        game["revealed"].append(index)
        game["status"] = "lost"
        return await query.edit_message_text(
            "BOOM! You hit a bomb 💣\nGame over.",
            reply_markup=get_button_grid(game["revealed"], game["board"])
        )

    game["revealed"].append(index)

    await query.edit_message_reply_markup(
        reply_markup=get_button_grid(game["revealed"], game["board"])
    )

    if len(game["revealed"]) >= 2:
        await query.message.reply_text("You can cash out now!", reply_markup=get_cashout_markup())

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1 or not update.message.reply_to_message:
        return await update.message.reply_text("Reply to a user and use: /gift <amount>")

    try:
        amount = int(context.args[0])
    except:
        return await update.message.reply_text("Invalid amount.")

    sender = update.effective_user.id
    receiver = update.message.reply_to_message.from_user.id

    if user_data.get(sender, {}).get("balance", 0) < amount:
        return await update.message.reply_text("Insufficient balance.")

    user_data.setdefault(receiver, {"balance": START_BALANCE, "game": None})
    user_data[sender]["balance"] -= amount
    user_data[receiver]["balance"] += amount

    await update.message.reply_text(f"Gifted ₹{amount} Hiwa!")

# Admin Commands

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    for uid in user_data:
        try:
            await context.bot.send_message(uid, f"[Broadcast]\n{msg}")
        except:
            continue
    await update.message.reply_text("Broadcast sent.")

async def setbalance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
    except:
        return await update.message.reply_text("Usage: /setbalance <user_id> <amount>")

    user_data.setdefault(uid, {"balance": START_BALANCE, "game": None})
    user_data[uid]["balance"] = amount
    await update.message.reply_text("Balance set.")

async def resetdata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        user_data.clear()
        await update.message.reply_text("All data reset.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("mine", mine))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("resetdata", resetdata))
    app.add_handler(CommandHandler("setbalance", setbalance))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot is running...")
    app.run_polling()
