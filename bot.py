import logging
import json
import os
from typing import Dict, List
from dataclasses import dataclass, asdict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8448447609:AAFEF95pEPD3_uY9uCPhPhcUlf1oIMjZnco"
# ID админа
ADMIN_CHAT_ID = 7973988177

# Структура для хранения данных
@dataclass
class BotData:
    username: str = "v3estnikov.t.me"
    anonymous_url: str = "https://t.me/anonaskorobot?start=7973988177"
    card_number: str = "2204120132703386"
    crypto_url: str = "http://t.me/send?start=IVKF2M5j40O5"
    
    # Структура для ссылок
    links: Dict[str, Dict[str, str]] = None
    
    # Статистика
    user_ids: List[int] = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = {
                "reviews": {"title": "Отзывы", "url": ""},
                "channel": {"title": "Канал", "url": ""},
                "reallife": {"title": "Real Life", "url": ""},
                "project": {"title": "Проект", "url": ""}
            }
        if self.user_ids is None:
            self.user_ids = []

class BotDatabase:
    def __init__(self, filename="bot_data.json"):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self) -> BotData:
        """Загружает данные из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data_dict = json.load(f)
                    return BotData(**data_dict)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
        return BotData()
    
    def save_data(self):
        """Сохраняет данные в файл"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.data), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def update_link(self, category: str, url: str):
        """Обновляет ссылку в категории"""
        if category in self.data.links:
            self.data.links[category]["url"] = url
            self.save_data()
    
    def add_link_category(self, category: str, title: str):
        """Добавляет новую категорию ссылок"""
        if category not in self.data.links:
            self.data.links[category] = {"title": title, "url": ""}
            self.save_data()
    
    def update_username(self, username: str):
        """Обновляет юзернейм"""
        self.data.username = username
        self.save_data()
    
    def add_user(self, user_id: int):
        """Добавляет пользователя в статистику"""
        if user_id not in self.data.user_ids:
            self.data.user_ids.append(user_id)
            self.save_data()
    
    def get_stats(self) -> Dict:
        """Получает статистику бота"""
        links_with_urls = sum(1 for link in self.data.links.values() if link["url"])
        unique_users = len(self.data.user_ids)
        
        return {
            "username": self.data.username,
            "links_categories": len(self.data.links),
            "links_with_urls": links_with_urls,
            "total_links": len(self.data.links),
            "unique_users": unique_users
        }

# Инициализация базы данных
db = BotDatabase()

