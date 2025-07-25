import logging
import os

from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SIMPLE_TASK_MODEL = "gpt-4.1-mini"
REASONING_MODEL = "o4-mini"
model_clients = {}

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)


def create_model_client(model: str) -> AzureOpenAIChatCompletionClient:
    """Create or retrieve a model client for the specified model."""
    return AzureOpenAIChatCompletionClient(
        azure_deployment=os.getenv(
            f"AZURE_OPENAI_{''.join(c if c.isalnum() else '_' for c in model.upper())}_DEPLOYMENT",
            model,
        ),
        model=model,
        api_version=os.getenv("AZURE_OPENAI_APIVERSION", "2024-12-01-preview"),
        azure_endpoint=os.getenv(
            "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com"
        ),
        azure_ad_token_provider=token_provider,
    )
    global model_clients
    if model not in model_clients:
        model_clients[model] = AzureOpenAIChatCompletionClient(
            azure_deployment=os.getenv(
                f"AZURE_OPENAI_{''.join(c if c.isalnum() else '_' for c in model.upper())}_DEPLOYMENT",
                model,
            ),
            model=model,
            api_version=os.getenv("AZURE_OPENAI_APIVERSION", "2024-12-01-preview"),
            azure_endpoint=os.getenv(
                "AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com"
            ),
            azure_ad_token_provider=token_provider,
        )
    return model_clients[model]
