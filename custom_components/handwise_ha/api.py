"""API client for Handwise MGC01 cloud polling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import re
import time
from typing import Any
import uuid
from urllib.parse import parse_qs, quote, urlparse

from aiohttp import ClientError, ClientSession
from yarl import URL

from homeassistant.exceptions import HomeAssistantError

from .const import (
    DEFAULT_IOT_ENDPOINT,
    DEFAULT_IOT_REGION,
    IOT_ENDPOINT_TEMPLATE,
)

_LOGGER = logging.getLogger(__name__)


class HandwiseGenieApiError(HomeAssistantError):
    """Raised when the Handwise API request fails."""


@dataclass(frozen=True, slots=True)
class HandwiseBoundDevice:
    """A mower/device bound to the Handwise account."""

    serial_number: str
    alias: str
    model: str
    is_owner: bool | None = None


@dataclass(frozen=True, slots=True)
class HandwiseTemporaryIotCredentials:
    """Temporary Handwise-issued AWS IoT credentials."""

    access_key_id: str
    secret_access_key: str
    session_token: str
    region_name: str
    endpoint: str
    expiration: int | None = None


@dataclass(frozen=True, slots=True)
class HandwiseDeviceRegion:
    """Cloud region metadata for a bound mower."""

    serial_number: str
    region_name: str
    iot_endpoint: str


class HandwiseCloudApiClient:
    """Client for Handwise cloud account endpoints."""

    def __init__(
        self,
        *,
        session: ClientSession,
        host: str,
        bearer_token: str | None = None,
    ) -> None:
        self._session = session
        self._host = host
        self._bearer_token = bearer_token
        self._auth_headers = {
            "Accept": "application/json, text/plain, */*",
            "version": "v2",
            "language": "en",
            "User-Agent": "LdMower/1581 CFNetwork/3860.400.51 Darwin/25.3.0",
        }
        if bearer_token:
            self._auth_headers["Authorization"] = bearer_token

    async def async_login(
        self, *, username: str, password: str, area_code: str
    ) -> str:
        """Login and return bearer token."""
        url = f"https://{self._host}/api/v1/login"
        headers = {
            "Accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "version": "v2",
            "language": "en",
            "User-Agent": "LdMower/1581 CFNetwork/3860.400.51 Darwin/25.3.0",
        }
        payload = {"username": username, "password": password, "areaCode": area_code}

        try:
            async with self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=15,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"Login failed ({resp.status}): {body[:300]}"
                    )
                data = await resp.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(data, dict):
            raise HandwiseGenieApiError("Invalid login payload type")
        if data.get("code") != 0:
            raise HandwiseGenieApiError(f"Login rejected: code={data.get('code')!r}")

        token_data = data.get("data")
        if not isinstance(token_data, dict):
            raise HandwiseGenieApiError("Login payload missing data object")
        access_token = token_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise HandwiseGenieApiError("Login payload missing access_token")

        bearer_token = f"Bearer {access_token}"
        self._bearer_token = bearer_token
        self._auth_headers["Authorization"] = bearer_token
        return bearer_token

    def _require_token(self) -> None:
        if not self._bearer_token:
            raise HandwiseGenieApiError("Bearer token not configured")

    @staticmethod
    def build_verification_token(serial_number: str, timestamp: int | None = None) -> str:
        """Build the app-style verification token used by device file/STS APIs."""
        unix_timestamp = timestamp or int(datetime.now(timezone.utc).timestamp())
        token_suffix = str(unix_timestamp)
        token_prefix = hashlib.md5(
            f"{serial_number}{token_suffix}".encode("utf-8")
        ).hexdigest()
        return f"{token_prefix}{token_suffix}"

    async def async_get_bound_devices(self) -> list[HandwiseBoundDevice]:
        """Fetch account-bound Handwise devices."""
        self._require_token()

        url = f"https://{self._host}/api/v1/device/bind/list"
        try:
            async with self._session.get(
                url, headers=self._auth_headers, timeout=15
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"Bind list failed ({resp.status}): {body[:300]}"
                    )
                payload = await resp.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(payload, dict):
            raise HandwiseGenieApiError("Invalid bind list payload type")
        if payload.get("code") != 0:
            raise HandwiseGenieApiError(f"Bind list returned code={payload.get('code')}")

        data = payload.get("data")
        if not isinstance(data, list):
            raise HandwiseGenieApiError("Bind list payload missing data array")

        devices: list[HandwiseBoundDevice] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            serial_number = item.get("sn")
            if not isinstance(serial_number, str) or not serial_number:
                continue
            alias = item.get("alias")
            model_value = item.get("category_id")
            model = str(model_value) if model_value is not None else ""
            owner_value = item.get("is_owner")
            is_owner = None
            if isinstance(owner_value, bool):
                is_owner = owner_value
            elif isinstance(owner_value, int):
                is_owner = owner_value == 1
            devices.append(
                HandwiseBoundDevice(
                    serial_number=serial_number,
                    alias=alias if isinstance(alias, str) and alias else serial_number,
                    model=model if model else "Handwise mower",
                    is_owner=is_owner,
                )
            )

        return devices

    async def async_get_device_region(self, serial_number: str) -> HandwiseDeviceRegion:
        """Fetch device cloud region metadata."""
        self._require_token()

        url = f"https://{self._host}/api/v1/device/v2/region"
        try:
            async with self._session.get(
                url,
                headers=self._auth_headers,
                params={"sn": serial_number},
                timeout=15,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"Device region failed ({resp.status}): {body[:300]}"
                    )
                payload = await resp.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(payload, dict):
            raise HandwiseGenieApiError("Invalid device region payload type")
        if payload.get("code") != 0:
            raise HandwiseGenieApiError(
                f"Device region returned code={payload.get('code')}"
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            raise HandwiseGenieApiError("Device region payload missing data object")

        region_name = data.get("region_name")
        iot_endpoint = data.get("iot_endpoint")
        if not isinstance(region_name, str) or not region_name:
            raise HandwiseGenieApiError("Device region missing region_name")
        if not isinstance(iot_endpoint, str) or not iot_endpoint:
            raise HandwiseGenieApiError("Device region missing iot_endpoint")

        return HandwiseDeviceRegion(
            serial_number=serial_number,
            region_name=region_name,
            iot_endpoint=iot_endpoint,
        )

    async def async_get_device_iot_credentials(
        self, serial_number: str
    ) -> HandwiseTemporaryIotCredentials:
        """Fetch temporary AWS IoT credentials for a mower."""
        self._require_token()

        url = f"https://{self._host}/api/v1/device/v2/iot/sts/arn"
        payload = {
            "sn": serial_number,
            "verification_token": self.build_verification_token(serial_number),
        }
        try:
            async with self._session.post(
                url,
                headers={**self._auth_headers, "content-type": "application/json"},
                json=payload,
                timeout=15,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"IoT STS failed ({resp.status}): {body[:300]}"
                    )
                response_payload = await resp.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(response_payload, dict):
            raise HandwiseGenieApiError("Invalid IoT STS payload type")
        if response_payload.get("code") != 0:
            raise HandwiseGenieApiError(
                f"IoT STS returned code={response_payload.get('code')}"
            )

        data = response_payload.get("data")
        if not isinstance(data, dict):
            raise HandwiseGenieApiError("IoT STS payload missing data object")

        access_key_id = data.get("access_key_id")
        secret_access_key = data.get("secret_access_key")
        session_token = data.get("session_token")
        region_name = data.get("region_name")
        endpoint = data.get("endpoint")
        if not all(
            isinstance(value, str) and value
            for value in (
                access_key_id,
                secret_access_key,
                session_token,
                region_name,
                endpoint,
            )
        ):
            raise HandwiseGenieApiError("IoT STS payload missing required fields")

        expiration = data.get("expiration")
        if not isinstance(expiration, int):
            expiration = None

        return HandwiseTemporaryIotCredentials(
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
            region_name=region_name,
            endpoint=endpoint,
            expiration=expiration,
        )

    async def async_get_device_area_definition(
        self, serial_number: str
    ) -> dict[str, Any]:
        """Fetch the mower area definition file."""
        self._require_token()

        url = f"https://{self._host}/api/v1/device/v2/presigned_url"
        params = {
            "filename": f"area_{serial_number}.txt",
            "sn": serial_number,
            "category": "device",
            "sub_category": "area",
            "verification_token": self.build_verification_token(serial_number),
        }

        try:
            async with self._session.get(
                url,
                headers=self._auth_headers,
                params=params,
                timeout=15,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"Area presigned URL failed ({resp.status}): {body[:300]}"
                    )
                payload = await resp.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(payload, dict):
            raise HandwiseGenieApiError("Invalid area presigned URL payload type")
        if payload.get("code") != 0:
            raise HandwiseGenieApiError(
                f"Area presigned URL returned code={payload.get('code')}"
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            raise HandwiseGenieApiError("Area presigned URL payload missing data object")
        presigned_url = data.get("presigned_url")
        if not isinstance(presigned_url, str) or not presigned_url:
            raise HandwiseGenieApiError("Area presigned URL payload missing presigned_url")

        try:
            async with self._session.get(presigned_url, timeout=15) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"Area definition download failed ({resp.status}): {body[:300]}"
                    )
                text = await resp.text()
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        try:
            area_definition = json.loads(text)
        except json.JSONDecodeError as err:
            raise HandwiseGenieApiError("Area definition is not valid JSON") from err

        if not isinstance(area_definition, dict):
            raise HandwiseGenieApiError("Area definition payload type is not an object")

        return area_definition

    async def async_get_device_presigned_region(self, serial_number: str) -> str | None:
        """Fetch presigned_url metadata and extract AWS region."""
        self._require_token()

        url = f"https://{self._host}/api/v1/device/v2/presigned_url"
        try:
            async with self._session.get(
                url,
                headers=self._auth_headers,
                params={"sn": serial_number},
                timeout=15,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise HandwiseGenieApiError(
                        f"Presigned URL failed ({resp.status}): {body[:300]}"
                    )
                payload = await resp.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(payload, dict):
            raise HandwiseGenieApiError("Invalid presigned URL payload type")
        if payload.get("code") != 0:
            raise HandwiseGenieApiError(
                f"Presigned URL returned code={payload.get('code')}"
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            raise HandwiseGenieApiError("Presigned URL payload missing data object")
        presigned_url = data.get("presigned_url")
        if not isinstance(presigned_url, str) or not presigned_url:
            raise HandwiseGenieApiError("Presigned URL payload missing presigned_url")

        parsed = urlparse(presigned_url)
        host = parsed.netloc
        if host:
            host_parts = host.split(".")
            if len(host_parts) >= 4 and host_parts[0] == "s3":
                if host_parts[1] == "dualstack":
                    candidate = host_parts[2]
                else:
                    candidate = host_parts[1]
                if candidate and candidate not in {"amazonaws", "amazonaws.com"}:
                    return candidate

        query = parse_qs(parsed.query, keep_blank_values=False)
        credential_values = query.get("X-Amz-Credential", [])
        if credential_values:
            credential_parts = credential_values[0].split("/")
            if len(credential_parts) >= 3 and credential_parts[2]:
                return credential_parts[2]

        return None


class HandwiseShadowApiClient:
    """Client for Handwise AWS IoT shadow endpoint."""

    def __init__(
        self,
        *,
        session: ClientSession,
        serial_number: str,
        region_name: str | None,
        iot_endpoint: str | None,
        account_client: HandwiseCloudApiClient | None = None,
        iot_credentials: HandwiseTemporaryIotCredentials | None = None,
        device_model: str | None = None,
    ) -> None:
        self._session = session
        self._serial_number = serial_number
        self._device_model = device_model
        self._account_client = account_client
        self._region_name = (
            region_name if isinstance(region_name, str) and region_name else None
        )
        self._iot_endpoint = self._normalize_endpoint(iot_endpoint)
        self._temporary_credentials: HandwiseTemporaryIotCredentials | None = None
        self._temporary_credentials_expires_at = 0.0
        if iot_credentials is not None:
            self.set_temporary_credentials(iot_credentials)
        endpoint_region = self._guess_region_from_endpoint(self._iot_endpoint)
        if (
            self._region_name
            and endpoint_region
            and self._region_name != endpoint_region
        ):
            _LOGGER.debug(
                "Handwise region mismatch for %s: api region=%s endpoint region=%s endpoint=%s; endpoint region will be used for signing",
                serial_number,
                self._region_name,
                endpoint_region,
                self._iot_endpoint,
            )

    def set_temporary_credentials(
        self, credentials: HandwiseTemporaryIotCredentials
    ) -> None:
        """Store Handwise-issued temporary AWS IoT credentials."""
        self._temporary_credentials = credentials
        self._region_name = credentials.region_name
        self._iot_endpoint = self._normalize_endpoint(credentials.endpoint)
        expires_in = credentials.expiration if credentials.expiration else 3600
        self._temporary_credentials_expires_at = time.monotonic() + max(
            expires_in - 300, 60
        )

    async def async_ensure_temporary_credentials(
        self, account_client: HandwiseCloudApiClient | None = None
    ) -> None:
        """Refresh temporary AWS IoT credentials before they expire."""
        if (
            self._temporary_credentials is not None
            and time.monotonic() < self._temporary_credentials_expires_at
        ):
            return
        await self.async_refresh_temporary_credentials(account_client)

    async def async_refresh_temporary_credentials(
        self, account_client: HandwiseCloudApiClient | None = None
    ) -> None:
        """Force-refresh temporary AWS IoT credentials."""
        credential_client = account_client or self._account_client
        if credential_client is None:
            raise HandwiseGenieApiError("IoT credential refresh client not configured")
        self.set_temporary_credentials(
            await credential_client.async_get_device_iot_credentials(self._serial_number)
        )

    @staticmethod
    def _is_forbidden_status(status: int) -> bool:
        """Return whether an IoT response status should refresh credentials."""
        return status == 403

    @staticmethod
    def _normalize_endpoint(iot_endpoint: str | None) -> str:
        if not isinstance(iot_endpoint, str) or not iot_endpoint:
            return DEFAULT_IOT_ENDPOINT
        endpoint = iot_endpoint.strip()
        endpoint = re.sub(r"^https?://", "", endpoint, flags=re.IGNORECASE)
        return endpoint.rstrip("/") or DEFAULT_IOT_ENDPOINT

    @staticmethod
    def _guess_region_from_endpoint(iot_endpoint: str) -> str | None:
        if ".iot." not in iot_endpoint:
            return None
        right_side = iot_endpoint.split(".iot.", 1)[1]
        region = right_side.split(".", 1)[0]
        return region or None

    @staticmethod
    def guess_region_from_endpoint(iot_endpoint: str) -> str | None:
        """Public helper to extract region from an IoT endpoint host."""
        return HandwiseShadowApiClient._guess_region_from_endpoint(iot_endpoint)

    @property
    def serial_number(self) -> str:
        """Return the configured device serial number."""
        return self._serial_number

    @property
    def iot_endpoint(self) -> str:
        """Return resolved IoT endpoint host."""
        return self._iot_endpoint

    @property
    def signing_region(self) -> str:
        """Return the signing region for AWS SigV4 requests."""
        endpoint_region = self._guess_region_from_endpoint(self._iot_endpoint)
        if endpoint_region:
            return endpoint_region
        return (
            self._region_name or DEFAULT_IOT_REGION
        )

    @staticmethod
    def build_default_iot_endpoint_for_region(region_name: str) -> str:
        """Build the default Handwise IoT endpoint host for a region."""
        return IOT_ENDPOINT_TEMPLATE.format(region=region_name)

    def _access_key_id(self) -> str:
        if self._temporary_credentials is not None:
            return self._temporary_credentials.access_key_id
        if self._iot_endpoint == CN_NORTHWEST_IOT_ENDPOINT:
            return AWS_ACCESS_KEY_CN_NORTHWEST
        if self.signing_region.startswith("cn"):
            return AWS_ACCESS_KEY_CN
        return AWS_ACCESS_KEY_DEFAULT

    def _secret_access_key(self) -> str:
        if self._temporary_credentials is not None:
            return self._temporary_credentials.secret_access_key
        if self._iot_endpoint == CN_NORTHWEST_IOT_ENDPOINT:
            return AWS_SECRET_KEY_CN_NORTHWEST
        if self.signing_region.startswith("cn"):
            return AWS_SECRET_KEY_CN
        return AWS_SECRET_KEY_DEFAULT

    def _session_token(self) -> str | None:
        if self._temporary_credentials is not None:
            return self._temporary_credentials.session_token
        return None

    @staticmethod
    def _sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _signing_key(self, date_stamp: str) -> bytes:
        service = "iotdata"
        k_date = self._sign(("AWS4" + self._secret_access_key()).encode("utf-8"), date_stamp)
        k_region = self._sign(k_date, self.signing_region)
        k_service = self._sign(k_region, service)
        return self._sign(k_service, "aws4_request")

    def _build_authorization(self, amz_date: str, date_stamp: str, canonical_request: str) -> str:
        algorithm = "AWS4-HMAC-SHA256"
        signed_headers = self._signed_headers_from_request(canonical_request)
        credential_scope = (
            f"{date_stamp}/{self.signing_region}/iotdata/aws4_request"
        )
        string_to_sign = (
            f"{algorithm}\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )
        signature = hmac.new(
            self._signing_key(date_stamp),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return (
            f"{algorithm} Credential={self._access_key_id()}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

    @staticmethod
    def _normalize_header_value(value: str) -> str:
        return " ".join(value.strip().split())

    @staticmethod
    def _canonical_headers(headers: dict[str, str]) -> tuple[str, str]:
        lowered = {
            key.lower(): HandwiseShadowApiClient._normalize_header_value(value)
            for key, value in headers.items()
        }
        ordered_keys = sorted(lowered.keys())
        canonical = "".join(f"{key}:{lowered[key]}\n" for key in ordered_keys)
        signed_headers = ";".join(ordered_keys)
        return canonical, signed_headers

    @staticmethod
    def _signed_headers_from_request(canonical_request: str) -> str:
        parts = canonical_request.split("\n")
        if len(parts) < 6:
            return "host;x-amz-content-sha256;x-amz-date"
        return parts[-2]

    @staticmethod
    def _canonical_uri_for_sigv4(request_uri: str) -> str:
        """Build SigV4 canonical URI.

        AWS canonicalization requires encoding '%' as '%25', so an already
        encoded request path (for example '/topics/%24aws%2F...') must be
        double-encoded only for signing.
        """
        encoded: list[str] = []
        for byte in request_uri.encode("utf-8"):
            if (
                0x30 <= byte <= 0x39  # 0-9
                or 0x41 <= byte <= 0x5A  # A-Z
                or 0x61 <= byte <= 0x7A  # a-z
                or byte in (45, 46, 95, 126, 47)  # - . _ ~ /
            ):
                encoded.append(chr(byte))
            else:
                encoded.append(f"%{byte:02X}")
        return "".join(encoded)

    async def _async_get_named_shadow_reported_state(
        self, shadow_name: str, *, allow_credential_refresh: bool = True
    ) -> dict[str, Any]:
        """Fetch a named device shadow and return state.reported."""
        request_uri = f"/things/{quote(self._serial_number, safe='-_.~')}/shadow"
        canonical_uri = self._canonical_uri_for_sigv4(request_uri)
        canonical_query = f"name={quote(shadow_name, safe='-_.~')}"
        payload_hash = hashlib.sha256(b"").hexdigest()

        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        signed_header_values = {
            "host": self._iot_endpoint,
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        headers = {
            "Accept": "*/*",
            "Host": self._iot_endpoint,
            "x-amz-date": amz_date,
            "x-amz-content-sha256": payload_hash,
        }
        session_token = self._session_token()
        if session_token:
            invocation_id = str(uuid.uuid4())
            signed_header_values["amz-sdk-invocation-id"] = invocation_id
            signed_header_values["amz-sdk-request"] = "attempt=1; max=3"
            signed_header_values["x-amz-security-token"] = session_token
            signed_header_values["x-amz-user-agent"] = "aws-sdk-js/3.1025.0"
            headers["amz-sdk-invocation-id"] = invocation_id
            headers["amz-sdk-request"] = "attempt=1; max=3"
            headers["x-amz-security-token"] = session_token
            headers["x-amz-user-agent"] = "aws-sdk-js/3.1025.0"
            headers["User-Agent"] = (
                "aws-sdk-js/3.1025.0 ua/2.1 os/other lang/js "
                "md/rn api/iot-data-plane#3.1025.0 m/N,E"
            )
        else:
            headers["User-Agent"] = "LdMower/1581 CFNetwork/3860.400.51 Darwin/25.3.0"
        canonical_headers, signed_headers = self._canonical_headers(signed_header_values)
        canonical_request = (
            "GET\n"
            f"{canonical_uri}\n"
            f"{canonical_query}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )
        authorization = self._build_authorization(
            amz_date=amz_date,
            date_stamp=date_stamp,
            canonical_request=canonical_request,
        )

        url = f"https://{self._iot_endpoint}{request_uri}?{canonical_query}"
        headers["Authorization"] = authorization

        try:
            async with self._session.get(url, headers=headers, timeout=15) as response:
                if response.status != 200:
                    body = await response.text()
                    if (
                        self._is_forbidden_status(response.status)
                        and allow_credential_refresh
                        and self._account_client is not None
                    ):
                        _LOGGER.debug(
                            "Handwise shadow request failed with 403, refreshing IoT credentials: sn=%s endpoint=%s region=%s",
                            self._serial_number,
                            self._iot_endpoint,
                            self.signing_region,
                        )
                        await self.async_refresh_temporary_credentials()
                        return await self._async_get_named_shadow_reported_state(
                            shadow_name,
                            allow_credential_refresh=False,
                        )
                    raise HandwiseGenieApiError(
                        f"Shadow request failed ({response.status}) at endpoint "
                        f"'{self._iot_endpoint}' (region '{self.signing_region}'): "
                        f"{body[:300]}"
                    )
                payload = await response.json(content_type=None)
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

        if not isinstance(payload, dict):
            raise HandwiseGenieApiError("Invalid response payload type")

        state = payload.get("state")
        reported = state.get("reported") if isinstance(state, dict) else None
        if not isinstance(reported, dict):
            raise HandwiseGenieApiError("Missing state.reported in response")

        return reported

    async def async_get_shadow_reported_state(self) -> dict[str, Any]:
        """Fetch property shadow and return state.reported."""
        return await self._async_get_named_shadow_reported_state("property")

    async def async_get_service_reported_state(self) -> dict[str, Any]:
        """Fetch service shadow and return state.reported."""
        # M5/M9 devices use the property shadow instead of service shadow
        # since they don't have access to the service named shadow
        is_m_series = self._device_model and ("M5" in str(self._device_model).upper() or "M9" in str(self._device_model).upper())
        if is_m_series:
            return await self._async_get_named_shadow_reported_state("property")
        return await self._async_get_named_shadow_reported_state("service")

    async def _async_signed_post(
        self,
        *,
        request_uri: str,
        canonical_query: str,
        payload_bytes: bytes,
        include_sdk_headers: bool,
        canonical_uri_override: str | None = None,
        sign_content_length: bool = True,
    ) -> tuple[int, str, dict[str, Any] | None, dict[str, str]]:
        """Execute a signed IoTData POST request."""
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        signed_header_values = {
            "host": self._iot_endpoint,
            "content-type": "application/octet-stream",
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        headers = {
            "Accept": "*/*",
            "Host": self._iot_endpoint,
            "Content-Type": "application/octet-stream",
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": amz_date,
        }
        if sign_content_length:
            signed_header_values["content-length"] = str(len(payload_bytes))
            headers["Content-Length"] = str(len(payload_bytes))

        if include_sdk_headers:
            invocation_id = str(uuid.uuid4())
            signed_header_values["amz-sdk-invocation-id"] = invocation_id
            signed_header_values["amz-sdk-request"] = "attempt=1; max=3"
            signed_header_values["x-amz-user-agent"] = "aws-sdk-js/3.1025.0"
            headers["amz-sdk-invocation-id"] = invocation_id
            headers["amz-sdk-request"] = "attempt=1; max=3"
            headers["x-amz-user-agent"] = "aws-sdk-js/3.1025.0"
            headers["User-Agent"] = (
                "aws-sdk-js/3.1025.0 ua/2.1 os/other lang/js "
                "md/rn api/iot-data-plane#3.1025.0 m/N,E"
            )
        else:
            headers["User-Agent"] = "LdMower/1581 CFNetwork/3860.400.51 Darwin/25.3.0"

        session_token = self._session_token()
        if session_token:
            signed_header_values["x-amz-security-token"] = session_token
            headers["x-amz-security-token"] = session_token

        canonical_headers, signed_headers = self._canonical_headers(signed_header_values)
        canonical_uri = (
            canonical_uri_override
            if isinstance(canonical_uri_override, str)
            else self._canonical_uri_for_sigv4(request_uri)
        )
        canonical_request = (
            "POST\n"
            f"{canonical_uri}\n"
            f"{canonical_query}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )
        headers["Authorization"] = self._build_authorization(
            amz_date=amz_date,
            date_stamp=date_stamp,
            canonical_request=canonical_request,
        )

        url = f"https://{self._iot_endpoint}{request_uri}"
        if canonical_query:
            url = f"{url}?{canonical_query}"

        try:
            async with self._session.post(
                URL(url, encoded=True),
                headers=headers,
                data=payload_bytes,
                timeout=15,
            ) as response:
                body_text = await response.text()
                payload: dict[str, Any] | None = None
                try:
                    parsed = json.loads(body_text)
                    if isinstance(parsed, dict):
                        payload = parsed
                except json.JSONDecodeError:
                    payload = None
                response_headers = {
                    "x-amzn-errortype": response.headers.get("x-amzn-errortype", ""),
                    "x-amzn-requestid": response.headers.get("x-amzn-requestid", ""),
                    "x-amzn-request-id": response.headers.get("x-amzn-request-id", ""),
                    "date": response.headers.get("date", ""),
                }
                return response.status, body_text, payload, response_headers
        except ClientError as err:
            raise HandwiseGenieApiError(f"Network error: {err}") from err
        except TimeoutError as err:
            raise HandwiseGenieApiError("Request timed out") from err

    async def async_publish_service_command(self, *, cmd: str, data: Any) -> None:
        """Publish a service command to the mower service shadow topic."""
        topic = f"$aws/things/{self._serial_number}/shadow/name/service/update"
        body = {"state": {"desired": {"cmd": cmd, "data": data}}}

        payload_bytes = json.dumps(body, separators=(",", ":")).encode("utf-8")
        
        request_uri_encoded = "/topics/" + quote(topic, safe="-_.~")
        request_uri_raw = f"/topics/{topic}"

        # Different AWS clients canonicalize the URI slightly differently.
        # Try the app-observed mode first, then fall back to alternatives.
        attempts = (
            # 1) SDK headers + encoded URI + app-style canonical URI (trace match)
            (request_uri_encoded, True, None, True),
            # 2) SDK headers + encoded URI + raw canonical URI
            (request_uri_encoded, True, request_uri_encoded, True),
            # 3) SDK headers + encoded URI + app-style canonical URI, no signed content-length
            (request_uri_encoded, True, None, False),
            # 4) LdMower headers + encoded URI + app-style canonical URI
            (request_uri_encoded, False, None, True),
            # 5) Raw topic path, SDK headers, app-style canonical URI
            (request_uri_raw, True, None, True),
            # 6) Raw topic path, SDK headers, raw canonical URI
            (request_uri_raw, True, request_uri_raw, True),
            # 7) Raw topic path, LdMower headers, app-style canonical URI
            (request_uri_raw, False, None, True),
        )

        last_status = 0
        last_body = ""
        last_headers: dict[str, str] = {}
        for refresh_attempt in range(2):
            for attempt_index, (
                request_uri,
                include_sdk_headers,
                canonical_uri_override,
                sign_content_length,
            ) in enumerate(attempts):
                status, body_text, payload, response_headers = (
                    await self._async_signed_post(
                        request_uri=request_uri,
                        canonical_query="",
                        payload_bytes=payload_bytes,
                        include_sdk_headers=include_sdk_headers,
                        canonical_uri_override=canonical_uri_override,
                        sign_content_length=sign_content_length,
                    )
                )
                if status == 200 and isinstance(payload, dict):
                    if attempt_index > 0 or refresh_attempt > 0:
                        _LOGGER.debug(
                            "Handwise command publish recovered after fallback: cmd=%s sn=%s endpoint=%s region=%s uri=%s sdk_headers=%s canonical_override=%s sign_content_length=%s refreshed=%s",
                            cmd,
                            self._serial_number,
                            self._iot_endpoint,
                            self.signing_region,
                            request_uri,
                            include_sdk_headers,
                            canonical_uri_override is not None,
                            sign_content_length,
                            refresh_attempt > 0,
                        )
                    return
                last_status = status
                last_body = body_text
                last_headers = response_headers
                if status != 403:
                    break
                _LOGGER.debug(
                    "Handwise command publish attempt failed (403): cmd=%s sn=%s uri=%s sdk_headers=%s canonical_override=%s sign_content_length=%s errortype=%s requestid=%s",
                    cmd,
                    self._serial_number,
                    request_uri,
                    include_sdk_headers,
                    canonical_uri_override is not None,
                    sign_content_length,
                    response_headers.get("x-amzn-errortype", ""),
                    response_headers.get("x-amzn-requestid", "")
                    or response_headers.get("x-amzn-request-id", ""),
                )
            if (
                self._is_forbidden_status(last_status)
                and refresh_attempt == 0
                and self._account_client is not None
            ):
                _LOGGER.debug(
                    "Handwise command publish failed with 403, refreshing IoT credentials: cmd=%s sn=%s endpoint=%s region=%s",
                    cmd,
                    self._serial_number,
                    self._iot_endpoint,
                    self.signing_region,
                )
                await self.async_refresh_temporary_credentials()
                continue
            break

        raise HandwiseGenieApiError(
            f"Command '{cmd}' failed ({last_status}) at endpoint '{self._iot_endpoint}' "
            f"(region '{self.signing_region}', errortype '{last_headers.get('x-amzn-errortype', '')}', "
            f"requestid '{last_headers.get('x-amzn-requestid', '') or last_headers.get('x-amzn-request-id', '')}'): "
            f"{last_body[:300]}"
        )

    async def async_request_all_properties(self) -> None:
        """Request an updated property snapshot from the mower."""
        await self.async_publish_service_command(cmd="get_all_props", data=1)
