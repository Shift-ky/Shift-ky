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
total = sum(languages.values()) or 1
svg_card("Linguagens | Projetos públicos", [
    f"{name}: {size / total:.1%} do código" for name, size in top
] or ["Sem dados públicos de linguagens"], "profile-languages.svg")
