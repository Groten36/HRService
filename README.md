# HR Service

Boilerplate strony internetowej w Django 6.1.

## Struktura

```
hrservice/      konfiguracja projektu (settings, urls, wsgi/asgi)
pages/          strony publiczne: główna, o nas, kontakt (formularz -> e-mail)
documents/      zarządzenia i porady: lista, wyszukiwarka, pobieranie, CRUD
accounts/       rejestracja, profil; logowanie/wylogowanie/reset hasła z django.contrib.auth
templates/      base.html, partials/, pages/, registration/, 404/500
static/         css/main.css, js/main.js, img/
```

## Uruchomienie

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_documents   # grupa redaktorów + domyślne kategorie
python manage.py createsuperuser
python manage.py runserver
```

Strona: http://127.0.0.1:8000/ · Panel admina: http://127.0.0.1:8000/admin/

## Dokumenty (zarządzenia i porady)

- `/dokumenty/` — lista z wyszukiwarką (tytuł, numer, opis) i filtrami (rodzaj, kategoria), paginacja.
- Przeglądanie i pobieranie: obecnie bez logowania (`DOCUMENTS_REQUIRE_LOGIN=False`). **TODO: włączyć przed wdrożeniem.** Niezalogowani i pracownicy widzą tylko dokumenty opublikowane.
- Dodawanie, edycja i usuwanie: użytkownicy z grupy **Redaktorzy dokumentów**
  (przypisz w panelu admina) lub superuser. Redaktorzy widzą też nieopublikowane dokumenty.
- Pliki zapisywane są w `media/documents/` pod losowymi nazwami i **nie są serwowane publicznie**.
  Pobieranie odbywa się przez `/dokumenty/<id>/pobierz/`, który sprawdza uprawnienia.
  Przy produkcyjnym wdrożeniu nie wystawiaj katalogu `media/` przez serwer WWW.
- Dozwolone formaty — dokumenty: pdf, doc(x), odt, xls(x), ods, txt, png, jpg (limit `DJANGO_DOCUMENT_MAX_UPLOAD_MB`, domyślnie 20); programy (`/dokumenty/programy/`): exe, msi, msix, zip, 7z, dmg, pkg, deb, rpm, appimage (limit `DJANGO_SOFTWARE_MAX_UPLOAD_MB`, domyślnie 1024).
- Usunięcie lub podmiana dokumentu usuwa stary plik z dysku.

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
