"""Generate the 10-page draw.io architecture file for the Bharat Equity Intelligence Platform.

Deployment scope follows the BRD v1.0: GitHub Actions + private Git data branch + Gmail SMTP.
No cloud account, no always-on server.

Usage: python generate_drawio.py  -> writes system_architecture.drawio next to this script.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).with_name("system_architecture.drawio")

# layer -> (container fill, container stroke, badge/card colour)
PAL = {
    "user": ("#e8eaf6", "#9fa8da", "#1565c0"),
    "app": ("#e8f5e9", "#a5d6a7", "#43a047"),
    "gate": ("#fff3e0", "#ffcc80", "#ef6c00"),
    "red": ("#fce4ec", "#f48fb1", "#c62828"),
    "ai": ("#e1f5fe", "#81d4fa", "#0277bd"),
    "data": ("#f3e5f5", "#ce93d8", "#7b1fa2"),
    "mlops": ("#e0f2f1", "#80cbc4", "#00695c"),
    "infra": ("#eceff1", "#b0bec5", "#455a64"),
    "iam": ("#dae8fc", "#6c8ebf", "#0d47a1"),
    "policy": ("#fff2cc", "#d6b656", "#f57f17"),
    "audit": ("#d5e8d4", "#82b366", "#2e7d32"),
    "threat": ("#f8cecc", "#b85450", "#c62828"),
    "mcol": ("#e8f5e9", "#388e3c", "#388e3c"),
    "mvis": ("#e3f2fd", "#1565c0", "#1565c0"),
    "malert": ("#fff3e0", "#e65100", "#e65100"),
    "mops": ("#f3e5f5", "#6a1b9a", "#6a1b9a"),
}


class Page:
    def __init__(self, name, width=1700, height=1150):
        self.name, self.width, self.height = name, width, height
        self.cells = []
        self.ids = set()

    def _id(self, cid):
        assert cid not in self.ids, f"duplicate id {cid} on {self.name}"
        self.ids.add(cid)
        return cid

    def vertex(self, cid, value, style, x, y, w, h, parent="1"):
        self.cells.append(
            f'<mxCell id="{self._id(cid)}" value="{escape(value, {chr(10): "&#xa;", chr(34): "&quot;"})}" '
            f'style="{style}" vertex="1" parent="{parent}">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        return cid

    def title(self, text, subtitle=""):
        self.vertex("title", text, "text;html=1;fontSize=24;fontStyle=1;align=center;verticalAlign=middle;"
                    "fillColor=none;strokeColor=none;fontColor=#1a237e;", 50, 15, self.width - 100, 40)
        if subtitle:
            self.vertex("subtitle", subtitle, "text;html=1;fontSize=13;align=center;verticalAlign=middle;"
                        "fillColor=none;strokeColor=none;fontColor=#455a64;", 50, 55, self.width - 100, 25)

    def container(self, cid, layer, title, x, y, w, h):
        fill, stroke, badge = PAL[layer]
        self.vertex(cid, "", f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                    "strokeWidth=2;arcSize=8;verticalAlign=top;", x, y, w, h)
        self.vertex(cid + "_hdr", title, "text;html=1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;"
                    f"fillColor={badge};strokeColor=none;fontColor=#ffffff;rounded=1;arcSize=20;whiteSpace=wrap;",
                    x + 10, y + 10, w - 20, 30)
        return cid

    def card(self, cid, layer, text, x, y, w=180, h=46):
        color = PAL[layer][2]
        return self.vertex(cid, text, "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffffff;"
                           f"strokeColor={color};strokeWidth=1;fontSize=11;arcSize=12;shadow=1;", x, y, w, h)

    def cylinder(self, cid, layer, text, x, y, w=150, h=70):
        color = PAL[layer][2]
        return self.vertex(cid, text, "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;"
                           f"size=12;fillColor=#ffffff;strokeColor={color};fontSize=11;shadow=1;", x, y, w, h)

    def diamond(self, cid, text, x, y, w=170, h=90):
        return self.vertex(cid, text, "rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
                           "fontSize=11;fontStyle=1;shadow=1;", x, y, w, h)

    def actor(self, cid, text, x, y):
        return self.vertex(cid, text, "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;"
                           "outlineConnect=0;fillColor=#e8eaf6;strokeColor=#1565c0;fontSize=11;", x, y, 30, 60)

    def bar(self, cid, text, x, y, w, h=46, fill="#ffe6cc", stroke="#d79b00"):
        return self.vertex(cid, text, f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
                           "fontSize=12;fontStyle=1;arcSize=8;shadow=1;", x, y, w, h)

    def note(self, cid, text, x, y, w, h):
        return self.vertex(cid, text, "shape=note;whiteSpace=wrap;html=1;size=14;fillColor=#fffde7;"
                           "strokeColor=#f9a825;fontSize=11;align=left;spacingLeft=6;", x, y, w, h)

    def edge(self, cid, src, tgt, label="", color="#455a64", dashed=False):
        style = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;html=1;strokeColor={color};"
                 f"strokeWidth=2;endArrow=block;endFill=1;{'dashed=1;' if dashed else ''}")
        self.cells.append(
            f'<mxCell id="{self._id(cid)}" style="{style}" edge="1" parent="1" source="{src}" target="{tgt}">'
            '<mxGeometry relative="1" as="geometry"/></mxCell>')
        if label:
            self.cells.append(
                f'<mxCell id="{self._id(cid + "_lbl")}" value="{escape(label)}" '
                'style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;'
                'labelBackgroundColor=#ffffff;" vertex="1" connectable="0" parent="' + cid + '">'
                '<mxGeometry x="0" relative="1" as="geometry"><mxPoint as="offset"/></mxGeometry></mxCell>')

    def column(self, cid, layer, title, x, y, items, w=200, card_h=46, gap=10):
        h = 50 + len(items) * (card_h + gap) + 10
        self.container(cid, layer, title, x, y, w, h)
        ids = []
        for i, text in enumerate(items):
            ids.append(self.card(f"{cid}_c{i}", layer, text, x + 10, y + 50 + i * (card_h + gap), w - 20, card_h))
        return ids

    def xml(self):
        body = "".join(self.cells)
        page_id = "page" + self.name.split()[0]
        return (f'<diagram id="{page_id}" name="{escape(self.name)}">'
                f'<mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
                f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.width}" pageHeight="{self.height}" '
                f'math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root>'
                '</mxGraphModel></diagram>')


SCOPE = "v1.0 deployment: GitHub Actions + private Git data branch + Gmail SMTP | no cloud account, no always-on server (BRD §5.5, §15)"


def p1_logical():
    p = Page("1 Logical Architecture", 1800, 1250)
    p.title("Bharat Equity Intelligence Platform: Logical Architecture (Six Pillars)", SCOPE)
    for i, (a, t) in enumerate([("act_sp", "Sponsor /\nReport recipient"), ("act_op", "Operator\n(admin)"),
                                ("act_q", "Quant lead"), ("act_c", "Compliance")]):
        p.actor(a, t, 30, 130 + i * 190)
    trig = p.column("trig", "user", "P5 Triggers (GitHub Actions)", 110, 100, [
        "⏰ Schedule 09:00 IST\n(cron 30 3 * * 1-5)", "⏰ Schedule 13:00 IST\n(cron 30 7 * * 1-5)",
        "⏰ Schedule 16:00 IST\n(cron 30 10 * * 1-5)", "▶️ Manual dispatch\n(symbols, mode, horizons)",
        "🧪 Monthly training\nworkflow", "✅ CI on pull request"], w=190)
    ing = p.column("ing", "gate", "P1 Data Ingestion", 330, 100, [
        "🔌 Provider adapter\nfetch(dataset, symbols, range)", "📜 Licence & capability\ncheck (FR-143)",
        "🔁 Retry, backoff,\nrate-limit handling", "🏷️ Provenance capture\n(source, fetched_at)",
        "📅 Exchange trading\ncalendar", "📰 Filings & news\n(licensed feeds)"], w=210)
    sto = p.column("sto", "data", "P2 Storage & Data Quality", 570, 100, [
        "🧭 Manifest & checksum\nverification", "🕳️ Incremental gap\ndetection (FR-133)",
        "✅ Validation rules\nV1–V19", "🔀 Merge, dedupe,\nrevisions (FR-134/135)",
        "✂️ Corporate-action\nadjustment (A.1)", "🧮 Incremental feature\nrecompute (FR-138)"], w=210)
    p.cylinder("csv", "data", "🗄️ Persistent CSV store\n(data branch)", 600, 470, 150, 80)
    ana = p.column("ana", "ai", "P3 Analytics & Models", 810, 100, [
        "📊 Fundamental engine\n(ratios, scorecard)", "📈 Technical engine\n(indicators, summary)",
        "💰 Valuation engine\n(DCF, multiples, scenarios)", "🛑 Risk engine\n(stops, sizing, VaR)",
        "🧾 Derivatives engine\n(BSM, Greeks, payoffs)", "📉 Baselines B0/B1/B2\n+ EWMA/GARCH vol",
        "🌲 LightGBM-QR + CQR\n(forecast challenger)", "🏁 Ranking (gated)\nLambdaRank"], w=220)
    p.cylinder("reg", "ai", "📦 Model registry\nmodel_registry.json", 845, 600, 150, 80)
    rep = p.column("rep", "app", "P4 Research & Reporting", 1060, 100, [
        "🧾 Fact-sheet builder\n(engine facts + IDs)", "🔎 Hybrid retriever\n(BM25 + multilingual)",
        "🤖 LLM narrative\n(temp 0, JSON schema)", "🧷 Citation gate\n(numbers & entities)",
        "🚫 Prohibited-language\n& causation filter", "📚 Glossary EN / HI", "📄 Report renderer\n14-section HTML + CSV"],
        w=210)
    dlv = p.column("dlv", "red", "P5 Delivery & Persistence", 1300, 100, [
        "📧 Gmail SMTP report\n(idempotency key)", "⚠️ Failure notice\n(labelled FAILED)",
        "💾 Commit data branch\n(fast-forward + retry)", "🧾 Run record\nruns/<run_id>.json",
        "📒 Forecast ledger\n(append-only, hash chain)"], w=200)
    ext = p.column("ext", "infra", "External Services", 1530, 100, [
        "📈 Upstox REST\napi.upstox.com (v1.0)", "🏦 Licensed vendor (OD-02)\nCA, index, fundamentals",
        "🏛️ MoSPI api.mospi.gov.in\nRBI / FBIL (reviewed CSV)",
        "🧠 LLM API\n(provider per OD-12)", "✉️ smtp.gmail.com:587"], w=210)
    p.bar("p6bar", "P6 Configuration, Security & Observability  |  config/platform.yaml (schema-validated)  |  "
          "GitHub Actions secrets  |  least-privilege workflow token  |  structured JSON logs  |  job summaries  |  "
          "audit trail", 110, 1050, 1630, 50, "#eceff1", "#455a64")
    p.bar("mlbar", "Model governance  |  purged walk-forward evaluation  |  Diebold-Mariano + coverage publication gate  |"
          "  reviewed registry promotion (FR-181)  |  monthly / drift-triggered retraining", 110, 1115, 1630, 50,
          "#e0f2f1", "#00695c")
    p.edge("e1", trig[0], ing[0], "start pipeline", PAL["user"][2])
    p.edge("e2", ing[3], sto[3], "records + provenance", PAL["gate"][2])
    p.edge("e3", sto[5], "csv", "atomic write", PAL["data"][2])
    p.edge("e4", sto[5], ana[0], "validated features", PAL["data"][2])
    p.edge("e5", "reg", ana[6], "approved model", PAL["ai"][2])
    p.edge("e6", ana[0], rep[0], "engine outputs", PAL["ai"][2])
    p.edge("e7", rep[6], dlv[0], "HTML + CSV", PAL["app"][2])
    p.edge("e8", dlv[2], "csv", "git push data", PAL["red"][2], dashed=True)
    p.edge("e9", ext[0], ing[0], "HTTPS (TLS)", "#455a64")
    p.edge("e10", rep[2], ext[3], "fact sheet only", "#455a64")
    p.edge("e11", dlv[0], "act_sp", "email", PAL["red"][2])
    p.edge("e12", "act_op", trig[3], "dispatch", PAL["user"][2])
    return p


def p2_infra():
    p = Page("2 Infrastructure (GitHub)", 1700, 1100)
    p.title("Infrastructure View: GitHub Actions Execution (No Cloud Account)", SCOPE)
    p.container("gh", "infra", "GitHub (private repository, OD-23 / OD-28)", 40, 100, 1080, 960)
    p.container("main", "app", "Branch: main (code, protected)", 70, 160, 320, 420)
    for i, t in enumerate(["🐍 research_platform/ (Python package)", "⚙️ .github/workflows/research.yml",
                           "⚙️ .github/workflows/model-training.yml", "⚙️ .github/workflows/ci.yml",
                           "🧾 config/platform.yaml + JSON schema", "📦 models/ registry + artefacts (reviewed PR)"]):
        p.card(f"m{i}", "app", t, 85, 210 + i * 60, 290, 46)
    p.container("data", "data", "Branch: data (orphan, licensed data, private)", 420, 160, 340, 420)
    for i, (t, x, y) in enumerate([("🗄️ raw/\n(daily by year)", 435, 210), ("🗄️ processed/\nadjusted + features", 600, 210),
                                   ("🗄️ metadata/\nmanifest, logs", 435, 305), ("🗄️ checkpoints/\n+ backups/", 600, 305),
                                   ("🗄️ predictions/\n+ forecast ledger", 435, 400), ("🗄️ reports/ + runs/", 600, 400)]):
        p.cylinder(f"d{i}", "data", t, x, y, 145, 80)
    p.card("dtag", "data", "🏷️ Backup tags before full refresh", 435, 500, 310, 46)
    p.container("act", "mlops", "GitHub Actions (GitHub-hosted runners)", 790, 160, 310, 420)
    for i, t in enumerate(["🖥️ ubuntu-latest runner (CPU)", "🔒 concurrency: research-data\n(cancel-in-progress: false)",
                           "⏱️ timeout 60 min; p95 < 20 min", "📋 Job summary + structured logs",
                           "📦 Run artefacts (diagnostics only)", "🧮 ~2,000 min/month (Free, private)"]):
        p.card(f"a{i}", "mlops", t, 805, 210 + i * 60, 280, 46)
    p.container("sec", "iam", "Settings: secrets, variables, protection", 70, 610, 1030, 200)
    for i, t in enumerate(["🔑 MARKET_DATA_API_KEY", "🔑 FUNDAMENTALS_API_KEY", "🔑 LLM_API_KEY",
                           "🔑 GMAIL_SENDER / GMAIL_APP_PASSWORD", "🔑 REPORT_RECIPIENT (secret, OD-27)",
                           "🛡️ Branch protection + CODEOWNERS", "🛡️ Secret scanning + Dependabot",
                           "👥 Write access = dispatch rights"]):
        p.card(f"s{i}", "iam", t, 85 + (i % 4) * 255, 660 + (i // 4) * 70, 240, 50)
    p.container("ops", "user", "People (repository collaborators)", 70, 840, 1030, 190)
    for i, t in enumerate(["👤 Sponsor (report recipient)", "🛠️ Operator / engineering lead",
                           "📐 Quant lead (model approval)", "⚖️ Compliance (recipient allow-list)"]):
        p.card(f"u{i}", "user", t, 85 + i * 255, 900, 240, 50)
    p.container("ext", "gate", "External SaaS endpoints (HTTPS / SMTP)", 1160, 100, 500, 960)
    ext_items = ["📈 Upstox REST (v1.0 primary, sponsor-only)\nhttps://api.upstox.com/v3/historical-candle/…\n"
                 "/v3/market-quote/quotes · /v2/market/holidays\nBearer UPSTOX_ANALYTICS_TOKEN (1-yr, no static IP)",
                 "🗂️ Instrument master (CDN, daily ~06:00 IST)\nhttps://assets.upstox.com/market-quote/\n"
                 "instruments/exchange/complete.json.gz",
                 "🏦 Licensed vendor (OD-02): corporate actions,\nindex constituents, point-in-time fundamentals\n"
                 "base_url set in config/platform.yaml",
                 "🏛️ MoSPI REST https://api.mospi.gov.in (CPI, IIP, GDP)\noptional MCP: https://mcp.mospi.gov.in/",
                 "🏦 RBI https://data.rbi.org.in · FBIL https://www.fbil.org.in\n(no API: reviewed CSV in config/macro/)",
                 "🧠 LLM API (provider per OD-12, no-training terms)",
                 "✉️ Gmail SMTP smtp.gmail.com:587 STARTTLS",
                 "📥 Recipient inbox (sponsor only, OD-22)"]
    for i, t in enumerate(ext_items):
        p.card(f"x{i}", "gate", t, 1180, 160 + i * 110, 460, 95)
    p.edge("ie1", "a0", "x0", "HTTPS GET (missing ranges only)", PAL["gate"][2])
    p.edge("ie2", "a0", "x5", "HTTPS (fact sheet, no PII)", PAL["gate"][2])
    p.edge("ie3", "a0", "x6", "SMTP + App Password", PAL["red"][2])
    p.edge("ie4", "m1", "a0", "schedule / dispatch", PAL["mlops"][2])
    p.edge("ie5", "a0", "dtag", "checkout + commit (fast-forward)", PAL["data"][2], dashed=True)
    p.edge("ie6", "s0", "a1", "injected as env (masked)", PAL["iam"][2])
    p.edge("ie7", "x6", "x7", "report email", PAL["red"][2])
    p.edge("ie8", "u1", "m3", "PR review", PAL["user"][2])
    return p


def p3_security():
    p = Page("3 Security Architecture", 1700, 1100)
    p.title("Security & Compliance Architecture", "Identity · Policy & SEBI compliance · Audit · Threat protection")
    quads = [("iam", "🔐 Identity & Access", 40, 100, ["👥 Collaborators: write = dispatch (FR-176)",
              "🛡️ Branch protection on main (reviews)", "📝 CODEOWNERS for workflows, models, prompts",
              "🔑 Workflow token: contents:write only for data commit", "📌 Third-party actions pinned to SHA",
              "🔒 data branch writable by workflow only"]),
             ("policy", "⚖️ Policy & Regulatory Compliance", 860, 100, ["🚦 REG-01 route gate (feature flags)",
              "📬 Recipient allow-list (OD-22, sponsor-only)", "🤖 AI-use disclosure on every report (REG-03)",
              "📜 Licence registry + entitlement check (FR-125)", "🏷️ No 'buy / sell / target' labels",
              "🚫 Prohibited-language filter EN / HI"]),
             ("audit", "🧾 Audit & Traceability", 40, 560, ["📒 Forecast ledger, hash chain (FR-110)",
              "🧾 Run record per run (FR-155)", "🔁 revisions_log.csv (FR-135)", "📝 Model / schema changes = reviewed commits",
              "🧷 Citation IDs per sentence (FR-060)", "🗃️ Retention ≥ 5 years (NFR-031)"]),
             ("threat", "🛡️ Threat Protection", 860, 560, ["🔍 Secret scanning + push protection",
              "📦 Dependabot / dependency alerts", "🙈 Secrets & emails masked in logs",
              "✅ Dispatch inputs allow-listed; no shell interpolation", "🧱 Retrieved text treated as data (prompt-injection guard)",
              "🔄 Secret rotation ≤ 90 days (§15.7)"])]
    for cid, title, x, y, items in quads:
        p.container(cid, cid, title, x, y, 800, 420)
        for i, t in enumerate(items):
            p.card(f"{cid}_{i}", cid, t, x + 20 + (i % 2) * 390, y + 60 + (i // 2) * 110, 370, 80)
    p.bar("govbar", "Governance dashboard (v1.0 = GitHub job summary + report §14): failed rules · stale datasets · "
          "gate status · disclosure version · secret-scan results", 40, 1000, 1620, 50, "#ede7f6", "#5e35b1")
    p.note("legend", "Legend: blue = identity, yellow = policy, green = audit, red = threat.\n"
           "Only personal data in v1.0: recipient email addresses (secrets).", 1250, 60, 410, 40)
    p.edge("se1", "iam_2", "audit_3", "reviewed change", PAL["iam"][2])
    p.edge("se2", "policy_0", "threat_3", "gate enforced in code", PAL["policy"][2])
    return p


def p4_observability():
    p = Page("4 Observability & Monitoring", 1700, 1100)
    p.title("Observability, Logging & Monitoring", "File-based telemetry committed with every run; alerts by email")
    rows = [("mcol", "📥 Collection", ["🪵 Structured JSON logs", "🧾 metadata/run_log.csv", "⬇️ download_log.csv",
                                       "✅ data_quality_log.csv", "🔢 LLM token usage per run", "📒 Prediction ledger"]),
            ("mvis", "📊 Visualisation", ["📋 GitHub job summary", "📄 Report §2 freshness & §14 DQ",
                                          "📈 Monthly evaluation report", "🧮 Actions usage report",
                                          "🗂️ Model selection report", "🌐 Phase 4: web console (FR-126)"]),
            ("malert", "🚨 Alerting", ["📧 Failure email (FR-161)", "🟥 Stale-data banner (V1)",
                                       "🎯 80% coverage outside 70–90%", "📉 PSI > 0.25 on top features",
                                       "⏱️ Actions minutes ≥ 70%", "💽 data branch ≥ 500 MB"]),
            ("mops", "🛠️ Operations", ["▶️ Manual re-run (idempotent)", "♻️ Full refresh + reason",
                                       "🏷️ Restore from backup tag", "⏪ Model rollback (git revert)",
                                       "🔑 Secret rotation", "🧪 Monthly restore drill (NFR-094)"])]
    for r, (layer, title, items) in enumerate(rows):
        y = 100 + r * 240
        p.container(f"row{r}", layer, title, 40, y, 1620, 210)
        for i, t in enumerate(items):
            p.card(f"r{r}_{i}", layer, t, 60 + i * 265, y + 70, 245, 90)
    p.edge("oe1", "r0_1", "r1_0", "summarised", PAL["mcol"][2])
    p.edge("oe2", "r1_2", "r2_2", "threshold check", PAL["mvis"][2])
    p.edge("oe3", "r2_0", "r3_0", "operator action", PAL["malert"][2])
    p.edge("oe4", "r0_5", "r1_2", "matured forecasts", PAL["mcol"][2])
    return p


def p5_mlops():
    p = Page("5 MLOps CI-CD Pipeline", 1800, 1000)
    p.title("MLOps / LLMOps CI/CD Pipeline (GitHub Actions)", "Code, prompts and models change only through reviewed pull requests")
    stages = [("app", "1 Source", ["🌿 Feature branch", "📝 Pull request to main", "👀 CODEOWNERS review"]),
              ("gate", "2 CI (ci.yml)", ["🧹 Lint + type check", "🧪 Unit + golden tests\n(TST-CALC/DER/RISK)",
                                         "🔍 Leakage audit TST-FC-01", "🤖 AI red-team TST-AI-01..05", "🔐 Secret scan"]),
              ("mlops", "3 Training (monthly)", ["📥 Checkout data branch", "✂️ Purged walk-forward folds",
                                                "🎛️ Optuna (all trials logged)", "📏 CQR calibration"]),
              ("ai", "4 Evaluation gate", ["📊 Pinball / CRPS vs B0, B1", "🧮 Diebold-Mariano + FDR",
                                           "🎯 Coverage 75–85%", "🧾 Selection report"]),
              ("data", "5 Registry", ["📦 PR: model_registry.json", "✍️ Quant lead approval", "🔏 Artefact SHA-256"]),
              ("red", "6 Deploy & Monitor", ["👥 Shadow in ledger", "🏆 Champion in research.yml",
                                            "📉 Coverage / PSI drift", "📈 Monthly skill report"])]
    first = []
    for s, (layer, title, items) in enumerate(stages):
        ids = p.column(f"st{s}", layer, title, 40 + s * 290, 110, items, w=260, card_h=56)
        first.append(ids)
    for s in range(5):
        p.edge(f"pe{s}", first[s][-1], first[s + 1][0], ["merge", "data + code", "candidates", "pass", "approved"][s],
               PAL[stages[s][0]][2])
    p.edge("loop", first[5][2], first[2][0], "drift trigger → retrain", "#c62828", dashed=True)
    p.container("dp", "infra", "Research data pipeline (research.yml, 3× weekday)", 40, 560, 1720, 160)
    for i, t in enumerate(["📥 Load manifest", "🕳️ Detect gaps", "⬇️ Fetch missing", "✅ Validate + merge",
                           "🧮 Recompute features", "📦 Load approved models", "📊 Predict + analytics", "📧 Report + commit"]):
        p.card(f"dp{i}", "infra", t, 60 + i * 212, 620, 195, 60)
        if i:
            p.edge(f"dpe{i}", f"dp{i-1}", f"dp{i}", "", PAL["infra"][2])
    p.edge("dpr", first[4][2], "dp5", "registry read", PAL["data"][2], dashed=True)
    p.note("mln", "No model reaches a report unless it passed step 4 and was merged in step 5.\n"
           "If nothing passes: publish labelled naive baseline (status model_not_validated).", 40, 760, 820, 60)
    return p


def p6_lineage():
    p = Page("6 Data Lineage & Privacy", 1500, 1300)
    p.title("Data Lineage & Privacy Governance", "Every number traceable from vendor record to email sentence")
    chain = ["🏦 Vendor record\n(source, source_record_id, fetched_at)", "🗄️ raw/ CSV row\n(revision, natural key)",
             "✂️ Adjusted series\n(adj_factor_cum, ca_version)", "🧮 Feature row\n(feature_set_version, as_of_date)",
             "🌲 Prediction\n(model_id, version, manifest checksums)", "🧾 Fact sheet entry\n(fact_id, value, unit, period)",
             "🧷 Narrative sentence\n(fact_ids / source_ids)", "📄 Report\n(report_id, snapshot_id)",
             "📧 Email\n(run_id + report hash idempotency key)"]
    for i, t in enumerate(chain):
        if i in (0, 1, 2):
            p.cylinder(f"l{i}", "data", t, 120, 100 + i * 125, 300, 90)
        else:
            p.card(f"l{i}", "data", t, 120, 100 + i * 125, 300, 80)
        if i:
            p.edge(f"le{i}", f"l{i-1}", f"l{i}", "", PAL["data"][2])
    p.container("priv", "policy", "🔏 Privacy controls", 520, 100, 440, 560)
    for i, t in enumerate(["👤 Only personal data: recipient emails (secrets, masked)", "🚫 No personal data in LLM prompts (NFR-036)",
                           "🔒 Licensed data only in private repo (A-09)", "📤 CSVs never offered for download (§14.4)",
                           "🗓️ DPDP readiness by 12 May 2027 (REG-12)", "🧹 Retention policy entry before deletion",
                           "🧪 Test fixtures outside data/ (§5.6)"]):
        p.card(f"pv{i}", "policy", t, 540, 160 + i * 68, 400, 56)
    p.container("aud", "audit", "🧾 Audit trail sidebar", 1010, 100, 440, 560)
    for i, t in enumerate(["metadata/manifest.csv (sha256)", "metadata/revisions_log.csv", "metadata/download_log.csv",
                           "runs/<run_id>.json", "predictions/<date>/<run_id>.csv", "reports/<date>/<run_id>.html",
                           "git history = immutable change log"]):
        p.card(f"au{i}", "audit", "📁 " + t, 1030, 160 + i * 68, 400, 56)
    p.note("pin", "Point-in-time rule: fundamentals usable only after filing_ts_utc; index membership by effective date;\n"
           "macro by release date (vintages). Reproduce any report from snapshot_id + git SHA (FR-062, FR-113).",
           520, 700, 930, 70)
    p.edge("la1", "l4", "au4", "stored", PAL["audit"][2], dashed=True)
    p.edge("la2", "l7", "au5", "stored", PAL["audit"][2], dashed=True)
    p.edge("la3", "l5", "pv1", "public facts only", PAL["policy"][2], dashed=True)
    return p


def p7_resilience():
    p = Page("7 Resilience & Fallback", 1800, 1000)
    p.title("Resilience & Fallback Paths", "Never send stale results as current; keep last valid data; degrade to deterministic output")
    chains = [("gate", "Market data", ["🏦 Primary vendor", "🔁 Retry 2-4-8-16-32 s + jitter", "🏦 Secondary vendor\n(if licensed)",
                                       "🗄️ Keep last valid CSV\n+ stale label", "⚠️ Failure email"]),
              ("ai", "LLM narrative", ["🤖 LLM draft", "🧷 Citation gate", "🔁 Regenerate once\n(>20% failed)",
                                       "📄 Template-only report", "🛑 Kill switch (REG-15)"]),
              ("mlops", "Scheduling", ["⏰ Cron slot", "🕒 Late-run flag", "🚨 Missed-slot alert", "▶️ Manual dispatch",
                                       "🧾 Run record"]),
              ("data", "Persistence", ["💾 git push data", "🔄 Fetch + re-merge once", "⚠️ data_not_persisted",
                                       "🏷️ Restore backup tag", "♻️ Repair download (one file)"]),
              ("red", "Email", ["📧 SMTP submit", "🔁 Retry", "🧾 smtp_error recorded", "📋 Job summary shows fix",
                                "🔐 Gmail API OAuth (OD-26)"])]
    labels = ["5xx / 429", "exhausted", "unavailable", "notify"]
    for r, (layer, title, items) in enumerate(chains):
        y = 100 + r * 175
        p.container(f"ch{r}", layer, title, 40, y, 1720, 150)
        for i, t in enumerate(items):
            p.card(f"c{r}_{i}", layer, t, 60 + i * 340, y + 55, 290, 70)
            if i:
                p.edge(f"ce{r}_{i}", f"c{r}_{i-1}", f"c{r}_{i}", "fallback" if r else labels[i - 1], PAL[layer][2],
                       dashed=True)
    return p


def p8_orchestration():
    p = Page("8 Pipeline Orchestration", 1800, 900)
    p.title("Pipeline Orchestration & Tool Execution (deterministic, no autonomous agents)",
            "One Python entry point runs the 14 steps of BRD §15.5.3 for scheduled and manual triggers (FR-152)")
    steps = ["1 Checkout main + data", "2 Python + pinned deps", "3 Validate config", "4 Load manifest, verify checksums",
             "5 Detect missing records", "6 Fetch, validate, revise", "7 Persist atomically", "8 Recompute features",
             "9 Load approved models", "10 Analytics, forecasts, risk", "11 Save predictions", "12 HTML report + CSV",
             "13 Email / failure notice", "14 Commit + job summary"]
    layers = ["infra"] * 3 + ["data"] * 5 + ["ai"] * 3 + ["app", "red", "red"]
    for i, t in enumerate(steps):
        x = 40 + (i % 7) * 250
        y = 140 if i < 7 else 360
        p.card(f"s{i}", layers[i], ("⚙️ " if i < 7 else "🧠 ") + t, x, y, 220, 70)
        if i:
            p.edge(f"se{i}", f"s{i-1}", f"s{i}", "", "#455a64")
    p.container("tools", "ai", "Tools called as Python modules (no LLM tool-calling)", 40, 520, 1100, 170)
    for i, t in enumerate(["📊 fundamentals", "📈 technicals", "💰 valuation", "🛑 risk", "🧾 derivatives", "🌲 forecasting"]):
        p.card(f"t{i}", "ai", t, 60 + i * 180, 580, 165, 60)
    p.cylinder("mem", "data", "🗄️ State = data branch\n(no conversation memory)", 1200, 540, 220, 110)
    p.note("why", "Why no agents: the BRD requires one deterministic\nimplementation of every step and forbids the LLM\n"
           "from producing numbers (G-3, FR-152). The LLM is a\nsingle bounded call in step 12.", 1460, 520, 300, 140)
    p.edge("te", "s9", "t0", "invoke", PAL["ai"][2])
    p.edge("tm", "s6", "mem", "write", PAL["data"][2], dashed=True)
    return p


def p9_finops():
    p = Page("9 FinOps & Cost Optimisation", 1700, 1050)
    p.title("FinOps & Cost Optimisation", "Costs: Actions minutes · data licence (OD-02) · LLM tokens. Tracked per run (KPI-23)")
    p.card("start", "user", "▶️ Run starts", 40, 130, 170, 50)
    p.diamond("dnew", "New data since\nlast confirmed date?", 260, 110)
    p.card("reuse", "app", "♻️ No historical requests\n(NFR-091, TST-HIST-B)", 260, 260, 200, 60)
    p.card("fetch", "gate", "⬇️ Fetch missing ranges only\n+ 5-day look-back", 500, 130, 220, 60)
    p.diamond("dcache", "Narrative cached\nfor this snapshot?", 770, 110)
    p.card("cached", "app", "♻️ Reuse cached narrative\n($0 LLM)", 770, 260, 200, 60)
    p.diamond("dtask", "Task type?", 1020, 110)
    p.card("rules", "app", "📏 Rules / TF-IDF\n(filing class, linking) $0", 1020, 260, 200, 60)
    p.card("small", "ai", "🤖 Mid-tier LLM, temp 0\n(narrative) $$", 1270, 130, 200, 60)
    p.card("tmpl", "app", "📄 Template report\nwhen budget cap hit", 1270, 260, 200, 60)
    p.edge("f1", "start", "dnew", "", "#455a64")
    p.edge("f2", "dnew", "reuse", "no", "#43a047")
    p.edge("f3", "dnew", "fetch", "yes", "#ef6c00")
    p.edge("f4", "fetch", "dcache", "", "#455a64")
    p.edge("f5", "dcache", "cached", "yes", "#43a047")
    p.edge("f6", "dcache", "dtask", "no", "#ef6c00")
    p.edge("f7", "dtask", "rules", "classification", "#43a047")
    p.edge("f8", "dtask", "small", "narrative", "#0277bd")
    p.edge("f9", "small", "tmpl", "over cap", "#c62828", dashed=True)
    p.container("lev", "mlops", "💡 Cost levers", 40, 420, 800, 520)
    for i, t in enumerate(["⏱️ p95 run < 20 min → 66 runs ≈ 1,320 min (fits 2,000 Free)", "🧮 Training in separate monthly job",
                           "🌲 CPU-only models (LightGBM, linear, GARCH)", "📅 Year-partitioned CSVs → small commits",
                           "🚫 No intraday history in Git (OD-25)", "🔢 Per-run and daily LLM token caps (NFR-061)",
                           "🧾 Fact sheet only in prompt (short context)"]):
        p.card(f"lv{i}", "mlops", t, 60, 480 + i * 64, 760, 52)
    p.container("kpi", "data", "📊 Budget alerts", 880, 420, 780, 520)
    for i, t in enumerate(["⚠️ Actions minutes ≥ 70% of plan (NFR-110)", "⚠️ data branch ≥ 500 MB → review retention",
                           "🛑 data branch ≥ 1 GB → approved migration (OD-24)", "💸 Cost per report ≥ 120% budget (NFR-060)",
                           "📈 API calls ≥ 70% vendor quota (NFR-107)", "🧾 Cost per completed run (KPI-23)"]):
        p.card(f"k{i}", "data", t, 900, 480 + i * 72, 740, 56)
    return p


def p10_governance():
    p = Page("10 AI Governance, Safety & HITL", 1800, 1100)
    p.title("AI Model Governance, Safety & Human-in-the-Loop", "Three gated flows: forecasts, narratives, governance flags")
    p.card("cand", "mlops", "🌲 Candidate model\n(selection report)", 40, 140, 190, 60)
    p.diamond("g1", "DM test vs B0\np < 0.05 (FDR)?", 270, 125)
    p.diamond("g2", "80% coverage\nin 75–85%?", 480, 125)
    p.card("rev", "user", "✍️ Quant lead + compliance\nPR review", 690, 140, 210, 60)
    p.card("shadow", "ai", "👥 Shadow in ledger\n(≥ 1 cycle)", 940, 140, 180, 60)
    p.card("champ", "ai", "🏆 Champion\n(sponsor-only until OD-01)", 1160, 140, 210, 60)
    p.card("naive", "app", "📉 Publish labelled naive range\nmodel_not_validated", 370, 300, 240, 60)
    for a, b, l in [("cand", "g1", ""), ("g1", "g2", "yes"), ("g2", "rev", "yes"), ("rev", "shadow", "approved"),
                    ("shadow", "champ", "promote")]:
        p.edge(f"{a}_{b}", a, b, l, "#00695c")
    p.edge("g1n", "g1", "naive", "no", "#c62828")
    p.edge("g2n", "g2", "naive", "no", "#c62828")
    p.card("draft", "ai", "🤖 LLM draft\n(fact IDs per sentence)", 40, 470, 190, 60)
    p.diamond("cg", "Every number /\nentity matched?", 270, 455)
    p.diamond("pct", "> 20% sentences\ndropped?", 480, 455)
    p.card("regen", "ai", "🔁 Regenerate once", 690, 470, 180, 60)
    p.card("tmpl", "app", "📄 Template-only report", 690, 590, 180, 60)
    p.card("pub", "app", "📄 Verified narrative\n+ AI-use disclosure", 940, 470, 210, 60)
    p.card("samp", "user", "🔎 5% human sample\n(OD-13)", 1190, 470, 180, 60)
    for a, b, l, c in [("draft", "cg", "", "#0277bd"), ("cg", "pub", "yes", "#43a047"), ("cg", "pct", "no", "#c62828"),
                       ("pct", "regen", "yes", "#c62828"), ("regen", "tmpl", "fails again", "#c62828"),
                       ("pct", "pub", "no (drop failed)", "#43a047"), ("pub", "samp", "weekly", "#1565c0")]:
        p.edge(f"{a}_{b}", a, b, l, c)
    p.card("flag", "policy", "🏛️ Governance flag\nextraction (FR-025)", 40, 790, 190, 60)
    p.diamond("span", "Verbatim span found\n& confidence ≥ τ?", 270, 775)
    p.card("show", "audit", "✅ Flag + source paragraph", 500, 790, 210, 60)
    p.card("queue", "user", "🧑‍⚖️ Human review queue\n(not shown until reviewed)", 500, 910, 230, 60)
    p.diamond("route", "OD-01 route &\nOD-22 recipients?", 800, 775)
    p.card("sponsor", "red", "📬 Sponsor-only delivery", 1040, 790, 200, 60)
    p.card("public", "red", "🌐 Public research (RA, G2)", 1040, 910, 200, 60)
    for a, b, l, c in [("flag", "span", "", "#f57f17"), ("span", "show", "yes", "#43a047"), ("span", "queue", "no", "#c62828"),
                       ("show", "route", "", "#455a64"), ("route", "sponsor", "not closed", "#c62828"),
                       ("route", "public", "RA + counsel", "#43a047")]:
        p.edge(f"{a}_{b}", a, b, l, c)
    p.note("stages", "Registry stages: experimental → candidate (passed gate) → shadow → champion → retired.\n"
           "Every transition is a reviewed commit (FR-175, FR-181).", 1300, 790, 460, 70)
    return p


def main():
    pages = [p1_logical(), p2_infra(), p3_security(), p4_observability(), p5_mlops(), p6_lineage(),
             p7_resilience(), p8_orchestration(), p9_finops(), p10_governance()]
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<mxfile host="app.diagrams.net" type="device">'
           + "".join(pg.xml() for pg in pages) + "</mxfile>\n")
    OUT.write_text(xml, encoding="utf-8")
    for pg in pages:
        n = sum(1 for c in pg.cells if 'vertex="1"' in c and "edgeLabel" not in c)
        print(f"{pg.name}: {n} vertices")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
