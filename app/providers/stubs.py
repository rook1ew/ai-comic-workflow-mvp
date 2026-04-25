from app.providers.base import ProviderExecutionError
from app.providers.interfaces import RealImageProvider, RealVideoProvider
from app.providers.schemas import ImageProviderInput, ProviderResult, VideoProviderInput
from app.core.config import get_settings


class Image2ProviderStub(RealImageProvider):
    name = "image2_stub"

    def generate(self, payload: ImageProviderInput) -> ProviderResult:
        settings = get_settings()
        shot_id = getattr(payload, "shot_id")
        input_payload = payload.model_dump()
        if hasattr(payload, "payload"):
            input_payload = getattr(payload, "payload")
        return ProviderResult(
            url=f"mock://image2-stub/{shot_id}.png",
            metadata={
                "provider_name": self.name,
                "model": settings.image2_model,
                "input_payload": input_payload,
                "real_call": False,
                "safety_note": "stub only, no real API call",
            },
        )


class SeedanceVideoProviderStub(RealVideoProvider):
    name = "seedance_video_stub"

    def generate(self, payload: VideoProviderInput) -> ProviderResult:
        raise ProviderExecutionError(
            "SeedanceVideoProviderStub is a design-time placeholder only. Real API integration is not enabled in v0.2."
        )
