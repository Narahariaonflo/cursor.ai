"""Architecture dependency-rule tests."""

import ast
from pathlib import Path


_FORBIDDEN_DOMAIN_ROOTS = {
    "adapters",
    "application",
    "bootstrap",
    "config",
    "fastapi",
    "playwright",
    "ports",
    "pydantic",
    "sqlite3",
}


def test_domain_has_no_outward_dependencies() -> None:
    """Domain modules import only standard library and domain modules."""
    domain_root = Path(__file__).resolve().parents[2] / "src" / "domain"
    violations: list[str] = []

    for module_path in domain_root.rglob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            imported_roots = _imported_roots(node)
            for root in imported_roots.intersection(_FORBIDDEN_DOMAIN_ROOTS):
                violations.append(f"{module_path.relative_to(domain_root)} imports {root}")

    assert violations == []


def test_application_does_not_import_infrastructure() -> None:
    """Application modules depend on domain and ports, never adapters/bootstrap."""
    _assert_layer_excludes("application", {"adapters", "bootstrap", "fastapi", "sqlite3"})


def test_ports_do_not_import_implementations() -> None:
    """Port contracts remain independent of application and adapters."""
    _assert_layer_excludes("ports", {"adapters", "application", "bootstrap", "fastapi"})


def _assert_layer_excludes(layer: str, forbidden: set[str]) -> None:
    """Assert every module in a layer excludes forbidden import roots."""
    layer_root = Path(__file__).resolve().parents[2] / "src" / layer
    violations: list[str] = []
    for module_path in layer_root.rglob("*.py"):
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            for root in _imported_roots(node).intersection(forbidden):
                violations.append(f"{module_path.relative_to(layer_root)} imports {root}")
    assert violations == []


def _imported_roots(node: ast.AST) -> set[str]:
    """Return top-level package names imported by an AST node."""
    if isinstance(node, ast.Import):
        return {alias.name.split(".", maxsplit=1)[0] for alias in node.names}
    if isinstance(node, ast.ImportFrom) and node.module:
        return {node.module.split(".", maxsplit=1)[0]}
    return set()
