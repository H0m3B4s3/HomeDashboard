# HomeBase

A comprehensive home management application built with FastAPI and modern web technologies. HomeBase helps you organize and manage your home-related tasks, events, and information in one centralized location.

## Features

- **Calendar Management**: Sync with external calendars and manage events
- **Task Organization**: Create and track home-related tasks
- **Category Management**: Organize items by categories
- **Modern Web Interface**: Responsive design that works on desktop and mobile
- **Real-time Updates**: Live synchronization of data across the application

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript
- **Calendar Integration**: CalDAV support
- **Authentication**: JWT-based authentication
- **Scheduling**: APScheduler for background tasks

## Project Structure

```
HomeBase/
├── app/                    # Main application code
│   ├── api/               # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   └── main.py           # FastAPI application entry point
├── frontend/              # Frontend assets
│   ├── static/           # CSS, JS, and other static files
│   └── templates/        # HTML templates
├── venv/                 # Python virtual environment
└── config.py            # Configuration settings
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd HomeBase
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python create_db.py
   ```

5. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## Configuration

The application uses a `config.py` file for configuration settings. You can modify this file to adjust:

- Database connection settings
- Calendar sync configurations
- Authentication settings
- Application preferences

## API Documentation

Once the application is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

### Adding New Features

1. Create new API endpoints in `app/api/`
2. Add corresponding models in `app/models/`
3. Implement business logic in `app/services/`
4. Update frontend templates and static files as needed

### Database Migrations

When making changes to database models:
1. Update the model definitions in `app/models/`
2. Run database creation script: `python create_db.py`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and commit them: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository or contact the development team. 