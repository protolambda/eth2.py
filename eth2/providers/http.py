from typing import Awaitable, cast, Any, TypeVar, Optional

import json
import dataclasses
import httpx
import urllib.parse

from remerkleable.core import View

from eth2.core import ContentType, APIPath, APIEndpointFn, APIResult, FromObjProtocol, \
    APIMethodDecorator, APIProviderMethodImpl, Eth2Provider, Eth2EndpointImpl

from eth2.util import ToObjProtocol


class Eth2HttpOptions(object):
    api_base_url: str
    default_req_type: ContentType
    default_resp_type: ContentType
    default_timeout: httpx.Timeout

    def __init__(self,
                 api_base_url: str = 'http://localhost:5052/',
                 default_req_type: ContentType = ContentType.json,
                 default_resp_type: ContentType = ContentType.json,
                 default_timeout: httpx.Timeout = httpx.Timeout(connect_timeout=2.0,
                                                                read_timeout=2.0,
                                                                write_timeout=2.0,
                                                                pool_timeout=2.0)):
        self.api_base_url = api_base_url
        self.default_req_type = default_req_type
        self.default_resp_type = default_resp_type
        self.default_timeout = default_timeout


M = TypeVar('M')


class Eth2HttpProvider(Eth2Provider):
    options: Eth2HttpOptions
    _client: httpx.AsyncClient

    def __init__(self, client: httpx.AsyncClient, options: Eth2HttpOptions = Eth2HttpOptions()):
        self.options = options
        self._client = client

    def api_req(self, end_point: APIPath) -> APIMethodDecorator:  # noqa C901  TODO: split this up
        api = self

        def entry(fn: APIEndpointFn) -> APIProviderMethodImpl:
            async def run_req(*args, **kwargs) -> Awaitable[APIResult]:
                keys = [key for key in fn.arg_keys if key not in kwargs]

                # If there are any arguments, they should match the missing arguments.
                if len(args) != 0 and len(keys) != len(args):
                    raise Exception(f"unexpected arguments, got {len(args)} args but expected {len(keys)} ({', '.join(keys)})")

                for key, arg in zip(keys, args):
                    kwargs[key] = arg

                headers = {}
                if fn.resp_type is not None:
                    headers['Accept'] = fn.resp_type.value
                else:
                    if api.options.default_resp_type in fn.supports:
                        headers['Accept'] = api.options.default_resp_type.value
                    # TODO: No Accept header otherwise, or supply all different supported types into Accept?

                req_type: ContentType
                if fn.req_type is not None:
                    req_type = fn.req_type
                else:
                    req_type = api.options.default_req_type

                data: Optional[bytes] = None
                if fn.data is not None:
                    data_obj: Any
                    if fn.data in kwargs:
                        data_obj = kwargs.pop(fn.data)
                    else:
                        raise Exception(f"No args or suitable kwarg for data '{fn.data}' key")

                    if req_type == ContentType.json:
                        if isinstance(data_obj, (ToObjProtocol, View)):
                            data_obj = data_obj.to_obj()
                        data = json.dumps(data_obj).encode("utf-8")
                    elif req_type == ContentType.ssz:
                        if isinstance(data_obj, View):
                            data = data_obj.encode_bytes()
                        else:
                            raise Exception(f"input {data_obj} is not a SSZ type")

                    headers['Content-Type'] = req_type.value

                req_path = urllib.parse.urljoin(api.options.api_base_url, end_point)
                resp = await api._client.request(
                    fn.method.value,
                    req_path,
                    data=data,
                    # Normalize parameters
                    params={k: (v.to_obj() if isinstance(v, ToObjProtocol) else v)
                            for k, v in kwargs.items() if v is not None},
                    headers=headers,
                    timeout=api.options.default_timeout,  # TODO: option to change timeout on a function-call level
                )
                headers['Content-Type'] = req_type.value

                if resp.status_code != 200:
                    raise Exception(f"request error: {resp.text}")

                # Figure out what content type we are reading, with default
                content_type: ContentType
                if 'Content-Type' in resp.headers:
                    content_type = ContentType(resp.headers['Content-Type'])
                    if fn.resp_type is not None:
                        if fn.resp_type != content_type:
                            raise Exception("unsupported content type")
                        content_type = fn.resp_type
                else:
                    if fn.resp_type is None:
                        content_type = api.options.default_resp_type
                    else:
                        content_type = fn.resp_type
                if content_type not in fn.supports:
                    raise Exception(f"selected content type '{content_type.value}' is not supported by api function")
                # Decode the response
                resp_data: APIResult
                if content_type == ContentType.ssz:
                    resp_data = fn.typ.decode_bytes(resp.content)
                elif content_type == ContentType.json:
                    if fn.typ is None:
                        resp_data = None
                    elif isinstance(fn.typ, FromObjProtocol):
                        resp_data = fn.typ.from_obj(resp.json())
                    elif dataclasses.is_dataclass(fn.typ):
                        resp_data = fn.typ(**resp.json())
                    else:
                        resp_data = resp.json()
                else:
                    raise Exception("unknown content type")
                return resp_data
            # Make a copy, don't modify the original API endpoint.
            wrap_fn = APIEndpointFn(fn)
            wrap_fn.call = run_req
            return wrap_fn
        return entry

    # TODO: expose standard API
    # @property
    # def api(self) -> Eth2API:
    #     root_endpoint = Eth2EndpointImpl(self, APIPath(''), Eth2API)
    #     return cast(Eth2API, root_endpoint)

    def extended_api(self, model: M) -> M:
        """
        Hook any API model to the HTTP provider, to use custom APIs
        :param model: the model, any APIEndpointFn, VariablePathSegmentFn or
         just a class with methods annotated as such, or decorated as such.
         Basically anything that can be understood as API model.
        :return: An Eth2EndpointImpl which shadows the model, implementing it by calling HTTP functions.
        """
        root_endpoint = Eth2EndpointImpl(self, APIPath(''), model)
        return cast(model, root_endpoint)


class Eth2HttpClient(object):
    options: Eth2HttpOptions
    _client: httpx.AsyncClient
    _prov: Eth2HttpProvider

    def __init__(self, options: Eth2HttpOptions = Eth2HttpOptions()):
        self.options = options

    async def __aenter__(self):
        self._client = await httpx.AsyncClient().__aenter__()
        self._prov = Eth2HttpProvider(self._client, self.options)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.__aexit__(exc_type, exc_val, exc_tb)

    # @property
    # def api(self) -> Eth2API:
    #     return self._prov.api

    def extended_api(self, model: M) -> M:
        return self._prov.extended_api(model)
