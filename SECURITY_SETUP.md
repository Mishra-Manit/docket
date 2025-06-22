# Security Setup Guide

## 🔐 Environment Variables Setup

This project has been configured to use environment variables for sensitive information like API keys. Follow these steps to set up your environment:

### 1. Backend Environment Setup

1. Navigate to the `backend/` directory
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Edit the `.env` file and replace the placeholder with your actual Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_actual_api_key_here
   ```

### 2. Important Security Notes

- ✅ **DO commit**: `.env.example` files (these are templates)
- ❌ **NEVER commit**: `.env` files (these contain actual secrets)
- ✅ The `.gitignore` files are configured to exclude `.env` files automatically
- ✅ API keys are loaded from environment variables, not hardcoded

### 3. Verification

After setting up your `.env` file, verify that:
- Your application starts without errors
- The API key is loaded correctly from the environment
- The `.env` file is listed in `.gitignore` and won't be committed

### 4. For Contributors

If you're contributing to this project:
1. Never commit actual API keys or secrets
2. Use the `.env.example` template to understand required variables
3. Test with your own API keys in your local `.env` file

### 5. What Was Changed for Security

- Moved hardcoded API key from `config.py` to environment variables
- Added comprehensive `.gitignore` files
- Updated `config.py` to use `python-dotenv`
- Added validation to ensure API key is present
- Created `.env.example` for easy setup

This ensures your sensitive information stays secure and is never accidentally committed to version control. 