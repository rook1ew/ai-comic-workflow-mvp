from app.models.enums import AssetModality
from app.core.config import get_settings
from app.providers.base import ProviderExecutionError
from app.providers.mock import MockImageProvider, MockMusicProvider, MockVideoProvider, MockVoiceProvider
from app.providers.stubs import Image2ProviderStub, SeedanceVideoProviderStub


def get_provider(modality: AssetModality, provider_name: str):
    settings = get_settings()

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

    if provider_name == "image2_real" and modality == AssetModality.IMAGE:
        if not settings.enable_real_image_provider:
            raise ProviderExecutionError(
                "Real Image2 provider is disabled. Set ENABLE_REAL_IMAGE_PROVIDER=true before using provider_name=image2_real."
            )
        if not settings.image2_api_key.strip():
            raise ProviderExecutionError(
                "IMAGE2_API_KEY is required before using provider_name=image2_real."
            )
        if settings.image_provider_mode != "image2_real":
            raise ProviderExecutionError(
                "IMAGE_PROVIDER_MODE must be image2_real before using provider_name=image2_real."
            )
        raise ProviderExecutionError(
            "Real Image2 provider is not implemented in v0.3-A. Use mock or image2_stub."
        )

    if provider_name == "seedance_video_stub" and modality == AssetModality.VIDEO:
        return SeedanceVideoProviderStub()

    raise ValueError(f"Unsupported provider: {provider_name}")
