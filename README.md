# HR Loan & Advance Salary Management — Odoo 17

![Odoo Version](https://img.shields.io/badge/Odoo-17.0-blue)
![License](https://img.shields.io/badge/License-LGPL--3-green)
![Category](https://img.shields.io/badge/Category-HR%2FPayroll-orange)

A production-ready Odoo 17 module that solves the real business problem of managing **employee loans and advance salary requests** with a full multi-level approval workflow and **automatic payroll deduction** integration.

---

## Table of Contents

- [Business Problem Solved](#business-problem-solved)
- [Features](#features)
- [Module Structure](#module-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Payroll Integration](#payroll-integration)
- [Security & Access Roles](#security--access-roles)
- [Technical Reference](#technical-reference)
- [Changelog](#changelog)
- [Author](#author)

---

## Business Problem Solved

Most companies struggle with:
- No formal loan request process — handled by email or paper
- Manual tracking of repayments in spreadsheets
- Payroll team not notified of deductions → missed or double deductions
- No approval trail or audit history
- No visibility into employee outstanding balances

This module solves all of the above by providing a structured, auditable, and automated process inside Odoo.

---

## Features

### Core
- **Two request types**: Employee Loan & Advance Salary
- **Multi-level approval workflow**: Employee → HR Manager → Finance/Admin
- **Automatic repayment schedule** generation on disbursement
- **Automatic payroll deduction** via salary rule integration (`LOAN_DED`)
- **Loan refusal wizard** with mandatory reason
- **Printable PDF** loan agreement with repayment schedule and signature block

### Tracking & Visibility
- Real-time repayment progress (paid / remaining)
- Overdue installment highlighting in the UI
- Chatter logs every status change with timestamps and user info
- Full audit trail via `mail.thread`

### Views
- **Tree view** with color-coded status rows
- **Kanban view** grouped by status
- **Form view** with dynamic buttons based on user role and state
- **Search view** with filters (My Loans, Active, Overdue, by Type)

### Security
- Three role levels: Employee, HR Manager, Finance
- Record rules: employees see only their own loans
- Multi-company support

---

## Module Structure

```
hr_loan_management/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── hr_loan.py            # Main loan model + workflow
│   ├── hr_loan_line.py       # Repayment schedule lines
│   └── hr_payslip.py         # Payslip & salary rule integration
├── wizard/
│   ├── __init__.py
│   ├── hr_loan_refuse_wizard.py
│   └── hr_loan_refuse_wizard_views.xml
├── views/
│   ├── hr_loan_views.xml     # Form, Tree, Kanban, Search
│   ├── hr_loan_line_views.xml
│   └── hr_loan_menu.xml
├── report/
│   ├── hr_loan_report.xml
│   └── hr_loan_report_template.xml
├── security/
│   ├── hr_loan_security.xml
│   └── ir.model.access.csv
├── data/
│   ├── hr_loan_sequence.xml  # LOAN/YYYY/XXXXX sequence
│   └── hr_loan_salary_rule.xml
└── static/
    └── description/
        └── icon.png
```

---

## Installation

### Requirements

| Dependency | Version |
|---|---|
| Odoo | 17.0 |
| Python | 3.10+ |
| `hr` | Bundled with Odoo |
| `hr_payroll` | Bundled with Odoo Enterprise or Community |
| `mail` | Bundled with Odoo |
| `account` | Bundled with Odoo |

### Steps

1. **Copy the module** into your Odoo addons directory:
   ```bash
   cp -r hr_loan_management /path/to/odoo/addons/
   ```

2. **Restart the Odoo server**:
   ```bash
   sudo systemctl restart odoo
   # or
   python odoo-bin --config=/etc/odoo/odoo.conf
   ```

3. **Activate Developer Mode** in Odoo:
   `Settings → General Settings → Developer Tools → Activate the developer mode`

4. **Update the apps list**:
   `Apps → Update Apps List`

5. **Search for and install** `HR Loan & Advance Salary Management`

---

## Configuration

### Step 1 — Assign User Roles

Go to `Settings → Users` and assign the appropriate group to each user:

| Group | Who Gets It |
|---|---|
| Employee (Loan Requester) | All employees who can submit requests |
| HR Manager | HR officers who approve at step 1 |
| Finance (Loan Disburser) | Finance team / admin who gives final approval |

### Step 2 — Add the Salary Rule to Your Payroll Structure

1. Go to `Payroll → Configuration → Salary Structures`
2. Open your active structure (e.g., **Employee** or **Basic**)
3. Go to the **Salary Rules** tab
4. Click **Add a line** and search for `Loan Deduction` (code: `LOAN_DED`)
5. Save

This single step enables fully automatic deductions when payslips are confirmed.

### Step 3 — (Optional) Multi-Company Setup

The loan sequence and rules are shared across companies by default. If you need per-company sequences, go to `Settings → Technical → Sequences` and create a company-specific override for the `hr.loan` sequence.

---

## Usage Guide

### For Employees

1. Go to **Loan Management → My Loans**
2. Click **New**
3. Fill in:
   - **Type**: Loan or Advance Salary
   - **Employee**: Yourself (or select if HR is creating on behalf)
   - **Loan Amount** and **Number of Installments**
   - **First Deduction Date**: the month you want deductions to start
   - **Notes**: purpose/reason for the loan
4. Click **Submit for Approval**

### For HR Managers

1. Go to **Loan Management → Management → All Loan Requests**
2. Filter by `Waiting Approval`
3. Open the request, review it, and click **Approve (HR)**
4. Or click **Refuse** and enter a mandatory reason

### For Finance Team

1. After HR approval, requests appear in `HR Approved` state
2. Open the request, verify the amount, and click **Approve & Disburse**
3. The system automatically generates the full monthly repayment schedule

### Viewing Repayment Progress

- Open any active loan
- The **Installments** smart button shows `paid / total` count
- The **Repayment Schedule** tab shows each line color-coded:
  - 🟢 Green = Paid
  - 🔴 Red = Overdue (past due date, not paid)
  - ⚪ Normal = Upcoming

### Printing a Loan Agreement

- From any non-draft loan, click **Print** in the header
- A PDF is generated with full details, repayment schedule, and signature block

---

## Payroll Integration

This module integrates with `hr_payroll` at two levels:

### Level 1 — Salary Rule (Automatic Deduction)

The `LOAN_DED` salary rule runs Python code inside the payslip to:
1. Find all **unpaid** installment lines for the employee within the payslip's date range
2. Sum the amounts
3. Apply as a **negative deduction** on the payslip

```python
# Inside the salary rule (amount_python_compute):
loan_lines = env['hr.loan.line'].search([
    ('employee_id', '=', employee.id),
    ('paid', '=', False),
    ('date', '>=', payslip.date_from),
    ('date', '<=', payslip.date_to),
    ('loan_id.state', '=', 'validate'),
])
result = -sum(loan_lines.mapped('amount'))
```

### Level 2 — Payslip Confirm Hook

When a payslip is set to **Done**, the `action_payslip_done` override automatically:
1. Finds all due loan lines for the employee in that period
2. Marks them as **Paid**
3. Links the `payslip_id` to each line for full traceability

This means finance can always trace which payslip covered which installment.

### Payslip View Enhancement

The payslip form shows:
- `Loan Deductions` smart button with count
- `Total Loan Deduction` field
- Button to open the deduction lines list

---

## Security & Access Roles

| Action | Employee | HR Manager | Finance |
|---|:---:|:---:|:---:|
| Create loan request | ✅ | ✅ | ✅ |
| View own loans | ✅ | ✅ | ✅ |
| View all company loans | ❌ | ✅ | ✅ |
| Approve (HR step) | ❌ | ✅ | ✅ |
| Approve & Disburse | ❌ | ❌ | ✅ |
| Refuse loan | ❌ | ✅ | ✅ |
| Delete loan | ❌ | ❌ | ✅ |
| Mark installment paid/unpaid | ❌ | ✅ | ✅ |

---

## Technical Reference

### Models

#### `hr.loan`
| Field | Type | Description |
|---|---|---|
| `name` | Char | Auto-generated sequence (LOAN/YYYY/XXXXX) |
| `loan_type` | Selection | `loan` or `advance` |
| `employee_id` | Many2one | hr.employee |
| `loan_amount` | Monetary | Total loan amount |
| `installment` | Integer | Number of monthly installments |
| `installment_amount` | Monetary | Computed: loan_amount / installment |
| `payment_date` | Date | First deduction date |
| `state` | Selection | draft → confirm → validate1 → validate |
| `loan_lines` | One2many | hr.loan.line repayment schedule |
| `total_paid` | Monetary | Sum of paid lines |
| `total_remaining` | Monetary | loan_amount − total_paid |

#### `hr.loan.line`
| Field | Type | Description |
|---|---|---|
| `loan_id` | Many2one | Parent loan |
| `date` | Date | Scheduled deduction date |
| `amount` | Monetary | Installment amount |
| `paid` | Boolean | Whether this line has been deducted |
| `paid_date` | Date | Date marked as paid |
| `payslip_id` | Many2one | Linked payslip (if auto-deducted) |

### Workflow States

```
draft → confirm → validate1 → validate
                ↘ refuse
draft ← cancel ←┘ (reset to draft)
```

### Sequence Format
`LOAN/2025/00001`, `LOAN/2025/00002`, resets each year.

---

## Changelog

### v17.0.1.0.0 (Initial Release)
- Employee Loan and Advance Salary request management
- Multi-level approval workflow (Employee → HR → Finance)
- Automatic repayment schedule generation
- Payroll integration with `LOAN_DED` salary rule
- Payslip confirmation hook for automatic marking
- Printable QWeb PDF report
- Role-based security (3 groups + record rules)
- Multi-company support

---

## Author

**Shehab Eldin Saeed Zakaria**
Odoo Developer | Backend Developer
- GitHub: [github.com/Shehab1001](https://github.com/Shehab1001)
- LinkedIn: [linkedin.com/in/shehab1001](https://www.linkedin.com/in/shehab1001/)
- Email: dev.shehabsaid@gmail.com

---

## License

This module is licensed under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.en.html).
