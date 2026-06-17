from dataclasses import dataclass
from datetime import date


@dataclass
class SiteRow:
    name: str
    status: str
    http_status_code: int | None
    error_message: str | None


def generate_report(rows: list[SiteRow], report_date: date | None = None) -> str:
    """
    Build a plain-text monitoring report.

    Args:
        rows: One SiteRow per monitored website (results from today's run).
        report_date: The date to display in the header. Defaults to today.

    Returns:
        A formatted string ready to be sent as an email body.
    """
    if report_date is None:
        report_date = date.today()

    total = len(rows)
    healthy = sum(1 for r in rows if r.status == "online")
    failed = total - healthy

    lines: list[str] = [
        "=" * 50,
        "       Website Monitoring Report",
        "=" * 50,
        f"Date            : {report_date.isoformat()}",
        f"Total Websites  : {total}",
        f"Healthy         : {healthy}",
        f"Failed          : {failed}",
        "-" * 50,
    ]

    for row in rows:
        if row.status == "online":
            detail = str(row.http_status_code)
        else:
            detail = row.error_message or "Unknown error"

        status_label = "ONLINE " if row.status == "online" else "OFFLINE"
        lines.append(f"{row.name:<30} {status_label}  {detail}")

    lines.append("=" * 50)
    return "\n".join(lines)
