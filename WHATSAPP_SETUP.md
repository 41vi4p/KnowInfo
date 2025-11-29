# WhatsApp PyWhatKit Setup Guide

## 🎯 Overview

PyWhatKit uses **WhatsApp Web** to send messages, which means:
- ✅ **100% FREE** - No API costs, no Twilio
- ✅ Uses your **existing WhatsApp number**
- ✅ No special permissions needed
- ⚠️ Requires **GUI environment** (desktop/laptop with display)
- ⚠️ Requires **WhatsApp Web** to be logged in

---

## 📋 Prerequisites

### 1. System Requirements
- **GUI Environment**: Must have a desktop environment (X11/Wayland)
  - ✅ Ubuntu Desktop, Pop!_OS, Fedora Workstation
  - ❌ Headless servers (AWS EC2, DigitalOcean droplets without GUI)
- **Browser**: Chrome/Firefox installed
- **Python**: 3.8+ with GUI support
- **Your Phone**: WhatsApp installed on your mobile device

### 2. Check Your Display
```bash
# Check if you have a display
echo $DISPLAY
# Should show something like ":0" or ":1"

# If empty or error, you're on a headless server
# You'll need to set up a virtual display (see Advanced Setup below)
```

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Install Required System Packages

```bash
# Install display and browser automation tools
sudo apt update
sudo apt install -y \
    xdotool \
    scrot \
    python3-tk \
    python3-dev \
    chromium-browser

# Or for Google Chrome:
# wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
# sudo dpkg -i google-chrome-stable_current_amd64.deb
```

### Step 2: Verify Python Packages

```bash
# These should already be installed from requirements.txt
pip list | grep -E "pywhatkit|pyautogui|pillow"

# If missing, install:
pip install pywhatkit pyautogui pillow
```

### Step 3: Log into WhatsApp Web

**IMPORTANT**: You must log into WhatsApp Web **BEFORE** testing

1. **Open WhatsApp Web** in your browser:
   ```bash
   # Open Chrome/Chromium
   chromium-browser https://web.whatsapp.com
   # OR
   google-chrome https://web.whatsapp.com
   ```

2. **Scan QR Code** with your phone:
   - Open WhatsApp on your phone
   - Tap ⋮ (menu) → "Linked Devices"
   - Tap "Link a Device"
   - Scan the QR code on your computer screen

3. **Keep Browser Tab Open** (optional but recommended for testing)

### Step 4: Test PyWhatKit

Create a test script:

```bash
# Create test file
cat > test_whatsapp.py << 'EOF'
import pywhatkit as kit
from datetime import datetime

# Your phone number (with country code, no + needed in some methods)
# Format: Country code + number (e.g., "911234567890" for USA)
recipient = "+911234567890"  # CHANGE THIS to your test number

# Test message
message = "🤖 Hello from KnowInfo! This is a test message from PyWhatKit."

# Send in 2 minutes from now
now = datetime.now()
hour = now.hour
minute = now.minute + 2

if minute >= 60:
    minute -= 60
    hour += 1

print(f"📱 Sending WhatsApp message to {recipient}")
print(f"⏰ Scheduled for {hour:02d}:{minute:02d}")
print("🌐 WhatsApp Web will open automatically...")
print("⚠️  Keep the browser window open!\n")

try:
    kit.sendwhatmsg(recipient, message, hour, minute, wait_time=15, tab_close=False)
    print("\n✅ Message sent successfully!")
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure WhatsApp Web is logged in")
    print("2. Check your DISPLAY environment variable")
    print("3. Ensure you have a GUI environment")
EOF

# Run the test
python test_whatsapp.py
```

**What happens:**
1. Browser opens WhatsApp Web
2. Waits 15 seconds for page to load
3. Types the message
4. Sends it automatically
5. You'll see the message in your chat!

### Step 5: Integrate with KnowInfo

Update your environment to include your WhatsApp number:

```bash
# Edit .env file
nano .env

# Add or update:
WHATSAPP_BOT_NUMBER=+911234567890  # Your WhatsApp number
```

---

## 🎮 Usage Examples

### Example 1: Send Instant Message

```python
import asyncio
from src.stage5_response.whatsapp_bot import WhatsApp Bot
from config import settings

async def send_test_message():
    bot = WhatsAppBot(
        knowledge_base_path=settings.knowledge_base_path,
        vector_db_path=settings.vector_db_path
    )

    # Send to yourself or a test number
    await bot.send_instant_message(
        phone_number="+911234567890",  # Recipient
        message="🔍 Test message from KnowInfo bot!"
    )

asyncio.run(send_test_message())
```

### Example 2: Verify Claim and Send Result

```python
import asyncio
from src.stage5_response.whatsapp_bot import WhatsAppBot
from src.database.mongodb import init_mongo
from src.database.redis_cache import init_redis
from src.utils.model_manager import init_model_manager
from config import settings

async def verify_and_send():
    # Initialize services
    await init_mongo(settings.mongodb_uri, settings.mongodb_db_name)
    await init_redis(settings.redis_url)
    init_model_manager(
        ollama_base_url=settings.ollama_base_url,
        gemini_api_key=settings.gemini_api_key
    )

    # Create bot
    bot = WhatsAppBot(
        knowledge_base_path=settings.knowledge_base_path,
        vector_db_path=settings.vector_db_path
    )

    # Verify and respond
    result = await bot.verify_and_respond(
        phone_number="+911234567890",  # Recipient
        claim_text="WHO says COVID vaccines cause autism"
    )

    print(f"Status: {result.status}")
    print(f"Confidence: {result.confidence_score}%")

asyncio.run(verify_and_send())
```

