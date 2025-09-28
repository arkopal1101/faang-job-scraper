"""
Application settings and configuration management.

This module provides centralized configuration management using Pydantic Settings
for environment variable handling, type validation, and default values.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os


class AppSettings(BaseSettings):
    """Application-wide settings."""

    app_name: str = Field(default="FAANG Job Scraper", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="Modular FAANG job scraping system with FastAPI and plug-and-play architecture",
        description="Application description"
    )
    environment: str = Field(default="development", description="Environment (development, staging, production)")


class APISettings(BaseSettings):
    """API server configuration."""

    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, description="API server port")
    api_workers: int = Field(default=1, description="Number of API workers")
    api_reload: bool = Field(default=True, description="Enable auto-reload in development")
    api_prefix: str = Field(default="/api/v1", description="API URL prefix")

    @field_validator("api_port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class DatabaseSettings(BaseSettings):
    """Database configuration for future migration."""

    database_url: str = Field(default="sqlite:///./data/jobs.db", description="Database connection URL")


class DataSettings(BaseSettings):
    """Data storage and processing settings."""

    data_storage_path: str = Field(default="./data/jobs.json", description="Path to JSON data file")
    data_backup_path: str = Field(default="./data/backups/", description="Path to backup directory")
    data_max_backups: int = Field(default=10, description="Maximum number of backups to keep")
    data_compression: bool = Field(default=True, description="Enable data compression")

    @field_validator("data_storage_path", "data_backup_path")
    def validate_paths(cls, v):
        # Ensure parent directories exist
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class ScrapingSettings(BaseSettings):
    """Web scraping configuration."""

    scrape_interval_minutes: int = Field(default=60, description="Scraping interval in minutes")
    max_concurrent_scrapers: int = Field(default=3, description="Maximum concurrent scrapers")
    request_timeout_seconds: int = Field(default=30, description="HTTP request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=5, description="Delay between retry attempts")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        description="User agent string for HTTP requests"
    )

    @field_validator("max_concurrent_scrapers")
    def validate_concurrent_scrapers(cls, v):
        if v < 1:
            raise ValueError("Must have at least 1 concurrent scraper")
        return v


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""

    rate_limit_requests_per_minute: int = Field(default=60, description="Requests per minute limit")
    rate_limit_burst: int = Field(default=10, description="Burst request limit")
    rate_limit_cooldown_seconds: int = Field(default=60, description="Cooldown period after rate limit hit")


class BrowserSettings(BaseSettings):
    """Browser and WebDriver configuration."""

    browser_type: str = Field(default="chrome", description="Browser type (chrome, firefox)")
    browser_headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_timeout: int = Field(default=30, description="Browser operation timeout")
    browser_window_size: str = Field(default="1920x1080", description="Browser window size")
    webdriver_path: str = Field(default="auto", description="WebDriver binary path")
    chrome_binary_path: Optional[str] = Field(default=None, description="Chrome binary path")
    firefox_binary_path: Optional[str] = Field(default=None, description="Firefox binary path")

    @field_validator("browser_type")
    def validate_browser_type(cls, v):
        if v.lower() not in ["chrome", "firefox"]:
            raise ValueError("Browser type must be 'chrome' or 'firefox'")
        return v.lower()


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="structured", description="Log format (structured, json)")
    log_file_path: str = Field(default="./logs/scraper.log", description="Log file path")
    log_file_max_size_mb: int = Field(default=10, description="Maximum log file size in MB")
    log_file_backup_count: int = Field(default=5, description="Number of log file backups")
    log_console_output: bool = Field(default=True, description="Enable console logging")

    @field_validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("log_file_path")
    def validate_log_file_path(cls, v):
        # Ensure log directory exists
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class JobProcessingSettings(BaseSettings):
    """Job data processing settings."""

    max_jobs_per_company: int = Field(default=100, description="Maximum jobs to scrape per company")
    job_deduplication: bool = Field(default=True, description="Enable job deduplication")
    job_data_retention_days: int = Field(default=30, description="Job data retention period")
    min_job_description_length: int = Field(default=50, description="Minimum job description length")
    max_job_description_length: int = Field(default=10000, description="Maximum job description length")


class CompanySettings(BaseSettings):
    """Company-specific scraping settings."""

    enable_meta_scraping: bool = Field(default=True, description="Enable Meta/Facebook scraping")
    enable_amazon_scraping: bool = Field(default=True, description="Enable Amazon scraping")
    enable_apple_scraping: bool = Field(default=True, description="Enable Apple scraping")
    enable_netflix_scraping: bool = Field(default=True, description="Enable Netflix scraping")
    enable_google_scraping: bool = Field(default=True, description="Enable Google scraping")


class ProxySettings(BaseSettings):
    """Proxy configuration."""

    use_proxy: bool = Field(default=False, description="Enable proxy usage")
    proxy_host: Optional[str] = Field(default=None, description="Proxy host")
    proxy_port: Optional[int] = Field(default=None, description="Proxy port")
    proxy_username: Optional[str] = Field(default=None, description="Proxy username")
    proxy_password: Optional[str] = Field(default=None, description="Proxy password")
    proxy_type: str = Field(default="http", description="Proxy type (http, https, socks5)")


class CacheSettings(BaseSettings):
    """Cache configuration."""

    enable_caching: bool = Field(default=True, description="Enable caching")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")
    cache_max_size_mb: int = Field(default=100, description="Maximum cache size in MB")


class SecuritySettings(BaseSettings):
    """Security configuration."""

    api_key: str = Field(default="your-secret-api-key-here", description="API key for authentication")
    jwt_secret_key: str = Field(default="your-jwt-secret-key-here", description="JWT secret key")
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration in hours")
    allowed_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], description="Allowed hosts")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS allowed origins"
    )


class Settings:
    """Main settings container that combines all setting groups."""

    def __init__(self):
        """Initialize all settings from environment variables."""
        self.app = AppSettings()
        self.api = APISettings()
        self.database = DatabaseSettings()
        self.data = DataSettings()
        self.scraping = ScrapingSettings()
        self.rate_limit = RateLimitSettings()
        self.browser = BrowserSettings()
        self.logging = LoggingSettings()
        self.job_processing = JobProcessingSettings()
        self.companies = CompanySettings()
        self.proxy = ProxySettings()
        self.cache = CacheSettings()
        self.security = SecuritySettings()

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app.environment.lower() == "production"

    def get_enabled_companies(self) -> List[str]:
        """Get list of enabled companies for scraping."""
        enabled_companies = []

        if self.companies.enable_meta_scraping:
            enabled_companies.append("meta")
        if self.companies.enable_amazon_scraping:
            enabled_companies.append("amazon")
        if self.companies.enable_apple_scraping:
            enabled_companies.append("apple")
        if self.companies.enable_netflix_scraping:
            enabled_companies.append("netflix")
        if self.companies.enable_google_scraping:
            enabled_companies.append("google")

        return enabled_companies

    def get_database_url(self) -> str:
        """Get database URL with environment-specific adjustments."""
        if self.is_development and self.database.database_url.startswith("sqlite"):
            # Ensure SQLite database directory exists
            db_path = Path(self.database.database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        return self.database.database_url


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


# Helper function for FastAPI dependency injection
def get_settings_dependency() -> Settings:
    """FastAPI dependency for injecting settings."""
    return settings
