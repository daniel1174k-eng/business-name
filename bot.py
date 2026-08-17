import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get tokens from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

# Hugging Face API setup
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

def call_huggingface_api(prompt):
    """Call Hugging Face API to generate names"""
    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.8,
                "top_p": 0.95,
                "do_sample": True,
                "return_full_text": False
            }
        }

        logger.info("Calling Hugging Face API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'No response')
            return str(result)
        else:
            return f"API Error {response.status_code}: {response.text}"

    except requests.exceptions.Timeout:
        return "⏰ The request took too long. Please try again with a shorter description."
    except Exception as e:
        return f"❌ Error: {str(e)}"

def parse_names(text):
    """Parse the AI response into a list of names with reasoning"""
    lines = text.strip().split('\n')
    names = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line and line[0].isdigit():
            parts = line.split('.', 1)
            if len(parts) > 1:
                name_part = parts[1].strip()
                if ' - ' in name_part:
                    name, reasoning = name_part.split(' - ', 1)
                    names.append({'name': name.strip(), 'reasoning': reasoning.strip()})
                elif ':' in name_part:
                    name, reasoning = name_part.split(':', 1)
                    names.append({'name': name.strip(), 'reasoning': reasoning.strip()})
                else:
                    names.append({'name': name_part, 'reasoning': ''})

    if not names:
        for line in lines:
            if line and not line.startswith('Here are') and not line.startswith('```'):
                clean_line = line.lstrip('•-* ').strip()
                if clean_line and len(clean_line) > 3:
                    names.append({'name': clean_line, 'reasoning': ''})

    return names if names else [{'name': text[:150] + '...', 'reasoning': 'Generated names'}]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when /start is issued."""
    user = update.effective_user
    
    welcome_message = f"""
👋 *Welcome to Business Name Generator Bot!*

Hi {user.first_name}! I'm here to help you create creative business names.

🚀 *How to use me:*
Simply send me a description of your business, and I'll generate 10 creative name ideas!

📝 *Examples:*
• "A sustainable fashion brand using recycled materials"
• "A vegan restaurant serving healthy plant-based meals"  
• "A tech startup creating AI-powered tools for small businesses"

💡 *Tips:*
• Be specific about what you do
• Mention your target audience
• Include your unique selling point

📊 *Commands:*
/start - Show this welcome message
/help - Get help and tips
/examples - See business description examples
/about - Learn more about this bot

*Ready to start?* Just describe your business! 🎯
"""

    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a help message."""
    help_text = """
🆘 *How to use this bot:*

1️⃣ *Describe your business*
Send a message describing what your business does.

2️⃣ *Get name ideas*
The bot will generate 10 creative business names.

3️⃣ *Try different descriptions*
The more detailed your description, the better the names!

📝 *Good examples:*
• "A coffee shop that also serves as a co-working space"
• "An app that connects freelance writers with clients"
• "A subscription box for organic beauty products"

🎯 *Tips for better results:*
• Mention your target audience
• Include what makes you unique
• Describe your products/services
• Add your brand values

❗ *Need help?* Just describe your business and I'll do the rest!
"""

    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )

async def examples_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send example business descriptions."""
    examples_text = """
📋 *Example Business Descriptions:*

1️⃣ *Eco-Fashion*
"Sustainable fashion brand creating eco-friendly clothing from recycled materials, targeting environmentally conscious millennials"

2️⃣ *Vegan Restaurant*  
"Plant-based restaurant serving healthy, organic, and delicious vegan meals in a cozy atmosphere"

3️⃣ *Tech Startup*
"AI-powered platform that helps small businesses automate their customer service using chatbots"

4️⃣ *Fitness App*
"Mobile app that creates personalized workout plans using AI, perfect for busy professionals"

5️⃣ *Coffee Shop*
"Specialty coffee shop that doubles as a co-working space with high-speed WiFi and comfortable seating"

