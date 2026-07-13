from glue.config import stretches
from glue.viewers.matplotlib.state import (
    DeferredDrawDictCallbackProperty as DDDCProperty,
    DeferredDrawSelectionCallbackProperty as DDSCProperty,
)

__all__ = ["create_stretch_state_mixin", "StretchStateMixin"]


def create_stretch_state_mixin(stretch_name,
                               stretch_params_name=None,
                               stretch_object_name=None):

    stretch_params_name = stretch_params_name or f"{stretch_name}_parameters"
    stretch_object_name = stretch_object_name or f"{stretch_name}_object"
    internal_stretch_object_name = f"_{stretch_object_name}"
    setup_name = f"_{stretch_name}_set_up"
    reset_name = f"_reset_{stretch_name}"
    sync_name = f"_sync_{stretch_name}_parameters"
    setup_callback_name = f"setup_{stretch_name}_callback"

    def get_stretch_object(self):
        if not getattr(self, setup_name, False):
            raise Exception(f"{setup_callback_name} has not been called")
        return getattr(self, internal_stretch_object_name)

    def setup_stretch_callback(self):
        getattr(type(self), stretch_name).set_choices(self, list(stretches.members))
        getattr(type(self), stretch_name).set_display_func(self, stretches.display_func)
        getattr(self, reset_name)()
        self.add_callback(stretch_name, getattr(self, reset_name))
        self.add_callback(stretch_params_name, getattr(self, sync_name))
        setattr(self, setup_name, True)

    def _sync_stretch_parameters(self, *args):
        stretch_object = getattr(self, stretch_object_name)
        for key, value in getattr(self, stretch_params_name).items():
            if hasattr(stretch_object, key):
                setattr(stretch_object, key, value)
            else:
                raise ValueError(
                    f"Stretch object {stretch_object.__class__.__name__} has no attribute {key}"
                )

    def _reset_stretch(self, *args):
        setattr(self, internal_stretch_object_name, stretches.members[getattr(self, stretch_name)]())
        getattr(self, stretch_params_name).clear()


    class CustomStretchStateMixin:
        pass

    setattr(CustomStretchStateMixin, stretch_name, DDSCProperty(
        docstring="The stretch used to render the layer, "
           "which should be one of ``linear``, "
           "``sqrt``, ``log``, or ``arcsinh``"
    ))
    setattr(CustomStretchStateMixin, stretch_params_name, DDDCProperty(
        docstring="Keyword arguments to pass to the stretch"
    ))
    setattr(CustomStretchStateMixin, stretch_object_name, property(get_stretch_object, None))
    setattr(CustomStretchStateMixin, setup_callback_name, setup_stretch_callback)
    setattr(CustomStretchStateMixin, reset_name, _reset_stretch)
    setattr(CustomStretchStateMixin, sync_name, _sync_stretch_parameters)

    return CustomStretchStateMixin


# The default stretch state mixin
StretchStateMixin = create_stretch_state_mixin(stretch_name="stretch",
                                               stretch_params_name="stretch_parameters",
                                               stretch_object_name="stretch_object")
