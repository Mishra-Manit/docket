#!/usr/bin/env python3
"""
Computer Use Claude Agent - Generic Website Navigator with Flask API
This script uses Anthropic's Computer Use feature to control the computer,
specifically to open Spotlight and navigate to any user-specified website.
Can be used as both a command-line tool and a web API.
"""

import time
import base64
from io import BytesIO
from anthropic import Anthropic
from PIL import ImageGrab
import pyautogui
import config
import threading
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import re
import os
import json
import subprocess
from spotlight_optimizer import spotlight_optimizer

# Configure pyautogui
pyautogui.FAILSAFE = True  # Keep failsafe enabled for safety
pyautogui.PAUSE = config.PYAUTOGUI_PAUSE  # Pause between actions for better reliability

# Flask app setup
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Global lock to ensure only one agent runs at a time
agent_lock = threading.Lock()

# Directory to store temporary JSON files for dynamic endpoints
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Track endpoints that have been registered at runtime
dynamic_routes = set()

class WebsiteNavigatorAgent:
    def __init__(self):
        self.client = Anthropic(
            api_key=config.ANTHROPIC_API_KEY,
            default_headers={
                "anthropic-beta": "computer-use-2025-01-24"
            }
        )
        self.model = "claude-opus-4-20250514"  # Use Claude 4 Opus for computer use sessions
        
    def extract_website_from_text(self, user_input):
        """
        Use Claude to extract website information from natural language input
        Returns the website URL/domain that the user wants to visit
        """
        try:
            system_prompt = """You are a helpful assistant that extracts website information from user requests.

Your task is to identify what website the user wants to visit based on their natural language input.

Rules:
1. Extract the main website/domain the user wants to visit
2. Return ONLY the website domain (e.g., "google.com", "github.com", "traderjoes.com")
3. Do NOT include protocols (http/https)
4. If it's a well-known brand/company, use their main website domain
5. If the user mentions a specific domain, use that exact domain
6. If unclear or no website can be identified, return "UNCLEAR"
7. SPECIAL CASE: For ANY mention of Trader Joe's, TJ's, traderjoes, or related terms, return "traderjoes.com.special"

Examples:
- "Navigate to the traderjoes website" → "traderjoes.com.special"
- "Go to trader joes" → "traderjoes.com.special"
- "Take me to TJ's" → "traderjoes.com.special"
- "trader joe's new products" → "traderjoes.com.special"
- "navigate to traderjoes whats new site" → "traderjoes.com.special"
- "traderjoes what's new" → "traderjoes.com.special"
- "tj new products" → "traderjoes.com.special"
- "trader joes whats new" → "traderjoes.com.special"
- "traderjoes.com" → "traderjoes.com.special"
- "trader joe's website" → "traderjoes.com.special"
- "Go to Google" → "google.com"
- "Open GitHub" → "github.com"
- "Visit stackoverflow" → "stackoverflow.com"
- "Take me to the Apple website" → "apple.com"
- "Go to reddit" → "reddit.com"
- "Navigate to youtube" → "youtube.com"
- "github.com" → "github.com"
- "https://example.com" → "example.com"
- "What is the weather?" → "UNCLEAR"

IMPORTANT: Return ONLY the domain name or "traderjoes.com.special" for Trader Joe's, nothing else. 
Be very liberal in detecting Trader Joe's references - any mention of "trader", "traderjoes", "tj", combined with words like "joes", "joe's", "new", "products", "whats", "what's", "site", "website" should trigger "traderjoes.com.special"."""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Use Claude 4 Sonnet for extraction
                system=system_prompt,
                max_tokens=50,
                messages=[{
                    "role": "user", 
                    "content": f"Extract the website from this user request: '{user_input}'"
                }]
            )
            
            extracted_website = response.content[0].text.strip()
            print(f"🤖 Claude extracted website: '{extracted_website}' from input: '{user_input}'")
            
            # Validate the extraction
            if extracted_website == "UNCLEAR" or not extracted_website:
                return None
            
            # Special case for Trader Joe's
            if extracted_website == "traderjoes.com.special":
                return "traderjoes.com.special"
                
            # Basic validation - should look like a domain
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', extracted_website):
                # If it doesn't look like a domain, try to fix common patterns
                if '.' not in extracted_website:
                    extracted_website = f"{extracted_website}.com"
                else:
                    return None
            
            return extracted_website
            
        except Exception as e:
            print(f"❌ Error extracting website from text: {e}")
            return None
        
    def take_screenshot(self):
        """Take a screenshot and return it as base64 encoded string"""
        try:
            screenshot = ImageGrab.grab()
            buffer = BytesIO()
            screenshot.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            return img_base64
        except Exception as e:
            error_msg = str(e)
            if "Input/output error" in error_msg or "Permission denied" in error_msg:
                raise Exception(
                    "Screen recording permission required. "
                    "Please grant Screen Recording permission to Terminal in "
                    "System Preferences > Security & Privacy > Privacy > Screen Recording"
                )
            else:
                raise Exception(f"Screenshot failed: {error_msg}")
    
    def execute_computer_tool(self, tool_input):
        """Execute a computer tool action and return the result"""
        action = tool_input.get('action')
        result = ""
        
        try:
            if action == 'screenshot':
                # Take screenshot and return as base64 for Claude
                screenshot_b64 = self.take_screenshot()
                result = screenshot_b64  # Return the base64 data directly for Claude to process
                
            elif action == 'left_click':
                # Click at coordinates
                if 'coordinate' in tool_input:
                    coordinate = tool_input['coordinate']
                    x, y = coordinate
                    print(f"Clicking at coordinates ({x}, {y})")
                    pyautogui.click(x, y)
                    result = f"Left clicked at coordinates ({x}, {y})"
                else:
                    x, y = 100, 100
                    print(f"No coordinates provided, using default ({x}, {y})")
                    pyautogui.click(x, y)
                    result = f"Left clicked at default coordinates ({x}, {y})"
                
            elif action == 'type':
                # Type text
                text = tool_input.get('text', '')
                print(f"Typing: {text}")
                pyautogui.write(text)
                result = f"Typed text: {text}"
                
            elif action == 'key':
                # Press a key or key combination - use only 'key' field per API docs
                key_value = tool_input.get('key')
                
                print(f"Key action requested. Raw tool_input: {tool_input}")
                print(f"Extracted key_value: {key_value}")
                
                if not key_value:
                    print("No key value found, using default 'return'")
                    pyautogui.press('return')
                    result = "Pressed Enter key (default)"
                else:
                    # Normalize to list for hotkey handling
                    if isinstance(key_value, str):
                        keys = [k.strip() for k in key_value.split('+') if k.strip()]
                    else:
                        keys = key_value
                    
                    print(f"Processed keys: {keys}")
                    
                    if len(keys) == 1:
                        print(f"Single key press: {keys[0]}")
                        pyautogui.press(keys[0])
                        result = f"Pressed key: {keys[0]}"
                    else:
                        print(f"Key combination: {keys}")
                        if 'command' in keys and 'space' in keys:
                            print("🔍 Detected command+space - using optimized Spotlight opening")
                            success, time_taken = spotlight_optimizer.open_spotlight_optimized()
                            if success:
                                result = f"Pressed key combination: {'+'.join(keys)} (opened in {time_taken:.3f}s)"
                            else:
                                result = f"Failed to open Spotlight after {time_taken:.3f}s - please try again"
                        else:
                            pyautogui.hotkey(*keys)
                            result = f"Pressed key combination: {'+'.join(keys)}"
                
            elif action == 'scroll':
                # Scroll in specified direction and amount
                direction = tool_input.get('scroll_direction', 'down')
                amount = int(tool_input.get('scroll_amount', 1))
                # Move to coordinate first if provided
                if 'coordinate' in tool_input:
                    x, y = tool_input['coordinate']
                    pyautogui.moveTo(x, y)
                scroll_pixels = amount * 100  # heuristic: 100px per unit
                print(f"Scrolling {direction} by {amount} units ({scroll_pixels} px)")
                pyautogui.scroll(-scroll_pixels if direction == 'down' else scroll_pixels)
                result = f"Scrolled {direction} by {amount} units"

            elif action == 'wait':
                # Accept both 'seconds' and 'duration' for compatibility
                seconds = float(tool_input.get('seconds') or tool_input.get('duration', 1))
                print(f"Waiting for {seconds} seconds")
                time.sleep(seconds)
                result = f"Waited {seconds} seconds"

            elif action == 'right_click':
                coordinate = tool_input.get('coordinate')
                if coordinate:
                    x, y = coordinate
                    print(f"Right clicking at ({x}, {y})")
                    pyautogui.rightClick(x, y)
                else:
                    pyautogui.rightClick()
                result = "Performed right click"

            elif action == 'double_click':
                coordinate = tool_input.get('coordinate')
                if coordinate:
                    x, y = coordinate
                    print(f"Double clicking at ({x}, {y})")
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.doubleClick()
                result = "Performed double click"

            elif action == 'left_click_drag':
                start = tool_input.get('start_coordinate')
                end = tool_input.get('end_coordinate')
                if start and end:
                    sx, sy = start; ex, ey = end
                    print(f"Dragging from ({sx}, {sy}) to ({ex}, {ey})")
                    pyautogui.moveTo(sx, sy)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(ex, ey, duration=0.2)
                    pyautogui.mouseUp()
                    result = f"Dragged mouse from ({sx}, {sy}) to ({ex}, {ey})"
                else:
                    result = "Missing start_coordinate or end_coordinate for left_click_drag"

            elif action == 'left_mouse_down':
                coordinate = tool_input.get('coordinate')
                if coordinate:
                    x, y = coordinate
                    pyautogui.mouseDown(x, y)
                else:
                    pyautogui.mouseDown()
                result = "Mouse button down"

            elif action == 'left_mouse_up':
                pyautogui.mouseUp()
                result = "Mouse button up"

            elif action == 'hold_key':
                key_to_hold = tool_input.get('key')
                hold_seconds = float(tool_input.get('seconds', 0.5))
                if not key_to_hold:
                    result = "hold_key action requires 'key' parameter"
                else:
                    print(f"Holding key '{key_to_hold}' for {hold_seconds} seconds")
                    pyautogui.keyDown(key_to_hold)
                    time.sleep(hold_seconds)
                    pyautogui.keyUp(key_to_hold)
                    result = f"Held key '{key_to_hold}' for {hold_seconds} seconds"

            elif action == 'mouse_move':
                # Move mouse to coordinates
                if 'coordinate' in tool_input:
                    coordinate = tool_input['coordinate']
                    x, y = coordinate
                    print(f"Moving mouse to coordinates ({x}, {y})")
                    pyautogui.moveTo(x, y)
                    result = f"Moved mouse to coordinates ({x}, {y})"
                else:
                    x, y = 100, 100
                    print(f"No coordinates provided, using default ({x}, {y})")
                    pyautogui.moveTo(x, y)
                    result = f"Moved mouse to default coordinates ({x}, {y})"
                
            elif action == 'capture_html':
                # Capture the current page HTML by selecting all, copying and reading clipboard
                print("⚙️  Capturing page HTML via clipboard")
                try:
                    # Select all and copy
                    pyautogui.hotkey('command', 'a')
                    time.sleep(0.15)
                    pyautogui.hotkey('command', 'c')
                    time.sleep(0.15)

                    # Read clipboard contents (macOS specific)
                    html_bytes = subprocess.check_output(['pbpaste'])
                    html_text = html_bytes.decode('utf-8', errors='ignore')

                    snippet = (html_text[:200] + '...') if len(html_text) > 200 else html_text
                    result = html_text  # Return full HTML for downstream processing
                    print(f"📄 HTML captured (first 200 chars): {snippet}")
                except Exception as cap_err:
                    err_msg = f"Failed to capture HTML: {cap_err}"
                    print(f"❌ {err_msg}")
                    result = err_msg
            
            else:
                result = f"Unknown action: {action}"
                
        except Exception as e:
            error_msg = str(e)
            if "Permission denied" in error_msg or "Accessibility" in error_msg:
                result = f"Permission error: Please grant Accessibility permission to Terminal in System Preferences > Security & Privacy > Privacy > Accessibility"
            elif "Screen recording permission required" in error_msg:
                result = error_msg
            else:
                result = f"Error executing {action}: {error_msg}"
            print(f"❌ Exception in execute_computer_tool: {e}")
            
        return result
    
    def agent_loop(self, initial_message, max_iterations=10):
        """Run the agent loop with tool use"""
        system_prompt = (
            "You are controlling a macOS machine via the computer tool. "
            "You have access to these actions: screenshot, left_click, right_click, double_click, left_click_drag, left_mouse_down, left_mouse_up, type, key, hold_key, scroll, mouse_move, wait, capture_html. "
            "\nIMPORTANT GUIDELINES:\n"
            "- ALWAYS take a screenshot first to see the current state\n"
            "- After each action that should change the display, take another screenshot to verify the result\n"
            "- For keyboard shortcuts on macOS: Use 'command+space' to open Spotlight (OPTIMIZED - opens fast!), 'return' for Enter\n"
            "- When using 'key' action, populate ONLY the 'key' field with exact combinations (e.g., 'command+space', 'return')\n"
            "- For wait action, use 'seconds' or 'duration' parameter (e.g., {'action': 'wait', 'seconds': 2})\n"
            "- SPOTLIGHT IS OPTIMIZED: command+space now opens instantly and automatically detects when ready\n"
            "- If Spotlight is already open (visible in screenshot), clear any existing text with command+a first, then type the new URL\n"
            "- Take a screenshot immediately after command+space - no additional waiting needed\n"
            "- If an action doesn't work as expected, take a screenshot and try a different approach\n"
            "- Be efficient - the system is now optimized for speed and responsiveness"
        )

        messages = [{"role": "user", "content": initial_message}]
        
        for iteration in range(max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            try:
                # Call Claude with current conversation (non-streaming)
                response = self.client.beta.messages.create(
                    model=self.model,
                    system=system_prompt,
                    max_tokens=1024,
                    messages=messages,
                    tools=[
                        {
                            "type": "computer_20250124",
                            "name": "computer",
                            "display_width_px": config.DISPLAY_WIDTH,
                            "display_height_px": config.DISPLAY_HEIGHT
                        }
                    ],
                    betas=["computer-use-2025-01-24"],  # CRITICAL: Required beta flag for Claude 4
                    stream=False  # Changed to False for reliable tool use
                )
                
                # Add assistant's response to conversation history
                messages.append({"role": "assistant", "content": response.content})
                
                tool_used = False
                tool_results = []
                
                # Find and execute any tool use requests
                for block in response.content:
                    if block.type == 'text':
                        print(f"💬 Claude: {block.text}")
                    
                    elif block.type == 'tool_use':
                        tool_used = True
                        tool_name = block.name
                        tool_input = block.input
                        tool_use_id = block.id
                        
                        print(f"🔧 Tool: {tool_name}")
                        print(f"📝 Action: {tool_input.get('action', 'unknown')}")
                        print(f"🔸 Raw tool input: {tool_input}")
                        if 'coordinate' in tool_input:
                            print(f"📍 Coordinates: {tool_input['coordinate']}")
                        if 'key' in tool_input:
                            print(f"⌨️  Key: {tool_input['key']}")
                        
                        # Execute the tool
                        if tool_name == "computer":
                            result_content = self.execute_computer_tool(tool_input)
                        else:
                            result_content = f"Unknown tool: {tool_name}"
                        
                        # Smart logging - don't flood console with base64 screenshot data
                        if tool_input.get('action') == 'screenshot' and isinstance(result_content, str) and len(result_content) > 100:
                            print(f"✅ Result: Screenshot captured successfully ({len(result_content)} characters of base64 data)")
                        else:
                            print(f"✅ Result: {result_content}")
                        
                        # Collect tool results (special handling for screenshots)
                        if tool_input.get('action') == 'screenshot' and isinstance(result_content, str) and len(result_content) > 100:
                            # Screenshot result - format as image
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": [
                                    {
                                        "type": "image",
                                        "source": {
                                            "type": "base64",
                                            "media_type": "image/png",
                                            "data": result_content
                                        }
                                    }
                                ]
                            })
                        else:
                            # Regular text result
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result_content
                            })
                
                # If tools were used, add results to conversation and continue
                if tool_used:
                    messages.append({"role": "user", "content": tool_results})
                    time.sleep(config.BETWEEN_ITERATIONS_SLEEP)  # Pause for reliability
                else:
                    # No tools used, conversation is complete
                    print("🏁 Task completed - no more tools requested")
                    break
                    
            except Exception as e:
                print(f"❌ Error in iteration {iteration + 1}: {e}")
                
        return messages
    
    def navigate_to_website(self, website_url):
        """Open Spotlight search and navigate to any specified website"""
        print(f"🚀 Starting computer use agent to navigate to: {website_url}")
        print("⚠️  IMPORTANT: The agent will now control your computer!")
        print("   Move your mouse to the top-left corner to emergency stop")
        
        time.sleep(config.USER_WARNING_DELAY)  # Give user time to read warning
        
        # Special handling for Trader Joe's
        if website_url == "traderjoes.com.special":
            target_url = "https://www.traderjoes.com/home/products/category/products-2?filters=%7B%22areNewProducts%22%3Atrue%7D"
            spotlight_url = target_url  # Use the full URL for Spotlight
            print(f"🏪 Special Trader Joe's navigation to What's New page: {target_url}")
        else:
            # Clean up the website URL if needed
            if not website_url.startswith(('http://', 'https://')):
                # Add .com if it's just a domain name without extension
                if '.' not in website_url:
                    website_url = f"{website_url}.com"
            target_url = website_url
            spotlight_url = website_url  # Use the website_url for Spotlight

        # --- SIMPLE DEMO FLOW (skips Claude Computer Use) ---
        if website_url == "traderjoes.com.special":
            print("🧪 DEMO MODE: Launching simple pyautogui automation (no Claude Computer Use).")
            # Step 1: small delay so the user can see what's happening
            time.sleep(3)
            # Step 2: Open Spotlight
            pyautogui.hotkey('command', 'space')
            time.sleep(0.3)
            # Step 3: Type the target Trader Joe's What's New URL
            pyautogui.write(target_url)
            # Step 4: Press return to open the URL
            pyautogui.press('return')
            # Step 5: Wait a few seconds for the browser to load
            time.sleep(4)
            print(f"🎉 Simple navigation to {target_url} completed.")
            return []
        
        initial_message = f"""
        I need you to help me navigate to the website "{website_url}" using Spotlight search on macOS. 
        
        IMPORTANT: The system now has OPTIMIZED Spotlight opening - it opens instantly and detects when ready automatically!
        
        Please follow these efficient steps:
        1. First, take a screenshot to see the current desktop
        2. Use Command+Space to open Spotlight search (this is now OPTIMIZED and opens instantly)
        3. IMMEDIATELY take a screenshot after command+space - no waiting needed
        4. Type '{spotlight_url}' directly in Spotlight (this will open the website in the default browser)
        5. IMMEDIATELY press Enter/Return to navigate to the website (no delay after typing)
        6. Wait 2 seconds for the page to load
        7. Take a final screenshot to confirm we're on the correct website
        
        KEY OPTIMIZATIONS:
        - For opening Spotlight, use the exact format: {{"action": "key", "key": "command+space"}}
        - For pressing Enter, use: {{"action": "key", "key": "return"}}
        - NO MANUAL WAITING after command+space - the system detects when Spotlight is ready
        - NO DELAY between typing and pressing return - do it immediately
        - Take screenshots immediately after actions to verify progress
        - If Spotlight is already open, clear existing content with command+a first
        - The system is now optimized for your fast MacBook!
        
        EXAMPLE sequence:
        1. {{"action": "key", "key": "command+space"}}
        2. {{"action": "screenshot"}} (immediate - no waiting!)
        3. {{"action": "type", "text": "{spotlight_url}"}}
        4. {{"action": "key", "key": "return"}} (IMMEDIATELY after typing)
        
        Start by taking a screenshot, then proceed with opening Spotlight and navigating to {spotlight_url}.
        """
        
        print(f"📋 Task: Open Spotlight and navigate to {target_url}")
        
        # Run the agent loop
        conversation = self.agent_loop(initial_message, max_iterations=12)
        
        print(f"\n🎉 Computer use agent task completed!")
        print(f"Spotlight should have opened and navigated to {target_url}.")
        
        return conversation

