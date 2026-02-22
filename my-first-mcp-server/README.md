# Leave Management MCP Server 🏢

An **HR Leave Management Agent** built with the [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) SDK. Enables any MCP client (Claude Desktop, chatbot, etc.) to manage employee leaves conversationally.

---

## 🚀 Quick Start

```bash
# Install dependencies
uv add "mcp[cli]"

# Run with MCP Inspector (browser UI for testing)
uv run mcp dev main.py

# Run in production mode (stdio transport)
uv run mcp run main.py
```

---

## 📁 Project Structure

```
my-first-mcp-server/
├── main.py          # MCP server — tools, resources, prompts
├── db.py            # In-memory employee & leave database
├── pyproject.toml   # Project config & dependencies
└── README.md
```

---

## 👥 Pre-seeded Employees

| ID   | Name            | Department  | Role                  |
|------|-----------------|-------------|----------------------|
| E001 | Alice Johnson   | Engineering | Software Engineer     |
| E002 | Bob Smith       | Marketing   | Marketing Analyst     |
| E003 | Carol Williams  | Engineering | Engineering Manager   |
| E004 | David Brown     | HR          | HR Manager            |
| E005 | Eva Martinez    | Finance     | Financial Analyst     |

---

## 🛠️ Tools

| Tool | Description |
|---|---|
| `get_employee_info` | Get employee details by ID or name |
| `get_leave_balance` | View remaining leave days by type |
| `apply_leave` | Submit a new leave request |
| `get_leave_status` | Check status of a leave request |
| `list_pending_leaves` | List all pending leaves (manager view) |
| `list_employee_leaves` | List all leaves for a specific employee |
| `approve_leave` | Approve a pending leave request |
| `reject_leave` | Reject a pending leave with a reason |
| `cancel_leave` | Cancel a pending or approved leave |

---

## 📦 Resources

| URI | Description |
|---|---|
| `employees://list` | Full employee directory (JSON) |
| `leaves://all` | All leave records (JSON) |
| `leaves://pending` | Pending leave requests (JSON) |

---

## 💬 Prompts

| Prompt | Description |
|---|---|
| `leave_policy` | Company leave policy document |
| `apply_leave_guide` | Step-by-step guide for applying leave |

---

## 📋 Leave Types & Entitlements

| Type | Days/Year | Notes |
|---|---|---|
| Casual | 10 | Personal errands |
| Sick | 12 | Medical certificate if > 2 days |
| Annual | 20 | 14 days advance notice required |
| Maternity | 90 | Female employees only |
| Paternity | 5 | Male employees only |

---

## 💡 Example Conversations

```
User: "What is Alice's leave balance?"
Agent: [calls get_employee_info + get_leave_balance for E001]

User: "Apply sick leave for E001 from 2026-03-10 to 2026-03-11. Reason: Fever."
Agent: [calls apply_leave → returns Leave ID L001]

User: "Show me all pending leave requests."
Agent: [calls list_pending_leaves]

User: "Approve leave L001."
Agent: [calls approve_leave → deducts balance]
```

---

## 🔗 Claude Desktop Integration

Add to your Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "leave-management": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/my-first-mcp-server",
        "mcp",
        "run",
        "main.py"
      ]
    }
  }
}
```
