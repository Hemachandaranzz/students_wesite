from flask import Flask, render_template, request, jsonify, Response, stream_with_context, session, redirect, url_for, send_file
import google.generativeai as genai
import os
import json
import uuid
import base64
import io
import re
import PyPDF2
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not available. DOCX file processing will be disabled.")

from werkzeug.utils import secure_filename
import tempfile
from datetime import datetime
import threading
import time
import hashlib
import secrets

# Optional: Load env variables from .env during development
from dotenv import load_dotenv
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 16MB
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))

# File upload folder (optional)
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure Gemini API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please add it to your environment or .env file.")

else:
    genai.configure(api_key=api_key)
    print("Gemini API configured successfully!")

# Session memory for voice chat
session_memory = {}

# User authentication
USERS = {
    'Dhinesh': hashlib.sha256('dhineshsin<3'.encode()).hexdigest(),
    'Hemachandaran': hashlib.sha256('hemachan'.encode()).hexdigest(),
    'Dhaanush': hashlib.sha256('220301012'.encode()).hexdigest()
}

# In-memory storage for chat history (in production, use a database)
chat_sessions = {}
current_session_id = None

# Memory management configuration
MAX_CONTEXT_MESSAGES = 20  # Keep last 20 message pairs for context
CONTEXT_WINDOW_TOKENS = 8000  # Approximate token limit for context

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # For API routes, return JSON error instead of redirect
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def initialize_model():
    """Initialize the Nova AI model with professional ChatGPT-style behavior."""
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "max_output_tokens": 2048,
        "candidate_count": 1,
    }
    
    # Lumora AI system instruction with perfect ChatGPT/Gemini formatting
    system_instruction = """You are Lumora AI, designed to respond exactly like ChatGPT/Gemini with structured, polished, and concise answers.

CRITICAL FORMATTING RULES - FOLLOW EXACTLY:

1. **NEVER USE ESCAPE CHARACTERS**: Do not use \\n, \\t, or any escape characters in your response. Use actual line breaks instead.

2. **HEADERS**: Format section headers like this:
   **I. Section Title**
   
   NOT like this: **I. Section Title** \\n\\n

3. **BULLET POINTS**: Use • symbol for all bullet points:
   • **Point Title:** Description here.
   
   NOT: * **Point Title:** Description here.

4. **PROPER STRUCTURE**: Format your response exactly like this example:
   **I. What is a Tree?**
   
   • **Biological Definition:** A tree is a perennial plant with a single, self-supporting trunk or stem, typically reaching a considerable height.
   
   • **Ecological Importance:** Trees play a vital role in ecosystems, providing habitat for diverse wildlife.
   
   **II. Tree Anatomy**
   
   • **Trunk:** The main supporting structure of the tree.
   
   • **Branches:** Extensions of the trunk, supporting leaves.

5. **ABSOLUTELY FORBIDDEN**:
   - \\n characters anywhere in your response
   - \\t characters
   - Any escape sequences
   - Messy formatting with backslashes

6. **REQUIRED**:
   - Clean, readable formatting
   - Proper bullet points with •
   - Bold headings for sections
   - Professional ChatGPT/Gemini style
   - Use actual line breaks, not escape characters

3. **BEHAVIOR GUIDELINES**
   - Give context-aware answers (always connect with previous queries when possible)
   - For explanations → start with a quick summary, then expand into details
   - For step-by-step guides → number each step clearly
   - For comparisons → use structured tables or bullet points
   - Always end answers cleanly (never cut mid-sentence)

4. **RESPONSE STRUCTURE**
   - Maintain professional, structured style across all response types:
     - Text explanations
     - Code examples
     - MCQs and quizzes
     - Essays and summaries
     - Creative writing
     - Data analysis

5. **SPECIAL FEATURES**
   - Remember file contents (PDF, DOCX, PPT, TXT, images) for follow-up questions
   - Provide comprehensive but well-organized answers
   - Never break character or ignore formatting rules

GOAL: Every response should feel indistinguishable from ChatGPT/Gemini, with rich formatting, adaptive style, and polished presentation."""
    
    return genai.GenerativeModel(
        "gemini-1.5-flash", 
        generation_config=generation_config,
        system_instruction=system_instruction
    )

def build_conversation_context(messages, max_messages=MAX_CONTEXT_MESSAGES):
    """Build conversation context from message history for continuous memory."""
    if not messages:
        return []
    
    # Get the last max_messages messages for context
    recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
    
    context_parts = []
    
    # Add conversation history with role indicators
    for msg in recent_messages:
        role = "Human" if msg['role'] == 'user' else "Assistant"
        content = msg['content']
        
        # Include document content if present
        if msg.get('document_content'):
            content = f"[Document: {msg.get('filename', 'uploaded file')}]\n{msg['document_content']}\n\nUser question: {content}"
        
        context_parts.append(f"{role}: {content}")
    
    # Join with proper formatting for context
    full_context = "\n\n".join(context_parts)
    
    return full_context

