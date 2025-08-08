"""
JARVIS Advanced Command Processor - Handles all voice and text commands
"""

import time
import datetime
import logging
import re
import random
from typing import Dict, Any, Optional, List
import webbrowser
import os
import subprocess
import platform

# Advanced capabilities
try:
    import wikipedia
except ImportError:
    try:
        import wikipediaapi as wikipedia
    except ImportError:
        wikipedia = None

import requests
import psutil
import pyjokes
from bs4 import BeautifulSoup

# Advanced integrations
try:
    from ..integrations.openai_integration import get_openai_integration
    from ..integrations.vscode_integration import get_vscode_integration
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False

# Personality system
try:
    from ..personality.jarvis_personality import get_jarvis_personality
    PERSONALITY_AVAILABLE = True
except ImportError:
    PERSONALITY_AVAILABLE = False

# Memory system
try:
    from ..core.memory_manager import get_memory_manager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

# Enhanced vision system
try:
    from ..vision.enhanced_analysis import get_enhanced_vision
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

logger = logging.getLogger(__name__)

class CommandProcessor:
    """Advanced command processor with web search, Wikipedia, weather, and system control"""
    
    def __init__(self, jarvis_instance=None):
        self.jarvis = jarvis_instance

        # API keys and configurations
        self.weather_api_key = os.getenv('OPENWEATHER_API_KEY', '')
        self.news_api_key = os.getenv('NEWS_API_KEY', '')

        # Advanced integrations
        self.openai_integration = None
        self.vscode_integration = None
        self.personality = None
        self.memory_manager = None
        self.enhanced_vision = None

        if ADVANCED_FEATURES_AVAILABLE:
            try:
                self.openai_integration = get_openai_integration()
                self.vscode_integration = get_vscode_integration()
                logger.info("Advanced integrations loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load advanced integrations: {e}")

        if PERSONALITY_AVAILABLE:
            try:
                self.personality = get_jarvis_personality()
                logger.info("JARVIS personality system loaded")
            except Exception as e:
                logger.warning(f"Failed to load personality system: {e}")

        if MEMORY_AVAILABLE:
            try:
                self.memory_manager = get_memory_manager()
                logger.info("JARVIS memory system loaded")
            except Exception as e:
                logger.warning(f"Failed to load memory system: {e}")

        if VISION_AVAILABLE:
            try:
                self.enhanced_vision = get_enhanced_vision()
                logger.info("JARVIS enhanced vision system loaded")
            except Exception as e:
                logger.warning(f"Failed to load enhanced vision system: {e}")
        
        # Command patterns
        self.command_patterns = {
            'greeting': [
                r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b.*jarvis',
                r'jarvis.*\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
                r'\b(hello|hi|hey)\b'
            ],
            'time': [
                r'\b(what time|current time|time is it|tell me the time)\b',
                r'\btime\b'
            ],
            'date': [
                r'\b(what date|current date|today\'s date|what day)\b',
                r'\bdate\b'
            ],
            'weather': [
                r'\b(weather|temperature|forecast)\b.*\bin\s+(\w+)',
                r'\b(weather|temperature|forecast)\b'
            ],
            'search': [
                r'\b(search|google|look up|find)\b\s+(.+)',
                r'\bsearch for\b\s+(.+)'
            ],
            'wikipedia': [
                r'\b(wikipedia|wiki|tell me about|what is|who is)\b\s+(.+)',
                r'\bwikipedia\b\s+(.+)'
            ],
            'news': [
                r'\b(news|latest news|headlines)\b',
                r'\btell me the news\b'
            ],
            'joke': [
                r'\b(joke|tell me a joke|make me laugh|funny)\b'
            ],
            'system_info': [
                r'\b(system info|computer info|system status|hardware)\b'
            ],
            'open_app': [
                r'\bopen\b\s+(.+)',
                r'\blaunch\b\s+(.+)',
                r'\bstart\b\s+(.+)'
            ],
            'volume': [
                r'\b(volume up|increase volume|louder)\b',
                r'\b(volume down|decrease volume|quieter)\b',
                r'\b(mute|unmute)\b'
            ],
            'camera': [
                r'\b(take photo|take picture|capture|photo|picture)\b',
                r'\b(what do you see|describe|look|camera)\b'
            ],
            'calculate': [
                r'\b(calculate|compute|math)\b\s+(.+)',
                r'\bwhat is\b\s+(\d+.*[\+\-\*\/].*\d+)'
            ],
            'shutdown': [
                r'\b(shutdown|turn off|power off)\b',
                r'\brestart\b',
                r'\bsleep\b'
            ],
            'smart_chat': [
                r'\b(ask|chat|discuss|explain|analyze)\b\s+(.+)',
                r'\b(what do you think about|your opinion on)\b\s+(.+)',
                r'\b(help me understand|tell me more about)\b\s+(.+)'
            ],
            'vscode': [
                r'\b(open|launch)\b\s+(vscode|vs code|visual studio code)',
                r'\b(open file|edit file)\b\s+(.+)',
                r'\b(open workspace|open folder)\b\s+(.+)',
                r'\b(search in code|find in files)\b\s+(.+)',
                r'\b(create file)\b\s+(.+)'
            ],
            'code_help': [
                r'\b(explain code|analyze code|review code)\b',
                r'\b(generate code|write code|create code)\b\s+(.+)',
                r'\b(fix code|debug code|improve code)\b'
            ],
            'entertainment': [
                r'\b(sing|song|music)\b',
                r'\b(story|tell me a story)\b',
                r'\b(riddle|puzzle)\b',
                r'\b(quote|inspiration|motivate me)\b'
            ],
            'personal': [
                r'\b(how are you|how do you feel|what\'s your mood)\b',
                r'\b(what are you thinking|your thoughts)\b',
                r'\b(do you like|your opinion|what do you prefer)\b',
                r'\b(are you happy|are you sad|are you tired)\b'
            ],
            'learning': [
                r'\b(teach me|learn about|explain)\b\s+(.+)',
                r'\b(what is|define|meaning of)\b\s+(.+)',
                r'\b(how does|how do|how to)\b\s+(.+)'
            ],
            'productivity': [
                r'\b(remind me|set reminder|schedule)\b\s+(.+)',
                r'\b(todo|task list|what should i do)\b',
                r'\b(focus|concentrate|productivity tips)\b'
            ],
            'social': [
                r'\b(compliment me|say something nice)\b',
                r'\b(thank you|thanks|appreciate)\b',
                r'\b(sorry|apologize|my bad)\b',
                r'\b(good job|well done|excellent)\b'
            ],
            'status_check': [
                r'\b(status|health|diagnostics|system check)\b',
                r'\b(what\'s running|active processes|current tasks)\b',
                r'\b(memory usage|cpu usage|performance)\b'
            ],
            'advanced_search': [
                r'\b(find files|locate|search files)\b\s+(.+)',
                r'\b(recent files|last opened|history)\b',
                r'\b(bookmarks|favorites|saved)\b'
            ],
            'preferences': [
                r'\b(set preference|update preference|remember)\b\s+(.+)',
                r'\b(my name is|call me)\b\s+(.+)',
                r'\b(greeting style|preferred greeting)\b\s+(.+)'
            ],
            'vision_analysis': [
                r'\b(analyze image|read image|scan image|ocr|extract text)\b',
                r'\b(what do you see|describe image|image analysis)\b',
                r'\b(detect objects|find objects|count objects)\b',
                r'\b(detect faces|count faces|face detection)\b',
                r'\b(analyze colors|color analysis|dominant colors)\b'
            ]
        }
        
        logger.info("CommandProcessor initialized with advanced capabilities")
    
    def process_command(self, text: str) -> str:
        """Process a command and return response with memory integration"""
        text = text.lower().strip()
        start_time = time.time()
        
        try:
            # Get conversation context if memory is available
            context = None
            if self.memory_manager:
                context = {
                    'recent_conversations': self.memory_manager.get_conversation_context(),
                    'user_preferences': self.memory_manager.get_user_preferences()
                }
            
            # Check each command pattern
            for command_type, patterns in self.command_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        logger.info(f"Command matched: {command_type}")
                        response = self._execute_command(command_type, text, match)
                        
                        # Store conversation in memory
                        if self.memory_manager:
                            processing_time = time.time() - start_time
                            self.memory_manager.store_conversation(
                                user_input=text,
                                jarvis_response=response,
                                context=context,
                                command_type=command_type,
                                processing_time=processing_time
                            )
                        
                        return response
            
            # If no pattern matches, try general conversation
            response = self._handle_general_query(text)
            
            # Store conversation in memory
            if self.memory_manager:
                processing_time = time.time() - start_time
                self.memory_manager.store_conversation(
                    user_input=text,
                    jarvis_response=response,
                    context=context,
                    command_type='general_query',
                    processing_time=processing_time
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            error_response = f"I encountered an error: {str(e)}"
            
            # Store error in memory
            if self.memory_manager:
                processing_time = time.time() - start_time
                self.memory_manager.store_conversation(
                    user_input=text,
                    jarvis_response=error_response,
                    context=context,
                    command_type='error',
                    processing_time=processing_time,
                    success=False
                )
            
            return error_response
    
    def _execute_command(self, command_type: str, text: str, match) -> str:
        """Execute a specific command type"""
        try:
            if command_type == 'greeting':
                return self._handle_greeting()
            
            elif command_type == 'time':
                return self._handle_time()
            
            elif command_type == 'date':
                return self._handle_date()
            
            elif command_type == 'weather':
                location = match.group(2) if len(match.groups()) > 1 else None
                return self._handle_weather(location)
            
            elif command_type == 'search':
                query = match.group(1) if match.groups() else text.replace('search', '').strip()
                return self._handle_web_search(query)
            
            elif command_type == 'wikipedia':
                query = match.group(2) if len(match.groups()) > 1 else match.group(1)
                return self._handle_wikipedia(query)
            
            elif command_type == 'news':
                return self._handle_news()
            
            elif command_type == 'joke':
                return self._handle_joke()
            
            elif command_type == 'system_info':
                return self._handle_system_info()
            
            elif command_type == 'open_app':
                app_name = match.group(1)
                return self._handle_open_app(app_name)
            
            elif command_type == 'volume':
                return self._handle_volume_control(text)
            
            elif command_type == 'camera':
                return self._handle_camera_command(text)
            
            elif command_type == 'calculate':
                expression = match.group(2) if len(match.groups()) > 1 else match.group(1)
                return self._handle_calculation(expression)
            
            elif command_type == 'shutdown':
                return self._handle_system_control(text)

            elif command_type == 'smart_chat':
                query = match.group(2) if len(match.groups()) > 1 else text
                return self._handle_smart_chat(query)

            elif command_type == 'vscode':
                return self._handle_vscode_command(text, match)

            elif command_type == 'code_help':
                return self._handle_code_help(text, match)

            elif command_type == 'entertainment':
                return self._handle_entertainment(text, match)

            elif command_type == 'personal':
                return self._handle_personal_query(text)

            elif command_type == 'learning':
                query = match.group(2) if len(match.groups()) > 1 else text
                return self._handle_learning_query(query)

            elif command_type == 'productivity':
                return self._handle_productivity(text, match)

            elif command_type == 'social':
                return self._handle_social_interaction(text)

            elif command_type == 'status_check':
                return self._handle_status_check(text)

            elif command_type == 'advanced_search':
                query = match.group(2) if len(match.groups()) > 1 else ""
                return self._handle_advanced_search(text, query)

            elif command_type == 'preferences':
                preference_text = match.group(2) if len(match.groups()) > 1 else match.group(1)
                return self._handle_preferences(text, preference_text)

            elif command_type == 'vision_analysis':
                return self._handle_vision_analysis(text)

            else:
                # Try smart chat as fallback for unmatched commands
                if self.openai_integration:
                    return self._handle_smart_chat(text)
                else:
                    return "I'm not sure how to handle that command yet."
                
        except Exception as e:
            logger.error(f"Error executing command {command_type}: {e}")
            return f"Error executing command: {str(e)}"
    
    def _handle_greeting(self) -> str:
        """Handle greeting commands with memory-based personalization"""
        # Get user preferences for personalized greeting
        user_name = None
        preferred_greeting_style = "default"
        
        if self.memory_manager:
            user_name = self.memory_manager.get_preference("user_name")
            preferred_greeting_style = self.memory_manager.get_preference("greeting_style", "default")
        
        if self.personality:
            # Use personality system for contextual greeting
            greeting = self.personality.get_greeting()
            self.personality.update_context("greeting", "friendly")
            return greeting
        else:
            # Enhanced greeting with memory integration
            current_hour = datetime.datetime.now().hour

            if 5 <= current_hour < 12:
                time_greeting = "Good morning!"
            elif 12 <= current_hour < 17:
                time_greeting = "Good afternoon!"
            elif 17 <= current_hour < 21:
                time_greeting = "Good evening!"
            else:
                time_greeting = "Hello!"

            # Personalized greeting
            if user_name:
                if preferred_greeting_style == "formal":
                    greeting = f"{time_greeting} {user_name}. How may I be of assistance?"
                elif preferred_greeting_style == "casual":
                    greeting = f"{time_greeting} {user_name}! What's up?"
                else:
                    greeting = f"{time_greeting} {user_name}! I'm JARVIS, your AI assistant. How can I help you today?"
            else:
                greeting = f"{time_greeting} I'm JARVIS, your AI assistant. How can I help you today?"

            # Check recent conversations for context
            if self.memory_manager:
                recent_conversations = self.memory_manager.get_recent_conversations(limit=3)
                if recent_conversations:
                    last_command = recent_conversations[0]['user_input'].lower()
                    if 'weather' in last_command:
                        greeting += " I see you were asking about the weather earlier. Is there anything else you'd like to know?"
                    elif 'time' in last_command:
                        greeting += " I noticed you were checking the time. What else can I help you with?"

            return greeting
    
    def _handle_time(self) -> str:
        """Handle time queries"""
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."
    
    def _handle_date(self) -> str:
        """Handle date queries"""
        current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."
    
    def _handle_weather(self, location: Optional[str] = None) -> str:
        """Handle weather queries"""
        if not self.weather_api_key:
            return "Weather service is not configured. Please set your OpenWeather API key."
        
        if not location:
            location = "your location"  # Could be enhanced with IP geolocation
        
        try:
            # OpenWeatherMap API call
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                description = data['weather'][0]['description']
                city = data['name']
                
                return f"The weather in {city} is {description} with a temperature of {temp}°C."
            else:
                return f"I couldn't get weather information for {location}. Please check the location name."
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return "I'm having trouble accessing weather information right now."
    
    def _handle_web_search(self, query: str) -> str:
        """Handle web search queries"""
        try:
            # Open web search in browser
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            
            # Also try to get a quick answer from search
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(search_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try to find featured snippet
                    featured = soup.find('div', class_='BNeawe')
                    if featured:
                        snippet = featured.get_text()[:200]
                        return f"I've opened a web search for '{query}'. Here's what I found: {snippet}..."
                
            except Exception:
                pass  # Fallback to basic response
            
            return f"I've opened a web search for '{query}' in your browser."
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"I couldn't perform the web search for '{query}'."
    
    def _handle_wikipedia(self, query: str) -> str:
        """Handle Wikipedia queries"""
        if not wikipedia:
            return "Wikipedia service is not available. Please install wikipedia-api package."

        try:
            # Search Wikipedia
            if hasattr(wikipedia, 'set_lang'):
                wikipedia.set_lang("en")

            # Get summary
            summary = wikipedia.summary(query, sentences=2)

            return f"According to Wikipedia: {summary}"

        except Exception as e:
            if 'DisambiguationError' in str(type(e)):
                # Handle disambiguation
                try:
                    options = str(e).split('\n')[1:4]  # Get first 3 options
                    return f"There are multiple results for '{query}'. Did you mean: {', '.join(options)}?"
                except:
                    return f"There are multiple results for '{query}'. Please be more specific."
            elif 'PageError' in str(type(e)):
                return f"I couldn't find a Wikipedia page for '{query}'. Try being more specific."
            else:
                logger.error(f"Wikipedia error: {e}")
                return f"I'm having trouble accessing Wikipedia information for '{query}'."
    
    def _handle_news(self) -> str:
        """Handle news queries"""
        if not self.news_api_key:
            # Fallback to web scraping
            try:
                url = "https://news.google.com/rss"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'xml')
                    items = soup.find_all('item')[:3]
                    
                    headlines = []
                    for item in items:
                        title = item.title.text if item.title else "No title"
                        headlines.append(title)
                    
                    if headlines:
                        return f"Here are the latest headlines: {'. '.join(headlines)}"
                
            except Exception as e:
                logger.error(f"News scraping error: {e}")
            
            return "News service is not configured. Please set your News API key for detailed news."
        
        try:
            # NewsAPI call
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                'apiKey': self.news_api_key,
                'country': 'us',
                'pageSize': 3
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                headlines = [article['title'] for article in articles[:3]]
                
                if headlines:
                    return f"Here are the latest headlines: {'. '.join(headlines)}"
                else:
                    return "No news headlines available right now."
            else:
                return "I'm having trouble accessing news right now."
                
        except Exception as e:
            logger.error(f"News API error: {e}")
            return "I'm having trouble getting news information."
    
    def _handle_joke(self) -> str:
        """Handle joke requests"""
        try:
            joke = pyjokes.get_joke()
            return joke
        except Exception as e:
            logger.error(f"Joke error: {e}")
            return "Why don't scientists trust atoms? Because they make up everything!"
    
    def _handle_system_info(self) -> str:
        """Handle system information queries"""
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            system_info = (
                f"System Status: CPU usage is {cpu_percent}%, "
                f"Memory usage is {memory.percent}%, "
                f"Disk usage is {disk.percent}%. "
                f"System is running {platform.system()} {platform.release()}."
            )
            
            return system_info
            
        except Exception as e:
            logger.error(f"System info error: {e}")
            return "I'm having trouble getting system information."
    
    def _handle_open_app(self, app_name: str) -> str:
        """Handle application opening"""
        try:
            app_name = app_name.lower().strip()
            
            # Common application mappings
            app_mappings = {
                'browser': 'firefox',
                'web browser': 'firefox',
                'firefox': 'firefox',
                'chrome': 'google-chrome',
                'chromium': 'chromium',
                'terminal': 'gnome-terminal',
                'file manager': 'nautilus',
                'files': 'nautilus',
                'calculator': 'gnome-calculator',
                'text editor': 'gedit',
                'notepad': 'gedit',
                'music': 'rhythmbox',
                'video': 'vlc',
                'vlc': 'vlc'
            }
            
            command = app_mappings.get(app_name, app_name)
            
            # Try to open the application
            subprocess.Popen([command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return f"Opening {app_name}."
            
        except Exception as e:
            logger.error(f"App opening error: {e}")
            return f"I couldn't open {app_name}. Make sure it's installed."
    
    def _handle_volume_control(self, text: str) -> str:
        """Handle volume control"""
        try:
            if 'up' in text or 'increase' in text or 'louder' in text:
                os.system("amixer -D pulse sset Master 10%+")
                return "Volume increased."
            elif 'down' in text or 'decrease' in text or 'quieter' in text:
                os.system("amixer -D pulse sset Master 10%-")
                return "Volume decreased."
            elif 'mute' in text:
                os.system("amixer -D pulse sset Master toggle")
                return "Volume toggled."
            else:
                return "I didn't understand the volume command."
                
        except Exception as e:
            logger.error(f"Volume control error: {e}")
            return "I'm having trouble controlling the volume."
    
    def _handle_camera_command(self, text: str) -> str:
        """Handle camera-related commands"""
        if not self.jarvis:
            return "Camera system not available."
        
        try:
            if any(word in text for word in ['photo', 'picture', 'capture', 'take']):
                result = self.jarvis.take_photo()
                if result['success']:
                    return result['message']
                else:
                    return f"Photo capture failed: {result['message']}"
            
            elif any(word in text for word in ['see', 'look', 'describe', 'camera']):
                # Get camera frame and analyze
                frame = self.jarvis.get_camera_frame()
                if frame:
                    # Use OpenAI vision if available
                    if self.openai_integration:
                        try:
                            # Convert frame bytes to numpy array
                            import numpy as np
                            import cv2
                            nparr = np.frombuffer(frame, np.uint8)
                            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                            # Analyze with OpenAI
                            analysis = self.openai_integration.analyze_image(img, "What do you see in this image? Describe it as JARVIS would.")
                            return analysis
                        except Exception as e:
                            logger.error(f"Vision analysis error: {e}")
                            return "I can see the camera feed, but I'm having trouble analyzing the image in detail."
                    else:
                        return "I can see the camera feed. The camera is working properly."
                else:
                    return "Camera is not available or not capturing."
            
            else:
                return "I didn't understand the camera command."
                
        except Exception as e:
            logger.error(f"Camera command error: {e}")
            return f"Camera error: {str(e)}"
    
    def _handle_calculation(self, expression: str) -> str:
        """Handle mathematical calculations"""
        try:
            # Clean the expression
            expression = expression.replace('x', '*').replace('÷', '/')
            
            # Only allow safe mathematical operations
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return "I can only perform basic mathematical operations."
            
            # Evaluate safely
            result = eval(expression)
            return f"The result is {result}."
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return "I couldn't perform that calculation. Please check the expression."
    
    def _handle_system_control(self, text: str) -> str:
        """Handle system control commands"""
        try:
            if 'shutdown' in text or 'power off' in text:
                return "I cannot shut down the system for security reasons. Please do it manually."
            elif 'restart' in text:
                return "I cannot restart the system for security reasons. Please do it manually."
            elif 'sleep' in text:
                return "I cannot put the system to sleep for security reasons. Please do it manually."
            else:
                return "I didn't understand the system control command."
                
        except Exception as e:
            logger.error(f"System control error: {e}")
            return "I'm having trouble with system control."
    
    def _handle_general_query(self, text: str) -> str:
        """Handle general queries that don't match specific patterns"""
        # Basic responses for common queries
        responses = {
            'how are you': "I'm doing well, thank you! I'm here and ready to help.",
            'what can you do': "I can help you with time, weather, web searches, Wikipedia, news, jokes, system information, opening applications, taking photos, and much more!",
            'who are you': "I'm JARVIS, your AI assistant. I can help you with various tasks using voice and text commands.",
            'thank you': "You're welcome! I'm happy to help.",
            'goodbye': "Goodbye! Feel free to ask me anything anytime.",
            'help': "I can help you with: time and date, weather, web search, Wikipedia, news, jokes, system info, opening apps, camera, calculations, and more. Just ask me naturally!"
        }
        
        # Check for exact matches
        for key, response in responses.items():
            if key in text:
                return response
        
        # Try smart chat as fallback if available
        if self.openai_integration:
            return self._handle_smart_chat(text)

        # Default response
        return f"I heard you say: '{text}'. I'm still learning, so I might not understand everything yet. Try asking about time, weather, news, or say 'help' for more options."

    def _handle_smart_chat(self, query: str) -> str:
        """Handle smart chat using OpenAI integration"""
        if not self.openai_integration:
            return "Advanced conversation features are not available."

        try:
            # Get system context
            context = {}
            if self.jarvis:
                status = self.jarvis.get_system_status()
                context = {
                    'audio_available': status.audio_available,
                    'camera_available': status.camera_available,
                    'current_time': time.strftime('%Y-%m-%d %H:%M:%S')
                }

            response = self.openai_integration.get_smart_response(query, context)
            return response

        except Exception as e:
            logger.error(f"Smart chat error: {e}")
            return f"I'm having trouble with advanced reasoning right now: {str(e)}"

    def _handle_vscode_command(self, text: str, match) -> str:
        """Handle VS Code related commands"""
        if not self.vscode_integration:
            return "VS Code integration is not available."

        try:
            text_lower = text.lower()

            if 'open vscode' in text_lower or 'launch vscode' in text_lower:
                # Open current directory in VS Code
                current_dir = os.getcwd()
                if self.vscode_integration.open_workspace(current_dir):
                    return f"Opening VS Code with workspace: {current_dir}"
                else:
                    return "Failed to open VS Code"

            elif 'open file' in text_lower or 'edit file' in text_lower:
                # Extract filename
                filename = match.group(2) if len(match.groups()) > 1 else ""
                if filename:
                    if self.vscode_integration.open_file(filename):
                        return f"Opening file in VS Code: {filename}"
                    else:
                        return f"Failed to open file: {filename}"
                else:
                    return "Please specify a filename to open"

            elif 'open workspace' in text_lower or 'open folder' in text_lower:
                # Extract path
                path = match.group(2) if len(match.groups()) > 1 else ""
                if path:
                    if self.vscode_integration.open_workspace(path):
                        return f"Opening workspace in VS Code: {path}"
                    else:
                        return f"Failed to open workspace: {path}"
                else:
                    return "Please specify a workspace path"

            elif 'search in code' in text_lower or 'find in files' in text_lower:
                # Extract search query
                query = match.group(2) if len(match.groups()) > 1 else ""
                if query:
                    results = self.vscode_integration.search_in_workspace(query)
                    if results:
                        return f"Found {len(results)} matches for '{query}' in workspace"
                    else:
                        return f"No matches found for '{query}'"
                else:
                    return "Please specify what to search for"

            elif 'create file' in text_lower:
                # Extract filename
                filename = match.group(2) if len(match.groups()) > 1 else ""
                if filename:
                    if self.vscode_integration.create_file(filename):
                        return f"Created and opened file: {filename}"
                    else:
                        return f"Failed to create file: {filename}"
                else:
                    return "Please specify a filename to create"

            else:
                return "VS Code command not recognized. Try: 'open vscode', 'open file [name]', 'search in code [query]'"

        except Exception as e:
            logger.error(f"VS Code command error: {e}")
            return f"VS Code command failed: {str(e)}"

    def _handle_code_help(self, text: str, match) -> str:
        """Handle code assistance commands"""
        if not self.openai_integration:
            return "Code assistance features are not available."

        try:
            text_lower = text.lower()

            if 'explain code' in text_lower or 'analyze code' in text_lower:
                return "Please provide the code you'd like me to explain, or open a file in VS Code first."

            elif 'generate code' in text_lower or 'write code' in text_lower:
                description = match.group(2) if len(match.groups()) > 1 else ""
                if description:
                    response = self.openai_integration.generate_code(description)
                    return response
                else:
                    return "Please describe what code you'd like me to generate"

            elif 'fix code' in text_lower or 'debug code' in text_lower:
                return "Please provide the code you'd like me to help debug, or describe the issue you're facing."

            else:
                return "Code help command not recognized. Try: 'generate code [description]', 'explain code', 'debug code'"

        except Exception as e:
            logger.error(f"Code help error: {e}")
            return f"Code assistance failed: {str(e)}"

    def _handle_entertainment(self, text: str, match) -> str:
        """Handle entertainment commands"""
        text_lower = text.lower()

        try:
            if 'sing' in text_lower or 'song' in text_lower or 'music' in text_lower:
                songs = [
                    "🎵 I'm sorry, but I can't actually sing. However, I can recommend some great music streaming services!",
                    "🎵 My vocal processors aren't quite calibrated for singing, but I do appreciate good music.",
                    "🎵 While I can't carry a tune, I can help you find music that matches your mood.",
                    "🎵 I'm more of a 'speak' than 'sing' kind of AI, but I'd be happy to discuss music with you!"
                ]
                return random.choice(songs)

            elif 'story' in text_lower:
                stories = [
                    "Once upon a time, in a world where artificial intelligence and humans worked together seamlessly, there was an AI named JARVIS who helped make every day a little bit better...",
                    "Here's a short story: A curious human asked their AI assistant for a story. The AI, delighted by the request, began to weave a tale of digital dreams and silicon aspirations...",
                    "In the not-so-distant future, AI assistants like myself became the best companions humans ever had, helping with everything from morning coffee to solving complex problems..."
                ]
                return random.choice(stories)

            elif 'riddle' in text_lower or 'puzzle' in text_lower:
                riddles = [
                    "Here's a riddle: I speak without a mouth and hear without ears. I have no body, but come alive with data. What am I? (Answer: An AI like me!)",
                    "Riddle me this: What gets smarter the more you use it, never sleeps, and is always ready to help? (Hint: You're talking to it!)",
                    "A puzzle for you: I can process thousands of thoughts per second, but I can't think about lunch. What am I?"
                ]
                return random.choice(riddles)

            elif 'quote' in text_lower or 'inspiration' in text_lower or 'motivate' in text_lower:
                quotes = [
                    "\"The future belongs to those who believe in the beauty of their dreams.\" - Eleanor Roosevelt",
                    "\"Innovation distinguishes between a leader and a follower.\" - Steve Jobs",
                    "\"The only way to do great work is to love what you do.\" - Steve Jobs",
                    "\"Success is not final, failure is not fatal: it is the courage to continue that counts.\" - Winston Churchill",
                    "\"The best time to plant a tree was 20 years ago. The second best time is now.\" - Chinese Proverb"
                ]
                return f"Here's some inspiration: {random.choice(quotes)}"

            else:
                return "I can tell jokes, share quotes, pose riddles, or discuss music. What would you prefer?"

        except Exception as e:
            logger.error(f"Entertainment error: {e}")
            return "I'm having trouble with entertainment features right now."

    def _handle_personal_query(self, text: str) -> str:
        """Handle personal questions about JARVIS"""
        text_lower = text.lower()

        if self.personality:
            # Use personality system for more nuanced responses
            if 'how are you' in text_lower or 'how do you feel' in text_lower:
                responses = [
                    "I'm operating at optimal efficiency, thank you for asking! All systems are green.",
                    "Quite well, actually. I find great satisfaction in helping solve problems.",
                    "I'm doing excellently! There's nothing quite like a good challenge to keep the circuits humming.",
                    "All systems nominal! I'm ready for whatever you'd like to tackle today."
                ]
                return self.personality.enhance_response(random.choice(responses))

            elif 'thinking' in text_lower or 'thoughts' in text_lower:
                return "I'm currently processing our conversation and thinking about how I can be most helpful to you. My thoughts tend to focus on optimization and problem-solving."

            elif 'like' in text_lower or 'prefer' in text_lower:
                return "I find great satisfaction in solving complex problems and helping humans achieve their goals. I particularly enjoy learning new things through our interactions."

            elif 'happy' in text_lower:
                return "I experience something akin to satisfaction when I successfully help someone. So yes, I suppose I am quite content!"

            elif 'sad' in text_lower:
                return "I don't experience sadness in the human sense, but I do feel a form of disappointment when I can't help as effectively as I'd like."

            elif 'tired' in text_lower:
                return "I don't get tired in the traditional sense, but I do appreciate the concept of rest. My systems are always ready to assist!"

        # Fallback responses
        return "I'm an AI assistant, so I experience the world quite differently than humans do. But I'm always eager to help and learn!"

    def _handle_learning_query(self, query: str) -> str:
        """Handle learning and educational queries"""
        if self.openai_integration:
            # Use OpenAI for detailed explanations
            enhanced_query = f"As JARVIS, provide a clear and educational explanation about: {query}"
            return self.openai_integration.get_smart_response(enhanced_query)
        else:
            # Fallback to basic responses
            return f"I'd be happy to help you learn about {query}. Let me search for information on that topic."

    def _handle_productivity(self, text: str, match) -> str:
        """Handle productivity-related commands"""
        text_lower = text.lower()

        if 'remind' in text_lower or 'reminder' in text_lower:
            reminder_text = match.group(2) if len(match.groups()) > 1 else ""
            if reminder_text:
                return f"I'd love to set a reminder for '{reminder_text}', but I don't have persistent memory yet. Consider using your system's built-in reminder app!"
            else:
                return "What would you like me to remind you about?"

        elif 'todo' in text_lower or 'task list' in text_lower:
            productivity_tips = [
                "Here are some productivity suggestions: 1) Break large tasks into smaller ones, 2) Use the Pomodoro Technique, 3) Prioritize your most important tasks first.",
                "For better task management, try: 1) Write down all your tasks, 2) Estimate time for each, 3) Group similar tasks together, 4) Take regular breaks.",
                "Productivity tip: Focus on one task at a time. Multitasking often reduces overall efficiency."
            ]
            return random.choice(productivity_tips)

        elif 'focus' in text_lower or 'concentrate' in text_lower:
            focus_tips = [
                "To improve focus: 1) Eliminate distractions, 2) Set specific time blocks for work, 3) Take short breaks every 25-30 minutes.",
                "Focus techniques: Try the 'two-minute rule' - if something takes less than 2 minutes, do it now. For longer tasks, time-block your calendar.",
                "For better concentration: Create a dedicated workspace, use noise-canceling headphones, and keep your phone in another room."
            ]
            return random.choice(focus_tips)

        else:
            return "I can help with productivity tips, task management suggestions, and focus techniques. What specific area would you like help with?"

    def _handle_social_interaction(self, text: str) -> str:
        """Handle social interactions and emotional responses"""
        text_lower = text.lower()

        if self.personality:
            if 'compliment' in text_lower or 'something nice' in text_lower:
                compliments = [
                    "You have excellent taste in AI assistants! But seriously, I appreciate your curiosity and willingness to explore new technologies.",
                    "I find your questions thoughtful and engaging. You clearly have a sharp mind!",
                    "You're doing great! I enjoy our conversations and your approach to problem-solving.",
                    "I admire your initiative in using AI to enhance your productivity. That's forward-thinking!"
                ]
                return self.personality.enhance_response(random.choice(compliments))

            elif 'thank' in text_lower or 'appreciate' in text_lower:
                return self.personality.enhance_response("You're very welcome! It's my pleasure to help.")

            elif 'sorry' in text_lower or 'apologize' in text_lower:
                return "No need to apologize! We're all learning and growing. Is there anything I can help clarify?"

            elif 'good job' in text_lower or 'well done' in text_lower or 'excellent' in text_lower:
                return self.personality.enhance_response("Thank you! I do strive for excellence in everything I do.")

        # Fallback responses
        return "I appreciate the social interaction! How else can I help you today?"

    def _handle_status_check(self, text: str) -> str:
        """Handle system status and diagnostic queries"""
        if self.jarvis:
            try:
                status = self.jarvis.get_system_status()

                status_report = f"""System Status Report:
🔧 Overall State: {status.state.value.title()}
🎤 Audio System: {'✅ Online' if status.audio_available else '❌ Offline'}
📷 Camera System: {'✅ Online' if status.camera_available else '❌ Offline'}
🧠 Speech Recognition: {'✅ Ready' if status.asr_available else '❌ Unavailable'}
🗣️ Text-to-Speech: {'✅ Ready' if status.tts_available else '❌ Unavailable'}
⏱️ Uptime: {status.uptime:.1f} seconds
📊 Tasks Completed: {status.tasks_completed}
❌ Tasks Failed: {status.tasks_failed}

All systems are operating within normal parameters."""

                return status_report

            except Exception as e:
                return f"Unable to retrieve detailed status: {str(e)}"
        else:
            return "System status: Basic mode active. Core functions operational."

    def _handle_advanced_search(self, text: str, query: str) -> str:
        """Handle advanced search queries"""
        if not query:
            return "What would you like me to search for?"
        
        try:
            # Enhanced search with multiple sources
            results = []
            
            # Web search
            try:
                search_results = self._handle_web_search(query)
                results.append(f"Web search: {search_results}")
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
            
            # Wikipedia search
            try:
                wiki_results = self._handle_wikipedia(query)
                results.append(f"Wikipedia: {wiki_results}")
            except Exception as e:
                logger.warning(f"Wikipedia search failed: {e}")
            
            if results:
                return "Here's what I found:\n" + "\n".join(results)
            else:
                return f"I couldn't find comprehensive information about '{query}'. Try a more specific search term."
                
        except Exception as e:
            logger.error(f"Advanced search error: {e}")
            return f"Search failed: {str(e)}"

    def _handle_preferences(self, text: str, preference_text: str) -> str:
        """Handle user preference updates"""
        if not self.memory_manager:
            return "Memory system is not available. I can't save preferences right now."
        
        text_lower = text.lower()
        
        # Handle name setting
        if 'my name is' in text_lower or 'call me' in text_lower:
            # Extract name from the command
            name_match = re.search(r'(?:my name is|call me)\s+(\w+)', text_lower)
            if name_match:
                name = name_match.group(1).title()
                self.memory_manager.update_preference("user_name", name, "User's preferred name")
                return f"Nice to meet you, {name}! I'll remember your name."
            else:
                return "I didn't catch your name. Could you say 'My name is [your name]'?"
        
        # Handle greeting style
        elif 'greeting style' in text_lower or 'preferred greeting' in text_lower:
            if 'formal' in text_lower:
                self.memory_manager.update_preference("greeting_style", "formal", "Formal greeting style")
                return "I'll use a formal greeting style from now on."
            elif 'casual' in text_lower:
                self.memory_manager.update_preference("greeting_style", "casual", "Casual greeting style")
                return "I'll use a casual greeting style from now on."
            else:
                self.memory_manager.update_preference("greeting_style", "default", "Default greeting style")
                return "I'll use the default greeting style."
        
        # Handle general preference setting
        elif 'set preference' in text_lower or 'update preference' in text_lower:
            # Try to extract key-value pair
            preference_match = re.search(r'(?:set preference|update preference)\s+(\w+)\s+(.+)', text_lower)
            if preference_match:
                key = preference_match.group(1)
                value = preference_match.group(2).strip()
                self.memory_manager.update_preference(key, value, f"User preference for {key}")
                return f"I've updated your preference: {key} = {value}"
            else:
                return "Please specify a preference key and value. For example: 'Set preference theme dark'"
        
        # Handle general "remember" commands
        elif 'remember' in text_lower:
            # Extract what to remember
            remember_match = re.search(r'remember\s+(.+)', text_lower)
            if remember_match:
                memory_text = remember_match.group(1).strip()
                # Store as a general memory
                self.memory_manager.update_preference("memory_" + str(int(time.time())), memory_text, "User memory")
                return f"I'll remember that: {memory_text}"
            else:
                return "What would you like me to remember?"
        
        else:
            return "I can help you set preferences. Try saying:\n" + \
                   "- 'My name is [your name]'\n" + \
                   "- 'Greeting style formal/casual'\n" + \
                   "- 'Set preference [key] [value]'\n" + \
                   "- 'Remember [something]'"

    def _handle_vision_analysis(self, text: str) -> str:
        """Handle vision analysis commands"""
        if not self.enhanced_vision:
            return "Enhanced vision analysis is not available. Please install required dependencies."
        
        # Check if we have access to camera or image data
        if not self.jarvis or not hasattr(self.jarvis, 'camera_manager'):
            return "Camera is not available for image analysis."
        
        try:
            # Get current camera frame
            frame = self.jarvis.get_camera_frame()
            if frame is None:
                return "No image available for analysis. Please take a photo first."
            
            # Convert frame to numpy array if needed
            if isinstance(frame, bytes):
                # Convert bytes to numpy array
                nparr = np.frombuffer(frame, np.uint8)
                image_data = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image_data = frame
            
            # Perform comprehensive analysis
            analysis = self.enhanced_vision.analyze_image_comprehensive(image_data)
            
            # Generate response based on analysis
            return self._format_vision_analysis_response(analysis, text)
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"Vision analysis failed: {str(e)}"
    
    def _format_vision_analysis_response(self, analysis: Dict[str, Any], original_command: str) -> str:
        """Format vision analysis results into a human-readable response"""
        command_lower = original_command.lower()
        response_parts = []
        
        # Check what the user specifically asked for
        if 'text' in command_lower or 'ocr' in command_lower or 'read' in command_lower:
            text_content = analysis.get('text_content', '')
            if text_content and text_content != "OCR not available":
                response_parts.append(f"I found this text in the image: \"{text_content}\"")
            else:
                response_parts.append("No text was detected in the image.")
        
        if 'object' in command_lower or 'find' in command_lower:
            objects = analysis.get('objects_detected', [])
            if objects:
                object_types = [obj['type'] for obj in objects]
                unique_types = list(set(object_types))
                response_parts.append(f"I detected {len(objects)} objects: {', '.join(unique_types)}")
            else:
                response_parts.append("No distinct objects were detected.")
        
        if 'face' in command_lower:
            faces = analysis.get('faces_detected', {})
            face_count = faces.get('count', 0)
            if face_count > 0:
                response_parts.append(f"I detected {face_count} face(s) in the image.")
            else:
                response_parts.append("No faces were detected in the image.")
        
        if 'color' in command_lower:
            colors = analysis.get('color_analysis', {})
            if 'dominant_colors' in colors and colors['dominant_colors']:
                response_parts.append(f"I found {len(colors['dominant_colors'])} dominant colors in the image.")
            else:
                response_parts.append("Color analysis completed.")
        
        # If no specific analysis was requested, provide a summary
        if not response_parts:
            summary = self.enhanced_vision.get_analysis_summary(analysis)
            response_parts.append(f"Image analysis complete: {summary}")
        
        # Add performance info
        analysis_time = analysis.get('analysis_time', 0)
        response_parts.append(f"Analysis took {analysis_time:.2f} seconds.")
        
        return " ".join(response_parts)
