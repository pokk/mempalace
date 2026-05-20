from _mcp_server_helpers import _get_collection, _patch_mcp_server


def test_add_drawer_skip_tag_short_circuits(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer

    before = col.count()
    result = tool_add_drawer(
        wing="w",
        room="r",
        content="Real content. <mempalace-skip> please do not file this.",
    )
    assert result["success"] is True
    assert result.get("skipped") is True
    assert result["reason"] == "mempalace_skip_tag"
    assert "drawer_id" not in result
    assert col.count() == before


def test_add_drawer_strips_private_blocks(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer

    content = (
        "Public preamble.\n"
        "<private>SECRET_TOKEN_abc123</private>\n"
        "Public body about decorators.\n"
        "<private>another\nmultiline\nsecret</private>\n"
        "Public tail."
    )
    result = tool_add_drawer(wing="w", room="r", content=content)
    assert result["success"] is True
    assert result.get("skipped") is not True
    stored = col.get(ids=[result["drawer_id"]], include=["documents"])
    doc = stored["documents"][0]
    assert "SECRET_TOKEN_abc123" not in doc
    assert "another\nmultiline\nsecret" not in doc
    assert "Public preamble." in doc
    assert "Public body about decorators." in doc
    assert "Public tail." in doc


def test_add_drawer_all_private_yields_skip(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer

    before = col.count()
    result = tool_add_drawer(
        wing="w",
        room="r",
        content="   <private>only secrets here</private>   \n  ",
    )
    assert result["success"] is True
    assert result.get("skipped") is True
    assert result["reason"] == "empty_after_private_strip"
    assert col.count() == before


def test_add_drawer_no_tags_unchanged(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer

    original = "Plain content with no tags. Includes < and > but no privacy markers."
    result = tool_add_drawer(wing="w", room="r", content=original)
    assert result["success"] is True
    stored = col.get(ids=[result["drawer_id"]], include=["documents"])
    assert stored["documents"][0] == original
