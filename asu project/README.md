# 🎓 ASU Project - AI-Powered Educational Platform

A comprehensive Flask-based web application that provides AI-powered educational tools including voice assistant, document processing, YouTube suggestions, flashcard generation, and MCQ creation.

## ✨ Features

### 🤖 AI Voice Assistant
- **Natural Speech Recognition** - Listen to user voice input
- **Text-to-Speech** - Respond with natural female voice (ChatGPT-style)
- **Multi-language Support** - English, Tamil, Hindi, Telugu, Kannada, Malayalam
- **Real-time Processing** - Instant voice responses
- **Smart Waiting** - Waits for user to finish speaking

### 💬 AI Chat
- **Gemini AI Integration** - Powered by Google's Gemini API
- **Context-aware Responses** - Maintains conversation history
- **File Upload Support** - PDF, DOCX, TXT, images
- **Streaming Responses** - Real-time message delivery
- **Session Management** - Persistent chat sessions

### 📚 Educational Tools
- **Flashcard Generator** - AI-generated study cards
- **MCQ Generator** - Multiple choice questions with answers
- **YouTube Suggestions** - AI-curated educational videos
- **Document Processing** - Extract and analyze uploaded files

### 🎨 Modern UI
- **Dark Theme** - Beautiful black theme with purple accents
- **Responsive Design** - Works on desktop and mobile
- **Glass Morphism** - Modern visual effects
- **Smooth Animations** - Engaging user experience

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip (Python package manager)
- Gemini API key

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/asu-project.git
   cd asu-project
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

6. **Access the application:**
   Open your browser and go to `http://localhost:5000`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and run
docker-compose up --build

# Access at http://localhost:5000
```

### Using Docker directly
```bash
# Build image
docker build -t asu-project .

# Run container
docker run -p 5000:5000 asu-project
```

## 📁 Project Structure

```
asu-project/
├── main.py                 # Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── DOCKER_README.md      # Docker instructions
├── templates/            # HTML templates
│   ├── index.html        # Main chat interface
│   ├── voice_assistant.html  # Voice assistant page
│   ├── welcome.html      # Dashboard
│   ├── flashcards.html   # Flashcard generator
│   ├── mcq_generator.html # MCQ generator
│   └── youtube_suggestions.html # YouTube suggestions
├── static/               # Static files
│   ├── style.css         # Main styles
│   ├── voice_assistant.css # Voice assistant styles
│   └── voice_assistant.js # Voice assistant logic
└── uploads/              # File uploads directory
```

## 🛠️ Technologies Used

### Backend
- **Flask** - Web framework
- **Google Generative AI** - AI responses and content generation
- **gTTS** - Text-to-speech for regional languages
- **PyPDF2** - PDF processing
- **python-docx** - DOCX processing
- **Werkzeug** - WSGI utilities

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling with animations
- **JavaScript** - Interactive functionality
- **Web Speech API** - Voice recognition and synthesis
- **Font Awesome** - Icons
- **Google Fonts** - Typography

### Deployment
- **Docker** - Containerization
- **Gunicorn** - Production WSGI server
- **Nginx** - Reverse proxy (optional)

## 🎯 API Endpoints

### Authentication
- `POST /login` - User login
- `POST /register` - User registration
- `GET /logout` - User logout

### Chat & AI
- `POST /api/chat` - Send chat message
- `POST /api/voice-chat` - Voice chat processing
- `POST /api/gtts-speak` - Text-to-speech generation

### Educational Tools
- `POST /api/generate-flashcards` - Generate flashcards
- `POST /api/generate-mcq` - Generate MCQs
- `POST /api/youtube-suggestions` - Get YouTube suggestions

### File Processing
- `POST /api/upload` - File upload
- `GET /api/sessions` - Get chat sessions

## 🔧 Configuration

### Environment Variables
```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here

# Optional
FLASK_ENV=development
PORT=5000
```

### Voice Assistant Settings
- **Speech Recognition**: Web Speech API
- **Text-to-Speech**: gTTS + Browser TTS
- **Languages**: 6 languages supported
- **Voice**: ChatGPT-style female voice

## 🚀 Deployment

### Production Deployment
1. **Set up environment variables**
2. **Use Gunicorn** for production server
3. **Set up reverse proxy** (Nginx)
4. **Configure SSL** for HTTPS
5. **Set up monitoring** and logging

### Cloud Deployment
- **AWS** - EC2, ECS, or Lambda
- **Google Cloud** - App Engine or Compute Engine
- **Azure** - App Service or Container Instances
- **Heroku** - Platform as a Service

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google** - For Gemini AI API
- **Flask** - For the web framework
- **Web Speech API** - For voice recognition
- **Font Awesome** - For icons
- **Google Fonts** - For typography

## 📞 Support

If you have any questions or need help, please:
- Open an issue on GitHub
- Contact the development team
- Check the documentation

## 🔮 Future Enhancements

- [ ] User authentication with OAuth
- [ ] Real-time collaboration
- [ ] Mobile app development
- [ ] Advanced AI features
- [ ] Multi-tenant support
- [ ] Analytics dashboard
- [ ] API rate limiting
- [ ] Caching layer

---

**Made with ❤️ for education and learning**