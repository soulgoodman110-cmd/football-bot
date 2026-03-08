import os
import random
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, CallbackQueryHandler, ContextTypes
)

# Загружаем токен из файла .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv('BOT_TOKEN')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Состояния диалога для создания игрока
NAME, SURNAME, PATRONYMIC, BIRTHDATE, COUNTRY = range(5)

# Словарь для сопоставления названий лиг разных уровней
LEAGUE_MAPPING = {
    ("Россия", 1): ("РПЛ", 1),
    ("Россия", 2): ("ФНЛ", 2),
    ("Англия", 1): ("Premier League", 1),
    ("Англия", 2): ("Чемпионшип", 2),
    ("Испания", 1): ("La Liga", 1),
    ("Испания", 2): ("Сегунда", 2),
    ("Италия", 1): ("Серия А", 1),
    ("Италия", 2): ("Серия B", 2),
    ("Германия", 1): ("Бундеслига", 1),
    ("Германия", 2): ("2. Бундеслига", 2),
    ("Франция", 1): ("Лига 1", 1),
    ("Франция", 2): ("Лига 2", 2),
    ("Украина", 1): ("УПЛ", 1),
    ("Украина", 2): ("Первая лига", 2),
    ("Турция", 1): ("Суперлига", 1),
    ("Турция", 2): ("1. Лига", 2),
    ("Бразилия", 1): ("Бразилейран", 1),
    ("Бразилия", 2): ("Серия B", 2),
    ("Аргентина", 1): ("Примера", 1),
    ("Аргентина", 2): ("Примера B", 2),
    ("Япония", 1): ("J1 Лига", 1),
    ("Япония", 2): ("J2 Лига", 2),
    ("Япония", 3): ("J3 Лига", 3),
    ("Китай", 1): ("Суперлига", 1),
    ("Китай", 2): ("Первая лига", 2),
    ("Кипр", 1): ("Первая лига", 1),
    ("Кипр", 2): ("Вторая лига", 2),
    ("Португалия", 1): ("Примейра-лига", 1),
    ("Португалия", 2): ("Сегунда-лига", 2),
    ("Австрия", 1): ("Бундеслига", 1),
    ("Австрия", 2): ("Вторая лига", 2),
    ("Польша", 1): ("Экстракласа", 1),
    ("Польша", 2): ("Первая лига", 2),
    ("Сербия", 1): ("Суперлига", 1),
    ("Сербия", 2): ("Первая лига", 2),
    ("Хорватия", 1): ("ХНЛ", 1),
    ("Хорватия", 2): ("Первая лига", 2),
    ("США", 1): ("MLS", 1),
    ("США", 2): ("USL", 2),
    ("Канада", 1): ("MLS", 1),
    ("Канада", 2): ("USL", 2),
}

# --- Классы ---

class Tournament:
    def __init__(self, name, years, level, is_national=False):
        self.name = name
        self.years = set(years)
        self.level = level
        self.is_national = is_national

# Турниры (годы проведения)
TOURNAMENTS = [
    Tournament("Лига чемпионов", list(range(1960, 2027)), 1),
    Tournament("Лига Европы", list(range(1971, 2027)), 2),
    Tournament("Лига конференций", list(range(2021, 2027)), 3),
    Tournament("Чемпионат мира", list(range(1960, 2027, 4)), 0, is_national=True),
    Tournament("Чемпионат Европы", list(range(1960, 2027, 4)), 0, is_national=True),
    Tournament("Кубок Америки", list(range(1960, 2027, 4)), 0, is_national=True),
    Tournament("Кубок Африки", list(range(1960, 2027, 2)), 0, is_national=True),
    Tournament("Кубок Азии", list(range(1960, 2027, 4)), 0, is_national=True),
    Tournament("Финалиссима", list(range(2022, 2027, 4)), 0, is_national=True),
]

class Club:
    def __init__(self, name, league, country, ratings_by_year, league_tier=1):
        self.name = name
        self.league = league
        self.country = country
        self.ratings_by_year = ratings_by_year
        self.league_tier = league_tier
        self.league_position = None
        self.trophies = []

    def get_rating(self, year):
        years = sorted(self.ratings_by_year.keys())
        if not years:
            return 50
        if year in self.ratings_by_year:
            return self.ratings_by_year[year]
        if year < years[0]:
            return self.ratings_by_year[years[0]]
        if year > years[-1]:
            return self.ratings_by_year[years[-1]]
        for i in range(len(years)-1):
            if years[i] < year < years[i+1]:
                r1 = self.ratings_by_year[years[i]]
                r2 = self.ratings_by_year[years[i+1]]
                return int(r1 + (r2 - r1) * (year - years[i]) / (years[i+1] - years[i]))
        return 50

