"""Tests for the scraper factory implementation."""

from typing import Dict, List
import sys
import types

import pytest


def _install_pydantic_stub() -> None:
    """Install a minimal pydantic stub when the package is unavailable."""

    if "pydantic" in sys.modules:
        return

    stub = types.ModuleType("pydantic")

    from dataclasses import dataclass, field as dataclass_field

    class ConfigDict(dict):
        def __init__(self, **kwargs):  # pragma: no cover - trivial initializer
            super().__init__(**kwargs)

    def Field(*, default=None, default_factory=None):  # pragma: no cover - simple helper
        if default_factory is not None:
            return dataclass_field(default_factory=default_factory)
        if default is not None:
            return dataclass_field(default=default)
        return dataclass_field()

    class _BaseModelMeta(type):
        def __new__(mcls, name, bases, namespace):  # pragma: no cover - simple meta
            cls = super().__new__(mcls, name, bases, dict(namespace))
            return dataclass(cls)

    class BaseModel(metaclass=_BaseModelMeta):
        pass

    stub.BaseModel = BaseModel
    stub.ConfigDict = ConfigDict
    stub.Field = Field

    sys.modules.setdefault("pydantic", stub)


_install_pydantic_stub()


def _install_selenium_stubs() -> None:
    """Install lightweight Selenium stubs so imports succeed during testing."""

    selenium_module = types.ModuleType("selenium")

    # webdriver module and dependencies
    webdriver_module = types.ModuleType("selenium.webdriver")
    webdriver_module.Remote = type("Remote", (), {})
    selenium_module.webdriver = webdriver_module

    webdriver_common = types.ModuleType("selenium.webdriver.common")
    webdriver_common_by = types.ModuleType("selenium.webdriver.common.by")
    webdriver_common_by.By = type("By", (), {})

    webdriver_support = types.ModuleType("selenium.webdriver.support")
    webdriver_support_ui = types.ModuleType("selenium.webdriver.support.ui")
    webdriver_support_ui.WebDriverWait = type("WebDriverWait", (), {})
    webdriver_support_ec = types.ModuleType("selenium.webdriver.support.expected_conditions")

    webdriver_chrome_options = types.ModuleType("selenium.webdriver.chrome.options")
    webdriver_chrome_options.Options = type("Options", (), {})

    webdriver_firefox_options = types.ModuleType("selenium.webdriver.firefox.options")
    webdriver_firefox_options.Options = type("Options", (), {})

    selenium_common = types.ModuleType("selenium.common")
    selenium_common_exceptions = types.ModuleType("selenium.common.exceptions")
    selenium_common_exceptions.TimeoutException = type("TimeoutException", (Exception,), {})
    selenium_common_exceptions.WebDriverException = type("WebDriverException", (Exception,), {})

    modules: Dict[str, types.ModuleType] = {
        "selenium": selenium_module,
        "selenium.webdriver": webdriver_module,
        "selenium.webdriver.common": webdriver_common,
        "selenium.webdriver.common.by": webdriver_common_by,
        "selenium.webdriver.support": webdriver_support,
        "selenium.webdriver.support.ui": webdriver_support_ui,
        "selenium.webdriver.support.expected_conditions": webdriver_support_ec,
        "selenium.webdriver.chrome": types.ModuleType("selenium.webdriver.chrome"),
        "selenium.webdriver.chrome.options": webdriver_chrome_options,
        "selenium.webdriver.firefox": types.ModuleType("selenium.webdriver.firefox"),
        "selenium.webdriver.firefox.options": webdriver_firefox_options,
        "selenium.common": selenium_common,
        "selenium.common.exceptions": selenium_common_exceptions,
    }

    for name, module in modules.items():
        sys.modules.setdefault(name, module)


def _install_webdriver_manager_stubs() -> None:
    """Install webdriver-manager stubs used by the base scraper."""

    class _ChromeDriverManager:
        def install(self) -> str:  # pragma: no cover - trivial return
            return "chromedriver"

    class _GeckoDriverManager:
        def install(self) -> str:  # pragma: no cover - trivial return
            return "geckodriver"

    chrome_module = types.ModuleType("webdriver_manager.chrome")
    chrome_module.ChromeDriverManager = _ChromeDriverManager

    firefox_module = types.ModuleType("webdriver_manager.firefox")
    firefox_module.GeckoDriverManager = _GeckoDriverManager

    sys.modules.setdefault("webdriver_manager", types.ModuleType("webdriver_manager"))
    sys.modules.setdefault("webdriver_manager.chrome", chrome_module)
    sys.modules.setdefault("webdriver_manager.firefox", firefox_module)


_install_selenium_stubs()
_install_webdriver_manager_stubs()


def _install_settings_stub() -> None:
    """Provide a lightweight settings module used by the base scraper."""

    config_package = sys.modules.setdefault("config", types.ModuleType("config"))
    settings_module = types.ModuleType("config.settings")

    class _BrowserSettings:
        browser_timeout = 30
        browser_type = "chrome"
        browser_headless = True
        browser_window_size = "1920x1080"
        webdriver_path = "auto"
        chrome_binary_path = None
        firefox_binary_path = None

    class _ScrapingSettings:
        user_agent = "test-agent"

    class _Settings:
        def __init__(self) -> None:
            self.browser = _BrowserSettings()
            self.scraping = _ScrapingSettings()

    def get_settings() -> _Settings:  # pragma: no cover - simple factory
        return _Settings()

    settings_module.get_settings = get_settings
    config_package.settings = settings_module
    sys.modules["config.settings"] = settings_module


_install_settings_stub()

from scrapers import ScraperFactory  # noqa: E402  pylint: disable=wrong-import-position
from scrapers.base_scraper import BaseScraper  # noqa: E402  pylint: disable=wrong-import-position


class DummyScraper(BaseScraper):
    """Minimal scraper implementation used for testing."""

    async def _extract_job_listings(self) -> List[Dict]:
        return []

    async def scrape_jobs(self) -> List:  # type: ignore[override]
        # Override to avoid interacting with Selenium during tests
        return []


@pytest.fixture()
def factory() -> ScraperFactory:
    return ScraperFactory()


def test_available_companies(factory: ScraperFactory) -> None:
    companies = set(factory.available_companies())
    assert {"meta", "amazon", "apple", "netflix", "google"}.issubset(companies)


def test_register_and_create_scraper(factory: ScraperFactory) -> None:
    factory.register_scraper("meta", DummyScraper)

    scraper = factory.create_scraper("meta")

    assert isinstance(scraper, DummyScraper)
    assert scraper.company_config["name"].lower() == "meta"
    assert "categorization_rules" in scraper.global_config


def test_disabled_scraper_raises(factory: ScraperFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    original_get_company_config = factory.get_company_config

    def disable_meta(_: str) -> Dict:
        config = original_get_company_config("meta")
        config["enabled"] = False
        return config

    monkeypatch.setattr(factory, "get_company_config", disable_meta)

    with pytest.raises(ValueError):
        factory.create_scraper("meta")


def test_missing_scraper_class_raises(factory: ScraperFactory, monkeypatch: pytest.MonkeyPatch) -> None:
    original_get_company_config = factory.get_company_config

    def config_without_class(_: str) -> Dict:
        config = original_get_company_config("meta")
        config.pop("scraper_class", None)
        return config

    monkeypatch.setattr(factory, "get_company_config", config_without_class)

    with pytest.raises(ValueError):
        factory.create_scraper("meta")
