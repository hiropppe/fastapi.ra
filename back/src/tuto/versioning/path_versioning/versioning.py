# Copyright (c) 2023 DeanWay
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Modified from: https://github.com/DeanWay/fastapi-versioning

from collections import defaultdict
from collections.abc import Callable
from typing import Any, Dict, List, Tuple, TypeVar, cast

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

CallableT = TypeVar("CallableT", bound=Callable[..., Any])


def version(major: int, minor: int = 0) -> Callable[[CallableT], CallableT]:
    def decorator(func: CallableT) -> CallableT:
        func._api_version = (major, minor)  # type: ignore
        return func

    return decorator


def version_to_route(
    route: BaseRoute,
    default_version: tuple[int, int],
) -> tuple[tuple[int, int], APIRoute]:
    api_route = cast(APIRoute, route)
    version = getattr(api_route.endpoint, "_api_version", default_version)
    return version, api_route


def VersionedFastAPI(
    app: FastAPI,
    version_format: str = "{major}.{minor}",
    prefix_format: str = "/v{major}_{minor}",
    default_version: tuple[int, int] = (1, 0),
    enable_latest: bool = False,
    **kwargs: Any,
) -> FastAPI:
    parent_app = FastAPI(
        title=app.title,
        **kwargs,
    )
    version_route_mapping: dict[tuple[int, int], list[APIRoute]] = defaultdict(list)
    version_routes = [version_to_route(route, default_version) for route in app.routes]

    for version, route in version_routes:
        version_route_mapping[version].append(route)

    unique_routes = {}
    versions = sorted(version_route_mapping.keys())
    for version in versions:
        major, minor = version
        prefix = prefix_format.format(major=major, minor=minor)
        semver = version_format.format(major=major, minor=minor)
        versioned_app = FastAPI(
            title=app.title,
            description=app.description,
            version=semver,
        )
        for route in version_route_mapping[version]:
            for method in route.methods:
                unique_routes[route.path + "|" + method] = route
        for route in unique_routes.values():
            versioned_app.router.routes.append(route)
        parent_app.mount(prefix, versioned_app)

        @parent_app.get(f"{prefix}/openapi.json", name=semver, tags=["Versions"])
        @parent_app.get(f"{prefix}/docs", name=semver, tags=["Documentations"])
        def noop() -> None: ...

    if enable_latest:
        prefix = "/latest"
        major, minor = version
        semver = version_format.format(major=major, minor=minor)
        versioned_app = FastAPI(
            title=app.title,
            description=app.description,
            version=semver,
        )
        for route in unique_routes.values():
            versioned_app.router.routes.append(route)
        parent_app.mount(prefix, versioned_app)

    return parent_app
