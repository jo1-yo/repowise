"""flow_entries: route decorator prefix resolution from APIRouter bindings."""

from __future__ import annotations

import networkx as nx

from repowise.core.generation.flow_entries import (
    ROUTE,
    Entry,
    _decorated_entries,
    line_reader,
)


def _add(g: nx.DiGraph, node: str, start: int, end: int, **attrs) -> None:
    path, name = node.split("::", 1)
    g.add_node(path, node_type="file", is_test=False)
    g.add_node(
        node,
        node_type="symbol",
        kind="function",
        name=name,
        file_path=path,
        start_line=start,
        end_line=end,
        visibility="public",
        **attrs,
    )


def _entries(g: nx.DiGraph, source_map: dict[str, bytes]) -> list[Entry]:
    read = line_reader(None, source_map)
    return list(_decorated_entries(g, program="", scripts={}, read=read))


# --- prefix from APIRouter(prefix=...) ---


def test_route_with_apirouter_prefix():
    g = nx.DiGraph()
    _add(
        g,
        "app/api/r1.py::stream1",
        10,
        20,
        decorators=['@router.post("/turns/stream")'],
    )
    source = {
        "app/api/r1.py": b'router = APIRouter(prefix="/api/coach")\n'
        b'@router.post("/turns/stream")\n'
        b"def stream1(): ...\n",
    }
    entries = _entries(g, source)
    assert len(entries) == 1
    assert entries[0].kind == ROUTE
    assert entries[0].public == "/api/coach/turns/stream"


def test_route_with_include_router_prefix_on_same_file():
    """An include_router prefix lives in a different file and is not resolved here."""
    g = nx.DiGraph()
    _add(
        g,
        "app/routes.py::list_items",
        5,
        15,
        decorators=['@items.get("/")'],
    )
    source = {
        "app/routes.py": b'items = APIRouter(prefix="/items")\n'
        b'@items.get("/")\n'
        b"def list_items(): ...\n",
    }
    entries = _entries(g, source)
    assert len(entries) == 1
    assert entries[0].public == "/items/"


def test_route_without_prefix():
    """A route on a router with no prefix keeps its literal path."""
    g = nx.DiGraph()
    _add(
        g,
        "app/main.py::health",
        1,
        5,
        decorators=['@app.get("/health")'],
    )
    source = {
        "app/main.py": b"app = FastAPI()\n"
        b'@app.get("/health")\n'
        b"def health(): ...\n",
    }
    entries = _entries(g, source)
    assert len(entries) == 1
    assert entries[0].public == "/health"


def test_flask_style_route_unchanged():
    """A Flask-style route decorator is not affected by the APIRouter prefix logic."""
    g = nx.DiGraph()
    _add(
        g,
        "app/views.py::index",
        1,
        5,
        decorators=['@app.route("/index")'],
    )
    source = {
        "app/views.py": b'@app.route("/index")\ndef index(): ...\n',
    }
    entries = _entries(g, source)
    assert len(entries) == 1
    assert entries[0].public == "/index"
