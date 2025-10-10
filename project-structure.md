# 📁 Project Structure

```
telegram-reminder-bot/
├── 📄 README.md                    # Main documentation
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Configuration template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 LICENSE                      # MIT License
├── 📄 Dockerfile                   # Container configuration
├── 📄 docker-compose.yml           # Local development setup
├── 📄 CHANGELOG.md                 # Version history
├── 📄 CONTRIBUTING.md              # Development guidelines
│
├── 📁 src/                         # Source code
│   ├── 📄 __init__.py
│   ├── 📄 main.py                  # Entry point
│   ├── 📄 config.py                # Configuration management
│   │
│   ├── 📁 bot/                     # Bot core
│   │   ├── 📄 __init__.py
│   │   ├── 📄 bot.py               # Bot initialization
│   │   └── 📄 states.py            # FSM states
│   │
│   ├── 📁 handlers/                # Message handlers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 start.py             # /start command
│   │   ├── 📄 reminders.py         # Reminder CRUD
│   │   ├── 📄 callbacks.py         # Button callbacks
│   │   └── 📄 stats.py             # Statistics
│   │
│   ├── 📁 database/                # Database operations
│   │   ├── 📄 __init__.py
│   │   ├── 📄 models.py            # Data models
│   │   ├── 📄 operations.py        # CRUD operations
│   │   └── 📄 migrations.py        # Database migrations
│   │
│   ├── 📁 services/                # Business logic
│   │   ├── 📄 __init__.py
│   │   ├── 📄 time_parser.py       # Enhanced time parsing
│   │   ├── 📄 reminder_service.py  # Reminder logic
│   │   └── 📄 scheduler_service.py # Job scheduling
│   │
│   └── 📁 utils/                   # Utilities
│       ├── 📄 __init__.py
│       ├── 📄 logging.py           # Logging configuration
│       ├── 📄 validators.py        # Input validation
│       └── 📄 formatters.py        # Text formatting
│
├── 📁 tests/                       # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 conftest.py              # Pytest configuration
│   ├── 📁 unit/                    # Unit tests
│   ├── 📁 integration/             # Integration tests
│   └── 📁 fixtures/                # Test data
│
├── 📁 docs/                        # Documentation
│   ├── 📄 deployment.md            # Deployment guide
│   ├── 📄 architecture.md          # Architecture overview
│   └── 📄 api.md                   # API documentation
│
├── 📁 scripts/                     # Utility scripts
│   ├── 📄 deploy.sh                # Deployment script
│   ├── 📄 backup.sh                # Database backup
│   └── 📄 health_check.py          # Health monitoring
│
└── 📁 .github/                     # GitHub configuration
    ├── 📁 workflows/               # CI/CD pipelines
    │   ├── 📄 ci.yml               # Continuous Integration
    │   ├── 📄 release.yml          # Release automation
    │   └── 📄 security.yml         # Security scanning
    ├── 📁 ISSUE_TEMPLATE/          # Issue templates
    └── 📄 PULL_REQUEST_TEMPLATE.md # PR template
```

## 🎯 Benefits of This Structure

### 🧩 **Modularity**
- Clear separation of concerns
- Easy to test individual components
- Scalable architecture

### 🔧 **Maintainability**  
- Well-organized codebase
- Easy to locate and fix bugs
- Simple to add new features

### 🚀 **Production Ready**
- Docker support
- CI/CD pipelines
- Comprehensive testing
- Documentation

### 👥 **Team Collaboration**
- Clear contribution guidelines
- Standardized issue templates
- Automated code quality checks