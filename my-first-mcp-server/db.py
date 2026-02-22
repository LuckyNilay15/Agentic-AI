"""
db.py — In-memory database for the Leave Management System.
Stores employee records and leave requests. Pre-seeded with sample data.
"""

from datetime import datetime, date
from typing import Optional

# ─────────────────────────────────────────────
#  EMPLOYEE STORE
# ─────────────────────────────────────────────

EMPLOYEES: dict[str, dict] = {
    "E001": {
        "id": "E001",
        "name": "Alice Johnson",
        "department": "Engineering",
        "role": "Software Engineer",
        "email": "alice.johnson@company.com",
        "manager_id": "E003",
        "leave_balance": {
            "casual": 10,
            "sick": 12,
            "annual": 20,
            "maternity": 0,
            "paternity": 5,
        },
    },
    "E002": {
        "id": "E002",
        "name": "Bob Smith",
        "department": "Marketing",
        "role": "Marketing Analyst",
        "email": "bob.smith@company.com",
        "manager_id": "E004",
        "leave_balance": {
            "casual": 8,
            "sick": 10,
            "annual": 18,
            "maternity": 0,
            "paternity": 5,
        },
    },
    "E003": {
        "id": "E003",
        "name": "Carol Williams",
        "department": "Engineering",
        "role": "Engineering Manager",
        "email": "carol.williams@company.com",
        "manager_id": None,
        "leave_balance": {
            "casual": 10,
            "sick": 12,
            "annual": 25,
            "maternity": 90,
            "paternity": 0,
        },
    },
    "E004": {
        "id": "E004",
        "name": "David Brown",
        "department": "HR",
        "role": "HR Manager",
        "email": "david.brown@company.com",
        "manager_id": None,
        "leave_balance": {
            "casual": 10,
            "sick": 12,
            "annual": 22,
            "maternity": 0,
            "paternity": 5,
        },
    },
    "E005": {
        "id": "E005",
        "name": "Eva Martinez",
        "department": "Finance",
        "role": "Financial Analyst",
        "email": "eva.martinez@company.com",
        "manager_id": "E004",
        "leave_balance": {
            "casual": 9,
            "sick": 11,
            "annual": 19,
            "maternity": 90,
            "paternity": 0,
        },
    },
}

# ─────────────────────────────────────────────
#  LEAVE STORE
# ─────────────────────────────────────────────

LEAVES: dict[str, dict] = {}
_leave_counter = 1

VALID_LEAVE_TYPES = {"casual", "sick", "annual", "maternity", "paternity"}
VALID_STATUSES = {"pending", "approved", "rejected", "cancelled"}


# ─────────────────────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────────────────────

def _new_leave_id() -> str:
    global _leave_counter
    lid = f"L{_leave_counter:03d}"
    _leave_counter += 1
    return lid


def _parse_date(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _count_days(start: str, end: str) -> int:
    """Return inclusive business day count between two date strings."""
    s = _parse_date(start)
    e = _parse_date(end)
    if e < s:
        raise ValueError("end_date must be on or after start_date")
    delta = (e - s).days + 1
    return delta


# ── Employee helpers ──────────────────────────

def find_employee(employee_id: Optional[str] = None, name: Optional[str] = None) -> Optional[dict]:
    """Return employee dict by ID or by (partial, case-insensitive) name."""
    if employee_id:
        return EMPLOYEES.get(employee_id.upper())
    if name:
        name_lower = name.lower()
        for emp in EMPLOYEES.values():
            if name_lower in emp["name"].lower():
                return emp
    return None


def get_all_employees() -> list[dict]:
    return list(EMPLOYEES.values())


# ── Leave helpers ─────────────────────────────

def create_leave(employee_id: str, leave_type: str, start_date: str,
                 end_date: str, reason: str) -> dict:
    """Create and store a new leave request. Returns the leave record."""
    emp = EMPLOYEES.get(employee_id.upper())
    if not emp:
        raise ValueError(f"Employee '{employee_id}' not found.")

    leave_type = leave_type.lower()
    if leave_type not in VALID_LEAVE_TYPES:
        raise ValueError(f"Invalid leave type '{leave_type}'. Valid types: {', '.join(sorted(VALID_LEAVE_TYPES))}")

    days = _count_days(start_date, end_date)
    balance = emp["leave_balance"].get(leave_type, 0)
    if days > balance:
        raise ValueError(
            f"Insufficient {leave_type} leave balance. "
            f"Requested: {days} day(s), Available: {balance} day(s)."
        )

    lid = _new_leave_id()
    record = {
        "leave_id": lid,
        "employee_id": employee_id.upper(),
        "employee_name": emp["name"],
        "leave_type": leave_type,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "reason": reason,
        "status": "pending",
        "rejection_reason": None,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    LEAVES[lid] = record
    return record


def get_leave(leave_id: str) -> Optional[dict]:
    return LEAVES.get(leave_id.upper())


def get_all_leaves() -> list[dict]:
    return list(LEAVES.values())


def get_pending_leaves() -> list[dict]:
    return [l for l in LEAVES.values() if l["status"] == "pending"]


def get_employee_leaves(employee_id: str) -> list[dict]:
    return [l for l in LEAVES.values() if l["employee_id"] == employee_id.upper()]


def approve_leave_record(leave_id: str) -> dict:
    record = LEAVES.get(leave_id.upper())
    if not record:
        raise ValueError(f"Leave request '{leave_id}' not found.")
    if record["status"] != "pending":
        raise ValueError(f"Leave '{leave_id}' is already '{record['status']}'. Only pending leaves can be approved.")

    # Deduct from balance
    emp = EMPLOYEES[record["employee_id"]]
    emp["leave_balance"][record["leave_type"]] -= record["days"]

    record["status"] = "approved"
    record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return record


def reject_leave_record(leave_id: str, rejection_reason: str) -> dict:
    record = LEAVES.get(leave_id.upper())
    if not record:
        raise ValueError(f"Leave request '{leave_id}' not found.")
    if record["status"] != "pending":
        raise ValueError(f"Leave '{leave_id}' is already '{record['status']}'. Only pending leaves can be rejected.")

    record["status"] = "rejected"
    record["rejection_reason"] = rejection_reason
    record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return record


def cancel_leave_record(leave_id: str) -> dict:
    record = LEAVES.get(leave_id.upper())
    if not record:
        raise ValueError(f"Leave request '{leave_id}' not found.")
    if record["status"] not in ("pending", "approved"):
        raise ValueError(f"Leave '{leave_id}' is '{record['status']}' and cannot be cancelled.")

    # Restore balance if it was approved
    if record["status"] == "approved":
        emp = EMPLOYEES[record["employee_id"]]
        emp["leave_balance"][record["leave_type"]] += record["days"]

    record["status"] = "cancelled"
    record["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return record
