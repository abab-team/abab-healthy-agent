from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApiErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    MISSING_CURRENT_USER = "missing_current_user"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"
    CONFLICT = "conflict"
    INVALID_STATE = "invalid_state"
    INTERNAL_SERVER_ERROR = "internal_server_error"


DEFAULT_MESSAGES: dict[ApiErrorCode, str] = {
    ApiErrorCode.INVALID_REQUEST: "The request is invalid.",
    ApiErrorCode.VALIDATION_ERROR: "The request parameters are invalid.",
    ApiErrorCode.UNAUTHORIZED: "Authentication is required for this request.",
    ApiErrorCode.MISSING_CURRENT_USER: "Authentication is required for this request.",
    ApiErrorCode.PERMISSION_DENIED: "You do not currently have permission to access this data.",
    ApiErrorCode.RESOURCE_NOT_FOUND: "The resource was not found or you do not have access to it.",
    ApiErrorCode.CONFLICT: "The request conflicts with the current resource state.",
    ApiErrorCode.INVALID_STATE: "The resource is not in a valid state for this operation.",
    ApiErrorCode.INTERNAL_SERVER_ERROR: "The server encountered an unexpected error.",
}

SENSITIVE_FIELD_NAMES = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "session_token",
    "session_token_hash",
    "token_hash",
    "secret",
    "api_key",
    "private_key",
    "file_path",
    "raw_text",
    "raw_extracted_text",
    "medical_content",
    "health_data",
}


def build_error_detail(
    *,
    code: ApiErrorCode | str,
    message: str | None = None,
    request_id: str | None = None,
    fields: list[dict[str, str | None]] | None = None,
) -> dict[str, Any]:
    error_code = _coerce_code(code)
    return {
        "code": error_code.value,
        "message": safe_error_message(message, error_code),
        "request_id": request_id,
        "fields": fields,
    }


def raise_api_error(
    *,
    status_code: int,
    code: ApiErrorCode | str,
    message: str | None = None,
    fields: list[dict[str, str | None]] | None = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=build_error_detail(code=code, message=message, fields=fields),
    )


def raise_permission_denied(message: str | None = None) -> None:
    raise_api_error(
        status_code=status.HTTP_403_FORBIDDEN,
        code=ApiErrorCode.PERMISSION_DENIED,
        message=message,
    )


def raise_not_found(message: str | None = None) -> None:
    raise_api_error(
        status_code=status.HTTP_404_NOT_FOUND,
        code=ApiErrorCode.RESOURCE_NOT_FOUND,
        message=message,
    )


def raise_bad_request(message: str | None = None) -> None:
    raise_api_error(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ApiErrorCode.INVALID_REQUEST,
        message=message,
    )


def raise_conflict(message: str | None = None, *, code: ApiErrorCode = ApiErrorCode.CONFLICT) -> None:
    raise_api_error(status_code=status.HTTP_409_CONFLICT, code=code, message=message)


def raise_unauthorized(message: str | None = None, *, code: ApiErrorCode = ApiErrorCode.UNAUTHORIZED) -> None:
    raise_api_error(status_code=status.HTTP_401_UNAUTHORIZED, code=code, message=message)


def safe_error_message(message: str | None, code: ApiErrorCode | str) -> str:
    error_code = _coerce_code(code)
    if not message:
        return DEFAULT_MESSAGES[error_code]
    if error_code in {
        ApiErrorCode.RESOURCE_NOT_FOUND,
        ApiErrorCode.INTERNAL_SERVER_ERROR,
        ApiErrorCode.UNAUTHORIZED,
        ApiErrorCode.MISSING_CURRENT_USER,
    }:
        return DEFAULT_MESSAGES[error_code]
    if error_code == ApiErrorCode.PERMISSION_DENIED:
        return DEFAULT_MESSAGES[error_code] if _contains_sensitive_token(message) else message
    if _contains_sensitive_token(message):
        return DEFAULT_MESSAGES[error_code]
    return message


