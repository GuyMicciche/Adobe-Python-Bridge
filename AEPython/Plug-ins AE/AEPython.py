import re
import json
import pathlib

import _AEPython as _ae

# Explicitly define common introspection attributes to prevent __getattr__ calls
__wrapped__ = None
__name__ = 'AEPython'
__all__ = []  # Prevents 'from AEPython import *' from trying weird stuff

__ES_class_names = [
    # Core / top-level objects
    "Array",               # ES Array wrapper (AE often returns these)
    "Application",         # app
    "Project",             # app.project
    "Settings",            # app.settings, project.settings

    # Items / sources
    "Item",                # Base for Project items
    "AVItem",              # Base for items with time (CompItem, FootageItem)
    "CompItem",            # Composition
    "FolderItem",          # Folder in project panel
    "FootageItem",         # Footage / still / precomp
    "FootageSource",       # Base for FileSource, SolidSource, PlaceholderSource
    "FileSource",          # File-based footage source
    "SolidSource",         # Solid color footage source
    "PlaceholderSource",   # Placeholder / missing footage

    # Layers
    "Layer",               # Base for all layers
    "AVLayer",             # Base for comp layers that have time
    "CameraLayer",         # Camera layer
    "LightLayer",          # Light layer
    "ShapeLayer",          # Shape layer
    "TextLayer",           # Text layer
    "ThreeDModelLayer",    # 3D model layer (newer AE versions)

    # Collections
    "Collection",          # Generic collection base
    "ItemCollection",      # app.project.items
    "LayerCollection",     # comp.layers
    "OMCollection",        # OutputModule collection
    "RQItemCollection",    # RenderQueue item collection

    # Properties / property groups
    "PropertyBase",        # Base for PropertyGroup/Property
    "Property",            # leaf property
    "PropertyGroup",       # group (Masks, Effects, Transform, etc.)
    "MaskPropertyGroup",   # layer.Masks (mask parade)

    # Masks and related
    "Mask",                # single mask: layer.Masks(n)
    "MaskFeather",         # per-vertex feather data for a mask

    # Effects / layer styles
    "Effect",              # single effect: layer.effect("name")(1)
    "EffectCollection",    # effect parade: layer.effect
    "LayerStyle",          # single layer style (Stroke, Drop Shadow, etc.)
    "LayerStyles",         # collection: layer.property("ADBE Layer Styles")

    # Text
    "TextDocument",        # Source Text value
    "TextLayer",           # already listed above

    # Shapes
    "Shape",               # AE Shape object (paths, vertices, tangents)
    "ShapeLayer",          # already listed above

    # Render queue
    "RenderQueue",         # app.project.renderQueue
    "RenderQueueItem",     # renderQueue.item(n)
    "OutputModule",        # renderQueue.item(n).outputModule(m)

    # Misc / system / viewing
    "System",              # system object (system.callSystem, sleep, etc.)
    "Viewer",              # Composition / Layer / Footage viewer
    "ViewOptions",         # viewer.viewOptions

    "KeyframeEase",        # easing object for keys
    "MarkerValue",         # layer marker value
]


def _executeScript(code: str):
    # Wrap code for the ES side dispatcher
    code = repr(code)
    return _ae.executeScript(f"__AEPython_executeScript({code})")


def executeScript(code: str):
    """
    Execute ExtendScript code and convert the result into a Python type.

    The ES side returns a CSV string like:
        "boolean,true"
        "number,12.0"
        "string,Hello"
        "object,CompItem,42"
    """
    ret = _executeScript(code)

    if ret == "null" or ret == "":
        return None

    results = ret.split(",")
    ret_type = results[0]

    if ret_type == "boolean":
        return results[1] == "true"

    elif ret_type == "number":
        v = float(results[1])
        return int(v) if v == int(v) else v

    elif ret_type == "string":
        # Strip the "string," prefix only once
        return ret.replace("string,", "", 1)

    elif ret_type == "function":
        # ESFunction represents a top-level function object
        return ESFunction(results[2])

    elif ret_type == "object":
        class_name = results[1]
        es_id = results[2]

        # Known ES class name -> construct our Python wrapper
        if class_name in __ES_class_names:
            obj = eval(f"{class_name}(_id={es_id})")
            # Auto-convert AE Array to Python list for convenience
            if isinstance(obj, Array):
                return obj.to_list()
            return obj

        # Unknown ES object -> generic wrapper
        return ESWrapper(es_id)

    else:
        raise Exception(f"ES type error: {results[0]}")


