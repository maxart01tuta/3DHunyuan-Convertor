# HyperAgent Guide

HyperAgent — AI-powered автономный веб-агент Hyperbrowser.ai. Позволяет описывать задачи на естественном языке вместо написания селекторов и логики навигации.

## Quick Start (Python)

```python
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import StartHyperAgentTaskParams
from dotenv import load_dotenv
import os

load_dotenv()

client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))

result = client.agents.hyper_agent.start_and_wait(
    StartHyperAgentTaskParams(
        task="Go to Hacker News and get the title of the first post"
    )
)

print(f"Result: {result.data.final_result}")
```

## Async Version

```python
from hyperbrowser import AsyncHyperbrowser
from hyperbrowser.models import StartHyperAgentTaskParams
import asyncio

client = AsyncHyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))

async def main():
    result = await client.agents.hyper_agent.wait_for_task(
        StartHyperAgentTaskParams(
            task="Go to 3d.hunyuan.tencent.com and check the 3D Photo generation page"
        )
    )
    print(result.data.final_result)

asyncio.run(main())
```

## REST API

```bash
curl -X POST https://api.hyperbrowser.ai/api/task/hyper-agent \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: <YOUR_API_KEY>' \
  -d '{"task": "Go to Hacker News and get the title of the first post"}'
```

## Key Features

- **No CSS selectors needed** — AI handles DOM navigation
- **Complex workflows** — Multi-step tasks, dynamic content
- **Rapid prototyping** — Describe what you want, not how to do it
- **Handles browser state automatically**
- **Supports multiple AI models** — OpenAI GPT-4o (default), Claude, Gemini

## When to Use HyperAgent vs Playwright

| Use HyperAgent When | Use Playwright When |
|---------------------|---------------------|
| Dynamic/complex DOMs | Known, stable selectors |
| Multi-step complex flows | Precise timing control |
| Rapid prototyping | Maximum reliability |
| Content extraction | Form filling with validation |
| LLM-driven decisions | High-volume scraping |

## 3DHunyuan Use Cases

HyperAgent could be used for:
1. **Photo upload flow**: "Navigate to 3d.hunyuan.tencent.com, upload a photo with prompt '3D model', and click Generate"
2. **Status verification**: "Check if the generation completed and extract the download URL"
3. **Cookie-based auth**: "Load session cookies and verify authentication on 3d.hunyuan.tencent.com"

## Node.js SDK (HyperAgent Class)

```typescript
import { HyperAgent } from "@/agent";
import { ChatOpenAI } from "@langchain/openai";

const agent = new HyperAgent({
  llm: new ChatOpenAI({ modelName: "gpt-4o" }),
  browserProvider: "Hyperbrowser",
  debug: true,
  customActions: [/* custom actions */],
});

// Task execution
const result = await agent.executeTask(
  "Find the contact email on this page",
  { outputSchema: z.object({ email: z.string() }) }
);

// Async task with control
const task = await agent.executeTaskAsync("Go to example.com and summarize");
task.pause();
task.resume();
task.cancel();
```

## MCP Integration

```python
# MCP allows extending agent with custom tools
await agent.initializeMCPClient({
    "servers": [
        {"id": "server1", "url": "ws://localhost:8080"}
    ]
})
```
