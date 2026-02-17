import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Any

load_dotenv()

# Load model configurations from YAML
CONFIG_PATH = Path(__file__).parent / "models.yml"
with open(CONFIG_PATH, 'r') as f:
    MODEL_CONFIG = yaml.safe_load(f)

DEFAULT_PROVIDER = os.environ.get("GENERATIVE_MODEL_PROVIDER", MODEL_CONFIG.get("default_provider", "bedrock"))


def create_model(provider: str = DEFAULT_PROVIDER) -> Any:
    """Create and return a language model instance based on the provider.
    
    Args:
        provider: Provider name (bedrock, openai, anthropic, gemini)
        
    Returns:
        Configured language model instance
    """
    provider_config = MODEL_CONFIG.get("providers", {}).get(provider)
    if not provider_config:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(MODEL_CONFIG.get('providers', {}).keys())}")
    
    if provider == "bedrock":
        import boto3
        from botocore.config import Config
        from langchain_aws import ChatBedrock
        
        region = os.environ.get(provider_config.get("region_env"))
        model_id = os.environ.get(provider_config.get("model_id_env"))
        
        if not region or not model_id:
            raise ValueError(f"Missing env vars for bedrock: {provider_config.get('region_env')}, {provider_config.get('model_id_env')}")
        
        boto3_client = boto3.client(
            service_name=provider_config.get("service_name"),
            region_name=region,
            config=Config(
                connect_timeout=20,
                read_timeout=500,
                retries={"max_attempts": 8, "mode": "adaptive"}
            )
        )
        
        return ChatBedrock(
            client=boto3_client,
            model_id=model_id,
            model_kwargs=provider_config.get("model_kwargs", {}),
            provider=provider_config.get("provider")
        )
    
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        
        api_key = os.environ.get(provider_config.get("api_key_env"))
        model = os.environ.get(provider_config.get("model_env"))
        
        if not api_key or not model:
            raise ValueError(f"Missing env vars for openai: {provider_config.get('api_key_env')}, {provider_config.get('model_env')}")
        
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            **provider_config.get("model_kwargs", {})
        )
    
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        
        api_key = os.environ.get(provider_config.get("api_key_env"))
        model = os.environ.get(provider_config.get("model_env"))
        
        if not api_key or not model:
            raise ValueError(f"Missing env vars for anthropic: {provider_config.get('api_key_env')}, {provider_config.get('model_env')}")
        
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            **provider_config.get("model_kwargs", {})
        )
    
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        api_key = os.environ.get(provider_config.get("api_key_env"))
        model = os.environ.get(provider_config.get("model_env"))
        
        if not api_key or not model:
            raise ValueError(f"Missing env vars for gemini: {provider_config.get('api_key_env')}, {provider_config.get('model_env')}")
        
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            **provider_config.get("model_kwargs", {})
        )
    
    else:
        raise ValueError(f"Provider '{provider}' not implemented yet.")


# Instantiate model based on default/env provider
try:
    model = create_model(DEFAULT_PROVIDER)
    print(f"✓ Loaded model from provider: {DEFAULT_PROVIDER}")
except Exception as e:
    print(f"✗ Failed to load model from provider '{DEFAULT_PROVIDER}': {e}")
    raise