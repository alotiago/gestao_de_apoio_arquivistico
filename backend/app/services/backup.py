"""Serviço simples de backup incremental e restauração parcial."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime


class BackupStore:
    def __init__(self) -> None:
        self.snapshots: dict[str, dict] = {}

    def create_snapshot(self, payload: dict) -> dict:
        snapshot_id = str(uuid.uuid4())
        snapshot = {
            "id": snapshot_id,
            "created_at": datetime.now(UTC).isoformat(),
            **payload,
        }
        self.snapshots[snapshot_id] = snapshot
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> dict | None:
        return self.snapshots.get(snapshot_id)

    def list_snapshots(self) -> list[dict]:
        return sorted(self.snapshots.values(), key=lambda item: item["created_at"], reverse=True)


backup_store = BackupStore()
