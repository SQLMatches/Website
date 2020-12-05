# -*- coding: utf-8 -*-

"""
GNU General Public License v3.0 (GPL v3)
Copyright (c) 2020-2020 WardPearce
Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


from starlette.endpoints import HTTPEndpoint
from starlette.authentication import requires
from starlette.requests import Request

from webargs import fields
from webargs_starlette import use_args

from .rate_limiter import LIMITER

from ...api import response
from ...api.model_convertor import community_to_dict, match_to_dict

from ...communities import communities, matches

from ...caches import CommunitiesCache


class CommunitiesAPI(HTTPEndpoint):
    @use_args({"search": fields.Str(), "page": fields.Int(),
               "desc": fields.Bool()})
    @requires("steam_login")
    @LIMITER.limit("30/minute")
    async def post(self, request: Request, parameters: dict) -> response:
        """Used to get communities.

        Parameters
        ----------
        request : Request
        parameters : dict

        Returns
        -------
        response
        """

        cache = CommunitiesCache()
        cache_get = await cache.get()
        if cache_get:
            return cache_get

        data = [
            community_to_dict(community) async for community, _ in
            communities(**parameters)
        ]

        await cache.set(data)

        return response(data)


class CommunityMatchesAPI(HTTPEndpoint):
    @use_args({"search": fields.Str(), "page": fields.Int(),
               "desc": fields.Bool()})
    @requires("steam_login")
    @LIMITER.limit("30/minute")
    async def post(self, request: Request, parameters: dict) -> response:
        """Used to get matches outside of community context.

        Parameters
        ----------
        request : Request
        parameters : dict

        Returns
        -------
        """

        cache = CommunitiesCache().matches()
        cache_get = await cache.get()
        if cache_get:
            return cache_get

        data = [
            match_to_dict(match) async for match, _ in
            matches(**parameters)
        ]

        await cache.set(data)

        return response(data)


class MatchesCommunitiesAPI(HTTPEndpoint):
    @requires("steam_login")
    @LIMITER.limit("30/minute")
    async def get(self, request: Request) -> response:
        """Used to get communities & matches in one response,
           ideally I'd be using GraphQL but this is the only
           time I need to combine responses.

        Parameters
        ----------
        request : Request

        Returns
        -------
        response
        """

        data = {}

        cache = CommunitiesCache()
        matches_cache = cache.matches()

        cache_get = await cache.get()
        if cache_get:
            data["communities"] = cache_get
        else:
            data["communities"] = [
                community_to_dict(community) async for community, _ in
                communities()
            ]

            await cache.set(data["communities"])

        matches_cache_get = await matches_cache.get()
        if matches_cache_get:
            data["matches"] = matches_cache_get
        else:
            data["matches"] = [
                match_to_dict(match) async for match, _ in matches()
            ]

            await matches_cache.set(data["matches"])

        return response(data)