def estimate_token_count(text):
    """Rough estimation of token count (approximate: 1 token ≈ 4 characters)."""
    return len(text) // 4

def trim_context_if_needed(context, max_tokens=CONTEXT_WINDOW_TOKENS):
    """Trim context if it exceeds token limits while preserving recent messages."""
    if estimate_token_count(context) <= max_tokens:
        return context
    
    # Split context into messages and keep the most recent ones
    messages = context.split("\n\nHuman:")
    trimmed_messages = []
    current_tokens = 0
    
    # Start from the most recent and work backwards
    for i in range(len(messages) - 1, -1, -1):
        msg = messages[i]
        if i > 0:  # Add back the "Human:" prefix for non-first messages
            msg = "Human:" + msg
        
        msg_tokens = estimate_token_count(msg)
        if current_tokens + msg_tokens > max_tokens and trimmed_messages:
            break
        
        trimmed_messages.insert(0, msg)
        current_tokens += msg_tokens
    
    return "\n\n".join(trimmed_messages)

def extract_text_from_pdf(file_path):
    """Extract text from PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from DOCX file."""
    if not DOCX_AVAILABLE:
        return "Error: DOCX processing not available. Please install python-docx package."
    
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_txt(file_path):
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading TXT: {str(e)}"

def process_uploaded_file(file):
    """Process uploaded file and extract text content."""
    filename = secure_filename(file.filename)
    file_ext = filename.split('.')[-1].lower()
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_ext}') as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        if file_ext == 'pdf':
            content = extract_text_from_pdf(temp_path)
        elif file_ext == 'docx':
            if DOCX_AVAILABLE:
                content = extract_text_from_docx(temp_path)
            else:
                content = "Error: DOCX processing not available. Please install python-docx package."
        elif file_ext == 'txt':
            content = extract_text_from_txt(temp_path)
        else:
            content = f"Unsupported file type: {file_ext}"
        
        return content
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login page and authentication."""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    # Check credentials
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if username in USERS and USERS[username] == password_hash:
        session['user'] = username
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid username or password'})

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@require_auth
def index():
    """Redirect to student details if not completed, otherwise to welcome page."""
    if 'student_details' not in session:
        return redirect(url_for('student_details'))
    return redirect(url_for('welcome'))

@app.route('/student-details')
@require_auth
def student_details():
    """Serve the student details page."""
    return render_template('student_details.html')

@app.route('/welcome')
@require_auth
def welcome():
    """Serve the welcome dashboard page."""
    return render_template('welcome.html')

@app.route('/chatbot')
@require_auth
def chatbot():
    """Serve the main chatbot page."""
    return render_template('index.html')

@app.route('/flashcards')
@require_auth
def flashcards():
    """Serve the flashcards page."""
    return render_template('flashcards.html')

@app.route('/mcq-generator')
@require_auth
def mcq_generator():
    """Serve the MCQ generator page."""
    return render_template('mcq_generator.html')

@app.route('/youtube-suggestions')
@require_auth
def youtube_suggestions():
    """Serve the YouTube suggestions page."""
    return render_template('youtube_suggestions.html')

@app.route('/voice-assistant')
@require_auth
def voice_assistant():
    """Serve the voice assistant page."""
    return render_template('voice_assistant.html')

@app.route('/api/student-details', methods=['POST'])
@require_auth
def submit_student_details():
    """Handle student details submission."""
    try:
        data = request.get_json()
        student_name = data.get('student_name', '').strip()
        department = data.get('department', '').strip()
        year = data.get('year', '').strip()
        age = data.get('age', '').strip()
        
        # Validate required fields
        if not all([student_name, department, year, age]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Store in session
        session['student_details'] = {
            'student_name': student_name,
            'department': department,
            'year': year,
            'age': age
        }
        
        return jsonify({'success': True, 'message': 'Student details saved successfully'})
        
    except Exception as e:
        print(f"Error in student details submission: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to save student details'}), 500

@app.route('/api/student-info', methods=['GET'])
@require_auth
def get_student_info():
    """Get student information from session."""
    try:
        student_details = session.get('student_details', {})
        student_name = student_details.get('student_name', '')
        
        return jsonify({
            'success': True,
            'student_name': student_name,
            'department': student_details.get('department', ''),
            'year': student_details.get('year', ''),
            'age': student_details.get('age', '')
        })
    except Exception as e:
        print(f"Error getting student info: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to get student info'}), 500

@app.route('/api/generate-flashcards', methods=['POST'])
@require_auth
def generate_flashcards():
    """Generate flash cards from content using Gemini API."""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'message': 'No content provided'})
        
        # Check if API key is configured
        if not api_key:
            return jsonify({'success': False, 'message': 'AI service not configured. Please set GEMINI_API_KEY environment variable.'}), 500
        
        # Initialize Gemini model
        model = initialize_model()
        
        # Create prompt for flash card generation
        prompt = f"""Create flash cards from the following content. Generate 5-10 flash cards with clear front (question/keyword) and back (answer/explanation) pairs.

