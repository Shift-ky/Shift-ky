import json, os, urllib.request, html
from collections import Counter
from pathlib import Path

USER = "Shift-ky"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "github-profile-cards"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def api(path):
    req = urllib.request.Request("https://api.github.com/" + path, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

user = api(f"users/{USER}")
repos = []
for page in range(1, 6):
    batch = api(f"users/{USER}/repos?per_page=100&page={page}&type=owner")
    repos.extend(batch)
    if len(batch) < 100:
        break
repos = [r for r in repos if not r.get("fork")]
stars = sum(r.get("stargazers_count", 0) for r in repos)
languages = Counter()
for repo in repos:
    try:
        languages.update(api(f"repos/{USER}/{repo['name']}/languages"))
    except Exception as e:
        print("Language lookup failed:", repo["name"], e)
top = languages.most_common(6)
Path("dist").mkdir(exist_ok=True)

def svg_card(title, lines, filename):
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="260" viewBox="0 0 480 260">',
      '<rect width="480" height="260" rx="18" fill="#0d1117" stroke="#164e63" stroke-width="2"/>',
      '<text x="24" y="44" font-family="Arial,sans-serif" font-size="23" font-weight="bold" fill="#22d3ee">' + html.escape(title) + '</text>',
      '<line x1="24" x2="456" y1="62" y2="62" stroke="#164e63"/>']
    for i, line in enumerate(lines[:7]):
        elements.append(f'<text x="25" y="{92+i*25}" font-family="Arial,sans-serif" font-size="17" fill="#cbd5e1">{html.escape(str(line))}</text>')
    elements.append('</svg>')
    Path("dist", filename).write_text("\n".join(elements), encoding="utf-8")

svg_card("GitHub | Estatísticas", [
    f"Repositórios públicos: {user.get('public_repos', 0)}",
    f"Estrelas recebidas: {stars}",
    f"Seguidores: {user.get('followers', 0)}",
    f"Seguindo: {user.get('following', 0)}",
    f"Projetos próprios analisados: {len(repos)}",
], "profile-stats.svg")
# Donut chart: language byte share across public, non-fork repositories.
import math
total = sum(languages.values())
palette = ["#22d3ee", "#818cf8", "#34d399", "#fbbf24", "#fb7185", "#c084fc", "#64748b"]
entries = languages.most_common(6)
remainder = total - sum(v for _, v in entries)
if remainder > 0:
    entries.append(("Outras", remainder))

svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="480" height="300" viewBox="0 0 480 300">',
       '<rect width="480" height="300" rx="18" fill="#0d1117" stroke="#164e63" stroke-width="2"/>',
       '<text x="24" y="42" font-family="Arial,sans-serif" font-size="22" font-weight="bold" fill="#22d3ee">Linguagens | Distribuição</text>',
       '<text x="24" y="64" font-family="Arial,sans-serif" font-size="12" fill="#94a3b8">Por volume de código nos repositórios públicos</text>']
if total:
    radius = 76
    circumference = 2 * math.pi * radius
    offset = 0
    for i, (name, amount) in enumerate(entries):
        fraction = amount / total
        length = fraction * circumference
        svg.append(f'<circle cx="132" cy="180" r="{radius}" fill="none" stroke="{palette[i]}" stroke-width="27" stroke-dasharray="{length:.3f} {circumference - length:.3f}" stroke-dashoffset="{-offset:.3f}" transform="rotate(-90 132 180)"/>')
        offset += length
        y = 104 + i * 27
        svg.append(f'<rect x="258" y="{y-11}" width="12" height="12" rx="3" fill="{palette[i]}"/>')
        svg.append(f'<text x="279" y="{y}" font-family="Arial,sans-serif" font-size="14" fill="#cbd5e1">{html.escape(name)}: {fraction * 100:.1f}%</text>')
    svg.append('<text x="132" y="174" text-anchor="middle" font-family="Arial,sans-serif" font-size="19" font-weight="bold" fill="#f8fafc">TOP</text>')
    svg.append('<text x="132" y="194" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#94a3b8">LINGUAGENS</text>')
else:
    svg.append('<text x="24" y="140" font-family="Arial,sans-serif" font-size="16" fill="#cbd5e1">Sem dados públicos de linguagens.</text>')
svg.append('</svg>')
Path("dist/profile-languages.svg").write_text("\\n".join(svg), encoding="utf-8")
