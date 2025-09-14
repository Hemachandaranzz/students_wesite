// Voice Assistant JavaScript - Modern Dark Theme with Purple Accents
class VoiceAssistant {
    constructor() {
        this.isListening = false;
        this.isSpeaking = false;
        this.recognition = null;
        this.synthesis = null;
        this.currentLanguage = 'en';
        this.sessionId = 'voice_' + Date.now();
        this.voices = [];
        this.settings = {
            speed: 0.85,
            pitch: 0.95,
            volume: 0.9
        };
        
        this.init();
    }

    init() {
        this.setupSpeechRecognition();
        this.setupSpeechSynthesis();
        this.createInterface();
        console.log('Voice Assistant initialized successfully!');
    }

    setupSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
        } else if ('SpeechRecognition' in window) {
            this.recognition = new SpeechRecognition();
        } else {
            console.warn('Speech recognition not supported in this browser');
            this.updateStatus('Speech recognition not supported. Please use Chrome or Edge.');
            return;
        }

        if (this.recognition) {
            this.recognition.continuous = false;
            this.recognition.interimResults = true;
            this.recognition.lang = this.getLanguageCode(this.currentLanguage);
            this.recognition.maxAlternatives = 3;
            this.recognitionTimeout = null;

            this.recognition.onstart = () => {
                console.log('Speech recognition started');
                this.updateStatus('Listening... Speak now!');
                this.startListeningAnimation();
                
                this.recognitionTimeout = setTimeout(() => {
                    if (this.isListening) {
                        console.log('Speech recognition timeout');
                        this.recognition.stop();
                    }
                }, 10000);
            };

            this.recognition.onresult = (event) => {
                console.log('Speech recognition result:', event.results);
                
                let finalTranscript = '';
                let interimTranscript = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interimTranscript += transcript;
                    }
                }
                
                if (interimTranscript) {
                    this.updateStatus(`Listening: "${interimTranscript}"`);
                }
                
                if (finalTranscript) {
                    console.log('Final speech recognized:', finalTranscript);
                    this.handleVoiceInput(finalTranscript.trim());
                }
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                let errorMessage = 'Speech recognition error. Please try again.';
                
                if (this.recognitionTimeout) {
                    clearTimeout(this.recognitionTimeout);
                    this.recognitionTimeout = null;
                }
                
                switch(event.error) {
                    case 'no-speech':
                        errorMessage = 'No speech detected. Please try again.';
                        break;
                    case 'audio-capture':
                        errorMessage = 'Microphone not found. Please check your microphone.';
                        break;
                    case 'not-allowed':
                        errorMessage = 'Microphone permission denied. Please allow microphone access.';
                        break;
                    case 'network':
                        errorMessage = 'Network error. Please check your connection.';
                        break;
                    case 'aborted':
                        return;
                    case 'service-not-allowed':
                        errorMessage = 'Speech recognition service not allowed. Please check browser settings.';
                        break;
                }
                
                this.updateStatus(errorMessage);
                this.stopListeningAnimation();
                this.isListening = false;
            };

            this.recognition.onend = () => {
                console.log('Speech recognition ended');
                
                if (this.recognitionTimeout) {
                    clearTimeout(this.recognitionTimeout);
                    this.recognitionTimeout = null;
                }
                
                this.stopListeningAnimation();
                this.isListening = false;
                this.updateStatus('Click the microphone to start talking');
            };
        }
    }

    getLanguageCode(lang) {
        const languageMap = {
            'en': 'en-US',
            'ta': 'ta-IN',
            'hi': 'hi-IN',
            'te': 'te-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN'
        };
        return languageMap[lang] || 'en-US';
    }

    setupSpeechSynthesis() {
        this.synthesis = window.speechSynthesis;
        this.voices = this.synthesis.getVoices();
        
        if (this.voices.length === 0) {
            this.synthesis.onvoiceschanged = () => {
                this.voices = this.synthesis.getVoices();
                console.log('Voices loaded:', this.voices.length);
            };
        }
    }

    getVoiceForLanguage(lang) {
        const preferredVoices = {
            'en': [
                'Google UK English Female', 'Google UK English Male',
                'Microsoft Zira Desktop', 'Microsoft David Desktop',
                'Alex', 'Samantha', 'Victoria', 'Daniel'
            ],
            'ta': ['Google தமிழ் (India)', 'Microsoft Valluvar Desktop'],
            'hi': ['Google हिन्दी (India)', 'Microsoft Hemant Desktop'],
            'te': ['Google తెలుగు (India)', 'Microsoft Chitra Desktop'],
            'kn': ['Google ಕನ್ನಡ (India)', 'Microsoft Gagan Desktop'],
            'ml': ['Google മലയാളം (India)', 'Microsoft Ravi Desktop']
        };
        
        const langCode = this.getLanguageCode(lang);
        const preferred = preferredVoices[lang] || [];
        
        for (const preferredName of preferred) {
            const voice = this.voices.find(v => 
                v.name.includes(preferredName) || 
                v.name.toLowerCase().includes(preferredName.toLowerCase())
            );
            if (voice) {
                console.log(`Using preferred voice: ${voice.name} (${voice.lang})`);
                return voice;
            }
        }
        
        const voice = this.voices.find(v => v.lang === langCode) || 
                     this.voices.find(v => v.lang.startsWith(lang.split('-')[0])) ||
                     this.voices.find(v => v.lang.includes('en')) ||
                     this.voices[0];
        
        if (voice) {
            console.log(`Using fallback voice: ${voice.name} (${voice.lang})`);
        }
        
        return voice;
    }

    createInterface() {
        console.log('Creating modern dark voice assistant interface');
        
        const existingOverlay = document.getElementById('gptVoiceOverlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        const overlay = document.createElement('div');
        overlay.id = 'gptVoiceOverlay';
        overlay.className = 'voice-assistant-overlay';
        overlay.innerHTML = `
            <div class="voice-assistant-container">
                <div class="voice-assistant-header">
                    <div class="voice-assistant-title">
                        <div class="voice-assistant-icon">
                            <i class="fas fa-microphone"></i>
                        </div>
                        <div class="voice-assistant-title-text">
                            <h3>Voice Assistant</h3>
                            <span class="voice-assistant-subtitle">Powered by Lumora AI</span>
                        </div>
                    </div>
                    <button class="voice-assistant-close" id="voiceAssistantClose">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <div class="voice-assistant-content">
                    <div class="voice-assistant-messages" id="voiceAssistantMessages">
                        <div class="welcome-message">
                            <div class="welcome-avatar">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div class="welcome-content">
                                <h4>Hello! I'm Lumora</h4>
                                <p>Your AI voice assistant. Click the microphone and start talking!</p>
                                <div class="welcome-features">
                                    <span class="feature-tag">Voice Input</span>
                                    <span class="feature-tag">Multi-language</span>
                                    <span class="feature-tag">Voice Output</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="voice-assistant-controls">
                        <div class="language-selector">
                            <label class="language-label">Language</label>
                            <select id="languageSelect" class="language-dropdown">
                                <option value="en">English</option>
                                <option value="ta">தமிழ் (Tamil)</option>
                                <option value="hi">हिन्दी (Hindi)</option>
                                <option value="te">తెలుగు (Telugu)</option>
                                <option value="kn">ಕನ್ನಡ (Kannada)</option>
                                <option value="ml">മലയാളം (Malayalam)</option>
                            </select>
                        </div>
                        
                        <div class="voice-animation" id="voiceAnimation">
                            <div class="voice-control-container">
                                <div class="voice-button" id="micButton">
                                    <div class="mic-icon">
                                        <i class="fas fa-microphone"></i>
                                    </div>
                                    <div class="voice-waves">
                                        <div class="voice-wave wave-1"></div>
                                        <div class="voice-wave wave-2"></div>
                                        <div class="voice-wave wave-3"></div>
                                        <div class="voice-wave wave-4"></div>
                                        <div class="voice-wave wave-5"></div>
                                    </div>
                                </div>
                                
                                <button class="stop-button" id="stopButton" style="display: none;">
                                    <i class="fas fa-stop"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="voice-assistant-status" id="voiceStatus">
                            <span>Click the microphone to start talking</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        this.addCSS();
        this.setupEventListeners();
        this.setupSmoothScrolling();
    }

    addCSS() {
        const existingCSS = document.getElementById('voice-assistant-css');
        if (existingCSS) {
            existingCSS.remove();
        }
        
        const style = document.createElement('style');
        style.id = 'voice-assistant-css';
        style.textContent = `
            .voice-assistant-overlay {
                position: fixed;
                top: 0;
                right: 0;
                width: 420px;
                height: 100vh;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                backdrop-filter: blur(20px);
                z-index: 10000;
                transform: translateX(100%);
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                border-left: 1px solid rgba(139, 92, 246, 0.2);
                box-shadow: -20px 0 40px rgba(0, 0, 0, 0.8), -10px 0 20px rgba(139, 92, 246, 0.1);
                display: none;
            }

            .voice-assistant-overlay.show {
                transform: translateX(0);
                display: block;
            }

            .voice-assistant-container {
                width: 100%;
                height: 100%;
                background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                position: relative;
            }

            .voice-assistant-header {
                padding: 24px;
                background: rgba(0, 0, 0, 0.8);
                border-bottom: 1px solid rgba(139, 92, 246, 0.2);
                display: flex;
                align-items: center;
                justify-content: space-between;
                position: relative;
                backdrop-filter: blur(10px);
            }

            .voice-assistant-title {
                display: flex;
                align-items: center;
                gap: 16px;
            }

            .voice-assistant-icon {
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, #8b5cf6, #a78bfa);
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 20px;
                box-shadow: 0 8px 32px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
            }

            .voice-assistant-title-text h3 {
                margin: 0;
                color: #ffffff;
                font-size: 20px;
                font-weight: 700;
                letter-spacing: -0.02em;
            }

            .voice-assistant-subtitle {
                color: #9ca3af;
                font-size: 13px;
                font-weight: 500;
                margin-top: 2px;
            }

            .voice-assistant-close {
                width: 40px;
                height: 40px;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid #374151;
                border-radius: 12px;
                color: #9ca3af;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .voice-assistant-close:hover {
                background: rgba(239, 68, 68, 0.1);
                border-color: #ef4444;
                color: #ef4444;
                transform: scale(1.05);
            }

            .voice-assistant-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                padding: 0 24px 24px;
                overflow: hidden;
            }

            .voice-assistant-messages {
                flex: 1;
                overflow-y: auto;
                padding: 20px 0;
                scroll-behavior: smooth;
                max-height: 400px;
            }

            .welcome-message {
                display: flex;
                gap: 16px;
                margin-bottom: 24px;
                padding: 20px;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 16px;
                backdrop-filter: blur(10px);
                animation: slideInUp 0.6s ease;
            }

            .welcome-avatar {
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, #8b5cf6, #a78bfa);
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 20px;
                flex-shrink: 0;
                box-shadow: 0 8px 32px rgba(139, 92, 246, 0.3);
            }

            .welcome-content h4 {
                margin: 0 0 8px;
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
            }

            .welcome-content p {
                margin: 0 0 16px;
                color: #e5e7eb;
                font-size: 14px;
                line-height: 1.5;
            }

            .welcome-features {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }

            .feature-tag {
                background: rgba(139, 92, 246, 0.2);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 20px;
                padding: 6px 12px;
                font-size: 12px;
                color: #a78bfa;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .voice-assistant-controls {
                display: flex;
                flex-direction: column;
                gap: 24px;
                margin-top: auto;
            }

            .language-selector {
                margin-bottom: 8px;
            }

            .language-label {
                display: block;
                color: #e5e7eb;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .language-dropdown {
                width: 100%;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 14px 16px;
                color: #ffffff;
                font-size: 14px;
                cursor: pointer;
                appearance: none;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            }

            .language-dropdown:focus {
                outline: none;
                border-color: #8b5cf6;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
            }

            .language-dropdown option {
                background: #1a1a1a;
                color: #ffffff;
                padding: 12px;
            }

            .voice-animation {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
            }

            .voice-control-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 24px;
            }

            .voice-button {
                position: relative;
                width: 140px;
                height: 140px;
                background: linear-gradient(135deg, #8b5cf6, #a78bfa);
                border: none;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 20px 40px rgba(139, 92, 246, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.1);
                overflow: hidden;
            }

            .voice-button:hover {
                transform: scale(1.05);
                box-shadow: 0 25px 50px rgba(139, 92, 246, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.2);
            }

            .voice-button:active {
                transform: scale(0.95);
            }

            .mic-icon {
                font-size: 36px;
                z-index: 2;
                position: relative;
            }

            .voice-waves {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 100%;
                height: 100%;
                pointer-events: none;
            }

            .voice-wave {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                border: 2px solid rgba(139, 92, 246, 0.4);
                border-radius: 50%;
                opacity: 0;
            }

            .voice-wave.wave-1 { width: 80px; height: 80px; animation: wave 2s infinite 0s; }
            .voice-wave.wave-2 { width: 100px; height: 100px; animation: wave 2s infinite 0.2s; }
            .voice-wave.wave-3 { width: 120px; height: 120px; animation: wave 2s infinite 0.4s; }
            .voice-wave.wave-4 { width: 140px; height: 140px; animation: wave 2s infinite 0.6s; }
            .voice-wave.wave-5 { width: 160px; height: 160px; animation: wave 2s infinite 0.8s; }

            @keyframes wave {
                0% { 
                    opacity: 0; 
                    transform: translate(-50%, -50%) scale(0.8);
                    border-color: rgba(139, 92, 246, 0.2);
                }
                50% { 
                    opacity: 1; 
                    transform: translate(-50%, -50%) scale(1);
                    border-color: rgba(139, 92, 246, 0.6);
                }
                100% { 
                    opacity: 0; 
                    transform: translate(-50%, -50%) scale(1.2);
                    border-color: rgba(139, 92, 246, 0.1);
                }
            }

            .stop-button {
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #ef4444, #dc2626);
                border: none;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                transition: all 0.3s ease;
                box-shadow: 0 15px 30px rgba(239, 68, 68, 0.4);
            }

            .stop-button:hover {
                transform: scale(1.05);
                box-shadow: 0 20px 40px rgba(239, 68, 68, 0.6);
            }

            .voice-assistant-status {
                text-align: center;
                color: #9ca3af;
                font-size: 14px;
                padding: 12px;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid #374151;
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }

            .voice-button.listening {
                animation: listeningPulse 1.5s ease-in-out infinite;
                background: linear-gradient(135deg, #06b6d4, #0891b2);
                box-shadow: 0 25px 50px rgba(6, 182, 212, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.3);
            }

            @keyframes listeningPulse {
                0%, 100% { 
                    transform: scale(1); 
                    box-shadow: 0 25px 50px rgba(6, 182, 212, 0.6);
                }
                50% { 
                    transform: scale(1.1); 
                    box-shadow: 0 30px 60px rgba(6, 182, 212, 0.8);
                }
            }

            .voice-button.listening .voice-wave {
                animation-play-state: running;
            }

            .voice-button:not(.listening) .voice-wave {
                animation-play-state: paused;
            }

            .voice-button.speaking {
                animation: speakingGlow 2s ease-in-out infinite;
                background: linear-gradient(135deg, #10b981, #059669);
            }

            @keyframes speakingGlow {
                0%, 100% { 
                    transform: scale(1);
                    box-shadow: 0 25px 50px rgba(16, 185, 129, 0.4);
                }
                50% { 
                    transform: scale(1.05);
                    box-shadow: 0 30px 60px rgba(16, 185, 129, 0.6);
                }
            }

            .voice-message {
                margin-bottom: 20px;
                animation: messageSlideIn 0.4s ease;
            }

            .voice-message-user {
                display: flex;
                justify-content: flex-end;
                margin-left: 40px;
            }

            .voice-message-assistant {
                display: flex;
                justify-content: flex-start;
                margin-right: 40px;
            }

            .voice-message-content {
                max-width: 85%;
                padding: 16px 20px;
                border-radius: 20px;
                position: relative;
                backdrop-filter: blur(10px);
            }

            .user-message {
                background: linear-gradient(135deg, #8b5cf6, #a78bfa);
                color: white;
                margin-left: auto;
                box-shadow: 0 8px 32px rgba(139, 92, 246, 0.3);
            }

            .assistant-message {
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid rgba(139, 92, 246, 0.2);
                color: #ffffff;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }

            .voice-message-content p {
                margin: 0;
                font-size: 14px;
                line-height: 1.5;
            }

            .typing-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 16px 20px;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid rgba(139, 92, 246, 0.2);
                border-radius: 20px;
                backdrop-filter: blur(10px);
                margin-right: 40px;
                max-width: 85%;
            }

            .typing-dots {
                display: flex;
                gap: 4px;
            }

            .typing-dot {
                width: 8px;
                height: 8px;
                background: #8b5cf6;
                border-radius: 50%;
                animation: typingDot 1.4s infinite ease-in-out;
            }

            .typing-dot:nth-child(1) { animation-delay: -0.32s; }
            .typing-dot:nth-child(2) { animation-delay: -0.16s; }
            .typing-dot:nth-child(3) { animation-delay: 0s; }

            @keyframes typingDot {
                0%, 80%, 100% { 
                    transform: scale(0.8);
                    opacity: 0.5;
                }
                40% { 
                    transform: scale(1);
                    opacity: 1;
                }
            }

            @keyframes slideInUp {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes messageSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @media (max-width: 768px) {
                .voice-assistant-overlay {
                    width: 100%;
                    right: 0;
                }
                
                .voice-button {
                    width: 120px;
                    height: 120px;
                }
                
                .mic-icon {
                    font-size: 32px;
                }
                
                .voice-assistant-messages {
                    max-height: 350px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }

    setupEventListeners() {
        const closeBtn = document.getElementById('voiceAssistantClose');
        const micBtn = document.getElementById('micButton');
        const stopBtn = document.getElementById('stopButton');
        const langSelect = document.getElementById('languageSelect');
        
        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.close();
            });
        }
        
        if (micBtn) {
            micBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleListening();
            });
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.stopSpeaking();
            });
        }
        
        if (langSelect) {
            langSelect.addEventListener('change', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.setLanguage(e.target.value);
            });
        }
    }

    setupSmoothScrolling() {
        const messagesContainer = document.getElementById('voiceAssistantMessages');
        if (messagesContainer) {
            const observer = new MutationObserver(() => {
                this.scrollToBottom();
            });
            
            observer.observe(messagesContainer, {
                childList: true,
                subtree: true
            });
        }
    }

    open() {
        console.log('Opening voice assistant');
        const overlay = document.getElementById('gptVoiceOverlay');
        if (overlay) {
            overlay.style.display = 'block';
            overlay.style.zIndex = '10000';
            setTimeout(() => {
                overlay.classList.add('show');
            }, 10);
            console.log('Voice assistant opened successfully');
        } else {
            console.error('Voice assistant overlay not found');
        }
    }

    close() {
        console.log('Closing voice assistant');
        const overlay = document.getElementById('gptVoiceOverlay');
        if (overlay) {
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 300);
            this.stopListening();
            this.stopSpeaking();
            console.log('Voice assistant closed successfully');
        } else {
            console.error('Voice assistant overlay not found');
        }
    }

    async toggleListening() {
        console.log('Toggle listening called, current state:', this.isListening);
        
        if (!this.recognition) {
            alert('Speech recognition not supported in this browser. Please use Chrome or Edge.');
            return;
        }

        if (this.isListening) {
            console.log('Stopping listening...');
            this.stopListening();
        } else {
            console.log('Starting listening...');
            try {
                console.log('Requesting microphone permission...');
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                console.log('Microphone permission granted');
                
                stream.getTracks().forEach(track => track.stop());
                
                this.startListening();
            } catch (error) {
                console.error('Microphone permission denied:', error);
                this.updateStatus('Microphone permission required. Please allow microphone access.');
                
                let errorMessage = 'Microphone permission is required for voice input. ';
                if (error.name === 'NotAllowedError') {
                    errorMessage += 'Please click "Allow" when prompted for microphone access.';
                } else if (error.name === 'NotFoundError') {
                    errorMessage += 'No microphone found. Please connect a microphone.';
                } else {
                    errorMessage += 'Please check your microphone settings and try again.';
                }
                
                alert(errorMessage);
                return;
            }
        }
    }

    startListening() {
        if (this.isListening) {
            console.log('Already listening, ignoring start request');
            return;
        }
        
        console.log('Starting speech recognition...');
        this.isListening = true;
        this.recognition.lang = this.getLanguageCode(this.currentLanguage);
        
        try {
            this.recognition.start();
            console.log('Speech recognition start() called successfully');
            
            const micButton = document.getElementById('micButton');
            if (micButton) {
                micButton.classList.add('listening');
            }
        } catch (error) {
            console.error('Error starting speech recognition:', error);
            this.isListening = false;
            this.updateStatus('Error starting speech recognition. Please try again.');
        }
    }

    stopListening() {
        if (!this.isListening) return;
        
        this.isListening = false;
        this.recognition.stop();
        
        const micButton = document.getElementById('micButton');
        micButton.classList.remove('listening');
    }

    startListeningAnimation() {
        const micButton = document.getElementById('micButton');
        micButton.classList.add('listening');
    }

    stopListeningAnimation() {
        const micButton = document.getElementById('micButton');
        micButton.classList.remove('listening');
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        console.log('Language changed to:', lang);
        this.updateStatus(`Language changed to ${lang}`);
    }

    updateStatus(message) {
        const statusElement = document.getElementById('voiceStatus');
        if (statusElement) {
            statusElement.querySelector('span').textContent = message;
        }
    }

    async handleVoiceInput(transcript) {
        console.log('Processing voice input:', transcript);
        this.updateStatus('Processing your message...');
        
        this.addMessage('user', transcript);
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/voice-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: transcript,
                    session_id: this.sessionId,
                    language: this.currentLanguage
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.hideTypingIndicator();
                this.addMessage('assistant', data.response);
                await this.speakResponse(data.response);
            } else {
                this.hideTypingIndicator();
                this.updateStatus('Error: ' + data.message);
            }
        } catch (error) {
            console.error('Error processing voice input:', error);
            this.hideTypingIndicator();
            this.updateStatus('Error processing your message');
        }
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('voiceAssistantMessages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicator';
        typingDiv.className = 'voice-message voice-message-assistant';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                <span style="margin-left: 8px; color: #9ca3af; font-size: 12px;">Lumora is thinking...</span>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    addMessage(sender, content) {
        const messagesContainer = document.getElementById('voiceAssistantMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `voice-message voice-message-${sender}`;
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="voice-message-content user-message">
                    <p>${content}</p>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="voice-message-content assistant-message">
                    <p>${content}</p>
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('voiceAssistantMessages');
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTo({
                    top: messagesContainer.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        }
    }

    async speakResponse(text) {
        if (this.isSpeaking) {
            this.stopSpeaking();
        }

        this.isSpeaking = true;
        this.updateStatus('Speaking...');
        
        const stopButton = document.getElementById('stopButton');
        const micButton = document.getElementById('micButton');
        stopButton.style.display = 'flex';
        micButton.style.display = 'none';
        
        micButton.classList.add('speaking');

        try {
            const cleanText = this.cleanTextForSpeech(text);
            console.log('Speaking cleaned text:', cleanText);
            
            if (['ta', 'hi', 'te', 'kn', 'ml'].includes(this.currentLanguage)) {
                await this.speakWithGTTS(cleanText);
            } else {
                await this.speakWithBrowser(cleanText);
            }
        } catch (error) {
            console.error('Error speaking:', error);
            this.updateStatus('Error speaking response');
        } finally {
            this.isSpeaking = false;
            stopButton.style.display = 'none';
            micButton.style.display = 'flex';
            micButton.classList.remove('speaking');
            this.updateStatus('Click the microphone to start talking');
        }
    }

    cleanTextForSpeech(text) {
        if (!text) return '';
        
        let cleanText = text
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/`(.*?)`/g, '$1')
            .replace(/```[\s\S]*?```/g, '')
            .replace(/`[\s\S]*?`/g, '')
            .replace(/#{1,6}\s+/g, '')
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
            .replace(/^\s*[-*+]\s+/gm, '')
            .replace(/^\s*\d+\.\s+/gm, '')
            .replace(/\n{3,}/g, '\n\n')
            .replace(/\s+/g, ' ')
            .trim();
        
        cleanText = cleanText
            .replace(/&/g, ' and ')
            .replace(/@/g, ' at ')
            .replace(/#/g, ' hash ')
            .replace(/\$/g, ' dollar ')
            .replace(/%/g, ' percent ')
            .replace(/\*/g, ' ')
            .replace(/\+/g, ' plus ')
            .replace(/=/g, ' equals ')
            .replace(/</g, ' less than ')
            .replace(/>/g, ' greater than ')
            .replace(/\|/g, ' or ')
            .replace(/\\/g, ' ')
            .replace(/\//g, ' ')
            .replace(/\[/g, ' ')
            .replace(/\]/g, ' ')
            .replace(/\{/g, ' ')
            .replace(/\}/g, ' ')
            .replace(/\(/g, ' ')
            .replace(/\)/g, ' ')
            .replace(/~/g, ' ')
            .replace(/`/g, ' ')
            .replace(/"/g, ' ')
            .replace(/'/g, ' ')
            .replace(/;/g, ' ')
            .replace(/:/g, ' ')
            .replace(/,/g, ' ')
            .replace(/\./g, ' ')
            .replace(/\?/g, ' ')
            .replace(/!/g, ' ')
            .replace(/-/g, ' ')
            .replace(/_/g, ' ');
        
        cleanText = cleanText.replace(/\s+/g, ' ').trim();
        
        if (cleanText.length > 500) {
            cleanText = cleanText.substring(0, 500) + '...';
        }
        
        return cleanText;
    }

    async speakWithGTTS(text) {
        try {
            const response = await fetch('/api/gtts-speak', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    language: this.currentLanguage
                })
            });

            if (response.ok) {
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                
                audio.volume = this.settings.volume;
                
                audio.onended = () => {
                    URL.revokeObjectURL(audioUrl);
                };
                
                await audio.play();
            } else {
                throw new Error('GTTS request failed');
            }
        } catch (error) {
            console.error('GTTS error:', error);
            await this.speakWithBrowser(text);
        }
    }

    async speakWithBrowser(text) {
        return new Promise((resolve, reject) => {
            const utterance = new SpeechSynthesisUtterance(text);
            
            utterance.lang = this.getLanguageCode(this.currentLanguage);
            
            const voice = this.getVoiceForLanguage(this.currentLanguage);
            if (voice) {
                utterance.voice = voice;
                console.log('Using voice:', voice.name, voice.lang);
            } else {
                console.log('Using default voice for language:', utterance.lang);
            }
            
            utterance.rate = this.settings.speed;
            utterance.pitch = this.settings.pitch;
            utterance.volume = this.settings.volume;
            
            utterance.text = this.addSpeechPauses(text);
            
            utterance.onstart = () => {
                console.log('Speech synthesis started');
            };
            
            utterance.onend = () => {
                console.log('Speech synthesis ended');
                resolve();
            };
            
            utterance.onerror = (error) => {
                console.error('Speech synthesis error:', error);
                reject(error);
            };
            
            this.synthesis.cancel();
            this.synthesis.speak(utterance);
        });
    }

    addSpeechPauses(text) {
        return text
            .replace(/\./g, '. ')
            .replace(/,/g, ', ')
            .replace(/:/g, ': ')
            .replace(/;/g, '; ')
            .replace(/\?/g, '? ')
            .replace(/!/g, '! ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    stopSpeaking() {
        if (this.synthesis) {
            this.synthesis.cancel();
        }
        this.isSpeaking = false;
        
        const stopButton = document.getElementById('stopButton');
        const micButton = document.getElementById('micButton');
        stopButton.style.display = 'none';
        micButton.style.display = 'flex';
        micButton.classList.remove('speaking');
        
        this.updateStatus('Click the microphone to start talking');
    }
}

// Make VoiceAssistant available as GPTVoiceAssistant for compatibility
window.GPTVoiceAssistant = VoiceAssistant;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Voice Assistant loaded successfully!');
});
