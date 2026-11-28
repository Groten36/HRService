# HR Service

Boilerplate strony internetowej w Django 6.1.

## Struktura

```
hrservice/      konfiguracja projektu (settings, urls, wsgi/asgi)
pages/          strony publiczne: główna, o nas, kontakt (formularz -> e-mail)
documents/      zarządzenia i porady: lista, wyszukiwarka, pobieranie, CRUD
accounts/       role, zarządzanie użytkownikami, profil; logowanie/wylogowanie/reset hasła z django.contrib.auth
templates/      base.html, partials/, pages/, registration/, 404/500
static/         css/main.css, js/main.js, img/
```

## Uruchomienie

Jedną komendą:

```bash
./run.sh                 # domyślnie http://127.0.0.1:8000/
./run.sh 0.0.0.0:8000    # opcjonalnie inny adres/port
```

Skrypt tworzy `.venv` (jeśli nie istnieje), instaluje zależności (tylko gdy zmienił się
`requirements.txt`), wczytuje `.env` (jeśli istnieje), wykonuje migracje, tworzy domyślne
kategorie dokumentów, przy pierwszym uruchomieniu prosi o utworzenie superużytkownika
(lub tworzy go bez pytania z `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD` /
`DJANGO_SUPERUSER_EMAIL`) i startuje serwer.

Ręcznie, krok po kroku:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_documents   # domyślne kategorie dokumentów
python manage.py createsuperuser
python manage.py runserver
```

Strona: http://127.0.0.1:8000/ · Panel admina: http://127.0.0.1:8000/admin/

## Dokumenty (zarządzenia i porady)

- `/dokumenty/` — lista z wyszukiwarką (tytuł, numer, opis) i filtrami (rodzaj, kategoria), paginacja.
- Przeglądanie i pobieranie: obecnie bez logowania (`DOCUMENTS_REQUIRE_LOGIN=False`). **TODO: włączyć przed wdrożeniem.** Niezalogowani i pracownicy widzą tylko dokumenty opublikowane.
- Dodawanie, edycja i usuwanie: rola **Administrator IT** lub superuser. Administratorzy IT widzą też nieopublikowane dokumenty.
- Pliki zapisywane są w `media/documents/` pod losowymi nazwami i **nie są serwowane publicznie**.
  Pobieranie odbywa się przez `/dokumenty/<id>/pobierz/`, który sprawdza uprawnienia.
  Przy produkcyjnym wdrożeniu nie wystawiaj katalogu `media/` przez serwer WWW.
- Dozwolone formaty — dokumenty: pdf, doc(x), odt, xls(x), ods, txt, png, jpg (limit `DJANGO_DOCUMENT_MAX_UPLOAD_MB`, domyślnie 20); programy (`/dokumenty/programy/`): exe, msi, msix, zip, 7z, dmg, pkg, deb, rpm, appimage (limit `DJANGO_SOFTWARE_MAX_UPLOAD_MB`, domyślnie 1024).
- Usunięcie lub podmiana dokumentu usuwa stary plik z dysku.

## Role użytkowników

Grupy ról tworzone są automatycznie przy `migrate` (ręcznie: `python manage.py setup_roles`).
Definicje uprawnień: `accounts/roles.py`.

| Rola | Uprawnienia |
|---|---|
| **Pracownik** (domyślna dla nowych kont) | przegląda stronę; w portalu HR czyta ogłoszenia, składa wnioski urlopowe, widzi swoje dane |
| **Administrator IT** | zarządza użytkownikami (`/accounts/uzytkownicy/`), dokumentami, programami, kategoriami i przydatnymi linkami |
| **Administrator HR** | ogłoszenia HR, rozpatrywanie wniosków urlopowych, profile kadrowe, książka telefoniczna |

Publiczna rejestracja jest wyłączona — konta zakłada wyłącznie superużytkownik lub Administrator IT.

Zabezpieczenia: Administrator IT nie może nadać uprawnień superużytkownika, edytować ani usuwać
superużytkowników, zmienić własnej roli ani usunąć własnego konta (zarówno w portalu, jak i w panelu admina).

## Konfiguracja

Ustawienia czytane są ze zmiennych środowiskowych — patrz `.env.example`.
W trybie deweloperskim e-maile wypisywane są w konsoli.

## Testy

```bash
python manage.py test
```

## Produkcja

```bash
export DJANGO_DEBUG=False DJANGO_SECRET_KEY=... DJANGO_ALLOWED_HOSTS=twojadomena.pl
python manage.py collectstatic
python manage.py check --deploy
```
