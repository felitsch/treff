"""Shot List API routes — Filming guides for students abroad.

CRUD operations for shot lists plus AI-powered shot generation
based on content type, country, and season.
"""
from __future__ import annotations

import json
import logging
import random
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.shot_list import ShotList
from app.models.video_script import VideoScript
from app.models.student import Student

logger = logging.getLogger(__name__)

router = APIRouter()

# ──────────────────────────────────────────────
# Content types for shot list generation
# ──────────────────────────────────────────────
CONTENT_TYPES = {
    "arrival_story": {
        "label": "Ankunfts-Story",
        "description": "Erste Momente im neuen Land",
        "season_hint": "August/September",
    },
    "first_day_school": {
        "label": "Erster Schultag",
        "description": "Erster Tag an der Highschool",
        "season_hint": "August/September",
    },
    "school_day": {
        "label": "Schulalltag",
        "description": "Typischer Schultag",
        "season_hint": "Ganzjaehrig",
    },
    "host_family": {
        "label": "Gastfamilien-Moment",
        "description": "Leben mit der Gastfamilie",
        "season_hint": "Ganzjaehrig",
    },
    "cultural_moment": {
        "label": "Kultureller Moment",
        "description": "Kulturelle Unterschiede & Ueberraschungen",
        "season_hint": "Ganzjaehrig",
    },
    "holiday": {
        "label": "Feiertag im Ausland",
        "description": "Feiertage anders erleben",
        "season_hint": "Saisonal",
    },
    "school_event": {
        "label": "Schul-Event",
        "description": "Sportevents, Dances, Clubs",
        "season_hint": "Ganzjaehrig",
    },
    "farewell": {
        "label": "Abschied & Rueckkehr",
        "description": "Die letzten Wochen und der Abschied",
        "season_hint": "Juni/Juli",
    },
    "alumni": {
        "label": "Alumni-Rueckblick",
        "description": "Erinnerungen und Tipps fuer neue Schueler",
        "season_hint": "Ganzjaehrig",
    },
    "general": {
        "label": "Allgemeiner Content",
        "description": "Freie Themen aus dem Auslandsalltag",
        "season_hint": "Ganzjaehrig",
    },
}

# ──────────────────────────────────────────────
# Country-specific shot ideas
# ──────────────────────────────────────────────
COUNTRY_NAMES = {
    "usa": "USA",
    "canada": "Kanada",
    "australia": "Australien",
    "newzealand": "Neuseeland",
    "ireland": "Irland",
}

