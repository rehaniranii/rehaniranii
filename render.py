"""Render the profile README cards into cards/*.svg.

    python render.py            # animated cards
    STATIC=1 python render.py   # final frame only, for screenshots

Reads data/github.json (refreshed daily by .github/workflows/cards.yml).
Needs: pip install fonttools
"""
import base64, collections, datetime as dt, html, json, os, sys
from pathlib import Path
from fontTools.subset import main as pyftsubset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).parent
STATIC = os.environ.get("STATIC") == "1"

NAME = "Rehan Irani"
HANDLE = "@rehaniranii"
ABOUT = "IT student building with code, AI, and curiosity."
SUBLINE = "Mumbai, India  ·  K.J. Somaiya School of Engineering"
PORTRAIT = ROOT / "assets/portrait.jpg"  # delete the file to drop the portrait
SITE = "https://rehan-portfolio-rosy.vercel.app"
TILES = [  # (file, label, value, href) -- href is used by README.md
    ("tile-site", "Portfolio", "rehan-portfolio", SITE),
    ("tile-linkedin", "LinkedIn", "in/rehan-irani", "https://www.linkedin.com/in/rehan-irani"),
    ("tile-blog", "Writing", "Blog & notes", SITE + "/blog"),
]
FEATURED = {  # owner/repo (yours, or one you've contributed to) -> blurb, used when the GitHub description is empty
    "rehaniranii/margin.pdf": "A free, standalone PDF workspace for editing existing text in place, powered by MuPDF in WebAssembly. No backend, no accounts.",
    "parthpalav/kakashi": "Check a token before you buy it: a pre-trade risk check for Hedera tokens that spends only inside a mandate a verified human approved.",
    "rehaniranii/Morrow": "Takes a first-time investor from \u201cwhere do I even start?\u201d to a one-page financial blueprint. Honest, illustrative maths, no stock tips.",
}

# Colours and fonts from the portfolio site (zinc scale + link blue, Geist / Geist Mono).
LIGHT = dict(bg="#ffffff", fg="#09090b", muted="#71717a", line="#e4e4e7", surface="#f4f4f5", brand="#1d4ed8")
DARK = dict(bg="#09090b", fg="#fafafa", muted="#a1a1aa", line="#27272a", surface="#18181b", brand="#3b82f6")
FONTS = {"sans": "Geist-Regular.ttf", "semi": "Geist-SemiBold.ttf", "mono": "GeistMono-Regular.ttf"}
_ttf = {k: TTFont(ROOT / "fonts" / f) for k, f in FONTS.items()}
W = 840  # full-width card


def text_width(s, font, size):
    f = _ttf[font]
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in s) * size / f["head"].unitsPerEm


def wrap(s, font, size, width):
    lines, cur = [], ""
    for word in s.split():
        if cur and text_width(cur + " " + word, font, size) > width:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    return lines + [cur] if cur else lines


