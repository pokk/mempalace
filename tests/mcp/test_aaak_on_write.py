from _mcp_server_helpers import _get_collection, _patch_mcp_server


def test_add_drawer_emits_aaak_index_entry(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, drawer_col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer
    from mempalace.palace import get_closets_collection

    original = (
        "Decision: switched the auth pipeline from Firebase to Supabase to align "
        "with the cross-platform rewrite. Alice approved on 2026-05-12."
    )
    result = tool_add_drawer(
        wing="work",
        room="decisions",
        content=original,
        source_file="meeting-notes.md",
    )
    assert result["success"] is True
    drawer_id = result["drawer_id"]
    stored = drawer_col.get(ids=[drawer_id], include=["documents"])
    assert stored["documents"][0] == original
    closet_col = get_closets_collection(palace_path, create=False)
    closet = closet_col.get(ids=[drawer_id], include=["documents", "metadatas"])
    assert closet["ids"] == [drawer_id]
    assert closet["documents"][0]
    assert closet["documents"][0] != original
    meta = closet["metadatas"][0]
    assert meta["wing"] == "work"
    assert meta["room"] == "decisions"
    assert "compression_ratio" in meta
    assert "original_tokens" in meta


def test_aaak_index_failure_does_not_break_drawer(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, drawer_col = _get_collection(palace_path, create=True)
    del _client
    import mempalace.mcp_server as mcp_server
    from mempalace.mcp_server import tool_add_drawer

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated closets failure")

    monkeypatch.setattr(mcp_server, "_emit_aaak_index_sync", boom)

    result = tool_add_drawer(wing="w", room="r", content="content that must persist")
    assert result["success"] is True
    stored = drawer_col.get(ids=[result["drawer_id"]], include=["documents"])
    assert stored["documents"][0] == "content that must persist"


def test_aaak_index_idempotent_when_drawer_already_exists(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, _drawer_col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer
    from mempalace.palace import get_closets_collection

    content = "Decision: ship v3.3.5 with AAAK closets-on-write index."

    first = tool_add_drawer(wing="w", room="r", content=content)
    assert first["success"] is True
    assert "reason" not in first

    closet_col = get_closets_collection(palace_path, create=False)
    count_after_first = closet_col.count()
    assert count_after_first == 1

    second = tool_add_drawer(wing="w", room="r", content=content)
    assert second["success"] is True
    assert second.get("reason") == "already_exists"
    assert second["drawer_id"] == first["drawer_id"]
    closet_col = get_closets_collection(palace_path, create=False)
    assert closet_col.count() == count_after_first


def test_already_exists_path_repairs_missing_closet(monkeypatch, config, palace_path, kg):
    _patch_mcp_server(monkeypatch, config, kg)
    _client, _drawer_col = _get_collection(palace_path, create=True)
    del _client
    from mempalace.mcp_server import tool_add_drawer
    from mempalace.palace import get_closets_collection

    content = "Operational note: closet repair on idempotent retry."
    first = tool_add_drawer(wing="w", room="r", content=content)
    assert first["success"] is True
    drawer_id = first["drawer_id"]

    closet_col = get_closets_collection(palace_path, create=False)
    assert closet_col.count() == 1
    closet_col.delete(ids=[drawer_id])
    assert closet_col.count() == 0

    second = tool_add_drawer(wing="w", room="r", content=content)
    assert second["success"] is True
    assert second.get("reason") == "already_exists"
    closet_col = get_closets_collection(palace_path, create=False)
    assert closet_col.count() == 1
    repaired = closet_col.get(ids=[drawer_id], include=["documents", "metadatas"])
    assert repaired["ids"] == [drawer_id]
    assert repaired["documents"] and repaired["documents"][0]