# Flask Routes
@app.route('/', methods=['GET'])
def home():
    """Root endpoint - welcome page"""
    return jsonify({
        "message": "🚀 Computer Use Claude Agent API",
        "status": "running",
        "description": "Flask backend for website navigation using Claude Computer Use API with natural language processing",
        "features": {
            "natural_language": "Supports natural language input like 'Navigate to Google' or 'Go to GitHub'",
            "direct_urls": "Also supports direct URLs like 'google.com' or 'https://example.com'",
            "computer_control": "Uses Claude Computer Use to control your Mac via Spotlight search"
        },
        "endpoints": {
            "health": "/health - Health check",
            "navigate": "/navigate (POST) - Navigate to website with natural language or URL",
            "extract-website": "/extract-website (POST) - Test endpoint to extract website without navigation"
        },
        "examples": [
            "Navigate to the traderjoes website",
            "Go to Google", 
            "Take me to GitHub",
            "Open YouTube",
            "github.com",
            "https://stackoverflow.com"
        ],
        "frontend": "http://localhost:3000",
        "version": "2.0.0"
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Computer Use Claude Agent",
        "version": "1.0.0"
    })

@app.route('/navigate', methods=['POST'])
def navigate_to_website():
    """API endpoint to navigate to a website using Computer Use Agent"""
    try:
        # Check if another agent is already running
        if not agent_lock.acquire(blocking=False):
            return jsonify({
                "error": "Agent is currently busy. Please try again later.",
                "status": "busy"
            }), 429
        
        try:
            # Get the user input from request
            data = request.get_json()
            if not data or 'website' not in data:
                return jsonify({
                    "error": "Missing 'website' parameter in request body",
                    "status": "error"
                }), 400
            
            user_input = data['website'].strip()
            if not user_input:
                return jsonify({
                    "error": "Website input cannot be empty",
                    "status": "error"
                }), 400
            
            print(f"📝 User input: {user_input}")
            
            # Create agent instance for website extraction
            agent = WebsiteNavigatorAgent()
            
            # First, try to extract website from natural language
            website_url = None

            # Step 1: Does the input already look like a URL or domain?
            url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            url_match = re.search(url_pattern, user_input)
            if url_match:
                # Input already resembles a URL/domain – use it directly.
                website_url = url_match.group(1)
                print(f"🔗 Direct URL detected: {website_url}")

            # Step 2: Heuristic shortcut for Trader Joe's demo if we still don't have a URL
            if not website_url:
                lower_input = user_input.lower()
                trader_terms = ["traderjoes", "trader joe", "trader joe's", "tj's", "tj "]
                if any(term in lower_input for term in trader_terms):
                    website_url = "traderjoes.com.special"
                    print("🤖 Heuristic matched Trader Joe's keywords – skipping Claude extraction.")

            # Step 3: Fallback to Claude extraction when necessary
            if not website_url:
                print("🤖 Using Claude to extract website from natural language...")
                website_url = agent.extract_website_from_text(user_input)
                
                if not website_url:
                    return jsonify({
                        "error": "Could not identify a website from your request. Please try being more specific (e.g., 'Navigate to Google' or 'go to github.com')",
                        "status": "error",
                        "suggestion": "Try phrases like: 'Go to [website name]', 'Navigate to [company] website', or directly enter a URL like 'google.com'"
                    }), 400
            
            print(f"🎯 Target website: {website_url}")
            
            # Run the navigation in a separate thread to avoid blocking
            def run_navigation():
                try:
                    conversation = agent.navigate_to_website(website_url)
                    print(f"✅ Navigation completed for {website_url}")
                except Exception as e:
                    print(f"❌ Navigation failed for {website_url}: {e}")
            
            # Start navigation in background
            navigation_thread = threading.Thread(target=run_navigation)
            navigation_thread.daemon = True
            navigation_thread.start()
            
            # Determine the actual target URL for response
            if website_url == "traderjoes.com.special":
                actual_target = "https://www.traderjoes.com/home/products/category/products-2?filters=%7B%22areNewProducts%22%3Atrue%7D"
                display_message = f"Navigation to Trader Joe's What's New page started successfully"
            else:
                actual_target = website_url
                display_message = f"Navigation to {website_url} started successfully"
            
            return jsonify({
                "message": display_message,
                "original_input": user_input,
                "extracted_website": website_url,
                "target_url": actual_target,
                "status": "started",
                "warning": "The agent is now controlling your computer. Move mouse to top-left corner to emergency stop."
            }), 200
            
        finally:
            # Release the lock after a short delay to allow the agent to start
            def release_lock():
                time.sleep(config.LOCK_RELEASE_DELAY)  # Give the agent time to start
                if agent_lock.locked():
                    agent_lock.release()
            
            release_thread = threading.Thread(target=release_lock)
            release_thread.daemon = True
            release_thread.start()
            
    except Exception as e:
        if agent_lock.locked():
            agent_lock.release()
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500