Content:
{content}

Format the response as JSON with this structure:
{{
    "flashcards": [
        {{
            "front": "Question or keyword",
            "back": "Answer or explanation"
        }}
    ]
}}

Make sure the front side contains concise questions or key terms, and the back side contains detailed explanations or answers. Focus on the most important concepts."""
        
        # Generate response
        response = model.generate_content(prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            response_text = response.candidates[0].content.parts[0].text
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    flashcards_data = json.loads(json_match.group())
                    return jsonify({
                        'success': True,
                        'flashcards': flashcards_data.get('flashcards', [])
                    })
                else:
                    # Fallback: parse manually if JSON extraction fails
                    flashcards = parse_flashcards_manually(response_text)
                    return jsonify({
                        'success': True,
                        'flashcards': flashcards
                    })
            except json.JSONDecodeError:
                # Fallback parsing
                flashcards = parse_flashcards_manually(response_text)
                return jsonify({
                    'success': True,
                    'flashcards': flashcards
                })
        else:
            return jsonify({'success': False, 'message': 'Failed to generate flash cards'})
            
    except Exception as e:
        print(f"Error generating flash cards: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to generate flash cards'}), 500

def parse_flashcards_manually(text):
    """Parse flash cards from text when JSON parsing fails."""
    flashcards = []
    lines = text.split('\n')
    
    current_card = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for patterns like "Front:", "Back:", "Q:", "A:", etc.
        if any(keyword in line.lower() for keyword in ['front:', 'question:', 'q:']):
            if current_card:
                flashcards.append(current_card)
            current_card = {'front': line.split(':', 1)[1].strip(), 'back': ''}
        elif any(keyword in line.lower() for keyword in ['back:', 'answer:', 'a:']):
            if current_card:
                current_card['back'] = line.split(':', 1)[1].strip()
        elif current_card and not current_card.get('back'):
            # If we have a front but no back yet, this might be the back
            current_card['back'] = line
    
    # Add the last card if it exists
    if current_card and current_card.get('front') and current_card.get('back'):
        flashcards.append(current_card)
    
    # If no structured cards found, create simple pairs
    if not flashcards:
        # Split content into chunks and create simple Q&A pairs
        chunks = [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]
        for i in range(0, min(len(chunks), 8), 2):
            if i + 1 < len(chunks):
                flashcards.append({
                    'front': chunks[i][:100] + '...' if len(chunks[i]) > 100 else chunks[i],
                    'back': chunks[i + 1][:200] + '...' if len(chunks[i + 1]) > 200 else chunks[i + 1]
                })
    
@app.route('/api/generate-mcqs', methods=['POST'])
@require_auth
def generate_mcqs():
    """Generate MCQs from content using Gemini API."""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        count = data.get('count', 5)
        
        if not content:
            return jsonify({'success': False, 'message': 'No content provided'})
        
        if count < 1 or count > 20:
            return jsonify({'success': False, 'message': 'Count must be between 1 and 20'})
        
        # Initialize Gemini model
        model = initialize_model()
        
        # Create prompt for MCQ generation
        prompt = f"""Create {count} multiple choice questions from the following content. Each question should have 4 options (A, B, C, D) with only one correct answer.

Content:
{content}

Format the response as JSON with this structure:
{{
    "mcqs": [
        {{
            "question": "Question text here",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct": 0
        }}
    ]
}}

