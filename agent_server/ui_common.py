"""Shared Databricks-branded chrome for the GulfNet UI pages."""

from urllib.parse import quote

from agent_server.ui_brand import DATABRICKS_LOGO, DATABRICKS_MARK, LAKEBASE_ICON

# Databricks palette: Navy 800 surfaces, Lava 600 brand, Oat Light ink,
# Maize for memory, Green 600 for completion, Blue for data objects.
BASE_CSS = """
:root {
  --navy-900:#0D1B21; --navy-800:#1B3139; --navy-700:#24404A; --navy-600:#2F5361;
  --oat:#F9F7F4; --oat-dim:#EEEDE9;
  --lava:#FF3621; --lava-dim:#C2291A;
  --maize:#FFAB00; --green:#00A972; --blue:#5BA7D9;
  --muted:#9BB1B9; --line:#2A4A55; --err:#FF5F52;
}
* { box-sizing:border-box; }
html, body { height:100%; }
body {
  margin:0; color:var(--oat);
  font-family:"DM Sans","Inter",-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background:
    radial-gradient(980px 520px at 92% -8%, rgba(255,54,33,.16) 0%, rgba(255,54,33,0) 60%),
    radial-gradient(1100px 620px at 4% -12%, #24404A 0%, var(--navy-900) 62%);
  background-color:var(--navy-900);
  display:flex; flex-direction:column; min-height:100vh;
}
header.top {
  flex:0 0 auto; padding:12px 22px; border-bottom:1px solid var(--line);
  display:flex; align-items:center; justify-content:space-between; gap:18px; flex-wrap:wrap;
  background:rgba(13,27,33,.72);
}
.lockup { display:flex; align-items:center; gap:14px; }
.lockup .dbl { width:74px; height:42px; flex:0 0 auto; display:block; }
.lockup .dbl svg { width:100%; height:100%; display:block; }
.lockup .rule { width:1px; height:38px; background:var(--line); flex:0 0 auto; }
.brand h1 { margin:0; font-size:16.5px; letter-spacing:.01em; font-weight:600; }
.brand p {
  margin:3px 0 0; font-size:11.5px; color:var(--muted);
  display:flex; align-items:center; gap:6px; flex-wrap:wrap;
}
.lbchip {
  display:inline-flex; align-items:center; gap:5px; color:var(--oat);
  background:rgba(255,54,33,.12); border:1px solid rgba(255,54,33,.4);
  border-radius:5px; padding:2px 7px; font-size:10.5px; font-weight:600;
}
.lbchip svg { width:11px; height:12px; display:block; }
.navlinks { display:flex; gap:8px; flex-wrap:wrap; }
.navlinks a {
  color:var(--oat); text-decoration:none; font-size:12px;
  border:1px solid var(--line); border-radius:6px; padding:6px 12px; background:rgba(27,49,57,.6);
}
.navlinks a:hover { border-color:var(--lava); color:var(--lava); }
.navlinks a.on { border-color:var(--lava); color:var(--lava); background:rgba(255,54,33,.1); }
"""

FAVICON = '<link rel="icon" href="data:image/svg+xml,' + quote(DATABRICKS_MARK) + '" />'


def header_html(active: str = "") -> str:
    def cls(name: str) -> str:
        return ' class="on"' if name == active else ""

    return (
        '<header class="top">'
        '<div class="lockup">'
        '<a class="dbl" href="https://www.databricks.com/product/lakebase"'
        ' target="_blank" rel="noopener" aria-label="Databricks">' + DATABRICKS_LOGO + "</a>"
        '<div class="rule"></div>'
        '<div class="brand">'
        "<h1>GulfNet Care Copilot</h1>"
        "<p><span class=\"lbchip\">" + LAKEBASE_ICON + "Lakebase</span>"
        " agent memory &middot; hybrid search &middot; task orchestration</p>"
        "</div></div>"
        '<nav class="navlinks">'
        '<a href="/"' + cls("home") + ">Architecture</a>"
        '<a href="/chat"' + cls("chat") + ">Chat</a>"
        '<a href="/ops/dashboard"' + cls("ops") + ">Ops dashboard</a>"
        '<a href="/docs">API docs</a>'
        "</nav></header>"
    )
