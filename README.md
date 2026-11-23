# Octen for Antigravity

Octen gives Antigravity agents live information from the web: web and news search, company and people lookup, places, images, design references, videos, and clean page extraction. The plugin connects the hosted Octen MCP server and adds one skill that teaches the agent which tool fits which task.

## Setup

1. Create an API key on the [Octen API Platform](https://octen.ai/platform/api-keys).
2. Install the plugin from this repository:

   ```bash
   agy plugin install https://github.com/Octen-Team/octen-antigravity-plugin
   ```

   If you found Octen in the Antigravity Marketplace, install it from there instead.

3. Turn the plugin on. Antigravity asks for your **Octen API Key** before it enables the plugin: in the CLI, open `/plugin`; in the Antigravity App, open the **Customizations** panel.

Nothing else needs to be installed. The MCP server is hosted at `https://mcp.octen.ai/mcp`, and the key is sent only to that server, in the `x-api-key` header.

## What you get

### MCP tools

| Tool | What it does |
| --- | --- |
| `search` | Web search for one focused lookup |
| `premier_search` | Web search with deeper retrieval and reranking, for hard-to-find pages |
| `broad_search` | One question expanded into several searches, for surveys and multi-part questions |
| `news_search` | Recent news, with the coverage grouped into storylines |
| `business_search` | Company and people cards: profile, key people, financials, recent announcements |
| `place_search` | Real-world places as cards: address, opening hours, phone, rating |
| `pulse_search` | The likely URL of a site or docs page you can almost name |
| `extract` | Clean content of 1 to 20 pages by URL |
| `image_search` | Images by text query or by reference image |
| `design_search` | Real web page, app screen and slide designs, with their colours and fonts, and HTML for page sections |
| `video_search` | Videos by text query (beta: access is by request) |

All tools are read-only.

### Skill

`octen-search-guide` tells the agent how to choose between the tools, when to follow a search with `extract`, and what to do when a call fails. The agent loads it on its own when a task needs web information; you can also run `/octen-search-guide`.

## Pricing

Calls are billed to your Octen account at the rates on the [pricing page](https://octen.ai/pricing). `premier_search` has its own rate, and `broad_search` runs several searches per call.

## Troubleshooting

- **The plugin stays off after installing.** It is disabled until the API key is filled in. Open `/plugin` in the CLI, or the Customizations panel in the App, and turn it on.
- **`code=401 msg=Invalid API Key`.** The key is wrong or was not filled in. Set it again in the plugin's settings.
- **`video_search` is not available to your account.** Video Search is in beta. Contact Octen to request access.

## Learn more

- [Octen MCP Server](https://docs.octen.ai/integrations/octen-mcp-server): every tool and its parameters
- [Octen documentation](https://docs.octen.ai)

## License

[MIT](LICENSE)
