"""
Base scraper abstract class for all company-specific scrapers.

This module provides the foundation for all company scrapers with common
functionality, job categorization, and standardized interfaces.
"""

import json
import re
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from urllib.parse import urljoin, urlparse
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from data.models import (
    Job, JobCategory, JobType, ExperienceLevel, WorkplaceType,
    CompanyName, JobCategorizationResult
)
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class JobCategorizer:
    """Job categorization utility class."""

    def __init__(self, category_configs: Dict[str, Any]):
        """Initialize with category configuration."""
        self.categories = category_configs.get("job_categories", {})
        self.rules = category_configs.get("categorization_rules", {})

    def categorize_job(self, title: str, description: str, department: Optional[str] = None) -> JobCategorizationResult:
        """Categorize a job based on title, description, and department."""
        scores = {}
        keyword_matches = {}

        # Get weights from configuration
        title_weight = self.rules.get("title_weight", 0.6)
        department_weight = self.rules.get("department_weight", 0.3)
        description_weight = self.rules.get("description_weight", 0.1)

        # Normalize text for matching
        title_lower = title.lower() if title else ""
        description_lower = description.lower() if description else ""
        department_lower = department.lower() if department else ""

        # Calculate scores for each category
        for category_id, category_info in self.categories.items():
            score = 0
            matches = {}

            # Check keywords in title
            title_matches = self._find_keyword_matches(title_lower, category_info.get("keywords", []))
            if title_matches:
                score += len(title_matches) * title_weight
                matches["title"] = title_matches

            # Check keywords in description (sample first 500 chars for performance)
            desc_sample = description_lower[:500]
            desc_matches = self._find_keyword_matches(desc_sample, category_info.get("keywords", []))
            if desc_matches:
                score += len(desc_matches) * description_weight * 0.5  # Reduced weight for description
                matches["description"] = desc_matches

            # Check department matches
            dept_matches = self._find_keyword_matches(department_lower, category_info.get("departments", []))
            if dept_matches:
                score += len(dept_matches) * department_weight
                matches["department"] = dept_matches

            # Apply exact match bonus
            exact_match_bonus = self.rules.get("keyword_matching", {}).get("exact_match_bonus", 2.0)
            for match_list in matches.values():
                for match in match_list:
                    if len(match.split()) == 1:  # Single word exact matches get bonus
                        score += exact_match_bonus

            if score > 0:
                scores[category_id] = score
                keyword_matches[category_id] = len([m for match_list in matches.values() for m in match_list])

        # Determine best category
        if not scores:
            return JobCategorizationResult(
                category=JobCategory.OTHER,
                confidence=0.0,
                keyword_matches=keyword_matches,
                reasoning="No category keywords found"
            )

        # Get category with highest score
        best_category_id = max(scores.items(), key=lambda x: x[1])[0]
        best_score = scores[best_category_id]

        # Normalize confidence score
        max_possible_score = len(self.categories[best_category_id].get("keywords", [])) * title_weight
        confidence = min(best_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        # Check minimum confidence threshold
        min_confidence = self.rules.get("min_confidence_threshold", 0.3)
        if confidence < min_confidence:
            return JobCategorizationResult(
                category=JobCategory.OTHER,
                confidence=confidence,
                keyword_matches=keyword_matches,
                reasoning=f"Confidence {confidence:.2f} below threshold {min_confidence}"
            )

        # Check if department matches category
        category_info = self.categories[best_category_id]
        department_match = any(
            dept.lower() in department_lower
            for dept in category_info.get("departments", [])
        ) if department_lower else False

        try:
            category_enum = JobCategory(best_category_id)
        except ValueError:
            category_enum = JobCategory.OTHER

        return JobCategorizationResult(
            category=category_enum,
            confidence=confidence,
            keyword_matches=keyword_matches,
            department_match=department_match,
            reasoning=f"Best match with score {best_score:.2f}"
        )

    def _find_keyword_matches(self, text: str, keywords: List[str]) -> List[str]:
        """Find keyword matches in text."""
        matches = []

        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Check for exact phrase match
            if keyword_lower in text:
                matches.append(keyword)

            # Check for partial matches (individual words)
            elif len(keyword.split()) > 1:
                words = keyword.split()
                if all(word.lower() in text for word in words):
                    matches.append(keyword)

        return matches


class BaseScraper(ABC):
    """Abstract base class for all company scrapers."""

    def __init__(self, company_config: Dict[str, Any], global_config: Dict[str, Any]):
        """Initialize base scraper with configuration."""
        self.company_config = company_config
        self.global_config = global_config
        self.company_name = CompanyName(company_config["name"].lower())
        self.display_name = company_config.get("display_name", company_config["name"])
        self.careers_url = company_config["careers_url"]
        self.selectors = company_config.get("selectors", {})
        self.search_params = company_config.get("search_params", {})
        self.request_config = company_config.get("request_config", {})

        # Rate limiting
        self.rate_limit = company_config.get("rate_limit", global_config.get("default_rate_limit", 2))
        self.max_pages = company_config.get("max_pages", global_config.get("default_max_pages", 5))

        # Browser configuration
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None

        # Job categorizer
        self.categorizer = JobCategorizer(global_config)

        # Statistics
        self.stats = {
            "jobs_found": 0,
            "jobs_processed": 0,
            "jobs_categorized": 0,
            "errors": []
        }

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def initialize(self) -> bool:
        """Initialize the scraper (setup browser, etc.)."""
        try:
            self.driver = self._create_driver()
            self.wait = WebDriverWait(
                self.driver,
                settings.browser.browser_timeout
            )
            self.logger.info(f"Initialized {self.display_name} scraper")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize scraper: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources (close browser, etc.)."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(f"Cleaned up {self.display_name} scraper")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")

    def _create_driver(self) -> webdriver.Remote:
        """Create and configure WebDriver instance."""
        browser_type = settings.browser.browser_type.lower()

        if browser_type == "chrome":
            options = ChromeOptions()

            if settings.browser.browser_headless:
                options.add_argument("--headless")

            # Security and performance options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-images")
            options.add_argument("--disable-javascript")  # Can be removed if JS is needed
            options.add_argument(f"--window-size={settings.browser.browser_window_size}")

            # User agent
            user_agent = self._get_user_agent()
            options.add_argument(f"--user-agent={user_agent}")

            # Chrome binary path if specified
            if settings.browser.chrome_binary_path:
                options.binary_location = settings.browser.chrome_binary_path

            # Create driver
            if settings.browser.webdriver_path == "auto":
                driver_path = ChromeDriverManager().install()
            else:
                driver_path = settings.browser.webdriver_path

            return webdriver.Chrome(executable_path=driver_path, options=options)

        elif browser_type == "firefox":
            options = FirefoxOptions()

            if settings.browser.browser_headless:
                options.add_argument("--headless")

            # Firefox-specific options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")

            # User agent
            user_agent = self._get_user_agent()
            options.set_preference("general.useragent.override", user_agent)

            # Firefox binary path if specified
            if settings.browser.firefox_binary_path:
                options.binary_location = settings.browser.firefox_binary_path

            # Create driver
            if settings.browser.webdriver_path == "auto":
                driver_path = GeckoDriverManager().install()
            else:
                driver_path = settings.browser.webdriver_path

            return webdriver.Firefox(executable_path=driver_path, options=options)

        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")

    def _get_user_agent(self) -> str:
        """Get user agent string."""
        user_agents = self.global_config.get("user_agents", [settings.scraping.user_agent])

        if self.global_config.get("user_agent_rotation", False) and len(user_agents) > 1:
            import random
            return random.choice(user_agents)

        return user_agents[0] if user_agents else settings.scraping.user_agent

    async def scrape_jobs(self) -> List[Job]:
        """Main scraping method. Must be implemented by subclasses."""
        jobs = []

        try:
            # Navigate to careers page
            self.driver.get(self.careers_url)
            await self._wait_for_page_load()

            # Get job listings
            raw_jobs = await self._extract_job_listings()

            # Process each job
            for raw_job in raw_jobs:
                try:
                    job = await self._process_job_data(raw_job)
                    if job:
                        jobs.append(job)
                        self.stats["jobs_processed"] += 1
                except Exception as e:
                    self.logger.error(f"Error processing job: {e}")
                    self.stats["errors"].append(str(e))

                # Rate limiting
                if self.rate_limit > 0:
                    await asyncio.sleep(1 / self.rate_limit)

            self.stats["jobs_found"] = len(raw_jobs)
            self.logger.info(f"Scraped {len(jobs)} jobs from {self.display_name}")

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            self.stats["errors"].append(str(e))

        return jobs

    @abstractmethod
    async def _extract_job_listings(self) -> List[Dict[str, Any]]:
        """Extract raw job listing data. Must be implemented by subclasses."""
        pass

    async def _process_job_data(self, raw_job: Dict[str, Any]) -> Optional[Job]:
        """Process raw job data into Job model."""
        try:
            # Extract basic information
            title = self._clean_text(raw_job.get("title", ""))
            description = self._clean_text(raw_job.get("description", ""))
            location = self._clean_text(raw_job.get("location", ""))
            department = self._clean_text(raw_job.get("department"))
            url = raw_job.get("url", "")

            if not title or not description or not location:
                self.logger.warning("Missing required job fields")
                return None

            # Ensure absolute URL
            if url and not url.startswith("http"):
                url = urljoin(self.careers_url, url)

            # Categorize job
            categorization = self.categorizer.categorize_job(title, description, department)
            self.stats["jobs_categorized"] += 1

            # Parse dates
            posted_date = self._parse_date(raw_job.get("posted_date"))

            # Determine job type
            job_type = self._determine_job_type(title, description)

            # Determine experience level
            experience_level = self._determine_experience_level(title, description)

            # Determine workplace type
            workplace_type = self._determine_workplace_type(location, description)

            # Create Job model
            job = Job(
                id="",  # Will be auto-generated
                url=url,
                company=self.company_name,
                title=title,
                department=department,
                location=location,
                job_type=job_type,
                workplace_type=workplace_type,
                experience_level=experience_level,
                description=description,
                requirements=self._clean_text(raw_job.get("requirements")),
                responsibilities=self._clean_text(raw_job.get("responsibilities")),
                benefits=self._clean_text(raw_job.get("benefits")),
                category=categorization.category,
                categorization_result=categorization,
                posted_date=posted_date,
                source_data=raw_job
            )

            return job

        except Exception as e:
            self.logger.error(f"Error processing job data: {e}")
            return None

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text."""
        if not text:
            return None

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)

        # Remove special characters that might cause issues
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        return text if text else None

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string into date object."""
        if not date_str:
            return None

        # Common date formats
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\w{3,9}\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
            r'\d{1,2}\s+\w{3,9}\s+\d{4}',  # DD Month YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    from dateutil.parser import parse
                    return parse(match.group()).date()
                except:
                    continue

        # If relative date (e.g., "2 days ago", "1 week ago")
        relative_patterns = [
            (r'(\d+)\s*days?\s*ago', lambda x: datetime.now().date()),
            (r'(\d+)\s*weeks?\s*ago', lambda x: datetime.now().date()),
            (r'yesterday', lambda x: datetime.now().date()),
            (r'today', lambda x: datetime.now().date()),
        ]

        for pattern, date_func in relative_patterns:
            if re.search(pattern, date_str.lower()):
                try:
                    return date_func(None)
                except:
                    continue

        return None

    def _determine_job_type(self, title: str, description: str) -> JobType:
        """Determine job type from title and description."""
        text = f"{title} {description}".lower()

        if any(word in text for word in ["intern", "internship", "student"]):
            return JobType.INTERNSHIP
        elif any(word in text for word in ["contract", "contractor", "temporary", "temp"]):
            return JobType.CONTRACT
        elif any(word in text for word in ["part time", "part-time", "parttime"]):
            return JobType.PART_TIME
        elif any(word in text for word in ["freelance", "freelancer", "consultant"]):
            return JobType.FREELANCE
        else:
            return JobType.FULL_TIME

    def _determine_experience_level(self, title: str, description: str) -> ExperienceLevel:
        """Determine experience level from title and description."""
        text = f"{title} {description}".lower()

        # Check title first (more reliable)
        title_lower = title.lower()

        if any(word in title_lower for word in ["senior", "sr.", "lead", "staff"]):
            return ExperienceLevel.SENIOR
        elif any(word in title_lower for word in ["junior", "jr.", "entry", "associate"]):
            if "entry" in title_lower:
                return ExperienceLevel.ENTRY_LEVEL
            return ExperienceLevel.ASSOCIATE
        elif any(word in title_lower for word in ["principal", "architect", "distinguished"]):
            return ExperienceLevel.PRINCIPAL
        elif any(word in title_lower for word in ["director", "head of", "vp", "vice president"]):
            return ExperienceLevel.DIRECTOR
        elif any(word in title_lower for word in ["cto", "ceo", "cmo", "cfo", "chief"]):
            return ExperienceLevel.C_LEVEL

        # Check description for experience requirements
        if re.search(r'\b0-2\s*years?\b', text) or "entry level" in text:
            return ExperienceLevel.ENTRY_LEVEL
        elif re.search(r'\b2-4\s*years?\b', text):
            return ExperienceLevel.ASSOCIATE
        elif re.search(r'\b4-7\s*years?\b', text):
            return ExperienceLevel.MID_LEVEL
        elif re.search(r'\b7\+?\s*years?\b', text) or re.search(r'\b8\+?\s*years?\b', text):
            return ExperienceLevel.SENIOR

        return ExperienceLevel.UNKNOWN

    def _determine_workplace_type(self, location: str, description: str) -> WorkplaceType:
        """Determine workplace type from location and description."""
        text = f"{location} {description}".lower()

        if any(word in text for word in ["remote", "work from home", "telecommute", "distributed"]):
            if any(word in text for word in ["hybrid", "flexible", "optional remote"]):
                return WorkplaceType.HYBRID
            return WorkplaceType.REMOTE
        elif any(word in text for word in ["hybrid", "flexible work", "remote optional"]):
            return WorkplaceType.HYBRID
        elif any(word in text for word in ["on-site", "onsite", "office", "in-person"]):
            return WorkplaceType.ON_SITE
        else:
            return WorkplaceType.UNKNOWN

    async def _wait_for_page_load(self):
        """Wait for page to load completely."""
        try:
            # Wait for page load state
            self.wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for dynamic content
            await asyncio.sleep(2)

        except TimeoutException:
            self.logger.warning("Page load timeout")

    async def _wait_for_element(self, selector: str, timeout: int = 10):
        """Wait for element to be present."""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except TimeoutException:
            self.logger.warning(f"Element not found: {selector}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics."""
        return self.stats.copy()
