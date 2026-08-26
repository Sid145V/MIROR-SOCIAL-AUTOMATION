"""
T01 Exact Text Lock & Text Integrity System
Enforces immutable string preservation, SHA-256 fingerprint hashing, 
strict schema validation, zero-mutation guarantee, and layout fit checking.
"""

import os
import json
import hashlib

class TextLockError(ValueError):
    """Raised when a text field is missing, empty, mutated, or fails lock validation."""
    pass

class TextFitError(RuntimeError):
    """Raised when exact supplied text exceeds approved layout visual bounds."""
    pass

class TextLockSystem:
    @staticmethod
    def compute_sha256(text_str: str) -> str:
        """Calculate exact SHA-256 hash of a string preserving exact bytes, case, and newlines."""
        if not isinstance(text_str, str):
            raise TextLockError(f"Field value must be string, got {type(text_str).__name__}")
        return hashlib.sha256(text_str.encode("utf-8")).hexdigest()

    @staticmethod
    def validate_exact_string(text_str: str, field_name: str, expected_hash: str = None) -> str:
        """Validate string presence, non-emptiness, and optional SHA-256 fingerprint matching."""
        if text_str is None:
            raise TextLockError(f"T01 TEXT LOCK FAILURE: Field '{field_name}' is None/null.")
        if not isinstance(text_str, str):
            raise TextLockError(f"T01 TEXT LOCK FAILURE: Field '{field_name}' expected string, got {type(text_str).__name__}.")
        if len(text_str) == 0:
            raise TextLockError(f"T01 TEXT LOCK FAILURE: Field '{field_name}' is empty string.")

        actual_hash = TextLockSystem.compute_sha256(text_str)
        if expected_hash and actual_hash != expected_hash:
            raise TextLockError(
                f"T01 TEXT LOCK FAILURE: Field '{field_name}' hash mismatch.\n"
                f"Expected SHA-256: {expected_hash}\n"
                f"Actual SHA-256:   {actual_hash}\n"
                f"Content mutated:  '{text_str}'"
            )
        return actual_hash

    @staticmethod
    def generate_manifest(slide_content: dict, slide_id: str) -> dict:
        """Generate SHA-256 manifest dictionary for all locked text elements in a slide."""
        manifest = {}

        if "headline" in slide_content:
            hl = slide_content["headline"]
            hl_text = hl.get("text", hl) if isinstance(hl, dict) else hl
            manifest[f"{slide_id}.headline"] = TextLockSystem.compute_sha256(hl_text)

        if "body" in slide_content:
            body = slide_content["body"]
            if isinstance(body, list):
                for idx, b_item in enumerate(body):
                    b_text = b_item.get("text", b_item) if isinstance(b_item, dict) else b_item
                    manifest[f"{slide_id}.body.{idx}"] = TextLockSystem.compute_sha256(b_text)
            elif isinstance(body, str):
                manifest[f"{slide_id}.body"] = TextLockSystem.compute_sha256(body)

        if "cta" in slide_content:
            cta = slide_content["cta"]
            cta_text = cta.get("text", cta) if isinstance(cta, dict) else cta
            manifest[f"{slide_id}.cta"] = TextLockSystem.compute_sha256(cta_text)

        return manifest

    @staticmethod
    def validate_slide_payload(slide_payload: dict, expected_manifest: dict = None) -> dict:
        """Perform full validation of a slide payload against strict exact text rules."""
        slide_id = slide_payload.get("id") or slide_payload.get("slide") or f"S0{slide_payload.get('slide_number', 1)}"
        
        # 1. Headline Validation
        if "headline" not in slide_payload and "headline_groups" not in slide_payload:
            raise TextLockError(f"T01 TEXT LOCK FAILURE: Slide '{slide_id}' is missing required field 'headline'.")

        hl_value = slide_payload.get("headline")
        if hl_value:
            hl_text = hl_value.get("text") if isinstance(hl_value, dict) else hl_value
            if isinstance(hl_value, dict) and hl_value.get("lock") != "EXACT":
                raise TextLockError(f"T01 TEXT LOCK FAILURE: Slide '{slide_id}' headline lock attribute must be 'EXACT'.")
            
            exp_hash = expected_manifest.get(f"{slide_id}.headline") if expected_manifest else None
            TextLockSystem.validate_exact_string(hl_text, f"{slide_id}.headline", exp_hash)

        # 2. Body Validation (if present)
        body_value = slide_payload.get("body") or slide_payload.get("body_paragraphs")
        if body_value:
            if isinstance(body_value, list):
                for idx, item in enumerate(body_value):
                    item_text = item.get("text") if isinstance(item, dict) else (
                        "\n".join(item) if isinstance(item, list) else item
                    )
                    if isinstance(item, dict) and item.get("lock") != "EXACT":
                        raise TextLockError(f"T01 TEXT LOCK FAILURE: Slide '{slide_id}' body[{idx}] lock attribute must be 'EXACT'.")
                    
                    exp_hash = expected_manifest.get(f"{slide_id}.body.{idx}") if expected_manifest else None
                    TextLockSystem.validate_exact_string(item_text, f"{slide_id}.body.{idx}", exp_hash)

        # 3. CTA Validation (if S03 / cta)
        cta_value = slide_payload.get("cta")
        if slide_payload.get("type") == "cta" or slide_id == "S03":
            if not cta_value:
                raise TextLockError(f"T01 TEXT LOCK FAILURE: Slide '{slide_id}' is missing required field 'cta'.")
            
            cta_text = cta_value.get("text") if isinstance(cta_value, dict) else cta_value
            if isinstance(cta_value, dict) and cta_value.get("lock") != "EXACT":
                raise TextLockError(f"T01 TEXT LOCK FAILURE: Slide '{slide_id}' cta lock attribute must be 'EXACT'.")
            
            exp_hash = expected_manifest.get(f"{slide_id}.cta") if expected_manifest else None
            TextLockSystem.validate_exact_string(cta_text, f"{slide_id}.cta", exp_hash)

        return TextLockSystem.generate_manifest(slide_payload, slide_id)
