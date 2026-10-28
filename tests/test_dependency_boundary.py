import subprocess
import sys
import textwrap

SERVICE_ONLY = (
    "fastapi",
    "starlette",
    "pydantic",
    "uvicorn",
    "redis",
    "jwt",
    "multipart",
    "pandas",
)
CORE_MODULES = (
    "survey_structure",
    "survey_data_dictionary",
    "limesurvey_connector",
    "survey_structure",
    "limesurvey_connector.data_dictionary",
    "limesurvey_connector.limesurvey",
    "limesurvey_connector.remote",
)


def test_core_modules_import_without_optional_dependencies():
    script = textwrap.dedent(
        f"""
        import importlib, importlib.abc, sys

        class Block(importlib.abc.MetaPathFinder):
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in {SERVICE_ONLY!r}:
                    raise ImportError(f"optional dependency imported: {{name}}")
                return None

        sys.meta_path.insert(0, Block())
        for module in {CORE_MODULES!r}:
            importlib.import_module(module)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr


def test_ported_packages_are_independent_of_the_connector():
    script = textwrap.dedent(
        """
        import importlib, importlib.abc, sys

        class Block(importlib.abc.MetaPathFinder):
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] in {"limesurvey_connector", "citric", "defusedxml", "requests"}:
                    raise ImportError(f"survey_structure imported {name}")
                return None

        sys.meta_path.insert(0, Block())
        import survey_structure
        import survey_data_dictionary
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
