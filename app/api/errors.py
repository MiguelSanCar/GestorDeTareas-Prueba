from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import TodoStatus

FIELD_NAMES = {
    "title": "título",
    "description": "descripción",
    "status": "estado",
    "todo_id": "id",
}

_VALID_STATUSES = ", ".join(s.value for s in TodoStatus)


def _translate(error: dict) -> str:
    """Devuelve el mensaje de un error de validación de pydantic en español."""
    loc = [str(part) for part in error["loc"]]
    field = FIELD_NAMES.get(loc[-1], loc[-1]) if len(loc) > 1 else None
    subject = f"El campo «{field}»" if field else "El cuerpo de la petición"
    ctx = error.get("ctx") or {}

    match error["type"]:
        case "missing":
            return f"El campo «{field}» es obligatorio"
        case "string_too_short" if ctx.get("min_length") == 1:
            return f"{subject} no puede estar vacío"
        case "string_too_short":
            return f"{subject} debe tener al menos {ctx.get('min_length')} caracteres"
        case "string_too_long":
            return f"{subject} no puede superar los {ctx.get('max_length')} caracteres"
        case "string_type":
            return f"{subject} debe ser texto"
        case "enum":
            return f"{subject} no es válido; valores permitidos: {_VALID_STATUSES}"
        case "extra_forbidden":
            return f"El campo «{loc[-1]}» no está permitido"
        case "int_parsing" | "int_type":
            return f"{subject} debe ser un número entero"
        case "greater_than_equal":
            return f"{subject} debe ser mayor o igual que {ctx.get('ge')}"
        case "json_invalid":
            return "El cuerpo de la petición no es un JSON válido"
        case "model_attributes_type" | "dict_type":
            return "El cuerpo de la petición debe ser un objeto JSON"
        case "value_error":
            # Los validadores propios ya escriben en español; quita el prefijo de pydantic.
            return error["msg"].removeprefix("Value error, ")
        case _:
            return error["msg"]


async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": list(e["loc"]), "msg": _translate(e), "type": e["type"]}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, validation_error_handler)
