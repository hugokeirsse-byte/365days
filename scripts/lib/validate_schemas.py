"""Module 22 — Validateur Schéma.

Vérifie que tous les JSON du repo sont conformes à leurs schémas
(opportunity.schema.json, asset.schema.json) et que les JSON de config
sont parseables.

Aucun appel LLM. 100% déterministe.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "data" / "schemas"
CONFIG_DIR = REPO_ROOT / "data" / "config"
WHITELISTS_DIR = REPO_ROOT / "data" / "whitelists"


def _validate_with_jsonschema(instance: dict, schema: dict) -> list[str]:
    try:
        import jsonschema  # type: ignore
    except ImportError:
        return ["jsonschema non installé : pip install jsonschema"]
    try:
        jsonschema.validate(instance=instance, schema=schema)
        return []
    except jsonschema.ValidationError as exc:
        return [f"{list(exc.path)}: {exc.message}"]


def _validate_parseable(path: Path) -> list[str]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return []
    except json.JSONDecodeError as exc:
        return [f"JSON invalide : {exc}"]


def validate_all() -> dict[str, list[str]]:
    """Retourne {file_path_relative: [errors]}. Vide = tout passe."""
    errors: dict[str, list[str]] = {}

    # 1) Tous les JSON parseables
    for json_file in REPO_ROOT.glob("data/**/*.json"):
        rel = str(json_file.relative_to(REPO_ROOT))
        errs = _validate_parseable(json_file)
        if errs:
            errors[rel] = errs

    # 2) Opportunities & Assets contre leurs schémas
    opp_schema_path = SCHEMAS_DIR / "opportunity.schema.json"
    asset_schema_path = SCHEMAS_DIR / "asset.schema.json"

    if opp_schema_path.exists():
        try:
            opp_schema = json.loads(opp_schema_path.read_text(encoding="utf-8"))
            for opp_file in REPO_ROOT.glob("data/opportunities/**/*.json"):
                rel = str(opp_file.relative_to(REPO_ROOT))
                instance = json.loads(opp_file.read_text(encoding="utf-8"))
                errs = _validate_with_jsonschema(instance, opp_schema)
                if errs:
                    errors[rel] = errors.get(rel, []) + errs
        except json.JSONDecodeError as exc:
            errors[str(opp_schema_path.relative_to(REPO_ROOT))] = [f"Schéma invalide : {exc}"]

    if asset_schema_path.exists():
        try:
            asset_schema = json.loads(asset_schema_path.read_text(encoding="utf-8"))
            for asset_meta in REPO_ROOT.glob("staging/**/metadata.json"):
                rel = str(asset_meta.relative_to(REPO_ROOT))
                try:
                    instance = json.loads(asset_meta.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    errors[rel] = [f"JSON invalide : {exc}"]
                    continue
                errs = _validate_with_jsonschema(instance, asset_schema)
                if errs:
                    errors[rel] = errors.get(rel, []) + errs
        except json.JSONDecodeError as exc:
            errors[str(asset_schema_path.relative_to(REPO_ROOT))] = [
                f"Schéma invalide : {exc}"
            ]

    return errors


def main() -> int:
    errors = validate_all()
    if not errors:
        print("✅ Tous les JSON sont valides et conformes aux schémas.")
        return 0
    print(f"❌ {len(errors)} fichier(s) en erreur :", file=sys.stderr)
    for path, errs in errors.items():
        print(f"\n  {path}:", file=sys.stderr)
        for err in errs:
            print(f"    - {err}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
