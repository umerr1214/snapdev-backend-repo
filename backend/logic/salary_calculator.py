from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import pandas as pd
import io
import csv

class SalaryCalculator:
    RATE_AM = Decimal('2000')
    RATE_PM = Decimal('1500')

    def next_boundary(self, dt):
        noon = dt.replace(hour=12, minute=0, second=0, microsecond=0)
        if dt < noon:
            return noon
        return (dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))

    def parse_iso_zoned(self, s):
        return datetime.fromisoformat(s)

    def rate_for(self, dt):
        return self.RATE_AM if dt.hour < 12 else self.RATE_PM

    def hms(self, total_seconds):
        s = int(round(total_seconds))
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        return h, m, sec

    def format_hms(self, total_seconds):
        h, m, s = self.hms(total_seconds)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def breakdown_str(self, am_seconds, pm_seconds):
        ph, pmn, ps = self.hms(pm_seconds)
        ah, amn, asec = self.hms(am_seconds)
        return f"1500 x {ph} hours {pmn} minutes {ps} seconds & 2000 x {ah} hours {amn} minutes {asec} seconds"

    def calculate(self, csv_contents):
        data = io.StringIO(csv_contents.decode("utf-8"))
        reader = csv.DictReader(data)
        workers = {}

        for row in reader:
            worker = (row.get("workers") or "").strip()
            if not worker:
                continue
            start_s = row.get("start_time")
            end_s = row.get("end_time")
            if not start_s or not end_s:
                continue
            
            try:
                start = self.parse_iso_zoned(start_s)
                end = self.parse_iso_zoned(end_s)
            except ValueError:
                # Handle cases where the timestamp is not in the correct format
                continue

            if end <= start:
                continue

            cur = start
            while cur < end:
                b = self.next_boundary(cur)
                seg_end = min(b, end)
                seg_seconds = (seg_end - cur).total_seconds()
                if worker not in workers:
                    workers[worker] = {"am_seconds": 0.0, "pm_seconds": 0.0}
                
                if self.rate_for(cur) == self.RATE_AM:
                    workers[worker]["am_seconds"] += seg_seconds
                else:
                    workers[worker]["pm_seconds"] += seg_seconds
                cur = seg_end

        rows = []
        for worker, d in sorted(workers.items(), key=lambda item: item.lower()):
            am_sec = Decimal(d["am_seconds"])
            pm_sec = Decimal(d["pm_seconds"])
            total_sec = am_sec + pm_sec

            payment = (am_sec * (self.RATE_AM / Decimal(3600))) + (pm_sec * (self.RATE_PM / Decimal(3600)))
            payment = payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            rows.append({
                "Worker": worker,
                "Total time": self.format_hms(total_sec),
                "Total payment": f"{payment}",
                "Payment breakdown": self.breakdown_str(am_sec, pm_sec),
            })
        
        return rows