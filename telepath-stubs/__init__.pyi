from collections.abc import Callable
from typing import Any, TypeVar, overload

from django import forms as forms
from django.forms import MediaDefiningClass as MediaDefiningClass
from django.utils.functional import Promise as Promise, cached_property as cached_property

_T = TypeVar("_T")

# Recursive JSON-serializable type produced by Node.emit()
_JSONValue = (
    str
    | int
    | float
    | bool
    | None
    | list[_JSONValue]
    | dict[str, _JSONValue]
)

_PrimitiveValue = int | float | bool | None

DICT_RESERVED_KEYS: list[str]
STRING_REF_MIN_LENGTH: int

class UnpackableTypeError(TypeError): ...

class Node:
    id: int | None
    seen: bool
    use_id: bool
    def __init__(self) -> None: ...
    def emit(self) -> _JSONValue: ...

class ValueNode(Node):
    value: _PrimitiveValue
    def __init__(self, value: _PrimitiveValue) -> None: ...
    def emit_verbose(self) -> dict[str, _PrimitiveValue]: ...
    def emit_compact(self) -> _PrimitiveValue: ...

class StringNode(Node):
    value: str
    def __init__(self, value: str) -> None: ...
    def emit_verbose(self) -> dict[str, str]: ...
    def emit_compact(self) -> str: ...

class ListNode(Node):
    value: list[Node]
    def __init__(self, value: list[Node]) -> None: ...
    def emit_verbose(self) -> dict[str, list[_JSONValue]]: ...
    def emit_compact(self) -> list[_JSONValue]: ...

class DictNode(Node):
    value: dict[str, Node]
    def __init__(self, value: dict[str, Node]) -> None: ...
    def emit_verbose(self) -> dict[str, dict[str, _JSONValue]]: ...
    def emit_compact(self) -> dict[str, _JSONValue]: ...

class ObjectNode(Node):
    constructor: str
    args: list[Node]
    def __init__(self, constructor: str, args: list[Node]) -> None: ...
    def emit_verbose(self) -> dict[str, str | list[_JSONValue]]: ...
    def emit_compact(self) -> dict[str, str | list[_JSONValue]]: ...

class BaseAdapter:
    def build_node(self, obj: Any, context: ValueContext) -> Node: ...

class StringAdapter(BaseAdapter):
    def build_node(self, obj: str, context: ValueContext) -> StringNode: ...

class DictAdapter(BaseAdapter):
    def build_node(self, obj: dict[Any, Any], context: ValueContext) -> DictNode: ...

class Adapter(BaseAdapter, metaclass=MediaDefiningClass):
    js_constructor: str
    @property
    def media(self) -> forms.Media: ...
    def get_media(self, obj: Any) -> forms.Media: ...
    def pack(self, obj: Any, context: ValueContext) -> tuple[str, list[Any]]: ...
    def build_node(self, obj: Any, context: ValueContext) -> ObjectNode: ...

class AutoAdapter(Adapter):
    def pack(self, obj: Any, context: ValueContext) -> tuple[str, list[Any]]: ...

class JSContextBase:
    media: forms.Media
    media_fragments: set[str]
    telepath_js_path: str
    registry: AdapterRegistry
    def __init__(self) -> None: ...
    @property
    def base_media(self) -> forms.Media: ...
    def add_media(
        self,
        media: forms.Media | None = ...,
        js: str | list[str] | None = ...,
        css: dict[str, list[str]] | None = ...,
    ) -> None: ...
    def pack(self, obj: Any) -> _JSONValue: ...

class AdapterRegistry:
    js_context_base_class: type[JSContextBase]
    telepath_js_path: str
    adapters: dict[type, BaseAdapter]
    def __init__(self, telepath_js_path: str = ...) -> None: ...
    @overload
    def register(self, adapter: BaseAdapter, cls: type) -> None: ...
    @overload
    def register(self, cls: type[_T]) -> type[_T]: ...
    @overload
    def register(self, *, adapter: BaseAdapter | None = ...) -> Callable[[type[_T]], type[_T]]: ...
    def find_adapter(self, cls: type) -> BaseAdapter | None: ...
    @cached_property
    def js_context_class(self) -> type[JSContextBase]: ...

class ValueContext:
    parent_context: JSContextBase
    registry: AdapterRegistry
    raw_values: dict[int, Any]
    nodes: dict[int, Node]
    next_id: int
    def __init__(self, parent_context: JSContextBase) -> None: ...
    def add_media(
        self,
        media: forms.Media | None = ...,
        js: str | list[str] | None = ...,
        css: dict[str, list[str]] | None = ...,
    ) -> None: ...
    def build_node(self, val: Any) -> Node: ...

registry: AdapterRegistry
JSContext: type[JSContextBase]
register = registry.register