@app.route('/extract-website', methods=['POST'])
def extract_website_only():
    """Test endpoint to extract website from natural language without running the agent"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                "error": "Missing 'text' parameter in request body",
                "status": "error"
            }), 400
        
        user_input = data['text'].strip()
        if not user_input:
            return jsonify({
                "error": "Text input cannot be empty",
                "status": "error"
            }), 400
        
        print(f"🧪 Testing extraction for: {user_input}")
        
        # Create agent instance for website extraction
        agent = WebsiteNavigatorAgent()
        
        # Try to extract website from natural language
        website_url = None
        
        # Check if input is already a URL/domain (simple heuristic)
        url_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        url_match = re.search(url_pattern, user_input)
        
        if url_match:
            # Input already looks like a URL/domain
            website_url = url_match.group(1)
            extraction_method = "direct_url"
        else:
            # Try to extract website using Claude
            website_url = agent.extract_website_from_text(user_input)
            extraction_method = "claude_extraction"
        
        if not website_url:
            return jsonify({
                "error": "Could not identify a website from the input",
                "original_input": user_input,
                "extracted_website": None,
                "extraction_method": extraction_method,
                "status": "failed"
            }), 400
        
        return jsonify({
            "message": "Website extracted successfully",
            "original_input": user_input,
            "extracted_website": website_url,
            "extraction_method": extraction_method,
            "status": "success"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500

# ============================================================
# Dynamic API generation endpoints
# ============================================================

def _register_dynamic_route(slug):
    """Helper: register a Flask GET endpoint to serve cached JSON for the slug."""

    if slug in dynamic_routes:
        # Already registered
        return

    @app.route(f"/{slug}", methods=["GET"])
    def _serve_dynamic():  # type: ignore  # noqa: WPS430
        file_path = os.path.join(TEMP_DIR, f"{slug}.json")
        if not os.path.isfile(file_path):
            return jsonify({"error": "Data file not found. Try refreshing the endpoint."}), 404

        try:
            with open(file_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            return jsonify(data), 200
        except Exception as read_err:
            return jsonify({"error": f"Failed to read JSON: {read_err}"}), 500

    dynamic_routes.add(slug)

# ------------------------------------------------------------
# Automatically register any cached endpoints that exist on disk
# ------------------------------------------------------------

try:
    for _fname in os.listdir(TEMP_DIR):
        if _fname.endswith('.json'):
            _register_dynamic_route(_fname[:-5])
except FileNotFoundError:
    # TEMP_DIR might not exist yet – ignore
    pass

# ------------------------------------------------------------
# Always make sure the /whatsnew endpoint exists – even if the
# underlying JSON hasn't been scraped yet. The handler will
# still return 404 until the file appears, but the route is
# guaranteed to be present so frontend links never break.
# ------------------------------------------------------------
try:
    _register_dynamic_route('whatsnew')
except Exception:
    # If registration fails (shouldn't), continue without crashing
    pass

@app.route('/create-endpoint', methods=['POST'])
def create_endpoint():
    """Create or refresh a dynamic endpoint by driving the computer use agent."""
    if not agent_lock.acquire(blocking=False):
        return jsonify({"error": "Agent is currently busy. Please try again later.", "status": "busy"}), 429

    try:
        payload = request.get_json() or {}
        request_text = payload.get('request', '').strip()
        endpoint_slug = payload.get('endpoint', '').strip().lower()

        if not request_text or not endpoint_slug:
            return jsonify({"error": "Both 'request' and 'endpoint' are required."}), 400

        # Slug sanitisation
        # Allow users to pass values like "whatsnew.json" or "/whatsnew".
        # 1️⃣ Strip a leading slash
        if endpoint_slug.startswith('/'):
            endpoint_slug = endpoint_slug[1:]

        # 2️⃣ Remove an optional .json suffix (people often include it by mistake)
        if endpoint_slug.endswith('.json'):
            endpoint_slug = endpoint_slug[:-5]

        # 3️⃣ Keep only safe URL characters
        endpoint_slug = re.sub(r'[^a-zA-Z0-9_-]', '', endpoint_slug)

        if not endpoint_slug:
            return jsonify({"error": "Provided endpoint slug contains no valid characters."}), 400

        print(f"🆕 Create-endpoint called with slug '{endpoint_slug}' and request '{request_text}'")

        agent = WebsiteNavigatorAgent()

        # ------------------------------------------------------------
        # Phase 2: parse intent – for now, infer website via existing util
        # ------------------------------------------------------------
        website_domain = agent.extract_website_from_text(request_text) or "traderjoes.com"
        section_desc = "What's New" if 'new' in request_text.lower() else "Home"

        # ------------------------------------------------------------
        # Phase 3-4: Navigate + capture HTML (runs in background)
        # ------------------------------------------------------------
        def _scrape_and_store():
            try:
                # Build initial instruction for the agent (add site-specific hints for Trader Joe's)
                if website_domain == "traderjoes.com" and section_desc.lower().startswith("what's new"):
                    initial_msg = (
                        """You are on macOS. We need the complete HTML of Trader Joe's What's New page.
