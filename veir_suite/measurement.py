"""Measurement identity excludes administrative changes, never acceptance criteria."""
from __future__ import annotations

from .model import InvalidData, digest

REQUIREMENT_METADATA = {"title", "owner", "priority", "next_action", "decision_record"}


def measurement_contract(registry: dict) -> dict:
    """Keep the full contract while omitting fields used only to organise work.

    Unknown fields remain significant. New acceptance settings must not silently
    fall outside the comparison boundary. The complete registry is still hashed
    separately in every receipt, including all display and administrative fields.
    """
    contract = {key: value for key, value in registry.items() if key != "name"}
    contract["scopes"] = sorted(
        [{key: value for key, value in scope.items() if key != "title"}
         for scope in registry["scopes"]], key=lambda item: item["id"])
    contract["requirements"] = sorted(
        [{key: value for key, value in requirement.items() if key not in REQUIREMENT_METADATA}
         for requirement in registry["requirements"]], key=lambda item: item["id"])
    contract["tests"] = sorted(registry["tests"], key=lambda item: item["id"])
    return contract


def measurement_cohort(registry: dict, harness: str, profile: dict, *, version: int = 2) -> str:
    if type(version) is not int or version not in {1, 2}:
        raise InvalidData("Unknown measurement identity version")
    contract = registry if version == 1 else measurement_contract(registry)
    # Keep the version in new identities; historical v1 receipts remain exact.
    payload = {"registry": contract, "harness": harness, "profile": profile}
    if version == 2:
        payload["measurement_identity_version"] = 2
    return digest(payload)
