"""
main.py — Leave Management MCP Server

An HR Leave Management Agent backend built with the MCP (Model Context Protocol) SDK.
Exposes tools, resources, and prompts so any MCP client (Claude Desktop, chatbot, etc.)
can manage employee leaves conversationally.

Run with:
    uv run mcp dev main.py          # opens MCP Inspector in browser
    uv run mcp run main.py          # run in production mode
"""

import json
from mcp.server.fastmcp import FastMCP
import db

# ─────────────────────────────────────────────
#  SERVER SETUP
# ─────────────────────────────────────────────

mcp = FastMCP(
    name="Leave Management System",
    instructions=(
        "You are an HR Leave Management Agent. "
        "You help employees apply for leaves, check balances, and help managers "
        "approve or reject leave requests. Always be polite and professional. "
        "Use the available tools to fetch real data before giving answers."
    ),
)

# ─────────────────────────────────────────────
#  TOOLS
# ─────────────────────────────────────────────


@mcp.tool()
def get_employee_info(employee_id: str = "", name: str = "") -> str:
    """
    Fetch information about an employee by their employee ID or name.

    Args:
        employee_id: The employee's ID (e.g., 'E001'). Preferred over name.
        name: Partial or full name of the employee (case-insensitive).

    Returns:
        Employee details including department, role, email, and manager ID.
    """
    if not employee_id and not name:
        return "❌ Please provide either an employee_id or a name to search."

    emp = db.find_employee(employee_id=employee_id or None, name=name or None)
    if not emp:
        return f"❌ No employee found for id='{employee_id}' name='{name}'."

    return json.dumps(emp, indent=2)


@mcp.tool()
def get_leave_balance(employee_id: str) -> str:
    """
    Get the remaining leave balance for an employee, broken down by leave type.

    Args:
        employee_id: The employee's ID (e.g., 'E001').

    Returns:
        A breakdown of available leave days per leave type (casual, sick, annual, etc.).
    """
    emp = db.find_employee(employee_id=employee_id)
    if not emp:
        return f"❌ Employee '{employee_id}' not found."

    balance = emp["leave_balance"]
    lines = [f"📊 Leave balance for {emp['name']} ({emp['id']}):"]
    for leave_type, days in balance.items():
        emoji = {"casual": "🌴", "sick": "🤒", "annual": "✈️", "maternity": "👶", "paternity": "👨‍👦"}.get(leave_type, "📅")
        lines.append(f"  {emoji} {leave_type.capitalize():<12}: {days} day(s)")
    return "\n".join(lines)


@mcp.tool()
def apply_leave(
    employee_id: str,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
) -> str:
    """
    Submit a new leave request on behalf of an employee.

    Args:
        employee_id: The employee's ID (e.g., 'E001').
        leave_type: Type of leave — one of: casual, sick, annual, maternity, paternity.
        start_date: Start date in YYYY-MM-DD format (e.g., '2026-03-10').
        end_date: End date in YYYY-MM-DD format (e.g., '2026-03-12').
        reason: Reason for taking the leave.

    Returns:
        Confirmation of the submitted leave request with the assigned leave ID.
    """
    try:
        record = db.create_leave(employee_id, leave_type, start_date, end_date, reason)
    except ValueError as e:
        return f"❌ Cannot apply leave: {e}"

    return (
        f"✅ Leave request submitted successfully!\n"
        f"   Leave ID   : {record['leave_id']}\n"
        f"   Employee   : {record['employee_name']} ({record['employee_id']})\n"
        f"   Type       : {record['leave_type'].capitalize()}\n"
        f"   Period     : {record['start_date']} → {record['end_date']} ({record['days']} day(s))\n"
        f"   Reason     : {record['reason']}\n"
        f"   Status     : {record['status'].upper()}\n"
        f"   Submitted  : {record['created_at']}"
    )


@mcp.tool()
def get_leave_status(leave_id: str) -> str:
    """
    Check the current status and details of a specific leave request.

    Args:
        leave_id: The leave request ID (e.g., 'L001').

    Returns:
        Full details and current status of the leave request.
    """
    record = db.get_leave(leave_id)
    if not record:
        return f"❌ Leave request '{leave_id}' not found."

    status_emoji = {
        "pending": "⏳",
        "approved": "✅",
        "rejected": "❌",
        "cancelled": "🚫",
    }.get(record["status"], "📋")

    lines = [
        f"{status_emoji} Leave Request — {record['leave_id']}",
        f"   Employee   : {record['employee_name']} ({record['employee_id']})",
        f"   Type       : {record['leave_type'].capitalize()}",
        f"   Period     : {record['start_date']} → {record['end_date']} ({record['days']} day(s))",
        f"   Reason     : {record['reason']}",
        f"   Status     : {record['status'].upper()}",
        f"   Submitted  : {record['created_at']}",
        f"   Updated    : {record['updated_at']}",
    ]
    if record["rejection_reason"]:
        lines.append(f"   Rejection  : {record['rejection_reason']}")

    return "\n".join(lines)


