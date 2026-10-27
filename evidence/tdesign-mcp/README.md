# TDesign MCP Usage Evidence

The project used `tdesign-mcp-server@0.2.4` over MCP stdio.

Server startup command:

```text
npx -y tdesign-mcp-server@latest
```

Tools returned by `tools/list`:

- `get-component-list`
- `get-component-docs`
- `get-component-dom`
- `get-component-changelog`
- `search-icon`

Actual calls made for this dashboard:

```json
[
  {
    "name": "get-component-list",
    "arguments": {
      "framework": "vue-next"
    }
  },
  {
    "name": "get-component-docs",
    "arguments": {
      "framework": "vue-next",
      "names": [
        "Button",
        "DateRangePicker",
        "Pagination",
        "RadioGroup",
        "Select",
        "Switch",
        "Table",
        "Tabs",
        "Tag",
        "Tooltip"
      ]
    }
  },
  {
    "name": "get-component-dom",
    "arguments": {
      "framework": "vue-next",
      "names": [
        "RadioGroup",
        "Tabs",
        "Table"
      ]
    }
  },
  {
    "name": "search-icon",
    "arguments": {
      "keywords": [
        "chart",
        "download",
        "calendar",
        "refresh"
      ],
      "limit": 12
    }
  }
]
```

The raw responses are retained beside this file as `tools.json`,
`component-list.json`, `component-docs.json`, `component-dom.json`, and
`icons.json`.