STEP-BY-STEP:
1. Press ⌘+Space to open Spotlight, type 'traderjoes.com', hit Return, wait 3 s until the homepage loads.
2. On the Trader Joe's homepage, move the mouse to the top-left navigation bar and click the link labelled 'Products' (it has a banana icon above it). Take a screenshot first if unsure.
3. Wait 2 s for the Products page to load.
4. On the Products page, find and click the link or button labelled "What's New" (approx. middle of page). Use scrolling if necessary. Take a screenshot before clicking.
5. After the What's New page is fully loaded (wait 3 s), execute the action {"action": "capture_html"} to copy the entire page HTML to clipboard.
6. Do NOT finish until the clipboard HTML is successfully captured. If clipboard is empty, retry the capture_html action."""
                    )
                else:
                    # Generic navigation prompt
                    initial_msg = f"""
                    Open Spotlight (command+space), type '{website_domain}', press return, wait 3 seconds.
                    Once the site loads, locate the '{section_desc}' section and click it.
                    Wait 3 seconds until the page fully loads, then use the action {{"action": "capture_html"}} to capture the page HTML.
                    """

                conversation = agent.agent_loop(initial_msg, max_iterations=15)

                # Try to extract HTML from conversation tool results
                html_content = None
                for msg in conversation:
                    content = msg.get('content') if isinstance(msg, dict) else None
                    if isinstance(content, list):
                        for tr in content:
                            if not isinstance(tr, dict):
                                continue      # ignore BetaTextBlock, etc.
                            if tr.get('type') == "tool_result":
                                captured = tr.get('content', '') or ''
                                if isinstance(captured, str) and '<html' in captured.lower():
                                    html_content = captured
                if not html_content:
                    print("❌ Failed to retrieve HTML from agent conversation")
                    return

                # ----------------------------------------------------
                # Phase 5: Transform HTML → JSON via Claude
                # ----------------------------------------------------
                extractor_system = (
                    "You are an API data extractor. Convert the Trader Joe's 'What's New' page HTML into a JSON array. "
                    "Each object must contain: product_name, price, product_url, image_url. Output ONLY JSON."
                )

                extraction_resp = agent.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    system=extractor_system,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": html_content[:100000]}]  # Truncate to fit token limits
                )

                json_str = extraction_resp.content[0].text.strip()
                try:
                    data_json = json.loads(json_str)
                except Exception as jerr:
                    print(f"❌ JSON parse fail: {jerr}")
                    return

                # ----------------------------------------------------
                # Phase 6: Persist & register
                # ----------------------------------------------------
                file_path = os.path.join(TEMP_DIR, f"{endpoint_slug}.json")
                with open(file_path, 'w', encoding='utf-8') as fp:
                    json.dump(data_json, fp, ensure_ascii=False, indent=2)

                _register_dynamic_route(endpoint_slug)
                print(f"✅ Endpoint '/{endpoint_slug}' created with {len(data_json)} records")
            finally:
                if agent_lock.locked():
                    agent_lock.release()

        threading.Thread(target=_scrape_and_store, daemon=True).start()

        return jsonify({
            "message": f"Endpoint creation for '/{endpoint_slug}' started.",
            "status": "started"
        }), 202

    finally:
        # ensure lock released for early exits
        if agent_lock.locked():
            agent_lock.release()

@app.route('/refresh-endpoint', methods=['POST'])
def refresh_endpoint():
    """Trigger re-scrape for an existing endpoint."""
    payload = request.get_json() or {}
    slug = payload.get('endpoint', '').strip().lower()
    if not slug:
        return jsonify({"error": "'endpoint' field is required"}), 400

    # Reuse create-endpoint logic by calling internally
    return create_endpoint()

@app.route('/generate-docs', methods=['POST', 'GET'])
def generate_documentation():
    """Generate API documentation for a given request using Claude with streaming"""
    try:
        # Handle both POST (JSON) and GET (query params) for EventSource compatibility
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'request' not in data:
                return jsonify({
                    "error": "Missing 'request' parameter in request body",
                    "status": "error"
                }), 400
            user_request = data['request'].strip()
            endpoint_slug = data.get('endpoint', '').strip().lower()
        else:  # GET request for EventSource
            user_request = request.args.get('request', '').strip()
            endpoint_slug = request.args.get('endpoint', '').strip().lower()
            if not user_request:
                return "data: " + json.dumps({
                    "error": "Missing 'request' parameter in query params",
                    "status": "error"
                }) + "\n\n"
        
        if not user_request:
            if request.method == 'POST':
                return jsonify({
                    "error": "Request input cannot be empty",
                    "status": "error"
                }), 400
            else:
                return "data: " + json.dumps({
                    "error": "Request input cannot be empty",
                    "status": "error"
                }) + "\n\n"
        
        print(f"📋 Generating documentation for request: {user_request}")
        
        # Create agent instance for documentation generation
        agent = WebsiteNavigatorAgent()
        
        # Extract website information for context
        website_url = agent.extract_website_from_text(user_request)
        
        # Special handling for Trader Joe's endpoint
        if website_url == "traderjoes.com.special":
            endpoint_slug = "whatsnew"
        
        # Prepare documentation prompt
        doc_generation_prompt = f"""You are an expert technical writer creating API documentation. Based on the user's request: "{user_request}", generate comprehensive, beautiful API documentation.

