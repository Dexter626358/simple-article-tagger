"""
Клиент для работы с ИС «Метафора» (metafora.rcsi.science).
Загрузка учётных данных из .env или переменных окружения, вход и сохранение сессии для дальнейших запросов.
"""

import logging
import os
import re
from urllib.parse import urljoin

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://metafora.rcsi.science"
DEFAULT_TIMEOUT = 30


def get_credentials() -> tuple[str, str]:
    """Читает логин и пароль из переменных окружения."""
    login = os.getenv("METAFORA_LOGIN", "").strip()
    password = os.getenv("METAFORA_PASSWORD", "").strip()
    if not login or not password:
        raise ValueError(
            "Задайте METAFORA_LOGIN и METAFORA_PASSWORD в .env или переменных окружения"
        )
    return login, password


def _parse_login_form(html: str, base_url: str) -> dict | None:
    """Извлекает из HTML действие формы и скрытые поля (в т.ч. CSRF)."""
    action_match = re.search(
        r'<form[^>]*\s+action=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    action = action_match.group(1).strip() if action_match else "/login"
    if not action.startswith("http"):
        action = urljoin(base_url, action)

    inputs = {}
    for m in re.finditer(
        r'<input[^>]*\s+name=["\']([^"\']+)["\'][^>]*\s+value=["\']([^"\']*)["\']',
        html,
        re.IGNORECASE,
    ):
        inputs[m.group(1)] = m.group(2)
    for m in re.finditer(
        r'<input[^>]*\s+value=["\']([^"\']*)["\'][^>]*\s+name=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE,
    ):
        inputs[m.group(2)] = m.group(1)

    login_name = None
    password_name = None
    for name in inputs.keys():
        n = name.lower()
        if n in ("email", "username", "login", "user", "inputname"):
            login_name = name
        if n in ("password", "inputpassword"):
            password_name = name
    if not login_name:
        for m in re.finditer(
            r'<input[^>]*\s+name=["\']([^"\']+)["\'][^>]*type=["\'](?:text|email)["\']',
            html, re.I
        ):
            login_name = m.group(1)
            break
        if not login_name:
            for m in re.finditer(
                r'<input[^>]*type=["\'](?:text|email)["\'][^>]*name=["\']([^"\']+)["\']',
                html, re.I
            ):
                login_name = m.group(1)
                break
    if not password_name:
        for m in re.finditer(
            r'<input[^>]*type=["\']password["\'][^>]*name=["\']([^"\']+)["\']',
            html, re.I
        ):
            password_name = m.group(1)
            break
        if not password_name:
            for m in re.finditer(
                r'<input[^>]*name=["\']([^"\']+)["\'][^>]*type=["\']password["\']',
                html, re.I
            ):
                password_name = m.group(1)
                break

    if not action or (not login_name and not password_name):
        return None
    return {
        "action": action,
        "inputs": inputs,
        "login_field": login_name or "login",
        "password_field": password_name or "password",
    }


class MetaforaClient:
    """Клиент с сессией для запросов к ИС «Метафора» после входа."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = (base_url or os.getenv("METAFORA_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MetaforaParser/1.0 (Python; +https://github.com/metathora-parser)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        })

    def _url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"

    def login(self, login: str | None = None, password: str | None = None) -> bool:
        """
        Выполняет вход. Если логин/пароль не переданы — берёт из окружения (.env или переменные).
        Возвращает True при успешном входе.
        """
        if login is None or password is None:
            login, password = get_credentials()

        login_page_url = self._url("/")
        try:
            r = self.session.get(login_page_url, timeout=self.timeout)
            r.raise_for_status()
        except requests.RequestException as e:
            logger.exception("Не удалось загрузить страницу входа: %s", e)
            return False

        form_info = _parse_login_form(r.text, self.base_url)
        if form_info:
            data = dict(form_info["inputs"])
            data[form_info["login_field"]] = login
            data[form_info["password_field"]] = password
            post_url = form_info["action"]
            logger.debug("POST логин на %s, поля: %s", post_url, list(data.keys()))
        else:
            post_url = self._url("/login")
            data = {"InputName": login, "InputPassword": password}
            token_m = re.search(r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']', r.text, re.I)
            if token_m:
                data["_token"] = token_m.group(1)

        try:
            r2 = self.session.post(
                post_url,
                data=data,
                timeout=self.timeout,
                allow_redirects=True,
            )
        except requests.RequestException as e:
            logger.exception("Ошибка при отправке формы входа: %s", e)
            return False

        if r2.status_code != 200:
            logger.warning("Ответ входа: %s %s", r2.status_code, r2.url)
            return False

        if "вход" in r2.text.lower() and "войти" in r2.text.lower() and "password" in r2.text.lower():
            logger.warning(
                "Похоже, вход не прошёл: на странице по-прежнему форма входа. "
                "Проверьте, что на metafora.rcsi.science доступен вход по логину/паролю (а не только через КИАС)."
            )
            return False

        logger.info("Вход выполнен, сессия сохранена.")
        return True

    def get(self, path: str, **kwargs) -> requests.Response:
        """GET-запрос с учётом базового URL и текущей сессии."""
        url = self._url(path)
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def is_logged_in(self) -> bool:
        """Проверяет, что сессия авторизована (запрос к защищённой странице)."""
        r = self.get("/")
        if r.status_code != 200:
            return False
        text = r.text.lower()
        if "войти" in text and "password" in text and "вход" in text:
            return False
        return True


def main() -> None:
    """Проверка входа: загрузка учётных данных из .env и попытка авторизации."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        client = MetaforaClient()
        if client.login():
            print("Вход выполнен успешно.")
            if client.is_logged_in():
                print("Сессия активна, можно делать запросы через client.get(...).")
            else:
                print("Предупреждение: проверка сессии не подтвердила авторизацию.")
        else:
            print("Вход не удался. Проверьте логин/пароль в .env и доступность сайта.")
    except ValueError as e:
        logger.error("%s", e)
        raise


if __name__ == "__main__":
    main()
