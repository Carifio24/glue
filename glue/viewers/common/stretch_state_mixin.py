from glue.config import stretches
from glue.viewers.matplotlib.state import (
    DeferredDrawDictCallbackProperty as DDDCProperty,
    DeferredDrawSelectionCallbackProperty as DDSCProperty,
)

__all__ = ["custom_stretch_state_mixin", "StretchStateMixin"]

def custom_stretch_state_mixin(prefix):

    def stretch_getter(self):
        if not getattr(self, f"_{prefix}_stretch_set_up"):
            raise Exception(f"{prefix}_setup_stretch_callback has not been called")
        return getattr(self, f"{prefix}stretch_object")

    def _sync_stretch_parameters(self, *args):
        for key, value in self.stretch_parameters.items():
            if hasattr(self._stretch_object, key):
                setattr(self._stretch_object, key, value)
            else:
                raise ValueError(
                    f"Stretch object {self._stretch_object.__class__.__name__} has no attribute {key}"
                )

    def _reset_stretch(self, *args):
        setattr(self, f"{prefix}stretch_object", stretches.members[self.stretch]())
        getattr(self, f"{prefix}stretch_parameters").clear()

    class CustomStretchMixin:
        __name__ = f"{prefix.title().replace('_', '')}StretchStateMixin"

        def setup_stretch_callback(self):
            stretch = f"{prefix}stretch"
            setattr(self, f"_{stretch}_set_up", False)
            getattr(type(self), stretch).set_choices(self, list(stretches.members))
            getattr(type(self), stretch).set_display_func(self, stretches.display_func)
            resetter = getattr(self, f"_reset_{prefix}stretch")()
            resetter()
            setattr(self, f"_sync_{prefix}stretch_parameters", _sync_stretch_parameters)
            setattr(self, f"_reset_{prefix}stretch", _reset_stretch)
            self.add_callback(stretch, resetter)
            self.add_callback(f"{prefix}stretch_parameters", _sync_stretch_parameters)
            setattr(self, f"{prefix}stretch_set_up", True)
    
    setattr(CustomStretchMixin, f"{prefix}stretch", DDSCProperty(
        docstring="The stretch used to render the layer, "
        "which should be one of ``linear``, "
        "``sqrt``, ``log``, or ``arcsinh``"
    ))
    setattr(CustomStretchMixin, f"{prefix}stretch_parameters", DDDCProperty(
        docstring="Keyword arguments to pass to the stretch"
    ))
    setattr(CustomStretchMixin, f"_{prefix}stretch_set_up", False)
    setattr(CustomStretchMixin, f"{prefix}stretch_object", property(fget=stretch_getter, fset=None))

    return CustomStretchMixin


StretchStateMixin = custom_stretch_state_mixin(prefix="")
