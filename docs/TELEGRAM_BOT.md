# Telegram Bot Usage Guide

## 🚀 Quick Start

### 1. Start the Bot

Make sure your databases are running first:
```bash
# Start databases (if using Docker)
docker-compose up -d mongodb redis neo4j

# Or if databases are already running locally, just run the bot:
conda activate knowinfo
python run_telegram_bot.py
```

You should see output like:
```
🔵 KnowInfo Telegram Bot - Starting up...
============================================================
🤖 KnowInfo Telegram Fact-Checking Bot
============================================================
...
Telegram bot running
```

### 2. Find Your Bot on Telegram

1. Open Telegram app (mobile or desktop)
2. Search for your bot username (the one you created with @BotFather)
3. Click "START" or send `/start`

### 3. Start Fact-Checking!

Just send any message to the bot:
```
User: WHO says vaccines cause autism
```

The bot will respond with:
```
❌ FALSE

Confidence: 95%

Explanation:
We understand this is confusing. The World Health Organization has 
never made this claim. Multiple large-scale studies have found no 
link between vaccines and autism.

Sources:
1. WHO Vaccine Safety
2. CDC Autism Research

🤖 Powered by KnowInfo
```

## 📱 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show welcome message | `/start` |
| `/help` | Display help information | `/help` |
| `/verify <claim>` | Verify a specific claim | `/verify COVID is caused by 5G` |

**Note:** You can also just send any text message without a command, and the bot will automatically verify it!

## 🎯 Usage Examples

### Example 1: Simple Claim
```
User: The earth is flat
Bot: ❌ FALSE (Confidence: 99%)
```

### Example 2: Medical Claim
```
User: Drinking bleach cures COVID-19
Bot: ❌ FALSE (Confidence: 100%)
     ⚠️  P0 Priority - Potentially Harmful
```

### Example 3: Forwarded Message
Forward any message from another chat to the bot, and it will fact-check it!

### Example 4: Using /verify Command
```
User: /verify The moon landing was faked
Bot: ❌ FALSE (Confidence: 98%)
```

## ⚙️ Configuration

The bot uses settings from your `.env` file:

```bash
# Required
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# At least one LLM provider (Gemini recommended)
GEMINI_API_KEY=your_gemini_api_key

# Or use local Ollama (FREE)
OLLAMA_BASE_URL=http://localhost:11434
USE_LOCAL_MODELS_FIRST=true

# Databases (should already be configured)
MONGODB_URI=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
```

## 🏗️ How It Works

```
User Message (Telegram)
        ↓
1. Claim Extraction (Gemini/Ollama)
        ↓
2. Vector Search (ChromaDB)
        ↓
3. Source Evaluation (LLM)
        ↓
4. Consensus Calculation
        ↓
5. Response Generation
        ↓
Telegram Message (User)
```

## 🔍 Features

- ✅ **Instant verification** - Usually responds in < 60 seconds
- ✅ **Source citations** - Shows authoritative sources
- ✅ **Confidence scores** - Transparent about certainty
- ✅ **Caching** - Repeated claims return instantly
- ✅ **Priority handling** - Flags harmful misinformation
- ✅ **Rich formatting** - Emojis, bold text, links
- ✅ **Command support** - `/start`, `/help`, `/verify`
- ✅ **Message forwarding** - Forward from any chat to verify

## 🛠️ Troubleshooting

### Bot doesn't respond
- Check that `run_telegram_bot.py` is still running
- Check your internet connection
- Verify the bot token is correct in `.env`
- Look for errors in the terminal where bot is running

### "No verifiable claims found"
- Make the claim more specific
- Add context or details
- Try rephrasing as a clear statement
- Example: Instead of "Is this true?", say "WHO recommends X"

### "Cannot verify claim"
- The knowledge base might not have relevant sources
- Add more sources with `scripts/seed_knowledge_base.py`
- Or the claim might be too new/obscure

### Bot is slow
- First query takes longer (loading models)
- Subsequent queries should be faster
- Cached results return instantly
- Check if Ollama/APIs are responsive

## 📊 Monitoring

Watch the bot logs in the terminal for:
- Incoming queries
- Claim extraction results
- Verification status
- Response times
- Errors

Example log output:
```
[info] Starting verification claim_text=WHO says vaccines cause autism
[info] Claims extracted count=1
[info] Vector search complete sources=5
[info] Verification completed status=false confidence=95.0
```

## 🔐 Privacy & Safety

- Bot doesn't store personal information
- Messages are processed in real-time
- Results are cached by claim content (not user)
- No message history is retained
- All verification is automated

## 💡 Tips

1. **Be specific**: "WHO says X" is better than "Is X true?"
2. **Forward messages**: You can forward from any chat to verify
3. **Use commands**: `/verify` lets you include context
4. **Check sources**: Always read the cited sources
5. **Report issues**: If bot gives wrong info, that's a bug!

## 🚦 Status Indicators

- ✅ **TRUE** - Claim is accurate (>80% confidence)
- ❌ **FALSE** - Claim is incorrect (>80% confidence)
- ⚠️ **MISLEADING** - Partially true/false or needs context
- 🔍 **UNVERIFIED** - Cannot verify with current knowledge base
- 📅 **OUTDATED** - Information is no longer current

## 🎓 Advanced Usage

### Running in Background
```bash
# Using nohup
nohup python run_telegram_bot.py > telegram_bot.log 2>&1 &

# Using screen
screen -S telegram_bot
python run_telegram_bot.py
# Press Ctrl+A, then D to detach
```

### Monitoring Logs
```bash
# Follow live logs
tail -f telegram_bot.log

# Search for errors
grep ERROR telegram_bot.log
```

### Stopping the Bot
```bash
# If running in foreground
Press Ctrl+C

# If running in background
pkill -f run_telegram_bot.py
```

## 📞 Support

If you encounter issues:
1. Check the logs in the terminal
2. Verify all dependencies are installed
3. Check database connections
4. Ensure API keys are valid
5. Try restarting the bot

---

**Ready to fight misinformation? Start the bot and let's go! 🚀**
