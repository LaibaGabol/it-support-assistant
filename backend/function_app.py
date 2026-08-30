"""Azure Functions entrypoint.

Wraps the existing FastAPI app (app/main.py) as an ASGI app so the whole API
runs on a Functions consumption plan without changing any routes.

Two Functions-specific concerns are handled here:
  * `/admin/*` is a RESERVED route namespace on the Functions host, so the API
    is served under the standard `api` route prefix (see host.json) to avoid it.
  * With that prefix the host passes the full `/api/...` path to the ASGI app,
    so `_StripPrefix` removes the leading `/api` before the request reaches the
    single FastAPI app. Going straight to the FastAPI app (rather than mounting
    it inside an outer app) keeps its CORS middleware as the first thing to run,
    so CORS preflight (OPTIONS) is answered correctly.
"""
import azure.functions as func

from app.main import app as fastapi_app

_PREFIX = "/api"


class _StripPrefix:
    """ASGI middleware that strips a leading path prefix before delegating."""

    def __init__(self, app, prefix):
        self.app = app
        self.prefix = prefix

    async def __call__(self, scope, receive, send):
        if scope.get("type") in ("http", "websocket"):
            path = scope.get("path", "")
            if path.startswith(self.prefix):
                scope = dict(scope)
                scope["path"] = path[len(self.prefix):] or "/"
                raw = scope.get("raw_path")
                if raw:
                    pref = self.prefix.encode()
                    if raw.startswith(pref):
                        scope["raw_path"] = raw[len(pref):] or b"/"
        await self.app(scope, receive, send)


_wrapped = _StripPrefix(fastapi_app, _PREFIX)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="{*route}")
async def http_app(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return await func.AsgiMiddleware(_wrapped).handle_async(req, context)
