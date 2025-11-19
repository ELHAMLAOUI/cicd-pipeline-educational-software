"""Page HTML de suivi du pipeline (.pipeline/status.html), rafraîchie automatiquement."""
import html
import os

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:32px;background:#f6f7f9;color:#1f2328}
h1{font-size:22px;margin:0 0 4px} .sub{color:#57606a;margin-bottom:24px}
.card{background:#fff;border:1px solid #d0d7de;border-radius:10px;padding:20px;margin-bottom:20px}
.flow{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin:12px 0}
.st{min-width:120px;padding:12px 14px;border-radius:8px;border:2px solid;text-align:center}
.st b{display:block;font-size:15px} .st span{font-size:12px}
.success{border-color:#1a7f37;background:#dafbe1} .failed{border-color:#cf222e;background:#ffebe9}
.skipped{border-color:#8c959f;background:#f6f8fa;color:#57606a}
.arrow{color:#8c959f;font-size:20px}
.badge{display:inline-block;padding:2px 10px;border-radius:12px;color:#fff;font-weight:600;font-size:13px}
.b-success{background:#1a7f37} .b-failed{background:#cf222e}
table{border-collapse:collapse;width:100%;font-size:14px} th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #eaeef2}
pre{background:#0d1117;color:#e6edf3;padding:12px;border-radius:8px;overflow:auto;font-size:12px;max-height:260px}
code{font-family:ui-monospace,Consolas,monospace}
.mini{display:inline-block;padding:1px 6px;margin:1px;border-radius:4px;font-size:11px;border:1px solid}
"""


def _stage_box(st):
    detail = {"success": "réussie", "failed": "échec", "skipped": "ignorée"}[st["status"]]
    if "coverage" in st:
        detail += f" · {st['coverage']} %"
    if st.get("rollback"):
        detail += " · rollback"
    elif "env" in st and st["status"] == "success":
        detail += f" · {st['release']}"
    return f'<div class="st {st["status"]}"><b>{html.escape(st["name"])}</b><span>{detail}</span></div>'


def _mini(st):
    label = html.escape(st["name"]) + (" (rollback)" if st.get("rollback") else "")
    return f'<span class="mini {st["status"]}">{label}</span>'


def write_status_page(ws, runs):
    os.makedirs(os.path.join(ws, ".pipeline"), exist_ok=True)
    out = os.path.join(ws, ".pipeline", "status.html")
    parts = [f"<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>"
             f"<meta http-equiv='refresh' content='2'><title>Pipeline CI/CD</title><style>{CSS}</style></head><body>",
             "<h1>Pipeline CI/CD</h1><div class='sub'>Cette page se met à jour toute seule après chaque commit.</div>"]
    if not runs:
        parts.append("<div class='card'>Aucun pipeline exécuté pour l'instant. Faites un commit !</div>")
    else:
        r = runs[-1]
        parts.append(f"<div class='card'><div><span class='badge b-{r['status']}'>"
                     f"{'SUCCÈS' if r['status'] == 'success' else 'ÉCHEC'}</span> "
                     f"&nbsp;<b>Pipeline #{r['id']}</b> — <code>{r['short']}</code> sur <code>{html.escape(r['branch'])}</code> "
                     f"— « {html.escape(r['message'])} »</div>")
        if r.get("error"):
            parts.append(f"<p style='color:#cf222e'>{html.escape(r['error'])}</p>")
        boxes = [_stage_box(s) for s in r["stages"]]
        parts.append("<div class='flow'>" + "<span class='arrow'>&#8594;</span>".join(boxes) + "</div>")
        for s in r["stages"]:
            if s["status"] == "failed":
                parts.append(f"<p><b>Journal de l'étape {html.escape(s['name'])}</b></p><pre>{html.escape(s['log'])}</pre>")
        parts.append("</div>")
        envs_dir = os.path.join(ws, ".pipeline", "env")
        if os.path.isdir(envs_dir):
            rows = []
            for env in sorted(os.listdir(envs_dir)):
                try:
                    with open(os.path.join(envs_dir, env, "current"), encoding="utf-8") as fh:
                        cur = fh.read().strip()
                except OSError:
                    cur = "—"
                rows.append(f"<tr><td>{html.escape(env)}</td><td><code>{html.escape(cur)}</code></td></tr>")
            parts.append("<div class='card'><b>Environnements</b><table><tr><th>Environnement</th>"
                         "<th>Version servie</th></tr>" + "".join(rows) + "</table></div>")
        hist = []
        for r in reversed(runs[-30:]):
            hist.append(f"<tr><td>#{r['id']}</td><td><span class='badge b-{r['status']}'>"
                        f"{'OK' if r['status'] == 'success' else 'KO'}</span></td><td><code>{r['short']}</code></td>"
                        f"<td>{html.escape(r['branch'])}</td><td>{''.join(_mini(s) for s in r['stages'])}</td>"
                        f"<td>{html.escape(r['message'])}</td>"
                        f"<td>{html.escape(r['date'].replace('T', ' '))}</td></tr>")
        parts.append("<div class='card'><b>Historique</b><table><tr><th>#</th><th>Statut</th><th>Commit</th>"
                     "<th>Branche</th><th>Étapes</th><th>Message</th><th>Date</th></tr>" + "".join(hist) + "</table></div>")
    parts.append("</body></html>")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))
    return out
