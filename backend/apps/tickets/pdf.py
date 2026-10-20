"""Private, offline HTML rendering. Only explicitly supplied assets may be fetched."""

import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import qrcode
from django.conf import settings
from django.template.loader import render_to_string

from apps.core.storage import get_storage


def render_order_pdf(order, tickets, *, sample=False):
    from weasyprint import HTML

    assets = {}
    asset_root = Path(__file__).parent / "assets"
    for path in asset_root.iterdir():
        if path.suffix in (".ttf", ".png"):
            assets[f"asset:{path.name}"] = path.read_bytes()
    snapshot = order.snapshot
    banner_key = snapshot.get("banner_key")
    if banner_key:
        assets["asset:banner"] = get_storage().read(banner_key)
    items = {item["category_id"]: item for item in snapshot["items"]}
    pages = []
    for ticket in tickets:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4, box_size=12)
        qr.add_data(ticket.qr_token)
        qr.make(fit=True)
        stream = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(stream, format="PNG")
        uri = f"asset:qr-{ticket.position}"
        assets[uri] = stream.getvalue()
        pages.append(
            {"ticket": ticket, "category": items[str(ticket.category_id)]["name"], "qr": uri}
        )

    def fetch(url, **kwargs):
        if url not in assets:
            raise ValueError("External PDF assets are disabled.")
        return {"string": assets[url]}

    local = ZoneInfo("Asia/Dhaka")
    context = {
        "order": order,
        "pages": pages,
        "sample": sample,
        "start": datetime.fromisoformat(snapshot["starts_at"])
        .astimezone(local)
        .strftime("%d %B %Y, %I:%M %p"),
        "end": datetime.fromisoformat(snapshot["ends_at"])
        .astimezone(local)
        .strftime("%d %B %Y, %I:%M %p"),
        "support": settings.SUPPORT_EMAIL,
        "has_banner": bool(banner_key),
    }
    document = HTML(
        string=render_to_string("tickets/order.html", context), url_fetcher=fetch
    ).render()
    if len(document.pages) != len(pages):
        raise ValueError("Ticket layout overflow; PDF was not delivered.")
    return document.write_pdf()
