import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Bosqichlar
ADD_KEY_ID, ADD_KEY, CHECK_KEY_ID, CHECK_KEY = range(4)

# SQLite bazani yaratish
conn = sqlite3.connect("test_bot.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS test_keys (test_id TEXT PRIMARY KEY, answer_key TEXT)''')
conn.commit()

# Asosiy menyu tugmalari
main_menu_keyboard = [['Testni kalitini qo\'shish', 'Testni kalitini tekshirish'], ['Orqaga qaytish']]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu alaykum! Botga xush kelibsiz!", reply_markup=main_menu_markup)

async def add_key_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Test ID sini kiriting:")
    return ADD_KEY_ID

async def add_key_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['test_id'] = update.message.text.strip()
    await update.message.reply_text("Test kalitini yuboring (masalan: A,B,C,D):")
    return ADD_KEY

async def save_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = context.user_data['test_id']
    answer_key = update.message.text.strip()

    try:
        cursor.execute("INSERT INTO test_keys (test_id, answer_key) VALUES (?, ?)", (test_id, answer_key))
        conn.commit()
        await update.message.reply_text("Test kaliti saqlandi!", reply_markup=main_menu_markup)
    except sqlite3.IntegrityError:
        await update.message.reply_text("Bu test ID uchun kalit mavjud. Yangi ID kiriting.", reply_markup=main_menu_markup)

    return ConversationHandler.END

async def check_key_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Test ID sini kiriting:")
    return CHECK_KEY_ID

async def check_key_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['test_id'] = update.message.text.strip()
    await update.message.reply_text("Test javoblarini yuboring (masalan: A,B,C,D):")
    return CHECK_KEY

async def validate_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    test_id = context.user_data['test_id']
    user_answers = update.message.text.strip().split(',')
    
    cursor.execute("SELECT answer_key FROM test_keys WHERE test_id = ?", (test_id,))
    result = cursor.fetchone()

    if not result:
        await update.message.reply_text("Test ID topilmadi!", reply_markup=main_menu_markup)
        return ConversationHandler.END

    correct_key = result[0].split(',')
    correct_count = sum(1 for a, b in zip(correct_key, user_answers) if a.strip() == b.strip())
    wrong_count = len(correct_key) - correct_count

    await update.message.reply_text(
        f"To'g'ri javoblar: {correct_count}\nXato javoblar: {wrong_count}",
        reply_markup=main_menu_markup
    )
    return ConversationHandler.END

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Asosiy menyuga qaytdingiz.", reply_markup=main_menu_markup)
    return ConversationHandler.END

def main():
    TOKEN = "7657643788:AAGPpYPLt6j2viW0mQCDB-V1Lts6kxArocY"  # Bu yerga o'z tokeningizni kiriting
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(Testni kalitini qo\'shish)$'), add_key_start),
                      MessageHandler(filters.Regex('^(Testni kalitini tekshirish)$'), check_key_start)],
        states={
            ADD_KEY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_id)],
            ADD_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_key)],
            CHECK_KEY_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_key_id)],
            CHECK_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, validate_key)],
        },
        fallbacks=[MessageHandler(filters.Regex('^(Orqaga qaytish)$'), back_to_main)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