@mcp.tool()
def list_pending_leaves() -> str:
    """
    List all currently pending leave requests across the organization.
    Intended for managers/HR to get an overview of leaves awaiting action.

    Returns:
        A formatted list of all pending leave requests, or a message if none exist.
    """
    pending = db.get_pending_leaves()
    if not pending:
        return "✅ No pending leave requests at the moment."

    lines = [f"⏳ Pending Leave Requests ({len(pending)} total):\n"]
    for r in pending:
        lines.append(
            f"  • [{r['leave_id']}] {r['employee_name']} ({r['employee_id']}) — "
            f"{r['leave_type'].capitalize()} | {r['start_date']} → {r['end_date']} "
            f"({r['days']} day(s)) | Reason: {r['reason']}"
        )
    return "\n".join(lines)


@mcp.tool()
def list_employee_leaves(employee_id: str) -> str:
    """
    List all leave requests (of any status) submitted by a specific employee.

    Args:
        employee_id: The employee's ID (e.g., 'E001').

    Returns:
        All leave records for the employee, sorted by submission date.
    """
    emp = db.find_employee(employee_id=employee_id)
    if not emp:
        return f"❌ Employee '{employee_id}' not found."

    leaves = db.get_employee_leaves(employee_id)
    if not leaves:
        return f"📋 {emp['name']} has no leave requests on record."

    status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌", "cancelled": "🚫"}
    lines = [f"📋 Leave History for {emp['name']} ({emp['id']}) — {len(leaves)} record(s):\n"]
    for r in leaves:
        emoji = status_emoji.get(r["status"], "📅")
        lines.append(
            f"  {emoji} [{r['leave_id']}] {r['leave_type'].capitalize()} | "
            f"{r['start_date']} → {r['end_date']} ({r['days']} day(s)) | "
            f"Status: {r['status'].upper()}"
        )
    return "\n".join(lines)


@mcp.tool()
def approve_leave(leave_id: str) -> str:
    """
    Approve a pending leave request. This deducts the days from the employee's balance.

    Args:
        leave_id: The leave request ID to approve (e.g., 'L001').

    Returns:
        Confirmation of approval and updated leave details.
    """
    try:
        record = db.approve_leave_record(leave_id)
    except ValueError as e:
        return f"❌ Cannot approve: {e}"

    emp = db.EMPLOYEES[record["employee_id"]]
    remaining = emp["leave_balance"][record["leave_type"]]
    return (
        f"✅ Leave request '{record['leave_id']}' APPROVED!\n"
        f"   Employee   : {record['employee_name']} ({record['employee_id']})\n"
        f"   Type       : {record['leave_type'].capitalize()}\n"
        f"   Period     : {record['start_date']} → {record['end_date']} ({record['days']} day(s))\n"
        f"   Remaining {record['leave_type'].capitalize()} Balance: {remaining} day(s)"
    )


@mcp.tool()
def reject_leave(leave_id: str, rejection_reason: str) -> str:
    """
    Reject a pending leave request with a reason.

    Args:
        leave_id: The leave request ID to reject (e.g., 'L001').
        rejection_reason: The reason for rejecting the leave request.

    Returns:
        Confirmation of rejection.
    """
    try:
        record = db.reject_leave_record(leave_id, rejection_reason)
    except ValueError as e:
        return f"❌ Cannot reject: {e}"

    return (
        f"❌ Leave request '{record['leave_id']}' REJECTED.\n"
        f"   Employee   : {record['employee_name']} ({record['employee_id']})\n"
        f"   Type       : {record['leave_type'].capitalize()}\n"
        f"   Period     : {record['start_date']} → {record['end_date']} ({record['days']} day(s))\n"
        f"   Reason for Rejection: {record['rejection_reason']}"
    )


