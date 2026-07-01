# Frontend Architecture Specification: React Application

This directory contains the user interface components and client state management for NexusBI, built with React, Tailwind CSS, Redux Toolkit, and Apache ECharts.

## 📁 Directory Structure Breakdown

```text
frontend/src/
├── components/          # Reusable UI widgets and presentation components
│   ├── chat/            # Conversational controls, message bubbles, action buttons
│   ├── dashboard/       # Layout grid controllers, widget containers, edit states
│   └── common/          # Global UI elements (Spinners, Input cards, Alerts)
│
├── features/            # Redux Slices, API hooks, and application logic
│   ├── auth/            # OAuth2 token handlers, permissions synchronization
│   ├── query/           # Conversational WebSocket events, SQL rendering slices
│   └── visual/          # Vega-Lite / ECharts specification parsers
│
└── routes/              # App routing, page layouts, and access guards
```

---

## 🏗️ Core Client Architectures

### 1. State Management System
We enforce a strict separation between **Global Application State** (Redux Store) and **Server Data Cache** (RTK Query / WebSockets).

* **Global UI State:** Contains session variables, active filters, selected theme parameters, and active dashboards configurations.
* **Server Sync (WebSockets):** The conversational interface communicates with the FastAPI backend over a persistent WebSocket connection, streaming token generation events, SQL compile steps, and driver execution states to provide real-time status bars (e.g. *Generating SQL...*, *Executing on Snowflake...*).

### 2. The Dynamic Visualization Pipeline
NexusBI renders data representations dynamically without using hardcoded chart widgets.

```
┌──────────────────────────────────────┐
│       Backend WebSocket Event        │
│    (Vega-Lite JSON Spec + Dataset)   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       Visual Specification Slice     │
│   (Parses encoding and dimensions)   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       ECharts Renderer Worker        │
│   (Compiles JSON to canvas visual)   │
└──────────────────────────────────────┘
```

1. **JSON Specs:** The backend sends a declarative visual specification format (Vega-Lite) containing the layout mapping.
2. **Dynamic Binding:** The ECharts component acts as an adaptive container, receiving the specification and binding the returned Snowflake dataset arrays directly to the rendering coordinates.
3. **Drill-down Handlers:** Clicks on chart visual elements (e.g., a specific column bar) trigger contextual events, sending automated follow-up requests back to the AI Chat slice (e.g., *"Filter by Category: Logistics"*).
