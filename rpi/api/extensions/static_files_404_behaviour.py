import typing

from fastapi import status
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope


class StaticFiles404Behaviour(StaticFiles):
    def __init__(
        self,
        *,
        directory: str = None,
        packages: typing.List[str] = None,
        html: bool = False,
        check_dir: bool = True,
        handler_404: typing.Callable = None,
    ) -> None:
        super(StaticFiles404Behaviour, self).__init__(
            directory=directory, packages=packages, html=html, check_dir=check_dir
        )
        self.handler_404 = handler_404

    async def get_response(self, path: str, scope: Scope) -> Response:
        super_response = await super().get_response(path=path, scope=scope)
        if super_response.status_code == status.HTTP_404_NOT_FOUND and self.handler_404:
            return self.handler_404(path)
        else:
            return super_response
