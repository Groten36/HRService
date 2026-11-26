"""Dni wolne od pracy w Polsce i liczenie dni roboczych."""
from datetime import date, timedelta
from functools import lru_cache


def easter_sunday(year):
    """Wielkanoc (algorytm Meeusa/Jonesa/Butchera)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


@lru_cache(maxsize=32)
def polish_holidays(year):
    easter = easter_sunday(year)
    days = {
        date(year, 1, 1): 'Nowy Rok',
        date(year, 1, 6): 'Trzech Króli',
        easter: 'Wielkanoc',
        easter + timedelta(days=1): 'Poniedziałek Wielkanocny',
        date(year, 5, 1): 'Święto Pracy',
        date(year, 5, 3): 'Święto Konstytucji 3 Maja',
        easter + timedelta(days=49): 'Zielone Świątki',
        easter + timedelta(days=60): 'Boże Ciało',
        date(year, 8, 15): 'Wniebowzięcie NMP',
        date(year, 11, 1): 'Wszystkich Świętych',
        date(year, 11, 11): 'Święto Niepodległości',
        date(year, 12, 25): 'Boże Narodzenie',
        date(year, 12, 26): 'Drugi dzień Bożego Narodzenia',
    }
    if year >= 2025:
        days[date(year, 12, 24)] = 'Wigilia'
    return days


def is_working_day(d):
    return d.weekday() < 5 and d not in polish_holidays(d.year)


def working_days(start, end):
    """Liczba dni roboczych w przedziale [start, end] (włącznie)."""
    if end < start:
        return 0
    return sum(1 for n in range((end - start).days + 1) if is_working_day(start + timedelta(days=n)))
