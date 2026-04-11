import hashlib
import json
from datetime import date
from pathlib import Path

from .base import Agent

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SourceScoutAgent(Agent):
    def __init__(self):
        super().__init__("source-scout")

    def run(self, context: dict) -> dict:
        client_id = context["client_id"]
        urls = context.get("urls", [])

        evidence_dir = PROJECT_ROOT / "regulatory_data" / client_id / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)

        created = []
        for url in urls:
            record = self._make_record(client_id, url=url, **context.get("metadata", {}))
            path = evidence_dir / f"{record['evidence_id']}.json"
            with open(path, "w") as f:
                json.dump(record, f, indent=2)
            created.append(record["evidence_id"])
            self.log(f"Ingested URL: {url}")

        return {"evidence_ids": created, "log": self.log_entries}

    def _make_record(self, client_id: str, url: str, **meta) -> dict:
        today = date.today().isoformat()
        hash_input = f"{client_id}:{url}:{today}"
        h = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        evidence_id = f"ev-{today[:7]}-{h}"
        return {
            "evidence_id": evidence_id,
            "client_id": client_id,
            "source_id": meta.get("source_id", "unknown"),
            "source_name": meta.get("source_name", "Unknown Source"),
            "url": url,
            "access_date": today,
            "document_title": meta.get("document_title", ""),
            "snippet": meta.get("snippet", ""),
            "hash": f"sha256:{hashlib.sha256(hash_input.encode()).hexdigest()}",
            "attached_by": "source-scout-agent",
            "confidence": meta.get("confidence", 0.85),
            "topic": meta.get("topic", "unknown"),
            "related_regulation_id": meta.get("related_regulation_id", ""),
        }