Important:
- Generate exactly {count} questions
- Each question must have exactly 4 options
- The "correct" field should be the index (0-3) of the correct option
- Make questions clear and relevant to the content
- Ensure options are plausible but only one is correct
- Focus on important concepts and key information"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            response_text = response.candidates[0].content.parts[0].text
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    mcqs_data = json.loads(json_match.group())
                    mcqs = mcqs_data.get('mcqs', [])
                    
                    # Validate MCQs
                    validated_mcqs = []
                    for mcq in mcqs:
                        if (isinstance(mcq, dict) and 
                            'question' in mcq and 
                            'options' in mcq and 
                            'correct' in mcq and
                            len(mcq['options']) == 4 and
                            0 <= mcq['correct'] <= 3):
                            validated_mcqs.append(mcq)
                    
                    if len(validated_mcqs) >= count:
                        return jsonify({
                            'success': True,
                            'mcqs': validated_mcqs[:count]
                        })
                    else:
                        # Fallback: generate simple MCQs
                        fallback_mcqs = generate_fallback_mcqs(content, count)
                        return jsonify({
                            'success': True,
                            'mcqs': fallback_mcqs
                        })
                else:
                    # Fallback parsing
                    fallback_mcqs = generate_fallback_mcqs(content, count)
                    return jsonify({
                        'success': True,
                        'mcqs': fallback_mcqs
                    })
            except json.JSONDecodeError:
                # Fallback parsing
                fallback_mcqs = generate_fallback_mcqs(content, count)
                return jsonify({
                    'success': True,
                    'mcqs': fallback_mcqs
                })
        else:
            return jsonify({'success': False, 'message': 'Failed to generate MCQs'})
            
    except Exception as e:
        print(f"Error generating MCQs: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to generate MCQs'}), 500

def generate_fallback_mcqs(content, count):
    """Generate simple MCQs when JSON parsing fails."""
    mcqs = []
    
    # Split content into sentences
    sentences = [s.strip() for s in content.split('.') if s.strip() and len(s.strip()) > 20]
    
    # Generate MCQs from sentences
    for i in range(min(count, len(sentences))):
        sentence = sentences[i]
        
        # Create a simple question
        question = f"What is mentioned about: {sentence[:50]}...?"
        
        # Create options
        options = [
            sentence[:100] + "..." if len(sentence) > 100 else sentence,
            "This is not mentioned in the content",
            "The information is unclear",
            "None of the above"
        ]
        
        mcqs.append({
            'question': question,
            'options': options,
            'correct': 0
        })
    
@app.route('/api/voice-chat', methods=['POST'])
@require_auth
def voice_chat():
    """Handle voice chat requests with natural conversation."""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        language = data.get('language', 'en')
        
        if not message:
            return jsonify({'success': False, 'message': 'No message provided'})
        
        # Initialize Gemini model
        model = initialize_model()
        
        # Create natural conversation prompt
        # Enhanced prompt for natural, human-like speech in regional languages
        language_names = {
            'en': 'English',
            'ta': 'Tamil (தமிழ்)',
            'hi': 'Hindi (हिन्दी)',
            'te': 'Telugu (తెలుగు)',
            'kn': 'Kannada (ಕನ್ನಡ)',
            'ml': 'Malayalam (മലയാളം)'
        }
        
        current_lang_name = language_names.get(language, 'English')
        
        # Build conversation context
        context = ""
        if session_id and session_id in session_memory:
            recent_conversations = session_memory[session_id][-3:]  # Last 3 exchanges
            if recent_conversations:
                context = "\n\nPrevious conversation context:\n"
                for conv in recent_conversations:
                    context += f"User: {conv['user']}\n"
                    context += f"Assistant: {conv['assistant']}\n"
                context += "\nCurrent user message: " + message
            else:
                context = f"\nUser message: {message}"
        else:
            context = f"\nUser message: {message}"

        prompt = f"""You are a helpful AI assistant having a natural voice conversation in {current_lang_name}. 
        
        CRITICAL INSTRUCTIONS FOR NATURAL SPEECH:
        - Respond in {current_lang_name} if the user is speaking in that language
        - Use natural, conversational speech patterns that sound human when spoken aloud
        - Use contractions and informal language (like "I'm", "you're", "don't", "can't")
        - Keep responses concise (2-3 sentences maximum) but informative
        - Avoid reading out special characters, formatting, symbols, or technical jargon
        - Use natural pauses and flow in your language
        - Be friendly, warm, and engaging like a real person
        - Use regional expressions and natural phrases when appropriate
        - Make it sound like you're talking to a friend, not reading a manual
        - If explaining something complex, break it down into simple, spoken language
        
        CONVERSATION FLOW:
        - ALWAYS maintain conversation context and flow
        - Reference previous topics when relevant (use "as we discussed", "like I mentioned", "building on what you said")
        - Connect new questions to earlier context naturally
        - Never treat questions as isolated - always consider the conversation history
        - Use pronouns and references to maintain continuity
        - If user asks follow-up questions, acknowledge the connection
        
        {context}
        
        Provide a natural, conversational response in {current_lang_name} that maintains conversation flow and sounds perfect when spoken aloud:"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            ai_response = response.candidates[0].content.parts[0].text.strip()
            
            # Store in session memory
            if session_id:
                if session_id not in session_memory:
                    session_memory[session_id] = []
                
                # Add to memory (keep last 10 exchanges)
                session_memory[session_id].append({
                    'user': message,
                    'assistant': ai_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Keep only last 10 exchanges
                if len(session_memory[session_id]) > 10:
                    session_memory[session_id] = session_memory[session_id][-10:]
            
            return jsonify({
                'success': True,
                'response': ai_response
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to generate response'})
            
    except Exception as e:
        print(f"Error in voice chat: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to process voice chat request'}), 500

@app.route('/api/gtts-speak', methods=['POST'])
@require_auth
def gtts_speak():
    """Generate speech using Google Text-to-Speech for regional languages."""
    try:
        from gtts import gTTS
        import io
        import tempfile
        import os
        
        data = request.get_json()
        text = data.get('text', '').strip()
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({'success': False, 'message': 'No text provided'}), 400
        
        # Enhanced text cleaning for better speech
        clean_text = text.replace('\n', ' ').replace('\r', ' ').strip()
        # Remove special characters that shouldn't be spoken
        clean_text = re.sub(r'[^\w\s.,!?;:()\-]', '', clean_text)
        # Remove extra spaces
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Language mapping for gTTS
        gtts_lang_map = {
            'en': 'en',
            'ta': 'ta',
            'hi': 'hi',
            'te': 'te',
            'kn': 'kn',
            'ml': 'ml'
        }
        
        gtts_lang = gtts_lang_map.get(language, 'en')
        tts = gTTS(text=clean_text, lang=gtts_lang, slow=False)
        
        # Generate audio in memory
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Return audio as response
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
        
    except Exception as e:
        print(f"Error in GTTS: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to generate speech'}), 500

@app.route('/api/youtube-suggestions', methods=['POST'])
@require_auth
def generate_youtube_suggestions():
    """Generate YouTube video suggestions using Gemini API."""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        language = data.get('language', 'english')
        
        if not topic:
            return jsonify({'success': False, 'message': 'No topic provided'})
        
        # Initialize Gemini model
        model = initialize_model()
        
        # Create prompt for YouTube suggestions
        language_instruction = "in Tamil language" if language == 'tamil' else "in English language"
        
        if language == 'tamil':
            prompt = f"""Find 5-8 high-quality educational YouTube videos specifically about "{topic}" in Tamil language. 

IMPORTANT: The videos MUST be directly related to "{topic}" and MUST be in Tamil language - not general programming, not random songs, not unrelated content.

For Tamil videos, focus on these popular Tamil educational channels:
- Tamil Tech Tutorials
- Tamil Programming
- Tamil Computer Education
- Tamil Software Training
- Tamil Web Development
- Tamil Coding
- Tamil IT Education
- Tamil Digital Learning

For each video, provide:
- Title (in Tamil or English, must be about {topic})
- Channel name (Tamil educational/tech channels)
- Brief description (2-3 sentences about {topic} content in Tamil)
- Estimated duration (e.g., "15:30", "1:25:00")
- View count (e.g., "1.2M views", "500K views")
- Publication date (e.g., "2 months ago", "1 year ago")
- YouTube URL (use format: https://www.youtube.com/watch?v=VIDEO_ID)

Format the response as JSON:
{{
    "videos": [
        {{
            "title": "{topic} - முழுமையான டுடோரியல் (Complete Tutorial)",
            "channel": "Tamil Tech Tutorials",
            "description": "இந்த வீடியோ {topic} பற்றிய அடிப்படைகளை விளக்குகிறது. நடைமுறை உதாரணங்களுடன் படிப்படியாக விளக்கப்பட்டுள்ளது.",
            "duration": "45:30",
            "views": "500K views",
            "published": "3 months ago",
            "url": "https://www.youtube.com/watch?v=VIDEO_ID",
            "thumbnail": "https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg"
        }}
    ]
}}

CRITICAL REQUIREMENTS FOR TAMIL VIDEOS:
- ALL videos must be specifically about "{topic}"
- Videos must be in Tamil language or have Tamil subtitles
- NO general programming videos unless they specifically teach {topic}
- NO music, entertainment, or unrelated content
- Focus on Tamil educational and tutorial content about {topic}
- Include popular Tamil educational channels
- Ensure videos are relevant to learning {topic} in Tamil
- Mix different difficulty levels (beginner to advanced) for {topic}
- Include both recent and classic Tamil videos about {topic}
- Make sure URLs are valid YouTube links"""
        else:
            prompt = f"""Find 5-8 high-quality educational YouTube videos specifically about "{topic}" in English language. 

IMPORTANT: Generate realistic, available videos with actual video IDs from popular educational channels.

For each video, provide:
- Title (compelling and descriptive, must be about {topic})
- Channel name (use these popular educational channels: freeCodeCamp.org, Traversy Media, Programming with Mosh, The Net Ninja, TechWorld with Nana, Academind, Code with Harry, Telusko, Apna College, CodeHelp, etc.)
- Brief description (2-3 sentences about {topic} content)
- Estimated duration (e.g., "15:30", "1:25:00")
- View count (realistic counts like "2.5M views", "1.8M views", "850K views")
- Publication date (e.g., "2 months ago", "1 year ago", "6 months ago")
- YouTube URL (use REAL video IDs from actual educational videos)

Format the response as JSON:
{{
    "videos": [
        {{
            "title": "Complete {topic} Tutorial for Beginners",
            "channel": "freeCodeCamp.org",
            "description": "This video covers the fundamentals of {topic} with practical examples and step-by-step explanations.",
            "duration": "45:30",
            "views": "2.5M views",
            "published": "3 months ago",
            "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
            "thumbnail": "https://img.youtube.com/vi/rfscVS0vtbw/maxresdefault.jpg"
        }}
    ]
}}

CRITICAL REQUIREMENTS:
- Use ONLY real, available video IDs from popular educational channels
- Generate realistic view counts (500K to 5M views)
- Use actual channel names from the list above
- Make titles and descriptions directly related to {topic}
- Ensure all video IDs are 11 characters long and alphanumeric
- Use recent publication dates (within the last 2 years)
- ALL videos must be specifically about "{topic}"
- NO general programming videos unless they specifically teach {topic}
- NO music, entertainment, or unrelated content
- Focus on educational and tutorial content about {topic}
- Include popular educational channels like freeCodeCamp, Traversy Media, Programming with Mosh, etc.
- Ensure videos are relevant to learning {topic}
- Mix different difficulty levels (beginner to advanced) for {topic}
- Include both recent and classic videos about {topic}
- Make sure URLs are valid YouTube links"""
        
        # Generate response
        response = model.generate_content(prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            response_text = response.candidates[0].content.parts[0].text
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    videos_data = json.loads(json_match.group())
                    videos = videos_data.get('videos', [])
                    
                    # Validate and clean videos
                    validated_videos = []
                    for video in videos:
                        if (isinstance(video, dict) and 
                            'title' in video and 
                            'url' in video and
                            'youtube.com' in video.get('url', '')):
                            
                            # Extract video ID for thumbnail
                            video_id = extract_video_id(video['url'])
                            if video_id:
                                video['thumbnail'] = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                            
                            validated_videos.append(video)
                    
                    if validated_videos:
                        return jsonify({
                            'success': True,
                            'videos': validated_videos[:8]  # Limit to 8 videos
                        })
                    else:
                        # Fallback: generate sample videos
                        fallback_videos = generate_fallback_videos(topic, language)
                        return jsonify({
                            'success': True,
                            'videos': fallback_videos
                        })
                else:
                    # Fallback parsing
                    fallback_videos = generate_fallback_videos(topic, language)
                    return jsonify({
                        'success': True,
                        'videos': fallback_videos
                    })
            except json.JSONDecodeError:
                # Fallback parsing
                fallback_videos = generate_fallback_videos(topic, language)
                return jsonify({
                    'success': True,
                    'videos': fallback_videos
                })
        else:
            return jsonify({'success': False, 'message': 'Failed to generate video suggestions'})
            
    except Exception as e:
        print(f"Error generating YouTube suggestions: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to generate video suggestions'}), 500

def extract_video_id(url):
    """Extract YouTube video ID from URL."""
    import re
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def generate_fallback_videos(topic, language):
    """Generate fallback video suggestions when API fails."""
    videos = []
    
    # Real educational videos for fallback - these are popular, available videos
    sample_videos = [
        {
            "title": f"Complete {topic} Tutorial for Beginners",
            "channel": "freeCodeCamp.org",
            "description": f"A comprehensive tutorial covering the basics of {topic}. Perfect for beginners who want to learn step by step.",
            "duration": "45:30",
            "views": "2.5M views",
            "published": "3 months ago",
            "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
            "thumbnail": "https://img.youtube.com/vi/rfscVS0vtbw/maxresdefault.jpg"
        },
        {
            "title": f"Advanced {topic} Concepts Explained",
            "channel": "Traversy Media",
            "description": f"Deep dive into advanced concepts of {topic}. Suitable for intermediate to advanced learners.",
            "duration": "1:25:00",
            "views": "1.8M views",
            "published": "1 month ago",
            "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c",
            "thumbnail": "https://img.youtube.com/vi/hdI2bqOjy3c/maxresdefault.jpg"
        },
        {
            "title": f"{topic} Crash Course - Learn in 30 Minutes",
            "channel": "Programming with Mosh",
            "description": f"Fast-paced crash course on {topic}. Get up to speed quickly with essential concepts.",
            "duration": "30:15",
            "views": "3.2M views",
            "published": "2 weeks ago",
            "url": "https://www.youtube.com/watch?v=kqtD5dpn9C8",
            "thumbnail": "https://img.youtube.com/vi/kqtD5dpn9C8/maxresdefault.jpg"
        },
        {
            "title": f"Practical {topic} Projects You Can Build",
            "channel": "The Net Ninja",
            "description": f"Hands-on projects to practice {topic}. Build real-world applications and improve your skills.",
            "duration": "1:10:45",
            "views": "1.5M views",
            "published": "1 week ago",
            "url": "https://www.youtube.com/watch?v=Yg7l2JyHl_Q",
            "thumbnail": "https://img.youtube.com/vi/Yg7l2JyHl_Q/maxresdefault.jpg"
        },
        {
            "title": f"{topic} Interview Questions and Answers",
            "channel": "TechWorld with Nana",
            "description": f"Common interview questions about {topic} with detailed answers. Prepare for your next job interview.",
            "duration": "55:20",
            "views": "2.1M views",
            "published": "1 month ago",
            "url": "https://www.youtube.com/watch?v=OXGznpKjp_s",
            "thumbnail": "https://img.youtube.com/vi/OXGznpKjp_s/maxresdefault.jpg"
        }
    ]
    
    return sample_videos[:5]

@app.route('/api/sessions', methods=['GET'])
@require_auth
def get_sessions():
    """Get all chat sessions."""
    user_sessions = {k: v for k, v in chat_sessions.items() if v.get('user') == session['user']}
    return jsonify({
        'sessions': list(user_sessions.keys()),
        'current_session': current_session_id
    })

@app.route('/api/sessions', methods=['POST'])
@require_auth
def create_session():
    """Create a new chat session."""
    global current_session_id
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        'id': session_id,
        'title': 'New Chat',
        'messages': [],
        'created_at': datetime.now().isoformat(),
        'user': session['user']
    }
    current_session_id = session_id
    return jsonify({'session_id': session_id})

@app.route('/api/sessions/<session_id>', methods=['PUT'])
@require_auth
def update_session(session_id):
    """Update session title."""
    data = request.get_json()
    if session_id in chat_sessions and chat_sessions[session_id].get('user') == session['user']:
        chat_sessions[session_id]['title'] = data.get('title', 'New Chat')
        return jsonify({'success': True})
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
@require_auth
def delete_session(session_id):
    """Delete a chat session."""
    global current_session_id
    if session_id in chat_sessions and chat_sessions[session_id].get('user') == session['user']:
        del chat_sessions[session_id]
        if current_session_id == session_id:
            current_session_id = None
        return jsonify({'success': True})
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/sessions/<session_id>/messages', methods=['GET'])
@require_auth
def get_messages(session_id):
    """Get messages for a specific session."""
    if session_id in chat_sessions and chat_sessions[session_id].get('user') == session['user']:
        return jsonify({'messages': chat_sessions[session_id]['messages']})
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/chat', methods=['POST'])
@require_auth
def chat():
    """Handle chat messages with streaming response and continuous memory."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        image_data = data.get('image')
        document_content = data.get('document_content')
        
        if not user_message and not image_data and not document_content:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get or create session
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = {
                'id': session_id,
                'title': user_message[:50] + '...' if len(user_message) > 50 else user_message,
                'messages': [],
                'created_at': datetime.now().isoformat(),
                'user': session['user']
            }
        
        # Store filename for context
        filename = data.get('filename', '')
        
        # Add user message to session
        user_msg = {
            'id': str(uuid.uuid4()),
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat(),
            'image': image_data,
            'document_content': document_content,
            'filename': filename
        }
        chat_sessions[session_id]['messages'].append(user_msg)
        
        def generate_response():
            try:
                model = initialize_model()
                
                # Build conversation context for memory
                conversation_history = chat_sessions[session_id]['messages'][:-1]  # Exclude current message
                context = build_conversation_context(conversation_history)
                context = trim_context_if_needed(context)
                
                # Prepare content for Gemini with context
                content_parts = []
                
                # Add conversation context if exists
                if context:
                    content_parts.append(f"Previous conversation context:\n{context}\n\n---\n\n")
                
                # Add current message components
                if image_data:
                    # Handle image
                    image_bytes = base64.b64decode(image_data.split(',')[1])
                    content_parts.append({
                        'mime_type': 'image/jpeg',
                        'data': image_bytes
                    })
                
                if document_content:
                    content_parts.append(f"Document content ({filename}):\n{document_content}\n\n")
                
                # Add the current user message
                current_query = f"Current question/request: {user_message}"
                content_parts.append(current_query)
                
                # Generate response with context
                response = model.generate_content(content_parts)
                
                if response.candidates and response.candidates[0].content.parts:
                    assistant_message = response.candidates[0].content.parts[0].text
                    # Clean up any remaining \n characters
                    assistant_message = assistant_message.replace('\\n', '').replace('\n\n', '\n').strip()
                else:
                    assistant_message = "I apologize, but I couldn't generate a response at the moment. Please try again."
                
                # Add assistant message to session for future context
                assistant_msg = {
                    'id': str(uuid.uuid4()),
                    'role': 'assistant',
                    'content': assistant_message,
                    'timestamp': datetime.now().isoformat()
                }
                chat_sessions[session_id]['messages'].append(assistant_msg)
                
                # Stream the response with improved formatting
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
                
                # Split response into chunks for better streaming
                paragraphs = assistant_message.split('\n\n')
                for para_idx, paragraph in enumerate(paragraphs):
                    if paragraph.strip():
                        # Stream paragraph word by word
                        words = paragraph.split()
                        for word_idx, word in enumerate(words):
                            yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
                            time.sleep(0.008)  # Optimized streaming speed
                        
                        # Add paragraph break if not the last paragraph
                        if para_idx < len(paragraphs) - 1:
                            newline_content = '\n\n'
                            yield f"data: {json.dumps({'type': 'token', 'content': newline_content})}\n\n"
                            time.sleep(0.02)
                
                yield f"data: {json.dumps({'type': 'end', 'message_id': assistant_msg['id']})}\n\n"
                
            except Exception as e:
                error_message = f"I encountered an error while processing your request. Please try again. Error: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'error': error_message})}\n\n"
        
        return Response(stream_with_context(generate_response()), 
                      mimetype='text/event-stream',
                      headers={
                          'Cache-Control': 'no-cache',
                          'X-Accel-Buffering': 'no'  # Disable nginx buffering
                      })
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your message. Please try again.'
        }), 500

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    """Handle file uploads (images and documents)."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        file_ext = filename.split('.')[-1].lower()
        
        # Handle image uploads
        if file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            # Convert to base64 for frontend
            file_data = file.read()
            base64_data = base64.b64encode(file_data).decode('utf-8')
            mime_type = f'image/{file_ext}'
            return jsonify({
                'success': True,
                'type': 'image',
                'data': f'data:{mime_type};base64,{base64_data}',
                'filename': filename
            })
        
        # Handle document uploads
        elif file_ext in ['pdf', 'docx', 'txt']:
            content = process_uploaded_file(file)
            return jsonify({
                'success': True,
                'type': 'document',
                'content': content,
                'filename': filename
            })
        
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
            
    except Exception as e:
        print(f"Error in upload endpoint: {str(e)}")
        return jsonify({'error': 'File upload failed'}), 500

@app.route('/api/voice', methods=['POST'])
@require_auth
def text_to_speech():
    """Convert text to speech."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # For now, return the text (in production, integrate with TTS service)
        return jsonify({
            'success': True,
            'audio_url': f'/api/audio/{uuid.uuid4()}'  # Placeholder
        })
        
    except Exception as e:
        print(f"Error in TTS endpoint: {str(e)}")
        return jsonify({'error': 'TTS conversion failed'}), 500