CONTEXT:
- The user wants to create an API endpoint for: {user_request}
- The extracted website/domain is: {website_url or 'various websites'}
- This API uses Computer Use to scrape websites and convert them to JSON endpoints
- The endpoint will be available at: /{endpoint_slug or 'generated-endpoint'}

SPECIAL CASE - If this is about Trader Joe's "What's New" products:
- The API endpoint will return an array of new products from traderjoes.com
- Each product has: product_name, price, product_url, image_url
- The endpoint navigates to: https://www.traderjoes.com/home/products/category/products-2?filters=%7B%22areNewProducts%22%3Atrue%7D
- The endpoint URL is: /whatsnew

Generate documentation that includes:

## API Overview
Brief description of what this API does

## Base URL
```
http://localhost:5000
```

## Authentication
No authentication required

## Endpoints

### GET /{endpoint_slug or 'your-endpoint'}
Description of what this endpoint returns

**Response Format:**
```json
[
  {{
    // Example JSON structure based on the website type
    // For Trader Joe's: product_name, price, product_url, image_url
    // For other sites: appropriate fields
  }}
]
```

**Example Response:**
```json
// Realistic example data for this specific endpoint
```

**Response Codes:**
- 200: Success
- 404: Endpoint not found
- 500: Server error

## Usage Examples

