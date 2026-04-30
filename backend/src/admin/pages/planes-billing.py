"""Admin page: Planes & Billing.

Thin wrapper — delegates all logic to src/admin/modules/billing.py.
"""

from src.admin.modules.billing import render_billing_admin

render_billing_admin()
