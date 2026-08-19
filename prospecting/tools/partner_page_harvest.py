#!/usr/bin/env python3
"""
partner_page_harvest.py - enumerate lead BUYERS from lead-seller "marketing partners" pages.

Why this works: TCPA consent disclosures must identify who may contact the consumer, so lead
sellers publish and maintain a page naming every buyer permitted to call. That page is a
self-updating, public list of confirmed lead buyers. Harvesting it weekly and diffing it turns
"who buys leads?" into a dated, sourced feed.

    # 1. discover the partner page from a quote-form URL
    python3 partner_page_harvest.py discover https://example-quotes.com/auto

    # 2. harvest names from a known partner page
    python3 partner_page_harvest.py harvest https://example-quotes.com/partners --seller example-quotes

    # 3. diff against the previous run -> newly added buyers are the outreach trigger
    python3 partner_page_harvest.py diff example-quotes

Stdlib only. Snapshots every fetch to ./snapshots/ because these pages change without notice
and the snapshot is your evidence if a prospect disputes the claim.
"""
import sys, os, re, json, csv, gzip, hashlib, datetime, urllib.request, urllib.parse
from html.parser import HTMLParser

BASE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(BASE, "snapshots")
DATA = os.path.join(BASE, "harvest_data")
UA = "Mozilla/5.0 (compatible; CiV-research/1.0; +prospect-research)"

# link text that typically leads from a consent checkbox to the buyer roster
PARTNER_LINK = re.compile(
    r"(marketing\s+partner|participating\s+(compan|provider|lender|insurer)|"
    r"our\s+partners?|partner\s+list|list\s+of\s+(compan|partner)|"
    r"authorized\s+(partner|seller)|network\s+of\s+(compan|partner))", re.I)

# the consent language itself - presence confirms this is a TCPA lead-capture form
CONSENT_HINT = re.compile(
    r"(prior\s+express\s+written\s+consent|autodial|automatic\s+telephone\s+dialing|"
    r"pre-?recorded|artificial\s+voice|consent\s+is\s+not\s+a\s+condition|"
    r"telephone\s+consumer\s+protection)", re.I)

# consent-capture platforms: presence => this domain ORIGINATES leads (seller/originator)
CAPTURE_SCRIPTS = {
    "TrustedForm": re.compile(r"(api|cert)\.trustedform\.com|trustedform\.js", re.I),
    "Jornaya/LeadiD": re.compile(r"create\.lidstatic\.com|leadid\.com|jornaya", re.I),
}

# obvious non-company noise in list markup
NOISE = re.compile(
    r"^(home|about|contact|privacy|terms|faq|blog|login|sign\s?in|menu|search|"
    r"back|next|close|all rights reserved|copyright|click here|learn more|read more)$", re.I)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self._href = None; self._buf = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs); self._href = d.get("href"); self._buf = []
    def handle_data(self, data):
        if self._href is not None: self._buf.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((" ".join("".join(self._buf).split()), self._href))
            self._href = None; self._buf = []


