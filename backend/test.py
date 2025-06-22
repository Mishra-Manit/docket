#!/usr/bin/env python3
"""
Computer Use Claude Agent - Generic Website Navigator
This script uses Anthropic's Computer Use feature to control the computer,
specifically to open Spotlight and navigate to any user-specified website.
"""

import time
import base64
from io import BytesIO
from anthropic import Anthropic
from PIL import ImageGrab
import pyautogui
import config
from spotlight_optimizer import spotlight_optimizer

# Configure pyautogui
pyautogui.FAILSAFE = True  # Keep failsafe enabled for safety
pyautogui.PAUSE = config.PYAUTOGUI_PAUSE  # Pause between actions for better reliability

class WebsiteNavigatorAgent:
    def __init__(self):
        self.client = Anthropic(
            api_key=config.ANTHROPIC_API_KEY,
            default_headers={
                "anthropic-beta": "computer-use-2024-10-22"
            }
        )
        self.model = "claude-3-5-sonnet-20241022"  # Computer use enabled model
        
    def take_screenshot(self):
        """Take a screenshot and return it as base64 encoded string"""
        screenshot = ImageGrab.grab()
        buffer = BytesIO()
        screenshot.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64
    
    def execute_computer_tool(self, tool_input):
        """Execute a computer tool action and return the result"""
        action = tool_input.get('action')
        result = ""
        
        try:
            if action == 'screenshot':
                # Take screenshot
                screenshot_b64 = self.take_screenshot()
                result = f"Screenshot taken successfully. Image data: {screenshot_b64[:100]}..."
                
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
                # Press a key or key combination
                key_value = (
                    tool_input.get('key')
                    or tool_input.get('keys')
                    or tool_input.get('text')
                )
                
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
                
            else:
                result = f"Unknown action: {action}"
                
        except Exception as e:
            result = f"Error executing {action}: {str(e)}"
            print(f"❌ Exception in execute_computer_tool: {e}")
            
        return result
    
    def agent_loop(self, initial_message, max_iterations=10):
        """Run the agent loop with tool use"""
        system_prompt = (
            "You are controlling a macOS machine via the computer tool. "
            "You have access to these actions: screenshot, left_click, type, key, mouse_move. "
            "For keyboard shortcuts on macOS:\n"
            "- Use 'command+space' to open Spotlight search\n"
            "- Use 'return' to press Enter\n"
            "- Always include the exact key combination in the 'key' field\n"
            "When using the 'key' action, you MUST populate the 'key' field with the exact key combination (e.g., 'command+space', 'return'). "
            "NEVER leave the key field empty or use other field names.\n"
            "Be methodical and take screenshots to see the current state before taking actions."
        )

        messages = [{"role": "user", "content": initial_message}]
        
        for iteration in range(max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            try:
                # Call Claude with current conversation
                response = self.client.messages.create(
                    model=self.model,
                    system=system_prompt,
                    max_tokens=1024,
                    messages=messages,
                    tools=[
                        {
                            "type": "computer_20241022",
                            "name": "computer",
                            "display_width_px": config.DISPLAY_WIDTH,
                            "display_height_px": config.DISPLAY_HEIGHT
                        }
                    ]
                )
                
                # Add Claude's response to conversation
                messages.append({"role": "assistant", "content": response.content})
                
                # Check if Claude used any tools
                tool_results = []
                tool_used = False
                
                for content_block in response.content:
                    if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                        tool_used = True
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id
                        
                        print(f"🔧 Tool: {tool_name}")
                        print(f"📝 Action: {tool_input.get('action', 'unknown')}")
                        print(f"🔸 Raw tool input: {tool_input}")
                        if 'coordinate' in tool_input:
                            print(f"📍 Coordinates: {tool_input['coordinate']}")
                        if 'key' in tool_input:
                            print(f"⌨️  Key: {tool_input['key']}")
                        
                        # Execute the tool
                        if tool_name == "computer":
                            result = self.execute_computer_tool(tool_input)
                        else:
                            result = f"Unknown tool: {tool_name}"
                        
                        print(f"✅ Result: {result}")
                        
                        # Add tool result to conversation
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": result
                        })
                    
                    elif hasattr(content_block, 'type') and content_block.type == 'text':
                        print(f"💬 Claude: {content_block.text}")
                
                # If tools were used, add results and continue
                if tool_results:
                    messages.append({"role": "user", "content": tool_results})
                    time.sleep(config.BETWEEN_ITERATIONS_SLEEP)  # Optimized pause for better reliability
                else:
                    # No tools used, conversation is complete
                    print("🏁 Task completed - no more tools requested")
                    break
                    
            except Exception as e:
                print(f"❌ Error in iteration {iteration + 1}: {e}")
                break
                
        return messages
    
    def navigate_to_website(self, website_url):
        """Open Spotlight search and navigate to any specified website"""
        print(f"🚀 Starting computer use agent to navigate to: {website_url}")
        print("⚠️  IMPORTANT: The agent will now control your computer!")
        print("   Move your mouse to the top-left corner to emergency stop")
        
        time.sleep(3)  # Give user time to read warning
        
        # Clean up the website URL if needed
        if not website_url.startswith(('http://', 'https://')):
            # Add .com if it's just a domain name without extension
            if '.' not in website_url:
                website_url = f"{website_url}.com"
        
        initial_message = f"""
        I need you to help me navigate to the website "{website_url}" using Spotlight search on macOS. 
        
        Please follow these streamlined steps:
        1. First, take a screenshot to see the current desktop
        2. Use Command+Space to open Spotlight search (this is CRITICAL - make sure Spotlight opens)
        3. Type '{website_url}' directly in Spotlight (this will open the website in the default browser)
        4. Press Enter to navigate to the website
        5. Wait 3 seconds for the page to load
        6. Take a final screenshot to confirm we're on the correct website
        
        IMPORTANT INSTRUCTIONS:
        - For opening Spotlight, use the exact format: {{"action": "key", "key": "command+space"}}
        - For pressing Enter, use: {{"action": "key", "key": "return"}}
        - Always take screenshots between major steps to verify progress
        - If Spotlight doesn't appear after the first attempt, try again
        - Be patient and methodical - take time between actions
        
        EXAMPLE of correct Spotlight opening:
        {{"action": "key", "key": "command+space"}}
        
        Start by taking a screenshot, then proceed with opening Spotlight and navigating to {website_url}.
        """
        
        print(f"📋 Task: Open Spotlight and navigate to {website_url}")
        
        # Run the agent loop
        conversation = self.agent_loop(initial_message, max_iterations=12)
        
        print(f"\n🎉 Computer use agent task completed!")
        print(f"Spotlight should have opened and navigated to {website_url}.")
        
        return conversation

def main():
    """Main function to run the computer use agent"""
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
    main()
