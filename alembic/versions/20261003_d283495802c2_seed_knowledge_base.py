"""seed knowledge base

Common issues and fixes per category, matched against a request's description by meaning rather
than exact wording — see app.ml.troubleshooting. Hand-authored rather than mined from a dataset:
the only dataset on hand (the Phase 3 support-ticket CSV) is generic IT-helpdesk material, the
same mismatch that led the complaint categories to be seeded by hand too.

Revision ID: d283495802c2
Revises: 604025d6a47e
Create Date: 2026-10-03 13:52:20.532563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd283495802c2'
down_revision: Union[str, Sequence[str], None] = '604025d6a47e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (category_name, equipment_type, issue_pattern, suggested_fix)
ENTRIES = [
    (
        "Electrical", "Electrical panel",
        "Circuit breaker trips repeatedly or won't stay reset",
        "Switch off all downstream loads, then reset the breaker alone. If it holds with "
        "everything off, reconnect one circuit at a time to isolate the short. If it won't stay "
        "reset even with nothing connected, the breaker itself is likely faulty and needs "
        "replacing — don't force it or bypass it.",
    ),
    (
        "Electrical", "Wiring",
        "Lights or equipment flicker or lose power intermittently",
        "Check for a loose neutral or ground connection at the nearest junction box or panel "
        "terminal — flickering under load is the classic sign. Tighten any connections found, "
        "and if it continues, test the circuit's voltage under load to rule out a failing "
        "breaker or an undersized conductor.",
    ),
    (
        "Electrical", "Electrical panel",
        "Burning smell or visible scorching near a panel, motor or outlet",
        "Cut power to the affected circuit at the main breaker immediately and do not "
        "re-energize it. A burning smell means insulation has already overheated; treat this as "
        "urgent and inspect for charring before any further use.",
    ),
    (
        "Electrical", "Motor",
        "Motor or appliance has no power even though the breaker is on",
        "Confirm voltage is actually present at the outlet or terminal with a meter before "
        "assuming the motor has failed. If voltage is present but it still won't start, check "
        "the thermal overload hasn't tripped and that the motor isn't seized.",
    ),
    (
        "Mechanical", "Lathe",
        "Loud grinding or clanking noise from moving parts",
        "Stop the equipment immediately — grinding usually means metal-on-metal contact from a "
        "worn bearing or a dislodged part. Running it further risks turning a bearing "
        "replacement into a full assembly repair.",
    ),
    (
        "Mechanical", "Pump",
        "Excessive vibration during operation",
        "Check for an imbalanced or loose coupling first — it's the most common cause and the "
        "easiest to fix. If the mount bolts and coupling are tight, inspect the bearing for play "
        "and the impeller or rotating element for buildup or damage.",
    ),
    (
        "Mechanical", "Conveyor",
        "Belt is slipping, squealing or has come off",
        "A squeal under load almost always means the belt has lost tension — check and "
        "re-tension it before replacing anything. If it keeps slipping even at correct tension, "
        "look for oil or grease contamination on the belt or pulley face.",
    ),
    (
        "Mechanical", "Motor",
        "Bearing is overheating or making a whining noise",
        "Feel for heat at the bearing housing (carefully) and listen for a dry, whining pitch — "
        "both point to insufficient lubrication. Regrease per the equipment's spec first; if the "
        "noise persists afterward, the bearing has likely already pitted and needs replacing.",
    ),
    (
        "HVAC", "AC unit",
        "Unit is running but not cooling or heating effectively",
        "Check the air filter first — a clogged filter restricts airflow and is the single most "
        "common cause of weak output. If the filter is clean, check refrigerant pressure and the "
        "condenser coil for dirt or blockage.",
    ),
    (
        "HVAC", "AC unit",
        "Unit short cycles, turning on and off every few minutes",
        "Short cycling is usually a thermostat sensing issue or a dirty condenser causing it to "
        "overheat and trip out. Clean the condenser coil and check the thermostat's placement "
        "isn't near a heat source or draft before replacing any parts.",
    ),
    (
        "HVAC", "Ductwork",
        "Strange or musty odor coming from vents",
        "A musty smell almost always means moisture buildup in the ductwork or on the evaporator "
        "coil, usually from condensate that isn't draining properly. Check the condensate drain "
        "line for a clog before assuming it needs a full duct cleaning.",
    ),
    (
        "HVAC", "AC unit",
        "Water leaking or pooling near the indoor unit",
        "This is almost always a blocked or disconnected condensate drain line, not a "
        "refrigerant leak. Clear the drain line first — a wet-vac at the outside termination "
        "point usually does it — before inspecting the drain pan for cracks.",
    ),
    (
        "Plumbing", "Pump",
        "Low water pressure at an outlet or fixture",
        "Check whether the drop is at one fixture or the whole system — one fixture usually "
        "means a clogged aerator or valve; the whole system points to the pump or a main line "
        "restriction. Clean the aerator first since it's the fastest thing to rule out.",
    ),
    (
        "Plumbing", "Piping",
        "Visible leak at a pipe joint or fitting",
        "Shut off the nearest isolation valve before doing anything else to stop the leak from "
        "getting worse. Most joint leaks are from a loosened or degraded seal — retightening or "
        "replacing the fitting usually resolves it without replacing the pipe run.",
    ),
    (
        "Plumbing", "Pump",
        "Pump won't prime or no water is flowing",
        "Check for air in the suction line first — a pump that's lost its prime is the most "
        "common reason for no flow, not a failed motor. Re-prime per the pump's manual, and "
        "check the foot valve isn't stuck open, which lets the line drain back between uses.",
    ),
    (
        "Plumbing", "Drainage",
        "Drain is clogged or backing up",
        "Try clearing the blockage mechanically before reaching for chemical cleaner, which can "
        "damage older pipework. If a manual clear doesn't work and backups keep recurring at the "
        "same point, it likely needs a camera inspection further down the line.",
    ),
    (
        "Electronic", "Control panel",
        "Control panel or display is unresponsive",
        "Power-cycle the unit first — a frozen display is very often a software hang rather than "
        "a hardware fault. If it doesn't come back after a full power cycle, check the control "
        "board's connections and fuses before assuming the board itself has failed.",
    ),
    (
        "Electronic", "Sensor",
        "Sensor is giving erratic or clearly wrong readings",
        "Check the sensor's wiring and connector for corrosion or a loose pin, which is the most "
        "common cause of erratic readings. If the connections are sound, recalibrate the sensor "
        "against a known reference before replacing it.",
    ),
    (
        "Electronic", "Control panel",
        "Device won't power on at all",
        "Confirm it's actually receiving power — check the supply voltage and any inline fuse "
        "before opening the unit up. A blown fuse with no other symptoms is far more common than "
        "a dead control board.",
    ),
    (
        "Electronic", "Control panel",
        "Intermittent communication or connectivity fault between devices",
        "Check cabling and connectors along the run first — intermittent faults are usually a "
        "physical connection issue, not a configuration problem. Reseat connectors and inspect "
        "for pinched or chafed cable before changing any settings.",
    ),
]

complaint_categories = sa.table(
    "complaint_categories", sa.column("id", sa.Integer), sa.column("category_name", sa.String)
)
knowledge_base = sa.table(
    "knowledge_base",
    sa.column("category_id", sa.Integer),
    sa.column("equipment_type", sa.String),
    sa.column("issue_pattern", sa.Text),
    sa.column("suggested_fix", sa.Text),
)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    category_ids = dict(bind.execute(sa.select(complaint_categories.c.category_name, complaint_categories.c.id)).all())
    op.bulk_insert(
        knowledge_base,
        [
            {
                "category_id": category_ids[category_name],
                "equipment_type": equipment_type,
                "issue_pattern": issue_pattern,
                "suggested_fix": suggested_fix,
            }
            for category_name, equipment_type, issue_pattern, suggested_fix in ENTRIES
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    category_ids = dict(bind.execute(sa.select(complaint_categories.c.category_name, complaint_categories.c.id)).all())
    seeded_category_ids = {category_ids[category_name] for category_name, *_ in ENTRIES}
    op.execute(knowledge_base.delete().where(knowledge_base.c.category_id.in_(seeded_category_ids)))
