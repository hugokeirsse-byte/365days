"""Module 10 — Arbitragiste Cross-canal.

À partir d'une opportunité (signal détecté sur 1 canal), génère la liste
des pipelines de production à déclencher en cascade sur les autres canaux.

Lit la matrice de réplication définie en code (cf. REVERSE_ENGINEERING_BESTSELLERS.md §4.1).
Aucun appel LLM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# Matrice de réplication : type de signal → pipelines à déclencher.
# Refléte REVERSE_ENGINEERING_BESTSELLERS.md §4.1.
REPLICATION_MATRIX: dict[str, list[str]] = {
    "kdp_coloring_bestseller": [
        "produce_merch_batch",      # extraire 5 visuels iconiques → t-shirts/stickers/posters/mug
        "produce_video_faceless",   # vidéo "process coloring" sur TikTok
        "produce_progeny_pack",     # si niche compatible PD
    ],
    "merch_tshirt_bestseller": [
        "produce_coloring_book",    # livre coloring avec variantes du design
        "produce_kdp_low_content",  # carnet/poster set inspiré
        "produce_ar_filter",        # filter qui applique l'esthétique
    ],
    "pinterest_trend": [
        "produce_coloring_book",
        "produce_merch_batch",
        "produce_kdp_low_content",
        "produce_card_deck",        # si niche métier
    ],
    "tiktok_trend_ephemeral": [
        "produce_merch_batch",      # vitesse, priorité stickers
        "produce_ar_filter",        # exploit éphémère, AR filter rapide
        "produce_coloring_book",    # déclinaison lente en backup
    ],
    "mobile_game_niche_signal": [
        # On ne clone pas, on dérive éditorial.
        "produce_merch_batch_fanart_transformative",
        "produce_kdp_guide",
    ],
    "domain_public_acquisition": [
        "produce_coloring_book",    # ex: Köhler, Audubon
        "produce_merch_batch",      # posters / mugs / t-shirts
        "produce_kdp_collector",
        "produce_card_deck_educational",  # ex: cartes plantes
    ],
    "progeny_combo_validated": [
        "produce_sticker_pack",     # priorité Iconic Offspring
        "produce_coloring_book",
        "produce_kdp_mini_book",
        "produce_merch_batch",
        "produce_ar_filter",
    ],
}

# Mapping signal_type → brand_id par défaut.
DEFAULT_BRAND_BY_SIGNAL: dict[str, str] = {
    "kdp_coloring_bestseller": "modern_cozy",
    "merch_tshirt_bestseller": "modern_cozy",
    "pinterest_trend": "modern_cozy",
    "tiktok_trend_ephemeral": "iconic_offspring",
    "mobile_game_niche_signal": "modern_cozy",
    "domain_public_acquisition": "heritage_coloring",
    "progeny_combo_validated": "iconic_offspring",
}


@dataclass
class PollinationPlan:
    source_signal_type: str
    niche: str
    brand_id: str
    primary_pipeline: str
    cascade_pipelines: list[str]

    def to_dict(self) -> dict:
        return {
            "source_signal_type": self.source_signal_type,
            "niche": self.niche,
            "brand_id": self.brand_id,
            "primary_pipeline": self.primary_pipeline,
            "cascade_pipelines": self.cascade_pipelines,
        }


def primary_pipeline_for(signal_type: str) -> str:
    """Le pipeline qui correspond au format natif du signal."""
    return {
        "kdp_coloring_bestseller": "produce_coloring_book",
        "merch_tshirt_bestseller": "produce_merch_batch",
        "pinterest_trend": "produce_merch_batch",  # le plus rapide à shipper
        "tiktok_trend_ephemeral": "produce_merch_batch",
        "mobile_game_niche_signal": "produce_merch_batch_fanart_transformative",
        "domain_public_acquisition": "produce_coloring_book",
        "progeny_combo_validated": "produce_progeny_pack",
    }.get(signal_type, "produce_merch_batch")


def plan_pollination(
    signal_type: str,
    niche: str,
    brand_id: str | None = None,
    exclude_pipelines: Iterable[str] | None = None,
) -> PollinationPlan:
    """Construit le plan de cascade.

    Args:
        signal_type: clé dans REPLICATION_MATRIX
        niche: nom de la niche (humain)
        brand_id: override de la brand cible
        exclude_pipelines: pipelines à exclure (déjà lancés, non applicables)
    """
    cascade = list(REPLICATION_MATRIX.get(signal_type, []))
    excluded = set(exclude_pipelines or [])
    primary = primary_pipeline_for(signal_type)

    # Évite le doublon primaire dans la cascade
    if primary in cascade:
        cascade.remove(primary)
    cascade = [p for p in cascade if p not in excluded]

    return PollinationPlan(
        source_signal_type=signal_type,
        niche=niche,
        brand_id=brand_id or DEFAULT_BRAND_BY_SIGNAL.get(signal_type, "modern_cozy"),
        primary_pipeline=primary,
        cascade_pipelines=cascade,
    )


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 3:
        print(
            "Usage: python -m scripts.lib.cross_pollinator <signal_type> <niche> [brand_id]",
            file=sys.stderr,
        )
        sys.exit(2)
    signal_type = sys.argv[1]
    niche = sys.argv[2]
    brand_id = sys.argv[3] if len(sys.argv) > 3 else None
    plan = plan_pollination(signal_type, niche, brand_id=brand_id)
    print(json.dumps(plan.to_dict(), indent=2, ensure_ascii=False))
