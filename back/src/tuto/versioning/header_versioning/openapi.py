# Copyright (c) 2023 tikon93
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
# Modified from: https://github.com/tikon93/fastapi-header-versioning

from collections import defaultdict

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

from .fastapi import HeaderRoutingFastAPI
from .routing import HeaderVersionedAPIRoute


def get_version_from_route(route: BaseRoute) -> str | None:
    if isinstance(route, HeaderVersionedAPIRoute):
        return route.api_version or None

    return None


def doc_generation(
    app: HeaderRoutingFastAPI,
) -> HeaderRoutingFastAPI:
    parent_app = app
    version_route_mapping: dict[str | None, list[BaseRoute]] = defaultdict(list)

    for route in app.routes:
        version = get_version_from_route(route)  # pyright: ignore[reportGeneralTypeIssues]
        version_route_mapping[version].append(route)  # pyright: ignore[reportGeneralTypeIssues]

    versions = version_route_mapping.keys()
    for version in versions:
        unique_routes = {}
        version_description = version if version is not None else "Not versioned"
        versioned_app = FastAPI(
            title=app.title,
            description=version_description + " " + app.description,
        )
        for route in version_route_mapping[version]:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    unique_routes[route.path + "|" + method] = route

            # TODO: support websocket routes

        versioned_app.router.routes.extend(unique_routes.values())

        prefix = f"/version_{version}"
        if version is None:
            prefix = "/no_version"
        parent_app.mount(prefix, versioned_app)

    return parent_app
