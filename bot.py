#!/usr/bin/env python3
"""
Thunder Tech Store Telegram Bot
- ကုန်ပစ္စည်းများ ရွေးချယ်မှု
- KPay ငွေပေးချေမှု အတည်ပြုခြင်း
- အော်ဒါ အုပ်စုံ
"""

import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load product configuration
with open('config.json', 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# Conversation states
SELECTING_PRODUCT, CONFIRMING_ORDER, AWAITING_PAYMENT = range(3)

# Store user orders
user_orders = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - ကုန်ပစ္စည်းများ ရွေးချယ်မှု စတင်ခြင်း"""
    user = update.effective_user
    user_id = user.id
    
    # Initialize user order
    user_orders[user_id] = {
        'user_id': user_id,
        'username': user.username or user.first_name,
        'products': [],
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    welcome_text = """
🔥 **Thunder Tech Store သို့ ကြိုးဆိုကြည့်ပါ** 🔥

ကျွန်တော်တို့ ရောင်းချတဲ့ ကုန်ပစ္စည်းများ:

🤖 Gemini Plan
🔒 Express VPN 1 Month  
🎬 CapCut Pro
🛡️ F-Secure VPN 5 Device

အောက်က ခလုတ်တွေမှ ကုန်ပစ္စည်း ရွေးချယ်ပါ:
    """
    
    # Create product selection buttons
    keyboard = []
    for product in CONFIG['products']:
        keyboard.append([
            InlineKeyboardButton(
                f"{product['emoji']} {product['name']}",
                callback_data=f"product_{product['id']}"
            )
        ])
    
    # Add "Order Complete" button
    keyboard.append([
        InlineKeyboardButton("✅ အော်ဒါ ပြီးစီးပါပြီ", callback_data="order_complete")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    product_id = int(query.data.split('_')[1])
    
    # Find product
    product = next((p for p in CONFIG['products'] if p['id'] == product_id), None)
    
    if product:
        # Add to user's order
        user_orders[user_id]['products'].append(product)
        
        confirmation_text = f"""
✅ **{product['emoji']} {product['name']} ထည့်သွင်းပြီးပါပြီ**

📝 **ကုန်ပစ္စည်းများ:**
"""
        
        for idx, prod in enumerate(user_orders[user_id]['products'], 1):
            confirmation_text += f"\n{idx}. {prod['emoji']} {prod['name']}"
        
        confirmation_text += """

\n🛒 နောက်ထပ် ကုန်ပစ္စည်း ရွေးချယ်ပါ သို့မဟုတ် အော်ဒါ ပြီးစီးပါ:
        """
        
        # Create product selection buttons again
        keyboard = []
        for product in CONFIG['products']:
            keyboard.append([
                InlineKeyboardButton(
                    f"{product['emoji']} {product['name']}",
                    callback_data=f"product_{product['id']}"
                )
            ])
        
        # Add "Order Complete" button
        keyboard.append([
            InlineKeyboardButton("✅ အော်ဒါ ပြီးစီးပါပြီ", callback_data="order_complete")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            confirmation_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return SELECTING_PRODUCT


async def order_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle order completion and payment"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    order = user_orders.get(user_id)
    
    if not order or not order['products']:
        await query.edit_message_text(
            "❌ အော်ဒါ မရှိပါ။ ကုန်ပစ္စည်းများ ရွေးချယ်ပါ။"
        )
        return SELECTING_PRODUCT
    
    # Display order summary
    order_summary = "📋 **အော်ဒါ အချုပ်:**\n\n"
    for idx, product in enumerate(order['products'], 1):
        order_summary += f"{idx}. {product['emoji']} {product['name']}\n"
    
    order_summary += f"""

💳 **ငွေပေးချေမှု အချက်အလက်:**

🏦 ငွေပေးချေမှု နည်းလမ်း: **KPay**

⚠️ KPay မှ ငွေ လွှဲပြောင်းပြီးတဲ့အခါ:
1. KPay ငွေလွှဲ အထောက်အထားကို ကျွန်တော်ထံ ပေးပို့ပါ
2. ကျွန်တော် အတည်ပြုပြီးတဲ့အခါ ကုန်ပစ္စည်းများ ပို့ဆောင်ပေးပါ့မယ်

📱 **ကျွန်တော်ထံ ဆက်သွယ်ရန်:**
@thunder_tech_store (Telegram)

✅ အတည်ပြုခြင်းအတွက် စောင့်ဆိုင်းနေပါတယ်...
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ ပြီးပါပြီ", callback_data="finish_order")],
        [InlineKeyboardButton("🔄 ပြန်စတင်ပါ", callback_data="restart")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        order_summary,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return CONFIRMING_ORDER


async def finish_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Finish order and save to file"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    order = user_orders.get(user_id)
    
    if order:
        # Save order to file
        with open('orders.json', 'a', encoding='utf-8') as f:
            json.dump(order, f, ensure_ascii=False, indent=2)
            f.write('\n---\n')
        
        finish_text = """
✅ **အော်ဒါ လက်ခံပြီးပါပြီ!**

📝 **အော်ဒါ အချက်အလက်:**
"""
        for idx, product in enumerate(order['products'], 1):
            finish_text += f"\n{idx}. {product['emoji']} {product['name']}"
        
        finish_text += f"""

🔔 ကျွန်တော် KPay ငွေလွှဲ အတည်ပြုပြီးတဲ့အခါ 
သင့်ထံ ကုန်ပစ္စည်းများ ပို့ဆောင်ပေးပါ့မယ်။

ကျေးဇူးတင်ပါတယ်! 🙏
        """
        
        await query.edit_message_text(finish_text, parse_mode='Markdown')
    
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Restart the conversation"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_orders[user_id] = {
        'user_id': user_id,
        'username': query.from_user.username or query.from_user.first_name,
        'products': [],
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    welcome_text = """
🔥 **Thunder Tech Store သို့ ကြိုးဆိုကြည့်ပါ** 🔥

ကျွန်တော်တို့ ရောင်းချတဲ့ ကုန်ပစ္စည်းများ:

🤖 Gemini Plan
🔒 Express VPN 1 Month  
🎬 CapCut Pro
🛡️ F-Secure VPN 5 Device

အောက်က ခလုတ်တွေမှ ကုန်ပစ္စည်း ရွေးချယ်ပါ:
    """
    
    keyboard = []
    for product in CONFIG['products']:
        keyboard.append([
            InlineKeyboardButton(
                f"{product['emoji']} {product['name']}",
                callback_data=f"product_{product['id']}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ အော်ဒါ ပြီးစီးပါပြီ", callback_data="order_complete")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    await update.message.reply_text(
        "❌ အော်ဒါ ပယ်ဖျက်ပြီးပါပြီ။\n\n/start ကို နှိပ်ပြီး ပြန်စတင်ပါ။"
    )
    return ConversationHandler.END


def main():
    """Start the bot"""
    # Replace with your actual bot token
    TOKEN = "8840360088:AAGFavPhLakUNhsNSh-OiJlRejXLd1nZ6-g"
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_PRODUCT: [
                CallbackQueryHandler(product_selected, pattern="^product_"),
                CallbackQueryHandler(order_complete, pattern="^order_complete$"),
            ],
            CONFIRMING_ORDER: [
                CallbackQueryHandler(finish_order, pattern="^finish_order$"),
                CallbackQueryHandler(restart, pattern="^restart$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Start bot
    print("🤖 Thunder Tech Store Bot စတင်နေပါတယ်...")
    application.run_polling()


if __name__ == '__main__':
    main()
