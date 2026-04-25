from app.providers.base import ProviderExecutionError
from app.providers.interfaces import RealImageProvider, RealVideoProvider
from app.providers.schemas import ImageProviderInput, ProviderResult, VideoProviderInput


class Image2ProviderStub(RealImageProvider):
    name = "image2_stub"

    def generate(self, payload: ImageProviderInput) -> ProviderResult:
        raise ProviderExecutionError(
            "Image2ProviderStub is a design-time placeholder only. Real API integration is not enabled in v0.2."
        )


class SeedanceVideoProviderStub(RealVideoProvider):
    name = "seedance_video_stub"

    def generate(self, payload: VideoProviderInput) -> ProviderResult:
        raise ProviderExecutionError(
            "SeedanceVideoProviderStub is a design-time placeholder only. Real API integration is not enabled in v0.2."
        )
