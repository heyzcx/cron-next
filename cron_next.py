#!/usr/bin/env python3
"""cron-next: print the next N run times of a cron expression.

Usage:
    python3 cron_next.py "30 9 * * 1-5"            # next 5 runs (default)
    python3 cron_next.py "0 0 1 * *" --count 3
    python3 cron_next.py "*/15 * * * *" --from "2026-11-13 10:00"

Supports the standard 5-field format (minute hour day-of-month month
day-of-week) with lists, ranges, steps and month/weekday names.
Day-of-month and day-of-week follow the classic cron OR rule: when both
are restricted, a date matches if either field matches.
"""

import argparse
import calendar
import re
import sys
from datetime import datetime, timedelta

MONTHS = {name: i for i, name in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
WEEKDAYS = {name: i for i, name in enumerate(
    ["sun", "mon", "tue", "wed", "thu", "fri", "sat"], start=0)}


def _expand_names(field, names):
    lowered = field.lower()
    for name, value in names.items():
        lowered = re.sub(rf"\b{name}\b", str(value), lowered)
    return lowered


def parse_field(field, lo, hi, names=None):
    """Parse one cron field into a sorted set of allowed values."""
    if names:
        field = _expand_names(field, names)
    values = set()
    for part in field.split(","):
        part = part.strip()
        if not part:
            raise ValueError(f"empty part in field {field!r}")
        step = 1
        if "/" in part:
            base, step_text = part.split("/", 1)
            if not step_text.isdigit() or int(step_text) < 1:
                raise ValueError(f"bad step in {part!r}")
            step = int(step_text)
        else:
            base = part
        if base == "*":
            start, end = lo, hi
        elif "-" in base:
            a, b = base.split("-", 1)
            start, end = int(a), int(b)
        else:
            start = end = int(base)
        if start < lo or end > hi or start > end:
            raise ValueError(f"value out of range in {part!r} ({lo}-{hi})")
        values.update(range(start, end + 1, step))
    return values


class CronExpression:
    def __init__(self, expression):
        fields = expression.split()
        if len(fields) != 5:
            raise ValueError(
                f"expected 5 fields, got {len(fields)}: {expression!r}")
        minute, hour, dom, month, dow = fields
        self.minutes = parse_field(minute, 0, 59)
        self.hours = parse_field(hour, 0, 23)
        self.dom = parse_field(dom, 1, 31)
        self.months = parse_field(month, 1, 12, MONTHS)
        self.dow = parse_field(dow, 0, 7, WEEKDAYS)
        self.dow = {0 if v == 7 else v for v in self.dow}
        self.dom_restricted = dom.strip() != "*"
        self.dow_restricted = dow.strip() != "*"

    def _day_matches(self, when):
        if when.month not in self.months:
            return False
        dom_ok = when.day in self.dom
        # cron weekday: Sunday=0 .. Saturday=6; Python: Monday=0 .. Sunday=6
        cron_dow = (when.weekday() + 1) % 7
        dow_ok = cron_dow in self.dow
        if self.dom_restricted and self.dow_restricted:
            return dom_ok or dow_ok
        if self.dom_restricted:
            return dom_ok
        if self.dow_restricted:
            return dow_ok
        return True

    def matches(self, when):
        return (
            when.minute in self.minutes
            and when.hour in self.hours
            and self._day_matches(when)
        )

    def next_runs(self, start, count):
        """Yield the next `count` run times strictly after `start`."""
        if count < 1:
            raise ValueError("count must be >= 1")
        found = []
        # Step minute by minute, but skip whole months that can't match.
        cursor = start.replace(second=0, microsecond=0) + timedelta(minutes=1)
        limit = start + timedelta(days=366 * 5)  # give up after ~5 years
        while len(found) < count and cursor <= limit:
            if cursor.month not in self.months:
                # Jump to the 1st of the next month at 00:00.
                year = cursor.year + (1 if cursor.month == 12 else 0)
                month = 1 if cursor.month == 12 else cursor.month + 1
                cursor = cursor.replace(year=year, month=month, day=1,
                                        hour=0, minute=0)
                continue
            if self.matches(cursor):
                found.append(cursor)
                cursor += timedelta(minutes=1)
            else:
                cursor += timedelta(minutes=1)
        if len(found) < count:
            raise ValueError("no further runs found within 5 years")
        return found


def parse_datetime(text):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"cannot parse datetime {text!r} "
                     "(expected YYYY-MM-DD HH:MM)")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print the next run times of a cron expression.")
    parser.add_argument("expression",
                        help='cron expression, e.g. "30 9 * * 1-5"')
    parser.add_argument("--count", "-n", type=int, default=5,
                        help="how many upcoming runs to show (default 5)")
    parser.add_argument("--from", dest="start", default=None,
                        help='start time "YYYY-MM-DD HH:MM" '
                             "(default: now)")
    args = parser.parse_args(argv)
    try:
        cron = CronExpression(args.expression)
        start = parse_datetime(args.start) if args.start else datetime.now()
        runs = cron.next_runs(start, args.count)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for run in runs:
        print(f"{run:%Y-%m-%d %H:%M} ({run:%A})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
