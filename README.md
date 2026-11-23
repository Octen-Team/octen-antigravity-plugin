# Octen for Antigravity

Octen gives Antigravity agents live information from the web: web and news search, company and people lookup, places, images, design references, videos, and clean page extraction. The plugin connects the hosted Octen MCP server and adds one skill that teaches the agent which tool fits which task.

## Setup

1. Make sure your Octen account has at least one API key; the sign-in page asks you to choose the key the plugin uses and cannot create one. Create an account and a key on the [Octen API Platform](https://octen.ai/platform/api-keys) if you have none.
2. Install the plugin from this repository:

   ```bash
   agy plugin install https://github.com/Octen-Team/octen-antigravity-plugin
   ```

   If you found Octen in the Antigravity Marketplace, install it from there instead.

3. Sign in to Octen. The plugin is on as soon as it is installed; its MCP server works once you have signed in.
   - In the CLI, open `/plugin`, expand **octen** under **Installed** and choose **Sign in**.
   - In the Antigravity App, open **Customizations**, then **Installed**, and start the sign-in from the Octen plugin or its MCP server (`octen_octen`).
4. In the browser, sign in to your Octen account, choose the account and API key the plugin should use, and approve. Antigravity then finishes the sign-in on its own. If it asks for an authorization code instead, copy the code from the browser page and paste it into Antigravity.

There is no API key to copy into Antigravity and nothing else to install. The MCP server is hosted at `https://mcp.octen.ai/mcp`; Antigravity keeps the sign-in token on your machine and refreshes it for you. This needs Antigravity CLI 1.5.8 or later, or the Antigravity App 2.33.0 or later; older versions sign you out when the first token expires, typically after an hour, so update instead of signing in again.

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

Calls are made with the API key you chose when signing in and are billed to its Octen account, at the rates on the [pricing page](https://octen.ai/pricing). `premier_search` has its own rate, and `broad_search` runs several searches per call.

## Troubleshooting

- **The agent does not see the Octen tools.** Check that the plugin is enabled in `/plugin` (CLI) or **Customizations** (App), and that Antigravity does not show that sign-in is required. If it does, sign in as described under [Setup](#setup).
- **`Access token rejected: <reason>`, or Antigravity shows that the Octen server needs sign-in again.** Most often the sign-in was revoked or has expired and could not be refreshed: check your Antigravity version (see [Setup](#setup)) and sign in again. If the error comes back right after signing in, contact Octen support with the full reason.
- **`code=401 msg=Invalid API Key`.** You are signed in, but the API key chosen at sign-in was rejected, for example because it was deleted. Sign out of the Octen server (in the App, use **Sign out** next to it), then sign in again and choose an active key.
- **You would rather use an API key than sign in.** Leave the plugin out and add the hosted server to your own MCP configuration with an `x-api-key` header, as described in the [Octen MCP Server](https://docs.octen.ai/integrations/octen-mcp-server) docs.
- **`video_search` is not available to your account.** Video Search is in beta. Contact Octen to request access.

## Learn more

- [Octen MCP Server](https://docs.octen.ai/integrations/octen-mcp-server): every tool and its parameters
- [Octen documentation](https://docs.octen.ai)

## License

[MIT](LICENSE)