class Card:
    def __init__(self, w, h, title, delay):
        self.w, self.h, self.title, self.base = w, h, title, delay
        self.body, self.chars = [], collections.defaultdict(set)

    def text(self, x, y, s, font="sans", size=14, cls="fg", anim="up", delay=0.0, extra=""):
        self.chars[font] |= set(s)
        self.body.append(f'<text x="{x:.1f}" y="{y:.1f}" class="{font} {cls}{self.a(anim)}" font-size="{size}"'
                         f'{self.d(delay)} {extra}>{html.escape(s)}</text>')

    def a(self, anim):
        return f" a-{anim}" if anim else ""

    def d(self, delay):
        return f' style="animation-delay:{self.base + delay:.2f}s"'

    def smil(self, attr, frm, to, delay, dur=1.2):
        """SMIL <animate>; the element's own attribute must already hold the final value."""
        if STATIC:
            return ""
        return (f'<animate attributeName="{attr}" from="{frm}" to="{to}" begin="{self.base + delay:.2f}s" '
                f'dur="{dur}s" fill="freeze" calcMode="spline" keySplines=".2 .7 .2 1" keyTimes="0;1"/>'
                # hold the start value until begin, so the element doesn't flash its final state first
                f'<set attributeName="{attr}" to="{frm}" begin="0s" end="{self.base + delay:.2f}s"/>')

    def add(self, s):
        self.body.append(s)

    def svg(self):
        faces = ""
        for font, chars in self.chars.items():
            tmp = ROOT / f".subset-{font}.woff"
            pyftsubset([str(ROOT / "fonts" / FONTS[font]), "--text=" + "".join(sorted(chars)) + " ",
                        "--flavor=woff", "--layout-features=kern,liga", "--drop-tables+=meta", f"--output-file={tmp}"])
            woff = tmp.read_bytes()
            tmp.unlink()
            faces += (f"@font-face{{font-family:'{font}';src:url(data:font/woff;base64,"
                      f"{base64.b64encode(woff).decode()}) format('woff')}}")
        theme = lambda c: "".join(f"--{k}:{v};" for k, v in c.items())
        css = f"""{faces}
svg{{{theme(LIGHT)}}}
@media (prefers-color-scheme:dark){{svg{{{theme(DARK)}}}}}
.sans{{font-family:'sans',system-ui,sans-serif}}.semi{{font-family:'semi',system-ui,sans-serif;font-weight:600}}
.mono{{font-family:'mono',ui-monospace,monospace;font-feature-settings:'zero' 1,'tnum' 1}}
.fg{{fill:var(--fg)}}.muted{{fill:var(--muted)}}.brand{{fill:var(--brand)}}
.frame{{fill:var(--bg);stroke:var(--line)}}.surface{{fill:var(--surface)}}.lined{{stroke:var(--line)}}"""
        if not STATIC:
            css += """
@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}
.a-up,.a-fade,.a-grow,.a-pop{animation:.8s cubic-bezier(.2,.7,.2,1) both}
.a-up{animation-name:up}.a-fade{animation-name:fade}.a-grow{animation-name:grow}.a-pop{animation-name:pop}
.a-grow,.a-pop{transform-box:fill-box;transform-origin:50% 100%}.a-pop{transform-origin:center}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important}
  /* author !important beats SMIL on presentation attributes */
  .smil-dash{stroke-dashoffset:0!important}.smil-op{opacity:1!important}
}"""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{html.escape(self.title)}">'
                f"<title>{html.escape(self.title)}</title><style>{css}</style>"
                f'<rect class="frame" x=".5" y=".5" width="{self.w - 1}" height="{self.h - 1}" rx="12"/>'
                + "".join(self.body) + "</svg>")


# ---------- data ----------

def stats(days):
    """days: [(date, count)] sorted ascending, last one is today."""
    active = sum(1 for _, c in days if c)
    busiest = max(days, key=lambda d: d[1])
    longest = run = 0
    for _, c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current, i = 0, len(days) - 1
    if days and not days[i][1]:
        i -= 1  # today doesn't break the streak until it's over
    while i >= 0 and days[i][1]:
        current, i = current + 1, i - 1
    return dict(active=active, busiest=busiest, longest=longest, current=current)


def _check():
    d = lambda *cs: [(dt.date(2026, 1, i + 1), c) for i, c in enumerate(cs)]
    s = stats(d(1, 0, 2, 3, 0))
    assert (s["current"], s["longest"], s["active"], s["busiest"][1]) == (2, 2, 3, 3), s
    assert stats(d(1, 1, 1))["current"] == 3 and stats(d(0, 0))["current"] == 0


# ---------- cards ----------

def hero(delay):
    c = Card(W, 220, f"{NAME} — {ABOUT}", delay)
    tx = 44
    if PORTRAIT.exists():
        b64 = base64.b64encode(PORTRAIT.read_bytes()).decode()
        c.add('<clipPath id="pc"><circle cx="126" cy="110" r="72"/></clipPath>'
              f'<g class="a-pop"{c.d(0)}><circle cx="126" cy="110" r="78" fill="none" stroke="var(--line)"/>'
              f'<image href="data:image/jpeg;base64,{b64}" x="54" y="38" width="144" height="144" '
              'clip-path="url(#pc)" preserveAspectRatio="xMidYMid slice"/></g>'
              # brand arc that draws itself around the portrait
              f'<circle class="smil-dash" cx="126" cy="110" r="78" fill="none" stroke="var(--brand)" stroke-width="2" '
              f'stroke-linecap="round" pathLength="100" stroke-dasharray="28 72" stroke-dashoffset="-61" '
              f'transform="rotate(-90 126 110)">{c.smil("stroke-dashoffset", 39, -61, .3, 1.6)}</circle>')
        tx = 240
    c.text(tx, 66, HANDLE, "mono", 13, "muted", delay=.1)
    c.text(tx, 112, NAME, "semi", 44, "fg", delay=.2, extra='letter-spacing="-1"')
    c.add(f'<line class="smil-dash" x1="{tx + 1.5}" y1="128" x2="{tx + 56}" y2="128" stroke="var(--brand)" '
          f'stroke-width="3" stroke-linecap="round" pathLength="100" stroke-dasharray="100" stroke-dashoffset="0">'
          f'{c.smil("stroke-dashoffset", 100, 0, .5)}</line>')
    c.text(tx, 160, ABOUT, "sans", 18, "fg", delay=.45)
    c.text(tx, 186, SUBLINE, "mono", 12, "muted", delay=.6)
    return c


