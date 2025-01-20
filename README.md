Weather API
Сервер предоставляет REST API для работы с прогнозами погоды, городами и пользователями.

Запуск проекта
1) Убедитесь, что у вас установлен Python 3.9 или выше.
2) Создать виртуальное окружение:
```
python -m venv myenv
```
    `source myenv/bin/activate`  # Для Linux/Mac
    `myenv\Scripts\activate`     # Для Windows
    
4) Установите зависимости
```
pip install -r requirements.txt
```
3) Запустите сервер:
```
python script.py
```
4) Сервер будет доступен по адресу: http://127.0.0.1:8000.


**Метод 1**: Регистрация пользователя (/register_user)  
Тип запроса: POST  
Описание: Регистрирует нового пользователя.  
URL: http://127.0.0.1:8000/users/register_user  
Тело запроса (JSON):, к примеру: 
```json
{  
  "username": "testuser"  
}  
```
Ответ:
```json
{  
    "username": "testuser",  
    "id": 1,  
    "cities": null  
}
```
**Метод 2**: Получение текущей погоды по координатам (/weather)  
Метод: GET /weather/weather  
Тип запроса: GET  
Описание: Возвращает текущую погоду для указанных координат.  
Параметры:  
    - latitude (например, 55.7558 для Москвы)  
    - longitude (например, 37.6176 для Москвы)  

Полный запрос может выглядеть так `http://127.0.0.1:8000/weather/weather/?latitude=52.52&longitude=13.41`  
Ответ:
```json
{  
    "temperature": 2.2,  
    "wind_speed": 5.8,  
    "atmospheric_pressure": 1018.9  
}
```
**Метод 3**: Добавление города для отслеживания (/track_city)  
Метод: POST /track_city  
Описание: Добавляет город для отслеживания погоды и сохраняет текущие данные о погоде.  
Полный запрос может выглядеть так `http://127.0.0.1:8000/cities/track_city`   
Тело запроса (JSON):
```json
{  
  "user_id": 1,  
  "name": "Moscow",  
  "latitude": 52.52,  
  "longitude": 13.41  
}  
```

Ответ:  
```json
{
    "id": 1,   
    "name": "Moscow",  
    "latitude": 52.52,  
    "longitude": 13.41,  
    "forecast": {  
        "city_id": 1,  
        "timestamp": "2025-01-20T14:05:56.069950",  
        "temperature": 2.4,  
        "wind_speed": 5.8,  
        "atmospheric_pressure": 1018.4
    }  
}  
```
, где id - уникальный идентификат города в бд  

**Метод 4**: Получение списка городов пользователя (/list_user_cities)  
Метод: GET /cities/list_user_cities    
URL: http://127.0.0.1:8000/cities/list_user_cities?user_id=1   
Описание: Возвращает список городов, которые отслеживает пользователь.    
Параметры:  
В Query Params добавьте: user_id (например, 1)  
Ответ:
```json
{  
    "user_id": 1,  
    "cities": [  
        {  
            "id": 1,  
            "name": "Moscow",  
            "latitude": 52.52,  
            "longitude": 13.41,  
            "forecast": {  
                "city_id": 1,  
                "timestamp": "2025-01-19T12:54:53.714454",  
                "temperature": 3.2,  
                "wind_speed": 11.8,  
                "atmospheric_pressure": 1037.3  
            }  
        }  
    ]  
}  
```

Метод 5: Получение погоды на указанное время (/get_weather_at_time)  
В методе get_weather_at_time вводите время в таком формате 15:46, минуты будут откидываться и мы будем искать вхождение именно даты и часов, потому что open-meteo возвращает данные о погоде каждый час.  
GET /weather/get_weather_at_time  
URL: http://127.0.0.1:8000/weather/get_weather_at_time    
Описание: Возвращает прогноз погоды для города на текущий день в указанное время.  
Тело запроса (JSON):  
```json
{
  "user_id": 1,
  "city_name": "Moscow",
  "time": "12:00",
  "params": ["temperature", "humidity"]
}   
```
Ответ:
```json
{
    "temperature": 3.5,
    "humidity": 87
}
```

Дополнительные задания
1. Работа с несколькими пользователями
Метод: POST /register_user

Описание:   
Регистрирует нового пользователя и возвращает его ID. Для каждого пользователя создается свой список городов.   

Метод 6: Фоновая обработка прогоза погоды для всех городов в бд  
Метод update_weather_forecasts — это фоновая задача, которая автоматически обновляет прогнозы погоды для всех городов, добавленных в систему. Он работает в бесконечном цикле и выполняет обновление данных каждые 15 минут.


