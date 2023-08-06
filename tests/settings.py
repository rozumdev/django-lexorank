SECRET_KEY = "tests"

INSTALLED_APPS = [
    "tests",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
