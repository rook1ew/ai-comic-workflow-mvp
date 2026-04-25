from app.models.enums import AssetModality
from app.providers.mock import MockImageProvider, MockMusicProvider, MockVideoProvider, MockVoiceProvider
from app.providers.stubs import Image2ProviderStub, SeedanceVideoProviderStub


def get_provider(modality: AssetModality, provider_name: str):
    if provider_name == "mock":
        mapping = {
            AssetModality.IMAGE: MockImageProvider(),
            AssetModality.VIDEO: MockVideoProvider(),
            AssetModality.VOICE: MockVoiceProvider(),
            AssetModality.BGM: MockMusicProvider(),
        }
        return mapping[modality]

    if provider_name == "image2_stub" and modality == AssetModality.IMAGE:
        return Image2ProviderStub()

    if provider_name == "seedance_video_stub" and modality == AssetModality.VIDEO:
        return SeedanceVideoProviderStub()

    raise ValueError(f"Unsupported provider: {provider_name}")
