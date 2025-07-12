import os
import random
import json
import pandas as pd
from datetime import datetime
from telegram import (
    Update,
    LabeledPrice,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    MenuButtonWebApp
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    PreCheckoutQueryHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)

TOKEN = "8195776605:AAHS2WJHJ9lpBOHdqycFTGclRVBKtLMPkIg"
WEB_APP_URL = "https://zoli801.github.io/nft_game_test/"

# Основной файл Excel
USER_DATA_FILE = "user_data.xlsx"

# Листы в Excel
BALANCE_SHEET = "Балансы"
PURCHASE_SHEET = "История покупок"
NFT_SHEET = "История NFT"

# Пользователи с бесконечным балансом
INFINITE_BALANCE_USERS = ["@zoli_main"]

# Состояния
INPUT_AMOUNT = 1


def init_excel_file():
    if not os.path.exists(USER_DATA_FILE):
        with pd.ExcelWriter(USER_DATA_FILE) as writer:
            # Лист балансов
            pd.DataFrame(columns=["user_id", "username", "balance", "nft_count"]).to_excel(
                writer, sheet_name=BALANCE_SHEET, index=False
            )
            # Лист истории покупок
            pd.DataFrame(columns=["user_id", "username", "amount", "date"]).to_excel(
                writer, sheet_name=PURCHASE_SHEET, index=False
            )
            # Лист истории NFT
            pd.DataFrame(columns=["user_id", "username", "action", "date"]).to_excel(
                writer, sheet_name=NFT_SHEET, index=False
            )


def load_user_data(user_id: int, username: str):
    try:
        with pd.ExcelFile(USER_DATA_FILE) as xls:
            df = pd.read_excel(xls, sheet_name=BALANCE_SHEET)

        user_data = df[df["user_id"] == user_id]

        if not user_data.empty:
            balance = int(user_data.iloc[0]["balance"])
            nft_count = int(user_data.iloc[0]["nft_count"])
        else:
            balance = 0
            nft_count = 0

        if username.lower() in [u.lower() for u in INFINITE_BALANCE_USERS]:
            balance = 10 ** 9

        return {"balance": balance, "nft_count": nft_count}
    except:
        return {"balance": 0, "nft_count": 0}


def update_user_data(user_id: int, username: str, balance: int, nft_count: int):
    try:
        with pd.ExcelFile(USER_DATA_FILE) as xls:
            balance_df = pd.read_excel(xls, sheet_name=BALANCE_SHEET)
            purchase_df = pd.read_excel(xls, sheet_name=PURCHASE_SHEET)
            nft_df = pd.read_excel(xls, sheet_name=NFT_SHEET)

        # Обновление балансов
        if username.lower() in [u.lower() for u in INFINITE_BALANCE_USERS]:
            if user_id in balance_df["user_id"].values:
                balance_df.loc[balance_df["user_id"] == user_id, "nft_count"] = nft_count
                balance_df.loc[balance_df["user_id"] == user_id, "username"] = username
            else:
                new_row = pd.DataFrame({
                    "user_id": [user_id],
                    "username": [username],
                    "balance": [0],
                    "nft_count": [nft_count]
                })
                balance_df = pd.concat([balance_df, new_row], ignore_index=True)
        else:
            if user_id in balance_df["user_id"].values:
                balance_df.loc[balance_df["user_id"] == user_id, "balance"] = balance
                balance_df.loc[balance_df["user_id"] == user_id, "nft_count"] = nft_count
                balance_df.loc[balance_df["user_id"] == user_id, "username"] = username
            else:
                new_row = pd.DataFrame({
                    "user_id": [user_id],
                    "username": [username],
                    "balance": [balance],
                    "nft_count": [nft_count]
                })
                balance_df = pd.concat([balance_df, new_row], ignore_index=True)

        # Сохранение всех листов
        with pd.ExcelWriter(USER_DATA_FILE) as writer:
            balance_df.to_excel(writer, sheet_name=BALANCE_SHEET, index=False)
            purchase_df.to_excel(writer, sheet_name=PURCHASE_SHEET, index=False)
            nft_df.to_excel(writer, sheet_name=NFT_SHEET, index=False)

    except Exception as e:
        print(f"Ошибка при обновлении данных: {e}")


