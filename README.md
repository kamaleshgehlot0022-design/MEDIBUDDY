# MediBuddy - Enterprise Healthcare Agent

An AI-powered platform for healthcare professionals providing instant drug and reimbursement information.

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env
# Edit .env with your API key

# Run the server
python -m uvicorn main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## Features

- 💊 **Drug Lookup** - NDC, GPI, dosing, indications, warnings
- 💰 **Pricing Intelligence** - AWP, WAC, NADAC, 340B, cash prices
- 🏥 **Payer Coverage** - 4,800+ plans, tiers, PA requirements
- 📋 **Prior Auth Assistant** - Auto-generate PA forms
- ⚠️ **Drug Interactions** - DDI, allergies, renal dosing
- 🤖 **AI Chat** - Natural language queries

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+K` | Command Palette |
| `[` | Toggle Sidebar |
| `V` | Voice Mode |
| `D` | Dashboard |
| `S` | Drug Search |

## License

MIT