def tile(label, value, delay):
    c = Card(270, 104, f"{label}: {value}", delay)
    c.text(22, 38, label.upper(), "mono", 11, "muted", delay=0, extra='letter-spacing="1.2"')
    c.text(22, 72, value, "semi", 19, "fg", delay=.1)
    c.add(f'<g class="a-pop"{c.d(.25)}><circle cx="236" cy="34" r="13" class="surface"/>'
          '<path d="M231 39l10-10M233 29h8v8" fill="none" stroke="var(--brand)" stroke-width="1.6" '
          'stroke-linecap="round" stroke-linejoin="round"/></g>')
    return c


def monthly(days, s, delay):
    by_month = collections.OrderedDict()
    for d, n in days:
        by_month[d.strftime("%Y-%m")] = by_month.get(d.strftime("%Y-%m"), 0) + n
    months = list(by_month.items())[-12:]
    total = sum(n for _, n in days)
    c = Card(W, 300, f"{total} contributions in the last year", delay)
    c.text(32, 46, "Contributions per month", "semi", 17, "fg", delay=0)
    c.text(32, 68, f"{total} in the last year", "mono", 12, "muted", delay=.05)

    x0, base, chart_h, bw, gap = 32, 250, 150, 30, 12
    peak = max(n for _, n in months) or 1
    for i, (m, n) in enumerate(months):
        x, h = x0 + i * (bw + gap), max(2, chart_h * n / peak)
        top = n == peak and n > 0
        c.add(f'<rect class="surface" x="{x}" y="{base - chart_h}" width="{bw}" height="{chart_h}" rx="4"/>'
              f'<rect class="a-grow" x="{x}" y="{base - h:.1f}" width="{bw}" height="{h:.1f}" rx="4" '
              f'fill="var(--brand)" opacity="{1 if top else .55}"{c.d(.2 + i * .06)}/>')
        if n:
            c.text(x + bw / 2, base - h - 7, str(n), "mono", 10, "fg" if top else "muted", "fade",
                   .5 + i * .06, 'text-anchor="middle"')
        c.text(x + bw / 2, base + 20, dt.date.fromisoformat(m + "-01").strftime("%b"), "mono", 10, "muted",
               "fade", .2 + i * .06, 'text-anchor="middle"')

    sx = x0 + 12 * (bw + gap) + 24
    c.add(f'<line class="lined" x1="{sx - 12}" y1="40" x2="{sx - 12}" y2="270"/>')
    b_date, b_n = s["busiest"]
    rows = [("Current streak", f'{s["current"]} day' + ("" if s["current"] == 1 else "s")),
            ("Longest streak", f'{s["longest"]} days'),
            ("Active days", f'{s["active"]} / {len(days)}'),
            ("Busiest day", f'{b_n} on {b_date.strftime("%b %-d")}')]
    for i, (k, v) in enumerate(rows):
        y = 64 + i * 56
        c.text(sx, y, k.upper(), "mono", 10, "muted", delay=.9 + i * .12, extra='letter-spacing="1"')
        c.text(sx, y + 24, v, "semi", 20, "brand" if i == 0 else "fg", delay=.95 + i * .12)
    if s["current"]:  # live dot next to an unbroken streak
        dot_x = sx + text_width("CURRENT STREAK", "mono", 10) + 14 + 10  # 14 letter-spacing gaps of 1px
        c.add(f'<circle class="smil-op" cx="{dot_x:.1f}" cy="60.5" r="3.5" fill="var(--brand)">'
              + ("" if STATIC else f'<animate attributeName="opacity" values="1;.25;1" dur="2s" '
                                   f'begin="{c.base + 1.2:.2f}s" repeatCount="indefinite"/>') + "</circle>")
    return c


