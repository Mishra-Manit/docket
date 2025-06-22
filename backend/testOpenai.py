"""
Simple Claude computer-use demo (macOS).
It tells Claude to open Spotlight and show the latest
Golden State Warriors game.

Requirements:
  pip install anthropic pyautogui pillow
  export ANTHROPIC_API_KEY=...
"""

import os, time
import anthropic
import pyautogui
from PIL import ImageGrab

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
TOOL_VER  = "20250124"               # latest tool
BETA_FLAG = "computer-use-2025-01-24"
MODEL     = "claude-opus-4-20250514"   # switched to Claude Opus 4

# --- very small tool-action executor ---------------------------------
def handle(action):
    match action["action"]:
        case "screenshot":
            path = "/tmp/ss.png"
            ImageGrab.grab().save(path)
            return {"file": path}
        case "left_click":
            x, y = action["coordinate"]
            pyautogui.moveTo(x, y, duration=0.15); pyautogui.click()
            return {"ok": True}
        case "type":
            pyautogui.write(action["text"], interval=0.05)
            return {"ok": True}
        case "hotkey":
            pyautogui.hotkey(*action["keys"])
            return {"ok": True}
        case "delay":
            time.sleep(action.get("seconds", 1)); return {"ok": True}
        case _:
            return {"error": f"unhandled {action['action']}"}

# ---------------------------------------------------------------------
def agent_loop(max_iters=6):
    msgs = [{"role":"user",
             "content":"Open Spotlight (⌘+Space), search 'Warriors latest game', "
                       "press ⏎, then open the top link."}]
    tools = [{"type":f"computer_{TOOL_VER}",
              "name":"computer",
              "display_width_px":1440,
              "display_height_px":900}]
    for _ in range(max_iters):
        resp = client.beta.messages.create(
                    model=MODEL,
                    max_tokens=1024,
                    messages=msgs,
                    tools=tools,
                    betas=[BETA_FLAG])
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                tool_results.append({"type":"tool_result",
                                     "tool_use_id":block.id,
                                     "content":handle(block.input)})
        if not tool_results:             # Claude finished
            print(resp.text)
            break
        msgs += [{"role":"assistant","content":resp.content},
                 {"role":"user","content":tool_results}]

if __name__ == "__main__":
    agent_loop()
