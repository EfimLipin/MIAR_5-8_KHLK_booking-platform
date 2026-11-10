from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.request_context import request_id_var


async def http_error_handler(request: Request, exc: HTTPException):
    mapping = {400:"bad_request",401:"unauthorized",403:"forbidden",404:"not_found",409:"conflict",
               500:"internal_server_error",502:"bad_gateway",503:"service_unavailable",504:"gateway_timeout"}
    return JSONResponse(status_code=exc.status_code,
        content={"error":{"code":mapping.get(exc.status_code,"http_error"),"message":str(exc.detail),"details":{}},
                 "request_id":request_id_var.get()}, headers=getattr(exc,"headers",None))


async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors=[{"field":".".join(str(p) for p in e.get("loc",())),"message":e.get("msg","Invalid value"),"type":e.get("type","")} for e in exc.errors()]
    return JSONResponse(status_code=400,content={"error":{"code":"bad_request","message":"Запрос не прошёл проверку.","details":{"validation_errors":errors}},"request_id":request_id_var.get()})


async def unhandled_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500,content={"error":{"code":"internal_server_error","message":"Внутренняя ошибка сервиса.","details":{}},"request_id":request_id_var.get()})