class Items(HTMLParser):
    """Collect candidate company names from list/table/link structures."""
    TARGET = {"li", "td", "a", "p", "span", "div"}
    def __init__(self):
        super().__init__(); self.items = []; self._stack = []
    def handle_starttag(self, tag, attrs):
        if tag in self.TARGET: self._stack.append([tag, []])
    def handle_data(self, data):
        if self._stack: self._stack[-1][1].append(data)
    def handle_endtag(self, tag):
        if self._stack and self._stack[-1][0] == tag:
            _, buf = self._stack.pop()
            t = " ".join("".join(buf).split())
            if t: self.items.append(t)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
    html = raw.decode("utf-8", "replace")
    os.makedirs(SNAP, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    key = hashlib.sha1(url.encode()).hexdigest()[:12]
    path = os.path.join(SNAP, f"{stamp}_{key}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- CiV snapshot | {url} | {datetime.datetime.now().isoformat()} -->\n{html}")
    return html, path


def looks_like_company(t):
    if not (2 < len(t) < 80) or NOISE.match(t): return False
    if t.count(" ") > 8: return False                      # sentence, not a name
    if re.search(r"[.!?]$", t) and " " in t: return False   # prose
    if not re.search(r"[A-Za-z]", t): return False
    letters = [c for c in t if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) < 0.05: return False
    return True


def cmd_discover(url):
    html, snap = fetch(url)
    print(f"snapshot: {snap}\n")
    if CONSENT_HINT.search(html):
        hits = sorted({m.group(0).lower() for m in CONSENT_HINT.finditer(html)})
        print(f"[+] TCPA consent language present: {', '.join(hits[:5])}")
    else:
        print("[-] no TCPA consent language found - may not be a lead-capture form")
    for name, rx in CAPTURE_SCRIPTS.items():
        if rx.search(html):
            print(f"[+] capture platform: {name}  => this domain ORIGINATES leads (seller)")
    p = Links(); p.feed(html)
    found = []
    for text, href in p.links:
        if href and (PARTNER_LINK.search(text or "") or PARTNER_LINK.search(href)):
            found.append((text, urllib.parse.urljoin(url, href)))
    uniq = {}
    for text, href in found:
        uniq.setdefault(href, text)
    print(f"\n[+] {len(uniq)} candidate partner-list link(s):")
    for href, text in uniq.items():
        print(f"    {href}")
        if text:
            print(f"        link text: {text!r}")
    if not uniq:
        print("    none found in <a> tags - the list may be in a modal or JS-rendered;")
        print("    open the consent checkbox link manually and pass that URL to `harvest`.")
    return uniq


def cmd_harvest(url, seller):
    html, snap = fetch(url)
    p = Items(); p.feed(html)
    seen, names = set(), []
    for t in p.items:
        t = t.strip(" ,;|·-–— ")
        k = re.sub(r"[^a-z0-9]", "", t.lower())
        if k and k not in seen and looks_like_company(t):
            seen.add(k); names.append(t)
    os.makedirs(DATA, exist_ok=True)
    today = datetime.date.today().isoformat()
    out = os.path.join(DATA, f"{seller}_{today}.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["company_name", "seller_source", "evidence_url",
                    "evidence_snapshot_path", "discovery_channel", "first_seen"])
        for n in names:
            w.writerow([n, seller, url, snap, "partner_page", today])
    print(f"[+] {len(names)} candidate buyers -> {out}")
    print(f"[+] snapshot: {snap}")
    print("\n    REVIEW MANUALLY before outreach - heuristics catch nav text and headings.")
    for n in names[:25]: print(f"      - {n}")
    if len(names) > 25: print(f"      ... +{len(names)-25} more")
    return out


def cmd_diff(seller):
    if not os.path.isdir(DATA): sys.exit("no harvest_data/ yet - run `harvest` first")
    runs = sorted(f for f in os.listdir(DATA) if f.startswith(seller + "_") and f.endswith(".csv"))
    if len(runs) < 2: sys.exit(f"need >=2 runs for {seller}; have {len(runs)}")
    def load(fn):
        with open(os.path.join(DATA, fn), encoding="utf-8") as f:
            return {r["company_name"] for r in csv.DictReader(f)}
    prev, cur = load(runs[-2]), load(runs[-1])
    added, removed = sorted(cur - prev), sorted(prev - cur)
    print(f"{seller}: {runs[-2]} -> {runs[-1]}")
    print(f"\n[+] {len(added)} ADDED  <- new lead buyers; highest-priority outreach trigger")
    for n in added: print(f"      + {n}")
    print(f"\n[-] {len(removed)} REMOVED  <- stopped buying, or rebranded")
    for n in removed: print(f"      - {n}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "discover": cmd_discover(arg)
    elif cmd == "harvest":
        seller = sys.argv[sys.argv.index("--seller")+1] if "--seller" in sys.argv \
                 else urllib.parse.urlparse(arg).netloc.replace("www.", "").split(".")[0]
        cmd_harvest(arg, seller)
    elif cmd == "diff": cmd_diff(arg)
    else: print(__doc__); sys.exit(1)
