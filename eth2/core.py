from enum import Enum, unique

from typing import Type, Optional, TypeVar, Protocol, NewType, Callable, Any, Sequence, Union, Set, runtime_checkable

from remerkleable.core import View, ObjType


@unique
class ContentType(Enum):
    json = 'application/json'
    ssz = 'application/ssz'


@unique
class Method(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'


@runtime_checkable
class ToObjProtocol(Protocol):
    def to_obj(self) -> ObjType: ...


S = TypeVar('S')


@runtime_checkable
class FromObjProtocol(Protocol):
    @classmethod
    def from_obj(cls: Type[S], obj: ObjType) -> S: ...


ResponseType = Union[ObjType, Type[FromObjProtocol], Type[View], None]

APIResult = TypeVar('APIResult', bound=Union[ObjType, FromObjProtocol, View, None])

APIPath = NewType('APIEndpoint', str)


APIMethod = NewType('APIMethod', Any)


@runtime_checkable
class ModelAPIEndpoint(Protocol):
    pass


class APIEndpointFn(object):
    typ: ResponseType
    name: Optional[str]
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

F = TypeVar('F')

APIMethodDecorator = Callable[[F], F]


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

        # Instead, we create this new function, annotated with data the Eth2 API provider may use.
        fn = APIEndpointFn()
        fn.typ = annotations['return'] if 'return' in annotations else None
        fn.name = name
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
