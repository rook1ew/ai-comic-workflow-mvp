from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.providers.base import ProviderExecutionError
from app.providers.interfaces import RealImageProvider
from app.providers.schemas import ImageProviderInput, ProviderRequest, ProviderResult


class Image2Provider(RealImageProvider):
    name = "image2_real"

    def _normalize_input(self, payload: ImageProviderInput | ProviderRequest | dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        if isinstance(payload, ProviderRequest):
            return dict(payload.payload or {})
        return payload.model_dump()

    def build_request_payload(self, payload: ImageProviderInput | ProviderRequest | dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        normalized = self._normalize_input(payload)
        return {
            "model": settings.image2_model,
            "prompt": normalized.get("enhanced_prompt") or normalized.get("prompt"),
            "reference_image_url": normalized.get("character_reference_url"),
            "style": normalized.get("style"),
            "metadata": {
                "shot_id": normalized.get("shot_id"),
                "storyboard_context": normalized.get("storyboard_context") or {},
            },
        }

    def parse_response(self, response: dict[str, Any]) -> ProviderResult:
        image_url = str(response.get("image_url") or "").strip()
        if not image_url:
            raise ProviderExecutionError("Image2 provider response missing image_url.")
        settings = get_settings()
        return ProviderResult(
            url=image_url,
            metadata={
                "provider_name": self.name,
                "model": response.get("model") or settings.image2_model,
                "job_id": response.get("id"),
                "usage": response.get("usage") or {},
                "real_call": True,
            },
        )

    def map_error(self, error: Exception | dict[str, Any]) -> str:
        if isinstance(error, dict):
            code = str(error.get("code") or "").lower()
            message = str(error.get("message") or error.get("detail") or "").lower()
            if "auth" in code or "auth" in message or "unauthorized" in message or "forbidden" in message:
                return "Image2 provider authentication failed."
            if "quota" in code or "balance" in message or "insufficient" in message:
                return "Image2 provider quota or balance is insufficient."
            if "timeout" in code or "timeout" in message:
                return "Image2 provider request timed out."
            if "image_url" in message:
                return "Image2 provider response missing image_url."
            return "Image2 provider returned an unknown error."

        message = str(error).lower()
        if isinstance(error, TimeoutError) or "timeout" in message:
            return "Image2 provider request timed out."
        if "api key" in message or "auth" in message or "unauthorized" in message or "forbidden" in message:
            return "Image2 provider authentication failed."
        if "quota" in message or "balance" in message or "insufficient" in message:
            return "Image2 provider quota or balance is insufficient."
        if "image_url" in message:
            return "Image2 provider response missing image_url."
        return "Image2 provider returned an unknown error."

    def generate(self, payload: ImageProviderInput | ProviderRequest | dict[str, Any]) -> ProviderResult:
        raise ProviderExecutionError(
            "Real Image2 HTTP calls are disabled in v0.3-B. This provider currently exposes request/response adapters only."
        )
