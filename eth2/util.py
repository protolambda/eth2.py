from typing import Type, TypeVar, Protocol, runtime_checkable, List, Dict, Union, Tuple

from remerkleable.core import ObjType


@runtime_checkable
class ToObjProtocol(Protocol):
    def to_obj(self) -> ObjType: ...


_T = TypeVar('_T')


@runtime_checkable
class FromObjProtocol(Protocol):
    @classmethod
    def from_obj(cls: Type[_T], obj: ObjType) -> _T:
        # Default implementation: try to expand the object into the constructor arguments
        if isinstance(obj, dict):
            return cls(**obj)
        # Lists/tuples generally take 1 arg as option to copy contents.
        # Other classes support type coercion in the constructor
        return cls(obj)


_E = TypeVar('_E')


class ObjList(List[_E]):
    el_class: Type[_E]

    def __class_getitem__(cls, item: Type[_E]):
        class TypedObjList(cls):
            pass
        setattr(TypedObjList, 'el_class', item)
        return TypedObjList

    def to_obj(self) -> ObjType:
        ft = self.__class__.el_class
        if isinstance(ft, ToObjProtocol):
            return [el.to_obj() for el in self]
        else:
            return list(self)

    @classmethod
    def from_obj(cls: Type[_T], obj: ObjType) -> _T:
        if not isinstance(obj, list):
            raise Exception("expected list input")
        ft = cls.el_class
        if isinstance(ft, FromObjProtocol):
            return cls(list(map(ft.from_obj, obj)))
        return cls(obj)


_K = TypeVar('_K')
_V = TypeVar('_V')


# Naive but easy typed dictionary, to force proper object to/from representation, following To/From Obj protocols
class ObjDict(Dict[_K, _V]):
    k_class: Type[_K]
    v_class: Type[_V]

    def __class_getitem__(cls, item: Tuple[Type[_K], Type[_V]]):
        kt, vt = item

        class TypedObjDict(cls):
            pass

        setattr(TypedObjDict, 'k_class', kt)
        setattr(TypedObjDict, 'v_class', vt)
        return TypedObjDict

    def to_obj(self) -> ObjType:
        kt = self.__class__.k_class
        vt = self.__class__.v_class
        if isinstance(kt, ToObjProtocol):
            if isinstance(vt, ToObjProtocol):
                return {k.to_obj(): v.to_obj() for k, v in self.items()}
            else:
                return {k.to_obj(): v for k, v in self.items()}
        else:
            if isinstance(vt, ToObjProtocol):
                return {k: v.to_obj() for k, v in self.items()}
            else:
                return dict(self)

    @classmethod
    def from_obj(cls: Type[_T], obj: ObjType) -> _T:
        if not isinstance(obj, dict):
            raise Exception("expected dict input")
        kt = cls.k_class
        vt = cls.v_class
        if isinstance(kt, FromObjProtocol):
            if isinstance(vt, FromObjProtocol):
                return cls({kt.from_obj(k): vt.from_obj(v) for k, v in obj.items()})
            else:
                return cls({kt.from_obj(k): v for k, v in obj.items()})
        else:
            if isinstance(vt, FromObjProtocol):
                return cls({k: vt.from_obj(v) for k, v in obj.items()})
            else:
                return cls(obj)


def _json_loader(t, obj):
    if isinstance(t, type):
        if issubclass(t, FromObjProtocol):
            return t.from_obj(obj)
        if isinstance(obj, dict):
            return t(**obj)
        return t(obj)
    else:
        if t.__origin__ is Union:
            if len(t.__args__) != 2 or t.__args__[1] is not type(None):  # noqa E721
                raise Exception("Only Optional[V] is supported")
            if obj is None:
                return None
            else:
                return _json_loader(t.__args__[0], obj)
        return obj


class ObjStruct(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_obj(self) -> ObjType:
        m = {k: (v.to_obj() if isinstance(v, ToObjProtocol) else v)
             for k, v in [(k, getattr(self, k)) for k in self.__annotations__.keys()]}
        return m

    @classmethod
    def from_obj(cls: Type[_T], obj: ObjType) -> _T:
        if not isinstance(obj, dict):
            raise Exception("expected dict input")
        ft = cls.__annotations__
        if set(ft.keys()) != set(obj.keys()):
            raise Exception("unexpected difference in obj keys")
        return cls(**{k: _json_loader(ft[k], v) for k, v in obj.items()})
