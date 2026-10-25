#!/usr/bin/env python3
"""Create the P35 Event A project-disjoint holdout manifest.

This is a data-selection script.  It imports no ML package and does not train,
predict, or evaluate a classifier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd


SALT = "P35_EVENT_A_V1|"
MODULUS = 5
SELECTED_REMAINDER = 0
EXPECTED_DATASET_BLOB_SHA1 = "6e1075ead90054ff9955cf310842c0d31a41e5dc"


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def normalize_project(link: str) -> str:
    """Return lowercase owner/repository from a GitHub source URL."""
    parsed = urlsplit(str(link).strip())
    if parsed.hostname is None or parsed.hostname.lower() != "github.com":
        raise ValueError(f"not a GitHub URL: {link!r}")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"GitHub URL lacks owner/repository: {link!r}")
    owner, repository = parts[0], parts[1].removesuffix(".git")
    if not owner or not repository:
        raise ValueError(f"GitHub URL lacks owner/repository: {link!r}")
    return f"{owner}/{repository}".lower()


def is_heldout(project_id: str) -> bool:
    digest = hashlib.sha256(f"{SALT}{project_id}".encode("utf-8")).digest()
    return int.from_bytes(digest, byteorder="big") % MODULUS == SELECTED_REMAINDER


def make_manifest(data: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    required = {"sample_id", "link", "code_snippet", "start_line", "end_line"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"dataset is missing required columns: {sorted(missing)}")
    if data["sample_id"].isna().any() or not data["sample_id"].is_unique:
        raise ValueError("sample_id must be present and unique")
    if data["code_snippet"].isna().any():
        raise ValueError("code_snippet must be present for duplicate-leakage checking")

    work = data.copy()
    work["sample_id"] = work["sample_id"].astype(int)
    work["project_id"] = work["link"].map(normalize_project)
    work["assignment"] = work["project_id"].map(
        lambda project: "holdout" if is_heldout(project) else "training"
    )
    work["code_snippet_sha256"] = work["code_snippet"].map(
        lambda snippet: hashlib.sha256(snippet.encode("utf-8")).hexdigest()
    )

    # Retain every held-out example.  Exclude only the matching training rows.
    heldout_snippets = set(work.loc[work["assignment"] == "holdout", "code_snippet"])
    excluded = work.loc[
        (work["assignment"] == "training")
        & work["code_snippet"].isin(heldout_snippets),
        "sample_id",
    ].tolist()
    work.loc[work["sample_id"].isin(excluded), "assignment"] = "excluded"

    manifest = work[
        ["sample_id", "project_id", "assignment", "link", "start_line", "end_line", "code_snippet_sha256"]
    ].sort_values("sample_id", kind="stable").reset_index(drop=True)
    return manifest, sorted(excluded)


def validate(manifest: pd.DataFrame, source: pd.DataFrame, excluded_ids: list[int]) -> None:
    if len(manifest) != len(source) or not manifest["sample_id"].is_unique:
        raise AssertionError("every source sample ID must occur exactly once in the manifest")
    if set(manifest["sample_id"]) != set(source["sample_id"].astype(int)):
        raise AssertionError("manifest sample IDs differ from source sample IDs")

    by_project = manifest.groupby("project_id")["assignment"].agg(set)
    if any("holdout" in assignments and "training" in assignments for assignments in by_project):
        raise AssertionError("a project occurs in both training and holdout")
    if any("holdout" in assignments and "excluded" in assignments for assignments in by_project):
        raise AssertionError("a held-out project has an excluded sample")

    assignments_by_id = manifest.set_index("sample_id")["assignment"]
    exact_snippets = source[["sample_id", "code_snippet"]].copy()
    exact_snippets["sample_id"] = exact_snippets["sample_id"].astype(int)
    exact_snippets["assignment"] = exact_snippets["sample_id"].map(assignments_by_id)
    by_snippet = exact_snippets.groupby("code_snippet")["assignment"].agg(set)
    if any("holdout" in assignments and "training" in assignments for assignments in by_snippet):
        raise AssertionError("an identical snippet crosses from training into holdout")
    actual_exclusions = manifest.loc[manifest["assignment"] == "excluded", "sample_id"].tolist()
    if actual_exclusions != excluded_ids:
        raise AssertionError("excluded IDs are inconsistent with the manifest")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the P35 Event A held-out split.")
    parser.add_argument("--input", type=Path, default=Path("data/god_class_df.csv"))
    parser.add_argument("--out", type=Path, default=Path("event_a"))
    args = parser.parse_args()

    blob_sha1 = git_blob_sha1(args.input)
    if blob_sha1 != EXPECTED_DATASET_BLOB_SHA1:
        raise SystemExit(
            f"dataset Git blob SHA-1 is {blob_sha1}, expected {EXPECTED_DATASET_BLOB_SHA1}"
        )
    source = pd.read_csv(args.input)
    manifest, excluded_ids = make_manifest(source)
    validate(manifest, source, excluded_ids)

    # The same selection must result when rows are presented in a different order.
    reordered = source.sample(frac=1, random_state=20261025).reset_index(drop=True)
    reordered_manifest, reordered_excluded = make_manifest(reordered)
    validate(reordered_manifest, reordered, reordered_excluded)
    if not manifest.equals(reordered_manifest) or excluded_ids != reordered_excluded:
        raise AssertionError("selection depends on CSV row order")

    repeated_manifest, repeated_excluded = make_manifest(source)
    if not manifest.equals(repeated_manifest) or excluded_ids != repeated_excluded:
        raise AssertionError("selection is not deterministic across repeated runs")

    args.out.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(args.out / "split_manifest.csv", index=False)
    heldout = manifest.loc[manifest["assignment"] == "holdout"].copy()
    heldout.to_csv(args.out / "heldout_cases.csv", index=False)

    counts = manifest["assignment"].value_counts().to_dict()
    summary = {
        "event": "P35 Event A",
        "dataset": {
            "path": "data/god_class_df.csv",
            "git_blob_sha1": blob_sha1,
            "expected_m2_git_blob_sha1": EXPECTED_DATASET_BLOB_SHA1,
            "sample_count": int(len(manifest)),
            "project_count": int(manifest["project_id"].nunique()),
        },
        "selection_algorithm": {
            "project_identifier": "lowercase owner/repository parsed from GitHub link",
            "hash": "SHA-256",
            "input_prefix": SALT,
            "integer_conversion": "unsigned big-endian digest integer",
            "rule": "select project when digest_integer modulo 5 equals 0",
        },
        "assignments": {
            "training_samples": int(counts.get("training", 0)),
            "excluded_samples": int(counts.get("excluded", 0)),
            "heldout_samples": int(counts.get("holdout", 0)),
            "training_projects": int(manifest.loc[manifest["assignment"] != "holdout", "project_id"].nunique()),
            "heldout_projects": int(heldout["project_id"].nunique()),
        },
        "exact_snippet_leakage": {
            "rule": "exclude training samples whose exact code snippet occurs in holdout; retain all heldout samples",
            "excluded_training_ids": excluded_ids,
            "excluded_training_count": len(excluded_ids),
        },
        "validation": {
            "all_source_ids_once": True,
            "training_and_holdout_projects_disjoint": True,
            "selection_deterministic_on_repeat": True,
            "selection_independent_of_csv_row_order": True,
            "exact_snippets_do_not_cross_training_holdout": True,
            "model_execution": "none; this script has no model imports or execution",
        },
    }
    (args.out / "selection_summary.json").write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
