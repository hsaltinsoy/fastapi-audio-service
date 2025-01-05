from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ExceptionCustom(HTTPException):
    pass


def exception_400_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": exc.detail})
