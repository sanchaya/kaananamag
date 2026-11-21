#!/usr/bin/env python3
"""Upload Kaanana issues missing from archive.org (ServantsOfKnowledge) and add them to issues.json.

Source: kaananamag.in WordPress API (category kaanana-pdf). An issue is "missing" when no
issues.json entry or IA item exists for its year-month. Metadata is cloned from the newest
existing issue. Usage: python3 sync_ia.py [--dry-run]   (needs `ia configure` credentials)
Also writes issues.json into every dir in MIRRORS.
"""
import calendar, copy, json, os, re, sys, tempfile, urllib.parse, urllib.request
from html import unescape
from internetarchive import get_item, search_items

API = "https://kaananamag.in/wp-json/wp/v2/"
MIRRORS = ["../kaananamag"]  # other copies of this project
UA = {"User-Agent": "Mozilla/5.0"}
DRY = "--dry-run" in sys.argv


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120)


def site_issues():
    cat = json.load(get(API + "categories?slug=kaanana-pdf"))[0]["id"]
    for page in range(1, 50):
        try:
            posts = json.load(get(f"{API}posts?categories={cat}&per_page=100&page={page}&_fields=date,title,content"))
        except urllib.error.HTTPError:  # past last page
            return
        for p in posts:
            pdfs = re.findall(r'https?://[^"\'<>\s]+\.pdf', p["content"]["rendered"])
            if pdfs:  # post date is the 1st of the issue month
                title = re.sub(r"\s*[–-]\s*|\s+", " ", unescape(p["title"]["rendered"])).strip()
                title = re.sub(r"\s*PDF$", "", title)
                if not title.startswith("ಕಾನನ"):
                    title = "ಕಾನನ " + title
                yield p["date"][:7], title, pdfs[0]


def main():
    data = json.load(open("issues.json"))
    books = data["books"]
    listed = {b["identifier"] for b in books}  # only IA items already in issues.json count as done
    have = {s["date"][:7] for s in map(dict, search_items("collection:ServantsOfKnowledge kaanana", fields=["identifier", "date"]))
            if s.get("date") and s["identifier"] in listed}
    tmpl_book = books[-1]
    tmpl = get_item(tmpl_book["identifier"]).item_metadata["metadata"]
    new = sorted((i for i in site_issues() if i[0] not in have), key=lambda i: i[0])
    print(f"{len(new)} missing issue(s): {[n[0] for n in new]}")

    for ym, title, pdf in new:
        year, month = ym.split("-")
        mname = calendar.month_name[int(month)]
        ident = f"kaanana-{mname.lower()}-{year}"
        md = {k: v for k, v in tmpl.items() if k in
              ("collection", "description", "publisher", "subject", "type")}
        md.update(title=title, alt_title=f"Kaanana {mname} {year}", date=ym, year=year, month=month,
                  mediatype="texts", language="Kannada")
        if ident in {b["identifier"] for b in books}:
            continue  # already listed (IA date field was just odd)
        print(f"- {ident}: {title} <- {pdf}")
        if DRY:
            continue
        on_ia = get_item(ident).exists  # e.g. uploaded by an interrupted run: only list it
        if not on_ia:
            path = os.path.join(tempfile.mkdtemp(), title.replace(" ", "-") + ".pdf")
            with open(path, "wb") as f:
                f.write(get(urllib.parse.quote(pdf, safe=":/%")).read())
            r = get_item(ident).upload(path, metadata=md, retries=5, verbose=True)
            if not all(x.status_code == 200 for x in r):
                sys.exit(f"upload failed for {ident}")
        b = copy.deepcopy(tmpl_book)
        b.update(identifier=ident, title=title, level=int(year), url=f"https://archive.org/details/{ident}",
                 cover=f"https://archive.org/services/img/{ident}")
        books.append(b)

    if new and not DRY:
        for d in [".", *MIRRORS]:
            with open(os.path.join(d, "issues.json"), "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")


if __name__ == "__main__":
    main()
