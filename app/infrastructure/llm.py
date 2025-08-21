from typing import Optional, Dict, Any, Union
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)

# Type alias for model clients
ModelClient = Any

class LLMInterface(ABC):
    """Abstract interface for LLM model clients."""
    
    @abstractmethod
    async def create(self, messages: list) -> Any:
        """Create a completion from messages."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the client connection."""
        pass

class OpenAIClient(LLMInterface):
    """OpenAI model client wrapper."""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            
            self.client = OpenAIChatCompletionClient(
                model=self.model,
                api_key=self.api_key,  # Optional if OPENAI_API_KEY env var is set
            )
            logger.info("OpenAI client initialized", model=self.model)
        except ImportError:
            logger.error("autogen-ext[openai] not installed. Run: pip install 'autogen-ext[openai]'")
            raise
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
            raise
    
    async def create(self, messages: list) -> Any:
        """Create completion using OpenAI client."""
        if not self.client:
            await self.initialize()
        return await self.client.create(messages)
    
    async def close(self) -> None:
        """Close OpenAI client."""
        if self.client:
            await self.client.close()

class AzureOpenAIClient(LLMInterface):
    """Azure OpenAI model client wrapper."""
    
    def __init__(
        self, 
        model: str, 
        azure_deployment: str,
        azure_endpoint: str,
        api_version: str = "2024-06-01",
        api_key: Optional[str] = None,
        use_aad_auth: bool = False
    ):
        self.model = model
        self.azure_deployment = azure_deployment
        self.azure_endpoint = azure_endpoint
        self.api_version = api_version
        self.api_key = api_key
        self.use_aad_auth = use_aad_auth
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the Azure OpenAI client."""
        try:
            from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
            
            kwargs = {
                "azure_deployment": self.azure_deployment,
                "model": self.model,
                "api_version": self.api_version,
                "azure_endpoint": self.azure_endpoint,
            }
            
            if self.use_aad_auth:
                from autogen_ext.auth.azure import AzureTokenProvider
                # from azure.identity import DefaultAzureCredential
                
                token_provider = AzureTokenProvider(
                    DefaultAzureCredential(),
                    "https://cognitiveservices.azure.com/.default",
                )
                kwargs["azure_ad_token_provider"] = token_provider
            else:
                kwargs["api_key"] = self.api_key
            
            self.client = AzureOpenAIChatCompletionClient(**kwargs)
            logger.info("Azure OpenAI client initialized", model=self.model, deployment=self.azure_deployment)
        except ImportError:
            logger.error("autogen-ext[openai,azure] not installed. Run: pip install 'autogen-ext[openai,azure]'")
            raise
        except Exception as e:
            logger.error("Failed to initialize Azure OpenAI client", error=str(e))
            raise
    
    async def create(self, messages: list) -> Any:
        """Create completion using Azure OpenAI client."""
        if not self.client:
            await self.initialize()
        return await self.client.create(messages)
    
    async def close(self) -> None:
        """Close Azure OpenAI client."""
        if self.client:
            await self.client.close()

class AnthropicClient(LLMInterface):
    """Anthropic model client wrapper."""
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        try:
            from autogen_ext.models.anthropic import AnthropicChatCompletionClient
            
            self.client = AnthropicChatCompletionClient(
                model=self.model,
                api_key=self.api_key,  # Optional if ANTHROPIC_API_KEY env var is set
            )
            logger.info("Anthropic client initialized", model=self.model)
        except ImportError:
            logger.error("autogen-ext[anthropic] not installed. Run: pip install 'autogen-ext[anthropic]'")
            raise
        except Exception as e:
            logger.error("Failed to initialize Anthropic client", error=str(e))
            raise
    
    async def create(self, messages: list) -> Any:
        """Create completion using Anthropic client."""
        if not self.client:
            await self.initialize()
        return await self.client.create(messages)
    
    async def close(self) -> None:
        """Close Anthropic client."""
        if self.client:
            await self.client.close()

class GeminiClient(LLMInterface):
    """Gemini model client wrapper (using OpenAI-compatible API)."""
    
    def __init__(
        self, 
        model: str, 
        api_key: Optional[str] = None,
        model_capabilities: Optional[Dict[str, Any]] = None
    ):
        self.model = model
        self.api_key = api_key
        self.model_capabilities = model_capabilities or {}
        self.client = None
        
    async def initialize(self) -> None:
        """Initialize the Gemini client using OpenAI-compatible API."""
        try:
            from autogen_ext.models.openai import OpenAIChatCompletionClient
            from autogen_core.models import ModelInfo
            
            kwargs = {
                "model": self.model,
                "api_key": self.api_key,  # Optional if GEMINI_API_KEY env var is set
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            }
            
            # Add model capabilities if provided
            if self.model_capabilities:
                model_info = ModelInfo(
                    vision=self.model_capabilities.get("vision", True),
                    function_calling=self.model_capabilities.get("function_calling", True),
                    json_output=self.model_capabilities.get("json_output", True),
                    family="gemini",
                    structured_output=self.model_capabilities.get("structured_output", True)
                )
                kwargs["model_info"] = model_info
            
            self.client = OpenAIChatCompletionClient(**kwargs)
            logger.info("Gemini client initialized", model=self.model)
        except ImportError:
            logger.error("autogen-ext[openai] not installed. Run: pip install 'autogen-ext[openai]'")
            raise
        except Exception as e:
            logger.error("Failed to initialize Gemini client", error=str(e))
            raise
    
    async def create(self, messages: list) -> Any:
        """Create completion using Gemini client."""
        if not self.client:
            await self.initialize()
        return await self.client.create(messages)
    
    async def close(self) -> None:
        """Close Gemini client."""
        if self.client:
            await self.client.close()

class LLMManager:
    """Manager for different LLM model clients."""
    
    def __init__(self):
        self.clients: Dict[str, LLMInterface] = {}
        self.active_client: Optional[str] = None
    
    async def add_openai_client(
        self, 
        name: str, 
        model: str, 
        api_key: Optional[str] = None
    ) -> None:
        """Add OpenAI client."""
        client = OpenAIClient(model=model, api_key=api_key)
        await client.initialize()
        self.clients[name] = client
        logger.info("Added OpenAI client", name=name, model=model)
    
    async def add_azure_openai_client(
        self,
        name: str,
        model: str,
        azure_deployment: str,
        azure_endpoint: str,
        api_version: str = "2024-06-01",
        api_key: Optional[str] = None,
        use_aad_auth: bool = False
    ) -> None:
        """Add Azure OpenAI client."""
        client = AzureOpenAIClient(
            model=model,
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            api_key=api_key,
            use_aad_auth=use_aad_auth
        )
        await client.initialize()
        self.clients[name] = client
        logger.info("Added Azure OpenAI client", name=name, model=model, deployment=azure_deployment)
    
    async def add_anthropic_client(
        self, 
        name: str, 
        model: str, 
        api_key: Optional[str] = None
    ) -> None:
        """Add Anthropic client."""
        client = AnthropicClient(model=model, api_key=api_key)
        await client.initialize()
        self.clients[name] = client
        logger.info("Added Anthropic client", name=name, model=model)
    
    async def add_gemini_client(
        self, 
        name: str, 
        model: str, 
        api_key: Optional[str] = None,
        model_capabilities: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add Gemini client."""
        client = GeminiClient(
            model=model, 
            api_key=api_key, 
            model_capabilities=model_capabilities
        )
        await client.initialize()
        self.clients[name] = client
        logger.info("Added Gemini client", name=name, model=model)
    
    def set_active_client(self, name: str) -> None:
        """Set the active client."""
        if name not in self.clients:
            raise ValueError(f"Client '{name}' not found. Available clients: {list(self.clients.keys())}")
        self.active_client = name
        logger.info("Set active client", client=name)
    
    def get_client(self, name: Optional[str] = None) -> LLMInterface:
        """Get a client by name, or the active client if no name provided."""
        client_name = name or self.active_client
        if not client_name:
            raise ValueError("No client name provided and no active client set")
        if client_name not in self.clients:
            raise ValueError(f"Client '{client_name}' not found. Available clients: {list(self.clients.keys())}")
        return self.clients[client_name]
    
    async def create_completion(
        self, 
        messages: list, 
        client_name: Optional[str] = None
    ) -> Any:
        """Create completion using specified or active client."""
        client = self.get_client(client_name)
        return await client.create(messages)
    
    async def shutdown(self) -> None:
        """Close all clients."""
        for name, client in self.clients.items():
            try:
                await client.close()
                logger.info("Closed client", name=name)
            except Exception as e:
                logger.warning("Failed to close client", name=name, error=str(e))
        self.clients.clear()
        self.active_client = None
        logger.info("All LLM clients shut down")

