import importlib
import pkgutil
import traceback
from fastapi import FastAPI, APIRouter
import app.modules as modules_pkg


def discover_and_register_routers(app: FastAPI, api_prefix: str = "/api/v1") -> None:
    """
    Dynamically discover all modules under app.modules that have
    api/v1/__init__.py with a 'router' attribute, and include them.
    """
    for module_info in pkgutil.iter_modules(modules_pkg.__path__):
        module_name = module_info.name
        # print(f"🔍 Checking module: {module_name}")
        try:
            api_module_path = f"app.modules.{module_name}.api.v1"
            api_module = importlib.import_module(api_module_path)
            if hasattr(api_module, "router") and isinstance(
                api_module.router, APIRouter
            ):
                app.include_router(api_module.router, prefix=api_prefix)
                print(f"✅ Registered router for module: {module_name}")
            else:
                print(
                    f"⚠️ Module {module_name} has api/v1 but no 'router' attribute or not an APIRouter"
                )
        except ModuleNotFoundError:
            print(f"⏭️ No api/v1 for module: {module_name} (skipping)")
        except Exception as e:
            traceback.print_exc()
            print(f"❌ Failed to load router for {module_name}: {e}")
