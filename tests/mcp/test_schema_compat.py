def test_tool_input_schemas_are_top_level_objects_without_union_keywords():
    from mempalace import mcp_server

    forbidden_top_level = {"oneOf", "anyOf", "allOf", "enum", "not"}
    violations = []

    for tool_name, tool in mcp_server.TOOLS.items():
        schema = tool["input_schema"]
        if schema.get("type") != "object":
            violations.append(f"{tool_name}: type={schema.get('type')!r}")
        present = forbidden_top_level.intersection(schema)
        if present:
            violations.append(f"{tool_name}: forbidden top-level keys={sorted(present)!r}")

    assert not violations
