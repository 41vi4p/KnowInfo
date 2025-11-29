"""
Multi-model manager supporting Gemini, Ollama, and other LLMs
"""
import structlog
from typing import Optional, List, Dict, Any
import asyncio
from enum import Enum
import re

logger = structlog.get_logger(__name__)


def clean_llm_response(text: str) -> str:
    """
    Clean LLM response by removing thinking blocks and extra whitespace.
    Removes content between <think> and </think> tags.
    """
    # Remove <think>...</think> blocks (case insensitive, handles multiline)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Remove any remaining think tags
    text = re.sub(r'</?think>', '', text, flags=re.IGNORECASE)
    # Clean up extra whitespace
    text = text.strip()
    return text


class ModelProvider(str, Enum):
    """Available model providers"""
    OLLAMA = "ollama"
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ModelManager:
    """Manages multiple LLM providers with fallback support"""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        use_local_first: bool = True
    ):
        self.ollama_base_url = ollama_base_url
        self.gemini_api_key = gemini_api_key
        self.openai_api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        self.use_local_first = use_local_first

        # Initialize clients
        self.ollama_client = None
        self.gemini_client = None
        self.openai_client = None
        self.anthropic_client = None

        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize available model clients"""
        # Ollama (local)
        try:
            import ollama
            self.ollama_client = ollama.AsyncClient(host=self.ollama_base_url)
            logger.info("Ollama client initialized", base_url=self.ollama_base_url)
        except ImportError:
            logger.warning("Ollama not available - install with: pip install ollama")

        # Gemini
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai
                logger.info("Gemini client initialized")
            except ImportError:
                logger.warning("Gemini not available - install with: pip install google-generativeai")

        # OpenAI
        if self.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI not available - install with: pip install openai")

        # Anthropic
        if self.anthropic_api_key:
            try:
                from anthropic import AsyncAnthropic
                self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("Anthropic not available - install with: pip install anthropic")

    async def generate_text(
        self,
        prompt: str,
        model: str = "qwen3",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        preferred_provider: Optional[ModelProvider] = None
    ) -> str:
        """
        Generate text using available models with automatic fallback
        """
        providers = self._get_provider_priority(preferred_provider)

        for provider in providers:
            try:
                if provider == ModelProvider.OLLAMA and self.ollama_client:
                    return await self._generate_ollama(prompt, model, temperature, max_tokens)
                elif provider == ModelProvider.GEMINI and self.gemini_client:
                    return await self._generate_gemini(prompt, temperature, max_tokens)
                elif provider == ModelProvider.OPENAI and self.openai_client:
                    return await self._generate_openai(prompt, model, temperature, max_tokens)
                elif provider == ModelProvider.ANTHROPIC and self.anthropic_client:
                    return await self._generate_anthropic(prompt, temperature, max_tokens)
            except Exception as e:
                logger.warning(
                    f"Failed to generate with {provider}",
                    error=str(e),
                    prompt_preview=prompt[:100]
                )
                continue

        raise RuntimeError("All model providers failed")

    async def _generate_ollama(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using Ollama"""
        response = await self.ollama_client.generate(
            model=model,
            prompt=prompt,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        logger.info("Generated with Ollama", model=model)
        return clean_llm_response(response['response'])

    async def _generate_gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using Gemini"""
        model = self.gemini_client.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        logger.info("Generated with Gemini")
        return clean_llm_response(response.text)

    async def _generate_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using OpenAI"""
        response = await self.openai_client.chat.completions.create(
            model=model if model.startswith("gpt") else "gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        logger.info("Generated with OpenAI", model=model)
        return clean_llm_response(response.choices[0].message.content)

    async def _generate_anthropic(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate text using Anthropic"""
        response = await self.anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Generated with Anthropic")
        return clean_llm_response(response.content[0].text)

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "nomic-embed-text"
    ) -> List[List[float]]:
        """
        Generate embeddings for text using available models
        """
        # Try Ollama first (free, local)
        if self.ollama_client:
            try:
                embeddings = []
                for text in texts:
                    response = await self.ollama_client.embeddings(
                        model=model,
                        prompt=text
                    )
                    embeddings.append(response['embedding'])
                logger.info("Generated embeddings with Ollama", count=len(texts))
                return embeddings
            except Exception as e:
                logger.warning("Ollama embeddings failed", error=str(e))

        # Fallback to OpenAI
        if self.openai_client:
            try:
                response = await self.openai_client.embeddings.create(
                    input=texts,
                    model="text-embedding-3-small"
                )
                embeddings = [item.embedding for item in response.data]
                logger.info("Generated embeddings with OpenAI", count=len(texts))
                return embeddings
            except Exception as e:
                logger.warning("OpenAI embeddings failed", error=str(e))

        raise RuntimeError("No embedding model available")

    async def classify_text(
        self,
        text: str,
        categories: List[str],
        model: str = "qwen3"
    ) -> Dict[str, float]:
        """
        Classify text into categories
        Returns dict of category: confidence_score
        """
        prompt = f"""Classify the following text into these categories: {', '.join(categories)}

Text: {text}

For each category, provide a confidence score between 0 and 1.
Respond in JSON format: {{"category_name": confidence_score}}"""

        response = await self.generate_text(
            prompt=prompt,
            model=model,
            temperature=0.3
        )

        # Parse JSON response
        try:
            import json
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except Exception as e:
            logger.error("Failed to parse classification response", error=str(e))
            # Return uniform distribution as fallback
            return {cat: 1.0 / len(categories) for cat in categories}

    async def extract_entities(
        self,
        text: str,
        model: str = "qwen3"
    ) -> List[Dict[str, str]]:
        """
        Extract named entities from text
        Returns list of {entity: text, type: entity_type}
        """
        prompt = f"""Extract all named entities from the following text.
For each entity, identify its type (PERSON, ORGANIZATION, LOCATION, DATE, etc.)

Text: {text}

Respond in JSON format: [{{"entity": "entity_text", "type": "entity_type"}}]"""

        response = await self.generate_text(
            prompt=prompt,
            model=model,
            temperature=0.2
        )

        try:
            import json
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except Exception as e:
            logger.error("Failed to parse entities", error=str(e))
            return []

    def _get_provider_priority(
        self,
        preferred: Optional[ModelProvider] = None
    ) -> List[ModelProvider]:
        """Get list of providers in priority order"""
        if preferred:
            # Put preferred first, then others
            providers = [preferred]
            for p in ModelProvider:
                if p != preferred:
                    providers.append(p)
            return providers

        if self.use_local_first:
            # Try local (Ollama) first, then APIs
            return [
                ModelProvider.OLLAMA,
                ModelProvider.GEMINI,
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC
            ]
        else:
            # Try APIs first
            return [
                ModelProvider.GEMINI,
                ModelProvider.OPENAI,
                ModelProvider.ANTHROPIC,
                ModelProvider.OLLAMA
            ]


# Global instance
model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get model manager instance"""
    global model_manager
    if model_manager is None:
        raise RuntimeError("Model manager not initialized")
    return model_manager


def init_model_manager(
    ollama_base_url: str,
    gemini_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    use_local_first: bool = True
):
    """Initialize model manager"""
    global model_manager
    model_manager = ModelManager(
        ollama_base_url=ollama_base_url,
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        use_local_first=use_local_first
    )
    logger.info("Model manager initialized")