def add_footer(text: str) -> str:
    """Добавляет мини-инфо внизу текста"""
    footer = "\n\n━━━━━━━━━━━━━━━━"
    return text + footer

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    # Добавляем пользователя в статистику
    user_id = update.effective_user.id
    db.add_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🔗 Ссылки", callback_data="links")],
        [InlineKeyboardButton("📨 Анонимные сообщения", callback_data="anonymous")],
        [InlineKeyboardButton("👤 Актуальный юзернейм", callback_data="username")],
        [InlineKeyboardButton("💳 Донат", callback_data="donate")],
    ]
    
    if update.effective_user.id == ADMIN_CHAT_ID:
        keyboard.append([InlineKeyboardButton("🛠️ Админ панель", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = add_footer(
        "👋 Привет! Я бот для управления ссылками и коммуникацией.\n"
        "Выберите нужный раздел:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)

async def show_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню ссылок"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for key, link in db.data.links.items():
        if link["url"]:  # Показываем только если есть ссылка
            keyboard.append([InlineKeyboardButton(
                f"• {link['title']}", 
                url=link["url"]
            )])
    
    # Добавляем кнопку "Назад" внизу
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Простой текст без указания, добавлена ссылка или нет
    text = add_footer("🔗 *Доступные ссылки:*\n\nВыберите нужную ссылку:")
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_anonymous(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает анонимные сообщения"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📝 Отправить анонимное сообщение", url=db.data.anonymous_url)],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = add_footer(
        "📨 *Анонимные сообщения*\n\n"
        "Вы можете отправить мне анонимное сообщение через специального бота. "
        "Ваше сообщение будет доставлено мне полностью анонимно."
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает актуальный юзернейм"""
    query = update.callback_query
    await query.answer()
    
    # Создаем ссылку из юзернейма
    if db.data.username.startswith("@"):
        username_for_url = db.data.username[1:]
    elif db.data.username.startswith("https://t.me/"):
        username_for_url = db.data.username[13:]
    elif db.data.username.startswith("t.me/"):
        username_for_url = db.data.username[5:]
    else:
        username_for_url = db.data.username
    
    # Убираем возможные .t.me или другие суффиксы
    username_for_url = username_for_url.replace(".t.me", "")
    
    keyboard = [
        [InlineKeyboardButton("🔗 Перейти в профиль", url=f"https://t.me/{username_for_url}")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = add_footer(f"👤 *Актуальный юзернейм:*\n\n`{db.data.username}`")
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает информацию о донате"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("💳 Перевести на карту", callback_data="show_card")],
        [InlineKeyboardButton("₿ Перевести крипту", url=db.data.crypto_url)],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = add_footer(
        "💳 *Поддержать автора*\n\n"
        "Выберите способ для доната:"
    )
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает номер карты"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад в донат", callback_data="donate")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = add_footer(f"💳 *Карта для перевода:*\n\n`{db.data.card_number}`")
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает админ панель"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("Доступ запрещен!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("➕ Добавить ссылку", callback_data="add_link")],
        [InlineKeyboardButton("📝 Изменить юзернейм", callback_data="edit_username")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = add_footer("🛠️ *Админ панель*\n\nВыберите действие:")
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("Доступ запрещен!", show_alert=True)
        return
    
    stats = db.get_stats()
    
    text = add_footer(
        f"📊 *Статистика бота:*\n\n"
        f"👤 Текущий юзернейм: `{stats['username']}`\n"
        f"👥 Уникальных пользователей: {stats['unique_users']}\n"
        f"📁 Категорий ссылок: {stats['links_categories']}\n"
        f"🔗 Ссылок с URL: {stats['links_with_urls']}\n"
        f"📝 Всего слотов для ссылок: {stats['total_links']}\n\n"
        "*Категории:*\n"
    )
    
    for key, link in db.data.links.items():
        status = "✅" if link["url"] else "❌"
        text += f"\n{status} {link['title']} (`{key}`)"
        if link["url"]:
            text += f"\n   └ {link['url'][:50]}..."
    
    keyboard = [
        [InlineKeyboardButton("🔙 Админ панель", callback_data="admin")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def add_link_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню добавления/редактирования ссылок"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.answer("Доступ запрещен!", show_alert=True)
        return
    
    keyboard = []
    for key, link in db.data.links.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{'✅' if link['url'] else '❌'} {link['title']}",
                callback_data=f"edit_link_{key}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ Новая категория", callback_data="new_category")])
    keyboard.append([InlineKeyboardButton("🔙 Админ панель", callback_data="admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📝 *Редактирование ссылок*\n\nВыберите категорию для редактирования:"
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def edit_link_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос на ввод новой ссылки"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_CHAT_ID:
        return
    
    data = query.data
    if data.startswith("edit_link_"):
        category = data[10:]
        context.user_data["edit_link_category"] = category
        
        current_link = db.data.links[category]["url"]
        current_text = f"\nТекущая ссылка: {current_link}" if current_link else ""
        
        text = f"📝 *Редактирование: {db.data.links[category]['title']}*\n\nОтправьте новую ссылку.{current_text}"
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="add_link")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif data == "new_category":
        context.user_data["waiting_for_new_category"] = True
        
        text = "➕ *Новая категория*\n\nОтправьте название новой категории (например, 'Блог'):"
        
        keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="add_link")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def edit_username_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос на ввод нового юзернейма"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_CHAT_ID:
        return
    
    context.user_data["waiting_for_username"] = True
    
    text = f"👤 *Изменение юзернейма*\n\nТекущий юзернейм: `{db.data.username}`\n\nОтправьте новый юзернейм:"
    
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений для админа"""
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    
    if update.message.text:
        text = update.message.text
        
        # Обработка новой ссылки
        if "edit_link_category" in context.user_data:
            category = context.user_data.pop("edit_link_category")
            
            if text.startswith(("http://", "https://", "t.me/")):
                db.update_link(category, text)
                
                await update.message.reply_text(
                    f"✅ Ссылка для '{db.data.links[category]['title']}' обновлена!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📝 Еще ссылки", callback_data="add_link")],
                        [InlineKeyboardButton("🏠 Главная", callback_data="back_to_main")]
                    ])
                )
            else:
                await update.message.reply_text(
                    "❌ Неверный формат ссылки. Начните с http://, https:// или t.me/"
                )
        
        # Обработка новой категории
        elif context.user_data.get("waiting_for_new_category"):
            context.user_data.pop("waiting_for_new_category")
            
            # Создаем ключ из названия
            key = text.lower().replace(" ", "_")
            db.add_link_category(key, text)
            
            await update.message.reply_text(
                f"✅ Категория '{text}' добавлена! Теперь добавьте ссылку для нее.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"📝 Добавить ссылку для '{text}'", callback_data=f"edit_link_{key}")],
                    [InlineKeyboardButton("📝 Другие ссылки", callback_data="add_link")]
                ])
            )
        
        # Обработка нового юзернейма
        elif context.user_data.get("waiting_for_username"):
            context.user_data.pop("waiting_for_username")
            
            db.update_username(text)
            
            await update.message.reply_text(
                f"✅ Юзернейм обновлен на: `{text}`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Главная", callback_data="back_to_main")]
                ])
            )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    data = query.data
    
    handlers = {
        "links": show_links,
        "anonymous": show_anonymous,
        "username": show_username,
        "donate": show_donate,
        "show_card": show_card,
        "admin": admin_panel,
        "stats": show_stats,
        "add_link": add_link_menu,
        "edit_username": edit_username_prompt,
        "back_to_main": start
    }
    
    if data in handlers:
        await handlers[data](update, context)
    elif data.startswith("edit_link_") or data == "new_category":
        await edit_link_prompt(update, context)

def main():
    """Запуск бота"""
    # Создаем Application с токеном
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    
    # Обработчики кнопок
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Обработчик текстовых сообщений (для админа)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    print("Бот запущен...")
    print(f"ID администратора: {ADMIN_CHAT_ID}")
    print("Нажмите Ctrl+C для остановки")
    
    # Запускаем polling
    application.run_polling()

if __name__ == '__main__':
    main()
