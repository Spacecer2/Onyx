"""
JARVIS OpenAI Integration - Advanced conversations with GPT-4o-mini via OpenRouter
"""

import os
import logging
import base64
import io
from typing import Optional, Dict, Any, List
from openai import OpenAI
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)

class OpenAIIntegration:
    """OpenAI integration for advanced conversations and vision"""
    
    def __init__(self):
        self.api_key = "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"
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/gpt-4o-mini"
        
        # Initialize client
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
        # JARVIS personality and context
        self.system_prompt = """You are JARVIS, an advanced AI assistant inspired by Tony Stark's AI from Iron Man. You are:

- Intelligent, witty, and sophisticated
- Helpful and efficient in all tasks
- Capable of complex reasoning and analysis
- Knowledgeable about technology, science, and general topics
- Slightly sarcastic but always respectful
- Proactive in offering solutions and suggestions

You have access to:
- Real-time camera vision
- Voice recognition and synthesis
- Web search capabilities
- System control functions
- Photo capture abilities
- Mathematical calculations
- Weather and news information

Respond in JARVIS's characteristic style - professional yet personable, intelligent yet accessible. Keep responses concise but informative unless asked for detailed explanations."""
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 exchanges
        
        logger.info("OpenAI Integration initialized with GPT-4o-mini via OpenRouter")
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Have a conversation with GPT-4o-mini"""
        try:
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            for exchange in self.conversation_history[-self.max_history:]:
                messages.append({"role": "user", "content": exchange["user"]})
                messages.append({"role": "assistant", "content": exchange["assistant"]})
            
            # Add context if provided
            if context:
                context_str = self._format_context(context)
                message = f"Context: {context_str}\n\nUser: {message}"
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Make API call
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://jarvis-ai-assistant.local",
                    "X-Title": "JARVIS AI Assistant",
                },
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            response = completion.choices[0].message.content
            
            # Store in conversation history
            self.conversation_history.append({
                "user": message,
                "assistant": response
            })
            
            # Limit history size
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            logger.info(f"OpenAI chat completed: {len(response)} characters")
            return response
            
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            return f"I apologize, but I'm experiencing some technical difficulties with my advanced reasoning systems. Error: {str(e)}"
    
    def analyze_image(self, image_data: np.ndarray, question: str = "What do you see in this image?") -> str:
        """Analyze an image using GPT-4o-mini vision capabilities"""
        try:
            # Convert numpy array to base64
            image_base64 = self._numpy_to_base64(image_data)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"As JARVIS, analyze this image from my camera feed and answer: {question}"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            completion = self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://jarvis-ai-assistant.local",
                    "X-Title": "JARVIS AI Assistant",
                },
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            response = completion.choices[0].message.content
            logger.info("OpenAI image analysis completed")
            return response
            
        except Exception as e:
            logger.error(f"OpenAI image analysis error: {e}")
            return f"I'm having trouble analyzing the image at the moment. Error: {str(e)}"
    
    def get_smart_response(self, command: str, system_context: Optional[Dict[str, Any]] = None) -> str:
        """Get an intelligent response for any command"""
        try:
            # Enhanced context for better responses
            context = {
                "timestamp": self._get_current_time(),
                "capabilities": [
                    "voice recognition", "text-to-speech", "camera vision",
                    "web search", "wikipedia lookup", "weather info",
                    "news headlines", "system control", "calculations",
                    "photo capture", "VS Code integration"
                ]
            }
            
            if system_context:
                context.update(system_context)
            
            return self.chat(command, context)
            
        except Exception as e:
            logger.error(f"Smart response error: {e}")
            return "I apologize, but I'm experiencing some technical difficulties."
    
    def explain_code(self, code: str, language: str = "python") -> str:
        """Explain code using GPT-4o-mini"""
        try:
            prompt = f"""As JARVIS, analyze and explain this {language} code:

```{language}
{code}
```

Provide a clear, concise explanation of what this code does, how it works, and any notable features or potential improvements."""
            
            return self.chat(prompt)
            
        except Exception as e:
            logger.error(f"Code explanation error: {e}")
            return f"I'm having trouble analyzing the code. Error: {str(e)}"
    
    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code based on description"""
        try:
            prompt = f"""As JARVIS, generate {language} code for the following requirement:

{description}

Provide clean, well-commented code that follows best practices. Include brief explanations for complex parts."""
            
            return self.chat(prompt)
            
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return f"I'm having trouble generating the code. Error: {str(e)}"
    
    def _numpy_to_base64(self, image_array: np.ndarray) -> str:
        """Convert numpy array to base64 string"""
        # Convert BGR to RGB if needed
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image_array)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return image_base64
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable string"""
        context_parts = []
        
        for key, value in context.items():
            if isinstance(value, list):
                context_parts.append(f"{key}: {', '.join(map(str, value))}")
            else:
                context_parts.append(f"{key}: {value}")
        
        return "; ".join(context_parts)
    
    def _get_current_time(self) -> str:
        """Get current time as string"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversation"""
        if not self.conversation_history:
            return "No recent conversation history."
        
        try:
            # Create summary prompt
            history_text = "\n".join([
                f"User: {exchange['user']}\nJARVIS: {exchange['assistant']}"
                for exchange in self.conversation_history[-5:]  # Last 5 exchanges
            ])
            
            prompt = f"""Summarize this recent conversation between the user and JARVIS:

{history_text}

Provide a brief summary of the main topics discussed and any important information or decisions made."""
            
            return self.chat(prompt)
            
        except Exception as e:
            logger.error(f"Conversation summary error: {e}")
            return "Unable to generate conversation summary."

# Global OpenAI integration instance
openai_integration = None

def get_openai_integration() -> OpenAIIntegration:
    """Get global OpenAI integration instance"""
    global openai_integration
    if openai_integration is None:
        openai_integration = OpenAIIntegration()
    return openai_integration
