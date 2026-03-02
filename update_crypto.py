import json
import requests
from datetime import datetime

# --- НАСТРОЙКИ ---
CRYPTORANK_API_KEY = "ef134d41efab8496de9c7caf4837b7c4790bad0ba4e7011a39a2d214f44c"
CRYPTORANK_URL = "https://api.cryptorank.io/v2/currencies"
FIXER_API_KEY = "6a3736274566c974989f265506934baa"
FIXER_URL = f"http://data.fixer.io/api/latest?access_key={FIXER_API_KEY}"

# Интересующие криптовалюты
CURRENCIES = ["USDT"]

# Настройки спреда (в процентах от среднего курса)
# Для USD/RUB: используем курс, полученный из USDT/RUB и USDT/USD
SPREAD_USD = 0.02  # 2% (покупка ниже рынка, продажа выше)
# Для USDT/RUB и USDT/USD
SPREAD_USDT = 0.015  # 1.5%

def get_usd_rates():
    """Получает курсы криптовалют к USD через CryptoRank"""
    headers = {"X-Api-Key": CRYPTORANK_API_KEY}
    params = {"symbol": ",".join(CURRENCIES)}
    try:
        response = requests.get(CRYPTORANK_URL, headers=headers, params=params, timeout=15)
        data = response.json()
        if not isinstance(data.get("data"), list):
            print(f"Неожиданный формат ответа: {data}")
            return None
        usd_rates = {}
        for item in data["data"]:
            symbol = item.get("symbol")
            price_str = item.get("price")
            if symbol and price_str:
                usd_rates[symbol] = float(price_str)
        return usd_rates
    except Exception as e:
        print(f"Ошибка CryptoRank: {e}")
        return None

def get_fiat_rates():
    """Получает курс USD/RUB через Fixer.io (и фиксированный AED/USD)"""
    try:
        response = requests.get(FIXER_URL, timeout=15)
        data = response.json()
        if not data.get("success"):
            print("Ошибка Fixer.io")
            return None
        rates = data["rates"]
        eur_rub = rates["RUB"]
        eur_usd = rates["USD"]
        usd_rub = eur_rub / eur_usd
        return {"RUB": usd_rub}
    except Exception as e:
        print(f"Ошибка Fixer.io: {e}")
        return None

def calculate_buy_sell(price, spread):
    """
    Рассчитывает цену покупки и продажи на основе среднего курса.
    Покупка (вы хотите купить) – клиент платит, значит цена выше среднего.
    Продажа (вы хотите продать) – клиент получает, значит цена ниже среднего.
    В примере пользователя: покупка USD = 77.20 (выше), продажа = 75.80 (ниже).
    Значит, покупка = средний * (1 + spread/2), продажа = средний * (1 - spread/2)
    """
    half_spread = spread / 2
    buy = price * (1 + half_spread)
    sell = price * (1 - half_spread)
    return round(buy, 2), round(sell, 2)

def fetch_and_save_rates():
    usd_rates = get_usd_rates()
    if not usd_rates or "USDT" not in usd_rates:
        print("Не удалось получить курс USDT/USD")
        return
    fiat_rates = get_fiat_rates()
    if not fiat_rates:
        return

    # Средний курс USD/RUB через USDT
    usdt_usd = usd_rates["USDT"]
    usd_rub_avg = fiat_rates["RUB"]  # это курс USD/RUB, уже полученный через Fixer.io
    # Но можно и через USDT: usdt_rub / usdt_usd, но у нас уже есть прямой usd_rub_avg.
    # Для согласованности используем usd_rub_avg из Fixer.io.

    # Расчет для USD
    usd_buy, usd_sell = calculate_buy_sell(usd_rub_avg, SPREAD_USD)

    # Расчет для USDT
    usdt_usd_buy, usdt_usd_sell = calculate_buy_sell(usdt_usd, SPREAD_USDT)
    # Курс USDT/RUB = usdt_usd * usd_rub_avg
    usdt_rub_avg = usdt_usd * usd_rub_avg
    usdt_rub_buy, usdt_rub_sell = calculate_buy_sell(usdt_rub_avg, SPREAD_USDT)

    # Формируем выходные данные
    output = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rates": {
            "USD": {
                "buy": usd_buy,
                "sell": usd_sell
            },
            "USDT": {
                "buy_usd": usdt_usd_buy,
                "sell_usd": usdt_usd_sell,
                "buy_rub": usdt_rub_buy,
                "sell_rub": usdt_rub_sell
            }
        }
    }

    with open('crypto_rates.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Данные обновлены: {output['last_update']}")
    print(f"   USD: buy={usd_buy}, sell={usd_sell}")
    print(f"   USDT: buy_usd={usdt_usd_buy}, sell_usd={usdt_usd_sell}, buy_rub={usdt_rub_buy}, sell_rub={usdt_rub_sell}")

if __name__ == "__main__":
    fetch_and_save_rates()