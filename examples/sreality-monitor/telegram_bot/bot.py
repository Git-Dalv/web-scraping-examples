"""
Sreality Monitor - Telegram Bot
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from handlers import search, analytics, subscriptions
from services.notifications import NotificationService

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show main menu"""
    keyboard = [
        [
            InlineKeyboardButton("Search", callback_data="menu_search"),
            InlineKeyboardButton("Analytics", callback_data="menu_analytics"),
        ],
        [
            InlineKeyboardButton("Subscriptions", callback_data="menu_subscriptions"),
            InlineKeyboardButton("Map", callback_data="menu_map"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "*Sreality Monitor*\n\n"
        "Real estate monitoring in Czech Republic\n\n"
        "Select an option:"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    text = (
        "*Sreality Monitor - Help*\n\n"
        "*Commands:*\n"
        "/start - Main menu\n"
        "/search - Search properties\n"
        "/stats - Statistics\n"
        "/subscribe - Subscriptions\n"
        "/my\\_subscriptions - My subscriptions\n\n"
        "*Features:*\n"
        "- Search with filters\n"
        "- Analytics and charts\n"
        "- New listings alerts\n"
        "- Price drop notifications\n"
        "- Daily digests"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_main":
        await start(update, context)
    elif data == "menu_search":
        await search.show_search_menu(update, context)
    elif data == "menu_analytics":
        await analytics.show_analytics_menu(update, context)
    elif data == "menu_subscriptions":
        await subscriptions.show_subscriptions_menu(update, context)
    elif data == "menu_map":
        await send_map_link(update, context)
    elif data.startswith("search_"):
        await search.handle_search_callback(update, context)
    elif data.startswith("analytics_"):
        await analytics.handle_analytics_callback(update, context)
    elif data.startswith("sub_"):
        await subscriptions.handle_subscription_callback(update, context)
    elif data.startswith("page_"):
        await search.handle_pagination(update, context)
    elif data.startswith("estate_"):
        await search.show_estate_details(update, context)
    elif data == "back_to_list":
        await search.show_estate_list(update, context)


async def send_map_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send link to map"""
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "*Property Map*\n\n"
        "Open interactive map in browser:\n\n"
        "http://localhost:8000/index.html\n\n"
        "_Map shows all active properties with clustering and filters_"
    )
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set in .env")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("search", search.cmd_search))
    app.add_handler(CommandHandler("stats", analytics.cmd_stats))
    app.add_handler(CommandHandler("subscribe", subscriptions.cmd_subscribe))
    app.add_handler(CommandHandler("my_subscriptions", subscriptions.cmd_my_subscriptions))
    
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        search.handle_text_input
    ))
    
    print("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
