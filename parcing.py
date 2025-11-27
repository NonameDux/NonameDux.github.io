import asyncio
import json
import os
import re
import glob
from pyrogram import Client
from pyrogram.errors import FloodWait

# --- КОНФИГУРАЦИЯ ---
API_ID = int(os.environ.get("TELEGRAM_API_ID", 0)) 
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
CHANNEL_USERNAME = "@kabi_mlp"
OUTPUT_JSON_FILE = "static/dolls_data.json" 
MEDIA_DIR = "static/doll_images" 
SESSION_NAME = "dolls_parser_session"

os.makedirs("static", exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)

# --- ФУНКЦИЯ ЗАДЕРЖКИ ПРИ FLOODWAIT ---
async def safe_execution(coro):
    """Выполняет корутину с ожиданием, если Telegram просит подождать"""
    while True:
        try:
            return await coro
        except FloodWait as e:
            wait_time = e.value + 10
            print(f"⚠️ [FLOOD WAIT] Ждем {wait_time} секунд...")
            await asyncio.sleep(wait_time)
            print("🔄 Повторяем попытку...")
        except Exception as e:
            raise e

# --- ФУНКЦИИ ФИЛЬТРАЦИИ И ПОИСКА ---
def filter_post(text: str) -> bool:
    if not text: return False
    text_lower = text.lower()
    cond1 = "ціна:" in text_lower and "#наявність" in text_lower
    cond2 = "#передзамовлення" in text_lower 
    return cond1 or cond2

def extract_prices(text: str) -> dict:
    data = {"price": None, "delivery_price": None}
    text_lower = text.lower()
    price_match = re.search(r"ціна:.*?(\d+)", text_lower)
    if price_match:
        data["price"] = price_match.group(1) 
        start_pos = price_match.end(0)
        delivery_match = re.search(r"\+\s*(\d+)\s*дс", text_lower[start_pos:start_pos + 50])
        if delivery_match:
            data["delivery_price"] = delivery_match.group(1)
    return data

def get_file_extension(message) -> str:
    if message.photo: return ".jpg"
    elif message.document: return "." + (message.document.mime_type.split('/')[-1] if message.document.mime_type else "bin")
    elif message.video: return "." + (message.video.mime_type.split('/')[-1] if message.video.mime_type else "bin")
    return ".bin"

def find_existing_photo(message_id: int):
    pattern = os.path.join(MEDIA_DIR, f"{message_id}_photo.*")
    found_files = glob.glob(pattern)
    if found_files:
        full_path = found_files[0].replace(os.sep, '/')
        if "static/" in full_path:
            return full_path[full_path.find("static/"):]
        return full_path
    return None

# --- ГЛАВНАЯ ФУНКЦИЯ ---
async def parse_channel():
    print("-> 🎀 Запуск парсера с защитой от флуда...")
    
    app = Client(SESSION_NAME, API_ID, API_HASH)
    
    # Безопасный старт
    try:
        await safe_execution(app.start())
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return 
    
    dolls_data = []
    
    # Получаем историю (тоже безопасно)
    # get_chat_history возвращает итератор, тут сложнее обернуть в safe_execution целиком,
    # но FloodWait обычно вылетает при получении чанков.
    
    try:
        async for message in app.get_chat_history(CHANNEL_USERNAME, limit=150): 
            post_content = message.text or message.caption or ""
            
            if post_content and filter_post(post_content):
                prices = extract_prices(post_content)
                
                # --- ПОДСЧЕТ КОММЕНТАРИЕВ ---
                # Pyrogram хранит это в replies
                comments_count = 0
                if message.reply_to_message:
                     pass
                try:
                    # Проверяем атрибут replies (объект MessageReplies)
                    if hasattr(message, 'replies') and message.replies:
                        comments_count = message.replies.replies
                except: 
                    comments_count = 0

                doll_entry = {
                    "id": message.id,
                    "text": post_content, 
                    "photo_path": None,
                    "photo_count": 1, 
                    "comment_count": comments_count, # Сохраняем кол-во
                    "is_preorder": "#передзамовлення" in post_content.lower(),
                    "link": f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}/{message.id}",
                    "price": prices["price"],
                    "delivery_price": prices["delivery_price"]
                }
                
                existing_photo = find_existing_photo(message.id)
                
                if existing_photo:
                    doll_entry["photo_path"] = existing_photo
                    # Если фото есть, фото-каунт оставляем 1 (или можно спарсить, но это лишние запросы)
                    # Если критично точное число фото при повторном запуске, нужно сохранять его в JSON и читать оттуда.
                    # Сейчас для скорости оставим как есть, или попробуем media_group_id если есть.
                else:
                    media_to_download = None
                    should_download = False
                    
                    if message.media_group_id:
                        try:
                            # Безопасно получаем группу
                            media_files = await safe_execution(app.get_media_group(message.chat.id, message.id))
                            if media_files and message.id == media_files[0].id:
                                media_to_download = media_files[0]
                                doll_entry["photo_count"] = len(media_files)
                                should_download = True
                        except Exception: pass
                    elif message.photo or message.document:
                        media_to_download = message
                        should_download = True

                    if should_download and media_to_download:
                        try:
                            ext = get_file_extension(media_to_download)
                            file_name = os.path.join(MEDIA_DIR, f"{message.id}_photo{ext}")
                            
                            # БЕЗОПАСНОЕ СКАЧИВАНИЕ
                            file_path = await safe_execution(
                                app.download_media(media_to_download, file_name=file_name)
                            )
                            
                            web_path = file_path.replace(os.sep, '/')
                            if "static/" in web_path:
                                doll_entry["photo_path"] = web_path[web_path.find("static/"):]
                            else:
                                doll_entry["photo_path"] = web_path
                            print(f"  [Down] Фото скачано: {message.id}")
                        except Exception as e:
                            print(f"  ⚠️ Ошибка скачивания {message.id}: {e}")

                dolls_data.append(doll_entry)
                
    except FloodWait as e:
        print(f"CRITICAL FLOOD WAIT in history loop: {e.value}")
        await asyncio.sleep(e.value + 10)
    except Exception as e:
        print(f"Global Error: {e}")

    await app.stop()
    
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(dolls_data, f, ensure_ascii=False, indent=4)
        
    print(f"\n-> ✨ Готово! Обработано товаров: {len(dolls_data)}")

if __name__ == "__main__":
    asyncio.run(parse_channel())
