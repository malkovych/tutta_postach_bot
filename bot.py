#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "7973829035:AAHylWqTFczrGNkqhpOQcGUK1BqjhV3ogeM"

PRODUCTS = {
    "Метро": ["Креветки", "Соус кисло-солодкий", "Соус брусничний", "Соус сирний", "Соус BBQ"],
    "М'ясо": ["Куряче філе", "Яловичина", "Фарш мікс", "Індичка", "Куряче стегно"],
    "М'ясні продукти": ["Шинка", "Бекон", "Чорізо", "Чорізо гостре", "Кабаноси"],
    "Сири, молокопродукти": ["Моцарела", "Пармезан", "Дорблю", "Чеддер", "Філадельфія"],
    "Консерви": ["Огірок маринований", "Ананас шматочки", "Персик конвервований"],
    "Бакалія та олія": ["Борошно", "Пелаті", "Дріжджі", "Цукор", "Сіль"],
    "Овочі": ["Томати чері", "Часник", "Перець", "Цибуля синя", "Картопля"],
    "Фрукти": ["Груша", "Апельсини", "Лимони", "Лайм"],
    "Зелень": ["Петрушка", "Айсберг салат", "Базилік", "Рукола", "Шпинат"],
    "Напої": ["Вода", "Сік", "Кава", "Чай", "Газовані напої Пепсі"],
    "Соуси": ["Кетчуп", "Майонез", "Гірчиця", "Соєвий соус", "Томатна паста"],
    "Сухі продукти": ["Паста Букатіні", "Локшина", "Папір для выпічки"],
    "Хімія та госптовари": ["Ланч бокс паста", "Ланч бокс салат", "Пергамент"]
}

SELECTING_CATEGORY, SELECTING_PRODUCT, ADDING_COMMENT, SELECTING_CONTACT = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Вітаю! Ви працівник піцерії. Оберіть категорію продуктів:",
        reply_markup=get_categories_keyboard()
    )
    context.user_data["order"] = {}
    return SELECTING_CATEGORY

def get_categories_keyboard():
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in PRODUCTS.keys()]
    keyboard.append([InlineKeyboardButton("📝 Переглянути замовлення", callback_data="view_order")])
    return InlineKeyboardMarkup(keyboard)

async def select_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "view_order":
        return await view_order(update, context)
    category = query.data.replace("cat_", "")
    context.user_data["current_category"] = category
    keyboard = [[InlineKeyboardButton(prod, callback_data=f"prod_{prod}")] for prod in PRODUCTS[category]]
    keyboard.append([InlineKeyboardButton("⬅️ Назад до категорій", callback_data="back_to_categories")])
    keyboard.append([InlineKeyboardButton("📝 Переглянути замовлення", callback_data="view_order")])
    await query.edit_message_text(
        f"Оберіть продукти з категорії \"{category}\":",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return SELECTING_PRODUCT

async def select_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_categories":
        await query.edit_message_text(
            "Оберіть категорію продуктів:",
            reply_markup=get_categories_keyboard()
        )
        return SELECTING_CATEGORY
    if query.data == "view_order":
        return await view_order(update, context)
    product = query.data.replace("prod_", "")
    category = context.user_data["current_category"]
    if category not in context.user_data["order"]:
        context.user_data["order"][category] = []
    if product not in context.user_data["order"][category]:
        context.user_data["order"][category].append(product)
        await query.message.reply_text(f"✅ Додано \"{product}\" до замовлення.")
    await query.message.reply_text(
        "Продовжуйте обирати продукти:",
        reply_markup=get_categories_keyboard()
    )
    return SELECTING_CATEGORY

async def view_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    order = context.user_data.get("order", {})
    if not order:
        await query.edit_message_text(
            "Ваше замовлення порожнє.",
            reply_markup=get_categories_keyboard()
        )
        return SELECTING_CATEGORY
    message = "📋 *Ваше замовлення:*\n\n"
    for category, items in order.items():
        if items:
            message += f"*{category}:*\n"
            for item in items:
                message += f"- {item}\n"
            message += "\n"
    keyboard = [
        [InlineKeyboardButton("➕ Додати ще продукти", callback_data="back_to_categories")],
        [InlineKeyboardButton("💬 Додати коментар", callback_data="add_comment")],
        [InlineKeyboardButton("📤 Відправити замовлення", callback_data="send_order")]
    ]
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECTING_CATEGORY

async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Введіть коментар до замовлення:")
    return ADDING_COMMENT

async def save_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["comment"] = update.message.text
    await update.message.reply_text(
        "Коментар збережено. Оберіть дію:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Переглянути замовлення", callback_data="view_order")],
            [InlineKeyboardButton("📤 Відправити замовлення", callback_data="send_order")]
        ])
    )
    return SELECTING_CATEGORY

async def send_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if not context.user_data.get("order"):
        await query.edit_message_text(
            "Ваше замовлення порожнє. Додайте продукти.",
            reply_markup=get_categories_keyboard()
        )
        return SELECTING_CATEGORY
    keyboard = [[KeyboardButton("📱 Обрати контакт", request_contact=True)]]
    await query.message.reply_text(
        "Оберіть контакт для відправки замовлення:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return SELECTING_CONTACT

async def forward_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    order = context.user_data.get("order", {})
    comment = context.user_data.get("comment", "")
    message = "📋 *Нове замовлення:*\n\n"
    for category, items in order.items():
        if items:
            message += f"*{category}:*\n"
            for item in items:
                message += f"- {item}\n"
            message += "\n"
    if comment:
        message += f"*Коментар:* {comment}\n"
    await context.bot.send_message(chat_id=contact.user_id, text=message, parse_mode="Markdown")
    await update.message.reply_text("Замовлення успішно відправлено!")
    context.user_data.clear()
    await update.message.reply_text("Почати нове замовлення?", reply_markup=get_categories_keyboard())
    return SELECTING_CATEGORY

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Бот для замовлення продуктів*\n\n"
        "Команди:\n"
        "/start - Почати роботу\n"
        "/help - Допомога\n\n"
        "Виберіть продукти, додайте коментар (за бажанням), і відправте замовлення контакту."
    )

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_CATEGORY: [
                CallbackQueryHandler(select_category, pattern="^cat_|^view_order$"),
                CallbackQueryHandler(send_order, pattern="^send_order$"),
                CallbackQueryHandler(add_comment, pattern="^add_comment$")
            ],
            SELECTING_PRODUCT: [
                CallbackQueryHandler(select_product, pattern="^prod_|^back_to_categories$|^view_order$")
            ],
            ADDING_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_comment)
            ],
            SELECTING_CONTACT: [
                MessageHandler(filters.CONTACT, forward_order)
            ]
        },
        fallbacks=[CommandHandler("help", help_command)]
    )
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    print("Бот запущено!")
    application.run_polling()

if __name__ == "__main__":
    main()
