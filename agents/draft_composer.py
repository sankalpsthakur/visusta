"""
DraftComposerAgent — turns changelog + evidence + template sections into a
structured draft revision (list of DraftSection-compatible dicts).

Input context keys:
    changelog       list[dict]  — regulatory change entries
    evidence        list[dict]  — evidence records (optional)
    template_sections list[dict] — section definitions from a template version
    locale          str         — BCP-47 tag, e.g. "en", "de"

Output:
    {
        "sections": list[dict],  # each matches DraftSection shape
        "locale":   str,
        "log":      list[dict],
    }
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from .base import Agent
from .llm import LLMInterface, StubLLM, get_llm


class DraftComposerAgent(Agent):
    def __init__(self, llm: LLMInterface | None = None):
        super().__init__("draft-composer")
        self._llm = llm if llm is not None else get_llm()

    def run(self, context: dict) -> dict:
        changelog: list[dict] = context.get("changelog", [])
        changelog_payload: dict[str, Any] = context.get("changelog_payload", {})
        evidence: list[dict] = context.get("evidence", [])
        template_sections: list[dict] = context.get("template_sections", [])
        locale: str = context.get("locale", "en")

        self.log(f"Composing draft for locale={locale}, changelog_entries={len(changelog)}")

        if isinstance(self._llm, StubLLM):
            raw_sections = self._compose_without_llm(
                changelog=changelog,
                changelog_payload=changelog_payload,
                evidence=evidence,
                template_sections=template_sections,
                locale=locale,
            )
        else:
            prompt = self._build_prompt(changelog, evidence, template_sections, locale)
            result: dict[str, Any] = self._llm.generate_structured(prompt)
            raw_sections = result.get("sections", [])

        sections = self._hydrate_sections(raw_sections, locale, template_sections)
        self.log(f"Composed {len(sections)} sections")

        return {"sections": sections, "locale": locale, "log": self.log_entries}

    # ── private ────────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        changelog: list[dict],
        evidence: list[dict],
        template_sections: list[dict],
        locale: str,
    ) -> str:
        section_names = [s.get("heading", "") for s in template_sections]
        change_summaries = [
            f"- {c.get('title', c.get('description', 'change'))}"
            for c in changelog[:20]
        ]
        evidence_snippets = [
            f"- [{e.get('source_name', '')}] {e.get('snippet', '')}"
            for e in evidence[:10]
        ]
        section_schema = ", ".join(
            f'{{"heading": "{name}", "blocks": [{{"type": "paragraph", "text": "..."}}], "facts": ["..."], "citations": ["..."]}}'
            for name in section_names
        )
        return (
            f"You are a regulatory intelligence analyst. Compose a report in locale={locale}.\n\n"
            f"CHANGES:\n" + "\n".join(change_summaries) + "\n\n"
            f"EVIDENCE:\n" + "\n".join(evidence_snippets) + "\n\n"
            f"Write one section per heading: {', '.join(section_names)}.\n"
            f"Each section should have substantive paragraphs analyzing the regulatory changes.\n\n"
            f"Return EXACTLY this JSON structure:\n"
            f'{{"sections": [{section_schema}]}}\n\n'
            f"Rules:\n"
            f'- Each block must have "type" (paragraph/bullet_list) and "text" (string content)\n'
            f"- facts: key data points as a list of strings\n"
            f"- citations: source references as a list of strings\n"
            f"- Write substantive analysis, not placeholders"
        )

    def _hydrate_sections(
        self,
        raw_sections: list[dict],
        locale: str,
        template_sections: list[dict],
    ) -> list[dict]:
        """Merge LLM output with template section definitions, adding IDs."""
        # Build a heading→template_section index for merging
        tpl_index = {
            s.get("heading", "").lower(): s
            for s in template_sections
        }

        hydrated = []
        for raw in raw_sections:
            heading = raw.get("heading", "")
            tpl = tpl_index.get(heading.lower(), {})
            # Normalize LLM block format → DB block format
            raw_blocks = raw.get("blocks", [])
            normalized_blocks = []
            for i, blk in enumerate(raw_blocks):
                normalized_blocks.append({
                    "block_id": blk.get("block_id", f"b{i + 1}"),
                    "block_type": blk.get("block_type", blk.get("type", "paragraph")),
                    "content": blk.get("content", blk.get("text", "")),
                    "metadata": blk.get("metadata", {}),
                })

            hydrated.append({
                "section_id": str(uuid.uuid4()),
                "heading": heading or tpl.get("heading", ""),
                "locale": locale,
                "blocks": normalized_blocks,
                "facts": raw.get("facts", []),
                "citations": raw.get("citations", []),
                "translation_status": "original",
                "approval_status": "pending",
                # Carry forward template metadata if present
                "template_section_id": tpl.get("section_id"),
            })

        # If LLM returned nothing, create a stub for each template section
        if not hydrated and template_sections:
            for tpl in template_sections:
                hydrated.append({
                    "section_id": str(uuid.uuid4()),
                    "heading": tpl.get("heading", ""),
                    "locale": locale,
                    "blocks": [{"type": "paragraph", "text": ""}],
                    "facts": [],
                    "citations": [],
                    "translation_status": "original",
                    "approval_status": "pending",
                    "template_section_id": tpl.get("section_id"),
                })

        return hydrated

    def _compose_without_llm(
        self,
        *,
        changelog: list[dict],
        changelog_payload: dict[str, Any],
        evidence: list[dict],
        template_sections: list[dict],
        locale: str,
    ) -> list[dict]:
        payload = self._normalize_payload(changelog, changelog_payload)
        evidence_by_id = {
            evidence_item.get("evidence_id"): evidence_item
            for evidence_item in evidence
            if isinstance(evidence_item, dict) and evidence_item.get("evidence_id")
        }
        change_entries = self._extract_change_entries(payload, changelog)
        sections = template_sections or [
            {"section_id": "executive_summary", "heading": "Executive Summary"},
            {"section_id": "critical_actions", "heading": "Critical Actions"},
        ]

        rendered = []
        for index, template_section in enumerate(sections):
            heading = template_section.get("heading", f"Section {index + 1}")
            section_id = str(template_section.get("section_id") or "")
            blocks, facts, citations = self._render_section(
                section_id=section_id,
                heading=heading,
                payload=payload,
                change_entries=change_entries,
                evidence_by_id=evidence_by_id,
                index=index,
            )
            rendered.append(
                {
                    "section_id": str(uuid.uuid4()),
                    "heading": heading,
                    "locale": locale,
                    "blocks": blocks,
                    "facts": facts,
                    "citations": citations,
                }
            )
        return rendered

    def _normalize_payload(
        self,
        changelog: list[dict],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        if payload:
            return payload
        if changelog and isinstance(changelog[0], dict):
            candidate = changelog[0]
            if any(key in candidate for key in ("executive_summary", "critical_actions", "sections")):
                return candidate
        return {}

    def _extract_change_entries(
        self,
        payload: dict[str, Any],
        changelog: list[dict],
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for key in (
            "critical_actions",
            "new_regulations",
            "status_changes",
            "content_updates",
            "timeline_changes",
            "metadata_updates",
            "ended_regulations",
            "carried_forward",
        ):
            value = payload.get(key)
            if isinstance(value, list):
                entries.extend(item for item in value if isinstance(item, dict))
        if entries:
            return entries
        return [item for item in changelog if isinstance(item, dict)]

    def _render_section(
        self,
        *,
        section_id: str,
        heading: str,
        payload: dict[str, Any],
        change_entries: list[dict[str, Any]],
        evidence_by_id: dict[str, dict[str, Any]],
        index: int,
    ) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
        key = "_".join(part for part in (self._normalize_key(section_id), self._normalize_key(heading)) if part)
        section_detail = self._match_detail_section(payload, heading, index)

        if "executive" in key:
            summary = payload.get("executive_summary") or self._derive_executive_summary(change_entries, payload)
            blocks = self._paragraph_blocks(summary or "No executive summary is available for this reporting period.")
            facts = self._summary_facts(payload, change_entries)
            citations = self._collect_citations(payload, section_detail, evidence_by_id)
            return blocks, facts, citations

        if "critical" in key or "action" in key:
            items = self._derive_action_items(payload, change_entries)
            blocks = [{"type": "bullet_list", "text": "\n".join(items)}] if items else self._paragraph_blocks(
                "No critical actions are currently recorded for this reporting period."
            )
            return blocks, items[:4], self._collect_citations(payload, section_detail, evidence_by_id)

        if "topic" in key and "status" in key:
            items = self._topic_status_items(payload)
            blocks = [{"type": "bullet_list", "text": "\n".join(items)}] if items else self._paragraph_blocks(
                "Topic-level monitoring status is not available."
            )
            return blocks, items[:4], self._collect_citations(payload, section_detail, evidence_by_id)

        if "change" in key or "regulatory" in key:
            items = self._change_log_items(change_entries)
            blocks = [{"type": "bullet_list", "text": "\n".join(items)}] if items else self._paragraph_blocks(
                "No material regulatory changes were captured for this reporting period."
            )
            facts = [f"{len(change_entries)} tracked change items"] if change_entries else []
            return blocks, facts, self._collect_citations(payload, section_detail, evidence_by_id)

        if "impact" in key:
            items = self._impact_items(change_entries)
            blocks = [{"type": "bullet_list", "text": "\n".join(items)}] if items else self._paragraph_blocks(
                "No quantified impact summary is currently available."
            )
            return blocks, items[:4], self._collect_citations(payload, section_detail, evidence_by_id)

        if "reference" in key:
            citations = self._collect_citations(payload, section_detail, evidence_by_id)
            blocks = self._paragraph_blocks("Reference sources supporting this draft are listed below.")
            return blocks, [], citations

        if section_detail:
            blocks = self._detail_blocks(section_detail)
            facts = self._detail_facts(section_detail)
            citations = self._collect_citations(payload, section_detail, evidence_by_id)
            return blocks, facts, citations

        fallback_items = self._change_log_items(change_entries)[:3]
        if fallback_items:
            return [{"type": "bullet_list", "text": "\n".join(fallback_items)}], [], self._collect_citations(
                payload, {}, evidence_by_id
            )
        return self._paragraph_blocks(f"No draft content is available yet for {heading}."), [], []

    def _normalize_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

    def _match_detail_section(
        self,
        payload: dict[str, Any],
        heading: str,
        index: int,
    ) -> dict[str, Any]:
        sections = payload.get("sections")
        if not isinstance(sections, list):
            return {}
        normalized_heading = self._normalize_key(heading)
        for section in sections:
            if not isinstance(section, dict):
                continue
            if self._normalize_key(section.get("heading", "")) == normalized_heading:
                return section
        if index < len(sections) and isinstance(sections[index], dict):
            return sections[index]
        return {}

    def _paragraph_blocks(self, text: str) -> list[dict[str, Any]]:
        paragraphs = [part.strip() for part in str(text).split("\n\n") if part.strip()]
        return [{"type": "paragraph", "text": paragraph} for paragraph in paragraphs] or [{"type": "paragraph", "text": ""}]

    def _derive_executive_summary(self, change_entries: list[dict[str, Any]], payload: dict[str, Any]) -> str:
        period = payload.get("screening_period", "the current period")
        key_titles = [
            entry.get("title") or entry.get("summary") or entry.get("heading")
            for entry in change_entries[:3]
            if isinstance(entry, dict)
        ]
        title_text = "; ".join(title for title in key_titles if title)
        if title_text:
            return f"{period} includes the following priority developments: {title_text}."
        return f"{period} does not yet contain a structured executive summary."

    def _derive_action_items(self, payload: dict[str, Any], change_entries: list[dict[str, Any]]) -> list[str]:
        items: list[str] = []
        raw_actions = payload.get("critical_actions")
        if isinstance(raw_actions, list):
            for action in raw_actions:
                if isinstance(action, dict):
                    summary = action.get("summary") or action.get("action_required") or action.get("title")
                    deadline = action.get("deadline") or action.get("enforcement_date")
                    if summary:
                        items.append(f"{summary} ({deadline})" if deadline else str(summary))
                elif action:
                    items.append(str(action))
        if items:
            return items[:6]

        for entry in change_entries:
            if not isinstance(entry, dict):
                continue
            action = entry.get("action_required") or entry.get("summary")
            title = entry.get("title")
            deadline = entry.get("deadline") or entry.get("enforcement_date")
            if action:
                line = f"{title}: {action}" if title and action != title else str(action)
                items.append(f"{line} ({deadline})" if deadline else line)
        return items[:6]

    def _topic_status_items(self, payload: dict[str, Any]) -> list[str]:
        statuses = payload.get("topic_change_statuses")
        if not isinstance(statuses, dict):
            return []
        items = []
        for topic, status in statuses.items():
            if not isinstance(status, dict):
                continue
            changed = "changed" if status.get("changed_since_last") else "no material change"
            count = status.get("changes_detected", 0)
            items.append(f"{topic.replace('_', ' ').title()}: {changed} ({count} tracked changes)")
        return items

    def _change_log_items(self, change_entries: list[dict[str, Any]]) -> list[str]:
        items = []
        for entry in change_entries[:8]:
            if not isinstance(entry, dict):
                continue
            title = entry.get("title") or entry.get("heading") or entry.get("summary") or "Regulatory update"
            summary = entry.get("summary") or entry.get("description")
            if summary and summary != title:
                items.append(f"{title}: {summary}")
            else:
                items.append(str(title))
        return items

    def _impact_items(self, change_entries: list[dict[str, Any]]) -> list[str]:
        items = []
        for entry in change_entries[:5]:
            if not isinstance(entry, dict):
                continue
            severity = entry.get("severity")
            title = entry.get("title") or entry.get("summary")
            deadline = entry.get("enforcement_date") or entry.get("effective_date")
            fragments = [fragment for fragment in (title, severity, deadline) if fragment]
            if fragments:
                items.append(" | ".join(str(fragment) for fragment in fragments))
        return items

    def _detail_blocks(self, section_detail: dict[str, Any]) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        for paragraph in section_detail.get("paragraphs", []):
            if paragraph:
                blocks.append({"type": "paragraph", "text": str(paragraph)})
        callout = section_detail.get("callout")
        if callout:
            blocks.append({"type": "paragraph", "text": f"Priority: {callout}"})
        table = section_detail.get("table")
        if isinstance(table, dict):
            rows = table.get("rows") or []
            if rows:
                items = [" | ".join(str(cell) for cell in row if cell not in (None, "")) for row in rows[:5]]
                if items:
                    blocks.append({"type": "bullet_list", "text": "\n".join(items)})
        return blocks or self._paragraph_blocks(section_detail.get("heading", ""))

    def _detail_facts(self, section_detail: dict[str, Any]) -> list[str]:
        facts = []
        table = section_detail.get("table")
        if isinstance(table, dict):
            headers = table.get("headers") or []
            rows = table.get("rows") or []
            for row in rows[:3]:
                if headers and isinstance(row, list):
                    label = row[0] if row else None
                    value = row[-1] if row else None
                    if label and value:
                        facts.append(f"{label}: {value}")
        return facts[:4]

    def _summary_facts(self, payload: dict[str, Any], change_entries: list[dict[str, Any]]) -> list[str]:
        facts = []
        if payload.get("screening_period"):
            facts.append(f"Reporting period: {payload['screening_period']}")
        if payload.get("total_changes_detected") is not None:
            facts.append(f"Changes detected: {payload['total_changes_detected']}")
        elif change_entries:
            facts.append(f"Tracked change items: {len(change_entries)}")
        if payload.get("total_regulations_tracked") is not None:
            facts.append(f"Regulations tracked: {payload['total_regulations_tracked']}")
        return facts[:4]

    def _collect_citations(
        self,
        payload: dict[str, Any],
        section_detail: dict[str, Any],
        evidence_by_id: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build citations as {label, url} dicts.

        Prior to this, title and URL were flattened into a single string so the
        URL was unrecoverable downstream. Keep both fields separate so the
        renderer can emit a real anchor tag.
        """
        citations: list[dict[str, Any]] = []
        references = payload.get("references")
        if isinstance(references, list):
            for reference in references[:4]:
                if not isinstance(reference, dict):
                    continue
                label = reference.get("citation") or reference.get("url")
                if not label:
                    continue
                url = reference.get("url")
                citations.append({"label": str(label), "url": str(url) if url else None})
        evidence_refs = section_detail.get("evidence_refs") if isinstance(section_detail, dict) else []
        if isinstance(evidence_refs, list):
            for evidence_id in evidence_refs[:4]:
                evidence = evidence_by_id.get(evidence_id)
                if not evidence:
                    continue
                title = evidence.get("document_title") or evidence.get("source_name") or evidence_id
                url = evidence.get("url")
                citations.append({"label": str(title), "url": str(url) if url else None})
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, str | None]] = set()
        for citation in citations:
            key = (citation["label"], citation.get("url"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(citation)
        return deduped[:6]
