# HR Loan & Advance Salary Management — Odoo 17 Community Edition

![Odoo Version](https://img.shields.io/badge/Odoo-17.0-blue)
![License](https://img.shields.io/badge/License-LGPL--3-green)
![Edition](https://img.shields.io/badge/Edition-Community-orange)
![Dependencies](https://img.shields.io/badge/Depends-base%20%7C%20hr%20%7C%20account%20%7C%20mail-lightgrey)

---

## Table of Contents

- [What Problem Does This Solve?](#what-problem-does-this-solve)
- [Features](#features)
- [Module Structure](#module-structure)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Accounting Integration](#accounting-integration)
- [Security & Roles](#security--roles)
- [Technical Reference](#technical-reference)
- [Changelog](#changelog)

---

## What Problem Does This Solve?

Companies manage employee loans through email and spreadsheets — no audit trail, missed deductions, and finance errors every month. This module provides:

- A **structured digital request & approval workflow**
- **Automatic repayment schedule** generation
- **Accounting journal entries** automatically on disbursal and repayment (via `account` module — no payroll required)
- **Full audit trail** through Odoo's chatter

---

## Features

| Feature | Detail |
|---|---|
| Request Types | Employee Loan & Advance Salary |
| Approval Levels | Employee → HR Manager → Finance (3 levels) |
| Repayment Schedule | Auto-generated monthly installments on disbursal |
| Accounting | Journal entries on disbursal & each repayment via `account.move` |
| Payment Registration | Wizard with installment selection + method (Bank/Cash/Cheque) |
| Payment Reversal | Reverse posted payments with automatic journal reversal |
| PDF Report | Printable loan agreement with schedule & 3-signature block |
| Loan Config | Per-company accounting setup (journal + 3 accounts) |
| Security | 3 roles + record-level rules (employees see only own loans) |
| Multi-company | Full support |
| Audit Trail | `mail.thread` chatter on every state change |
| Auto-close | Loan automatically closes when fully repaid |

---

## Module Structure

```
hr_loan_management/
├── __init__.py
├── __manifest__.py
│
├── models/
│   ├── __init__.py
│   ├── hr_loan_config.py       # Per-company accounting configuration
│   ├── hr_loan.py              # Main loan model + workflow + journal entry
│   ├── hr_loan_line.py         # Repayment schedule lines
│   └── hr_loan_payment.py      # Payment records + account.move integration
│
├── wizard/
│   ├── __init__.py
│   ├── hr_loan_refuse_wizard.py            # Refusal with mandatory reason
│   ├── hr_loan_refuse_wizard_views.xml
│   ├── hr_loan_payment_wizard.py           # Register repayment wizard
│   └── hr_loan_payment_wizard_views.xml
│
├── views/
│   ├── hr_loan_config_views.xml   # Accounting setup form
│   ├── hr_loan_views.xml          # Loan form/tree/kanban/search
│   ├── hr_loan_line_views.xml     # Installment tree
│   ├── hr_loan_payment_views.xml  # Payment form/tree
│   └── hr_loan_menu.xml           # All menus
│
├── report/
│   ├── hr_loan_report.xml
│   └── hr_loan_report_template.xml
│
├── security/
│   ├── hr_loan_security.xml
│   └── ir.model.access.csv
│
├── data/
│   ├── hr_loan_sequence.xml       # LOAN/YYYY/XXXXX & LPAY/YYYY/XXXXX
│   └── hr_loan_data.xml
│
└── static/description/
    └── icon.png
```

---

## Dependencies

```python
'depends': ['base', 'hr', 'account', 'mail']
```

**No `hr_payroll`. No Enterprise modules.** Installs on any Odoo 17 Community instance.

---

## Installation

### 1. Copy the module

```bash
cp -r hr_loan_management /path/to/your/odoo/custom_addons/
```

### 2. Ensure your `odoo.conf` includes the path

```ini
addons_path = /opt/odoo/addons,/opt/odoo/custom_addons
```

### 3. Restart Odoo

```bash
sudo systemctl restart odoo
# or
python odoo-bin -c /etc/odoo/odoo.conf
```

### 4. Update Apps List

In Odoo: **Apps → Update Apps List**

### 5. Install

Search for **"HR Loan"** → Click **Install**

> ✅ Required modules (`base`, `hr`, `account`, `mail`) are all standard Odoo Community modules.

---

## Configuration

### Step 1 — Assign User Roles

Go to **Settings → Users** and assign each user the appropriate group:

| Group | Who Gets It | Access |
|---|---|---|
| Employee (Loan Requester) | All staff | Create & view own loans |
| HR Manager | HR officers | Approve step 1, view all, refuse |
| Finance (Loan Disburser) | Finance / CFO | Final approval, disburse, payments |

### Step 2 — Configure Accounting (REQUIRED before first disbursal)

Go to **Loan Management → Configuration → Accounting Setup** and create a record:

| Field | What to Set |
|---|---|
| **Loan Journal** | A bank, cash, or miscellaneous journal |
| **Loan Receivable Account** | e.g. `1410 – Employee Loans Receivable` |
| **Disbursal / Source Account** | e.g. `1010 – Bank Account` |
| **Repayment Account** | e.g. `1010 – Bank Account` (or a clearing account) |
| **Max Loan Amount** | Ceiling per request (informational) |
| **Max Installments** | Max months allowed (informational) |

> **Without this configuration, disbursal will fail with a clear error message.**

---

## Usage Guide

### Employee — Submit a Loan Request

1. Go to **Loan Management → My Loans → New**
2. Choose **Type**: Employee Loan or Advance Salary
3. Fill in Amount, Number of Installments, First Repayment Date
4. Add a Note explaining the purpose
5. Click **Submit for Approval**

### HR Manager — Approve (Step 1)

1. Go to **Loan Management → Management → All Loan Requests**
2. Filter by **Waiting Approval**
3. Open the request → Click **Approve (HR)** or **Refuse** (with reason)

### Finance — Disburse (Step 2)

1. Open any **HR Approved** loan
2. Click **Approve & Disburse**
3. System automatically:
   - Creates a journal entry (DR Loan Receivable / CR Bank)
   - Generates the full monthly repayment schedule
4. Click **Print Agreement** to generate the signed PDF

### Finance — Register a Repayment

1. Open the active loan → Click **Register Repayment**
2. Set payment date, amount, method
3. Select which installment(s) this covers
4. Click **Register & Post Payment**
5. System creates: journal entry (DR Bank / CR Loan Receivable), marks installment paid

### Auto-Close

When all installments are paid, the loan automatically moves to **Closed** state.

---

## Accounting Integration

This module integrates with the standard `account` module (Community Edition):

### On Disbursal

```
DR  Loan Receivable Account    [loan_amount]
CR  Disbursal / Source Account [loan_amount]
```

### On Each Repayment

```
DR  Repayment Account (Bank/Cash) [payment_amount]
CR  Loan Receivable Account        [payment_amount]
```

### Payment Reversal

If a payment is reversed, `account.move._reverse_moves()` is called automatically — the journal entry is reversed and the installment is marked unpaid.

---

## Security & Roles

| Permission | Employee | HR Manager | Finance |
|---|:---:|:---:|:---:|
| Create loan request | ✅ | ✅ | ✅ |
| View own loans only | ✅ | — | — |
| View all company loans | ❌ | ✅ | ✅ |
| Approve — HR step | ❌ | ✅ | ✅ |
| Approve & Disburse | ❌ | ❌ | ✅ |
| Refuse loan | ❌ | ✅ | ✅ |
| Register payment | ❌ | ❌ | ✅ |
| Reverse payment | ❌ | ❌ | ✅ |
| Configure accounting | ❌ | ❌ | ✅ |
| Delete records | ❌ | ❌ | ✅ |

---

## Technical Reference

### Models

| Model | Purpose |
|---|---|
| `hr.loan` | Main loan record. Workflow, schedule generation, journal entry on disbursal |
| `hr.loan.line` | Installment lines. One per month. Tracks paid/unpaid + linked payment |
| `hr.loan.payment` | Payment records. Creates `account.move` on posting |
| `hr.loan.config` | Per-company accounting config (journal + accounts) |
| `hr.loan.refuse.wizard` | Transient model for refusal with mandatory reason |
| `hr.loan.payment.wizard` | Transient model for registering repayments |

### Loan State Machine

```
draft ──► confirm ──► validate1 ──► validate ──► close
                  └──► refuse      └──► refuse
draft ◄── cancel ◄──┘
draft ◄── (reset) ◄── refuse / cancel
```

### Sequences

| Code | Format | Example |
|---|---|---|
| `hr.loan` | `LOAN/YYYY/NNNNN` | `LOAN/2025/00001` |
| `hr.loan.payment` | `LPAY/YYYY/NNNNN` | `LPAY/2025/00001` |

---

## Changelog

### v17.0.2.0.0 — Community Edition Refactor

- **Removed** `hr_payroll` dependency entirely
- **Added** `hr.loan.config` model for per-company accounting setup
- **Added** `hr.loan.payment` model replacing payslip hook
- **Added** payment registration wizard with installment selector
- **Added** journal entry creation on disbursal via `account.move`
- **Added** journal entry creation on each repayment
- **Added** payment reversal with automatic journal reversal
- **Added** auto-close when loan is fully repaid
- **Added** payment smart button on loan form
- Installments now link to `hr.loan.payment` instead of `hr.payslip`

---

## Author

**Shehab Eldin Saeed Zakaria** — Odoo Developer  
📧 dev.shehabsaid@gmail.com  
🔗 [linkedin.com/in/shehab1001](https://www.linkedin.com/in/shehab1001/)  
💻 [github.com/Shehab1001](https://github.com/Shehab1001)

**License:** LGPL-3