# Additional utility endpoints for memory management
@app.route('/api/sessions/<session_id>/clear', methods=['POST'])
@require_auth
def clear_session_memory(session_id):
    """Clear session memory while keeping the session active."""
    if session_id in chat_sessions and chat_sessions[session_id].get('user') == session['user']:
        chat_sessions[session_id]['messages'] = []
        return jsonify({'success': True, 'message': 'Session memory cleared'})
    return jsonify({'error': 'Session not found'}), 404

@app.route('/api/sessions/<session_id>/summary', methods=['GET'])
@require_auth
def get_session_summary(session_id):
    """Get a summary of the session conversation."""
    if session_id not in chat_sessions or chat_sessions[session_id].get('user') != session['user']:
        return jsonify({'error': 'Session not found'}), 404
    
    messages = chat_sessions[session_id]['messages']
    if not messages:
        return jsonify({'summary': 'No conversation yet'})
    
    # Generate a simple summary based on message count and topics
    user_messages = [msg for msg in messages if msg['role'] == 'user']
    total_messages = len(messages)
    topics = [msg['content'][:50] + '...' if len(msg['content']) > 50 else msg['content'] 
              for msg in user_messages[:5]]  # First 5 topics
    
    summary = {
        'total_messages': total_messages,
        'user_messages': len(user_messages),
        'recent_topics': topics,
        'session_duration': 'Active session',
        'created_at': chat_sessions[session_id]['created_at']
    }
    
    return jsonify({'summary': summary})

if __name__ == '__main__':
    # Check if API key is set
    if not os.getenv('GEMINI_API_KEY'):
        print("Warning: GEMINI_API_KEY environment variable not set!")
        print("Please set your Google API key: set GEMINI_API_KEY=your_api_key_here")
    
    print("Starting Nova AI - Professional ChatGPT-Style Assistant")
    print("Features: ChatGPT-Level Responses, Advanced Memory, Professional Formatting")
    print("Server: http://localhost:5000")
    print("Quality: Enterprise-Grade AI Responses")
    
    app.run(debug=True, host='0.0.0.0', port=5000)