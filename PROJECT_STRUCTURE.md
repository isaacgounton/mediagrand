# Project Structure

This document describes the reorganized project structure for MediaGrand.

## Directory Structure

```
mediagrand/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (local)
├── .env.example                   # Example environment file
├── README.md                      # Main project documentation
├── LICENSE                        # License file
├── CLAUDE.md                      # Claude AI documentation
│
├── config/                        # Configuration files
│   ├── config.py                  # Main configuration
│   ├── version.py                 # Version information
│   ├── build_number.txt           # Build number
│   └── description.txt            # Project description
│
├── docker/                        # Docker-related files
│   ├── Dockerfile                 # Docker image definition
│   ├── docker-compose.yml         # Development docker-compose
│   ├── docker-compose.prod.yml    # Production docker-compose
│   ├── .dockerignore              # Docker ignore file
│   └── docker-compose.md          # Docker documentation
│
├── scripts/                       # Shell and utility scripts
│   ├── dev.sh                     # Development setup
│   ├── local.sh                   # Local environment setup
│   ├── generate_vector.sh         # Vector generation
│   ├── push-docker.sh             # Docker push script
│   ├── run_services.sh            # Service runner
│   ├── install_requirements.sh    # Requirements installer
│   ├── setup_youtube_auth.sh      # YouTube auth setup
│   ├── check_environment.py       # Environment checker
│   ├── check_playwright.py        # Playwright checker
│   ├── create_placeholders.py     # Placeholder creator
│   └── validate_startup.py        # Startup validator
│
├── utils/                         # Utility modules
│   ├── app_utils.py               # Application utilities
│   ├── bootstrap_admin.py         # Admin bootstrap
│   ├── generate_docs.py           # Documentation generator
│   └── start_worker.py            # Worker starter
│
├── routes/                        # Flask route definitions
│   ├── v1/                        # API v1 routes
│   └── ...                        # Other route files
│
├── services/                      # Business logic services
│   ├── v1/                        # API v1 services
│   └── ...                        # Other service files
│
├── models/                        # Data models
│   └── api_keys.py                # API key models
│
├── templates/                     # HTML templates
│
├── fonts/                         # Font files
│
└── docs/                          # Documentation
    └── ...                        # Documentation files
```

## Import Changes

After the reorganization, import statements have been updated:

- `from config import ...` → `from config.config import ...`
- `from app_utils import ...` → `from utils.app_utils import ...`
- `from version import ...` → `from config.version import ...`

## Docker Usage

To run with Docker:

```bash
# Development
cd docker
docker-compose up

# Production
cd docker
docker-compose -f docker-compose.prod.yml up
```

## Benefits of New Structure

1. **Better Organization**: Related files are grouped together
2. **Easier Navigation**: Clear separation of concerns
3. **Scalability**: Structure supports project growth
4. **Maintainability**: Easier to locate and modify files
5. **Professional**: Follows industry best practices