# Global LLM manager instance
llm_manager = LLMManager()

async def initialize_llm_clients() -> LLMManager:
    """Initialize LLM clients based on settings configuration."""
    from app.core.config import settings
    
    try:
        provider = settings.llm_provider.lower()
        
        if provider == "openai":
            await llm_manager.add_openai_client(
                name="default",
                model=settings.openai_model,
                api_key=str(settings.openai_api_key.get_secret_value()) if settings.openai_api_key else None
            )
            llm_manager.set_active_client("default")
            
        elif provider == "azure":
            if not settings.azure_openai_endpoint or not settings.azure_openai_deployment:
                raise ValueError("Azure endpoint and deployment are required for Azure OpenAI")
            await llm_manager.add_azure_openai_client(
                name="default",
                model=settings.azure_openai_model,
                azure_deployment=settings.azure_openai_deployment,
                azure_endpoint=settings.azure_openai_endpoint,
                api_version=settings.azure_openai_api_version,
                api_key=str(settings.azure_openai_api_key.get_secret_value()) if settings.azure_openai_api_key else None
            )
            llm_manager.set_active_client("default")
            
        elif provider == "anthropic":
            await llm_manager.add_anthropic_client(
                name="default",
                model=settings.anthropic_model,
                api_key=str(settings.anthropic_api_key.get_secret_value()) if settings.anthropic_api_key else None
            )
            llm_manager.set_active_client("default")
            
        elif provider == "gemini":
            await llm_manager.add_gemini_client(
                name="default",
                model=settings.gemini_model,
                api_key=str(settings.gemini_api_key.get_secret_value()) if settings.gemini_api_key else None
            )
            llm_manager.set_active_client("default")
            
        else:
            raise ValueError(f"Unsupported provider: {provider}. Supported: openai, azure, anthropic, gemini")
        
        logger.info("LLM clients initialized successfully", provider=provider)
        return llm_manager
        
    except Exception as e:
        logger.error("Failed to initialize LLM clients", provider=settings.llm_provider, error=str(e))
        raise