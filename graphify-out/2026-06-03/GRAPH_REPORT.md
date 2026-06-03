# Graph Report - .  (2026-06-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 87 nodes · 126 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `71106797`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]

## God Nodes (most connected - your core abstractions)
1. `User` - 10 edges
2. `track_event()` - 8 edges
3. `Link` - 6 edges
4. `ClickEvent` - 6 edges
5. `render_page()` - 6 edges
6. `Payment` - 5 edges
7. `PageView` - 5 edges
8. `Analytics` - 5 edges
9. `linkpay-uy` - 5 edges
10. `track_event()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `linkpay-uy` --references--> `Flask-Migrate`  [INFERRED]
  render.yaml → requirements.txt
- `linkpay-uy` --references--> `Flask`  [INFERRED]
  render.yaml → requirements.txt
- `linkpay-uy` --references--> `gunicorn`  [EXTRACTED]
  render.yaml → requirements.txt
- `create_app()` --calls--> `Analytics`  [EXTRACTED]
  app/__init__.py → zoo_analytics/__init__.py
- `register()` --calls--> `User`  [EXTRACTED]
  app/routes/auth.py → app/models/__init__.py

## Import Cycles
- None detected.

## Communities (12 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (15): LinkPay Uruguay - MVP Link-in-bio con pagos MercadoPago integrados. Metricas int, ClickEvent, Link, PageView, Payment, LinkPay - Modelos de Datos, create_payment(), mp_webhook() (+7 more)

### Community 1 - "Community 1"
Cohesion: 0.24
Nodes (8): ZOO Analytics - Dashboard routes, _add_buffer(), _flush_buffer(), _hash_ip(), _periodic_flush(), ZOO Analytics - Modulo simple de metricas para Flask. Cada proyecto define sus p, track_event(), track_page_view()

### Community 2 - "Community 2"
Cohesion: 0.26
Nodes (8): _add_buffer(), Analytics, _flush_buffer(), _hash_ip(), _periodic_flush(), ZOO Analytics - Modulo simple de metricas para Flask. Cada proyecto define sus p, track_event(), track_page_view()

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (4): User, LinkPay - Autenticacion (registro, login, logout), register(), UserMixin

### Community 4 - "Community 4"
Cohesion: 0.29
Nodes (7): index(), pagos(), LinkPay - Dashboard del usuario (gestion de links, ver estadisticas) CSS inline,, Renderiza una pagina del dashboard con el layout base., render_page(), settings(), stats()

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (8): linkpay-db, linkpay-uy, zoo_analytics_ext, Flask, Flask-Login, Flask-Migrate, Flask-SQLAlchemy, gunicorn

## Knowledge Gaps
- **7 isolated node(s):** `linkpay-db`, `zoo_analytics_ext`, `Flask-Login`, `Flask-SQLAlchemy`, `gunicorn` (+2 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Community 3` to `Community 0`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `track_event()` connect `Community 1` to `Community 0`, `Community 3`, `Community 4`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `Analytics` connect `Community 6` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `LinkPay Uruguay - MVP Link-in-bio con pagos MercadoPago integrados. Metricas int`, `LinkPay - Modelos de Datos`, `LinkPay - API (pagos MercadoPago, clicks, etc.)` to the rest of the system?**
  _20 weakly-connected nodes found - possible documentation gaps or missing edges._