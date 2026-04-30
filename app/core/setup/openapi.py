import traceback
from fastapi import FastAPI

def validate_openapi(app: FastAPI) -> None:
    """
    Force OpenAPI schema generation to catch Pydantic errors early.
    Prints full traceback and raises the exception if schema generation fails.
    """
    try:
        app.openapi_schema = app.openapi()
    except Exception as e:
        print("\n❌ ERROR: OpenAPI schema generation failed!")
        print("=" * 55)
        traceback.print_exc()
        print("=" * 55)
        raise e