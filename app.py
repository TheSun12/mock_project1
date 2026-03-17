from flask import Flask, request, Response, g
import random
import string
from datetime import datetime
import sqlite3
from contextlib import contextmanager
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app) 

@contextmanager
def get_db():
    conn = sqlite3.connect('mock_cbr.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id TEXT PRIMARY KEY,
                date TEXT,
                content TEXT,
                status_code INTEGER
            )
        ''')

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_xml_response(date: str) -> str:
    currencies = [
        {"id": "R01010", "numCode": "036", "charCode": "AUD", "nominal": 1, "name": "Австралийский доллар", "value": 16.0102, "vunitRate": 16.0102},
        {"id": "R01035", "numCode": "826", "charCode": "GBP", "nominal": 1, "name": "Фунт стерлингов", "value": 43.8254, "vunitRate": 43.8254},
        {"id": "R01090", "numCode": "974", "charCode": "BYR", "nominal": 1000, "name": "Белорусских рублей", "value": 43.8254, "vunitRate": 43.8254},
        {"id": "R01215", "numCode": "208", "charCode": "DKK", "nominal": 10, "name": "Датских крон", "value": 36.1010, "vunitRate": 3.6101},
        {"id": "R01235", "numCode": "840", "charCode": "USD", "nominal": 1, "name": "Доллар США", "value": 30.9436, "vunitRate": 30.9436},
        {"id": "R01239", "numCode": "978", "charCode": "EUR", "nominal": 1, "name": "Евро", "value": 26.8343, "vunitRate": 26.8343},
        {"id": "R01310", "numCode": "352", "charCode": "ISK", "nominal": 100, "name": "Исландских крон", "value": 30.7958, "vunitRate": 0.307958},
        {"id": "R01335", "numCode": "398", "charCode": "KZT", "nominal": 100, "name": "Тенге", "value": 20.3393, "vunitRate": 0.203393},
        {"id": "R01350", "numCode": "124", "charCode": "CAD", "nominal": 1, "name": "Канадский доллар", "value": 19.3240, "vunitRate": 19.324},
        {"id": "R01535", "numCode": "578", "charCode": "NOK", "nominal": 10, "name": "Норвежских крон", "value": 34.7853, "vunitRate": 3.47853},
        {"id": "R01589", "numCode": "960", "charCode": "XDR", "nominal": 1, "name": "СДР (специальные права заимствования)", "value": 38.4205, "vunitRate": 38.4205},
        {"id": "R01625", "numCode": "702", "charCode": "SGD", "nominal": 1, "name": "Сингапурский доллар", "value": 16.8878, "vunitRate": 16.8878},
        {"id": "R01700", "numCode": "792", "charCode": "TRL", "nominal": 1000000, "name": "Турецких лир", "value": 22.2616, "vunitRate": 2.22616E-05},
        {"id": "R01720", "numCode": "980", "charCode": "UAH", "nominal": 10, "name": "Гривен", "value": 58.1090, "vunitRate": 5.8109},
        {"id": "R01770", "numCode": "752", "charCode": "SEK", "nominal": 10, "name": "Шведских крон", "value": 29.5924, "vunitRate": 2.95924},
        {"id": "R01775", "numCode": "756", "charCode": "CHF", "nominal": 1, "name": "Швейцарский франк", "value": 18.1861, "vunitRate": 18.1861},
        {"id": "R01820", "numCode": "392", "charCode": "JPY", "nominal": 100, "name": "Иен", "value": 23.1527, "vunitRate": 0.231527}
    ]

    xml_parts = []
    for currency in currencies:
        xml_parts.append(f'''
                            <Valute ID="{currency['id']}">
                                <NumCode>{currency['numCode']}</NumCode>
                                <CharCode>{currency['charCode']}</CharCode>
                                <Nominal>{currency['nominal']}</Nominal>
                                <Name>{currency['name']}</Name>
                                <Value>{currency['value']}</Value>
                                <VunitRate>{currency['vunitRate']}</VunitRate>
                            </Valute>''')

    return f'''<?xml version="1.0" encoding="windows-1251"?>
                <ValCurs Date="{date}" name="Foreign Currency Market">
                {"".join(xml_parts)}
                </ValCurs>'''

@app.before_request
def init_app():
    if not hasattr(g, 'initialized'):
        init_db()
        g.initialized = True

@app.route("/scripts/XML_daily.asp")
def get_rates():
    """
    Получение курсов валют от ЦБ РФ (имитация)

    ---
    tags:
      - Currency Rates
    parameters:
      - name: date_req
        in: query
        type: string
        required: false
        description: Дата в формате DD/MM/YYYY. Если не указана — используется текущая дата.
        example: "25/04/2025"
    responses:
      200:
        description: Успешный ответ с XML-курсами валют
        content:
          text/xml:
            schema:
              type: string
              example: |
                <?xml version="1.0" encoding="windows-1251"?>
                <ValCurs Date="25.04.2025" name="Foreign Currency Market">
                  <Valute ID="R01235">
                    <NumCode>840</NumCode>
                    <CharCode>USD</CharCode>
                    <Nominal>1</Nominal>
                    <Name>Доллар США</Name>
                    <Value>30.9436</Value>
                    <VunitRate>30.9436</VunitRate>
                  </Valute>
                </ValCurs>
      400:
        description: Неверный формат даты
        content:
          text/plain:
            schema:
              type: string
              example: "Invalid date format"
      500:
        description: Внутренняя ошибка сервера (20% вероятность)
        content:
          text/plain:
            schema:
              type: string
              example: "Internal Server Error"
    """
    
    date_req = request.args.get('date_req')
    response_id = generate_id()

    if date_req:
        try:
            date = datetime.strptime(date_req, "%d/%m/%Y").date()
        except ValueError:
            return Response("Invalid date format", status=400)
    else:
        date = datetime.now().date()

    if random.random() < 0.2:
        status_code = 500
        content = "Internal Server Error"
    else:
        status_code = 200
        content = generate_xml_response(date.strftime("%d.%m.%Y"))

    with get_db() as conn:
        conn.execute(
            "INSERT INTO responses VALUES (?, ?, ?, ?)",
            (response_id, date.strftime("%d.%m.%Y"), content, status_code)
        )
        conn.commit()

    if status_code == 500:
        return Response(content, status=500, mimetype='text/plain')
    return Response(content, mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)