### Example 3: Using the API

```bash
# Make sure the API server is running
# Visit http://localhost:8000/docs

# Send verification request via API
curl -X POST http://localhost:8000/api/whatsapp/verify \
  -H 'Content-Type: application/json' \
  -d '{
    "phone_number": "+911234567890",
    "claim_text": "Breaking: Drinking hot water cures COVID-19",
    "async_mode": false
  }'
```

---

## 🔧 Advanced Configuration

### For Headless Servers (VPS/Cloud)

If you're on a headless server, you need a virtual display:

```bash
# Install Xvfb (X Virtual Framebuffer)
sudo apt install -y xvfb

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Now run your Python scripts
python test_whatsapp.py
```

**Or use in a systemd service:**

```bash
# Create service file
sudo nano /etc/systemd/system/whatsapp-bot.service
```

```ini
[Unit]
Description=KnowInfo WhatsApp Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/KnowInfo
Environment="DISPLAY=:99"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
ExecStart=/usr/bin/python3 src/stage5_response/whatsapp_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Scheduled Messages

```python
import pywhatkit as kit

# Send at specific time
kit.sendwhatmsg(
    "+911234567890",
    "Scheduled message!",
    hour=14,  # 2 PM
    minute=30,  # 2:30 PM
    wait_time=20,
    tab_close=True
)
```

### Send to Multiple Recipients

```python
recipients = [
    "+911234567890",
    "+919876543210",
    "+910000000000"
]

for phone in recipients:
    await bot.send_instant_message(phone, "Broadcast message!")
    await asyncio.sleep(30)  # Wait 30 seconds between messages
```

---

## ⚠️ Important Notes

### Phone Number Format
- **Always include country code**
- Format: `+[country code][number]`
- Examples:
  - India: `+911234567890`
  - USA: `+11234567890`
  - UK: `+441234567890`

### Rate Limiting
- **WhatsApp may detect automation** if you send too many messages
- Recommendations:
  - Max 20-30 messages per hour
  - Wait 20-30 seconds between messages
  - Don't send identical messages repeatedly

### Browser Requirements
- **Keep WhatsApp Web logged in**
- **Don't close all browser windows** if using scheduled messages
- PyWhatKit opens new tabs automatically

### Security
- **Never commit phone numbers** to git
- Use environment variables: `.env` file
- Add `.env` to `.gitignore`

---

## 🐛 Troubleshooting

### Error: "Can't connect to display"
```
Xlib.error.DisplayConnectionError: Can't connect to display ":1"
```

**Solution:**
```bash
# Check display
echo $DISPLAY

# If empty, you're on headless server
# Use Xvfb (see Advanced Configuration)
```

### Error: "WhatsApp Web not loading"
```
Element not found / Timeout error
```

**Solutions:**
1. Increase `wait_time` parameter:
   ```python
   kit.sendwhatmsg(..., wait_time=30)  # Wait 30 seconds
   ```

2. Check internet connection

3. Manually open WhatsApp Web first:
   ```bash
   chromium-browser https://web.whatsapp.com
   ```

### Message Not Sending
1. **Verify WhatsApp Web is logged in**
2. **Check phone number format** (include +country code)
3. **Ensure recipient has WhatsApp**
4. **Wait for page to fully load** (increase wait_time)

### Browser Opens But Nothing Happens
- **Check if QR code is showing** → Need to scan it
- **WhatsApp Web session expired** → Log in again
- **Wrong time** → Check your system clock

---

## 📊 Testing Checklist

Before deploying:

- [ ] Logged into WhatsApp Web
- [ ] Tested simple message with `test_whatsapp.py`
- [ ] Verified phone number format
- [ ] Tested instant message
- [ ] Tested scheduled message
- [ ] Tested claim verification flow
- [ ] Set proper rate limits
- [ ] Added your number to `.env`

---

## 🎯 Quick Start Command

```bash
# Complete test in one command
python -c "
import pywhatkit as kit
from datetime import datetime

# CHANGE THIS NUMBER
phone = '+911234567890'

now = datetime.now()
kit.sendwhatmsg(phone, '🤖 KnowInfo test!', now.hour, now.minute + 2, 15, False)
"
```

---

## 📚 Additional Resources

- **PyWhatKit Docs**: https://github.com/Ankit404butfound/PyWhatKit
- **WhatsApp Web**: https://web.whatsapp.com
- **KnowInfo Docs**: See `SYSTEM_STATUS.md`

---

## ✅ Ready to Use!

Once setup is complete:

```bash
# Test the bot
python src/stage5_response/whatsapp_bot.py

# Or use the API
curl -X POST http://localhost:8000/api/whatsapp/verify \
  -H 'Content-Type: application/json' \
  -d '{"phone_number":"+YOUR_NUMBER","claim_text":"test"}'
```

**That's it! Your WhatsApp bot is ready to fact-check claims! 🎉**
