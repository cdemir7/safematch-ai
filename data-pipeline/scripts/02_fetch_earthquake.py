from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = BASE_DIR / "sources" / "earthquake"
REPORTS_DIR = SOURCE_DIR / "district_reports"

REPORTS_PAGE_URL = (
    "https://depremzemin.ibb.istanbul/tr/"
    "olasi-deprem-kayip-tahminleri-ilce-kitapciklari"
)


def safe_filename(name: str) -> str:
    replacements = {
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ş": "s",
        "Ş": "S",
        "ü": "u",
        "Ü": "U",
        " ": "_",
        "/": "_",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    return "".join(
        character
        for character in name
        if character.isalnum() or character in ("_", "-")
    ).strip("_")


def get_pdf_links() -> list[tuple[str, str]]:
    response = requests.get(REPORTS_PAGE_URL, timeout=120)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    pdf_links: list[tuple[str, str]] = []

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if ".pdf" not in href.lower():
            continue

        title = link.get_text(" ", strip=True)

        if not title:
            title = Path(href.split("?")[0]).stem

        pdf_url = urljoin(REPORTS_PAGE_URL, href)
        pdf_links.append((title, pdf_url))

    unique_links = list(dict.fromkeys(pdf_links))

    print(f"PDF link count: {len(unique_links)}")

    if len(unique_links) != 39:
        raise ValueError(
            f"Expected 39 district reports, found {len(unique_links)}."
        )

    return unique_links


def download_pdf(title: str, url: str) -> None:
    filename = safe_filename(title) + ".pdf"
    destination = REPORTS_DIR / filename

    if destination.exists() and destination.stat().st_size > 0:
        print(f"Already exists: {filename}")
        return

    response = requests.get(url, timeout=180)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()

    if "pdf" not in content_type and not response.content.startswith(b"%PDF"):
        raise ValueError(f"Downloaded file is not a PDF: {url}")

    destination.write_bytes(response.content)

    print(
        f"Downloaded: {filename} "
        f"({destination.stat().st_size / 1024 / 1024:.1f} MB)"
    )


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    pdf_links = get_pdf_links()

    for index, (title, url) in enumerate(pdf_links, start=1):
        print(f"[{index}/39] {title}")
        download_pdf(title, url)

    downloaded_files = list(REPORTS_DIR.glob("*.pdf"))

    print()
    print(f"Downloaded PDF count: {len(downloaded_files)}")
    print(f"Saved directory: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
    