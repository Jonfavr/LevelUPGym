"""
exercise_cleanup.py
════════════════════════════════════════════════════════════════════
Two-stage database cleanup for LevelUp Gym exercises:

  STAGE 1 — Muscle Group Consolidation
    Merges fragmented primary_muscle labels down to a clean set of
    ~15 canonical groups. This is required for the auto-assigner to
    work correctly.

  STAGE 2 — Duplicate Removal
    Removes 7 confirmed duplicate exercises. Where a duplicate is
    referenced in routine_exercises or workout_logs, all foreign-key
    references are safely re-pointed to the KEPT record before the
    duplicate is deleted.

Usage:
    python exercise_cleanup.py                   # dry-run (safe, no changes)
    python exercise_cleanup.py --commit          # write all changes
    python exercise_cleanup.py --commit --stage 1  # muscle groups only
    python exercise_cleanup.py --commit --stage 2  # duplicates only
════════════════════════════════════════════════════════════════════
"""

import sqlite3
import argparse
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), 'levelup_gym.db')

# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — MUSCLE GROUP CONSOLIDATION
#
# Format: (list_of_labels_to_rename, canonical_target_label, reason)
#
# Design decisions:
#   • Abdomen / Abdominals / Lower Abs → Abs
#     All three mean the same thing. 'Abs' is what the split templates use.
#
#   • Lats / Upper Back / Middle Back → Back
#     These are all pulling muscles served by Pull-day routines. Keeping
#     them separate fragments the auto-assigner's routine lookup.
#
#   • Upper Chest / Lower Chest → Chest
#     Chest routines cover both. Incline/decline is captured in the exercise
#     name, not the muscle label.
#
#   • Front Deltoids / Rear Deltoids → Shoulders
#     All delt sub-regions fall under the Shoulders split category.
#
#   • Quadriceps / Quads / Inner Thighs → Legs
#     These are leg-day muscles. The distinction is captured in the exercise
#     name and description.
#
#   NOT merged (kept as distinct labels):
#   • Core       — valid standalone split type (Core day)
#   • Obliques   — specialised, often deliberately targeted
#   • Hips       — mobility/flexibility category, not a split type
#   • Forearms   — isolation group, not a split category
#   • Hamstrings — kept separate from Legs for targeted routine matching
#   • Glutes     — kept separate for targeted routine matching
#   • Calves     — kept separate for targeted routine matching
#   • Traps      — kept separate for targeted routine matching
#   • Spine / Ankles / Hip Flexors — small mobility groups, harmless to keep
# ════════════════════════════════════════════════════════════════════════════

MUSCLE_CONSOLIDATIONS = [
    (
        ['Abdomen', 'Abdominals', 'Lower Abs'],
        'Abs',
        'Fragmented ab labels → unified Abs'
    ),
    (
        ['Lats', 'Upper Back', 'Middle Back'],
        'Back',
        'All lat/back pulling muscles → Back'
    ),
    (
        ['Upper Chest', 'Lower Chest'],
        'Chest',
        'Chest sub-regions → Chest (variation captured in exercise name)'
    ),
    (
        ['Front Deltoids', 'Rear Deltoids'],
        'Shoulders',
        'Deltoid sub-regions → Shoulders'
    ),
    (
        ['Quadriceps', 'Quads', 'Inner Thighs'],
        'Legs',
        'Quad/inner thigh isolation muscles → Legs'
    ),
]


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — DUPLICATE RESOLUTION
#
# Each entry defines:
#   keep_id    — the exercise_id to KEEP (all references redirected here)
#   delete_id  — the exercise_id to DELETE
#   reason     — why we keep this one over the other
#
# Safety rules applied automatically by the script:
#   • Any routine_exercises rows pointing to delete_id are re-pointed to keep_id
#   • Any workout_logs rows pointing to delete_id are re-pointed to keep_id
#   • Any workout_set_completions rows are re-pointed
#   • delete_id is only removed after all references are cleared
# ════════════════════════════════════════════════════════════════════════════

