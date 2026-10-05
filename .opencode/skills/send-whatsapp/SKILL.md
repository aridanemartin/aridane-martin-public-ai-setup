---
name: send-whatsapp
description: Send a WhatsApp message via the CallMeBot API. Use when the user wants to send a notification, reminder, or message to their own WhatsApp number.
license: MIT
metadata:
  version: "1.0"
  scope: root
---

# Send WhatsApp

Sends a WhatsApp message to the configured phone number using the CallMeBot free API.

## When to Use

- "Send me a WhatsApp saying X"
- "Notify me on WhatsApp when X is done"
- "WhatsApp me: [message]"
- End of a long task: proactively offer to send a WhatsApp summary

## Setup Required

The skill reads the API key from the `CALLMEBOT_APIKEY` environment variable and the
destination number from `CALLMEBOT_PHONE` (international format, e.g. `+34600000000`).

If either variable is not set, tell the user:
> Set your CallMeBot credentials: `export CALLMEBOT_APIKEY=your_key_here` and
> `export CALLMEBOT_PHONE=+your_number_here` (add to `~/.zshrc` to persist them).
> Get your key by sending "I allow callmebot to send me messages" to the CallMeBot
> WhatsApp number, then follow the reply's instructions.

## How to Send

Run this Bash command (one line):

```bash
curl -s "https://api.callmebot.com/whatsapp.php?phone=${CALLMEBOT_PHONE}&text=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "<MESSAGE>"  )&apikey=$CALLMEBOT_APIKEY"
```

Or use this equivalent approach with URLSearchParams-style encoding via curl's `--data-urlencode`:

```bash
curl -sG "https://api.callmebot.com/whatsapp.php" \
  --data-urlencode "phone=${CALLMEBOT_PHONE}" \
  --data-urlencode "text=<MESSAGE>" \
  --data-urlencode "apikey=$CALLMEBOT_APIKEY"
```

## Steps

1. Check that `$CALLMEBOT_APIKEY` and `$CALLMEBOT_PHONE` are set. If not, show the setup instructions above and stop.
2. Compose the message text — use the user's exact wording, or a concise summary if sending a task result.
3. Run the curl command substituting `<MESSAGE>` with the actual message.
4. Report the API response to the user:
   - `Message Sent` → success
   - Any error → show the raw response and suggest checking the API key or phone registration.

## Notes

- The destination is always `${CALLMEBOT_PHONE}` — never hardcode a number in the command.
- The API is free but rate-limited — avoid sending more than one message per second.
- Messages are delivered via WhatsApp from the CallMeBot contact.
