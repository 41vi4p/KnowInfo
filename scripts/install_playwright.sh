#!/bin/bash

# Install Playwright browsers for Twitter scraping

echo "========================================="
echo "Installing Playwright Browsers"
echo "========================================="
echo ""

# Install Playwright
pip install playwright

# Install browsers
echo "Installing Chromium browser..."
playwright install chromium

echo "Installing dependencies..."
playwright install-deps chromium

echo ""
echo "✅ Playwright setup complete!"
echo ""
echo "You can now scrape Twitter without API access."