@mcp.tool()
def cancel_leave(leave_id: str) -> str:
    """
    Cancel a leave request. Can be used on both pending and approved leaves.
    If the leave was already approved, the balance is restored.

    Args:
        leave_id: The leave request ID to cancel (e.g., 'L001').

    Returns:
        Confirmation of cancellation and whether the balance was restored.
    """
    record = db.get_leave(leave_id)
    if not record:
        return f"❌ Leave request '{leave_id}' not found."

    was_approved = record["status"] == "approved"
    try:
        record = db.cancel_leave_record(leave_id)
    except ValueError as e:
        return f"❌ Cannot cancel: {e}"

    msg = (
        f"🚫 Leave request '{record['leave_id']}' CANCELLED.\n"
        f"   Employee : {record['employee_name']} ({record['employee_id']})\n"
        f"   Period   : {record['start_date']} → {record['end_date']} ({record['days']} day(s))\n"
    )
    if was_approved:
        emp = db.EMPLOYEES[record["employee_id"]]
        restored = emp["leave_balance"][record["leave_type"]]
        msg += f"   ✅ {record['days']} day(s) restored to {record['leave_type'].capitalize()} balance. New balance: {restored} day(s)"
    return msg


# ─────────────────────────────────────────────
#  RESOURCES
# ─────────────────────────────────────────────


@mcp.resource("employees://list")
def resource_employees_list() -> str:
    """Returns the full employee directory as JSON."""
    employees = db.get_all_employees()
    summary = []
    for emp in employees:
        summary.append({
            "id": emp["id"],
            "name": emp["name"],
            "department": emp["department"],
            "role": emp["role"],
            "email": emp["email"],
            "manager_id": emp["manager_id"],
        })
    return json.dumps(summary, indent=2)


@mcp.resource("leaves://all")
def resource_all_leaves() -> str:
    """Returns all leave requests across the organization as JSON."""
    return json.dumps(db.get_all_leaves(), indent=2)


@mcp.resource("leaves://pending")
def resource_pending_leaves() -> str:
    """Returns only pending leave requests as JSON."""
    return json.dumps(db.get_pending_leaves(), indent=2)


# ─────────────────────────────────────────────
#  PROMPTS
# ─────────────────────────────────────────────


@mcp.prompt()
def leave_policy() -> str:
    """Returns the company leave policy document."""
    return """
# 📋 Company Leave Policy

## Leave Types & Entitlements

| Leave Type   | Days/Year | Notes                                      |
|-------------|----------|--------------------------------------------|
| Casual       | 10       | For personal errands, short personal needs |
| Sick         | 12       | Requires medical certificate if > 2 days  |
| Annual       | 20       | Must be planned 2 weeks in advance         |
| Maternity    | 90       | For female employees, paid leave           |
| Paternity    | 5        | For male employees upon birth of child     |

## Rules & Guidelines

1. **Application**: All leave requests must be submitted through the Leave Management System before the leave begins.
2. **Approval**: Leave requests must be approved by your direct manager.
3. **Advance Notice**: Annual leaves require at least **14 days** advance notice.
4. **Sick Leave**: If sick leave exceeds **2 consecutive days**, a valid medical certificate must be submitted.
5. **Balance**: Unused casual and sick leaves do **not** carry over to the next year.
6. **Annual Leave**: Up to **5 days** of unused annual leave can be carried over to the next year.
7. **Cancellation**: Employees may cancel an approved leave at least **24 hours** before the leave start date.
8. **Rejection**: Management reserves the right to reject leave during critical project deadlines.

## Contact

For any leave-related queries, contact HR at: hr@company.com
"""


@mcp.prompt()
def apply_leave_guide() -> str:
    """Returns a step-by-step guide on how to apply for leave."""
    return """
# 🗓️ How to Apply for Leave

Follow these steps to submit a leave request through the Leave Management Agent:

## Step 1: Know Your Employee ID
Your employee ID can be found on your ID card or payslip. Example: `E001`

## Step 2: Check Your Leave Balance
Before applying, check your remaining leave balance:
> "What is my leave balance for employee ID E001?"

## Step 3: Choose Leave Type
Select the appropriate leave type:
- **casual** — Short personal needs
- **sick** — Health-related absences
- **annual** — Pre-planned vacations (14 days advance notice needed)
- **maternity** — For new mothers
- **paternity** — For new fathers

## Step 4: Submit the Request
Provide the following to submit:
- Your Employee ID
- Leave type
- Start date (YYYY-MM-DD format)
- End date (YYYY-MM-DD format)
- Reason for leave

Example:
> "Apply casual leave for E001 from 2026-03-10 to 2026-03-12. Reason: Family function."

## Step 5: Track Your Request
After submission, you'll receive a **Leave ID** (e.g., `L001`).
Use it to track status:
> "What is the status of leave L001?"

## Step 6: Await Approval
Your manager will review and approve or reject the request.
You'll receive a notification once the decision is made.
"""


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