def __getattr__(name):
    """
    Module-level __getattr__ for accessing global ExtendScript objects.

    Example:
        import AEPython as ae
        app = ae.app   # -> Application wrapper
        system = ae.system
        File = ae.File
    """
    try:
        return executeScript(name)
    except Exception as e:
        raise AttributeError(f"ExtendScript has no global '{name}': {e}")


def _toESObject(obj):
    """
    Convert Python objects (including ESWrapper instances) into
    a JSON-ish representation that ExtendScript can eval.

    ESWrapper instances are emitted as __AEPython_objects[n] instead
    of JSON strings so they can be used as native ES objects.
    """
    class Encoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, ESWrapper):
                # __repr__ returns "__AEPython_objects[id]"
                return repr(obj)
            return json.JSONEncoder.default(self, obj)

    dst = json.dumps(obj, cls=Encoder)
    # Unquote any "__AEPython_objects[n]" strings
    return re.sub(r'\"__AEPython_objects\[(\d+)\]\"', r'__AEPython_objects[\1]', dst)


class ESWrapper(object):
    """
    Base wrapper for any ExtendScript object reference.

    Holds an ES-side object ID and proxies attribute get/set
    and method calls back to ExtendScript.
    """

    def __init__(self, _id: str):
        # store ES object id as a private Python attribute
        super().__setattr__("_es_id", _id)

    def __repr__(self) -> str:
        # This string is valid ES code to reference the object
        return f"__AEPython_objects[{self._es_id}]"

    def __str__(self) -> str:
        return super().__repr__() + f"(id:{self._es_id})"

    def __del__(self):
        # Ask ES side to free the object
        _ae.executeScript(f"__AEPython_deleteObject({self._es_id});")

    def __eq__(self, __o: object) -> bool:
        # Compare underlying ES objects
        if isinstance(__o, ESWrapper):
            return executeScript(f"{repr(self)} == {repr(__o)};")
        return False

    def __getattr__(self, name: str) -> any:
        """
        Access ES object properties/methods:
            layer.name
            comp.frameDuration
            layer.property("ADBE Transform Group")
        """
        ret = executeScript(f"{repr(self)}.{name};")
        if isinstance(ret, ESFunction):
            # Return bound method wrapper so we can call it
            return ESObjectFunction(self, name)
        return ret

    def __setattr__(self, __name: str, __value: any) -> None:
        """
        Setting an attribute on the wrapper proxies to ES,
        unless it's a private/own attribute (starts with '_').
        """
        # Direct Python attributes should not go through to ES
        if __name.startswith('_') or __name in self.__dict__ or hasattr(type(self), __name):
            object.__setattr__(self, __name, __value)
            return

        __value = _toESObject(__value)
        executeScript(f"__AEPython_setattr({self._es_id}, {repr(__name)}, {__value});")


class ESFunction(ESWrapper):
    """
    Wrapper for a top-level ES function object.
    """

    def __call__(self, *args, **kwds) -> any:
        code = f"__AEPython_callObject({self._es_id}, {_toESObject(args)[1:-1]});"
        return executeScript(code)


class ESObjectFunction:
    """
    Wrapper for a method on an ES object.

    Example:
        layer = ae.app.project.activeItem.layer(1)
        layer.remove()  # -> ESObjectFunction -> calls layer.remove()
    """

    def __init__(self, object, function_name):
        self.__object = object
        self.__function_name = function_name

    def __call__(self, *args, **kwds) -> any:
        code = f"{repr(self.__object)}.{self.__function_name}({_toESObject(args)[1:-1]});"
        return executeScript(code)


# ---------------------------------------------------------------------------
# ES virtual/base classes (type hierarchy)
# ---------------------------------------------------------------------------

class Item(ESWrapper):
    """Base class for items in the Project panel (FolderItem, CompItem, FootageItem)."""
    pass


class AVItem(Item):
    """Base class for items with a time dimension (CompItem, FootageItem)."""
    pass


