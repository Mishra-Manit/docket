# Computer Use Claude Agent

This is a computer use agent that leverages Anthropic's Claude Computer Use API to control your computer and specifically open Chrome to navigate to Trader Joe's website.

## Features

- Takes screenshots of your screen
- Uses Claude's computer use capabilities to interact with your computer
- Opens Google Chrome browser
- Navigates to Trader Joe's website
- Provides step-by-step feedback

## Setup

1. **Install dependencies:**
   ```bash
   python setup.py
   ```

2. **Verify your API key:**
   Your API key is already configured in `config.py`. If you need to change it, edit the `ANTHROPIC_API_KEY` variable.

3. **Adjust display settings (if needed):**
   Edit `config.py` to match your screen resolution:
   ```python
   DISPLAY_WIDTH = 1920   # Your screen width
   DISPLAY_HEIGHT = 1080  # Your screen height
   ```

## Usage

Run the computer use agent:
```bash
python app.py
```

The agent will:
1. Ask for confirmation before starting
2. Take a screenshot of your current screen
3. Attempt to open Google Chrome
4. Navigate to traderjoes.com
5. Verify the website loaded correctly

## Requirements

- Python 3.7+
- Google Chrome browser installed
- Valid Anthropic API key with Computer Use access
- macOS (tested), Linux or Windows

## Important Notes

- **Security:** The agent can control your computer, so only run it when you're ready
- **Screen Resolution:** Make sure the display settings in `config.py` match your actual screen resolution
- **Permissions:** You may need to grant screen recording permissions to your terminal/Python on macOS
- **API Access:** Computer Use is a beta feature - ensure your API key has access

## Troubleshooting

- If Chrome doesn't open, check that it's installed and accessible
- If the agent can't take screenshots, check system permissions
- If API calls fail, verify your API key and computer use access
- For display issues, adjust the resolution settings in `config.py` 