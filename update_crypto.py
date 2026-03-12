import json
import requests
from datetime import datetime

# --- НАСТРОЙКИ ---
RATES_URL = "https://api.rapira.net/open/market/rates"
PAIR = "USDT/RUB"
MARKUP_RUB = 2.0  # наценка в рублях

def fetch_rapira_rates():
    """Получает данные с публичного эндпоинта Rapira"""
    try:
        response = requests.get(RATES_URL, timeout=15)
        data = response.json()
        
        if data.get("code") != 0 or data.get("message") != "SUCCESS":
            print(f"Ошибка API Rapira: {data.get('message')}")
            return None
        
        # Преобразуем список в словарь для быстрого доступа по символу
        rates_dict = {item["symbol"]: item for item in data.get("data", [])}
        return rates_dict
    except Exception as e:
        print(f"Ошибка при запросе к Rapira: {e}")
        return None

def calculate_rates(rates_dict):
    """Рассчитывает цены покупки/продажи с наценкой"""
    if PAIR not in rates_dict:
        print(f"Пара {PAIR} не найдена в ответе")
        return None
    
    pair_data = rates_dict[PAIR]
    
    # Берём цену последней сделки как базовую
    base_rub = float(pair_data.get("close", 0))
    if base_rub == 0:
        # Если close отсутствует, используем среднее между ask и bid
        ask = float(pair_data.get("askPrice", 0))
        bid = float(pair_data.get("bidPrice", 0))
        base_rub = (ask + bid) / 2
        if base_rub == 0:
            print("Не удалось определить базовый курс")
            return None
    
    # Применяем наценку
    buy_rub = base_rub + MARKUP_RUB   # цена покупки для клиента
    sell_rub = base_rub - MARKUP_RUB  # цена продажи для клиента
    
    # Для USD используем те же значения (USDT ≈ USD)
    usd_buy = buy_rub
    usd_sell = sell_rub
    
    # Для USDT/USD оставляем 1.0 (можно изменить при необходимости)
    usdt_usd_buy = 1.0
    usdt_usd_sell = 1.0
    
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rates": {
            "USD": {
                "buy": round(usd_buy, 2),
                "sell": round(usd_sell, 2)
            },
            "USDT": {
                "buy_usd": round(usdt_usd_buy, 3),
                "sell_usd": round(usdt_usd_sell, 3),
                "buy_rub": round(buy_rub, 2),
                "sell_rub": round(sell_rub, 2)
            }
        }
    }
    return output

def fetch_and_save_rates():
    print(f"🔄 Запрос к Rapira: {datetime.now()}")
    rates_dict = fetch_rapira_rates()
    if not rates_dict:
        return
    
    output = calculate_rates(rates_dict)
    if not output:
        return
    
    with open('crypto_rates.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Данные успешно обновлены: {output['last_update']}")
    print(f"   USD: buy = {output['rates']['USD']['buy']} ₽, sell = {output['rates']['USD']['sell']} ₽")
    print(f"   USDT: buy_usd = {output['rates']['USDT']['buy_usd']}, sell_usd = {output['rates']['USDT']['sell_usd']}")
    print(f"   USDT: buy_rub = {output['rates']['USDT']['buy_rub']} ₽, sell_rub = {output['rates']['USDT']['sell_rub']} ₽")

if __name__ == "__main__":
    fetch_and_save_rates()