class Layer(ESWrapper):
    """Base class for all layers in a comp."""
    pass


class AVLayer(Layer):
    """Base class for time-based layers (text, solids, footage, shape, etc.)."""
    pass


class FootageSource(ESWrapper):
    """Base class for footage sources (FileSource, SolidSource, PlaceholderSource)."""
    pass


class PropertyBase(ESWrapper):
    """Base class for Property and PropertyGroup."""
    pass


class Collection(ESWrapper):
    """
    Generic collection with integer indexing and iteration:
        for item in comp.layers:
            ...
        layer = comp.layers[1]
    """

    def __iter__(self):
        object.__setattr__(self, "_i", 0)
        return self

    def __next__(self):
        length = int(self.__getattr__("length"))
        if self._i >= length:
            raise StopIteration()

        ret = executeScript(f"{repr(self)}[{self._i}];")
        object.__setattr__(self, "_i", self._i + 1)
        return ret

    def __getitem__(self, index: int):
        return executeScript(f"{repr(self)}[{index}];")


# ---------------------------------------------------------------------------
# ES concrete classes
# ---------------------------------------------------------------------------

class Array(ESWrapper):
    """ExtendScript Array wrapper, convertable to a Python list."""

    def to_list(self):
        dst = []
        length = executeScript(f"{repr(self)}.length")
        for i in range(0, length):
            element = executeScript(f"{repr(self)}[{i}]")
            dst.append(element)
        return dst


class Application(ESWrapper):
    """app object wrapper, entry point to AE."""

    def beginUndoGroup(self, name: str):
        """Use host undo group implementation for better integration."""
        _ae.startUndoGroup(name)

    def endUndoGroup(self):
        _ae.endUndoGroup()


class CameraLayer(Layer):
    """Camera layer in a comp."""
    pass


class CompItem(AVItem):
    """Composition item in the Project (and comp object in timeline)."""
    pass


class FileSource(FootageSource):
    """Footage source backed by a file on disk."""
    pass


class FolderItem(Item):
    """Folder in the Project panel."""
    pass


class FootageItem(AVItem):
    """Footage item in the Project panel."""
    pass


class ImportOptions(ESWrapper):
    """
    ImportOptions wrapper for app.project.importFile() options.

    Example:
        opts = ImportOptions("/path/to/file.mov")
        item = app.project.importFile(opts)
    """

    def __init__(self, file: str | pathlib.Path | ESWrapper = None, _id: str = None):
        if _id is None:
            if file is None:
                code = "new ImportOptions()"
            elif isinstance(file, str):
                code = f"new ImportOptions(new File({repr(file)}))"
            elif isinstance(file, pathlib.Path):
                code = f"new ImportOptions(new File({repr(file.as_posix())}))"
            else:
                # assume ES file-like object / FootageSource
                code = f"new ImportOptions({repr(file)})"
            ret = _executeScript(code)
            _id = ret.split(",")[2]

        super().__init__(_id)


class ItemCollection(Collection):
    """app.project.items collection."""
    pass


class KeyframeEase(ESWrapper):
    """
    Easing object used for setting keyframe temporal ease.

    Example:
        easeIn = KeyframeEase(0, 75)
        easeOut = KeyframeEase(0, 0)
        prop.setTemporalEaseAtKey(1, [easeIn], [easeOut])
    """

    def __init__(self, x=None, y=None, _id: str = None):
        if _id is None:
            ret = _executeScript(f"new KeyframeEase({x}, {y})")
            _id = ret.split(",")[2]

        super().__init__(_id)


class LayerCollection(Collection):
    """comp.layers collection."""
    pass


class LightLayer(Layer):
    """Light layer in a comp."""
    pass


class MarkerValue(ESWrapper):
    """
    Marker value for layer or comp markers.

    Example:
        mv = MarkerValue("My Marker")
        layer.property("ADBE Marker").setValueAtTime(1.0, mv)
    """

    def __init__(self, comment=None, chapter=None, url=None, frameTarget=None,
                 cuePointName=None, params=None, _id: str = None):
        if _id is None:
            comment = repr(comment)
            chapter = "undefined" if chapter is None else repr(chapter)
            url = "undefined" if url is None else repr(url)
            frameTarget = "undefined" if frameTarget is None else repr(frameTarget)
            cuePointName = "undefined" if cuePointName is None else repr(cuePointName)
            params = "undefined" if params is None else repr(params)

            code = f"new MarkerValue({comment}, {chapter}, {url}, {frameTarget}, {cuePointName}, {params})"
            ret = _executeScript(code)
            _id = ret.split(",")[2]

        super().__init__(_id)


