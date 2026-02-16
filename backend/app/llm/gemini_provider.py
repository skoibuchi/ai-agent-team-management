"""
Google Gemini LLM Provider
"""
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from .base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro", **kwargs):
        """
        Initialize Gemini provider
        
        Args:
            api_key: Google API key
            model: Model name (gemini-pro, gemini-pro-vision, etc.)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)
        
        # Configure Gemini
        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client"""
        try:
            generation_config = {
                "temperature": self.config.get("temperature", 0.7),
                "top_p": self.config.get("top_p", 0.95),
                "top_k": self.config.get("top_k", 40),
                "max_output_tokens": self.config.get("max_tokens", 2048),
            }
            
            safety_settings = self.config.get("safety_settings", [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
            ])
            
            self.client = genai.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini client: {str(e)}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Gemini
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self.client:
            raise Exception("Gemini client not initialized")
        
        try:
            # Override config with kwargs
            generation_config = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            if "top_p" in kwargs:
                generation_config["top_p"] = kwargs["top_p"]
            
            # Generate response
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config if generation_config else None
            )
            
            # Extract text from response
            if response.text:
                return response.text
            else:
                # Handle blocked responses
                if response.prompt_feedback:
                    raise Exception(f"Content blocked: {response.prompt_feedback}")
                raise Exception("No text generated")
                
        except Exception as e:
            raise Exception(f"Gemini generation failed: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Chat with Gemini
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response
        """
        if not self.client:
            raise Exception("Gemini client not initialized")
        
        try:
            # Start chat session
            chat = self.client.start_chat(history=[])
            
            # Convert messages to Gemini format and send
            for msg in messages[:-1]:  # All but last message as history
                role = "user" if msg["role"] in ["user", "system"] else "model"
                chat.history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
            
            # Send last message
            last_message = messages[-1]["content"]
            
            # Override config with kwargs
            generation_config = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            
            response = chat.send_message(
                last_message,
                generation_config=generation_config if generation_config else None
            )
            
            if response.text:
                return response.text
            else:
                if response.prompt_feedback:
                    raise Exception(f"Content blocked: {response.prompt_feedback}")
                raise Exception("No text generated")
                
        except Exception as e:
            raise Exception(f"Gemini chat failed: {str(e)}")
    
    def stream_generate(self, prompt: str, **kwargs):
        """
        Stream generate text using Gemini
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Yields:
            Text chunks
        """
        if not self.client:
            raise Exception("Gemini client not initialized")
        
        try:
            generation_config = {}
            if "temperature" in kwargs:
                generation_config["temperature"] = kwargs["temperature"]
            if "max_tokens" in kwargs:
                generation_config["max_output_tokens"] = kwargs["max_tokens"]
            
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config if generation_config else None,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise Exception(f"Gemini streaming failed: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test Gemini API connection
        
        Returns:
            Dict with success status and message
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "message": "API key not configured"
                }
            
            # Try a simple generation
            response = self.generate("Hello", max_tokens=10)
            
            return {
                "success": True,
                "message": "Connection successful",
                "model": self.model,
                "response_preview": response[:50] if response else None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}"
            }
    
    def estimate_cost(self, prompt: str, max_tokens: int = 1000) -> float:
        """
        Estimate cost for Gemini API call
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Estimated cost in USD
        """
        # Gemini pricing (as of 2024)
        # Gemini Pro: $0.00025 per 1K characters input, $0.0005 per 1K characters output
        # Gemini Pro Vision: $0.00025 per 1K characters input, $0.0005 per 1K characters output
        
        input_chars = len(prompt)
        output_chars = max_tokens * 4  # Rough estimate: 1 token ≈ 4 characters
        
        if "vision" in self.model.lower():
            # Vision model pricing
            input_cost = (input_chars / 1000) * 0.00025
            output_cost = (output_chars / 1000) * 0.0005
        else:
            # Standard model pricing
            input_cost = (input_chars / 1000) * 0.00025
            output_cost = (output_chars / 1000) * 0.0005
        
        return input_cost + output_cost
