# FAANG Job Scraper PoC

A modular, dynamic job scraping system to automatically collect the newest job listings from FAANG companies (Meta, Amazon, Apple, Netflix, Google) with a plug-and-play architecture for easy expansion.

## 🎯 Project Overview

This proof-of-concept system demonstrates automated job data collection from major tech companies with a focus on modularity and scalability. The system is designed to be easily extensible for adding new companies while maintaining clean separation of concerns.

### Key Features
- **Modular Architecture**: Plug-and-play scrapers for easy company addition
- **Dynamic Data Collection**: Automated scraping with configurable schedules
- **FastAPI Integration**: RESTful API to serve the 10 newest job postings
- **Database-Ready**: JSON storage with easy migration path to databases
- **Extensible Design**: Add new companies without code changes to core system

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Scraper       │    │   Data Storage  │
│   Web Server    │◄───┤   Orchestrator  │◄───┤   Manager       │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         ▼              ┌─────────────────┐    ┌─────────────────┐
┌─────────────────┐     │  Company        │    │   jobs.json     │
│   API Clients   │     │  Scrapers       │    │   (Future: DB)  │
│   (Frontend)    │     │  - Meta         │    │                 │
└─────────────────┘     │  - Amazon       │    └─────────────────┘
                        │  - Apple        │
                        │  - Netflix      │
                        │  - Google       │
                        └─────────────────┘
```

## 📁 Project Structure

```
faang-job-scraper/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── main.py                     # FastAPI application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py            # Application configuration
│   └── company_configs.json   # Company-specific scraping configs
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py        # Abstract base scraper class
│   ├── scraper_factory.py     # Factory for creating scrapers
│   ├── companies/
│   │   ├── __init__.py
│   │   ├── meta_scraper.py
│   │   ├── amazon_scraper.py
│   │   ├── apple_scraper.py
│   │   ├── netflix_scraper.py
│   │   └── google_scraper.py
│   └── utils/
│       ├── __init__.py
│       ├── web_driver.py      # Selenium WebDriver utilities
│       └── rate_limiter.py    # Rate limiting utilities
├── data/
│   ├── __init__.py
│   ├── storage_manager.py     # Data storage abstraction
│   └── models.py             # Pydantic data models
├── api/
│   ├── __init__.py
│   ├── routes.py             # FastAPI routes
│   └── schemas.py            # API response schemas
├── orchestrator/
│   ├── __init__.py
│   ├── job_orchestrator.py   # Main scraping coordinator
│   └── scheduler.py          # Task scheduling
├── tests/
│   ├── __init__.py
│   ├── test_scrapers.py
│   ├── test_api.py
│   └── fixtures/
└── logs/
```

## 🚀 Implementation Plan

### Phase 1: Core Infrastructure (Week 1)
1. **Project Setup**
   - Initialize Python project with virtual environment
   - Set up project structure and dependencies
   - Configure logging and environment variables

2. **Base Architecture**
   - Create abstract `BaseScraper` class
   - Implement `ScraperFactory` for dynamic scraper loading
   - Design data models using Pydantic
   - Create storage abstraction layer

3. **Configuration System**
   - JSON-based company configuration
   - Environment-based settings management
   - Rate limiting and retry configurations

### Phase 2: Scraper Implementation (Week 2)
1. **Individual Company Scrapers**
   - Meta/Facebook careers page scraper
   - Amazon jobs scraper
   - Apple careers scraper
   - Netflix jobs scraper
   - Google careers scraper

2. **Scraping Utilities**
   - WebDriver management (Selenium/Playwright)
   - Rate limiting implementation
   - Error handling and retry logic
   - Data validation and cleaning

### Phase 3: Data Management (Week 3)
1. **Storage System**
   - JSON file storage implementation
   - Data deduplication logic
   - Timestamp-based sorting
   - Database interface preparation

2. **Job Orchestrator**
   - Scraping coordination and scheduling
   - Parallel scraping with rate limiting
   - Error recovery and logging
   - Data aggregation and filtering

### Phase 4: API Layer (Week 4)
1. **FastAPI Implementation**
   - RESTful endpoints for job data
   - Response pagination and filtering
   - Error handling and status codes
   - API documentation with OpenAPI/Swagger

2. **Testing and Validation**
   - Unit tests for scrapers
   - Integration tests for API
   - End-to-end testing
   - Performance optimization

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.9+**: Main programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and settings management
- **Selenium/Playwright**: Web scraping and browser automation

### Data & Storage
- **JSON**: Initial data storage format
- **SQLAlchemy**: Database ORM (future migration)
- **Pandas**: Data manipulation and analysis

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **pre-commit**: Git hooks for code quality

## 📋 Key Components

### 1. BaseScraper Abstract Class
```python
# Example structure
class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.company_name = config['company_name']
    
    @abstractmethod
    def scrape_jobs(self) -> List[Job]:
        pass
    
    @abstractmethod
    def parse_job_details(self, element) -> Job:
        pass
