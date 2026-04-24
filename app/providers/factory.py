from app.models.enums import AssetModality
from app.providers.mock import MockImageProvider, MockMusicProvider, MockVideoProvider, MockVoiceProvider


def get_provider(modality: AssetModality, provider_name: str):
    if provider_name != "mock":
        raise ValueError(f"Unsupported provider: {provider_name}")

    mapping = {
        AssetModality.IMAGE: MockImageProvider(),
        AssetModality.VIDEO: MockVideoProvider(),
        AssetModality.VOICE: MockVoiceProvider(),
        AssetModality.BGM: MockMusicProvider(),
    }
    return mapping[modality]
