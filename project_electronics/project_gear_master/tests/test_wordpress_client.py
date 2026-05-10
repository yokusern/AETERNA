from __future__ import annotations

import json

from publisher.wp_client import WordPressClient, WordPressPost


def test_wp_client_dry_run_archives_sample_payload(tmp_path):
    client = WordPressClient(
        base_url="https://example.com",
        username="",
        app_password="",
        dry_run=True,
        payload_archive=tmp_path,
    )

    result = client.create_post(
        WordPressPost(
            title="Test Electronics Post",
            content="<p>Hello</p>",
            status="draft",
            categories=("Electronics",),
            tags=("electronics", "test"),
            featured_media_id=123,
        )
    )

    assert result["ok"] is True
    payload = json.loads((tmp_path / "create_post_001.json").read_text(encoding="utf-8"))
    assert payload["status"] == "draft"
    assert payload["featured_media"] == 123
    assert payload["categories"] == ["Electronics"]


def test_wp_connection_dry_run_does_not_need_credentials(tmp_path):
    client = WordPressClient(
        base_url="https://example.com",
        username="",
        app_password="",
        dry_run=True,
        payload_archive=tmp_path,
    )

    result = client.test_connection()

    assert result["ok"] is True
    assert result["mode"] == "dry_run"
