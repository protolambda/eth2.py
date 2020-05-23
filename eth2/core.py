from enum import Enum, unique
from typing import Type, Optional, TypeVar, Protocol, NewType, Callable, Any, Sequence, Generic, Union, Set

from remerkleable.core import View, ObjType

from eth2.util import FromObjProtocol


@unique
class ContentType(Enum):
    json = 'application/json'
    ssz = 'application/ssz'


@unique
class Method(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'


ResponseType = Union[ObjType, Type[FromObjProtocol], Type[View], None]

APIResult = TypeVar('APIResult', bound=Union[ObjType, FromObjProtocol, View, None])

APIPath = NewType('APIEndpoint', str)


APIMethod = NewType('APIMethod', Any)


_P = TypeVar('_P')


class VariablePathSegment(Generic[_P]):
    model: Any
    path: str

    def __init__(self, model: Any, path: str):
        self.model = model
        self.path = path


class VariablePathSegmentFn(Generic[_P]):
    out_model: Any
    name: str
    formatter: Callable[[_P], str]

    def __init__(self, out_model: Any, name: str, formatter: Callable[[_P], str]):
        self.out_model = out_model
        self.name = name
        self.formatter = formatter

    def __call__(self, value: _P):
        path_segment = self.formatter(value)
        return VariablePathSegment(self.out_model, path_segment)


def var_path(formatter: Optional[Callable[[_P], str]] = None,
             name: Optional[str] = None) -> Callable[[Any], VariablePathSegmentFn[_P]]:
    if formatter is None:
        formatter = str  # format the input as str by default

    def deco(fn):
        if not hasattr(fn, '__annotations__'):
            raise Exception("variable path function is missing annotations to derive implementation from")
        if list(fn.__annotations__.keys()) != ['value', 'return']:
            raise Exception(f"annotations for variable path segment are bad."
                            f"Expected a 'value' input and a 'return'. But got {list(fn.__annotations__.keys())}")
        out_model = fn.__annotations__['return']
        segment_name = name if name is not None else fn.__name__
        return VariablePathSegmentFn(out_model, segment_name, formatter)
    return deco


class APIEndpointFn(object):
    typ: ResponseType
    name: str
    arg_keys: Sequence[str]
    method: Method
    req_type: Optional[ContentType]
    resp_type: Optional[ContentType]
    data: Optional[str]
    supports: Set[ContentType]
    call: Optional[Callable]

    def __init__(self, fn: Optional["APIEndpointFn"] = None):
        if fn is not None:
            self.typ = fn.typ
            self.name = fn.name
            self.arg_keys = fn.arg_keys
            self.method = fn.method
            self.req_type = fn.req_type
            self.resp_type = fn.resp_type
            self.data = fn.data
            self.supports = fn.supports
            self.call = fn.call

    async def __call__(self, *args, **kwargs):
        if self.call is None:
            raise Exception("Eth2 API provider required to call API function.")
        return await self.call(*args, **kwargs)


APIProviderMethodImpl = Callable

_F = TypeVar('_F')

APIMethodDecorator = Callable[[_F], _F]


def api(method: Method = Method.GET,
        supports: Optional[Set[ContentType]] = None,
        name: Optional[str] = None,
        req_type: Optional[ContentType] = None,
        resp_type: Optional[ContentType] = None,
        data: Optional[str] = None) -> APIMethodDecorator:
    """
    :param method: The method of requesting
    :param supports: The content-types that are supported in the *response*.
    :param name: A custom name for the function endpoint (joined to parent api endpoint),
     used if the function name doesn't match.
    :param req_type: Content type to use for the request.
    :param resp_type: Content type to use for the response.
    :param data: Optionally take one of the arguments to use as request data payload.
    :return: a decorator to ignore the non-functional input model func for,
      and return an APIEndpointFn that actually does something.
    """

    if supports is None:
        supports = {ContentType.json}

    def entry(fn):
        # The fn is dropped, we don't run any of the model functions, they are *models*, for typing.
        annotations = fn.__annotations__
        fn_name = name if name is not None else fn.__name__

        # Instead, we create this new function, annotated with data the Eth2 API provider may use.
        fn = APIEndpointFn()
        fn.typ = annotations['return'] if 'return' in annotations else None
        fn.name = fn_name
        fn.arg_keys = [key for key in annotations.keys() if key != 'return' and key != 'self']
        fn.method = method
        fn.req_type = req_type
        fn.resp_type = resp_type
        fn.data = data
        fn.supports = supports
        fn.call = None
        return fn
    return entry


class Eth2Provider(Protocol):
    def api_req(self, end_point: APIPath) -> APIMethodDecorator:
        ...


class Eth2EndpointImpl(object):
    """
    This shadows the API Model, creating endpoints on the fly, and wrapping them with the Eth2 provider as necessary.
    This way, the model can be a bare "Protocol" type, super easy to mock for testing,
     generic between any Eth2 provider.
    """
    prov: Eth2Provider
    path: APIPath
    model: Any

    def __init__(self, prov: Eth2Provider, path: APIPath, model: Any):
        self.prov = prov
        self.path = path
        self.model = model

    def __getattr__(self, item):
        # If we are dealing with an opened variable path that yet needs a value, then
        if isinstance(self.model, VariablePathSegmentFn):
            raise Exception("Cannot get sub route in variable path segment, need variable first")
        if hasattr(self.model, '__annotations__'):  # Sub routes in the model are just annotation fields
            annotations = self.model.__annotations__
            if item in annotations:
                return Eth2EndpointImpl(self.prov, APIPath(self.path + '/' + item), annotations[item])
        if hasattr(self.model, item):  # If not a sub-route, check if it's an APIEndpointFn
            attr = getattr(self.model, item)
            # If it's a an API function, then wrap it with the provider, and return the resulting callable.
            if isinstance(attr, APIEndpointFn):
                return self.prov.api_req(APIPath(self.path + '/' + attr.name))(attr)
            # If it's a variable path segment, then continue building the endpoint path
            if isinstance(attr, VariablePathSegmentFn):
                return Eth2EndpointImpl(self.prov, APIPath(self.path + '/' + attr.name), attr)

        raise AttributeError(f"unknown item '{item}', not a sub-route or APIEndpointFn")

    def __call__(self, *args, **kwargs):
        if not callable(self.model):
            raise Exception(f"endpoint '{self.path}' is not callable")
        # If this is a variable-path segment, then get the corresponding endpoint for the segment
        if isinstance(self.model, VariablePathSegmentFn):
            path_segment = self.model(*args, **kwargs)
            return Eth2EndpointImpl(self.prov, APIPath(self.path + '/' + path_segment.path), path_segment.model)
        # Otherwise, it may be a route that is callable itself. I.e. the model.__call__ is an APIEndpointFn
        v = self.model.__call__
        if isinstance(v, APIEndpointFn):
            return self.prov.api_req(APIPath(self.path + '/' + v.name))(v)
        # It's not part of the API, maybe just a helper method in the route model. Try calling the model definition.
        return self.model(*args, **kwargs)
