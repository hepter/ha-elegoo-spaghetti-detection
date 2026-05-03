import os
from functools import wraps

from flask import Response, request

ML_API_TOKEN = os.environ.get("ML_API_TOKEN")


def token_required(f):
    @wraps(f)
    def check_authorization(*args, **kwargs):
        if (
            request.headers.get("Authorization") == f"Bearer {ML_API_TOKEN}"
            or request.args.get("token") == ML_API_TOKEN
        ):
            return f(*args, **kwargs)
        return Response(status=401)

    @wraps(f)
    def passthru(*args, **kwargs):
        return f(*args, **kwargs)

    if ML_API_TOKEN:
        return check_authorization
    return passthru
