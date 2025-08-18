# Alfred Bot Monorepo

This is a monorepo setup for the Alfred Bot project, containing both the backend API and the frontend CMS.

## Project Structure

```
alfred-bot/
├── backend/                 # Python FastAPI application
│   ├── data/                # Data files (intents, audio, etc.)
│   ├── src/                 # Python source code
│   ├── static/              # Built frontend files
│   ├── main.py              # Application entry point
│   └── ...                  # Other backend files
├── frontend/                # React CMS application
│   ├── src/                 # React source code
│   ├── package.json         # Frontend dependencies
│   └── ...                  # Other frontend files
└── ...                      # Other root files
```

## Documentation

For detailed information about setting up and using the application, please refer to:

- [Usage Guide](./docs/usage.md) - Installation and setup instructions
- [API Documentation](./docs/api.md) - Detailed API endpoints and usage

## Features

### Backend

- FastAPI REST API
- Intent management with version history
- Audio file management
- Session management with Redis
- Vector search with ChromaDB
- Multi-language support (English, Malay)

### Frontend (CMS)

- Intent listing and editing
- Multi-language support
- Response management
- Pattern management
- Priority and category settings
- TailwindCSS styling
- Zustand state management

## CMS Access

Once both backend and frontend are running:

- Development: http://localhost:3000
- Production: http://localhost:8000/static/index.html
