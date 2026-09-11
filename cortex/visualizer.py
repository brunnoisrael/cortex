"""Cortex Visualizer (Onda 9) — standalone visual provenance graph generator."""

from __future__ import annotations

import html as _html
import json
from pathlib import Path

from cortex.storage.store import KnowledgeStore


def _generate_pyvis_html(store: KnowledgeStore, focus_id: str | None = None) -> str | None:
    """Render an interactive graph with optional pyvis.

    Pyvis is intentionally imported only at render time.  Its output is
    treated as untrusted HTML, so all knowledge fields are escaped before
    being passed as labels/titles.  Any incompatibility falls back to the
    deterministic standalone renderer below.
    """
    try:
        from pyvis.network import Network

        network = Network(
            height="800px", width="100%", directed=True,
            bgcolor="#0f172a", font_color="#f8fafc",
        )
        network.set_options(
            '{"interaction":{"hover":true,"navigationButtons":true},'
            '"physics":{"stabilization":{"iterations":150}}}'
        )
        metadata = []
        for entity in store.all_entities():
            entity_id = str(entity.id or "")
            statement = _html.escape(str(entity.statement or ""), quote=True)
            title = _html.escape(
                f"{entity.type.value} | {entity.authority.value} | "
                f"confidence={entity.confidence} | status={entity.status.value}",
                quote=True,
            )
            network.add_node(
                entity_id,
                label=statement[:120],
                title=title,
                color="#38bdf8" if entity_id == focus_id else None,
            )
            metadata.append({"id": entity_id, "statement": statement})
            for rel_type, source_entity in store.related(entity.id, direction="in"):
                network.add_edge(
                    str(source_entity.id), entity_id,
                    label=_html.escape(str(rel_type), quote=True),
                )
        rendered = network.generate_html(notebook=False)
        if not rendered.lstrip().lower().startswith("<!doctype html>"):
            rendered = "<!DOCTYPE html>\n" + rendered
        if "Cortex Knowledge Provenance Graph" not in rendered:
            rendered = rendered.replace(
                "<head>",
                "<head><title>Cortex Knowledge Provenance Graph</title>",
                1,
            )
        # Keep an escaped, machine-readable copy of the statements in the
        # document.  This makes provenance inspectable without relying on
        # pyvis' internal serialization and preserves the XSS contract.
        metadata_json = json.dumps(metadata, ensure_ascii=False).replace("</", "<\\/")
        payload = (
            '<script type="application/json" id="cortex-provenance-data">'
            f"{metadata_json}</script>"
        )
        rendered = rendered.replace("</body>", payload + "</body>")
        return rendered
    except Exception:
        return None


def generate_provenance_graph_html(store: KnowledgeStore, focus_id: str | None = None) -> str:
    """Generate standalone HTML string displaying provenance graph nodes and edges (Onda 9)."""
    pyvis_html = _generate_pyvis_html(store, focus_id)
    if pyvis_html is not None:
        return pyvis_html

    entities = store.all_entities()
    nodes = []
    links = []

    for e in entities:
        is_focused = (e.id == focus_id)
        nodes.append({
            "id": _html.escape(str(e.id or "")),
            "statement": _html.escape(str(e.statement or "")),
            "type": e.type.value,
            "authority": e.authority.value,
            "status": e.status.value,
            "confidence": e.confidence,
            "focused": is_focused,
            "scope": e.scope,
        })

        rel_in = store.related(e.id, direction="in")
        for rel_type, source_ent in rel_in:
            links.append({
                "source": source_ent.id,
                "target": e.id,
                "label": rel_type,
            })

    nodes_json = json.dumps(nodes, ensure_ascii=False).replace("</", "<\\/")
    links_json = json.dumps(links, ensure_ascii=False).replace("</", "<\\/")
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cortex Provenance & Confidence Graph</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        h1 {{ color: #38bdf8; font-size: 1.5rem; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
        .subtitle {{ color: #94a3b8; font-size: 0.9rem; margin-bottom: 20px; }}
        .container {{ display: flex; flex-direction: column; gap: 15px; }}
        .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin-bottom: 10px; }}
        .card.focused {{ border-color: #38bdf8; box-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-right: 5px; }}
        .badge-adr {{ background: #0284c7; color: white; }}
        .badge-correnda {{ background: #e11d48; color: white; }}
        .badge-fix {{ background: #16a34a; color: white; }}
        .badge-intention {{ background: #9333ea; color: white; }}
        .badge-negative {{ background: #ea580c; color: white; }}
        .meta {{ font-size: 0.85rem; color: #cbd5e1; margin-top: 5px; }}
        .links-list {{ font-size: 0.85rem; color: #38bdf8; margin-top: 8px; padding-left: 15px; }}
    </style>
</head>
<body>
    <h1>Cortex Knowledge Provenance Graph</h1>
    <div class="subtitle">Visualizing provenance, authority, and evidence chains (PRD §49 & §50)</div>
    
    <div class="container">
        <div id="graph-list"></div>
    </div>

    <script>
        const nodes = {nodes_json};
        const links = {links_json};
        
        const container = document.getElementById('graph-list');
        nodes.forEach(node => {{
            const card = document.createElement('div');
            card.className = 'card' + (node.focused ? ' focused' : '');
            
            const badgeKey = node.type.replace('_knowledge', '');
            const badgeClass = 'badge badge-' + badgeKey;
            const relatedLinks = links.filter(l => l.target === node.id || l.source === node.id);
            
            let linksHtml = '';
            if (relatedLinks.length > 0) {{
                linksHtml = '<ul class="links-list">' + relatedLinks.map(l => 
                    `<li>${{l.source}} &rarr; [${{l.label}}] &rarr; ${{l.target}}</li>`
                ).join('') + '</ul>';
            }}
            
            card.innerHTML = `
                <div>
                    <span class="${{badgeClass}}">${{node.type}}</span>
                    <strong>${{node.id}}</strong>
                </div>
                <div class="meta" style="margin-top: 8px;"></div>
                <div class="meta">Authority: <strong>${{node.authority}}</strong> | Confidence: <strong>${{node.confidence}}</strong> | Status: <strong>${{node.status}}</strong></div>
                ${{linksHtml}}
            `;
            // Use textContent for statement to prevent XSS
            const statementDiv = card.querySelector('.meta');
            if (statementDiv) {{
                statementDiv.textContent = node.statement;
            }}
            container.appendChild(card);
        }});
    </script>
</body>
</html>"""
    return html_content


def export_provenance_graph_file(store: KnowledgeStore, output_path: Path, focus_id: str | None = None) -> Path:
    content = generate_provenance_graph_html(store, focus_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
