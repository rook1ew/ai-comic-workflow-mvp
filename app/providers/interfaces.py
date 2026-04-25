from app.providers.base import BaseProvider
from app.providers.schemas import ImageProviderInput, ProviderRequest, ProviderResponse, ProviderResult, VideoProviderInput


class ImageProvider(BaseProvider[ProviderRequest, ProviderResponse]):
    pass


class VideoProvider(BaseProvider[ProviderRequest, ProviderResponse]):
    pass


class VoiceProvider(BaseProvider[ProviderRequest, ProviderResponse]):
    pass


class MusicProvider(BaseProvider[ProviderRequest, ProviderResponse]):
    pass


class RealImageProvider(BaseProvider[ImageProviderInput, ProviderResult]):
    pass


class RealVideoProvider(BaseProvider[VideoProviderInput, ProviderResult]):
    pass