class MaskPropertyGroup(ESWrapper):
    """
    Mask parade on a layer: layer.Masks

    Example:
        maskGroup = layer.Masks
        mask = maskGroup.addProperty("Mask")
    """
    pass


class Mask(ESWrapper):
    """
    Single mask on a layer.

    Typical access:
        mask = layer.Masks(1)
        shapeProp = mask.property("maskShape")
    """
    pass


class MaskFeather(ESWrapper):
    """
    Per-vertex feather data object for a mask.

    Access via mask.maskFeather or related APIs when present.
    """
    pass


class OMCollection(Collection):
    """Collection of OutputModules on a RenderQueueItem."""
    pass


class OutputModule(ESWrapper):
    """Single Output Module in the Render Queue."""
    pass


class PlaceholderSource(ESWrapper):
    """Placeholder footage source."""
    pass


class Project(ESWrapper):
    """app.project wrapper."""
    pass


class Property(PropertyBase):
    """Leaf property (no sub-properties)."""
    pass


class PropertyGroup(PropertyBase):
    """Group property (Transforms, Masks, Effects, Layer Styles, etc.)."""
    pass


class RenderQueue(ESWrapper):
    """app.project.renderQueue wrapper."""
    pass


class RenderQueueItem(ESWrapper):
    """Single item in the render queue."""
    pass


class RQItemCollection(Collection):
    """Collection of RenderQueueItems."""
    pass


class Settings(ESWrapper):
    """AE Settings object (project or app settings)."""
    pass


class Shape(ESWrapper):
    """
    AE Shape object, used for mask and shape layer paths.

    Example:
        s = Shape()
        s.vertices = [[0,0],[100,0],[100,100],[0,100]]
        mask.property("maskShape").setValue(s)
    """

    def __init__(self, _id: str = None):
        if _id is None:
            ret = _executeScript("new Shape()")
            _id = ret.split(",")[2]

        super().__init__(_id)


class ShapeLayer(ESWrapper):
    """Shape layer in a comp."""
    pass


class SolidSource(FootageSource):
    """Solid color footage source."""
    pass


class System(ESWrapper):
    """AE system object: system.callSystem, sleep, etc."""
    pass


class TextDocument(ESWrapper):
    """
    TextDocument value used by a text layer's Source Text property.

    Example:
        td = layer.property("Source Text").value;
        td.text = "Hello";
        layer.property("Source Text").setValue(td);
    """

    def __init__(self, docText: str = "", _id: str = None):
        if _id is None:
            text = repr(docText)
            ret = _executeScript(f"new TextDocument({text})")
            _id = ret.split(",")[2]

        super().__init__(_id)


class TextLayer(AVLayer):
    """Text layer in a comp."""
    pass


class ThreeDModelLayer(AVLayer):
    """Newer AE 3D model layer type."""
    pass


class Effect(ESWrapper):
    """
    Single effect instance on a layer.

    Example:
        blur = layer.effect("Gaussian Blur")(1)
        blur.blurriness.setValue(50)
    """
    pass


class EffectCollection(Collection):
    """
    Effect parade on a layer.

    Access:
        effects = layer.effect
        first = effects(1)
    """
    pass


class LayerStyle(ESWrapper):
    """
    Single layer style, e.g. Stroke, Drop Shadow.

    Access via layer.property("ADBE Layer Styles").property("ADBE Stroke") etc.
    """
    pass


class LayerStyles(Collection):
    """
    Collection of layer styles on a layer.

    Access:
        styles = layer.property("ADBE Layer Styles")
    """
    pass


class Viewer(ESWrapper):
    """Viewer wrapper (Comp, Layer, Footage viewer)."""
    pass


class ViewOptions(ESWrapper):
    """View options for a viewer (grid, guides, etc.)."""
    pass