```

### 2. Data Models
```python
# Example Job model
class Job(BaseModel):
    id: str
    title: str
    company: str
    location: str
    posted_date: datetime
    description: str
    url: str
    scraped_at: datetime
```

### 3. API Endpoints
- `GET /api/v1/jobs/latest` - Returns 10 newest jobs across all companies
- `GET /api/v1/jobs/company/{company_name}` - Jobs from specific company
- `GET /api/v1/jobs/search?q={query}` - Search jobs by keywords
- `GET /api/v1/companies` - List all configured companies
- `GET /api/v1/health` - System health check

## 🔧 Configuration

### Company Configuration (JSON)
```json
{
  "companies": {
    "meta": {
      "name": "Meta",
      "careers_url": "https://careers.meta.com/jobs/",
      "scraper_class": "MetaScraper",
      "rate_limit": 1,
      "selectors": {
        "job_listing": "div[data-testid='job-listing']",
        "title": "h3[data-testid='job-title']",
        "location": "span[data-testid='job-location']"
      }
    }
  }
}
```

### Environment Variables
```
# Scraping Settings
SCRAPE_INTERVAL_MINUTES=60
MAX_CONCURRENT_SCRAPERS=3
REQUEST_TIMEOUT_SECONDS=30

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Storage Settings
DATA_STORAGE_PATH=./data/jobs.json
LOG_LEVEL=INFO
```

## 🚦 Getting Started

### Prerequisites
- Python 3.9+
- Chrome/Chromium browser (for Selenium)
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd faang-job-scraper

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configurations

# Run the application
python main.py
```

### Usage
```bash
# Start the FastAPI server
uvicorn main:app --reload

# Trigger manual scraping
python -m orchestrator.job_orchestrator

# Run tests
pytest tests/

# Access API documentation
# Open http://localhost:8000/docs in your browser
```

## 🔮 Future Enhancements

### Database Integration
- PostgreSQL/MongoDB integration
- Data migration utilities
- Advanced querying capabilities
- Historical data analysis

### Advanced Features
- Machine learning for job categorization
- Real-time notifications for new jobs
- Job matching algorithms
- Duplicate detection improvements

### Monitoring & Operations
- Prometheus metrics
- Grafana dashboards
- Error alerting system
- Performance monitoring

### Scaling Considerations
- Docker containerization
- Kubernetes deployment
- Horizontal scraper scaling
- Caching layer (Redis)

## 🤝 Adding New Companies

1. **Create Company Scraper**
   ```python
   # scrapers/companies/new_company_scraper.py
   class NewCompanyScraper(BaseScraper):
       def scrape_jobs(self) -> List[Job]:
           # Implementation specific to new company
           pass
   ```

2. **Add Configuration**
   ```json
   // config/company_configs.json
   "new_company": {
     "name": "New Company",
     "careers_url": "https://careers.newcompany.com/jobs/",
     "scraper_class": "NewCompanyScraper"
   }
   ```

3. **Register in Factory**
   ```python
   # scrapers/scraper_factory.py - automatically loads from config
   ```

## 📊 Expected Deliverables

1. **Functional PoC System**
   - Working scrapers for all 5 FAANG companies
   - FastAPI server with documented endpoints
   - JSON data storage with 10 latest jobs endpoint

2. **Documentation**
   - Complete README with setup instructions
   - API documentation (auto-generated)
   - Code documentation and comments

3. **Testing Suite**
   - Unit tests for all scrapers
   - API integration tests
   - Mock data for testing

4. **Deployment Ready**
   - Docker configuration
   - Environment-based configuration
   - Logging and error handling

## 📈 Success Metrics

- **Functionality**: All 5 company scrapers working correctly
- **Performance**: API responds within 200ms for latest jobs
- **Reliability**: 95% uptime with proper error handling
- **Maintainability**: New company can be added in <30 minutes
- **Data Quality**: <5% duplicate or invalid job postings

## 🤔 Technical Challenges & Solutions

### Challenge 1: Anti-Bot Detection
**Problem**: Career sites may block automated scraping
**Solution**: 
- Rotate user agents and headers
- Implement random delays
- Use residential proxies if needed
- Respect robots.txt

### Challenge 2: Dynamic Content Loading
**Problem**: Jobs loaded via JavaScript
**Solution**:
- Use Selenium/Playwright for dynamic content
- Wait for elements to load
- Handle pagination and infinite scroll

### Challenge 3: Data Inconsistency
**Problem**: Different sites have different data formats
**Solution**:
- Standardized data models
- Flexible parsing with fallbacks
- Data validation and cleaning

### Challenge 4: Rate Limiting
**Problem**: Avoiding overwhelming target servers
**Solution**:
- Configurable rate limiting per company
- Exponential backoff for failures
- Parallel scraping with limits

---

*This PoC demonstrates a scalable, maintainable approach to automated job data collection that can serve as a foundation for a production-ready system.*