# 🌱 PlantPal AI Assistant

A smart, plant-only AI assistant for plant care, Q&A, and management. PlantPal helps you keep your plants healthy with personalized care recommendations, AI-powered diagnosis, and comprehensive plant management tools.

## ✨ Features

### 🌱 Plant Management
- **Plant Profiles**: Create detailed profiles for each plant with species, location, and care requirements
- **Care Tracking**: Log watering, fertilizing, pruning, and other care activities
- **Photo Storage**: Upload and store plant photos for diagnosis and history
- **Care Scheduling**: Set up automated care reminders and tasks

### 🤖 AI-Powered Assistance
- **Plant Diagnosis**: Upload photos for AI-powered plant health analysis
- **Care Recommendations**: Get personalized care advice based on your plants and environment
- **Q&A System**: Ask questions about plant care, troubleshooting, and best practices
- **Conversation History**: Maintain persistent conversation sessions for context-aware assistance

### 📊 Dashboard & Analytics
- **Plant Overview**: Visual dashboard showing all your plants and their care status
- **Care History**: Track care activities and plant health over time
- **Task Management**: View upcoming care tasks and maintenance schedules

### 🔐 User Management
- **Secure Authentication**: User registration and login with password hashing
- **Profile Management**: Store user preferences and location information
- **Session Management**: Persistent conversation sessions for better AI interactions

## 🏗️ Architecture

PlantPal is built using a modern microservices-ready architecture with FastAPI:

```
plantpal_app/
├── alembic/                 # Database migrations
├── forms/                   # Form validation schemas
├── models/                  # SQLAlchemy database models
├── plant_pal_bot/          # AI bot integration
├── repositories/           # Data access layer
├── routers/                # API route handlers
├── schemas/                # Pydantic models for API
├── services/               # Business logic layer
├── static/                 # CSS, images, and static assets
├── templates/              # HTML templates
├── utils/                  # Utility functions
├── database.py             # Database configuration
├── main.py                 # FastAPI application entry point
├── settings.py             # Application configuration
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd plantpal_app
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Database Configuration
   db_hostname=localhost
   db_port=5432
   db_password=your_password
   db_name=plantpal
   db_username=your_username
   
   # Security
   secret_key=your_secret_key_here
   algorithm=HS256
   access_token_expire_minutes=720
   
   # OpenAI Configuration
   open_ai_key=your_openai_api_key
   ```

5. **Set up the database**
   ```bash
   # Create database
   createdb plantpal
   
   # Run migrations
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - ReDoc Documentation: http://localhost:8000/redoc

## 📚 API Documentation

### Core Endpoints

#### Authentication
- `POST /register` - User registration
- `POST /login` - User authentication
- `POST /logout` - User logout

#### Plant Management
- `GET /plants` - List user's plants
- `POST /plants` - Create new plant
- `GET /plants/{plant_id}` - Get plant details
- `PUT /plants/{plant_id}` - Update plant
- `DELETE /plants/{plant_id}` - Delete plant

#### AI Assistant
- `POST /ai/chat` - Send message to AI assistant
- `POST /ai/diagnose` - Upload photo for plant diagnosis
- `GET /ai/history` - Get conversation history

#### Care Management
- `POST /care/log` - Log care activity
- `GET /care/tasks` - Get upcoming care tasks
- `POST /care/tasks` - Create care task

## 🛠️ Development

### Project Structure

The application follows a clean architecture pattern:

- **Models** (`models/`): SQLAlchemy ORM models for database entities
- **Schemas** (`schemas/`): Pydantic models for API request/response validation
- **Routers** (`routers/`): FastAPI route handlers organized by feature
- **Services** (`services/`): Business logic and external service integrations
- **Repositories** (`repositories/`): Data access layer for database operations
- **Templates** (`templates/`): Jinja2 HTML templates for web interface
- **Static** (`static/`): CSS, JavaScript, and image assets

### Database Schema

The application uses PostgreSQL with the following main tables:

- **users**: User accounts and profiles
- **plants**: Plant information and care details
- **plant_photos**: Plant images for diagnosis
- **care_logs**: Historical care activities
- **plant_care_tasks**: Scheduled care tasks
- **ai_logs**: AI interaction history
- **ai_responses**: AI response storage
- **conversation_sessions**: User conversation sessions

## 📄 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `db_hostname` | Database host | Required |
| `db_port` | Database port | Required |
| `db_password` | Database password | Required |
| `db_name` | Database name | Required |
| `db_username` | Database username | Required |
| `secret_key` | JWT secret key | Required |
| `algorithm` | JWT algorithm | HS256 |
| `access_token_expire_minutes` | Token expiration | 720 |
| `open_ai_key` | OpenAI API key | Required |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Add type hints to all functions
- Include tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the API docs at `/docs`
- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions for help and ideas

##  Acknowledgments

- FastAPI for the excellent web framework
- SQLAlchemy for robust database ORM
- OpenAI for AI capabilities
- Alembic for database migrations
- The plant care community for inspiration and feedback

---

**Made with ❤️ for plant lovers everywhere**
