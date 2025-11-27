import asyncio
import json
import os
import re
from pyrogram import Client
from pyrogram.enums import MessageMediaType

# --- КОНФИГУРАЦИЯ ---
# ! На Render эти данные должны быть в переменных окружения.
API_ID = 32614477 
API_HASH = "ea52bfb513bf2a15a9e65b6321ecdcd3"
CHANNEL_USERNAME = "@kabi_mlp"
OUTPUT_JSON_FILE = "static/dolls_data.json" 
MEDIA_DIR = "static/doll_images" 
SESSION_NAME = "dolls_parser_session"

# Создаем папки, если их нет
os.makedirs("static", exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)


# --- ФУНКЦИЯ ФИЛЬТРАЦИИ ---
def filter_post(text: str) -> bool:
    """Проверяет, соответствует ли текст поста заданным условиям."""
    
    if not text:
        return False
        
    text_lower = text.lower()

    # Условие 1: Должен содержать "ціна:" И "#наявність"
    cond1_price = "ціна:" in text_lower
    cond1_stock = "#наявність" in text_lower
    cond1 = cond1_price and cond1_stock

    # Условие 2: Должен содержать "#передзамовлення"
    cond2 = "#передзамовлення" in text_lower 

    return cond1 or cond2


# --- НОВАЯ ФУНКЦИЯ: ИЗВЛЕЧЕНИЕ ЦЕН ---
def extract_prices(text: str) -> dict:
    """Извлекает основную цену и цену доставки из текста поста."""
    
    data = {"price": None, "delivery_price": None}
    text_lower = text.lower()
    
    # 1. Находим основную цену (первое число, следующее за "ціна:")
    # Шаблон: (ціна:.*?)(\d+) - ищем 'ціна:', захватываем первое число
    price_match = re.search(r"ціна:.*?(\d+)", text_lower)
    if price_match:
        data["price"] = price_match.group(1) 
        
        # 2. Поиск доставки (только если найдена цена)
        # Ищем паттерн '+ ЧИСЛО дс'
        # Ищем в радиусе 50 символов после начала основной цены для точности
        start_pos = price_match.end(0)
        delivery_match = re.search(r"\+\s*(\d+)\s*дс", text_lower[start_pos:start_pos + 50])
        
        if delivery_match:
            data["delivery_price"] = delivery_match.group(1)
            
    return data


# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: ПОЛУЧЕНИЕ РАСШИРЕНИЯ ---
def get_file_extension(message) -> str:
    """Определяет расширение файла на основе его MIME-типа."""
    
    if message.photo:
        return ".jpg" # Фотографии Telegram всегда конвертируются в JPG
    elif message.document:
        mime = message.document.mime_type
    elif message.video:
        mime = message.video.mime_type
    elif message.sticker:
        # Стикеры обычно webp/png/tgs, но для целей галереи лучше оставить .webp или .png
        return ".webp"
    else:
        return ".bin" # Запасное расширение

    # Извлекаем расширение из MIME-типа (image/jpeg -> .jpeg)
    if mime:
        return "." + mime.split('/')[-1]
    return ".bin"


# --- ОСНОВНАЯ ФУНКЦИЯ ПАРСИНГА ---
async def parse_channel():
    """Основная функция парсинга."""
    
    print("-> Запуск парсинга канала...")
    
    app = Client(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await app.start()
    except Exception as e:
        print(f"Ошибка подключения к Telegram: {e}")
        return 
    
    dolls_data = []
    processed_count = 0 
    
    async for message in app.get_chat_history(CHANNEL_USERNAME, limit=60): 
        
        processed_count += 1
        
        # === БЛОК УНИВЕРСАЛЬНОГО ПОЛУЧЕНИЯ ТЕКСТА ===
        post_content = message.text or message.caption or ""
        
        # --- БЛОК ОТЛАДКИ ---
        message_text_debug = post_content.strip() if post_content else "--- НЕТ ТЕКСТА ---"
        first_line = message_text_debug.split('\n', 1)[0]
        is_filtered = filter_post(post_content)
        print(f"[{processed_count}] ID:{message.id} | ФИЛЬТР: {'✅' if is_filtered else '❌'} | ТЕКСТ: '{first_line}'")
        # -------------------

        
        # ОСНОВНОЙ БЛОК: применяем фильтр и сохраняем
        if post_content and filter_post(post_content):
            
            prices = extract_prices(post_content) # Извлекаем цены
            
            doll_entry = {
                "id": message.id,
                "text": post_content, 
                "photo_path": None,
                "is_preorder": "#передзамовлення" in post_content.lower(),
                "link": f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}/{message.id}",
                "price": prices["price"],
                "delivery_price": prices["delivery_price"]
            }
            
            
            # === БЛОК СКАЧИВАНИЯ МЕДИА С ПРАВИЛЬНЫМ РАСШИРЕНИЕМ ===
            media_to_download = None
            if message.photo:
                media_to_download = message
            elif message.media and message.media == MessageMediaType.WEB_PAGE and message.web_page and message.web_page.photo:
                # Если это ссылка с превью-фото
                media_to_download = message
            elif message.media and message.media == MessageMediaType.DOCUMENT:
                 media_to_download = message
            
            
            if media_to_download:
                try:
                    # Определяем расширение
                    ext = get_file_extension(media_to_download)
                    file_name_prefix = os.path.join(MEDIA_DIR, f"{message.id}_photo")
                    
                    # Скачиваем фото с корректным расширением
                    file_path = await app.download_media(
                         media_to_download,
                         file_name=file_name_prefix + ext
                    )
                    
                    # Форматирование пути для веб-доступа (удаление абсолютного пути, замена слэшей)
                    web_path = file_path.replace(os.sep, '/')
                    start_index = web_path.find("static/")
                    
                    if start_index != -1:
                        final_web_path = web_path[start_index:]
                    else:
                        final_web_path = web_path
                        
                    doll_entry["photo_path"] = final_web_path
                    
                except Exception as e:
                    print(f"Ошибка при скачивании медиа {message.id}: {e}")
            
            # Обработка альбомов (MediaGroup)
            elif message.media_group_id: 
                try:
                    # Получаем первый медиа-файл из группы
                    media_files = await app.get_media_group(message.chat.id, message.id)
                    
                    # Проверяем, что это сообщение, к которому привязан текст (обычно первое)
                    if media_files and message.id == media_files[0].id:
                        first_media = media_files[0]
                        ext = get_file_extension(first_media)
                        file_name_prefix = os.path.join(MEDIA_DIR, f"{message.id}_photo")
                        
                        file_path = await app.download_media(
                            first_media,
                            file_name=file_name_prefix + ext
                        )
                        
                        web_path = file_path.replace(os.sep, '/')
                        start_index = web_path.find("static/")
                        final_web_path = web_path[start_index:] if start_index != -1 else web_path
                        
                        doll_entry["photo_path"] = final_web_path
                        
                except Exception:
                    pass # Игнорируем ошибки групп

            dolls_data.append(doll_entry)
            print(f"  [+] УСПЕШНО ДОБАВЛЕНО по фильтру пост ID: {message.id}") 
            
    await app.stop()
    
    # Записываем данные в JSON файл
    with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(dolls_data, f, ensure_ascii=False, indent=4)
        
    print(f"-> Парсинг завершен. Сохранено {len(dolls_data)} записей в {OUTPUT_JSON_FILE}. Обработано всего: {processed_count}")


if __name__ == "__main__":
    asyncio.run(parse_channel())