DUPLICATE_RESOLUTIONS = [
    {
        'keep_id':   129,
        'delete_id':  16,
        'keep_name':   'Sit-Ups',
        'delete_name': 'Sit Ups',
        'reason': 'ID 129 has a fuller description. ID 16 has no references.',
    },
    {
        'keep_id':    50,
        'delete_id': 124,
        'keep_name':   "Farmer's Carry (EXP 20)",
        'delete_name': "Farmer's Carry (EXP 15)",
        'reason': 'ID 50 has higher EXP and no references. ID 124 is the orphan.',
    },
    {
        'keep_id':    54,
        'delete_id': 214,
        'keep_name':   'Battle Rope Slam',
        'delete_name': 'Battle Rope Slams',
        'reason': (
            'ID 54 is referenced in routine_exercises (routine 9). '
            'ID 214 is advanced/orphaned — references will be re-pointed to 54.'
        ),
    },
    {
        'keep_id':   127,
        'delete_id': 209,
        'keep_name':   'Explosive Push-Ups',
        'delete_name': 'Explosive Push Ups',
        'reason': 'ID 127 has the better description. Neither has references.',
    },
    {
        'keep_id':    28,
        'delete_id': 108,
        'keep_name':   'Jump Squat',
        'delete_name': 'Jump Squats',
        'reason': (
            'ID 28 is referenced in routine_exercises (routine 9). '
            'ID 108 references will be re-pointed to 28.'
        ),
    },
    {
        'keep_id':     7,
        'delete_id': 105,
        'keep_name':   'Squat',
        'delete_name': 'Squats',
        'reason': (
            'ID 7 is referenced in 3 routines and has 36 workout log entries. '
            'ID 105 has no references — safe to delete.'
        ),
    },
    {
        'keep_id':   145,
        'delete_id': 126,
        'keep_name':   'Battle Rope Alternating Waves',
        'delete_name': 'Battle Ropes',
        'reason': (
            'ID 145 has the more specific and accurate name/description. '
            'Neither has references.'
        ),
    },
]


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

CYAN   = '\033[96m'
GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def header(text):
    print(f"\n{BOLD}{'═'*68}{RESET}")
    print(f"{BOLD}  {text}{RESET}")
    print(f"{BOLD}{'═'*68}{RESET}\n")

def ok(msg):   print(f"  {GREEN}✅  {msg}{RESET}")
def warn(msg): print(f"  {YELLOW}⚠️   {msg}{RESET}")
def info(msg): print(f"  {CYAN}ℹ️   {msg}{RESET}")
def err(msg):  print(f"  {RED}❌  {msg}{RESET}")
def skip(msg): print(f"  ⏭   {msg}")
def dry(msg):  print(f"  {YELLOW}~   {msg}{RESET}")


def get_exercise(conn, eid):
    row = conn.execute(
        "SELECT * FROM exercises WHERE exercise_id=?", (eid,)
    ).fetchone()
    return dict(row) if row else None


def count_refs(conn, table, column, eid):
    return conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column}=?", (eid,)
    ).fetchone()[0]


# ════════════════════════════════════════════════════════════════════════════
# STAGE 1 — MUSCLE CONSOLIDATION
# ════════════════════════════════════════════════════════════════════════════

def run_stage_1(conn, commit: bool):
    header("STAGE 1 — Muscle Group Consolidation")

    total_updated = 0

    for sources, target, reason in MUSCLE_CONSOLIDATIONS:
        print(f"  {BOLD}{', '.join(sources)}{RESET}  →  {BOLD}{CYAN}{target}{RESET}")
        print(f"  Reason: {reason}")

        for source in sources:
            count = conn.execute(
                "SELECT COUNT(*) FROM exercises WHERE primary_muscle=?",
                (source,)
            ).fetchone()[0]

            if count == 0:
                skip(f"  '{source}' — 0 exercises, nothing to update")
                continue

            # Also update complementary_muscle where it mentions this label
            comp_count = conn.execute(
                "SELECT COUNT(*) FROM exercises WHERE complementary_muscle LIKE ?",
                (f'%{source}%',)
            ).fetchone()[0]

            if commit:
                conn.execute(
                    "UPDATE exercises SET primary_muscle=? WHERE primary_muscle=?",
                    (target, source)
                )
                if comp_count > 0:
                    # Simple replace in the complementary_muscle text field
                    conn.execute(
                        "UPDATE exercises SET complementary_muscle = "
                        "REPLACE(complementary_muscle, ?, ?) "
                        "WHERE complementary_muscle LIKE ?",
                        (source, target, f'%{source}%')
                    )
                ok(f"  '{source}' → '{target}'  ({count} exercises updated"
                   + (f", {comp_count} complementary refs updated" if comp_count else "") + ")")
            else:
                dry(f"  WOULD rename '{source}' → '{target}'  ({count} exercises"
                    + (f", {comp_count} complementary refs" if comp_count else "") + ")")

            total_updated += count
        print()

    if commit:
        ok(f"Stage 1 complete — {total_updated} primary_muscle labels updated.")
    else:
        dry(f"Stage 1 dry-run — {total_updated} exercises would be updated.")


# ════════════════════════════════════════════════════════════════════════════
# STAGE 2 — DUPLICATE REMOVAL
# ════════════════════════════════════════════════════════════════════════════

