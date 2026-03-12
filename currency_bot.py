import asyncio
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8693832078:AAF4yo-bl9GubeR4ydiSIi1Y8C3HcRbQFPU"

# --- Клавиатура с одной кнопкой ---
reply_keyboard = [["Курсы обмена"]]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

# --- Загрузка курсов из crypto_rates.json (обновляется скриптом с Rapira) ---
def load_crypto_rates():
    try:
        with open('crypto_rates.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"last_update": "файл с данными не найден", "rates": {}}
    except json.JSONDecodeError:
        return {"last_update": "ошибка чтения файла", "rates": {}}

# --- Формирование сообщения с курсами из Rapira ---
def get_exchange_message():
    data = load_crypto_rates()
    last_update = data['last_update']
    rates = data.get('rates', {})

    usd = rates.get('USD', {})
    usdt = rates.get('USDT', {})

    usd_buy = usd.get('buy', 'N/A')
    usd_sell = usd.get('sell', 'N/A')
    usdt_buy_usd = usdt.get('buy_usd', 'N/A')
    usdt_sell_usd = usdt.get('sell_usd', 'N/A')
    usdt_buy_rub = usdt.get('buy_rub', 'N/A')
    usdt_sell_rub = usdt.get('sell_rub', 'N/A')

    def fmt(val):
        if val == 'N/A':
            return val
        return f"{val:.2f}"

    message = (
        f"📊 **Курсы покупки/продажи** (обновлено: {last_update})\n"
        f"🌐 Сеть: TRC20\n\n"
        "**Вы хотите купить:**\n"
        f"USD = {fmt(usd_buy)} руб.\n"
        f"USDT = {fmt(usdt_buy_usd)} USD\n"
        f"USDT = {fmt(usdt_buy_rub)} руб.\n\n"
        "**Вы хотите продать:**\n"
        f"USD = {fmt(usd_sell)} руб.\n"
        f"USDT = {fmt(usdt_sell_usd)} USD\n"
        f"USDT = {fmt(usdt_sell_rub)} руб."
    )
    return message

# --- Обработчики команд и сообщений ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот курсов обменника.\n"
        "Нажмите кнопку ниже, чтобы получить актуальные курсы.",
        reply_markup=markup
    )

async def exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Загружаю курсы...")
    msg = get_exchange_message()
    await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Курсы обмена":
        await exchange(update, context)
    else:
        # Если пользователь отправил что-то другое – игнорируем или отвечаем вежливо
        await update.message.reply_text("Пожалуйста, используйте кнопку «Курсы обмена».", reply_markup=markup)

# --- Главная функция ---
async def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("exchange", exchange))  # оставим для совместимости
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("✅ Бот запущен. Нажмите кнопку 'Курсы обмена' в Telegram.")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())