def add_purchase_record(user_id: int, username: str, amount: int):
    try:
        with pd.ExcelFile(USER_DATA_FILE) as xls:
            purchase_df = pd.read_excel(xls, sheet_name=PURCHASE_SHEET)
            balance_df = pd.read_excel(xls, sheet_name=BALANCE_SHEET)
            nft_df = pd.read_excel(xls, sheet_name=NFT_SHEET)

        new_row = pd.DataFrame({
            "user_id": [user_id],
            "username": [username],
            "amount": [amount],
            "date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })

        purchase_df = pd.concat([purchase_df, new_row], ignore_index=True)

        # Обновление баланса
        if user_id in balance_df["user_id"].values and not has_infinite_balance(username):
            current_balance = balance_df.loc[balance_df["user_id"] == user_id, "balance"].values[0]
            balance_df.loc[balance_df["user_id"] == user_id, "balance"] = current_balance + amount

        # Сохранение всех листов
        with pd.ExcelWriter(USER_DATA_FILE) as writer:
            balance_df.to_excel(writer, sheet_name=BALANCE_SHEET, index=False)
            purchase_df.to_excel(writer, sheet_name=PURCHASE_SHEET, index=False)
            nft_df.to_excel(writer, sheet_name=NFT_SHEET, index=False)

    except Exception as e:
        print(f"Ошибка при добавлении покупки: {e}")


def add_nft_record(user_id: int, username: str, action: str):
    try:
        with pd.ExcelFile(USER_DATA_FILE) as xls:
            nft_df = pd.read_excel(xls, sheet_name=NFT_SHEET)
            balance_df = pd.read_excel(xls, sheet_name=BALANCE_SHEET)
            purchase_df = pd.read_excel(xls, sheet_name=PURCHASE_SHEET)

        new_row = pd.DataFrame({
            "user_id": [user_id],
            "username": [username],
            "action": [action],
            "date": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })

        nft_df = pd.concat([nft_df, new_row], ignore_index=True)

        # Обновление счетчика NFT
        if user_id in balance_df["user_id"].values:
            current_nft = balance_df.loc[balance_df["user_id"] == user_id, "nft_count"].values[0]
            if action == "Добавил NFT в коллекцию":
                balance_df.loc[balance_df["user_id"] == user_id, "nft_count"] = current_nft + 1
            elif action == "Продал NFT":
                balance_df.loc[balance_df["user_id"] == user_id, "nft_count"] = current_nft - 1
                # Добавление средств за продажу
                if not has_infinite_balance(username):
                    current_balance = balance_df.loc[balance_df["user_id"] == user_id, "balance"].values[0]
                    balance_df.loc[balance_df["user_id"] == user_id, "balance"] = current_balance + 500

        # Сохранение всех листов
        with pd.ExcelWriter(USER_DATA_FILE) as writer:
            balance_df.to_excel(writer, sheet_name=BALANCE_SHEET, index=False)
            purchase_df.to_excel(writer, sheet_name=PURCHASE_SHEET, index=False)
            nft_df.to_excel(writer, sheet_name=NFT_SHEET, index=False)

    except Exception as e:
        print(f"Ошибка при добавлении NFT записи: {e}")


def get_username(user) -> str:
    if user.username:
        return f"@{user.username}"
    return f"id{user.id}"


def has_infinite_balance(username: str) -> bool:
    return username.lower() in [u.lower() for u in INFINITE_BALANCE_USERS]


def load_user_purchases(user_id: int) -> pd.DataFrame:
    try:
        with pd.ExcelFile(USER_DATA_FILE) as xls:
            df = pd.read_excel(xls, sheet_name=PURCHASE_SHEET)
        user_data = df[df["user_id"] == user_id]
        return user_data
    except:
        return pd.DataFrame()


async def start(update: Update, context: CallbackContext) -> None:
    init_excel_file()

    user = update.effective_user
    user_id = user.id
    username = get_username(user)
    user_data = load_user_data(user_id, username)

    balance_display = "∞" if has_infinite_balance(username) else user_data['balance']

    keyboard = [
        [InlineKeyboardButton("🛒 Купить звёзды", callback_data="buy_stars")],
        [InlineKeyboardButton("🎮 Играть в рулетку", callback_data="play_roulette")],
        [InlineKeyboardButton("👤 Профиль", callback_data="profile")]
    ]

    await update.message.reply_text(
        f"🌟 Ваш баланс: {balance_display} звёзд\n"
        f"🎴 NFT в коллекции: {user_data['nft_count']}\n"
        f"👤 Пользователь: {username}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def buy_command(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("✏️ Введите количество звёзд, которое вы хотите купить:")
    return INPUT_AMOUNT


async def buy_stars_callback(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✏️ Введите количество звёзд, которое вы хотите купить:")
    return INPUT_AMOUNT


async def input_amount(update: Update, context: CallbackContext) -> int:
    try:
        amount = int(update.message.text)
        if amount <= 0:
            await update.message.reply_text("⚠️ Пожалуйста, введите число больше 0")
            return INPUT_AMOUNT
    except ValueError:
        await update.message.reply_text("⚠️ Пожалуйста, введите целое число")
        return INPUT_AMOUNT

    context.user_data['stars_amount'] = amount

    user = update.effective_user
    chat_id = update.message.chat_id
    title = "Пополнение баланса"
    description = f"Покупка {amount} звёзд для вашего аккаунта"
    payload = f"{amount}-stars-payment"
    currency = "XTR"
    prices = [LabeledPrice(f"{amount} звёзд", amount)]

    await context.bot.send_invoice(
        chat_id,
        title,
        description,
        payload,
        provider_token="YOUR_PAYMENT_TOKEN",  # Замените на реальный платежный токен
        currency=currency,
        prices=prices,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        max_tip_amount=0
    )

    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Покупка отменена")
    return ConversationHandler.END


async def precheckout(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment(update: Update, context: CallbackContext) -> None:
    payment = update.message.successful_payment
    user = update.effective_user
    user_id = user.id
    username = get_username(user)
    amount = payment.total_amount

    user_data = load_user_data(user_id, username)

    if not has_infinite_balance(username):
        new_balance = user_data["balance"] + amount
        update_user_data(user_id, username, new_balance, user_data["nft_count"])
        add_purchase_record(user_id, username, amount)

        await update.message.reply_text(
            f"✅ Покупка подтверждена!\n"
            f"👤 Пользователь: {username}\n"
            f"💳 Зачислено: {amount} звёзд\n"
            f"💰 Новый баланс: {new_balance} звёзд\n"
            f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        await update.message.reply_text(
            f"✅ Покупка подтверждена!\n"
            f"👤 Пользователь: {username}\n"
            f"💳 Зачислено: {amount} звёзд\n"
            f"💰 Ваш баланс: ∞ (бесконечный)\n"
            f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )


async def profile_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    username = get_username(user)
    user_data = load_user_data(user_id, username)

    purchases = load_user_purchases(user_id)
    total_purchases = purchases["amount"].sum() if not purchases.empty else 0

    if not purchases.empty:
        purchase_history = "\n".join(
            [f"{row['date']} - {row['amount']} звёзд"
             for _, row in purchases.iterrows()]
        )
    else:
        purchase_history = "Нет данных о покупках"

    balance_display = "∞" if has_infinite_balance(username) else user_data['balance']

    message = (
        f"👤 Профиль пользователя\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Имя: {username}\n"
        f"💰 Баланс: {balance_display} звёзд\n"
        f"🎴 NFT в коллекции: {user_data['nft_count']}\n"
        f"🛒 Всего куплено: {total_purchases} звёзд\n\n"
        f"📜 История покупок:\n{purchase_history}"
    )

    await update.message.reply_text(message)


async def profile_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    username = get_username(user)
    user_data = load_user_data(user_id, username)

    purchases = load_user_purchases(user_id)
    total_purchases = purchases["amount"].sum() if not purchases.empty else 0

    if not purchases.empty:
        purchase_history = "\n".join(
            [f"{row['date']} - {row['amount']} звёзд"
             for _, row in purchases.iterrows()]
        )
    else:
        purchase_history = "Нет данных о покупках"

    balance_display = "∞" if has_infinite_balance(username) else user_data['balance']

    message = (
        f"👤 Профиль пользователя\n"
        f"🆔 ID: {user_id}\n"
        f"👤 Имя: {username}\n"
        f"💰 Баланс: {balance_display} звёзд\n"
        f"🎴 NFT в коллекции: {user_data['nft_count']}\n"
        f"🛒 Всего куплено: {total_purchases} звёзд\n\n"
        f"📜 История покупок:\n{purchase_history}"
    )

    await query.edit_message_text(text=message)


async def play_roulette(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    username = get_username(user)
    user_data = load_user_data(user_id, username)

    # Генерация уникального токена для верификации
    verification_token = f"{user_id}-{random.randint(100000, 99999999999999)}"
    context.user_data['web_app_token'] = verification_token

    keyboard = [
        [InlineKeyboardButton(
            "🎡 Открыть рулетку",
            web_app=WebAppInfo(
                url=f"{WEB_APP_URL}?user_id={user_id}&balance={user_data['balance']}&token={verification_token}")
        )]
    ]

    await query.message.reply_text(
        "🎮 Добро пожаловать в рулетку казино!\n"
        "💰 Стоимость одного вращения: 100 звёзд\n"
        "🎯 Нажмите кнопку ниже, чтобы открыть рулетку:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_web_app_data(update: Update, context: CallbackContext) -> None:
    data = json.loads(update.effective_message.web_app_data.data)
    user = update.effective_user
    user_id = user.id
    username = get_username(user)

    # Проверка токена верификации
    if data.get('token') != context.user_data.get('web_app_token'):
        await update.message.reply_text("❌ Ошибка верификации запроса")
        return

    action = data.get('action')

    if action == "spin":
        bet_amount = data.get('bet', 100)
        result = data["result"]
        result_type = data["result_type"]

        user_data = load_user_data(user_id, username)

        if not has_infinite_balance(username):
            # Списание ставки
            if user_data['balance'] < bet_amount:
                await update.message.reply_text("❌ Недостаточно средств для игры!")
                return

            new_balance = user_data["balance"] - bet_amount
            update_user_data(user_id, username, new_balance, user_data["nft_count"])
            add_purchase_record(user_id, username, -bet_amount)

        if result_type == "coins":
            win_amount = int(result)

            if not has_infinite_balance(username):
                new_balance += win_amount
                update_user_data(user_id, username, new_balance, user_data["nft_count"])
                add_purchase_record(user_id, username, win_amount)

            if has_infinite_balance(username):
                await update.message.reply_text(
                    f"🎉 Поздравляем! Вы выиграли {win_amount} звёзд!\n"
                    f"💰 Ваш баланс: ∞ (бесконечный)"
                )
            else:
                await update.message.reply_text(
                    f"🎉 Поздравляем! Вы выиграли {win_amount} звёзд!\n"
                    f"💰 Ваш новый баланс: {new_balance} звёзд"
                )

        elif result_type == "nft":
            add_nft_record(user_id, username, "Выиграл NFT")

            # Отправляем сообщение с предложением действий
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🎉 Поздравляем! Вы выиграли NFT!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Продать за 500 звёзд", callback_data="sell_nft")],
                    [InlineKeyboardButton("🎴 Добавить в коллекцию", callback_data="keep_nft")]
                ])
            )

    elif action == "get_balance":
        user_data = load_user_data(user_id, username)
        balance = "∞" if has_infinite_balance(username) else user_data['balance']
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=json.dumps({"balance": balance})
        )

    elif action == "place_bet":
        bet_amount = data.get('bet', 100)
        user_data = load_user_data(user_id, username)

        if not has_infinite_balance(username):
            if user_data['balance'] < bet_amount:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=json.dumps({"error": "insufficient_funds"})
                )
                return

        # Подтверждаем ставку
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=json.dumps({"action": "bet_accepted"})
        )


async def handle_nft_decision(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    username = get_username(user)
    user_data = load_user_data(user_id, username)

    if query.data == "sell_nft":
        if not has_infinite_balance(username):
            new_balance = user_data["balance"] + 500
            update_user_data(user_id, username, new_balance, user_data["nft_count"])
            add_purchase_record(user_id, username, 500)
        else:
            new_balance = user_data["balance"]

        add_nft_record(user_id, username, "Продал NFT")

        if has_infinite_balance(username):
            await query.message.reply_text(
                f"✅ Вы успешно продали NFT!\n"
                f"💰 Ваш баланс: ∞ (бесконечный)"
            )
        else:
            await query.message.reply_text(
                f"✅ Вы успешно продали NFT!\n"
                f"💰 Зачислено: 500 звёзд\n"
                f"💼 Ваш баланс: {new_balance} звёзд"
            )

    elif query.data == "keep_nft":
        new_nft_count = user_data["nft_count"] + 1
        update_user_data(user_id, username, user_data["balance"], new_nft_count)
        add_nft_record(user_id, username, "Добавил NFT в коллекцию")

        await query.message.reply_text(
            f"🎴 NFT добавлен в вашу коллекцию!\n"
            f"🏆 Теперь у вас {new_nft_count} NFT\n"
            f"👤 Посмотреть коллекцию можно в профиле (/profile)"
        )


def main() -> None:
    init_excel_file()

    async def post_init(application: Application):
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🎰 Рулетка",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        )
        print("Кнопка меню установлена")

    application = Application.builder() \
        .token(TOKEN) \
        .post_init(post_init) \
        .build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(buy_stars_callback, pattern="^buy_stars$"),
            CommandHandler("buy", buy_command)
        ],
        states={
            INPUT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, input_amount)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    nft_handler = CallbackQueryHandler(handle_nft_decision, pattern="^(sell_nft|keep_nft)$")

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(nft_handler)
    application.add_handler(PreCheckoutQueryHandler(precheckout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))

    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CallbackQueryHandler(profile_callback, pattern="^profile$"))
    application.add_handler(CallbackQueryHandler(play_roulette, pattern="^play_roulette$"))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
