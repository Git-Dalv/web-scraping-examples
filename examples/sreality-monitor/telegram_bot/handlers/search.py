"""
Search handler for Telegram bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.database.db import Database


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command /search"""
    await show_search_menu(update, context, is_command=True)


async def show_search_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_command: bool = False):
    """Show search menu"""
    keyboard = [
        [
            InlineKeyboardButton("By Region", callback_data="search_region"),
            InlineKeyboardButton("By Type", callback_data="search_type"),
        ],
        [
            InlineKeyboardButton("By Category", callback_data="search_category"),
            InlineKeyboardButton("By Price", callback_data="search_price"),
        ],
        [
            InlineKeyboardButton("New Today", callback_data="search_new"),
            InlineKeyboardButton("Price Drops", callback_data="search_price_drop"),
        ],
        [InlineKeyboardButton("<< Back", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "*Search Properties*\n\nSelect search criteria:"
    
    if is_command:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def handle_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle search callbacks"""
    query = update.callback_query
    data = query.data
    
    if data == "search_region":
        await show_region_filter(update, context)
    elif data == "search_type":
        await show_type_filter(update, context)
    elif data == "search_category":
        await show_category_filter(update, context)
    elif data == "search_price":
        await show_price_filter(update, context)
    elif data == "search_new":
        await show_new_listings(update, context)
    elif data == "search_price_drop":
        await show_price_drops(update, context)
    elif data.startswith("search_region_"):
        region_id = int(data.replace("search_region_", ""))
        await show_results_by_region(update, context, region_id)
    elif data.startswith("search_type_"):
        type_id = int(data.replace("search_type_", ""))
        await show_results_by_type(update, context, type_id)
    elif data.startswith("search_cat_"):
        cat_id = int(data.replace("search_cat_", ""))
        await show_results_by_category(update, context, cat_id)
    elif data.startswith("search_price_"):
        parts = data.replace("search_price_", "").split("_")
        min_price = int(parts[0])
        max_price = int(parts[1])
        await show_results_by_price(update, context, min_price, max_price)


async def show_region_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show region selection"""
    query = update.callback_query
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.name, COUNT(e.hash_id) as cnt
            FROM regions r
            LEFT JOIN estates e ON r.id = e.region_id AND e.status = 'active'
            GROUP BY r.id
            ORDER BY cnt DESC
        """)
        regions = cursor.fetchall()
    
    keyboard = []
    for r in regions:
        btn_text = f"{r[1]} ({r[2]})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"search_region_{r[0]}")])
    
    keyboard.append([InlineKeyboardButton("<< Back", callback_data="menu_search")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Select Region:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_type_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show type selection (sale/lease)"""
    query = update.callback_query
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ct.id, ct.name, COUNT(e.hash_id) as cnt
            FROM category_types ct
            LEFT JOIN estates e ON ct.id = e.category_type_id AND e.status = 'active'
            GROUP BY ct.id
        """)
        types = cursor.fetchall()
    
    keyboard = []
    for t in types:
        btn_text = f"{t[1]} ({t[2]})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"search_type_{t[0]}")])
    
    keyboard.append([InlineKeyboardButton("<< Back", callback_data="menu_search")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Select Type:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_category_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show category selection"""
    query = update.callback_query
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cm.id, cm.name, COUNT(e.hash_id) as cnt
            FROM category_main cm
            LEFT JOIN estates e ON cm.id = e.category_main_id AND e.status = 'active'
            GROUP BY cm.id
        """)
        categories = cursor.fetchall()
    
    keyboard = []
    for c in categories:
        btn_text = f"{c[1]} ({c[2]})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"search_cat_{c[0]}")])
    
    keyboard.append([InlineKeyboardButton("<< Back", callback_data="menu_search")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Select Category:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_price_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show price range selection"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("Up to 2M CZK", callback_data="search_price_0_2000000")],
        [InlineKeyboardButton("2-5M CZK", callback_data="search_price_2000000_5000000")],
        [InlineKeyboardButton("5-10M CZK", callback_data="search_price_5000000_10000000")],
        [InlineKeyboardButton("10-20M CZK", callback_data="search_price_10000000_20000000")],
        [InlineKeyboardButton("Over 20M CZK", callback_data="search_price_20000000_0")],
        [InlineKeyboardButton("<< Back", callback_data="menu_search")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "*Select Price Range:*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def show_new_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show new listings today"""
    query = update.callback_query
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT hash_id, name, city, price, category_main_id
            FROM estates
            WHERE DATE(first_seen_at) = DATE('now')
            AND status = 'active'
            ORDER BY first_seen_at DESC
            LIMIT 10
        """)
        estates = cursor.fetchall()
    
    if not estates:
        text = "*New Listings*\n\nNo new listings today."
    else:
        text = f"*New Listings Today* ({len(estates)})\n\n"
        for e in estates:
            price_str = f"{e[3]:,}".replace(",", " ") if e[3] else "Price on request"
            text += f"- {e[1][:40]}\n  {e[2]} | {price_str} CZK\n\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_search")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def show_price_drops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent price drops"""
    query = update.callback_query
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.hash_id, e.name, e.city,
                ph.price as old_price, e.price as new_price,
                ROUND((e.price - ph.price) * 100.0 / ph.price, 1) as change_pct
            FROM price_history ph
            JOIN estates e ON ph.hash_id = e.hash_id
            WHERE ph.price > e.price
            AND e.status = 'active'
            ORDER BY ph.recorded_at DESC
            LIMIT 10
        """)
        drops = cursor.fetchall()
    
    if not drops:
        text = "*Price Drops*\n\nNo price changes recorded yet."
    else:
        text = f"*Price Drops* ({len(drops)})\n\n"
        for d in drops:
            old_str = f"{d[3]:,}".replace(",", " ")
            new_str = f"{d[4]:,}".replace(",", " ")
            text += f"- {d[1][:35]}\n"
            text += f"  {d[2]} | {d[5]}%\n"
            text += f"  ~{old_str}~ > *{new_str}* CZK\n\n"
    
    keyboard = [[InlineKeyboardButton("<< Back", callback_data="menu_search")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def show_results_by_region(update: Update, context: ContextTypes.DEFAULT_TYPE, region_id: int):
    """Show estates by region"""
    context.user_data["filter"] = {"region_id": region_id}
    context.user_data["page"] = 0
    await show_estate_list(update, context)


async def show_results_by_type(update: Update, context: ContextTypes.DEFAULT_TYPE, type_id: int):
    """Show estates by type"""
    context.user_data["filter"] = {"type_id": type_id}
    context.user_data["page"] = 0
    await show_estate_list(update, context)


async def show_results_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE, cat_id: int):
    """Show estates by category"""
    context.user_data["filter"] = {"category_id": cat_id}
    context.user_data["page"] = 0
    await show_estate_list(update, context)


async def show_results_by_price(update: Update, context: ContextTypes.DEFAULT_TYPE, min_price: int, max_price: int):
    """Show estates by price range"""
    context.user_data["filter"] = {"min_price": min_price, "max_price": max_price}
    context.user_data["page"] = 0
    await show_estate_list(update, context)


async def show_estate_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show paginated estate list"""
    query = update.callback_query
    
    filter_data = context.user_data.get("filter", {})
    page = context.user_data.get("page", 0)
    per_page = 5
    
    where_clauses = ["status = 'active'"]
    params = []
    
    if "region_id" in filter_data:
        where_clauses.append("region_id = ?")
        params.append(filter_data["region_id"])
    if "type_id" in filter_data:
        where_clauses.append("category_type_id = ?")
        params.append(filter_data["type_id"])
    if "category_id" in filter_data:
        where_clauses.append("category_main_id = ?")
        params.append(filter_data["category_id"])
    if "min_price" in filter_data and filter_data["min_price"] > 0:
        where_clauses.append("price >= ?")
        params.append(filter_data["min_price"])
    if "max_price" in filter_data and filter_data["max_price"] > 0:
        where_clauses.append("price <= ?")
        params.append(filter_data["max_price"])
    
    where_sql = " AND ".join(where_clauses)
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT COUNT(*) FROM estates WHERE {where_sql}", params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT hash_id, name, city, price, price_m2
            FROM estates
            WHERE {where_sql}
            ORDER BY price DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, page * per_page])
        estates = cursor.fetchall()
    
    total_pages = (total + per_page - 1) // per_page
    
    text = f"*Found: {total}*\n"
    text += f"Page {page + 1}/{max(total_pages, 1)}\n\n"
    
    keyboard = []
    for e in estates:
        price_str = f"{e[3]:,}".replace(",", " ") if e[3] else "?"
        btn_text = f"{e[2]} | {price_str} CZK"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"estate_{e[0]}")])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("<< Prev", callback_data=f"page_{page - 1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next >>", callback_data=f"page_{page + 1}"))
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("<< Back", callback_data="menu_search")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle page navigation"""
    query = update.callback_query
    page = int(query.data.replace("page_", ""))
    context.user_data["page"] = page
    await show_estate_list(update, context)


async def show_estate_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show estate details"""
    query = update.callback_query
    hash_id = int(query.data.replace("estate_", ""))
    
    with Database() as db:
        conn = db.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                e.hash_id, e.name, e.price, e.price_m2,
                e.city, e.citypart, e.street,
                ct.name as type_name, cm.name as cat_name,
                e.city_seo, e.citypart_seo, e.street_seo,
                ct.seo_name as type_seo, cm.seo_name as main_seo,
                cs.seo_name as sub_seo
            FROM estates e
            LEFT JOIN category_types ct ON e.category_type_id = ct.id
            LEFT JOIN category_main cm ON e.category_main_id = cm.id
            LEFT JOIN category_sub cs ON e.category_sub_id = cs.id
            WHERE e.hash_id = ?
        """, (hash_id,))
        estate = cursor.fetchone()
    
    if not estate:
        await query.edit_message_text("Property not found")
        return
    
    city_seo = estate[9] or ""
    citypart_seo = estate[10] or ""
    street_seo = estate[11] or ""
    type_seo = estate[12] or "prodej"
    main_seo = estate[13] or "byt"
    sub_seo = estate[14] or ""
    
    if street_seo:
        locality = f"{city_seo}-{citypart_seo}-{street_seo}"
    elif citypart_seo:
        locality = f"{city_seo}-{citypart_seo}-"
    else:
        locality = f"{city_seo}-{city_seo}-"
    
    url = f"https://www.sreality.cz/detail/{type_seo}/{main_seo}/{sub_seo}/{locality}/{hash_id}"
    
    price_str = f"{estate[2]:,}".replace(",", " ") if estate[2] else "Price on request"
    price_m2_str = f"{estate[3]:,}".replace(",", " ") if estate[3] else "-"
    
    location_parts = [estate[4]]
    if estate[5]:
        location_parts.append(estate[5])
    if estate[6]:
        location_parts.append(estate[6])
    location = ", ".join(location_parts)
    
    text = (
        f"*{estate[1]}*\n\n"
        f"*Location:* {location}\n"
        f"*Type:* {estate[7]} - {estate[8]}\n\n"
        f"*Price:* {price_str} CZK\n"
        f"*Price/m2:* {price_m2_str} CZK\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("Open on Sreality", url=url)],
        [InlineKeyboardButton("<< Back to List", callback_data="back_to_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for search"""
    pass
