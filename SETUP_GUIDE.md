# Computer Use Claude Agent - Setup Guide

## Overview
This application connects a React frontend with a Flask backend that uses Claude's Computer Use API to automatically navigate to websites via Mac Spotlight.

## Architecture
```
Frontend (React/Next.js) → Flask API → Claude Computer Use Agent → Mac Spotlight → Website
```

## Prerequisites

### 1. System Requirements
- **macOS** (required for Spotlight functionality)
- **Python 3.8+**
- **Node.js 18+**
- **Anthropic API Key**

### 2. macOS Permissions
You **MUST** grant these permissions before running:

1. **System Preferences → Security & Privacy → Privacy**
2. **Screen Recording** - Add Terminal/your code editor
3. **Accessibility** - Add Terminal/your code editor

⚠️ **Without these permissions, the Computer Use Agent will not work!**

### 3. Environment Setup
1. Add your Anthropic API key to `backend/config.py`:
   ```python
   ANTHROPIC_API_KEY = "your-api-key-here"
   ```

## Quick Start

### Option 1: Use the Start Script (Recommended)
```bash
# Start both frontend and backend
./start.sh full

# Or start individually:
./start.sh backend  # Flask server only
./start.sh frontend # Next.js dev server only
```

### Option 2: Manual Setup

#### Backend (Flask API)
```bash
cd backend
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python app.py server
```
The Flask server will run on `http://localhost:5000`

#### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on `http://localhost:3000`

## API Endpoints

### Health Check
```bash
GET http://localhost:5000/health
```

### Navigate to Website
```bash
POST http://localhost:5000/navigate
Content-Type: application/json

{
  "website": "google.com"
}
```

## How It Works

1. **User Input**: Enter a website in the frontend form
2. **API Request**: Frontend sends POST request to `/navigate`
3. **Agent Activation**: Flask backend creates a Computer Use Agent
4. **Spotlight Control**: Agent opens Spotlight with `Cmd+Space`
5. **Navigation**: Types website URL and presses Enter
6. **Feedback**: Success/error message shown to user

## Supported Website Formats

- Simple domains: `google`, `github`
- Full domains: `google.com`, `github.com`
- With protocol: `https://stackoverflow.com`
- Auto-completion: `google` → `google.com`

## Safety Features

- **Emergency Stop**: Move mouse to top-left corner
- **Thread Safety**: Only one agent runs at a time
- **Error Handling**: Graceful failure with user feedback
- **Timeout Protection**: Agent stops after max iterations

## Troubleshooting

### "Permission Denied" Errors
- Grant Screen Recording and Accessibility permissions
- Restart Terminal after granting permissions

### "Connection Refused" 
- Make sure Flask server is running on port 5000
- Check if another service is using port 5000

### Agent Not Responding
- Move mouse to top-left corner to trigger emergency stop
- Restart the Flask server
- Check console logs for detailed error messages

### "Failed to connect to backend"
- Ensure Flask server is running: `./start.sh backend`
- Check if CORS is properly configured
- Verify the frontend is making requests to `http://localhost:5000`

## Development

### Backend Development
```bash
cd backend
source env/bin/activate
python app.py  # Command-line mode for testing
python app.py server  # Web server mode
```

### Frontend Development
```bash
cd frontend
npm run dev
```

## Advanced Usage

### Command Line Interface
You can still use the agent from command line:
```bash
cd backend
source env/bin/activate
python app.py
# Follow prompts to enter website
```

### Custom Configuration
Edit `backend/config.py` to adjust:
- Display resolution settings
- API timeouts
- Agent behavior parameters

## Security Notes

⚠️ **This application controls your computer**
- Only run on trusted networks
- Be cautious with the websites you navigate to
- The emergency stop (mouse to corner) is your safety net
- Review all code before running in production

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review console logs for detailed error messages
3. Ensure all permissions are granted
4. Verify your API key is valid and has Computer Use access 