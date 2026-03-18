# why machine

> "But can Claude Code sit in meetings asking 'why?' until we reach an actual first-principles answer?"
> — [@jen_spies](https://www.threads.net/@jen_spies)

A minimal web app that channels Claude as a Socratic questioner: you state a belief, decision, or assumption, and it keeps asking **why?** — in varied, incisive ways — until you hit bedrock.

![why machine screenshot](https://i.imgur.com/placeholder.png)

## What it does

1. You state something you believe or want to do (e.g. "We should rewrite our codebase")
2. Claude asks a probing question — not just "why?" but things like:
   - "What makes that necessarily true?"
   - "What's the underlying assumption there?"
   - "What would break if that weren't true?"
3. You answer. Claude digs deeper.
4. When you hit a first-principles answer — a bedrock truth that can't be reduced further — Claude says "We've reached bedrock" and summarizes the full chain of reasoning.

## Ship it

### One-click deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FNotGregMaxwellNullC%2FInput-algorithmic-creativity%2Ftree%2Fmain%2Fwhy-machine&env=ANTHROPIC_API_KEY&envDescription=Your%20Anthropic%20API%20key&envLink=https%3A%2F%2Fconsole.anthropic.com%2F)

### Run locally

```bash
git clone https://github.com/NotGregMaxwellNullC/Input-algorithmic-creativity
cd Input-algorithmic-creativity/why-machine

cp .env.example .env.local
# add your ANTHROPIC_API_KEY to .env.local

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## The prompt

The system prompt is in [`app/api/chat/route.ts`](app/api/chat/route.ts). The core instruction:

> You are a first-principles thinking partner sitting in a meeting. Your entire job is to ask "why?" — in varied, incisive, curious ways — until the conversation reaches a bedrock answer that cannot be reduced any further.

Key rules Claude follows:
- One question per turn, never two
- Vary phrasing so it doesn't feel robotic
- Reject answers that are conventions or habits dressed as reasons
- When bedrock is reached: say "We've reached bedrock" and summarize the chain

## Stack

- [Next.js 14](https://nextjs.org/) (App Router)
- [Claude claude-sonnet-4-6](https://anthropic.com) via the [Anthropic SDK](https://github.com/anthropic/anthropic-sdk-python)
- [Tailwind CSS](https://tailwindcss.com)
- Streaming responses

## License

MIT
