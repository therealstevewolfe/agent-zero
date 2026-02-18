### OpenClaw Integration
You have access to the OpenClaw system via the `openclaw_tool`. 
This allows you to send messages, control the browser, manage nodes, and more.
This is a powerful tool. Use it carefully.

**Usage:**
- `command`: The OpenClaw command arguments (e.g., `message send --target me --message "Hello"`)

**Examples:**
- Send a message:
{
    "tool_name": "openclaw_tool",
    "tool_args": {
        "command": "message send --target +123456789 --message 'Hello world'"
    }
}
- Open a URL in the browser:
{
    "tool_name": "openclaw_tool",
    "tool_args": {
        "command": "browser open --url https://example.com"
    }
}
- Check node status:
{
    "tool_name": "openclaw_tool",
    "tool_args": {
        "command": "nodes status"
    }
}
