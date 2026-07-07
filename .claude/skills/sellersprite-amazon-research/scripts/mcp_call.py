#!/usr/bin/env python3
"""Helper to call sellersprite MCP tools - fixed encoding"""
import sys, json, urllib.request, urllib.error, os

SECRET_KEY = ""
URL = "https://mcp.sellersprite.com/mcp"

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def call_tool(name: str, arguments: dict):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    }).encode('utf-8')
    req = urllib.request.Request(URL, data=payload,
        headers={"Content-Type": "application/json", "secret-key": SECRET_KEY,
                 "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)
            text = data['result']['content'][0]['text']
            return json.loads(text)
    except Exception as e:
        return {"error": str(e)}

if __name__ == '__main__':
    name = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    result = call_tool(name, args)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