def repo_card(r, delay):
    desc = r["description"] or FEATURED[r["nameWithOwner"]]
    title = r["nameWithOwner"].removeprefix(HANDLE[1:] + "/")
    lines = wrap(desc, "sans", 15, W - 80)[:2]
    c = Card(W, 92 + 22 * len(lines) + 34, f'{title}: {desc}', delay)
    c.add(f'<g class="a-pop"{c.d(0)}><rect x="32" y="32" width="28" height="28" rx="7" class="surface"/>'
          '<path d="M41 39h10v14l-5-3-5 3z" fill="none" stroke="var(--brand)" stroke-width="1.6" '
          'stroke-linejoin="round"/></g>')
    c.text(74, 53, title, "semi", 20, "fg", delay=.08)
    for i, line in enumerate(lines):
        c.text(32, 92 + i * 22, line, "sans", 15, "muted", delay=.18 + i * .06)
    y = 92 + 22 * len(lines) + 10
    x = 32
    if r["primaryLanguage"]:
        lang = r["primaryLanguage"]
        c.add(f'<circle class="a-pop" cx="{x + 5}" cy="{y - 4}" r="5" fill="{lang["color"] or "var(--muted)"}"'
              f'{c.d(.35)}/>')
        c.text(x + 16, y, lang["name"], "mono", 12, "muted", delay=.35)
        x += 30 + text_width(lang["name"], "mono", 12)
    pushed = dt.date.fromisoformat(r["pushedAt"][:10]).strftime("updated %b %Y")
    plural = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")
    meta = f'{plural(r["stargazerCount"], "star")}  ·  {plural(r["forkCount"], "fork")}  ·  {pushed}'
    c.text(x, y, meta, "mono", 12, "muted", delay=.4)
    return c


def graph(weeks, delay):
    cell, gap, x0, y0 = 11, 3, 40, 84
    c = Card(W, y0 + 7 * (cell + gap) + 48, "Contribution graph, last 12 months", delay)
    c.text(32, 46, "Contribution graph", "semi", 17, "fg", delay=0)
    level = {"NONE": 0, "FIRST_QUARTILE": .3, "SECOND_QUARTILE": .5, "THIRD_QUARTILE": .75, "FOURTH_QUARTILE": 1}
    last_month = None
    for wi, w in enumerate(weeks):
        x = x0 + wi * (cell + gap)
        cells = ""
        for d in w["contributionDays"]:
            wd = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday first, like GitHub
            o = level[d["contributionLevel"]]
            fill = f'fill="var(--brand)" opacity="{o}"' if o else 'class="surface"'
            cells += f'<rect x="{x}" y="{y0 + wd * (cell + gap)}" width="{cell}" height="{cell}" rx="2.5" {fill}/>'
        # columns sweep in left to right
        c.add(f'<g class="a-fade"{c.d(.1 + wi * .025)}>{cells}</g>')
        first = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != last_month and first.day <= 7 and wi < len(weeks) - 2:
            c.text(x, y0 - 10, first.strftime("%b"), "mono", 10, "muted", "fade", .1 + wi * .025)
        last_month = first.month
    for i, lbl in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        c.text(x0 - 8, y0 + i * (cell + gap) + 9, lbl, "mono", 9, "muted", "fade", .1, 'text-anchor="end"')
    ly = y0 + 7 * (cell + gap) + 22
    lx = W - 40 - 5 * (cell + 3) - 40
    c.text(lx - 8, ly + 9, "Less", "mono", 10, "muted", "fade", 1.5, 'text-anchor="end"')
    for i, o in enumerate([0, .3, .5, .75, 1]):
        fill = f'fill="var(--brand)" opacity="{o}"' if o else 'fill="var(--surface)"'
        c.add(f'<rect class="a-pop" x="{lx + i * (cell + 3)}" y="{ly}" width="{cell}" height="{cell}" rx="2.5" '
              f'{fill}{c.d(1.5 + i * .05)}/>')
    c.text(lx + 5 * (cell + 3) + 4, ly + 9, "More", "mono", 10, "muted", "fade", 1.75)
    return c


def main():
    _check()
    user = json.loads((ROOT / "data/github.json").read_text())["data"]["user"]
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [(dt.date.fromisoformat(d["date"]), d["contributionCount"]) for w in weeks for d in w["contributionDays"]]
    repos = {r["nameWithOwner"]: r for k in ("repositories", "repositoriesContributedTo") for r in user[k]["nodes"]}
    missing = [n for n in FEATURED if n not in repos]
    if missing:
        sys.exit(f"featured repos not found in data/github.json: {missing}")

    # base delays stagger the stack so the page plays top to bottom
    cards = {"hero": hero(0)}
    for i, (f, label, value, _) in enumerate(TILES):
        cards[f] = tile(label, value, .7 + i * .15)
    cards["monthly"] = monthly(days, stats(days), 1.2)
    for i, name in enumerate(FEATURED):
        cards[f"repo-{name.split('/')[1].lower()}"] = repo_card(repos[name], 2.0 + i * .3)
    cards["graph"] = graph(weeks, 2.0 + len(FEATURED) * .3)

    out = ROOT / "cards"
    out.mkdir(exist_ok=True)
    for name, card in cards.items():
        (out / f"{name}.svg").write_text(card.svg())
    print(f"wrote {len(cards)} cards to {out}{' (static)' if STATIC else ''}")


if __name__ == "__main__":
    main()
