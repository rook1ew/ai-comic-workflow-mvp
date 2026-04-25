from app.providers.base import ProviderExecutionError
from app.providers.interfaces import ImageProvider, MusicProvider, VideoProvider, VoiceProvider
from app.providers.schemas import ProviderRequest, ProviderResponse


class MockProviderMixin:
    name = "mock"

    def _build_response(self, payload: ProviderRequest, asset_type: str) -> ProviderResponse:
        if payload.payload.get("should_fail") is True:
            raise ProviderExecutionError(f"Mock {asset_type} provider forced failure")
        suffix = payload.payload.get("extension", "txt")
        return ProviderResponse(
            provider_name=self.name,
            asset_type=asset_type,
            url=f"https://mock.assets/{asset_type}/shot-{payload.shot_id}.{suffix}",
            metadata={
                "mock": True,
                "provider_name": self.name,
                "modality": asset_type,
                "input_payload": payload.payload,
            },
        )


class MockImageProvider(MockProviderMixin, ImageProvider):
    def generate(self, payload: ProviderRequest) -> ProviderResponse:
        return self._build_response(payload, "image")


class MockVideoProvider(MockProviderMixin, VideoProvider):
    def generate(self, payload: ProviderRequest) -> ProviderResponse:
        return self._build_response(payload, "video")


class MockVoiceProvider(MockProviderMixin, VoiceProvider):
    def generate(self, payload: ProviderRequest) -> ProviderResponse:
        return self._build_response(payload, "voice")


class MockMusicProvider(MockProviderMixin, MusicProvider):
    def generate(self, payload: ProviderRequest) -> ProviderResponse:
        return self._build_response(payload, "bgm")
