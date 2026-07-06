import asyncio
import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
API_ID = 26259835
API_HASH = "3fa32264398920f001dd2428b42060f6"
BOT_TOKEN = "8849260350:AAH3YDz5Qz6KfkfTCSPO2mzRu6nGUkrcGtY"  # Токен от бота, который будет управлять очисткой

# Файл для хранения белого списка
WHITELIST_FILE = "whitelist.json"


# ============================================================
# БЕЛЫЙ СПИСОК (ЗАГРУЗКА/СОХРАНЕНИЕ)
# ============================================================
def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_whitelist(data):
    with open(WHITELIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================
# СОЗДАНИЕ БОТА И КЛИЕНТА
# ============================================================
bot = Client("cleaner_bot", bot_token=BOT_TOKEN)
user_app = Client("user_session", api_id=API_ID, api_hash=API_HASH)

whitelist = load_whitelist()


# ============================================================
# ФУНКЦИЯ ПРОВЕРКИ БЕЛОГО СПИСКА
# ============================================================
def is_whitelisted(chat_title: str) -> bool:
    for name in whitelist:
        if name.lower() in chat_title.lower():
            return True
    return False


# ============================================================
# КОМАНДЫ БОТА
# ============================================================

# === СТАРТ ===
@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    await message.reply_text(
        "🔥 <b>БОТ ДЛЯ ОЧИСТКИ АККАУНТА</b>\n\n"
        "Я помогу вам выйти из всех групп и каналов, кроме тех, что в белом списке.\n\n"
        "📋 <b>Команды:</b>\n"
        "/start - Показать это сообщение\n"
        "/whitelist - Показать белый список\n"
        "/add [название] - Добавить чат в белый список\n"
        "/remove [название] - Удалить чат из белого списка\n"
        "/clear_whitelist - Очистить весь белый список\n"
        "/run_clean - Запустить очистку аккаунта\n"
        "/stop_clean - Остановить очистку\n\n"
        "⚠️ <b>ВНИМАНИЕ:</b> Бот будет выходить из ВСЕХ чатов, кроме указанных в белом списке!",
        parse_mode="HTML"
    )


# === ПОКАЗАТЬ БЕЛЫЙ СПИСОК ===
@bot.on_message(filters.command("whitelist"))
async def show_whitelist(client, message: Message):
    if not whitelist:
        await message.reply_text("📭 Белый список пуст.")
        return

    text = "📋 <b>БЕЛЫЙ СПИСОК</b>\n\n"
    for i, name in enumerate(whitelist, 1):
        text += f"{i}. {name}\n"

    await message.reply_text(text, parse_mode="HTML")


# === ДОБАВИТЬ В БЕЛЫЙ СПИСОК ===
@bot.on_message(filters.command("add") & filters.reply)
async def add_to_whitelist(client, message: Message):
    # Получаем название из ответа на сообщение
    if message.reply_to_message and message.reply_to_message.text:
        name = message.reply_to_message.text.strip()
    else:
        # Или из текста команды
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            await message.reply_text(
                "❌ Укажите название чата.\n\n"
                "Пример: /add Моя группа\n"
                "Или ответьте на сообщение с названием чата командой /add"
            )
            return
        name = parts[1].strip()

    if not name:
        await message.reply_text("❌ Название не может быть пустым.")
        return

    if name in whitelist:
        await message.reply_text(f"ℹ️ Чат «{name}» уже есть в белом списке.")
        return

    whitelist.append(name)
    save_whitelist(whitelist)
    await message.reply_text(f"✅ Чат «{name}» добавлен в белый список.")


# === УДАЛИТЬ ИЗ БЕЛОГО СПИСКА ===
@bot.on_message(filters.command("remove"))
async def remove_from_whitelist(client, message: Message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.reply_text(
            "❌ Укажите название чата для удаления.\n\n"
            "Пример: /remove Моя группа"
        )
        return

    name = parts[1].strip()

    if name not in whitelist:
        await message.reply_text(f"❌ Чат «{name}» не найден в белом списке.")
        return

    whitelist.remove(name)
    save_whitelist(whitelist)
    await message.reply_text(f"✅ Чат «{name}» удалён из белого списка.")


# === ОЧИСТИТЬ ВЕСЬ БЕЛЫЙ СПИСОК ===
@bot.on_message(filters.command("clear_whitelist"))
async def clear_whitelist_command(client, message: Message):
    if not whitelist:
        await message.reply_text("📭 Белый список уже пуст.")
        return

    # Подтверждение
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, очистить всё", callback_data="confirm_clear_whitelist")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel_clear_whitelist")]
    ])

    await message.reply_text(
        f"⚠️ <b>Вы уверены?</b>\n\n"
        f"Будет удалено {len(whitelist)} записей из белого списка.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@bot.on_callback_query(filters.regex("confirm_clear_whitelist"))
async def confirm_clear_whitelist(client, callback):
    global whitelist
    whitelist = []
    save_whitelist(whitelist)
    await callback.message.edit_text("✅ Белый список очищен.")
    await callback.answer()


@bot.on_callback_query(filters.regex("cancel_clear_whitelist"))
async def cancel_clear_whitelist(client, callback):
    await callback.message.edit_text("❌ Отменено.")
    await callback.answer()


# === ЗАПУСТИТЬ ОЧИСТКУ ===
@bot.on_message(filters.command("run_clean"))
async def run_clean_command(client, message: Message):
    if not whitelist:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить в белый список", callback_data="add_to_whitelist")],
            [InlineKeyboardButton("🚀 Всё равно запустить", callback_data="run_clean_anyway")]
        ])

        await message.reply_text(
            "⚠️ <b>БЕЛЫЙ СПИСОК ПУСТ!</b>\n\n"
            "Если запустить очистку сейчас, бот выйдет из ВСЕХ чатов.\n\n"
            "Добавьте чаты в белый список или подтвердите запуск.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # Запускаем очистку
    await message.reply_text(
        f"🚀 <b>ЗАПУСК ОЧИСТКИ</b>\n\n"
        f"📋 В белом списке: {len(whitelist)} чатов\n"
        f"⚠️ Бот выйдет из всех чатов, кроме указанных.\n\n"
        f"<i>Процесс может занять несколько минут...</i>",
        parse_mode="HTML"
    )

    # Запускаем очистку в фоне
    asyncio.create_task(run_cleanup(message.chat.id))


# === ОСТАНОВИТЬ ОЧИСТКУ (флаг) ===
cleanup_running = False


@bot.on_message(filters.command("stop_clean"))
async def stop_clean_command(client, message: Message):
    global cleanup_running
    cleanup_running = False
    await message.reply_text("⏹️ Очистка остановлена.")


# ============================================================
# ФУНКЦИЯ ОЧИСТКИ
# ============================================================
async def run_cleanup(chat_id: int):
    global cleanup_running
    cleanup_running = True

    try:
        # Запускаем пользовательский клиент
        await user_app.start()

        # Получаем все диалоги
        dialogs = []
        async for dialog in user_app.get_dialogs():
            dialogs.append(dialog)

        total = len(dialogs)
        processed = 0
        left = 0
        skipped = 0
        errors = 0

        # Отправляем статус
        await bot.send_message(chat_id, f"🔍 Найдено {total} чатов. Начинаем очистку...")

        for dialog in dialogs:
            if not cleanup_running:
                await bot.send_message(chat_id, "⏹️ Очистка остановлена пользователем.")
                return

            chat = dialog.chat
            chat_title = chat.title or "Без названия"
            processed += 1

            # Проверяем белый список
            if is_whitelisted(chat_title):
                skipped += 1
                # Периодически сообщаем прогресс
                if processed % 10 == 0:
                    await bot.send_message(
                        chat_id,
                        f"⏳ Прогресс: {processed}/{total} | "
                        f"Выходов: {left} | Пропущено: {skipped} | Ошибок: {errors}"
                    )
                continue

            try:
                # Выходим из чата
                await user_app.leave_chat(chat.id)
                left += 1

                # Удаляем диалог
                await user_app.delete_dialog(chat.id)

                # Логируем
                await bot.send_message(
                    chat_id,
                    f"🚪 Выход: {chat_title}"
                )

            except Exception as e:
                errors += 1
                await bot.send_message(
                    chat_id,
                    f"❌ Ошибка в {chat_title}: {str(e)[:100]}"
                )

            # Пауза
            await asyncio.sleep(0.5)

        # Финальный отчёт
        await bot.send_message(
            chat_id,
            f"✅ <b>ОЧИСТКА ЗАВЕРШЕНА!</b>\n\n"
            f"📊 Всего чатов: {total}\n"
            f"🚪 Выходов: {left}\n"
            f"📋 Пропущено (белый список): {skipped}\n"
            f"❌ Ошибок: {errors}\n\n"
            f"<b>Белый список ({len(whitelist)}):</b>\n" + "\n".join([f"• {name}" for name in whitelist[:10]]),
            parse_mode="HTML"
        )

    except Exception as e:
        await bot.send_message(chat_id, f"❌ Критическая ошибка: {str(e)}")
    finally:
        await user_app.stop()
        cleanup_running = False


# === ДОБАВЛЕНИЕ В БЕЛЫЙ СПИСОК ЧЕРЕЗ КНОПКУ ===
@bot.on_callback_query(filters.regex("add_to_whitelist"))
async def add_to_whitelist_callback(client, callback):
    await callback.message.edit_text(
        "📝 Отправьте название чата для добавления в белый список.\n\n"
        "Используйте команду /add [название]\n"
        "Или ответьте на сообщение с названием чата командой /add"
    )
    await callback.answer()


# === ЗАПУСК ОЧИСТКИ НЕСМОТРЯ НА ПУСТОЙ БЕЛЫЙ СПИСОК ===
@bot.on_callback_query(filters.regex("run_clean_anyway"))
async def run_clean_anyway_callback(client, callback):
    await callback.message.edit_text("🚀 Запуск очистки (белый список пуст)...")
    await callback.answer()
    asyncio.create_task(run_cleanup(callback.message.chat.id))


# ============================================================
# ЗАПУСК БОТА
# ============================================================
print("🔥 Бот для очистки аккаунта запущен!")
print(f"📋 Белый список: {len(whitelist)} записей")
print("\nКоманды бота:")
print("/start - Показать меню")
print("/whitelist - Показать белый список")
print("/add [название] - Добавить чат")
print("/remove [название] - Удалить чат")
print("/clear_whitelist - Очистить белый список")
print("/run_clean - Запустить очистку")
print("/stop_clean - Остановить очистку")

bot.run()
