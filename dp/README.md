# DaisuPop v0.0.1

Caveman rules:

1. Pick 1 to 6 dice.
2. Press the popper.
3. Cloudflare rolls the dice.
4. Everyone in the same room sees the same roll.
5. Last 20 rolls stay in session memory.
6. No bets. No scoring. No leaderboard. Players make the game.

This is a Cloudflare Worker + Durable Object app for `dp.f-keys.com`.

## Deploy

Cloudflare dashboard:

1. Workers & Pages.
2. Create app.
3. Connect GitHub repo `vince-gonzalez/f-keys`.
4. Root directory: `dp`
5. Build command: `npm run build`
6. Deploy command: `npx wrangler deploy`

Set env var before build:

```text
VITE_DISCORD_CLIENT_ID=your_discord_app_client_id
```

Route:

```text
dp.f-keys.com/*
```

Worker:

```text
daisupop
```