# Base shot templates per content type
SHOT_TEMPLATES = {
    "arrival_story": [
        {"description_for_student": "Filme den Moment, wenn du aus dem Flugzeug steigst oder durch die Ankunftshalle gehst", "example": "Selfie-Video beim Verlassen des Flugzeugs mit 'Ich bin da!' Reaktion", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht nutzen, Flughafenbeleuchtung ist oft gut", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige dein erstes Gepaeck am Foerderband — den Moment des Wartens", "example": "Zeitraffer vom Gepaeckband, dann Freude wenn der Koffer kommt", "duration_hint": "3-5 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Indoor-Licht, notfalls Handyblitz", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme das Willkommens-Schild oder den ersten Moment mit deiner Gastfamilie", "example": "Gastfamilie haelt Willkommens-Schild hoch, Umarmung", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerliches Licht bevorzugen", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige die Autofahrt zu deinem neuen Zuhause — Blick aus dem Fenster", "example": "Handy ans Autofenster halten, neue Landschaft zeigen", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gegenlicht vermeiden, Fenster leicht oeffnen gegen Spiegelungen", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme dein neues Zimmer — mach eine kleine Roomtour", "example": "Langsam durch das Zimmer schwenken: Bett, Schreibtisch, Fensterblick", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Alle Lichter anmachen, Vorhang oeffnen", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige dein erstes Essen mit der Gastfamilie", "example": "Filme dein Gastfamilien-Abendessen von der Seite, dann dein Gesicht", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Kuechen-/Esszimmerlicht, notfalls Kerzen", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Sage in die Kamera, wie du dich gerade fuehlst — ehrlich und ungefiltert", "example": "Selfie-Modus: 'Ich bin jetzt wirklich hier und es fuehlt sich so surreal an...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gutes Frontlicht, Fenster hinter der Kamera", "content_pillar": "erfahrungsberichte"},
    ],
    "first_day_school": [
        {"description_for_student": "Filme dich morgens im Spiegel in deinem Schul-Outfit (oder Schuluniform)", "example": "Outfit-Check im Spiegel, Kamera wackelt nicht", "duration_hint": "3-5 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gutes Raumlicht, kein Gegenlicht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige den Weg zur Schule — School Bus, Auto, oder zu Fuss", "example": "Zeitraffer-Video vom Schulweg oder Yellow School Bus", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Morgenlicht ist perfekt", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme das Schulgebaeude von aussen — zeige die Groesse", "example": "Handy langsam von unten nach oben schwenken am Gebaeude", "duration_hint": "3-5 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Sonne im Ruecken fuer klare Bilder", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige deinen Spind / Locker — wie im Film!", "example": "Locker oeffnen, Inhalt zeigen, 'Wie im Film!' sagen", "duration_hint": "5-8 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Flurbeleuchtung nutzen", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme die Cafeteria oder den Essensbereich", "example": "Schwenk ueber die Cafeteria, zeige das Essen", "duration_hint": "5-8 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht oder helle Raumbeleuchtung", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Reagiere auf eine Sache, die an deiner neuen Schule total anders ist", "example": "'In Deutschland haben wir das NICHT: ...' Ueberraschter Gesichtsausdruck", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerliches Licht bevorzugen", "content_pillar": "erfahrungsberichte"},
    ],
    "school_day": [
        {"description_for_student": "Filme deinen Stundenplan oder Tagesablauf als Zeitraffer", "example": "Morgens Aufstehen -> Schulweg -> Unterricht -> Sport -> Abends", "duration_hint": "15-30 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Verschiedene Lichtsituationen sind OK", "content_pillar": "tipps_tricks"},
        {"description_for_student": "Zeige einen besonderen Kurs den es in Deutschland nicht gibt", "example": "Woodshop, Yearbook, Drama Class, Cheerleading", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Raumlicht der Klasse nutzen", "content_pillar": "tipps_tricks"},
        {"description_for_student": "Filme eine Sport-AG oder ein School-Team bei dem du mitmachst", "example": "Training-Clips, Teamfoto, Jubel nach Tor/Punkt", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Aussenlicht bei Sport, Hallenlicht OK", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige dein Mittagessen in der Schule", "example": "Tablett mit Essen filmen, vergleiche mit deutschem Schulessen", "duration_hint": "5-8 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Cafeteria-Licht", "content_pillar": "tipps_tricks"},
        {"description_for_student": "Filme eine lustige oder ueberraschende Situation im Schulalltag", "example": "Pep Rally, Spirit Week, besonderer Moment mit Freunden", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht oder Veranstaltungslicht", "content_pillar": "erfahrungsberichte"},
    ],
    "host_family": [
        {"description_for_student": "Filme ein gemeinsames Abendessen oder Kochen mit der Gastfamilie", "example": "Gastmutter kocht, du hilfst, alle essen zusammen", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Kuechen-Licht, warm und gemuetlich", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige einen Familienausflug oder Wochenendaktivitaet", "example": "Wanderung, Shopping, Strandtag — alle zusammen", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht bei Outdoor-Aktivitaeten", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Stelle deine Gastgeschwister oder Haustiere vor", "example": "Kurzes Interview: 'Das ist... und er/sie...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerliches Licht, ruhiger Hintergrund", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme einen typischen Abend zuhause — Netflix, Spiele, Reden", "example": "Gemuetliche Couch-Szene, Brettspiel, Fernsehabend", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Wohnzimmerlicht, stimmungsvoll", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Sage in die Kamera was du an deiner Gastfamilie am meisten magst", "example": "Ehrlicher Moment: 'Was ich an meiner Gastfamilie am meisten schaetze...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gutes Frontlicht", "content_pillar": "erfahrungsberichte"},
    ],
    "cultural_moment": [
        {"description_for_student": "Filme etwas das in deinem Gastland total anders ist als in Deutschland", "example": "'In Deutschland machen wir das SO, hier machen sie DAS...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Beliebig, Situation anpassen", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige ein typisches Essen oder Getraenk das du vorher nicht kanntest", "example": "Erstes Mal Poutine/Vegemite/Root Beer probieren — echte Reaktion!", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Helles Licht fuer Essensaufnahmen", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Filme einen Ort der typisch fuer dein Gastland ist", "example": "Main Street, Strand, Nationalpark, typische Strasse", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Golden Hour fuer Landschaften", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Reagiere auf eine kulturelle Ueberraschung", "example": "'Ich haette nie gedacht dass hier...' Ueberraschtes Gesicht", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerlich, authentisch", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Vergleiche: So ist es in Deutschland vs. hier", "example": "Split-Screen oder Vorher/Nachher Style", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gleichmaessiges Licht fuer beide Teile", "content_pillar": "laender_spotlight"},
    ],
    "holiday": [
        {"description_for_student": "Zeige die Vorbereitungen fuer den Feiertag (Deko, Kochen, Einkaufen)", "example": "Gastfamilie dekoriert das Haus, Truthahn im Ofen, Geschenke einpacken", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Stimmungsvolles Festtagslicht", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Filme das eigentliche Fest — Essen, Familie, Traditionen", "example": "Thanksgiving-Tisch, Weihnachtsbaum, Halloween-Kostuem", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Kerzen + Raumlicht", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Erklaere in die Kamera wie sich der Feiertag von Deutschland unterscheidet", "example": "'Weihnachten hier ist komplett anders: Hier oeffnet man Geschenke am 25.!'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gutes Frontlicht", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige dein Kostuem, Outfit oder besonderes Feiertags-Essen", "example": "Outfit-Check, Teller mit speziellem Essen, Deko-Detail", "duration_hint": "3-5 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Helles, festliches Licht", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Sage was du am meisten vermisst und was du am meisten liebst an dem Fest hier", "example": "Ehrlicher Vergleich: 'Ich vermisse... aber ich liebe...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gemuetliches Setting", "content_pillar": "erfahrungsberichte"},
    ],
    "school_event": [
        {"description_for_student": "Filme die Atmosphaere des Events — Menschenmenge, Deko, Stimmung", "example": "Schwenk ueber die Zuschauer, Feld/Buehne, Jubel", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Veranstaltungslicht nutzen", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige dich und deine Freunde beim Event", "example": "Gruppen-Selfie, gemeinsames Anfeuern, Tanzen", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Front-Kamera mit Licht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme den Hoehepunkt des Events", "example": "Tor, Tanzperformance, Homecoming-Koenig/Koenigin, Gewinner", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Schnelle Bewegungen = gutes Licht noetig", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Erklaere in die Kamera was das Event ist (deutsche Zuschauer kennen das nicht!)", "example": "'In den USA gibt es sowas wie Prom/Homecoming/Pep Rally...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Ruhiger Moment suchen", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige dein Outfit oder deine Vorbereitung fuer das Event", "example": "Getting Ready Montage, Outfit-Check, Make-up", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gutes Raumlicht", "content_pillar": "erfahrungsberichte"},
    ],
    "farewell": [
        {"description_for_student": "Filme deinen letzten Schultag — Abschied von Freunden und Lehrern", "example": "Umarmungen, Unterschriften sammeln, letzte Momente", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerliches Licht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige wie du dein Zimmer zusammenpackst", "example": "Zeitraffer vom Packen, vorher/nachher", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Raumlicht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Sage in die Kamera was dir dieses Jahr bedeutet hat", "example": "Emotionaler Rueckblick: 'Dieses Jahr hat mein Leben veraendert...'", "duration_hint": "15-30 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Schoenes natuerliches Licht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Filme den Abschied von deiner Gastfamilie", "example": "Umarmung, vielleicht Traenen, Winken", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Mache ein Montage-Video deiner besten Momente", "example": "10-15 kurze Clips aus dem ganzen Jahr hintereinander", "duration_hint": "15-30 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Mix aus verschiedenen Lichtsituationen", "content_pillar": "erfahrungsberichte"},
    ],
    "alumni": [
        {"description_for_student": "Gib 3 Tipps fuer neue Austauschschueler", "example": "'Mein Tipp Nr. 1: Sag zu allem ja! Nr. 2: ...'", "duration_hint": "15-30 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Ruhiger Hintergrund, gutes Licht", "content_pillar": "tipps_tricks"},
        {"description_for_student": "Vergleiche: Wer warst du vorher vs. wer bist du jetzt?", "example": "Vorher/Nachher Style mit alten Fotos + neue Aufnahme", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gleichmaessiges Licht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Beantworte eine haeufig gestellte Frage ueber das Auslandsjahr", "example": "'Die Frage die ich am meisten hoere ist... und die Antwort ist...'", "duration_hint": "15-20 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Frontlicht, Kamera auf Augenhoehe", "content_pillar": "faq"},
        {"description_for_student": "Zeige Souvenirs oder Erinnerungsstuecke und erzaehle die Geschichte dahinter", "example": "Gegenstände auf dem Tisch, nimm eins auf und erzaehle", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Helles Raumlicht", "content_pillar": "erfahrungsberichte"},
    ],
    "general": [
        {"description_for_student": "Zeige einen schoenen Ort in deiner Umgebung", "example": "Panorama-Schwenk, Zeitraffer eines Sonnenuntergangs", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Golden Hour fuer beste Ergebnisse", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Filme etwas Lustiges oder Unerwartetes aus deinem Alltag", "example": "Witzige Situation, ueberraschendes Erlebnis", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Spontan ist OK!", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Mache ein kurzes Update — wie geht es dir gerade?", "example": "Selfie-Modus: 'Hey, kurzes Update aus [Land]...'", "duration_hint": "10-15 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Gutes Frontlicht", "content_pillar": "erfahrungsberichte"},
        {"description_for_student": "Zeige dein Lieblingsessen oder einen Lieblings-Ort", "example": "Close-Up vom Essen oder Panorama vom Ort", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerliches Licht", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Filme etwas das du vorher nie gemacht haettest", "example": "Neue Sportart, neues Essen, neues Hobby", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Beliebig, Authentizitaet zaehlt", "content_pillar": "erfahrungsberichte"},
    ],
}

# Seasonal adjustments: month -> suggested content types
SEASONAL_SUGGESTIONS = {
    1: ["holiday", "school_day", "cultural_moment"],       # January
    2: ["school_day", "cultural_moment", "school_event"],   # February
    3: ["school_day", "cultural_moment", "host_family"],    # March
    4: ["cultural_moment", "school_event", "host_family"],  # April
    5: ["school_event", "farewell", "host_family"],         # May
    6: ["farewell", "alumni", "general"],                   # June
    7: ["alumni", "general"],                               # July
    8: ["arrival_story", "first_day_school", "host_family"],# August
    9: ["first_day_school", "school_day", "host_family"],   # September
    10: ["school_day", "cultural_moment", "holiday"],       # October
    11: ["holiday", "school_event", "host_family"],         # November
    12: ["holiday", "cultural_moment", "host_family"],      # December
}

COUNTRY_SPECIFIC_SHOTS = {
    "usa": [
        {"description_for_student": "Filme den Yellow School Bus von aussen", "example": "Bus faehrt vor, Tueren oeffnen sich", "duration_hint": "3-5 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Morgenlicht", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige eine typische amerikanische Portion Essen", "example": "Riesiger Burger, Diner-Teller, Super-Size Drink", "duration_hint": "3-5 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Restaurant-Licht", "content_pillar": "laender_spotlight"},
    ],
    "canada": [
        {"description_for_student": "Filme eine kanadische Landschaft — Berge, Seen, Waelder", "example": "Panorama-Schwenk ueber Rocky Mountains oder Lake", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Golden Hour ideal", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige ein typisch kanadisches Erlebnis (Hockey, Ahornsirup, Tim Hortons)", "example": "Beim Eishockey, Ahornsirup auf Schnee, Tims Kaffee", "duration_hint": "5-8 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht oder Hallenbeleuchtung", "content_pillar": "laender_spotlight"},
    ],
    "australia": [
        {"description_for_student": "Filme den Strand oder das Meer", "example": "Wellen, Surfer, Sonnenuntergang am Strand", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Sonnenauf-/untergang", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige Australiens Tierwelt (Koalas, Kaengurus, Papageien)", "example": "Tier in freier Wildbahn oder im Sanctuary", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Tageslicht", "content_pillar": "laender_spotlight"},
    ],
    "newzealand": [
        {"description_for_student": "Filme die unglaubliche Natur Neuseelands", "example": "Berge, Fjorde, gruene Wiesen, Vulkane", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Golden Hour, klarer Himmel", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige einen Maori-Kulturmoment oder Haka", "example": "Haka-Auffuehrung, Marae-Besuch, Greenstone-Anhaenger", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Natuerlich, authentisch", "content_pillar": "laender_spotlight"},
    ],
    "ireland": [
        {"description_for_student": "Filme die gruene irische Landschaft", "example": "Gruene Huegel, Steinmauern, Schafe, Klippen", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Bewolktes Licht ist typisch irisch!", "content_pillar": "laender_spotlight"},
        {"description_for_student": "Zeige etwas typisch Irisches (Pub, GAA Match, Irish Music)", "example": "Pub-Atmosphaere (Musik!), Hurling/GAA Spiel, Traditional Music Session", "duration_hint": "5-10 Sekunden", "orientation": "Hochformat 9:16", "lighting_tip": "Stimmungsvolles Pub-Licht", "content_pillar": "laender_spotlight"},
    ],
}


def _generate_shots(content_type: str, country: str | None, season: str | None) -> list[dict]:
    """Generate shot list based on content type, country, and season."""
    base_shots = SHOT_TEMPLATES.get(content_type, SHOT_TEMPLATES["general"])

    # Select 5-8 shots from the base templates
    num_shots = min(random.randint(5, 8), len(base_shots))
    selected = random.sample(base_shots, num_shots)

    # Add 1-2 country-specific shots if applicable
    if country and country in COUNTRY_SPECIFIC_SHOTS:
        country_shots = COUNTRY_SPECIFIC_SHOTS[country]
        for cs in random.sample(country_shots, min(2, len(country_shots))):
            selected.append(cs)

    # Number the shots
    for i, shot in enumerate(selected):
        shot["shot_number"] = i + 1

    return selected


def _get_seasonal_content_types() -> list[str]:
    """Return suggested content types based on current month."""
    month = datetime.now().month
    return SEASONAL_SUGGESTIONS.get(month, ["general"])


def _shot_list_to_dict(sl: ShotList) -> dict:
    """Convert ShotList model to dict."""
    shots = []
    if sl.shots:
        try:
            shots = json.loads(sl.shots) if isinstance(sl.shots, str) else sl.shots
        except (json.JSONDecodeError, TypeError):
            shots = []

    return {
        "id": sl.id,
        "title": sl.title,
        "description": sl.description,
        "student_id": sl.student_id,
        "student_name": sl.student_name,
        "country": sl.country,
        "content_type": sl.content_type,
        "shots": shots,
        "due_date": sl.due_date.isoformat() if sl.due_date else None,
        "season": sl.season,
        "status": sl.status,
        "video_script_id": sl.video_script_id,
        "share_token": sl.share_token,
        "is_shared": sl.is_shared,
        "shots_completed": sl.shots_completed,
        "shots_total": sl.shots_total,
        "created_at": sl.created_at.isoformat() if sl.created_at else None,
        "updated_at": sl.updated_at.isoformat() if sl.updated_at else None,
    }


# ──────────────────────────────────────────────
# API Endpoints
# ──────────────────────────────────────────────

@router.get("/content-types")
async def get_content_types(user_id: int = Depends(get_current_user_id)):
    """Return available content types for shot list generation."""
    seasonal = _get_seasonal_content_types()
    return {
        "content_types": [
            {
                "id": k,
                "label": v["label"],
                "description": v["description"],
                "season_hint": v["season_hint"],
                "is_seasonal": k in seasonal,
            }
            for k, v in CONTENT_TYPES.items()
        ],
        "seasonal_suggestions": seasonal,
    }


@router.post("/generate")
async def generate_shot_list(
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a shot list for a student.

    Body:
    - content_type (str, required): Content type ID
    - country (str, optional): Country code
    - season (str, optional): Season hint
    - student_name (str, optional): Student name
    - student_id (int, optional): Student database ID
    - video_script_id (int, optional): Link to a video script
    """
    content_type = request.get("content_type", "general")
    if content_type not in CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid content_type: {content_type}")

    country = request.get("country")
    season = request.get("season")
    student_name = request.get("student_name", "")
    student_id = request.get("student_id")
    video_script_id = request.get("video_script_id")

    # Validate student exists if provided
    if student_id:
        result = await db.execute(select(Student).where(Student.id == student_id))
        student = result.scalar_one_or_none()
        if student:
            if not student_name:
                student_name = student.name
            if not country:
                country = student.country
        else:
            student_id = None  # Invalid student ID, clear it

    # Validate video script exists if provided
    if video_script_id:
        result = await db.execute(
            select(VideoScript).where(
                VideoScript.id == video_script_id,
                VideoScript.user_id == user_id,
            )
        )
        if not result.scalar_one_or_none():
            video_script_id = None  # Invalid, clear it

    # Generate shots
    shots = _generate_shots(content_type, country, season)

    ct_info = CONTENT_TYPES[content_type]
    country_name = COUNTRY_NAMES.get(country, "")
    title_parts = [ct_info["label"]]
    if student_name:
        title_parts.append(f"fuer {student_name}")
    if country_name:
        title_parts.append(f"({country_name})")
    title = " ".join(title_parts)

    # Create shot list
    share_token = secrets.token_urlsafe(32)
    shot_list = ShotList(
        user_id=user_id,
        title=title,
        description=ct_info["description"],
        student_id=student_id,
        student_name=student_name,
        country=country,
        content_type=content_type,
        shots=json.dumps(shots, ensure_ascii=False),
        season=season or _get_seasonal_content_types()[0] if _get_seasonal_content_types() else None,
        status="active",
        video_script_id=video_script_id,
        share_token=share_token,
        is_shared=False,
        shots_completed=0,
        shots_total=len(shots),
    )
    db.add(shot_list)
    await db.commit()
    await db.refresh(shot_list)

    logger.info("Shot list created: id=%d, content_type=%s, shots=%d", shot_list.id, content_type, len(shots))
    return _shot_list_to_dict(shot_list)


@router.post("/from-script/{script_id}")
async def generate_from_script(
    script_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a shot list from an existing video script (V-06 connection).

    Extracts visual descriptions from script scenes and creates corresponding
    filming instructions.
    """
    result = await db.execute(
        select(VideoScript).where(
            VideoScript.id == script_id,
            VideoScript.user_id == user_id,
        )
    )
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Video script not found")

    # Parse scenes
    scenes = json.loads(script.scenes) if isinstance(script.scenes, str) else script.scenes

    # Create shots from scene visual descriptions
    shots = []
    for i, scene in enumerate(scenes):
        shot = {
            "shot_number": i + 1,
            "description_for_student": f"Filme: {scene.get('visual_description', 'Szene nach Script')}",
            "example": scene.get("b_roll_suggestion", scene.get("text_overlay", "")),
            "duration_hint": f"{scene.get('end_time', 0) - scene.get('start_time', 0)} Sekunden",
            "orientation": "Hochformat 9:16",
            "lighting_tip": "Siehe Musik-Notiz: " + scene.get("music_note", "Natuerlich"),
            "content_pillar": "erfahrungsberichte",
        }
        shots.append(shot)

    country_name = COUNTRY_NAMES.get(script.country, "")
    title = f"Shot-List aus Script: {script.title}"
    if country_name:
        title += f" ({country_name})"

    share_token = secrets.token_urlsafe(32)
    shot_list = ShotList(
        user_id=user_id,
        title=title,
        description=f"Automatisch aus Video-Script '{script.title}' generiert",
        country=script.country,
        content_type="general",
        shots=json.dumps(shots, ensure_ascii=False),
        status="active",
        video_script_id=script_id,
        share_token=share_token,
        is_shared=False,
        shots_completed=0,
        shots_total=len(shots),
    )
    db.add(shot_list)
    await db.commit()
    await db.refresh(shot_list)

    logger.info("Shot list from script created: id=%d, script_id=%d, shots=%d", shot_list.id, script_id, len(shots))
    return _shot_list_to_dict(shot_list)


@router.get("")
async def list_shot_lists(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    country: Optional[str] = None,
    student_id: Optional[int] = None,
):
    """List shot lists with optional filtering."""
    query = select(ShotList).where(ShotList.user_id == user_id)

    if status:
        query = query.where(ShotList.status == status)
    if country:
        query = query.where(ShotList.country == country)
    if student_id:
        query = query.where(ShotList.student_id == student_id)

    query = query.order_by(desc(ShotList.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    items = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(ShotList).where(ShotList.user_id == user_id)
    if status:
        count_query = count_query.where(ShotList.status == status)
    if country:
        count_query = count_query.where(ShotList.country == country)
    if student_id:
        count_query = count_query.where(ShotList.student_id == student_id)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return {
        "items": [_shot_list_to_dict(sl) for sl in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{shot_list_id}")
async def get_shot_list(
    shot_list_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single shot list by ID."""
    result = await db.execute(
        select(ShotList).where(
            ShotList.id == shot_list_id,
            ShotList.user_id == user_id,
        )
    )
    sl = result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Shot list not found")
    return _shot_list_to_dict(sl)


@router.put("/{shot_list_id}")
async def update_shot_list(
    shot_list_id: int,
    request: dict,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a shot list."""
    result = await db.execute(
        select(ShotList).where(
            ShotList.id == shot_list_id,
            ShotList.user_id == user_id,
        )
    )
    sl = result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Shot list not found")

    if "title" in request:
        sl.title = request["title"]
    if "status" in request:
        sl.status = request["status"]
    if "shots" in request:
        sl.shots = json.dumps(request["shots"], ensure_ascii=False)
        sl.shots_total = len(request["shots"])
    if "shots_completed" in request:
        sl.shots_completed = request["shots_completed"]
    if "is_shared" in request:
        sl.is_shared = request["is_shared"]

    await db.commit()
    await db.refresh(sl)
    return _shot_list_to_dict(sl)


@router.delete("/{shot_list_id}")
async def delete_shot_list(
    shot_list_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a shot list."""
    result = await db.execute(
        select(ShotList).where(
            ShotList.id == shot_list_id,
            ShotList.user_id == user_id,
        )
    )
    sl = result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Shot list not found")

    await db.delete(sl)
    await db.commit()
    return {"success": True, "deleted_id": shot_list_id}


@router.post("/{shot_list_id}/share")
async def toggle_share(
    shot_list_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Toggle sharing for a shot list."""
    result = await db.execute(
        select(ShotList).where(
            ShotList.id == shot_list_id,
            ShotList.user_id == user_id,
        )
    )
    sl = result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Shot list not found")

    sl.is_shared = not sl.is_shared
    if not sl.share_token:
        sl.share_token = secrets.token_urlsafe(32)

    await db.commit()
    await db.refresh(sl)
    return _shot_list_to_dict(sl)


# ──────────────────────────────────────────────
# Public (no auth) endpoint for shared shot lists
# ──────────────────────────────────────────────

@router.get("/shared/{share_token}")
async def get_shared_shot_list(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a shared shot list by its public token (no auth required).

    This endpoint is for students to view their shot list on their phone.
    """
    result = await db.execute(
        select(ShotList).where(
            ShotList.share_token == share_token,
            ShotList.is_shared == True,
        )
    )
    sl = result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Shot list not found or not shared")

    data = _shot_list_to_dict(sl)
    # Remove internal fields for public view
    del data["share_token"]
    return data


@router.post("/shared/{share_token}/complete-shot")
async def complete_shot_public(
    share_token: str,
    request: dict,
    db: AsyncSession = Depends(get_db),
):
    """Mark a shot as completed (public endpoint for students).

    Body:
    - shot_number (int): The shot number to mark as completed
    """
    result = await db.execute(
        select(ShotList).where(
            ShotList.share_token == share_token,
            ShotList.is_shared == True,
        )
    )
    sl = result.scalar_one_or_none()
    if not sl:
        raise HTTPException(status_code=404, detail="Shot list not found or not shared")

    shot_number = request.get("shot_number")
    if not shot_number:
        raise HTTPException(status_code=400, detail="shot_number is required")

    # Parse shots, mark as completed
    shots = json.loads(sl.shots) if isinstance(sl.shots, str) else (sl.shots or [])
    completed_count = 0
    for shot in shots:
        if shot.get("shot_number") == shot_number:
            shot["completed"] = True
        if shot.get("completed"):
            completed_count += 1

    sl.shots = json.dumps(shots, ensure_ascii=False)
    sl.shots_completed = completed_count

    # Auto-complete if all shots done
    if completed_count >= sl.shots_total:
        sl.status = "completed"

    await db.commit()
    await db.refresh(sl)

    data = _shot_list_to_dict(sl)
    del data["share_token"]
    return data
