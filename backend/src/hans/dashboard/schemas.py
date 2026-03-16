from pydantic import BaseModel


# --- SCHEMAS ----------------------------------------------------------

class DashboardStatsRead(BaseModel):
    # Totals displayed on dashboard widgets.
    total_orders: int
    total_patients: int
    total_owners: int
