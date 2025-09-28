"""Utility for creating scraper instances from configuration."""

from __future__ import annotations

import copy
import importlib
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, Optional, Type, Union

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory responsible for instantiating company scraper classes."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """Load scraper configuration from the provided JSON file."""

        self._config_path = Path(config_path) if config_path else self._default_config_path()

        if not self._config_path.exists():
            raise FileNotFoundError(f"Scraper configuration not found: {self._config_path}")

        self._raw_config = self._load_config(self._config_path)
        self._company_configs: Dict[str, Dict] = {
            key.lower(): value for key, value in self._raw_config.get("companies", {}).items()
        }
        self._global_config: Dict = {
            key: value for key, value in self._raw_config.items() if key != "companies"
        }
        self._registry: Dict[str, Type[BaseScraper]] = {}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _default_config_path() -> Path:
        """Return the default path to the company configuration file."""

        return Path(__file__).resolve().parents[1] / "config" / "company_configs.json"

    @staticmethod
    def _load_config(path: Path) -> Dict:
        """Load the JSON configuration file."""

        with path.open("r", encoding="utf-8") as config_file:
            return json.load(config_file)

    # ------------------------------------------------------------------
    # Registration and lookup utilities
    # ------------------------------------------------------------------
    def register_scraper(self, company_key: str, scraper_cls: Type[BaseScraper]) -> None:
        """Register a scraper class for a given company key."""

        if not issubclass(scraper_cls, BaseScraper):
            raise TypeError("Scraper class must inherit from BaseScraper")

        normalized_key = company_key.lower()

        if normalized_key not in self._company_configs:
            raise KeyError(f"Unknown company '{company_key}' in configuration")

        self._registry[normalized_key] = scraper_cls
        logger.debug("Registered scraper %s for company %s", scraper_cls.__name__, normalized_key)

    def registered_companies(self) -> Iterable[str]:
        """Return an iterable of currently registered company keys."""

        return self._registry.keys()

    def available_companies(self, include_disabled: bool = False) -> Iterable[str]:
        """Return an iterable of company keys available in the configuration."""

        for key, config in self._company_configs.items():
            if include_disabled or config.get("enabled", True):
                yield key

    def get_company_config(self, company_key: str) -> Dict:
        """Retrieve a deep copy of the configuration for a company."""

        normalized_key = company_key.lower()

        if normalized_key not in self._company_configs:
            raise KeyError(f"No configuration found for company '{company_key}'")

        return copy.deepcopy(self._company_configs[normalized_key])

    # ------------------------------------------------------------------
    # Factory logic
    # ------------------------------------------------------------------
    def create_scraper(self, company_key: str) -> BaseScraper:
        """Instantiate the scraper associated with the provided company."""

        normalized_key = company_key.lower()

        company_config = self.get_company_config(normalized_key)

        if not company_config.get("enabled", True):
            raise ValueError(f"Scraper for company '{company_key}' is disabled in configuration")

        scraper_cls = self._get_scraper_class(normalized_key, company_config)

        return scraper_cls(company_config=company_config, global_config=copy.deepcopy(self._global_config))

    def _get_scraper_class(self, company_key: str, company_config: Dict) -> Type[BaseScraper]:
        """Resolve the scraper class for the given company."""

        if company_key in self._registry:
            return self._registry[company_key]

        class_name = company_config.get("scraper_class")

        if not class_name:
            raise ValueError(f"Scraper class not specified for company '{company_key}'")

        module_path = company_config.get("module", f"scrapers.companies.{company_key}_scraper")

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                f"Unable to import module '{module_path}' for company '{company_key}'"
            ) from exc

        try:
            scraper_cls = getattr(module, class_name)
        except AttributeError as exc:
            raise AttributeError(
                f"Module '{module_path}' does not define scraper class '{class_name}'"
            ) from exc

        if not issubclass(scraper_cls, BaseScraper):
            raise TypeError(
                f"Scraper class '{class_name}' for company '{company_key}' must inherit from BaseScraper"
            )

        self._registry[company_key] = scraper_cls
        logger.debug("Dynamically loaded scraper %s for company %s", class_name, company_key)
        return scraper_cls


__all__ = ["ScraperFactory"]