💡 *Copy one of these or create your own!*
"""

    await update.message.reply_text(
        examples_text,
        parse_mode='Markdown'
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about message."""
    about_text = """
🤖 *About This Bot*

This bot uses AI to generate creative business names based on your description.

⚙️ *How it works:*
1. You describe your business
2. AI analyzes your description
3. Generates 10 creative name ideas
4. Each name comes with reasoning

🔧 *Technology:*
• Hugging Face AI models
• Mistral 7B for name generation
• Python Telegram Bot framework

💡 *Free to use!*
No credit card required. Just describe your business and get inspired!

📱 *Share this bot!*
Forward this bot to friends who need business name ideas!

Made with ❤️ for entrepreneurs and creators!
"""

    await update.message.reply_text(
        about_text,
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle business description messages."""
    description = update.message.text.strip()

    if not HUGGINGFACE_API_KEY or HUGGINGFACE_API_KEY == 'hf_YOUR_TOKEN_HERE':
        await update.message.reply_text(
            "❌ *Bot not configured properly!*\n\nThe Hugging Face API key is missing.",
            parse_mode='Markdown'
        )
        return

    thinking_message = await update.message.reply_text(
        "🧠 *Generating creative business names...*\n\nThis may take 10-20 seconds...",
        parse_mode='Markdown'
    )

    try:
        prompt = f"""<|system|>
You are a creative business name generator. Generate unique, catchy, and memorable business names.

<|user|>
Generate 10 creative business names for a business with this description: {description}

Format your response as a numbered list (1-10). For each name, provide a brief explanation of why it works.

<|assistant|>
Here are 10 creative business names for "{description}":

"""

        raw_response = call_huggingface_api(prompt)
        names_list = parse_names(raw_response)

        if names_list:
            response_text = "✨ *Your Business Name Ideas:*\n\n"
            
            for idx, name_data in enumerate(names_list[:10], 1):
                name = name_data.get('name', 'Unknown')
                reasoning = name_data.get('reasoning', '')
                
                response_text += f"{idx}. *{name}*\n"
                if reasoning:
                    response_text += f"   💡 {reasoning}\n"
                response_text += "\n"
            
            response_text += "\n💡 Try different descriptions for more ideas!"
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Try Again", callback_data="retry"),
                    InlineKeyboardButton("📝 Examples", callback_data="examples")
                ],
                [
                    InlineKeyboardButton("📊 Help", callback_data="help"),
                    InlineKeyboardButton("ℹ️ About", callback_data="about")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await thinking_message.edit_text(
                response_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            await thinking_message.edit_text(
                "❌ Sorry, I couldn't generate names. Please try again with a different description.",
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await thinking_message.edit_text(
            f"❌ Error: {str(e)}\n\nPlease try again.",
            parse_mode='Markdown'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "retry":
        await query.edit_message_text(
            "🔄 Ready to try again! Send me a new business description.",
            parse_mode='Markdown'
        )
    
    elif query.data == "examples":
        examples_text = """
📋 *Example Descriptions:*
1. "Sustainable fashion brand creating eco-friendly clothing"
2. "Vegan restaurant serving healthy plant-based meals"
3. "AI-powered platform for small business automation"
4. "Fitness app with personalized workout plans"
5. "Coffee shop with co-working space"

💡 Copy one and send it to me!
"""
        await query.edit_message_text(
            examples_text,
            parse_mode='Markdown'
        )
    
    elif query.data == "help":
        help_text = """
🆘 *Quick Help:*
1. Send me a business description
2. I'll generate 10 creative names
3. Try different descriptions!

Commands:
/start - Welcome
/help - This guide
/examples - Examples
/about - About the bot
"""
        await query.edit_message_text(
            help_text,
            parse_mode='Markdown'
        )
    
    elif query.data == "about":
        about_text = """
🤖 *Business Name Generator Bot*

Creates 10 creative business names using AI!

Powered by Hugging Face AI
Free to use

Ready? Describe your business!
"""
        await query.edit_message_text(
            about_text,
            parse_mode='Markdown'
        )

def main():
    """Start the bot."""
    try:
        # Try the new way (for newer versions)
        application = Application.builder().token(TELEGRAM_TOKEN).build()
    except AttributeError:
        # Fallback for older versions
        try:
            from telegram.ext import Updater
            updater = Updater(TELEGRAM_TOKEN)
            application = updater.application
        except Exception as e:
            print(f"Error creating application: {e}")
            # Final fallback
            application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("examples", examples_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Business Name Generator Bot is running!")
    print("📱 Find your bot on Telegram and send /start")
    application.run_polling()

if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in environment variables!")
        exit(1)
    if not HUGGINGFACE_API_KEY:
        print("❌ ERROR: HUGGINGFACE_API_KEY not found in environment variables!")
        exit(1)
    print("✅ All tokens found. Starting bot...")
    main()