def map_business_exception(exc: Exception) -> tuple[int, ApiErrorCode, str | None]:
    name = exc.__class__.__name__.lower()
    if "permissiondenied" in name:
        return status.HTTP_403_FORBIDDEN, ApiErrorCode.PERMISSION_DENIED, None
    if "notfound" in name or "notconfigured" in name:
        return status.HTTP_404_NOT_FOUND, ApiErrorCode.RESOURCE_NOT_FOUND, None
    if "notpending" in name or "invalidstate" in name or "unsupported" in name:
        return status.HTTP_409_CONFLICT, ApiErrorCode.INVALID_STATE, str(exc)
    if "alreadyexists" in name or "ambiguous" in name or "conflict" in name:
        return status.HTTP_409_CONFLICT, ApiErrorCode.CONFLICT, str(exc)
    if "invalid" in name or "required" in name:
        return status.HTTP_400_BAD_REQUEST, ApiErrorCode.INVALID_REQUEST, str(exc)
    return status.HTTP_500_INTERNAL_SERVER_ERROR, ApiErrorCode.INTERNAL_SERVER_ERROR, None


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = normalize_http_detail(request, exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail}, headers=exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = [_validation_field_summary(error) for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": build_error_detail(
                code=ApiErrorCode.VALIDATION_ERROR,
                request_id=get_request_id(request),
                fields=fields,
            )
        },
    )


async def business_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code, code, message = map_business_exception(exc)
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": build_error_detail(
                code=code,
                message=message,
                request_id=get_request_id(request),
            )
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled API exception", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": build_error_detail(
                code=ApiErrorCode.INTERNAL_SERVER_ERROR,
                request_id=get_request_id(request),
            )
        },
    )


def normalize_http_detail(request: Request, status_code: int, detail: Any) -> dict[str, Any]:
    request_id = get_request_id(request)
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return build_error_detail(
            code=detail["code"],
            message=detail.get("message"),
            request_id=detail.get("request_id") or request_id,
            fields=detail.get("fields"),
        )
    code = _code_for_status(status_code)
    message = detail if isinstance(detail, str) else None
    return build_error_detail(code=code, message=message, request_id=request_id)


def get_request_id(request: Request | None) -> str | None:
    if request is None:
        return None
    state_request_id = getattr(request.state, "request_id", None)
    if state_request_id:
        return str(state_request_id)
    header_request_id = request.headers.get("X-Request-Id")
    return header_request_id or None


def _validation_field_summary(error: dict[str, Any]) -> dict[str, str | None]:
    loc = [str(part) for part in error.get("loc", []) if part != "body"]
    field = ".".join(loc) if loc else None
    if field and any(_is_sensitive_field_name(part) for part in loc):
        field = "[sensitive]"
    message = str(error.get("msg") or "Invalid value.")
    error_type = str(error.get("type") or "value_error")
    return {"field": field, "type": error_type, "message": _safe_validation_message(message)}


def _safe_validation_message(message: str) -> str:
    if _contains_sensitive_token(message):
        return "Invalid value."
    return message


def _code_for_status(status_code: int) -> ApiErrorCode:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return ApiErrorCode.UNAUTHORIZED
    if status_code == status.HTTP_403_FORBIDDEN:
        return ApiErrorCode.PERMISSION_DENIED
    if status_code == status.HTTP_404_NOT_FOUND:
        return ApiErrorCode.RESOURCE_NOT_FOUND
    if status_code == status.HTTP_409_CONFLICT:
        return ApiErrorCode.CONFLICT
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return ApiErrorCode.VALIDATION_ERROR
    if status_code >= 500:
        return ApiErrorCode.INTERNAL_SERVER_ERROR
    return ApiErrorCode.INVALID_REQUEST


def _coerce_code(code: ApiErrorCode | str) -> ApiErrorCode:
    if isinstance(code, ApiErrorCode):
        return code
    try:
        return ApiErrorCode(code)
    except ValueError:
        return ApiErrorCode.INTERNAL_SERVER_ERROR


def _contains_sensitive_token(message: str) -> bool:
    lowered = message.lower()
    return any(token in lowered for token in SENSITIVE_FIELD_NAMES) or any(
        marker in message for marker in ("\\", "/", "traceback", "select ", "insert ", "update ", "delete ")
    )


def _is_sensitive_field_name(field_name: str) -> bool:
    lowered = field_name.lower()
    return any(token in lowered for token in SENSITIVE_FIELD_NAMES)
