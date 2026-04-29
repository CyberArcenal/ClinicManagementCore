import pkgutil
import importlib
import app.modules

def setup_signals() -> None:
    """
    Automatically discover all modules under app.modules that have an 'event'
    submodule with a `register_events()` function, and call it.
    """
    for module_info in pkgutil.iter_modules(app.modules.__path__):
        module_name = module_info.name
        try:
            # Try to import the module's event package
            event_module = importlib.import_module(f"app.modules.{module_name}.event")
            if hasattr(event_module, "register_events") and callable(event_module.register_events):
                event_module.register_events()
                print(f"✅ Registered signals for module: {module_name}")
        except ModuleNotFoundError:
            # No event folder or no __init__.py – skip silently
            pass
        except Exception as e:
            print(f"⚠️ Failed to register signals for {module_name}: {e}")