def generate_clubs():
    """Генерирует расширенный список клубов со всего мира (включая Африку)"""
    clubs = []
    
    # === РОССИЯ ===
    # РПЛ (1-й дивизион)
    rpl_clubs = [
        "Зенит", "Спартак", "ЦСКА", "Локомотив", "Динамо", "Краснодар", 
        "Ростов", "Сочи", "Ахмат", "Крылья Советов", "Оренбург", 
        "Пари Нижний Новгород", "Факел", "Рубин", "Балтика", "Торпедо"
    ]
    for name in rpl_clubs:
        ratings = {year: random.randint(60, 85) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "РПЛ", "Россия", ratings, league_tier=1))
    
    # ФНЛ (2-й дивизион)
    fnl_clubs = [
        "Химки", "Урал", "Черноморец", "Родина", "Арсенал Тула", "Алания",
        "Енисей", "Шинник", "КАМАЗ", "Нефтехимик", "Волгарь", "Сокол",
        "Тюмень", "Ленинградец", "Уфа"
    ]
    for name in fnl_clubs:
        ratings = {year: random.randint(45, 65) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "ФНЛ", "Россия", ratings, league_tier=2))
    
    # ФНЛ-2 (3-й дивизион)
    fnl2_clubs = [
        "Ростов-2", "Севастополь", "Динамо-2", "Рубин Ялта", "Нарт",
        "Победа", "Дружба", "Астрахань", "Ангушт", "Спартак-Нальчик",
        "Заря", "Кызылташ", "ПСК", "Чайка-М", "Нефтяник"
    ]
    for name in fnl2_clubs:
        ratings = {year: random.randint(30, 50) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "ФНЛ-2", "Россия", ratings, league_tier=3))
    
    # === АНГЛИЯ ===
    premier_league = [
        "Манчестер Сити", "Манчестер Юнайтед", "Ливерпуль", "Арсенал", "Челси",
        "Тоттенхэм", "Ньюкасл Юнайтед", "Астон Вилла", "Брайтон", "Вест Хэм",
        "Вулверхэмптон", "Фулхэм", "Кристал Пэлас", "Брентфорд", "Ноттингем Форест",
        "Эвертон", "Борнмут", "Лестер Сити", "Саутгемптон", "Лидс Юнайтед"
    ]
    for name in premier_league:
        ratings = {year: random.randint(70, 95) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Premier League", "Англия", ratings, league_tier=1))
    
    championship = [
        "Лидс Юнайтед", "Сандерленд", "Мидлсбро", "Бернли", "Шеффилд Юнайтед",
        "Ковентри Сити", "Уотфорд", "Вест Бромвич", "Халл Сити", "Норвич Сити",
        "Куинз Парк Рейнджерс", "Сток Сити", "Кардифф Сити", "Суонси Сити", "Бристоль Сити"
    ]
    for name in championship:
        ratings = {year: random.randint(55, 75) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Чемпионшип", "Англия", ratings, league_tier=2))
    
    # === ИСПАНИЯ ===
    la_liga = [
        "Реал Мадрид", "Барселона", "Атлетико Мадрид", "Реал Сосьедад",
        "Атлетик Бильбао", "Вильярреал", "Реал Бетис", "Севилья", "Валенсия",
        "Жирона", "Осасуна", "Сельта", "Лас-Пальмас", "Райо Вальекано", "Хетафе"
    ]
    for name in la_liga:
        ratings = {year: random.randint(70, 98) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "La Liga", "Испания", ratings, league_tier=1))
    
    segunda = [
        "Эспаньол", "Леванте", "Эльче", "Спортинг Хихон", "Реал Сарагоса",
        "Гранада", "Альмерия", "Кордова", "Эйбар", "Малага",
        "Тенерифе", "Альбасете", "Кадис", "Уэска", "Леганес"
    ]
    for name in segunda:
        ratings = {year: random.randint(50, 70) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Сегунда", "Испания", ratings, league_tier=2))
    
    # === ИТАЛИЯ ===
    serie_a = [
        "Наполи", "Интер", "Аталанта", "Ювентус", "Рома", "Фиорентина",
        "Лацио", "Милан", "Болонья", "Комо", "Торино", "Удинезе",
        "Дженоа", "Верона", "Кальяри", "Парма", "Лечче", "Сассуоло"
    ]
    for name in serie_a:
        ratings = {year: random.randint(70, 95) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Серия А", "Италия", ratings, league_tier=1))
    
    serie_b = [
        "Бари", "Венеция", "Эмполи", "Зюдтироль", "Катандзаро", "Модена",
        "Монца", "Палермо", "Реджана", "Сампдория", "Специя", "Фрозиноне",
        "Каррарезе", "Мантова", "Юве Стабия", "Чезена"
    ]
    for name in serie_b:
        ratings = {year: random.randint(45, 70) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Серия B", "Италия", ratings, league_tier=2))
    
    # === ГЕРМАНИЯ ===
    bundesliga = [
        "Бавария", "Боруссия Дортмунд", "Байер Леверкузен", "РБ Лейпциг",
        "Унион Берлин", "Айнтрахт Франкфурт", "Боруссия Мёнхенгладбах",
        "Вольфсбург", "Штутгарт", "Хоффенхайм", "Вердер", "Аугсбург",
        "Майнц 05", "Кёльн", "Герта"
    ]
    for name in bundesliga:
        ratings = {year: random.randint(70, 95) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Бундеслига", "Германия", ratings, league_tier=1))
    
    bundesliga_2 = [
        "Гамбургер", "Шальке 04", "Герта", "Фортуна Дюссельдорф", "Ганновер 96",
        "Нюрнберг", "Карлсруэ", "Санкт-Паули", "Гройтер Фюрт", "Падерборн 07",
        "Дармштадт 98", "Магдебург", "Айнтрахт Брауншвейг", "Киль", "Кайзерслаутерн"
    ]
    for name in bundesliga_2:
        ratings = {year: random.randint(45, 70) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "2. Бундеслига", "Германия", ratings, league_tier=2))
    
    # === ФРАНЦИЯ ===
    ligue_1 = [
        "Пари Сен-Жермен", "Олимпик Марсель", "Монако", "Ницца", "Лилль",
        "Страсбур", "Ланс", "Брест", "Тулуза", "Осер", "Реймс",
        "Лорьян", "Мец", "Париж"
    ]
    for name in ligue_1:
        ratings = {year: random.randint(65, 95) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Лига 1", "Франция", ratings, league_tier=1))
    
    ligue_2 = [
        "Олимпик Лион", "Монпелье", "Сент-Этьенн", "Гавр", "Генгам",
        "Кан", "Анже", "Нанси", "Шатору", "Ним", "Аяччо", "По"
    ]
    for name in ligue_2:
        ratings = {year: random.randint(40, 65) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Лига 2", "Франция", ratings, league_tier=2))
    
    # === УКРАИНА ===
    ukraine_premier = [
        "Шахтёр", "Динамо Киев", "Днепр-1", "Заря", "Ворскла",
        "Колос", "Александрия", "Металлист 1925", "Рух", "Львов",
        "Минай", "Ингулец", "Черноморец", "Кривбасс", "Верес"
    ]
    for name in ukraine_premier:
        ratings = {year: random.randint(50, 80) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "УПЛ", "Украина", ratings, league_tier=1))
    
    # === ТУРЦИЯ ===
    turkey_super = [
        "Галатасарай", "Фенербахче", "Бешикташ", "Трабзонспор", "Башакшехир",
        "Коньяспор", "Аланьяспор", "Сивасспор", "Кайсериспор", "Антальяспор",
        "Газиантеп", "Адана Демирспор", "Хатайспор", "Касымпаша", "Ризеспор"
    ]
    for name in turkey_super:
        ratings = {year: random.randint(55, 85) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Суперлига", "Турция", ratings, league_tier=1))
    
    turkey_2 = [
        "Гёзтепе", "Алтай", "Бурсаспор", "Самсунспор", "Эрзурумспор", "Маниса"
    ]
    for name in turkey_2:
        ratings = {year: random.randint(40, 60) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "1. Лига", "Турция", ratings, league_tier=2))
    
    # === БРАЗИЛИЯ ===
    brasileirao = [
        "Фламенго", "Палмейрас", "Сантос", "Коринтианс", "Сан-Паулу",
        "Гремио", "Интернасьонал", "Атлетико Минейро", "Крузейро", "Ботафого",
        "Васко да Гама", "Флуминенсе", "Коритиба", "Баия", "Спорт Ресифи"
    ]
    for name in brasileirao:
        ratings = {year: random.randint(65, 88) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Бразилейран", "Бразилия", ratings, league_tier=1))
    
    serie_b_brazil = [
        "Америка-МГ", "Атлетико-ГО", "Аваи", "Сеара", "Крисиума",
        "Куяба", "Форталеза", "Гояс", "Жувентуде", "Лондрина",
        "Наутико", "Операрио-ПР", "Понте Прета", "Спорт", "Вила-Нова"
    ]
    for name in serie_b_brazil:
        ratings = {year: random.randint(45, 65) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Серия B", "Бразилия", ratings, league_tier=2))
    
    # === АРГЕНТИНА ===
    argentina_premier = [
        "Бока Хуниорс", "Ривер Плейт", "Индепендьенте", "Расинг", "Сан-Лоренсо",
        "Велес Сарсфилд", "Эстудиантес", "Ньюэллс Олд Бойз", "Росарио Сентраль", "Колон"
    ]
    for name in argentina_premier:
        ratings = {year: random.randint(60, 85) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Примера", "Аргентина", ratings, league_tier=1))
    
    # === ЯПОНИЯ ===
    j1 = [
        "Касима Антлерс", "Урава Ред Даймондс", "Виссел Кобе", "Кавасаки Фронтале",
        "Иокогама Ф. Маринос", "Сересо Осака", "Гамба Осака", "Санфречче Хиросима",
        "Нагоя Грампус", "ФК Токио", "Ависпа Фукуока", "Консадоле Саппоро",
        "Саган Тосу", "Сёнан Бельмаре", "Киото Санга", "Альбирекс Ниигата",
        "Касива Рейсол", "Токио Верди"
    ]
    for name in j1:
        ratings = {year: random.randint(55, 80) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "J1 Лига", "Япония", ratings, league_tier=1))
    
    j2 = [
        "Джубило Ивата", "Симидзу С-Палс", "Монтедио Ямагата", "Вегалта Сэндай",
        "Блаублиц Акита", "Иваки", "Мито Холлихок", "Тотиги", "В-Варен Нагасаки",
        "Фаджиано Окаяма", "Ренофа Ямагути", "Эхимэ", "Ванфоре Кофу",
        "Оита Тринита", "Токусима Вортис", "Кагосима Юнайтед", "Фудзиэда МИФК"
    ]
    for name in j2:
        ratings = {year: random.randint(40, 60) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "J2 Лига", "Япония", ratings, league_tier=2))
    
    j3 = [
        "Нагано Парсейро", "Каталле Тояма", "Гираванц Китакюсю", "Фукусима Юнайтед",
        "Мацумото Ямага", "Имабари", "Осака", "Цвайген Канадзава",
        "Ванрауре Хатинохе", "Тэгэвахаро Миядзаки", "Азул Кларо Нумадзу",
        "СКАП Сендай", "Иокогама СИСи", "Грулла Мориока", "Каматамамару Кагава"
    ]
    for name in j3:
        ratings = {year: random.randint(30, 50) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "J3 Лига", "Япония", ratings, league_tier=3))
    
    # === КИТАЙ ===
    china_super = [
        "Шанхай Порт", "Бейцзин Гоань", "Шаньдун Тайшань", "Шанхай Шэньхуа",
        "Чэнду Жунчэн", "Ухань Три Таунс", "Циндао Хайню", "Чанчунь Ятай",
        "Хэнань", "Чжэцзян Гринтаун", "Мэйчжоу Хакка", "Тяньцзинь Цзиньмэнь Тайгер",
        "Циндао Вест Кост", "Шэньчжэнь Пэн Сити", "Далянь Инбо", "Юньнань Юкун"
    ]
    for name in china_super:
        ratings = {year: random.randint(50, 75) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Суперлига", "Китай", ratings, league_tier=1))
    
    china_first = [
        "Гуанчжоу Эвергранд", "Шицзячжуан Юнчан", "Чунцин Лифань", "Наньтун Чжиюнь",
        "Ляонин Шэньян", "Цзянси Бэйда", "Хэйлунцзян", "Сучжоу Дунъу",
        "Нанкин Сити", "Шанхай Цзядин"
    ]
    for name in china_first:
        ratings = {year: random.randint(35, 55) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Первая лига", "Китай", ratings, league_tier=2))
    
    # === КИПР ===
    cyprus_first = [
        "АПОЭЛЬ Никосия", "Омония Никосия", "Арис Лимасол", "Анортосис",
        "Аполлон Лимасол", "АЕК Ларнака", "Пафос", "АЕЛ Лимасол",
        "Неа Саламина", "Этникос Ахнас", "Кармиотисса", "Омония 29-го Мая",
        "Докса Катокопия", "Эносис Паралимни"
    ]
    for name in cyprus_first:
        ratings = {year: random.randint(45, 65) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Первая лига", "Кипр", ratings, league_tier=1))
    
    cyprus_second = [
        "АСИЛ Лыси", "Айя-Напа", "Закакиу", "Ираклис Геролаккоу", "МЭАП Нису",
        "Кармиотисса", "Неа Саламина", "Омония 29-го Мая", "ПАЕЕК",
        "Докса Катокопия", "Дигенис Акритас", "Спартакос Китиу", "Апеа Акротириу"
    ]
    for name in cyprus_second:
        ratings = {year: random.randint(30, 50) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Вторая лига", "Кипр", ratings, league_tier=2))
    
    # === ПОРТУГАЛИЯ ===
    portugal_first = [
        "Порту", "Спортинг Лиссабон", "Бенфика", "Брага", "Жил Висенте",
        "Фамаликан", "Витория Гимарайнш", "Морейренсе", "Эшторил-Прая", "Риу Аве",
        "Алверка", "Насьонал", "Санта-Клара", "Эштрела Амадора", "Каза Пия",
        "Арока", "Тондела", "АВС Футебол"
    ]
    for name in portugal_first:
        ratings = {year: random.randint(50, 88) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Примейра-лига", "Португалия", ratings, league_tier=1))
    
    # === АВСТРИЯ ===
    austria_first = [
        "Ред Булл Зальцбург", "Рапид Вена", "Штурм Грац", "ЛАСК Линц",
        "Аустрия Вена", "Вольфсберг", "Хартберг", "Райндорф Альтах",
        "Аустрия Клагенфурт", "Блау-Вайсс Линц", "Тироль", "ГАК Грац"
    ]
    for name in austria_first:
        ratings = {year: random.randint(45, 85) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Бундеслига", "Австрия", ratings, league_tier=1))
    
    austria_second = [
        "Амштеттен", "Адмира Ваккер", "Аустрия Лустенау", "ФАК", "Санкт-Пёльтен",
        "Виенна", "Шварц-Вайс Брегенц", "Капфенберг", "Лиферинг", "Фёрст Виенна",
        "Лафниц", "Штрипфинг", "Хорн", "Оберварт"
    ]
    for name in austria_second:
        ratings = {year: random.randint(30, 50) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Вторая лига", "Австрия", ratings, league_tier=2))
    
    # === ПОЛЬША ===
    poland_first = [
        "Легия Варшава", "Лех Познань", "Ракув Ченстохова", "Погонь Щецин",
        "Висла Краков", "Шлёнск Вроцлав", "Гурник Забже", "Ягеллония Белосток",
        "Варта Познань", "Заглембе Любин", "Висла Плоцк"
    ]
    for name in poland_first:
        ratings = {year: random.randint(40, 75) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Экстракласа", "Польша", ratings, league_tier=1))
    
    # === СЕРБИЯ ===
    serbia_first = [
        "Црвена Звезда", "Партизан", "ТСЦ Бачка-Топола", "Чукарички",
        "Войводина", "Раднички Ниш", "Напредак", "Спартак Суботица",
        "Младост Лучани", "Нови Пазар"
    ]
    for name in serbia_first:
        ratings = {year: random.randint(45, 80) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Суперлига", "Сербия", ratings, league_tier=1))
    
    serbia_second = [
        "Мачва Шабац", "Ушче", "Текстилац О", "Инджия", "Смедерево",
        "Графичар", "ОФК Вршац", "Раднички СМ", "Слобода У", "Златибор",
        "Металац", "Траял", "Дубочица", "Земун", "Рад", "Колубара"
    ]
    for name in serbia_second:
        ratings = {year: random.randint(25, 45) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Первая лига", "Сербия", ratings, league_tier=2))
    
    # === ХОРВАТИЯ ===
    croatia_first = [
        "Хайдук Сплит", "Динамо Загреб", "Вараждин", "Истра 1961",
        "Славен Белупо", "Локомотива Загреб", "Горица", "Риека",
        "Вуковар 1991", "Осиек"
    ]
    for name in croatia_first:
        ratings = {year: random.randint(45, 80) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "ХНЛ", "Хорватия", ratings, league_tier=1))
    
    # === США/КАНАДА (MLS) ===
    mls_western = [
        "Лос-Анджелес Гэлакси", "ЛАФК", "Сан-Хосе Эртквейкс", "Портленд Тимберс",
        "Сиэтл Саундерс", "Ванкувер Уайткэпс", "Реал Солт-Лейк", "Колорадо Рэпидз",
        "Спортинг Канзас-Сити", "Миннесота Юнайтед", "Остин", "Хьюстон Динамо",
        "Даллас", "Сент-Луис Сити", "Сан-Диего"
    ]
    for name in mls_western:
        ratings = {year: random.randint(55, 80) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "MLS (Запад)", "США", ratings, league_tier=1))
    
    mls_eastern = [
        "Интер Майами", "Нью-Йорк Ред Буллз", "Нью-Йорк Сити", "Нью-Инглэнд Революшн",
        "Филадельфия Юнион", "Ди Си Юнайтед", "Торонто", "Монреаль",
        "Коламбус Крю", "Цинциннати", "Чикаго Файр", "Атланта Юнайтед",
        "Орландо Сити", "Шарлотт", "Нэшвилл"
    ]
    for name in mls_eastern:
        ratings = {year: random.randint(55, 80) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "MLS (Восток)", "США", ratings, league_tier=1))
    
    usl = [
        "Майами", "Сан-Антонио", "Финикс Райзинг", "Хартфорд", "Бирмингем Легион",
        "Колорадо-Спрингс", "Эль-Пасо", "Род-Айленд", "Сакраменто", "Лас-Вегас",
        "Лаудон Юнайтед", "Тампа-Бэй", "Лексингтон", "Детройт Сити"
    ]
    for name in usl:
        ratings = {year: random.randint(35, 60) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "USL", "США", ratings, league_tier=2))
    
    # === АФРИКА (расширенный список) ===
    africa_clubs = [
        # Египет
        ("Аль-Ахли", "Египет"), ("Замалек", "Египет"), ("Пирамидз", "Египет"), ("Смуха", "Египет"),
        # Тунис
        ("Эсперанс", "Тунис"), ("Клуб Африкэн", "Тунис"), ("Сфаксьен", "Тунис"), ("Этуаль дю Сахель", "Тунис"),
        # Марокко
        ("Раджа Касабланка", "Марокко"), ("Видад Касабланка", "Марокко"), ("ФАР Рабат", "Марокко"), ("Беркан", "Марокко"),
        # Алжир
        ("УСМ Алжир", "Алжир"), ("ЕС Сетиф", "Алжир"), ("Кабилия", "Алжир"), ("Белуиздад", "Алжир"),
        # ЮАР
        ("Кайзер Чифс", "ЮАР"), ("Орландо Пайретс", "ЮАР"), ("Мамелоди Сандаунз", "ЮАР"), ("Суперспорт Юнайтед", "ЮАР"),
        # Нигерия
        ("Еньимба", "Нигерия"), ("Кано Пилларс", "Нигерия"), ("Рейнджерс", "Нигерия"), ("Лоби Старз", "Нигерия"),
        # ДР Конго
        ("ТП Мазембе", "ДР Конго"), ("Вита", "ДР Конго"), ("Дон Боско", "ДР Конго"),
        # Камерун
        ("Котон Спорт", "Камерун"), ("Юнион Дуала", "Камерун"), ("Канон Яунде", "Камерун"),
        # Кот-д'Ивуар
        ("АСЕК Мимозас", "Кот-д'Ивуар"), ("Африка Спорт", "Кот-д'Ивуар"), ("Стад Абиджан", "Кот-д'Ивуар"),
        # Гана
        ("Асанте Котоко", "Гана"), ("Хартс оф Оук", "Гана"), ("Адуана Старз", "Гана"),
        # Ангола
        ("Петру Атлетику", "Ангола"), ("Примейру де Агошту", "Ангола"), ("Рекреативу ду Либоло", "Ангола"),
        # Замбия
        ("ЗАНАКО", "Замбия"), ("Пауэр Дайнамоз", "Замбия"), ("Нкана", "Замбия"),
        # Мали
        ("Стад Мальен", "Мали"), ("Джолиба", "Мали"), ("Реал Бамако", "Мали"),
    ]
    for name, country in africa_clubs:
        ratings = {year: random.randint(40, 70) for year in range(1960, 2027, 5)}
        clubs.append(Club(name, "Африканская лига", country, ratings, league_tier=1))
    
    return clubs

ALL_CLUBS = generate_clubs()

# Группируем клубы по лигам и странам для определения позиций
def group_clubs_by_league():
    leagues = {}
    for club in ALL_CLUBS:
        key = (club.league, club.country, club.league_tier)
        if key not in leagues:
            leagues[key] = []
        leagues[key].append(club)
    return leagues

LEAGUES = group_clubs_by_league()

def update_league_positions():
    for (league, country, tier), clubs in LEAGUES.items():
        sorted_clubs = sorted(clubs, key=lambda c: c.get_rating(2025), reverse=True)
        for pos, club in enumerate(sorted_clubs, 1):
            club.league_position = pos

update_league_positions()

class NationalTeam:
    def __init__(self, country):
        self.country = country
        self.name = f"{country} (сборная)"

class Player:
    def __init__(self, name, surname, patronymic, birth_date, country):
        self.name = name
        self.surname = surname
        self.patronymic = patronymic
        self.birth_date = birth_date
        self.country = country
        self.age = 15
        self.start_year = birth_date.year + 15
        self.current_year = self.start_year
        self.club = None
        self.club_number = None
        self.national_team = None
        self.national_number = None
        self.is_captain_club = False
        self.is_captain_national = False
        self.stats = self._generate_initial_stats(target_rating=50)
        self.overall = self._calc_overall()
        self.max_overall = self.overall
        self.career_history = []
        self.transfer_history = []
        self.tournament_wins = []
        self.club_trophies = []
        self.personal_awards = []
        self.total_goals = 0
        self.total_assists = 0

    def _generate_initial_stats(self, target_rating=50):
        target_sum = target_rating * 6
        stats = {attr: random.randint(1, 50) for attr in ['pace','shooting','passing','dribbling','defending','physical']}
        current_sum = sum(stats.values())
        factor = target_sum / current_sum
        for attr in stats:
            stats[attr] = max(1, min(99, int(stats[attr] * factor)))
        diff = target_sum - sum(stats.values())
        for _ in range(abs(diff)):
            attr = random.choice(list(stats.keys()))
            if diff > 0 and stats[attr] < 99:
                stats[attr] += 1
            elif diff < 0 and stats[attr] > 1:
                stats[attr] -= 1
        return stats

    def _calc_overall(self):
        return sum(self.stats.values()) // 6

    def update_stats_for_age(self):
        changes = {}
        if self.age <= 23:
            for attr in self.stats:
                inc = random.randint(2, 5)
                self.stats[attr] = min(99, self.stats[attr] + inc)
                changes[attr] = inc
        elif self.age <= 28:
            for attr in self.stats:
                inc = random.randint(0, 3)
                self.stats[attr] = min(99, self.stats[attr] + inc)
                changes[attr] = inc
        else:
            for attr in self.stats:
                dec = random.randint(0, 3)
                self.stats[attr] = max(1, self.stats[attr] - dec)
                changes[attr] = -dec
        self.overall = self._calc_overall()
        if self.overall > self.max_overall:
            self.max_overall = self.overall
        return changes

    def assign_club(self, club, year):
        self.club = club
        self.club_number = None

    def assign_national_team(self, team):
        self.national_team = team
        self.national_number = None
        self.personal_awards.append(f"Вызов в сборную {self.country} ({self.current_year})")

    def get_full_name(self):
        return f"{self.surname} {self.name} {self.patronymic}"

# --- Функции симуляции ---

def get_clubs_by_year(year, min_rating=0, max_rating=100, exclude_club=None, country=None, league_tier=None):
    candidates = []
    for club in ALL_CLUBS:
        rating = club.get_rating(year)
        if min_rating <= rating <= max_rating:
            if exclude_club and club == exclude_club:
                continue
            if country and club.country != country:
                continue
            if league_tier and club.league_tier != league_tier:
                continue
            candidates.append(club)
    return candidates

def simulate_club_performance(club, year):
    trophies = []
    base_rating = club.get_rating(year)
    
    if random.random() < 0.05 * (base_rating / 50):
        trophies.append(f"🏆 Лига чемпионов {year}")
        club.trophies.append(f"Лига чемпионов {year}")
    
    if random.random() < 0.15 * (base_rating / 50):
        trophies.append(f"🏆 Кубок страны {year}")
        club.trophies.append(f"Кубок страны {year}")
    
    return trophies

def check_promotion_relegation(club):
    messages = []
    country = club.country
    if club.league_tier not in (1, 2):
        return messages

    same_league_clubs = [c for c in ALL_CLUBS if c.league == club.league and c.country == country]
    league_size = len(same_league_clubs)

    if club.league_tier == 1 and club.league_position == league_size:
        second_league_clubs = [c for c in ALL_CLUBS if c.league_tier == 2 and c.country == country]
        if second_league_clubs:
            second_league_clubs.sort(key=lambda c: c.league_position or 999)
            best_second = second_league_clubs[0]
            if best_second.league_position == 1:
                old_tier1 = club.league_tier
                old_tier2 = best_second.league_tier
                club.league_tier, best_second.league_tier = old_tier2, old_tier1
                if (country, old_tier1) in LEAGUE_MAPPING:
                    club.league = LEAGUE_MAPPING[(country, old_tier1)][0]
                if (country, old_tier2) in LEAGUE_MAPPING:
                    best_second.league = LEAGUE_MAPPING[(country, old_tier2)][0]
                messages.append(f"📉 {club.name} вылетел во вторую лигу!")
                messages.append(f"✨ {best_second.name} вышел в высшую лигу!")

    elif club.league_tier == 2 and club.league_position == 1:
        first_league_clubs = [c for c in ALL_CLUBS if c.league_tier == 1 and c.country == country]
        if first_league_clubs:
            first_league_clubs.sort(key=lambda c: c.league_position or 0, reverse=True)
            worst_first = first_league_clubs[0]
            if worst_first.league_position == len(first_league_clubs):
                old_tier1 = club.league_tier
                old_tier2 = worst_first.league_tier
                club.league_tier, worst_first.league_tier = old_tier2, old_tier1
                if (country, old_tier1) in LEAGUE_MAPPING:
                    club.league = LEAGUE_MAPPING[(country, old_tier1)][0]
                if (country, old_tier2) in LEAGUE_MAPPING:
                    worst_first.league = LEAGUE_MAPPING[(country, old_tier2)][0]
                messages.append(f"✨ {club.name} вышел в высшую лигу!")
                messages.append(f"📉 {worst_first.name} вылетел во вторую лигу!")

    return messages

def simulate_season_stats(player):
    base = player.overall // 5
    goals = random.randint(0, base + random.randint(0, 5))
    assists = random.randint(0, base + random.randint(0, 5))
    if player.overall > 80:
        goals += random.randint(5, 15)
        assists += random.randint(5, 15)
    elif player.overall > 70:
        goals += random.randint(3, 10)
        assists += random.randint(3, 10)
    elif player.overall > 60:
        goals += random.randint(1, 5)
        assists += random.randint(1, 5)
    return max(0, goals), max(0, assists)

def simulate_tournaments(player, year):
    achievements = []
    if not player.club:
        return achievements
    for tournament in TOURNAMENTS:
        if year in tournament.years and not tournament.is_national:
            club_rating = player.club.get_rating(year)
            if tournament.level == 1:
                prob = max(0, min(1, (club_rating - 70) / 30))
            elif tournament.level == 2:
                prob = max(0, min(1, (club_rating - 60) / 35))
            elif tournament.level == 3:
                prob = max(0, min(1, (club_rating - 50) / 40))
            else:
                continue
            if random.random() < prob:
                result = simulate_tournament_result(tournament, club_rating)
                if result:
                    achievement = f"{tournament.name} {year}: {result}"
                    achievements.append(achievement)
                    if result == "победитель":
                        player.club_trophies.append(achievement)
    if player.national_team:
        for tournament in TOURNAMENTS:
            if year in tournament.years and tournament.is_national:
                prob = max(0, min(1, (player.overall - 70) / 25))
                if random.random() < prob:
                    result = simulate_tournament_result(tournament, player.overall)
                    if result:
                        achievements.append(f"{tournament.name} {year}: {result}")
    return achievements

def simulate_tournament_result(tournament, team_rating):
    rand = random.random()
    if team_rating > 90:
        if rand < 0.3:
            return "победитель"
        elif rand < 0.6:
            return "финалист"
        elif rand < 0.8:
            return "полуфинал"
        else:
            return "участие"
    elif team_rating > 80:
        if rand < 0.1:
            return "победитель"
        elif rand < 0.3:
            return "финалист"
        elif rand < 0.6:
            return "полуфинал"
        else:
            return "участие"
    elif team_rating > 70:
        if rand < 0.05:
            return "победитель"
        elif rand < 0.15:
            return "финалист"
        elif rand < 0.4:
            return "полуфинал"
        else:
            return "участие"
    else:
        if rand < 0.02:
            return "победитель"
        elif rand < 0.08:
            return "финалист"
        elif rand < 0.2:
            return "полуфинал"
        else:
            return "участие"

def generate_transfer_offers(player, year_for_club_search):
    if random.random() > 0.5:
        return []
    if player.overall < 80:
        max_rating = 84
        min_rating = 70
    else:
        max_rating = 100
        min_rating = 70
    candidates = get_clubs_by_year(year_for_club_search, min_rating=min_rating, max_rating=max_rating, exclude_club=player.club)
    if not candidates:
        return []
    num_offers = min(3, len(candidates))
    selected = random.sample(candidates, num_offers)
    offers = []
    for club in selected:
        transfer_type = random.choice(['аренда', 'полноценный'])
        offers.append((club, transfer_type))
    return offers

def generate_national_call(player, year_for_check):
    if player.overall >= 80 and player.national_team is None:
        return NationalTeam(player.country)
    return None

def check_captaincy(player):
    messages = []
    if player.overall >= 85:
        if not player.is_captain_club and player.club:
            player.is_captain_club = True
            msg = f"Капитан клуба {player.club.name}"
            player.personal_awards.append(msg)
            messages.append(f"🏆 Вы стали капитаном в клубе {player.club.name}!")
        if not player.is_captain_national and player.national_team:
            player.is_captain_national = True
            msg = f"Капитан сборной {player.country}"
            player.personal_awards.append(msg)
            messages.append(f"🏆 Вы стали капитаном сборной {player.country}!")
    return messages

def simulate_year(player):
    stat_changes = player.update_stats_for_age()
    goals, assists = simulate_season_stats(player)
    player.total_goals += goals
    player.total_assists += assists
    
    club_trophies = simulate_club_performance(player.club, player.current_year)
    for trophy in club_trophies:
        player.club_trophies.append(trophy)
    
    promotion_messages = check_promotion_relegation(player.club)
    achievements = simulate_tournaments(player, player.current_year)
    player.age += 1
    player.current_year += 1
    offers = generate_transfer_offers(player, player.current_year)
    national_call = generate_national_call(player, player.current_year)
    captain_messages = check_captaincy(player)
    
    # После всех изменений обновляем позиции клубов в лигах
    update_league_positions()
    
    return achievements, offers, national_call, captain_messages, stat_changes, goals, assists, club_trophies, promotion_messages

# --- Обработчики Telegram ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Добро пожаловать в симулятор футбольной карьеры!\n"
        "Давайте создадим вашего игрока.\n"
        "Введите имя:"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введите фамилию:")
    return SURNAME

async def get_surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['surname'] = update.message.text
    await update.message.reply_text("Введите отчество:")
    return PATRONYMIC

async def get_patronymic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['patronymic'] = update.message.text
    await update.message.reply_text("Введите дату рождения (в формате ДД.ММ.ГГГГ):")
    return BIRTHDATE

async def get_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    try:
        birth_date = datetime.strptime(text, "%d.%m.%Y").date()
        if birth_date.year < 1945 or birth_date.year > 2011:
            await update.message.reply_text("Год рождения должен быть между 1945 и 2011. Попробуйте ещё раз:")
            return BIRTHDATE
        context.user_data['birth_date'] = birth_date
        await update.message.reply_text("Введите страну (например, Россия, Испания, Бразилия):")
        return COUNTRY
    except ValueError:
        await update.message.reply_text("Неверный формат. Используйте ДД.ММ.ГГГГ:")
        return BIRTHDATE

async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()
    context.user_data['country'] = country
    player = Player(
        context.user_data['name'],
        context.user_data['surname'],
        context.user_data['patronymic'],
        context.user_data['birth_date'],
        country
    )
    start_year = player.start_year
    clubs = get_clubs_by_year(start_year, min_rating=40, max_rating=55, country=country, league_tier=2)
    if not clubs:
        clubs = get_clubs_by_year(start_year, min_rating=40, max_rating=55)
    if clubs:
        club = random.choice(clubs)
    else:
        club = random.choice(ALL_CLUBS)
    player.assign_club(club, start_year)
    player.club_number = None
    context.user_data['player'] = player
    context.user_data['awaiting_number_for'] = 'club'
    await update.message.reply_text(
        f"Вы начинаете карьеру в {player.club.name}\n"
        f"Страна: {player.club.country}\n"
        f"Лига: {player.club.league}\n"
        f"Год: {start_year}\n"
        f"Ваш начальный рейтинг: {player.overall}\n"
        "Теперь введите игровой номер в клубе (от 1 до 99):"
    )
    return ConversationHandler.END

async def handle_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'awaiting_number_for' not in context.user_data:
        return
    player = context.user_data.get('player')
    if not player:
        return
    try:
        number = int(update.message.text)
        if 1 <= number <= 99:
            target = context.user_data['awaiting_number_for']
            if target == 'club':
                player.club_number = number
                await update.message.reply_text(f"Номер {number} в клубе закреплён за вами!")
                if 'new_club' in context.user_data:
                    new_club = context.user_data.pop('new_club')
                    old_club = player.club
                    player.assign_club(new_club, player.current_year)
                    player.club_number = number
                    transfer_type = context.user_data.pop('transfer_type', 'трансфер')
                    record = f"{player.current_year}: Переход из {old_club.name} ({old_club.country}, {old_club.league}) в {new_club.name} ({new_club.country}, {new_club.league}) ({transfer_type})"
                    player.transfer_history.append(record)
                    await update.message.reply_text(f"Трансфер завершён. Теперь вы играете за {new_club.name} ({new_club.country}, {new_club.league}).")
            elif target == 'national':
                player.national_number = number
                await update.message.reply_text(f"Номер {number} в сборной закреплён за вами!")
            del context.user_data['awaiting_number_for']
            if context.user_data.get('pending_events'):
                await send_next_event(update, context)
            else:
                await show_main_menu(update, context)
        else:
            await update.message.reply_text("Номер должен быть от 1 до 99. Попробуйте ещё раз:")
    except ValueError:
        await update.message.reply_text("Введите целое число от 1 до 99:")

async def send_next_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = context.user_data.get('pending_events', [])
    if not pending:
        await show_main_menu(update, context)
        return
    event = pending.pop(0)
    context.user_data['pending_events'] = pending
    player = context.user_data['player']

    if event[0] == 'transfer_offers':
        offers = event[1]
        context.user_data['current_offers'] = offers
        keyboard = []
        for i, (club, ttype) in enumerate(offers):
            btn_text = f"✅ {club.name} ({club.country}, {club.league})"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f'transfer_{i}')])
        keyboard.append([InlineKeyboardButton("🚫 Остаться в команде", callback_data='reject_all_offers')])
        keyboard.append([InlineKeyboardButton("⏹ Завершить карьеру", callback_data='end_career_from_transfer')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = context.user_data.get('year_summary', '') + "\n\n"
        text += "📨 Вам поступили предложения:\n"
        for club, ttype in offers:
            text += f"• {club.name} ({club.country}, {club.league}) - рейтинг {club.get_rating(player.current_year)} ({ttype})\n"
        text += "\nВыберите действие:"
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
    elif event[0] == 'national':
        team = event[1]
        player.assign_national_team(team)
        context.user_data['national_call'] = team
        keyboard = [[InlineKeyboardButton("✅ Выбрать номер", callback_data='choose_national_number')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = context.user_data.get('year_summary', '') + "\n\n"
        text += f"🇨🇺 Вы вызваны в сборную {player.country}! Теперь выберите номер."
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = context.user_data['player']
    text = (f"✅ {player.get_full_name()}\n"
            f"🇨🇺 {player.country}, {player.age} лет\n"
            f"📅 Сезон: {player.current_year}\n"
            f"⚽ Клуб: {player.club.name}\n"
            f"🏟 Страна: {player.club.country}\n"
            f"🏆 Лига: {player.club.league} ({player.club.league_tier}-й дивизион)\n"
            f"📊 Позиция в лиге: {player.club.league_position or 'н/д'}\n"
            f"🔢 Номер: {player.club_number if player.club_number else '?'}\n"
            f"⭐ Рейтинг: {player.overall}\n"
            f"⚽ Голы: {player.total_goals}\n"
            f"🎯 Ассисты: {player.total_assists}\n"
            f"➕ Г+А: {player.total_goals + player.total_assists}\n")
    if player.national_team:
        text += f"🇨🇺 Сборная: {player.national_team.name} (№{player.national_number if player.national_number else '?'})\n"
    keyboard = [
        [InlineKeyboardButton("▶ Следующий год", callback_data='next_year')],
        [InlineKeyboardButton("ℹ Информация", callback_data='info')],
        [InlineKeyboardButton("📜 История", callback_data='history')],
        [InlineKeyboardButton("🏆 Трофеи клуба", callback_data='club_trophies')],
        [InlineKeyboardButton("⏹ Завершить карьеру", callback_data='end')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def next_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player = context.user_data['player']

    achievements, offers, national_call, captain_messages, stat_changes, goals, assists, club_trophies, promotion_messages = simulate_year(player)

    year_text = f"📅 {player.current_year-1} год завершён.\n"
    year_text += f"Возраст: {player.age-1} -> {player.age}\n"
    year_text += f"⭐ Рейтинг: {player.overall}\n\n"
    
    year_text += "📊 Изменение атрибутов:\n"
    for attr, change in stat_changes.items():
        if change > 0:
            year_text += f"  {attr}: +{change}\n"
        elif change < 0:
            year_text += f"  {attr}: {change}\n"
    year_text += "\n"
    
    year_text += f"⚽ Голы в сезоне: {goals}\n"
    year_text += f"🎯 Ассисты: {assists}\n"
    year_text += f"➕ Г+А в сезоне: {goals + assists}\n\n"
    
    year_text += f"📊 Позиция клуба в лиге: {player.club.league_position}\n"
    
    if club_trophies:
        year_text += "🏆 Трофеи клуба в этом сезоне:\n" + "\n".join(club_trophies) + "\n\n"
    
    if promotion_messages:
        year_text += "🔄 Изменения в лигах:\n" + "\n".join(promotion_messages) + "\n\n"
    
    if achievements:
        year_text += "🏅 Личные достижения:\n" + "\n".join(achievements) + "\n\n"
    
    if captain_messages:
        year_text += "\n".join(captain_messages) + "\n\n"
    
    player.career_history.append(year_text.strip())

    context.user_data['year_summary'] = year_text
    pending = []
    if offers:
        pending.append(('transfer_offers', offers))
    if national_call:
        pending.append(('national', national_call))
    context.user_data['pending_events'] = pending

    if pending:
        await send_next_event(update, context)
    else:
        await query.edit_message_text(year_text)
        await show_main_menu(update, context)

async def handle_transfer_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith('transfer_'):
        idx = int(data.split('_')[1])
        offers = context.user_data.get('current_offers', [])
        if idx < len(offers):
            target_club, transfer_type = offers[idx]
            context.user_data['new_club'] = target_club
            context.user_data['transfer_type'] = transfer_type
            context.user_data['awaiting_number_for'] = 'club'
            context.user_data.pop('current_offers', None)
            await query.edit_message_text(
                f"Вы приняли предложение от {target_club.name} ({target_club.country}, {target_club.league}).\n"
                f"Теперь введите номер в новом клубе (от 1 до 99):"
            )
    elif data == 'reject_all_offers':
        context.user_data.pop('current_offers', None)
        await query.edit_message_text(context.user_data.get('year_summary', '') + "\n\nВы остались в текущем клубе.")
        if context.user_data.get('pending_events'):
            await send_next_event(update, context)
        else:
            await show_main_menu(update, context)

async def end_career_from_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player = context.user_data['player']
    final_text = f"🏁 Карьера завершена.\n\n"
    final_text += f"Игрок: {player.get_full_name()}\n"
    final_text += f"Страна: {player.country}\n"
    final_text += f"Всего сезонов: {len(player.career_history)}\n"
    final_text += f"Максимальный рейтинг: {player.max_overall}\n"
    final_text += f"Всего голов: {player.total_goals}\n"
    final_text += f"Всего ассистов: {player.total_assists}\n"
    final_text += f"Всего Г+А: {player.total_goals + player.total_assists}\n"
    if player.tournament_wins:
        final_text += "\n🏆 Личные трофеи:\n" + "\n".join(player.tournament_wins)
    if player.club_trophies:
        final_text += "\n\n🏆 Трофеи клуба:\n" + "\n".join(set(player.club_trophies))
    if player.personal_awards:
        final_text += "\n\n📋 Личные награды:\n" + "\n".join(player.personal_awards)
    if player.transfer_history:
        final_text += "\n\n🔄 Трансферы:\n" + "\n".join(player.transfer_history)
    await query.edit_message_text(final_text)
    context.user_data.clear()
    await query.message.reply_text("Для новой игры введите /start")

async def choose_national_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['awaiting_number_for'] = 'national'
    await query.edit_message_text("Введите номер в сборной (от 1 до 99):")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player = context.user_data['player']
    text = f"📋 Информация об игроке:\n\n"
    text += f"Имя: {player.get_full_name()}\n"
    text += f"Страна: {player.country}\n"
    text += f"Дата рождения: {player.birth_date.strftime('%d.%m.%Y')}\n"
    text += f"Возраст: {player.age} лет\n"
    text += f"Текущий сезон: {player.current_year}\n"
    text += f"Клуб: {player.club.name}\n"
    text += f"Лига: {player.club.league}\n"
    text += f"Страна клуба: {player.club.country}\n"
    text += f"Номер: {player.club_number if player.club_number else 'не выбран'}\n"
    if player.national_team:
        text += f"Сборная: {player.national_team.name} (№{player.national_number if player.national_number else 'не выбран'})\n"
    text += f"Капитан клуба: {'да' if player.is_captain_club else 'нет'}\n"
    text += f"Капитан сборной: {'да' if player.is_captain_national else 'нет'}\n"
    text += f"Общий рейтинг: {player.overall}\n"
    text += f"Максимальный рейтинг: {player.max_overall}\n"
    text += f"Всего голов: {player.total_goals}\n"
    text += f"Всего ассистов: {player.total_assists}\n"
    text += f"Всего Г+А: {player.total_goals + player.total_assists}\n\n"
    text += "Статистика атрибутов:\n"
    for attr, val in player.stats.items():
        text += f"  {attr}: {val}\n"
    await query.edit_message_text(text)
    await show_main_menu(update, context)

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player = context.user_data['player']
    if not player.career_history:
        text = "История пока пуста."
    else:
        text = "📜 История карьеры (последние 10 лет):\n\n" + "\n".join(player.career_history[-10:])
    await query.edit_message_text(text)
    await show_main_menu(update, context)

async def club_trophies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player = context.user_data['player']
    if not player.club_trophies:
        text = "Пока нет выигранных трофеев с клубом."
    else:
        text = "🏆 Трофеи клуба:\n" + "\n".join(set(player.club_trophies))
    await query.edit_message_text(text)
    await show_main_menu(update, context)

async def end_career(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    player = context.user_data['player']
    final_text = f"🏁 Карьера завершена.\n\n"
    final_text += f"Игрок: {player.get_full_name()}\n"
    final_text += f"Страна: {player.country}\n"
    final_text += f"Всего сезонов: {len(player.career_history)}\n"
    final_text += f"Максимальный рейтинг: {player.max_overall}\n"
    final_text += f"Всего голов: {player.total_goals}\n"
    final_text += f"Всего ассистов: {player.total_assists}\n"
    final_text += f"Всего Г+А: {player.total_goals + player.total_assists}\n"
    if player.tournament_wins:
        final_text += "\n🏆 Личные трофеи:\n" + "\n".join(player.tournament_wins)
    if player.club_trophies:
        final_text += "\n\n🏆 Трофеи клуба:\n" + "\n".join(set(player.club_trophies))
    if player.personal_awards:
        final_text += "\n\n📋 Личные награды:\n" + "\n".join(player.personal_awards)
    if player.transfer_history:
        final_text += "\n\n🔄 Трансферы:\n" + "\n".join(player.transfer_history)
    await query.edit_message_text(final_text)
    context.user_data.clear()
    await query.message.reply_text("Для новой игры введите /start")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено. Для начала введите /start")
    return ConversationHandler.END

# --- Главная функция ---
def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_surname)],
            PATRONYMIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_patronymic)],
            BIRTHDATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_birthdate)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    app.add_handler(conv_handler)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number_input))

    app.add_handler(CallbackQueryHandler(next_year, pattern='next_year'))
    app.add_handler(CallbackQueryHandler(handle_transfer_choice, pattern='^(transfer_|reject_all_offers)'))
    app.add_handler(CallbackQueryHandler(end_career_from_transfer, pattern='end_career_from_transfer'))
    app.add_handler(CallbackQueryHandler(choose_national_number, pattern='choose_national_number'))
    app.add_handler(CallbackQueryHandler(info, pattern='info'))
    app.add_handler(CallbackQueryHandler(history, pattern='history'))
    app.add_handler(CallbackQueryHandler(club_trophies, pattern='club_trophies'))
    app.add_handler(CallbackQueryHandler(end_career, pattern='end'))

    print("Бот запущен...")
    # Запуск бота с отключёнными обработчиками сигналов (важно для Render)
    app.run_polling(use_signal_handlers=False)

if __name__ == '__main__':
    main()
