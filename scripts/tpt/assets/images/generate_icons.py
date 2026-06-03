"""
BrightOwl Learning — SVG Icon Generator
Generates cute line-art icons (style dessin d'enfant) for TPT worksheets.
All icons: 80x80px viewBox, black strokes, no fill, rounded style.
"""
from pathlib import Path

OUT = Path(__file__).parent

def svg_wrap(content, size=80):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <style>path,circle,ellipse,rect,line,polyline,polygon{{stroke:#2C3E50;stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round;fill:none}}</style>
  {content}
</svg>'''

# ── OWL (mascotte BrightOwl) ─────────────────────────────────────────────────
owl = svg_wrap("""
  <!-- corps -->
  <ellipse cx="40" cy="50" rx="22" ry="26"/>
  <!-- tête -->
  <circle cx="40" cy="26" r="18"/>
  <!-- oreilles/touffes -->
  <path d="M26,12 L22,4 L30,10"/>
  <path d="M54,12 L58,4 L50,10"/>
  <!-- yeux -->
  <circle cx="33" cy="24" r="6"/>
  <circle cx="47" cy="24" r="6"/>
  <circle cx="33" cy="24" r="2.5" style="fill:#2C3E50"/>
  <circle cx="47" cy="24" r="2.5" style="fill:#2C3E50"/>
  <!-- bec -->
  <path d="M37,30 L40,34 L43,30 Z" style="fill:#2C3E50"/>
  <!-- ailes -->
  <path d="M18,42 Q10,50 14,60 Q20,55 18,42"/>
  <path d="M62,42 Q70,50 66,60 Q60,55 62,42"/>
  <!-- pattes -->
  <path d="M32,74 L30,80 M36,75 L34,81 M40,75 L40,81"/>
  <path d="M48,74 L50,80 M44,75 L46,81 M40,75 L40,81"/>
  <!-- ventre rayures -->
  <path d="M32,52 Q40,55 48,52"/>
  <path d="M30,58 Q40,62 50,58"/>
  <!-- chapeau de diplômé -->
  <rect x="26" y="8" width="28" height="5" rx="1" style="fill:#2C3E50"/>
  <path d="M40,8 L40,2"/>
  <circle cx="40" cy="2" r="2" style="fill:#2C3E50"/>
""")

# ── PUMPKIN (halloween) ────────────────────────────────────────────────────────
pumpkin = svg_wrap("""
  <!-- tige -->
  <path d="M40,8 Q44,4 48,6" stroke-width="3"/>
  <!-- corps principal -->
  <ellipse cx="40" cy="46" rx="28" ry="26"/>
  <!-- côtes -->
  <path d="M28,22 Q20,46 28,68"/>
  <path d="M52,22 Q60,46 52,68"/>
  <path d="M36,18 Q32,46 36,72"/>
  <path d="M44,18 Q48,46 44,72"/>
  <!-- yeux triangles -->
  <path d="M28,38 L34,32 L40,38 Z" style="fill:#2C3E50"/>
  <path d="M40,38 L46,32 L52,38 Z" style="fill:#2C3E50"/>
  <!-- nez -->
  <path d="M38,46 L40,42 L42,46 Z" style="fill:#2C3E50"/>
  <!-- sourire dentelé -->
  <path d="M26,56 L30,52 L34,56 L38,52 L42,56 L46,52 L50,56 L54,52 L58,56"/>
""")

# ── PENCIL (back-to-school) ─────────────────────────────────────────────────
pencil = svg_wrap("""
  <!-- corps du crayon -->
  <rect x="28" y="10" width="24" height="52" rx="4"/>
  <!-- pointe -->
  <path d="M28,62 L40,78 L52,62"/>
  <!-- gomme -->
  <rect x="28" y="10" width="24" height="10" rx="4" style="fill:#E0E0E0"/>
  <line x1="28" y1="20" x2="52" y2="20"/>
  <!-- ligne centrale -->
  <line x1="40" y1="10" x2="40" y2="62" stroke-width="1.5"/>
  <!-- mine -->
  <path d="M36,68 L40,78 L44,68" style="fill:#2C3E50"/>
  <!-- visage -->
  <circle cx="36" cy="38" r="2.5" style="fill:#2C3E50"/>
  <circle cx="44" cy="38" r="2.5" style="fill:#2C3E50"/>
  <path d="M35,45 Q40,50 45,45"/>
""")

# ── APPLE (classroom) ─────────────────────────────────────────────────────────
apple = svg_wrap("""
  <!-- feuille -->
  <path d="M40,12 Q50,6 52,14 Q46,14 40,12"/>
  <!-- tige -->
  <path d="M40,12 L40,6"/>
  <!-- corps pomme -->
  <path d="M40,18 Q20,18 18,38 Q16,60 30,70 Q36,74 40,72 Q44,74 50,70 Q64,60 62,38 Q60,18 40,18"/>
  <!-- reflet -->
  <path d="M26,28 Q30,24 36,26" stroke-width="1.5"/>
  <!-- visage -->
  <circle cx="34" cy="42" r="2.5" style="fill:#2C3E50"/>
  <circle cx="46" cy="42" r="2.5" style="fill:#2C3E50"/>
  <path d="M33,50 Q40,56 47,50"/>
  <!-- joues -->
  <circle cx="28" cy="48" r="4" stroke-width="1" style="stroke:#E0E0E0"/>
  <circle cx="52" cy="48" r="4" stroke-width="1" style="stroke:#E0E0E0"/>
""")

# ── STAR (achievement) ────────────────────────────────────────────────────────
star = svg_wrap("""
  <path d="M40,8 L46,28 L68,28 L51,42 L57,62 L40,50 L23,62 L29,42 L12,28 L34,28 Z"/>
  <!-- visage -->
  <circle cx="34" cy="35" r="2.5" style="fill:#2C3E50"/>
  <circle cx="46" cy="35" r="2.5" style="fill:#2C3E50"/>
  <path d="M33,42 Q40,47 47,42"/>
""")

# ── SNOWFLAKE (winter/christmas) ──────────────────────────────────────────────
snowflake = svg_wrap("""
  <!-- axes principaux -->
  <line x1="40" y1="8" x2="40" y2="72"/>
  <line x1="8" y1="40" x2="72" y2="40"/>
  <line x1="17" y1="17" x2="63" y2="63"/>
  <line x1="63" y1="17" x2="17" y2="63"/>
  <!-- branches -->
  <path d="M40,18 L34,24 M40,18 L46,24"/>
  <path d="M40,62 L34,56 M40,62 L46,56"/>
  <path d="M18,40 L24,34 M18,40 L24,46"/>
  <path d="M62,40 L56,34 M62,40 L56,46"/>
  <path d="M23,23 L23,30 M23,23 L30,23"/>
  <path d="M57,23 L57,30 M57,23 L50,23"/>
  <path d="M23,57 L23,50 M23,57 L30,57"/>
  <path d="M57,57 L57,50 M57,57 L50,57"/>
  <!-- centre -->
  <circle cx="40" cy="40" r="4" style="fill:#2C3E50"/>
""")

# ── HEART (valentine) ──────────────────────────────────────────────────────────
heart = svg_wrap("""
  <path d="M40,68 Q14,50 14,32 Q14,16 28,14 Q36,12 40,22 Q44,12 52,14 Q66,16 66,32 Q66,50 40,68 Z"/>
  <!-- visage -->
  <circle cx="33" cy="36" r="2.5" style="fill:#2C3E50"/>
  <circle cx="47" cy="36" r="2.5" style="fill:#2C3E50"/>
  <path d="M32,44 Q40,50 48,44"/>
""")

# ── BUTTERFLY (spring) ─────────────────────────────────────────────────────────
butterfly = svg_wrap("""
  <!-- ailes hautes -->
  <path d="M40,34 Q24,10 10,20 Q6,34 20,42 Q30,46 40,40"/>
  <path d="M40,34 Q56,10 70,20 Q74,34 60,42 Q50,46 40,40"/>
  <!-- ailes basses -->
  <path d="M40,44 Q22,42 16,56 Q18,70 30,64 Q36,60 40,50"/>
  <path d="M40,44 Q58,42 64,56 Q62,70 50,64 Q44,60 40,50"/>
  <!-- corps -->
  <ellipse cx="40" cy="40" rx="4" ry="16"/>
  <!-- antennes -->
  <path d="M38,26 Q30,16 26,10"/>
  <circle cx="26" cy="10" r="2.5" style="fill:#2C3E50"/>
  <path d="M42,26 Q50,16 54,10"/>
  <circle cx="54" cy="10" r="2.5" style="fill:#2C3E50"/>
""")

# ── ROCKET (space/science) ─────────────────────────────────────────────────────
rocket = svg_wrap("""
  <!-- corps -->
  <path d="M40,8 Q26,20 24,50 L56,50 Q54,20 40,8 Z"/>
  <!-- hublot -->
  <circle cx="40" cy="34" r="8"/>
  <!-- ailerons -->
  <path d="M24,50 L14,66 L26,60"/>
  <path d="M56,50 L66,66 L54,60"/>
  <!-- flammes -->
  <path d="M30,60 Q36,72 40,68 Q44,72 50,60"/>
  <path d="M34,60 Q38,76 40,72 Q42,76 46,60" stroke-width="1.5"/>
  <!-- étoiles -->
  <path d="M12,20 L13,16 L14,20 L18,20 L15,22 L16,26 L13,24 L10,26 L11,22 L8,20 Z" style="fill:#2C3E50" stroke-width="1"/>
  <path d="M62,14 L63,11 L64,14 L67,14 L65,16 L66,19 L63,17 L60,19 L61,16 L59,14 Z" style="fill:#2C3E50" stroke-width="1"/>
""")

icons = {
    "owl": owl,
    "pumpkin": pumpkin,
    "pencil": pencil,
    "apple": apple,
    "star": star,
    "snowflake": snowflake,
    "heart": heart,
    "butterfly": butterfly,
    "rocket": rocket,
}

for name, svg in icons.items():
    path = OUT / f"{name}.svg"
    path.write_text(svg, encoding="utf-8")
    print(f"✓ {name}.svg → {len(svg)} chars")

print(f"\n{len(icons)} icônes générées dans {OUT}")
