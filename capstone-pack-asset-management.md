# Capstone Pack — Asset Management (Flask)

Student capstone pool app (reworked from the earlier Inventory Management pack into an internal B2B asset-tracking angle). Trainees receive only the Opening Statement below — everything after it is the instructor's answer key, not shown to trainees up front.

---

## 1. Opening Statement

> RPATech wants to stop tracking company assets — laptops, monitors, phones, furniture — in a shared spreadsheet. Build a system to register assets, assign them to employees or departments, and track every time an asset changes hands, goes in for repair, or is retired. Whoever's managing this needs to be able to answer "who has this right now, and where has it been" for any asset, at any time.

*(6 lines. Seeded ambiguity: it never says whether an asset can be assigned to a department as a whole or only ever to a named employee — trainees must ask. Hidden complexity: "where has it been" implies a full assignment/custody history per asset, not just a current-holder field — easy to under-build as a single "assigned_to" column that gets overwritten on every reassignment.)*

---

## 2. Instructor Answer Key

### Expected Entities
- **User** — admin/staff account (IT/ops team).
- **Employee** — name, department, contact info (can be a lightweight lookup table, not a full HR module).
- **Department** — name, cost center (optional).
- **Asset** — tag/serial number, category (laptop, monitor, phone, furniture, etc.), model, purchase date, purchase value, current status (in use / in repair / in storage / retired).
- **Asset Assignment** — the audit-grade record: asset, assigned-to (employee and/or department), assigned date, returned/reassigned date, assigned-by. This is the hidden-complexity entity — many teams collapse this into a single mutable field on Asset and lose history.
- **Maintenance/Repair Log** — asset, issue description, sent-out date, returned date, cost (optional), vendor (optional).

### Expected Roles
**Admin/IT Staff** — full access: register assets, assign/reassign, log repairs, retire assets. **Employee (optional, lighter role)** — read-only view of assets currently assigned to them. A single-role (admin-only) resolution is acceptable if documented.

### Expected Screens
1. Login.
2. Dashboard — asset counts by status/category, assets currently in repair, recently reassigned.
3. Asset CRUD — register new asset, edit details, retire.
4. Employee/Department lookup CRUD (lightweight — just enough to assign against).
5. Assignment flow — assign or reassign an asset to an employee/department, closing out the prior assignment record rather than overwriting it.
6. Asset detail/history view — full chronological custody trail plus repair history for one asset.
7. Maintenance log entry — send an asset for repair, mark it returned.
8. Retire flow — mark an asset retired/disposed, with a reason.

### Expected Clarifying Questions
1. Can an asset be assigned to a department as a whole, or only ever to a single named employee?
2. When an asset is reassigned, should the prior assignment record be closed out (end date set) and a new one created, or is it acceptable to only keep the current holder?
3. Does sending an asset for repair count as a special assignment state, or a separate log entirely, and does it interrupt the current assignment (e.g. does the employee "lose" the asset while it's out for repair)?
4. Is asset value/depreciation tracking in scope, or is purchase value just informational?
5. What are the valid asset statuses, and which transitions between them are allowed (e.g. can a retired asset be reassigned)?
6. Do departments themselves need a hierarchy (sub-departments), or is it a flat list?

### Suggested Phase Split → GitHub Milestones

**Milestone 1 — Scaffold, Schema, Auth**
1. Flask app scaffold (blueprints, config, DB connection)
2. Schema: users, employees, departments, assets, asset_assignments, maintenance_logs
3. Auth: login/logout, password hashing, role check (if employee role is in scope)
4. Seed script: a handful of employees, departments, and assets

**Milestone 2 — Asset, Employee, Department CRUD**
1. Asset CRUD (register, edit, view)
2. Employee/Department lookup CRUD
3. Asset list with status/category filters
4. Asset detail page shell (history sections added in Milestone 3)

**Milestone 3 — Assignment History + Maintenance**
1. Assignment flow that closes out the previous assignment record and opens a new one, atomically, on reassignment
2. Asset detail page showing full custody trail in chronological order
3. Maintenance/repair log entry and return flow, linked to the asset's status
4. Status transition rules enforced (e.g. an asset in repair can't be freshly assigned until returned)

**Milestone 4 — Reporting + Polish**
1. Dashboard widgets: counts by status/category, assets currently out for repair, assets not assigned to anyone
2. Retire flow with reason, blocking further assignment of a retired asset
3. Seed data crafted to demonstrate a multi-step custody trail (assigned → reassigned → sent for repair → returned → reassigned again) for one asset
4. Production sanity check (no debug mode, no hardcoded secrets)

---

## 3. Acceptance Criteria

- Reassigning an asset never overwrites history — the prior assignment record shows an end date/reassigned-date, and a new assignment record is created; the asset detail page lists every past assignment in order, not just the current holder.
- An asset sent for repair transitions status correctly and is visibly distinguishable from an actively-assigned asset; returning it from repair restores it to an assignable state.
- A retired asset cannot be assigned or reassigned — the action is blocked, not just discouraged in the UI.
- The asset detail view answers "who has this now, and where has it been" from stored history alone — no reliance on a single mutable "current holder" field that could have drifted from the assignment log.
- Dashboard counts (by status, by category, in-repair) match what a direct count against the underlying tables would show.
- On a fresh install, the seed script populates a working demo dataset including at least one asset with a multi-step history (assigned → repaired → reassigned).

---

## 4. Rubric Mapping

**Spec quality (25):** Full marks requires the fine-tuned PRD to explicitly resolve the employee-vs-department assignment ambiguity and to state, in writing, that assignment history must be preserved (not just current holder) — a spec that treats assignment as a single overwritable field on the asset has missed the hidden complexity regardless of how clean the resulting screens look.

**Git/milestone discipline (25):** Milestones matching the phase split above, with the assignment-history mechanism tracked as its own issue in Milestone 3, distinct from basic asset CRUD — since this is the part most likely to be bolted on as an afterthought rather than designed in from the start.

**Working app (30):** Full marks requires demonstrating an asset moving through multiple real transitions (assigned → reassigned → repaired → returned → reassigned) and showing the full trail is retrievable, not just asserting it works. Asset, employee, and department CRUD must function end-to-end.

**Diff-review evidence & corrections (20):** Full marks looks for a documented catch of a mistake specific to this app's trap — commonly, the agent implementing reassignment as an `UPDATE assets SET assigned_to = ...` that silently destroys history instead of closing the old assignment row and inserting a new one. Evidence should show the trainee spotted this in the diff and the corrected commit moving to a history-preserving pattern.