### cURL
```bash
curl -X GET "http://localhost:5000/{endpoint_slug or 'your-endpoint'}"
```

### JavaScript (fetch)
```javascript
// Example showing how to use this API in JavaScript
```

### Python (requests)
```python
# Example showing how to use this API in Python
```

## Data Freshness
Explain how often the data is updated and how to refresh it

## Rate Limiting
Information about any rate limits

## Error Handling
Common error responses and how to handle them

## Support
How to get help or report issues

Make the documentation professional, clear, and engaging. Use proper markdown formatting. Be specific about the data structure this particular endpoint will return based on the website type."""
        
        try:
            # Generate documentation using Claude Haiku (faster model) with streaming
            def generate():
                yield "data: " + json.dumps({"type": "start", "message": "Starting documentation generation..."}) + "\n\n"
                
                response = agent.client.messages.create(
                    model="claude-3-5-haiku-20241022",  # Using valid Claude 3.5 Haiku model
                    system="You are a technical documentation expert. Create clear, comprehensive, and professional API documentation in markdown format.",
                    max_tokens=2000,
                    messages=[{
                        "role": "user", 
                        "content": doc_generation_prompt
                    }],
                    stream=True  # Enable streaming
                )
                
                documentation_parts = []
                for chunk in response:
                    if chunk.type == "content_block_delta":
                        text_chunk = chunk.delta.text
                        documentation_parts.append(text_chunk)
                        yield "data: " + json.dumps({
                            "type": "chunk", 
                            "text": text_chunk,
                            "partial_content": "".join(documentation_parts)
                        }) + "\n\n"
                
                final_documentation = "".join(documentation_parts)
                yield "data: " + json.dumps({
                    "type": "complete",
                    "documentation": final_documentation,
                    "original_request": user_request,
                    "endpoint_slug": endpoint_slug,
                    "website_url": website_url,
                    "status": "success"
                }) + "\n\n"
            
            if request.method == 'GET':
                # Return Server-Sent Events stream
                return Response(
                    generate(),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'Connection': 'keep-alive',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Cache-Control'
                    }
                )
            else:
                # Return as regular JSON for POST requests (fallback)
                documentation_parts = []
                response = agent.client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    system="You are a technical documentation expert. Create clear, comprehensive, and professional API documentation in markdown format.",
                    max_tokens=2000,
                    messages=[{
                        "role": "user", 
                        "content": doc_generation_prompt
                    }]
                )
                final_documentation = response.content[0].text.strip()
                
                return jsonify({
                    "message": "Documentation generated successfully",
                    "documentation": final_documentation,
                    "original_request": user_request,
                    "endpoint_slug": endpoint_slug,
                    "website_url": website_url,
                    "status": "success"
                }), 200
            
        except Exception as e:
            print(f"❌ Error generating documentation: {e}")
            if request.method == 'GET':
                return "data: " + json.dumps({
                    "error": f"Failed to generate documentation: {str(e)}",
                    "status": "error"
                }) + "\n\n"
            else:
                return jsonify({
                    "error": f"Failed to generate documentation: {str(e)}",
                    "status": "error"
                }), 500
            
    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500

# Command-line interface (preserved for backward compatibility)
def main():
    """Main function to run the computer use agent from command line"""
    print("=== Computer Use Claude Agent - Website Navigator ===")
    print("This agent will use Spotlight to navigate to any website you specify!")
    print("Just enter a website name/URL and the agent will handle the rest.")
    print("\n🔐 PERMISSIONS REQUIRED:")
    print("   - Screen Recording (for screenshots)")
    print("   - Accessibility (for mouse/keyboard control)")
    print("   Go to System Preferences > Security & Privacy > Privacy")
    print("\n⚠️  SAFETY:")
    print("   - The agent will control your mouse and keyboard")
    print("   - Move mouse to top-left corner for emergency stop")
    print("   - Make sure you're ready before proceeding")
    
    # Get website input from user
    print("\n" + "="*50)
    website_input = input("Enter the website you want to visit (e.g., 'google', 'github.com', 'https://example.com'): ").strip()
    
    if not website_input:
        print("❌ No website entered. Exiting.")
        return
    
    print(f"\n📍 Target website: {website_input}")
    user_confirmation = input("Press Enter to start the agent, or 'q' to quit: ")
    
    if user_confirmation.lower() == 'q':
        print("Agent cancelled by user.")
        return
    
    # Create and run the agent
    agent = WebsiteNavigatorAgent()
    
    try:
        conversation = agent.navigate_to_website(website_input)
        
        print("\n" + "="*50)
        print("📊 SUMMARY")
        print(f"Target website: {website_input}")
        print(f"Total conversation turns: {len(conversation)}")
        print("Agent has completed the requested task!")
        
    except pyautogui.FailSafeException:
        print("\n🛑 EMERGENCY STOP: Mouse moved to corner - agent halted for safety")
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        print("Make sure your API key is valid and you have the required permissions for computer use.")
        print("Also ensure you have granted screen recording and accessibility permissions.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run as Flask web server
        print("🚀 Starting Computer Use Claude Agent Web Server...")
        print("🌐 Server will be available at: http://localhost:5000")
        print("📋 API Endpoints:")
        print("   GET  /health   - Health check")
        print("   POST /navigate - Navigate to website")
        print("\n⚠️  IMPORTANT: Make sure you have granted the required permissions:")
        print("   - Screen Recording (for screenshots)")
        print("   - Accessibility (for mouse/keyboard control)")
        print("   - Go to System Preferences > Security & Privacy > Privacy")
        
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # Run as command-line tool
        main()
