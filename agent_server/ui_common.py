"""Shared chrome for the GulfNet UI pages."""

BASE_CSS = """
:root {
  --bg:#0b1f1a; --panel:#12352c; --panel2:#164034; --ink:#e8f5f0;
  --muted:#8fb3a8; --accent:#2dd4a8; --mem:#f7c948; --data:#5eb0ef;
  --line:#1f4a3d; --err:#f2777a;
}
* { box-sizing:border-box; }
html, body { height:100%; }
body {
  margin:0; color:var(--ink);
  font-family:"IBM Plex Sans",-apple-system,"Segoe UI",Roboto,sans-serif;
  background:radial-gradient(1200px 620px at 8% -12%, #1a4d3f 0%, var(--bg) 58%);
  display:flex; flex-direction:column; min-height:100vh;
}
header.top {
  flex:0 0 auto; padding:13px 22px; border-bottom:1px solid var(--line);
  display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;
}
.brand h1 { margin:0; font-size:17px; letter-spacing:.02em; }
.brand h1 span { color:var(--accent); }
.brand p { margin:3px 0 0; font-size:11.5px; color:var(--muted); }
.navlinks { display:flex; gap:8px; flex-wrap:wrap; }
.navlinks a {
  color:var(--ink); text-decoration:none; font-size:12px;
  border:1px solid #2a5c4c; border-radius:8px; padding:6px 11px;
}
.navlinks a:hover { border-color:var(--accent); color:var(--accent); }
.navlinks a.on { border-color:var(--accent); color:var(--accent); }
"""


def header_html(active: str = "") -> str:
    def cls(name: str) -> str:
        return ' class="on"' if name == active else ""

    return (
        '<header class="top">'
        '<div class="brand">'
        '<h1><span>GulfNet</span> Care Copilot</h1>'
        "<p>UAE telco agent on Lakebase Postgres &middot; memory &middot; hybrid search "
        "&middot; task orchestration</p>"
        "</div>"
        '<nav class="navlinks">'
        '<a href="/"' + cls("home") + ">Architecture</a>"
        '<a href="/chat"' + cls("chat") + ">Chat</a>"
        '<a href="/ops/dashboard">Ops dashboard</a>'
        '<a href="/docs">API docs</a>'
        "</nav></header>"
    )