REFERENCE_TABLES = [
    # (table_name, column_name)
    ('routine_exercises',      'exercise_id'),
    ('workout_logs',           'exercise_id'),
    ('workout_set_completions','exercise_id'),
    ('session_exercise_swaps', 'old_exercise_id'),
    ('session_exercise_swaps', 'new_exercise_id'),
]

def run_stage_2(conn, commit: bool):
    header("STAGE 2 — Duplicate Exercise Removal")

    total_deleted = 0

    for res in DUPLICATE_RESOLUTIONS:
        keep_id   = res['keep_id']
        delete_id = res['delete_id']

        keep_ex   = get_exercise(conn, keep_id)
        delete_ex = get_exercise(conn, delete_id)

        print(f"  {BOLD}KEEP   [{keep_id:>3}]{RESET}  {res['keep_name']}")
        print(f"  {BOLD}DELETE [{delete_id:>3}]{RESET}  {res['delete_name']}")
        print(f"  Reason: {res['reason']}")

        if not keep_ex:
            err(f"keep_id {keep_id} not found in database — skipping pair.")
            print()
            continue

        if not delete_ex:
            skip(f"delete_id {delete_id} not found — already removed.")
            print()
            continue

        # ── Re-point all foreign-key references ──────────────────────────────
        for table, col in REFERENCE_TABLES:
            # Check table exists
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            ).fetchone()
            if not exists:
                continue

            ref_count = count_refs(conn, table, col, delete_id)
            if ref_count == 0:
                continue

            if commit:
                conn.execute(
                    f"UPDATE {table} SET {col}=? WHERE {col}=?",
                    (keep_id, delete_id)
                )
                warn(f"Re-pointed {ref_count} row(s) in {table}.{col}: "
                     f"{delete_id} → {keep_id}")
            else:
                dry(f"WOULD re-point {ref_count} row(s) in {table}.{col}: "
                    f"{delete_id} → {keep_id}")

        # ── Delete the duplicate ─────────────────────────────────────────────
        if commit:
            conn.execute(
                "DELETE FROM exercises WHERE exercise_id=?", (delete_id,)
            )
            ok(f"Deleted exercise_id {delete_id} — '{delete_ex['name']}'")
        else:
            dry(f"WOULD delete exercise_id {delete_id} — '{delete_ex['name']}'")

        total_deleted += 1
        print()

    if commit:
        ok(f"Stage 2 complete — {total_deleted} duplicate exercise(s) removed.")
    else:
        dry(f"Stage 2 dry-run — {total_deleted} exercises would be removed.")


# ════════════════════════════════════════════════════════════════════════════
# POST-RUN SUMMARY
# ════════════════════════════════════════════════════════════════════════════

def print_summary(conn):
    header("POST-CLEANUP SUMMARY")

    rows = conn.execute(
        "SELECT primary_muscle, COUNT(*) as cnt "
        "FROM exercises GROUP BY primary_muscle ORDER BY primary_muscle"
    ).fetchall()

    print(f"  {'Muscle Group':<25} {'Count':>6}")
    print(f"  {'─'*33}")
    for r in rows:
        print(f"  {r['primary_muscle']:<25} {r['cnt']:>6}")

    total = conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    print(f"\n  Total exercises in database: {BOLD}{total}{RESET}")


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='LevelUp Gym — Exercise Cleanup')
    parser.add_argument('--commit', action='store_true',
                        help='Write changes to the database (default is dry-run)')
    parser.add_argument('--stage', type=int, choices=[1, 2], default=None,
                        help='Run only stage 1 (muscle groups) or stage 2 (duplicates)')
    parser.add_argument('--db', type=str, default=DB_PATH,
                        help='Path to the SQLite database file')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        err(f"Database not found at: {args.db}")
        print(f"    Use --db /path/to/gym.db to specify the correct path.\n")
        sys.exit(1)

    mode = f"{BOLD}{'COMMIT' if args.commit else 'DRY RUN'}{RESET}"
    print(f"\n  Exercise Cleanup Script  |  Mode: {mode}  |  DB: {args.db}")

    if not args.commit:
        print(f"\n  {YELLOW}No changes will be made. "
              f"Add --commit to write to the database.{RESET}")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")   # we handle FK refs manually

    try:
        if args.stage in (None, 1):
            run_stage_1(conn, args.commit)

        if args.stage in (None, 2):
            run_stage_2(conn, args.commit)

        if args.commit:
            conn.commit()
            print_summary(conn)
            print(f"\n  {GREEN}{BOLD}✅  All changes committed successfully.{RESET}\n")
        else:
            print_summary(conn)
            print(f"\n  {YELLOW}Dry-run complete — database unchanged.{RESET}")
            print(f"  Run with {BOLD}--commit{RESET} to apply these changes.\n")

    except Exception as e:
        conn.rollback()
        err(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
