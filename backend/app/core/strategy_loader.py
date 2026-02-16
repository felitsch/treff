"""
Strategy Loader - Dynamische Strategie-Anbindung fuer den Text-Generator

Zentrale Singleton-Klasse die content-strategy.json und social-content.json
laedt und cached, damit der Text-Generator dynamisch auf Strategie-Aenderungen
reagieren kann, ohne hartcodierte Werte zu verwenden.

Die JSON-Dateien liegen unter frontend/src/config/ und werden von hier geladen.
Ein TTL-basierter Cache sorgt dafuer, dass Aenderungen an den Dateien nach
spaetstens 5 Minuten wirksam werden, ohne den Server neu starten zu muessen.
"""
from __future__ import annotations

import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Locate project root (backend/app/core -> backend/app -> backend -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONTENT_STRATEGY_PATH = _PROJECT_ROOT / "frontend" / "src" / "config" / "content-strategy.json"
_SOCIAL_CONTENT_PATH = _PROJECT_ROOT / "frontend" / "src" / "config" / "social-content.json"

# Cache TTL in seconds (5 minutes)
_CACHE_TTL = 300


class StrategyLoader:
    """Singleton that loads and caches strategy JSON files.

    Usage:
        strategy = StrategyLoader.instance()
        hook = strategy.get_weighted_hook(platform="instagram_feed")
        cta = strategy.get_cta_for_platform("tiktok")
    """

    _instance: Optional["StrategyLoader"] = None

    def __init__(self) -> None:
        self._content_strategy: dict = {}
        self._social_content: dict = {}
        self._loaded_at: float = 0.0

    @classmethod
    def instance(cls) -> "StrategyLoader":
        """Return the singleton instance, creating it if needed."""
        if cls._instance is None:
            cls._instance = cls()
        cls._instance._ensure_loaded()
        return cls._instance

    def _ensure_loaded(self) -> None:
        """Load or reload JSONs if cache has expired."""
        now = time.time()
        if now - self._loaded_at < _CACHE_TTL and self._content_strategy:
            return  # Cache is still valid
        self._load()

    def _load(self) -> None:
        """Read both JSON files from disk."""
        try:
            if _CONTENT_STRATEGY_PATH.exists():
                with open(_CONTENT_STRATEGY_PATH, "r", encoding="utf-8") as f:
                    self._content_strategy = json.load(f)
                logger.info("Loaded content-strategy.json (%d bytes)", _CONTENT_STRATEGY_PATH.stat().st_size)
            else:
                logger.warning("content-strategy.json not found at %s", _CONTENT_STRATEGY_PATH)
                self._content_strategy = {}
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load content-strategy.json: %s", e)
            self._content_strategy = {}

        try:
            if _SOCIAL_CONTENT_PATH.exists():
                with open(_SOCIAL_CONTENT_PATH, "r", encoding="utf-8") as f:
                    self._social_content = json.load(f)
                logger.info("Loaded social-content.json (%d bytes)", _SOCIAL_CONTENT_PATH.stat().st_size)
            else:
                logger.warning("social-content.json not found at %s", _SOCIAL_CONTENT_PATH)
                self._social_content = {}
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load social-content.json: %s", e)
            self._social_content = {}

        self._loaded_at = time.time()

    # ──────────────────────────────────────────────
    # Raw accessors
    # ──────────────────────────────────────────────

    @property
    def content_strategy(self) -> dict:
        self._ensure_loaded()
        return self._content_strategy

    @property
    def social_content(self) -> dict:
        self._ensure_loaded()
        return self._social_content

    # ──────────────────────────────────────────────
    # Hook Formulas (from social-content.json)
    # ──────────────────────────────────────────────

    def get_hook_formulas(self, platform: Optional[str] = None) -> list[dict]:
        """Return hook formulas, optionally filtered by platform.

        Each formula has an 'effectiveness' rating (1-10).
        """
        formulas = self._social_content.get("hook_formulas", {}).get("formulas", [])
        if platform:
            formulas = [f for f in formulas if platform in f.get("platforms", [])]
        return formulas

    def get_weighted_hook(self, platform: Optional[str] = None) -> Optional[dict]:
        """Pick a hook formula weighted by effectiveness rating.

        Higher-rated hooks are more likely to be selected.
        """
        formulas = self.get_hook_formulas(platform)
        if not formulas:
            return None
        # Build weighted list: effectiveness is 1-10, use as weight
        weights = [f.get("effectiveness", 5) for f in formulas]
        selected = random.choices(formulas, weights=weights, k=1)[0]
        return selected

    def get_hook_prompt_section(self, platform: Optional[str] = None) -> str:
        """Build a prompt section listing hook formulas with effectiveness ratings."""
        formulas = self.get_hook_formulas(platform)
        if not formulas:
            return ""

        lines = ["HOOK-FORMELN (fuer die erste Caption-Zeile - MUSS Aufmerksamkeit erregen):"]
        # Sort by effectiveness descending so best hooks come first
        sorted_formulas = sorted(formulas, key=lambda f: f.get("effectiveness", 5), reverse=True)
        for f in sorted_formulas:
            eff = f.get("effectiveness", 5)
            name = f.get("name", "")
            template = f.get("template", "")
            examples = f.get("examples", [])
            example_str = f' (Beispiel: "{examples[0]}")' if examples else ""
            lines.append(f'- {name} (Effektivitaet {eff}/10): "{template}"{example_str}')
        lines.append("Bevorzuge Hook-Formeln mit hoeherer Effektivitaet! Waehle passend zu Kategorie und Plattform!")
        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # CTA Strategies (from social-content.json)
    # ──────────────────────────────────────────────

    def get_cta_strategies(self, platform: Optional[str] = None) -> list[dict]:
        """Return CTA strategies, optionally filtered by platform."""
        strategies = self._social_content.get("engagement_strategies", {}).get("cta_strategies", [])
        if platform:
            strategies = [s for s in strategies if platform in s.get("best_for", [])]
        return strategies

    def get_cta_prompt_section(self, platform: Optional[str] = None) -> str:
        """Build a prompt section listing CTA strategies with examples."""
        strategies = self.get_cta_strategies(platform)
        if not strategies:
            return ""

        lines = ["ENGAGEMENT-STRATEGIE (fuer CTAs am Post-Ende):"]
        for s in strategies:
            cta_type = s.get("type", "")
            desc = s.get("description", "")
            examples = s.get("examples", [])
            example_str = f' z.B. "{examples[0]}"' if examples else ""
            platforms_str = ", ".join(s.get("best_for", []))
            lines.append(f"- {cta_type.title()}-CTA ({platforms_str}): {desc}{example_str}")
        lines.append("Waehle den CTA-Typ passend zur Kategorie und Plattform!")
        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # Country Rotation (from content-strategy.json)
    # ──────────────────────────────────────────────

    def get_country_weights(self) -> dict[str, int]:
        """Return country distribution weights (e.g. {'usa': 30, 'canada': 20, ...})."""
        calendar = self._content_strategy.get("content_calendar", {})
        rotation = calendar.get("country_rotation", {})
        return rotation.get("distribution", {
            "usa": 30,
            "canada": 20,
            "australia": 20,
            "newzealand": 15,
            "ireland": 15,
        })

    def pick_weighted_country(self, available_countries: Optional[list[str]] = None) -> str:
        """Select a country using weighted distribution from strategy.

        Args:
            available_countries: Optional list to restrict selection to.
                                 Defaults to all countries with weights.

        Returns:
            Country key, e.g. 'usa', 'canada', etc.
        """
        weights = self.get_country_weights()
        if available_countries:
            weights = {k: v for k, v in weights.items() if k in available_countries}
        if not weights:
            # Fallback
            return random.choice(available_countries or ["usa", "canada", "australia", "newzealand", "ireland"])
        countries = list(weights.keys())
        w = list(weights.values())
        return random.choices(countries, weights=w, k=1)[0]

    # ──────────────────────────────────────────────
    # Tone of Voice (from content-strategy.json)
    # ──────────────────────────────────────────────

    def get_tone_of_voice(self) -> dict:
        """Return the brand tone of voice guidelines."""
        return self._content_strategy.get("brand", {}).get("tone_of_voice", {})

    def get_tone_prompt_section(self) -> str:
        """Build a prompt section with tone of voice do's and don'ts."""
        tov = self.get_tone_of_voice()
        if not tov:
            return ""

        lines = [f"BRAND TONE-OF-VOICE: {tov.get('primary', 'Jugendlich aber serioess')}"]
        lines.append(tov.get("description", ""))

        dos = tov.get("do", [])
        if dos:
            lines.append("\nDO:")
            for d in dos:
                lines.append(f"  - {d}")

        donts = tov.get("dont", [])
        if donts:
            lines.append("\nDON'T:")
            for d in donts:
                lines.append(f"  - {d}")

        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # Buyer Journey (from content-strategy.json)
    # ──────────────────────────────────────────────

    def get_buyer_journey_stages(self) -> list[dict]:
        """Return all buyer journey stages."""
        return self._content_strategy.get("buyer_journey", {}).get("stages", [])

    def get_buyer_journey_stage(self, stage_id: str) -> Optional[dict]:
        """Return a specific buyer journey stage by ID (awareness/consideration/decision)."""
        for stage in self.get_buyer_journey_stages():
            if stage.get("id") == stage_id:
                return stage
        return None

    def get_buyer_journey_prompt_section(self, stage_id: str) -> str:
        """Build a prompt section for a specific buyer journey stage."""
        stage = self.get_buyer_journey_stage(stage_id)
        if not stage:
            return ""

        lines = [f"BUYER-JOURNEY-STUFE: {stage.get('name', stage_id)}"]
        lines.append(stage.get("description", ""))

        content_types = stage.get("content_types", [])
        if content_types:
            lines.append(f"Geeignete Content-Typen: {', '.join(content_types)}")

        example_hooks = stage.get("example_hooks", [])
        if example_hooks:
            lines.append("Beispiel-Hooks fuer diese Stufe:")
            for h in example_hooks:
                lines.append(f'  - "{h}"')

        # Stage-specific tone adjustments
        tone_adjustments = {
            "awareness": "Schreibe inspirierend und emotional. Wecke Fernweh und Neugier. Fokus auf Traeume und Moeglichkeiten, nicht auf Details oder Preise.",
            "consideration": "Schreibe informativ und vertrauensbildend. Gib konkrete Fakten, Vergleiche und Tipps. Beantworte haeufige Fragen proaktiv.",
            "decision": "Schreibe mit Dringlichkeit und klarem Call-to-Action. Betone Fristen, limitierte Plaetze und die naechsten Schritte. Senke die Hemmschwelle.",
        }
        adj = tone_adjustments.get(stage_id)
        if adj:
            lines.append(f"\nTON-ANPASSUNG: {adj}")

        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # Content Pillars (from content-strategy.json)
    # ──────────────────────────────────────────────

    def get_content_pillars(self) -> list[dict]:
        """Return all content pillars."""
        return self._content_strategy.get("content_pillars", [])

    def get_content_pillar(self, pillar_id: str) -> Optional[dict]:
        """Return a specific content pillar by ID."""
        for pillar in self.get_content_pillars():
            if pillar.get("id") == pillar_id:
                return pillar
        return None

    def get_content_pillar_prompt_section(self, category: str) -> str:
        """Build a prompt section for a content pillar based on category.

        Maps common category names to pillar IDs.
        """
        # Map category to pillar ID
        category_to_pillar = {
            "laender_spotlight": "laender_spotlight",
            "erfahrungsberichte": "erfahrungsberichte",
            "infografiken": "infografiken",
            "fristen_cta": "fristen_cta",
            "tipps_tricks": "tipps_tricks",
            "faq": "faq",
            "foto_posts": "behind_the_scenes",
            "reel_tiktok_thumbnails": "erfahrungsberichte",
            "story_posts": "behind_the_scenes",
        }
        pillar_id = category_to_pillar.get(category, category)
        pillar = self.get_content_pillar(pillar_id)
        if not pillar:
            return ""

        lines = [f"CONTENT-PILLAR: {pillar.get('name', '')} {pillar.get('emoji', '')}"]
        lines.append(pillar.get("description", ""))

        # Pillar-specific writing instructions
        pillar_instructions = {
            "erfahrungsberichte": "Schreibe emotionaler und persoenlicher. Nutze Ich-Perspektive oder direkte Zitate. Erzeuge Gaensehaut-Momente und Identifikation.",
            "laender_spotlight": "Schreibe informativ und inspirierend. Nutze konkrete Fakten, Highlights und Vergleiche. Mache Lust auf das jeweilige Land.",
            "tipps_tricks": "Schreibe praktisch und handlungsorientiert. Gib konkrete, umsetzbare Tipps. Nutze Nummerierungen und Checklisten-Stil.",
            "fristen_cta": "Schreibe mit Dringlichkeit. Betone Fristen und limitierte Verfuegbarkeit. Klare Handlungsaufforderung am Ende.",
            "faq": "Schreibe klar und sachlich. Beantworte die Frage direkt und vollstaendig. Baue Vertrauen auf durch Kompetenz.",
            "behind_the_scenes": "Schreibe authentisch und nahbar. Zeige die menschliche Seite von TREFF. Locker, aber professionell.",
            "infografiken": "Schreibe praezise und datengetrieben. Nutze Zahlen und Fakten. Visualisierungsfreundliche Formulierungen.",
        }
        instruction = pillar_instructions.get(pillar_id)
        if instruction:
            lines.append(f"\nSCHREIBSTIL-ANPASSUNG: {instruction}")

        example_topics = pillar.get("example_topics", [])
        if example_topics:
            lines.append(f"Beispielthemen: {', '.join(example_topics[:3])}")

        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # Seasonal Strategy (from content-strategy.json)
    # ──────────────────────────────────────────────

    def get_seasonal_phases(self) -> list[dict]:
        """Return all seasonal strategy phases."""
        calendar = self._content_strategy.get("content_calendar", {})
        return calendar.get("seasonal_strategy", {}).get("phases", [])

    def get_current_seasonal_phase(self) -> Optional[dict]:
        """Determine the current seasonal phase based on the current month."""
        current_month = datetime.now().month
        for phase in self.get_seasonal_phases():
            if current_month in phase.get("months", []):
                return phase
        return None

    def get_seasonal_prompt_section(self) -> str:
        """Build a prompt section for the current seasonal phase."""
        phase = self.get_current_seasonal_phase()
        if not phase:
            return ""

        lines = [f"SAISONALE PHASE: {phase.get('name', '')}"]
        lines.append(f"Fokus: {phase.get('focus', '')}")
        lines.append(phase.get("description", ""))

        key_events = phase.get("key_events", [])
        if key_events:
            lines.append("\nAktuelle/bevorstehende Events:")
            for event in key_events:
                lines.append(f"  - {event.get('label', '')}: {event.get('date_hint', '')}")

        content_mix = phase.get("content_mix", {})
        if content_mix:
            lines.append(f"\nContent-Mix fuer diese Phase: Awareness {content_mix.get('awareness', 0)}%, Consideration {content_mix.get('consideration', 0)}%, Decision {content_mix.get('decision', 0)}%")

        priority_pillars = phase.get("priority_pillars", [])
        if priority_pillars:
            lines.append(f"Prioritaets-Themen: {', '.join(priority_pillars)}")

        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # Platform Best Practices (from social-content.json)
    # ──────────────────────────────────────────────

    def get_platform_config(self, platform: str) -> Optional[dict]:
        """Return platform configuration from social-content.json.

        Platform keys: instagram_feed, instagram_stories, instagram_reels, tiktok
        """
        return self._social_content.get("platforms", {}).get(platform)

    def get_platform_best_practices_prompt(self, platform: str) -> str:
        """Build a prompt section with platform-specific best practices."""
        config = self.get_platform_config(platform)
        if not config:
            return ""

        lines = [f"PLATTFORM-BEST-PRACTICES ({config.get('name', platform)}):"]

        best_practices = config.get("best_practices", [])
        for bp in best_practices:
            lines.append(f"  - {bp}")

        # Caption rules (mainly for instagram_feed)
        caption_rules = config.get("caption_rules", {})
        if caption_rules:
            ideal_range = caption_rules.get("ideal_length_range", [])
            if ideal_range:
                lines.append(f"  - Ideale Caption-Laenge: {ideal_range[0]}-{ideal_range[1]} Zeichen")
            hashtag_count = caption_rules.get("hashtag_count", {})
            if hashtag_count:
                lines.append(f"  - Hashtags: {hashtag_count.get('min', 5)}-{hashtag_count.get('max', 15)} (ideal: {hashtag_count.get('ideal', 10)})")

        # Duration (for reels/tiktok)
        duration = config.get("duration", {})
        if duration:
            ideal = duration.get("ideal_range_seconds", [])
            if ideal:
                lines.append(f"  - Ideale Videolaenge: {ideal[0]}-{ideal[1]} Sekunden")

        # Posting frequency
        freq = config.get("posting_frequency", {})
        if freq:
            lines.append(f"  - Posting-Frequenz: {freq.get('ideal_per_week', '?')}x pro Woche ideal")

        return "\n".join(lines)

    # ──────────────────────────────────────────────
    # Hashtag Strategy (from social-content.json)
    # ──────────────────────────────────────────────

    def get_brand_hashtags(self) -> dict:
        """Return brand hashtag lists."""
        return self._social_content.get("hashtag_strategy", {}).get("brand_hashtags", {})

    def get_country_hashtags(self, country: str) -> list[str]:
        """Return country-specific hashtags."""
        return self._social_content.get("hashtag_strategy", {}).get("country_hashtags", {}).get(country, [])

    # ──────────────────────────────────────────────
    # Full enhanced system prompt builder
    # ──────────────────────────────────────────────

    def build_strategy_prompt_sections(
        self,
        platform: Optional[str] = None,
        category: Optional[str] = None,
        buyer_journey_stage: Optional[str] = None,
    ) -> str:
        """Build all strategy-driven prompt sections combined.

        This is the main method called by the text generator to inject
        dynamic strategy context into the Gemini system prompt.

        Args:
            platform: Target platform (instagram_feed, instagram_reels, tiktok, etc.)
            category: Content category (laender_spotlight, erfahrungsberichte, etc.)
            buyer_journey_stage: Optional buyer journey stage (awareness/consideration/decision)

        Returns:
            Combined string of all applicable strategy prompt sections.
        """
        sections = []

        # 1. Hook formulas (platform-filtered, with effectiveness ratings)
        hook_section = self.get_hook_prompt_section(platform)
        if hook_section:
            sections.append(hook_section)

        # 2. CTA strategies (platform-filtered)
        cta_section = self.get_cta_prompt_section(platform)
        if cta_section:
            sections.append(cta_section)

        # 3. Tone of voice from strategy
        tone_section = self.get_tone_prompt_section()
        if tone_section:
            sections.append(tone_section)

        # 4. Buyer journey stage (if provided)
        if buyer_journey_stage:
            bj_section = self.get_buyer_journey_prompt_section(buyer_journey_stage)
            if bj_section:
                sections.append(bj_section)

        # 5. Content pillar (if category provided)
        if category:
            pillar_section = self.get_content_pillar_prompt_section(category)
            if pillar_section:
                sections.append(pillar_section)

        # 6. Seasonal phase (automatic based on current month)
        seasonal_section = self.get_seasonal_prompt_section()
        if seasonal_section:
            sections.append(seasonal_section)

        # 7. Platform best practices
        if platform:
            platform_section = self.get_platform_best_practices_prompt(platform)
            if platform_section:
                sections.append(platform_section)

        return "\n\n".join(sections)
