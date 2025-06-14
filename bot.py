from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes

# Стани розмови
SELECTING_CATEGORY, SELECTING_PRODUCT = range(2)

# Приклад структури продуктів
PRODUCTS = {
    "М'ясо": ["Курка", "Свинина", "Яловичина"],
    "Овочі": ["Картопля", "Морква", "Огірки"],
    "Фрукти": ["Яблука", "Банани", "Апельсини"]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Початок роботи бота, відображення категорій."""
    keyboard = [
        [InlineKeyboardButton(category, callback_data=f"toggle_cat_{category}")]
        for category in PRODUCTS.keys()
    ]
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть категорію:", reply_markup=reply_markup)
    return SELECTING_CATEGORY

async def toggle_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Розгортання або згортання категорії."""
    query = update.callback_query
    await query.answer()
    category = query.data.replace("toggle_cat_", "")
    
    # Перемикаємо стан розгорнутої категорії
    if context.user_data.get("expanded_category") == category:
        context.user_data.pop("expanded_category", None)
    else:
        context.user_data["expanded_category"] = category
    
    return await show_products(update, context)

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Відображення категорій та товарів з чекбоксами."""
    query = update.callback_query
    expanded_category = context.user_data.get("expanded_category")
    keyboard = []

    # Формуємо клавіатуру
    for category in PRODUCTS.keys():
        if category == expanded_category:
            # Показуємо товари з чекбоксами
            for product in PRODUCTS[category]:
                selected = product in context.user_data.get("order", {}).get(category, [])
                checkbox = "✅" if selected else "⬜"
                keyboard.append([InlineKeyboardButton(
                    f"{checkbox} {product}", 
                    callback_data=f"toggle_prod_{category}_{product}"
                )])
            keyboard.append([InlineKeyboardButton(
                f"Згорнути {category}", 
                callback_data=f"toggle_cat_{category}"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                category, 
                callback_data=f"toggle_cat_{category}"
            )])
    keyboard.append([InlineKeyboardButton("Готово", callback_data="done")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Оберіть категорію або товари:", reply_markup=reply_markup)
    return SELECTING_PRODUCT

async def toggle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Перемикання стану вибору товару."""
    query = update.callback_query
    await query.answer()
    _, category, product = query.data.split("_", 2)
    
    # Оновлюємо список вибраних товарів
    order = context.user_data.get("order", {})
    if category not in order:
        order[category] = []
    if product in order[category]:
        order[category].remove(product)
    else:
        order[category].append(product)
    context.user_data["order"] = order
    
    return await show_products(update, context)

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Завершення вибору товарів."""
    query = update.callback_query
    await query.answer()
    order = context.user_data.get("order", {})
    
    if not order:
        await query.edit_message_text("Ви не вибрали жодного товару.")
        return SELECTING_CATEGORY
    
    order_text = "\n".join(
        f"{cat}: {', '.join(prods)}" 
        for cat, prods in order.items() if prods
    )
    await query.edit_message_text(f"Ваше замовлення:\n{order_text}\nДякую!")
    return ConversationHandler.END

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token("YOUR_BOT_TOKEN").build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_CATEGORY: [CallbackQueryHandler(toggle_category, pattern="^toggle_cat_"),
                                CallbackQueryHandler(done, pattern="^done$")],
            SELECTING_PRODUCT: [CallbackQueryHandler(toggle_category, pattern="^toggle_cat_"),
                               CallbackQueryHandler(toggle_product, pattern="^toggle_prod_"),
                               CallbackQueryHandler(done, pattern="^done$")]
        },
        fallbacks=[]
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
