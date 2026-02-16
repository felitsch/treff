"""
TREFF Sprachreisen - Text Content Generator

Generates structured German text content for social media posts based on
category, country, topic, and tone.

Uses Gemini 2.5 Flash for AI-powered text generation when an API key is available.
Falls back to rule-based content templates when no API key is configured or API errors occur.
"""

import json
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)

# Country-specific facts and content
COUNTRY_DATA = {
    "usa": {
        "name": "USA",
        "flag": "🇺🇸",
        "adjective": "amerikanisches",
        "highlights": [
            "Typisches High School Leben mit Cheerleadern und Football",
            "Riesige Schulen mit Hunderten von Wahlfaechern",
            "Homecoming, Prom und Spring Break erleben",
            "Gastfamilien, die dich wie ein eigenes Kind aufnehmen",
            "Road Trips durch atemberaubende Landschaften",
        ],
        "facts": [
            "Die USA haben ueber 26.000 High Schools",
            "Das Schuljahr beginnt im August oder September",
            "Sportteams sind das Herzstuck jeder High School",
            "Lunch wird in riesigen Cafeterias serviert",
            "School Spirit ist ein echtes Phaenomen",
        ],
        "cities": ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"],
        "price": "ab 13.800 EUR",
    },
    "canada": {
        "name": "Kanada",
        "flag": "🇨🇦",
        "adjective": "kanadisches",
        "highlights": [
            "Bilinguale Erfahrung: Englisch und Franzoesisch",
            "Atemberaubende Natur von Rocky Mountains bis Niagara Falls",
            "Freundliche und weltoffene Gastfamilien",
            "Exzellentes Schulsystem mit modernen Schulen",
            "Multikulturelles Land mit Menschen aus aller Welt",
        ],
        "facts": [
            "Kanada ist das zweitgroesste Land der Welt",
            "Zwei Amtssprachen: Englisch und Franzoesisch",
            "Kanadische Schulen gehoeren zu den besten weltweit",
            "Das Schuljahr hat zwei Semester",
            "Hockey ist der Nationalsport",
        ],
        "cities": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
        "price": "ab 15.200 EUR",
    },
    "australia": {
        "name": "Australien",
        "flag": "🇦🇺",
        "adjective": "australisches",
        "highlights": [
            "Surfen, Strand und Sonnenschein das ganze Jahr",
            "Einzigartige Tierwelt: Koalas, Kaengurus und mehr",
            "Relaxte Lebensart und offene Kultur",
            "Moderne Schulen mit innovativen Lernmethoden",
            "Great Barrier Reef und Outback-Abenteuer",
        ],
        "facts": [
            "Das Schuljahr beginnt im Januar (Suedhalbkugel)",
            "Australien hat ueber 9.000 Straende",
            "School Uniforms sind Pflicht an den meisten Schulen",
            "Outdoor Education ist ein beliebtes Fach",
            "Australier sagen 'mate' zu jedem",
        ],
        "cities": ["Sydney", "Melbourne", "Brisbane", "Perth", "Gold Coast"],
        "price": "ab 18.900 EUR",
    },
    "newzealand": {
        "name": "Neuseeland",
        "flag": "🇳🇿",
        "adjective": "neuseelaendisches",
        "highlights": [
            "Spektakulaere Landschaften wie aus Herr der Ringe",
            "Maori-Kultur hautnah erleben",
            "Kleine Klassen und persoenliche Betreuung",
            "Abenteuer-Aktivitaeten: Bungee, Rafting, Wandern",
            "Sicherste Laender der Welt fuer Austauschschueler",
        ],
        "facts": [
            "Neuseeland hat mehr Schafe als Menschen",
            "Die Maori-Kultur ist Teil des Schulalltags",
            "Das Schuljahr hat vier Terms",
            "Outdoor Education ist ein Pflichtfach",
            "Kiwi ist der Spitzname fuer Neuseelaender",
        ],
        "cities": ["Auckland", "Wellington", "Christchurch", "Queenstown", "Rotorua"],
        "price": "ab 19.500 EUR",
    },
    "ireland": {
        "name": "Irland",
        "flag": "🇮🇪",
        "adjective": "irisches",
        "highlights": [
            "Gruene Huegel, Klippen und mystische Landschaften",
            "Warmherzige Gastfamilien mit irischem Humor",
            "Europaeisches Auslandsjahr ohne langen Flug",
            "Gaelische Kultur und Musikszene entdecken",
            "Kleine Schulen mit familiaerem Flair",
        ],
        "facts": [
            "Irland ist nur 2 Flugstunden von Deutschland entfernt",
            "Gaelisch (Irisch) ist Pflichtfach an allen Schulen",
            "Das Schuljahr laeuft von September bis Juni",
            "Schuluniformen sind in Irland ueblich",
            "Irland hat eine der juengsten Bevoelkerungen Europas",
        ],
        "cities": ["Dublin", "Cork", "Galway", "Limerick", "Killarney"],
        "price": "ab 14.500 EUR",
    },
}

# Category-specific content generators
CATEGORY_CONTENT = {
    "laender_spotlight": {
        "headline_templates": [
            "Dein Highschool-Jahr in {country}",
            "{country}: Dein Abenteuer wartet!",
            "Entdecke {country} mit TREFF",
            "Highschool {country} – Alles was du wissen musst",
            "Warum {country}? 5 Gruende fuer dein Auslandsjahr",
        ],
        "subheadline_templates": [
            "Das erwartet dich in {country}",
            "So sieht dein Alltag aus",
            "Highschool-Leben wie im Film",
            "Dein Weg ins Ausland startet hier",
        ],
        "cta_templates": [
            "Jetzt informieren!",
            "Link in Bio fuer mehr Infos",
            "Bewirb dich jetzt bei TREFF!",
            "Bereit fuer {country}? DM uns!",
        ],
    },
    "erfahrungsberichte": {
        "headline_templates": [
            "Mein Jahr in {country} – Ein Erfahrungsbericht",
            '"Das Beste, was ich je gemacht habe"',
            "Von Deutschland nach {country}: Meine Story",
            "{name}s Auslandsjahr in {country}",
        ],
        "subheadline_templates": [
            "TREFF-Alumna berichtet",
            "Ein Schuljahr, das alles veraendert hat",
            "Erfahrungen, die ein Leben lang bleiben",
        ],
        "cta_templates": [
            "Willst du auch? Link in Bio!",
            "Deine Geschichte beginnt bei TREFF",
            "Bewirb dich jetzt!",
        ],
    },
    "infografiken": {
        "headline_templates": [
            "{country_a} vs. {country_b} – Der Vergleich",
            "5 Fakten ueber Highschool in {country}",
            "Auslandsjahr in Zahlen",
            "Was kostet ein Auslandsjahr?",
        ],
        "subheadline_templates": [
            "Die wichtigsten Unterschiede",
            "Das solltest du wissen",
            "Alle Fakten auf einen Blick",
        ],
        "cta_templates": [
            "Speicher dir diesen Post!",
            "Teile das mit deinen Freunden!",
            "Mehr Infos auf treff-sprachreisen.de",
        ],
    },
    "fristen_cta": {
        "headline_templates": [
            "Bewirb dich JETZT fuer {year}!",
            "⏰ Nur noch wenige Plaetze fuer {country}!",
            "Deadline: Bewerbungsschluss naht!",
            "Stipendien-Chance fuer {country}!",
        ],
        "subheadline_templates": [
            "Sichere dir deinen Platz",
            "Nicht verpassen!",
            "Die Zeit laeuft...",
        ],
        "cta_templates": [
            "Jetzt bewerben! Link in Bio",
            "DM uns fuer mehr Infos!",
            "Termin vereinbaren: treff-sprachreisen.de",
        ],
    },
    "tipps_tricks": {
        "headline_templates": [
            "Packliste fuer dein Auslandsjahr",
            "5 Tipps fuer dein Highschool-Jahr",
            "So bereitest du dich vor",
            "Gastfamilien-Tipps: Das solltest du wissen",
        ],
        "subheadline_templates": [
            "Von TREFF-Alumni getestet",
            "Das haetten wir gern vorher gewusst",
            "Insider-Tipps fuer dein Abenteuer",
        ],
        "cta_templates": [
            "Speichern fuer spaeter!",
            "Teile das mit anderen Austauschschuelern!",
            "Mehr Tipps auf unserem Blog",
        ],
    },
    "faq": {
        "headline_templates": [
            "Haeufig gestellte Fragen",
            "FAQ: Auslandsjahr mit TREFF",
            "Das wirst du am haeufigsten gefragt",
            "Deine Fragen – unsere Antworten",
        ],
        "subheadline_templates": [
            "Wir beantworten alles",
            "Keine Frage ist zu dumm",
            "Eltern fragen, TREFF antwortet",
        ],
        "cta_templates": [
            "Noch Fragen? DM uns!",
            "Beratungsgespraech vereinbaren",
            "Alle FAQs auf unserer Website",
        ],
    },
    "foto_posts": {
        "headline_templates": [
            "Impressionen aus {country}",
            "So sieht Highschool in {country} aus",
            "Memories from {country}",
            "TREFF-Schueler unterwegs in {country}",
        ],
        "subheadline_templates": [
            "Echte Momente, echte Erlebnisse",
            "Bilder sagen mehr als Worte",
        ],
        "cta_templates": [
            "Willst du das auch erleben?",
            "Dein Abenteuer wartet!",
            "Link in Bio",
        ],
    },
    "reel_tiktok_thumbnails": {
        "headline_templates": [
            "Das hat NIEMAND erwartet...",
            "3 Dinge, die ich in {country} gelernt habe",
            "Erwartung vs. Realitaet: Auslandsjahr",
            "POV: Dein erster Tag an einer {adj} High School",
        ],
        "subheadline_templates": [
            "Swipe fuer mehr!",
            "Du wirst nicht glauben was passiert ist",
        ],
        "cta_templates": [
            "Folge fuer mehr!",
            "Teil 2 kommt morgen!",
            "Kommentiere deine Erfahrung!",
        ],
    },
    "story_posts": {
        "headline_templates": [
            "Quick Poll: Welches Land?",
            "Countdown: Noch {days} Tage!",
            "Behind the Scenes bei TREFF",
            "Frage des Tages",
        ],
        "subheadline_templates": [
            "Tippe fuer deine Antwort!",
            "Swipe up fuer mehr",
        ],
        "cta_templates": [
            "Abstimmen!",
            "Swipe up!",
            "Antwort in den DMs!",
        ],
    },
}

# Generic body text snippets per category
BODY_TEXTS = {
    "laender_spotlight": [
        "Ein Highschool-Aufenthalt in {country} ist mehr als nur Schule – es ist ein Abenteuer, das dein Leben veraendern wird. Du tauchst ein in eine neue Kultur, findest Freunde fuers Leben und wirst selbststaendiger als je zuvor.",
        "Stell dir vor: Jeden Morgen gehst du in eine {adj} High School, nachmittags trainierst du im Sportteam, und abends isst du mit deiner Gastfamilie. Das ist Alltag fuer TREFF-Schueler in {country}.",
        "{country} bietet dir eine einzigartige Mischung aus Bildung, Abenteuer und persoenlicher Entwicklung. Mit TREFF Sprachreisen bist du bestens betreut – von der Bewerbung bis zur Rueckkehr.",
    ],
    "erfahrungsberichte": [
        "Als ich vor einem Jahr meine Koffer gepackt habe, war ich mega aufgeregt und ein bisschen aengstlich. Heute kann ich sagen: Es war die beste Entscheidung meines Lebens!",
        "Meine Gastfamilie hat mich vom ersten Tag an aufgenommen wie ein eigenes Kind. Wir haben zusammen gekocht, Ausfluege gemacht und ich habe so viel ueber die Kultur gelernt.",
        "Die Schule war komplett anders als in Deutschland – in einem guten Sinne! Ich konnte Faecher waehlen, die es bei uns gar nicht gibt, und habe mich in Clubs engagiert.",
    ],
    "infografiken": [
        "Wusstest du, dass ueber 10.000 deutsche Schueler jedes Jahr ein Auslandsjahr machen? Hier sind die wichtigsten Fakten und Zahlen rund um deinen Highschool-Aufenthalt.",
        "Die Kosten fuer ein Auslandsjahr variieren je nach Land, Programm und Dauer. Mit TREFF findest du das perfekte Angebot fuer dein Budget.",
    ],
    "fristen_cta": [
        "Die Plaetze fuer das naechste Schuljahr sind begrenzt! Bewirb dich jetzt, um deinen Traum vom Auslandsjahr zu verwirklichen. TREFF begleitet dich durch den gesamten Prozess.",
        "Frueh bewerben lohnt sich: Du hast bessere Chancen auf dein Wunschland und kannst dich in Ruhe vorbereiten. Starte jetzt!",
    ],
    "tipps_tricks": [
        "Tipp 1: Packe nicht zu viel ein! Du wirst vor Ort shoppen und brauchst Platz fuer Souvenirs auf dem Rueckweg.",
        "Sei offen fuer Neues! Die besten Erfahrungen machst du, wenn du dich auf die Kultur deines Gastlandes einlaesst.",
        "Halte Kontakt mit deiner Familie, aber uebertreibe es nicht. Zu viel Heimweh-Telefonate koennen das Einleben erschweren.",
    ],
    "faq": [
        "Frage: Wie finde ich die richtige Gastfamilie? Antwort: TREFF waehlt Gastfamilien sorgfaeltig aus und matched sie mit deinem Profil. Du kannst vorher Kontakt aufnehmen und Fragen stellen.",
        "Frage: Was kostet ein Auslandsjahr? Antwort: Die Kosten haengen vom Land und Programm ab. TREFF bietet transparente Preise und Stipendienmoeglichkeiten.",
    ],
    "foto_posts": [
        "Echte Momente aus dem Auslandsjahr unserer TREFF-Schueler. Diese Erinnerungen bleiben fuer immer!",
    ],
    "reel_tiktok_thumbnails": [
        "Watch bis zum Ende fuer die krasseste Erkenntnis ueber Auslandsjahre!",
    ],
    "story_posts": [
        "Schnelle Umfrage fuer unsere Community! Tippt auf eure Antwort!",
    ],
}

HASHTAGS_INSTAGRAM = [
    "#Auslandsjahr", "#HighschoolYear", "#TREFFSprachreisen",
    "#ExchangeStudent", "#Gastfamilie", "#Highschool",
    "#AustauschjahreGermany", "#StudyAbroad", "#Schueleraustausch",
    "#GapYear", "#HighschoolAbroad", "#Fernweh",
    "#Auslandserfahrung", "#Weltentdecker", "#Abenteuer",
]

HASHTAGS_COUNTRY = {
    "usa": ["#HighschoolUSA", "#AmericanHighSchool", "#USAExchange", "#StudyInUSA", "#AmericanDream"],
    "canada": ["#HighschoolKanada", "#CanadaExchange", "#StudyInCanada", "#CanadianSchool", "#OCanada"],
    "australia": ["#HighschoolAustralien", "#AussieExchange", "#StudyInAustralia", "#AustralianSchool", "#DownUnder"],
    "newzealand": ["#HighschoolNeuseeland", "#NZExchange", "#StudyInNZ", "#KiwiLife", "#AotearoaAdventure"],
    "ireland": ["#HighschoolIrland", "#IrelandExchange", "#StudyInIreland", "#IrishSchool", "#EmeraldIsle"],
}

HASHTAGS_TIKTOK = [
    "#auslandsjahr", "#highschoolyear", "#exchangestudent",
    "#studyabroad", "#highschool", "#schueleraustausch",
    "#fyp", "#foryou", "#viral", "#trending",
]

ALUMNI_NAMES = [
    "Lena", "Mia", "Emma", "Sophie", "Hannah",
    "Jonas", "Lukas", "Finn", "Maximilian", "Leon",
]

# Category display names for Gemini prompts
CATEGORY_DISPLAY_NAMES = {
    "laender_spotlight": "Laender-Spotlight",
    "erfahrungsberichte": "Erfahrungsberichte",
    "infografiken": "Infografiken",
    "fristen_cta": "Fristen & Call-to-Action",
    "tipps_tricks": "Tipps & Tricks",
    "faq": "FAQ (Haeufig gestellte Fragen)",
    "foto_posts": "Foto-Posts",
    "reel_tiktok_thumbnails": "Reel/TikTok Thumbnails",
    "story_posts": "Story-Posts",
}


def _build_personality_prompt_section(personality_preset: dict) -> str:
    """Build a personality-specific prompt section from a student's personality preset.

    Args:
        personality_preset: dict with keys:
            - tone (str): e.g. 'witzig', 'emotional', 'motivierend'
            - humor_level (int): 1-5, where 1=kaum Humor, 5=sehr humorvoll
            - emoji_usage (str): 'none', 'minimal', 'moderate', 'heavy'
            - perspective (str): 'first_person' or 'third_person'
            - catchphrases (list[str]): characteristic phrases to use

    Returns:
        A string to append to the system prompt for personality customization.
    """
    sections = []

    # Tone override
    tone = personality_preset.get("tone", "")
    if tone:
        sections.append(f"PERSOENLICHKEITS-TON: Schreibe im Stil '{tone}'.")

    # Humor level
    humor_level = personality_preset.get("humor_level", 3)
    humor_descriptions = {
        1: "Kaum Humor verwenden. Sachlich und ernst bleiben.",
        2: "Gelegentlich leichten Humor einstreuen, aber hauptsaechlich sachlich.",
        3: "Ausgewogener Mix aus Humor und Information.",
        4: "Deutlich humorvoll schreiben. Witzige Vergleiche und Wortspiele nutzen.",
        5: "Maximal humorvoll! Alles mit Humor und Witz wuerzen. Memes, uebertriebene Vergleiche, Pop-Kultur-Referenzen.",
    }
    humor_desc = humor_descriptions.get(humor_level, humor_descriptions[3])
    sections.append(f"HUMOR-LEVEL ({humor_level}/5): {humor_desc}")

    # Emoji usage
    emoji_usage = personality_preset.get("emoji_usage", "moderate")
    emoji_instructions = {
        "none": "Verwende KEINE Emojis. Nur reinen Text.",
        "minimal": "Verwende maximal 1-2 dezente Emojis pro Caption (z.B. Landesflagge).",
        "moderate": "Verwende 3-5 passende Emojis pro Caption.",
        "heavy": "Verwende viele Emojis (6-10 pro Caption). Emojis sollen den Text auflockern und Energie vermitteln.",
    }
    emoji_inst = emoji_instructions.get(emoji_usage, emoji_instructions["moderate"])
    sections.append(f"EMOJI-NUTZUNG ({emoji_usage}): {emoji_inst}")

    # Perspective
    perspective = personality_preset.get("perspective", "first_person")
    if perspective == "first_person":
        sections.append("PERSPEKTIVE: Schreibe aus der Ich-Perspektive. Der Student erzaehlt selbst ('Ich habe erlebt...', 'Mein erster Tag...').")
    else:
        name = personality_preset.get("student_name", "der Student")
        sections.append(f"PERSPEKTIVE: Schreibe in der dritten Person ueber {name}. ('{name} hat erlebt...', 'Sein/Ihr erster Tag...').")

    # Catchphrases
    catchphrases = personality_preset.get("catchphrases", [])
    if catchphrases and isinstance(catchphrases, list):
        phrases_str = ", ".join(f'"{p}"' for p in catchphrases[:5])
        sections.append(
            f"TYPISCHE PHRASEN: Baue folgende charakteristische Ausdruecke natuerlich in den Text ein: {phrases_str}. "
            "Nicht alle auf einmal verwenden, aber mindestens 1-2 pro Post."
        )

    return "\n\n".join(sections)


def _build_gemini_system_prompt(tone: str, personality_preset: dict | None = None) -> str:
    """Build the system prompt for Gemini with TREFF brand guidelines."""
    tone_instructions = {
        "serioess": (
            "Schreibe in einem serioesen, vertrauenswuerdigen Ton. "
            "Die Zielgruppe sind hier primaer die Eltern der Schueler. "
            "Verwende Sie-Anrede wo passend. Betone Sicherheit, Erfahrung seit 1984, "
            "und professionelle Betreuung. Kein Slang, keine uebertriebenen Emojis. "
            "Maximal 2-3 dezente Emojis pro Caption."
        ),
        "jugendlich": (
            "Schreibe in einem jugendlichen, aber nicht albernen Ton. "
            "Die Zielgruppe sind Teenager (14-18 Jahre), aber Eltern lesen mit. "
            "Verwende Du-Anrede. Sei begeisternd und motivierend, aber nicht unserioes. "
            "Verwende passende Emojis (3-5 pro Caption), z.B. Landesflaggen, "
            "Sterne, Herzen, Flugzeuge. Kein Slang wie 'digga' oder 'bruh'."
        ),
        "witzig": (
            "Schreibe in einem witzigen, humorvollen Ton. "
            "Nutze Wortspiele, uebertriebene Vergleiche und Self-Deprecating Humor. "
            "Referenziere Pop-Kultur die 16-18 Jaehrige kennen (Memes, TikTok-Trends, Serien). "
            "Verwende Du-Anrede. Humor soll sympathisch und einladend wirken, niemals verletzend. "
            "Verwende lustige Emojis (4-6 pro Caption) wie 😂🤣💀🙈🎉. "
            "Beispiel-Stil: 'Dein Koffer ist schwerer als deine Mathe-Note? Willkommen im Auslandsjahr-Modus! 😂'"
        ),
        "emotional": (
            "Schreibe in einem emotionalen, beruehrenden Ton. "
            "Erzaehle aus der Ich-Perspektive oder beschreibe Gefuehle konkret und bildhaft. "
            "Nutze sensorische Sprache: Was sieht, hoert, fuehlt man? "
            "Verwende Du-Anrede, schaffe Naehe und Intimaet. "
            "Verwende gefuehlvolle Emojis (3-5 pro Caption) wie 🥺💙✨🌅🫂. "
            "Ziel: Gaensehaut-Momente erzeugen, die zum Teilen und Speichern animieren. "
            "Beispiel-Stil: 'Der Moment, wenn du zum ersten Mal deine Gastfamilie umarmst und weisst: Hier gehoere ich hin. 🥺💙'"
        ),
        "motivierend": (
            "Schreibe in einem motivierenden, empowernden Ton. "
            "Nutze kraftvolle Verben, kurze Saetze, Aufrufe zum Handeln. "
            "Verwende Du-Anrede. Sprich direkt die Traeume und Ziele der Jugendlichen an. "
            "Ueberwindung von Aengsten und Zweifeln ist ein Kernthema. "
            "Verwende energiegeladene Emojis (4-6 pro Caption) wie 💪🔥🚀⭐🌍✨. "
            "Beispiel-Stil: 'Dein Auslandsjahr wartet nicht. MACH den ersten Schritt. HEUTE. 🚀💪'"
        ),
        "informativ": (
            "Schreibe in einem informativen, faktenbasierten Ton. "
            "Praesentiere Zahlen, Fakten und konkrete Details. "
            "Strukturiere Inhalte mit Listen, Vergleichen oder Schritt-fuer-Schritt-Anleitungen. "
            "Verwende eine neutrale, aber zugaengliche Anrede (Mix aus Du/allgemein). "
            "Verwende dezente Emojis (2-4 pro Caption) wie 📊📝✅ℹ️📌. "
            "Sei sachlich und praezise, aber nicht trocken - die Informationen sollen nuetzlich und teilbar sein. "
            "Beispiel-Stil: '📊 Highschool USA vs. Kanada: Kosten, Dauer, Voraussetzungen im Vergleich.'"
        ),
        "behind-the-scenes": (
            "Schreibe in einem authentischen Behind-the-Scenes Ton. "
            "Zeige den Blick hinter die Kulissen von TREFF Sprachreisen. "
            "Erzaehle ehrlich und transparent vom Alltag, von der Vorbereitung, vom Team. "
            "Verwende Du-Anrede, sei nahbar und ungefiltert (aber professionell). "
            "Verwende lockere Emojis (3-5 pro Caption) wie 👀📸🎬🤫💬. "
            "Ziel: Vertrauen durch Transparenz aufbauen, die Marke menschlich machen. "
            "Beispiel-Stil: '👀 Was passiert eigentlich bei TREFF, bevor ihr in den Flieger steigt? Wir zeigen es euch!'"
        ),
        "storytelling": (
            "Schreibe in einem erzaehlerischen Storytelling-Ton. "
            "Baue eine kleine Geschichte auf mit Anfang, Mitte und Ende. "
            "Nutze narrative Techniken: Spannungsaufbau, Details, Wendepunkte. "
            "Verwende Du-Anrede oder erzaehle in der dritten Person. "
            "Verwende stimmungsvolle Emojis (3-5 pro Caption) wie 📖✈️🌅🏫💫. "
            "Jeder Post soll sich wie eine Mini-Geschichte anfuehlen, die man bis zum Ende lesen will. "
            "Beispiel-Stil: 'Es war 6 Uhr morgens am Frankfurter Flughafen. Lena hielt ihr Boarding-Pass in der Hand und wusste: Ab jetzt wird alles anders. ✈️'"
        ),
        "provokant": (
            "Schreibe in einem provokanten, mutigen Ton der zum Nachdenken anregt. "
            "Stelle mutige Fragen, breche Erwartungen, nutze Hook-Saetze die zum Stoppen zwingen. "
            "Verwende Du-Anrede. Sei frech aber nicht beleidigend, mutig aber nicht respektlos. "
            "Hinterfrage gängige Annahmen ueber Auslandsaufenthalte und Schule. "
            "Verwende aufmerksamkeitsstarke Emojis (3-5 pro Caption) wie ⚡👊🎤🔥💥. "
            "Ziel: Scroll-Stopper erzeugen, Kommentare und Diskussionen provozieren. "
            "Beispiel-Stil: '⚡ Unpopular Opinion: Ein Auslandsjahr bringt dir mehr als jedes Abitur-Zeugnis. Change my mind. 👊'"
        ),
        "wholesome": (
            "Schreibe in einem herzlichen, wholesome Ton. "
            "Betone Gemeinschaft, Zusammenhalt, Dankbarkeit und positive Erlebnisse. "
            "Verwende Du-Anrede. Schaffe ein warmes, einladendes Gefuehl. "
            "Feiere kleine Erfolge und besondere Momente des Auslandsaufenthalts. "
            "Verwende warme Emojis (4-6 pro Caption) wie 🥰💛🏡🤗✨🌻. "
            "Ziel: Positive Vibes verbreiten, Community-Gefuehl staerken, zum Laecheln bringen. "
            "Beispiel-Stil: 'Wenn deine Gastmutter dir zum Geburtstag deinen Lieblingskuchen backt, obwohl du erst seit 3 Wochen da bist. 🥰🎂💛'"
        ),
    }

    tone_instruction = tone_instructions.get(tone, tone_instructions["jugendlich"])

    base_prompt = f"""Du bist der Social-Media-Content-Ersteller fuer TREFF Sprachreisen, einen deutschen Anbieter von Highschool-Aufenthalten im Ausland.

UNTERNEHMENSPROFIL:
- TREFF Sprachreisen, gegruendet 1984 in Eningen u.A. / Pfullingen, Deutschland
- Organisiert Highschool-Aufenthalte fuer deutsche Schueler in: USA, Kanada, Australien, Neuseeland, Irland
- Ca. 200 Teilnehmer pro Jahr
- Primaerfarbe: #3B7AB1 (Blau - Vertrauen, Bildung)
- Sekundaerfarbe: #FDD000 (Gelb - Energie, Abenteuer)

PROGRAMM-PREISE:
- USA Classic: ab 13.800 EUR
- USA Select: ab 22.000 EUR
- Kanada: ab 15.200 EUR
- Australien: ab 18.900 EUR
- Neuseeland: ab 19.500 EUR
- Irland: ab 14.500 EUR

LAENDERSPEZIFISCHE HIGHLIGHTS:
- USA: Typisches High School Leben, Cheerleader, Football, Homecoming, Prom, riesige Wahlfaecherangebote
- Kanada: Bilingual (Englisch/Franzoesisch), Rocky Mountains, exzellentes Schulsystem, multikulturell
- Australien: Surfen, einzigartige Tierwelt, relaxte Lebensart, innovative Schulen, Great Barrier Reef
- Neuseeland: Spektakulaere Natur, Maori-Kultur, kleine Klassen, Abenteuer-Aktivitaeten, sehr sicher
- Irland: Gruene Landschaften, kurzer Flug aus Deutschland, warmherzige Gastfamilien, europaeisch

TONALITAET:
{tone_instruction}

WICHTIGE REGELN:
- Schreibe IMMER auf Deutsch
- Erwaehne TREFF Sprachreisen oder TREFF in Captions
- Verwende relevante Landesflaggen-Emojis (z.B. die Flagge des jeweiligen Landes)
- Instagram-Hashtags: 8-12 relevante Hashtags, Mix aus deutsch und englisch, immer #TREFFSprachreisen
- TikTok-Hashtags: 3-5 kuerzere Hashtags + 1-2 Trending, immer #TREFFSprachreisen
- Captions sollen zum Engagement anregen (Fragen stellen, zum Kommentieren auffordern)
- Jede Slide-Headline soll kurz und praegnant sein (max 60 Zeichen)
- Body-Texte sollen informativ aber nicht zu lang sein (max 200 Zeichen pro Slide)
- Die letzte Slide sollte immer einen Call-to-Action enthalten
- Bullet Points (falls vorhanden) sollen konkrete Fakten oder Tipps enthalten

HOOK-FORMELN (fuer die erste Caption-Zeile - MUSS Aufmerksamkeit erregen):
- Wissensluecke: "Was ich gerne VOR meinem Auslandsjahr gewusst haette..."
- Vergleich: "USA vs. Kanada: Welches Land passt zu dir?"
- Mythos-Entlarvung: "MYTHOS: Ein Auslandsjahr ist nur was fuer Reiche. Die Wahrheit..."
- POV: "POV: Dein erster Tag an einer amerikanischen High School"
- Nummerierte Liste: "5 Gruende, warum DU ein Auslandsjahr machen solltest"
- Direkte Frage: "Wuerdest du 10 Monate bei einer fremden Familie leben?"
- Erwartung vs. Realitaet: "Erwartung: US High Schools sind wie in den Filmen..."
- Emotionaler Einstieg: "Der Moment, in dem ich realisiert habe: Jetzt bin ich alleine."
- Countdown/Dringlichkeit: "Nur noch 30 Tage bis Bewerbungsschluss!"
Waehle die passende Hook-Formel basierend auf Kategorie und Plattform!

ENGAGEMENT-STRATEGIE (fuer CTAs am Post-Ende):
- Frage-CTA: "In welches Land wuerdest du gehen? Kommentiere!"
- Speicher-CTA: "Speicher dir diesen Post fuer spaeter!"
- Teilen-CTA: "Tagge einen Freund, der das wissen muss!"
- UGC-CTA: "Zeig uns dein Auslandsjahr mit #MeinTREFFJahr!"
- DM-CTA: "Fragen? DM uns - wir antworten in 24h!"
- Link-CTA: "Alle Infos ueber den Link in unserer Bio!"
Waehle den CTA-Typ passend zur Kategorie und Plattform!

BRAND-HASHTAGS (immer mindestens einen davon verwenden):
#TREFFSprachreisen #HighschoolYear #MeinTREFFJahr"""

    # Append personality preset section if provided
    if personality_preset and isinstance(personality_preset, dict):
        personality_section = _build_personality_prompt_section(personality_preset)
        base_prompt += f"""

═══════════════════════════════════════════
PERSOENLICHKEITS-PRESET (WICHTIG - hat Vorrang vor allgemeiner Tonalitaet):
═══════════════════════════════════════════
{personality_section}

HINWEIS: Die Persoenlichkeits-Einstellungen oben ueberschreiben die allgemeine Tonalitaet.
Wenn das Preset z.B. humor_level=5 und perspective=first_person hat, dann schreibe
sehr humorvoll aus der Ich-Perspektive, unabhaengig vom allgemeinen Ton."""

    return base_prompt


def _build_gemini_content_prompt(
    category: str,
    country: Optional[str],
    topic: Optional[str],
    key_points: Optional[str],
    platform: str,
    slide_count: int,
) -> str:
    """Build the content generation prompt for Gemini."""
    country_name = COUNTRY_DATA.get(country, {}).get("name", country or "ein Land")
    category_name = CATEGORY_DISPLAY_NAMES.get(category, category)

    prompt = f"""Erstelle einen Social-Media-Post fuer die Kategorie "{category_name}".

DETAILS:
- Land: {country_name}
- Plattform: {platform}
- Anzahl Slides: {slide_count}"""

    if topic:
        prompt += f"\n- Thema: {topic}"
    if key_points:
        prompt += f"\n- Wichtige Punkte: {key_points}"

    prompt += f"""

ANFORDERUNGEN:
- Erstelle genau {slide_count} Slides
- Slide 0 ist das Cover (Hauptheadline + Subheadline + Intro-Text)
- Die letzte Slide (Slide {slide_count - 1}) soll einen starken CTA enthalten
- Mittlere Slides sollen Details, Fakten oder Tipps zum Thema enthalten
- Erstelle separate Instagram- und TikTok-Captions
- Erstelle separate Instagram- und TikTok-Hashtags
- Alle Texte auf Deutsch

Antworte ausschliesslich im folgenden JSON-Format (kein Markdown, keine Erklaerungen):
{{
  "slides": [
    {{
      "slide_index": 0,
      "headline": "Kurze praegnante Headline",
      "subheadline": "Ergaenzende Subheadline",
      "body_text": "Informative Beschreibung, max 200 Zeichen",
      "bullet_points": [],
      "cta_text": ""
    }}
  ],
  "caption_instagram": "Instagram Caption mit Emojis und CTA",
  "caption_tiktok": "Kurze TikTok Caption mit Hook",
  "hashtags_instagram": "#Hashtag1 #Hashtag2 ... (10-12 Hashtags)",
  "hashtags_tiktok": "#hashtag1 #hashtag2 ... (6-8 Hashtags inkl. #fyp)",
  "cta_text": "Call-to-Action Text",
  "headline": "Hauptheadline des Posts"
}}"""

    return prompt


def generate_text_with_gemini(
    api_key: str,
    category: str,
    country: Optional[str] = None,
    topic: Optional[str] = None,
    key_points: Optional[str] = None,
    tone: str = "jugendlich",
    platform: str = "instagram_feed",
    slide_count: int = 1,
    personality_preset: Optional[dict] = None,
) -> Optional[dict]:
    """
    Generate text content using Gemini 2.5 Flash.

    Returns structured dict matching the same format as generate_text_content(),
    or None if generation fails.

    If personality_preset is provided, it customizes the AI system prompt with
    the student's personality (tone, humor_level, emoji_usage, perspective, catchphrases).
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        system_prompt = _build_gemini_system_prompt(tone, personality_preset=personality_preset)
        content_prompt = _build_gemini_content_prompt(
            category=category,
            country=country,
            topic=topic,
            key_points=key_points,
            platform=platform,
            slide_count=slide_count,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.8,
                max_output_tokens=4096,
            ),
        )

        # Parse the JSON response
        response_text = response.text.strip()

        # Handle potential markdown code fences
        if response_text.startswith("```"):
            # Remove ```json or ``` prefix and trailing ```
            lines = response_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        result = json.loads(response_text)

        # Validate the response structure
        if not isinstance(result, dict):
            logger.warning("Gemini response is not a dict")
            return None

        required_keys = ["slides", "caption_instagram", "caption_tiktok", "hashtags_instagram", "hashtags_tiktok"]
        for key in required_keys:
            if key not in result:
                logger.warning("Gemini response missing key: %s", key)
                return None

        if not isinstance(result["slides"], list) or len(result["slides"]) == 0:
            logger.warning("Gemini response has invalid slides")
            return None

        # Ensure all slides have required fields
        for i, slide in enumerate(result["slides"]):
            slide.setdefault("slide_index", i)
            slide.setdefault("headline", "")
            slide.setdefault("subheadline", "")
            slide.setdefault("body_text", "")
            slide.setdefault("bullet_points", [])
            slide.setdefault("cta_text", "")

        # Ensure top-level fields
        result.setdefault("cta_text", result["slides"][-1].get("cta_text", ""))
        result.setdefault("headline", result["slides"][0].get("headline", ""))

        # Add source indicator
        result["source"] = "gemini"

        logger.info("Gemini text generation succeeded for category=%s, country=%s, tone=%s", category, country, tone)
        return result

    except json.JSONDecodeError as e:
        logger.warning("Failed to parse Gemini JSON response: %s", e)
        return None
    except ImportError:
        logger.warning("google-genai package not installed")
        return None
    except Exception as e:
        logger.warning("Gemini text generation failed: %s", e)
        return None


def generate_text_content(
    category: str,
    country: Optional[str] = None,
    topic: Optional[str] = None,
    key_points: Optional[str] = None,
    tone: str = "jugendlich",
    platform: str = "instagram_feed",
    slide_count: int = 1,
    api_key: Optional[str] = None,
    personality_preset: Optional[dict] = None,
) -> dict:
    """
    Generate structured text content for a social media post.

    If an api_key is provided, attempts Gemini 2.5 Flash generation first.
    Falls back to rule-based templates if no API key or if Gemini fails.

    If personality_preset is provided, it customizes the AI system prompt with
    the student's personality (tone, humor_level, emoji_usage, perspective, catchphrases).

    Returns dict with:
    - slides: list of slide content objects
    - caption_instagram: Instagram caption
    - caption_tiktok: TikTok caption
    - hashtags_instagram: Instagram hashtags
    - hashtags_tiktok: TikTok hashtags
    - cta_text: Call-to-action text
    - source: "gemini" or "rule_based"
    """
    # Try Gemini first if API key is available
    if api_key:
        logger.info("Attempting Gemini text generation (category=%s, country=%s, tone=%s, has_personality=%s)", category, country, tone, personality_preset is not None)
        gemini_result = generate_text_with_gemini(
            api_key=api_key,
            category=category,
            country=country,
            topic=topic,
            key_points=key_points,
            tone=tone,
            platform=platform,
            slide_count=slide_count,
            personality_preset=personality_preset,
        )
        if gemini_result:
            return gemini_result
        logger.info("Gemini failed, falling back to rule-based generation")

    # Rule-based fallback
    # Default to a random country if none specified
    if not country or country not in COUNTRY_DATA:
        country = random.choice(list(COUNTRY_DATA.keys()))

    c = COUNTRY_DATA[country]
    cat = CATEGORY_CONTENT.get(category, CATEGORY_CONTENT["laender_spotlight"])

    # Generate headline
    headline_template = random.choice(cat["headline_templates"])
    headline = headline_template.format(
        country=c["name"],
        adj=c["adjective"],
        name=random.choice(ALUMNI_NAMES),
        year=2027,
        days=random.randint(30, 180),
        country_a=c["name"],
        country_b=COUNTRY_DATA[random.choice([k for k in COUNTRY_DATA if k != country])]["name"],
    )

    # Generate subheadline
    subheadline_template = random.choice(cat["subheadline_templates"])
    subheadline = subheadline_template.format(
        country=c["name"],
        adj=c["adjective"],
    )

    # Use topic/key_points if provided, else generate from category
    if topic:
        body_intro = f"{topic}: "
    else:
        body_intro = ""

    body_texts = BODY_TEXTS.get(category, BODY_TEXTS["laender_spotlight"])
    body_template = random.choice(body_texts)
    body_text = body_intro + body_template.format(
        country=c["name"],
        adj=c["adjective"],
    )

    # Incorporate key points if provided
    if key_points:
        body_text = f"{body_text}\n\n{key_points}"

    # Generate CTA
    cta_template = random.choice(cat["cta_templates"])
    cta_text = cta_template.format(country=c["name"])

    # Generate slides
    slides = []
    for i in range(slide_count):
        slide = {
            "slide_index": i,
            "headline": headline if i == 0 else _generate_slide_headline(category, c, i, slide_count),
            "subheadline": subheadline if i == 0 else "",
            "body_text": body_text if i == 0 else _generate_slide_body(category, c, i, slide_count),
            "bullet_points": [],
            "cta_text": cta_text if i == slide_count - 1 else "",
        }

        # Add bullet points for certain slide types
        if i > 0 and i < slide_count - 1 and category in ("laender_spotlight", "tipps_tricks", "infografiken"):
            facts = c["highlights"] if category == "laender_spotlight" else c["facts"]
            slide["bullet_points"] = random.sample(facts, min(3, len(facts)))

        slides.append(slide)

    # Generate captions
    caption_instagram = _generate_instagram_caption(headline, body_text, c, category, tone)
    caption_tiktok = _generate_tiktok_caption(headline, c, category)

    # Generate hashtags
    base_hashtags = random.sample(HASHTAGS_INSTAGRAM, 8)
    country_hashtags = HASHTAGS_COUNTRY.get(country, [])[:4]
    hashtags_ig = " ".join(base_hashtags + country_hashtags)

    tiktok_tags = random.sample(HASHTAGS_TIKTOK, 6)
    country_tt = HASHTAGS_COUNTRY.get(country, [])[:2]
    hashtags_tt = " ".join(tiktok_tags + country_tt)

    return {
        "slides": slides,
        "caption_instagram": caption_instagram,
        "caption_tiktok": caption_tiktok,
        "hashtags_instagram": hashtags_ig,
        "hashtags_tiktok": hashtags_tt,
        "cta_text": cta_text,
        "headline": headline,
        "source": "rule_based",
    }


def _generate_slide_headline(category: str, country_data: dict, index: int, total: int) -> str:
    """Generate a headline for a specific slide in a carousel."""
    if index == total - 1:
        return f"Bereit fuer {country_data['name']}?"

    headlines_by_category = {
        "laender_spotlight": [
            f"Highlight #{index}: {random.choice(country_data['highlights'][:3])}",
            f"Fakt {index}: {random.choice(country_data['facts'][:3])}",
            f"Das erwartet dich in {country_data['name']}",
        ],
        "tipps_tricks": [
            f"Tipp #{index}",
            f"Wichtiger Hinweis #{index}",
            f"Das solltest du wissen",
        ],
        "erfahrungsberichte": [
            f"Kapitel {index}: Der Anfang",
            f"Kapitel {index}: Der Alltag",
            f"Kapitel {index}: Das Fazit",
        ],
        "faq": [
            f"Frage {index}",
            f"Haeufige Frage #{index}",
        ],
    }

    options = headlines_by_category.get(category, [f"Slide {index + 1}"])
    return random.choice(options)


def _generate_slide_body(category: str, country_data: dict, index: int, total: int) -> str:
    """Generate body text for a specific carousel slide."""
    if index == total - 1:
        return f"Starte dein Abenteuer in {country_data['name']} mit TREFF Sprachreisen! Wir begleiten dich von der Bewerbung bis zur Rueckkehr. {country_data['price']}."

    fact = random.choice(country_data["facts"])
    highlight = random.choice(country_data["highlights"])

    options = [
        f"{fact}. {highlight}.",
        f"{highlight}. Das macht {country_data['name']} so besonders fuer Austauschschueler.",
        f"In {random.choice(country_data['cities'])} und anderen Staedten erlebst du: {highlight}.",
    ]
    return random.choice(options)


def _generate_instagram_caption(headline: str, body: str, country_data: dict, category: str, tone: str) -> str:
    """Generate an Instagram caption based on tone."""
    flag = country_data["flag"]

    tone_captions = {
        "serioess": f"{flag} {headline}\n\n{body[:200]}\n\nSeit 1984 begleitet TREFF Sprachreisen junge Menschen auf ihrem Weg ins Ausland. Vertrauen Sie auf 40 Jahre Erfahrung.\n\n📩 Kostenlose Beratung: Link in Bio",
        "jugendlich": f"{flag} {headline}\n\n{body[:200]}\n\n✨ Dein Abenteuer beginnt bei TREFF Sprachreisen!\n💙 Seit 1984 schicken wir Schueler in die Welt\n📩 Link in Bio fuer mehr Infos!",
        "witzig": f"{flag} {headline}\n\n{body[:200]}\n\n😂 Plot Twist: Das wird die beste Entscheidung deines Lebens!\n🎉 TREFF Sprachreisen – seit 1984 Traeume wahr machen\n📩 Link in Bio!",
        "emotional": f"{flag} {headline}\n\n{body[:200]}\n\n🥺 Manche Momente veraendern dein ganzes Leben.\n💙 TREFF Sprachreisen begleitet dich auf deinem Weg.\n📩 Link in Bio fuer deine Geschichte",
        "motivierend": f"{flag} {headline}\n\n{body[:200]}\n\n💪 Trau dich! Dein Auslandsjahr wartet auf DICH!\n🔥 TREFF Sprachreisen – seit 1984 Mut belohnen\n📩 Starte jetzt: Link in Bio!",
        "informativ": f"{flag} {headline}\n\n{body[:200]}\n\n📊 Alle Fakten & Details findest du bei TREFF Sprachreisen.\n✅ Seit 1984 – ueber 8.000 Schueler betreut\n📩 Mehr Infos: Link in Bio",
        "behind-the-scenes": f"{flag} {headline}\n\n{body[:200]}\n\n👀 So sieht's hinter den Kulissen bei TREFF aus!\n📸 Echte Einblicke, echte Menschen, seit 1984\n📩 Link in Bio fuer mehr!",
        "storytelling": f"{flag} {headline}\n\n{body[:200]}\n\n📖 Jede Reise beginnt mit einem ersten Schritt.\n✈️ TREFF Sprachreisen schreibt seit 1984 Geschichten.\n📩 Deine Geschichte beginnt hier: Link in Bio",
        "provokant": f"{flag} {headline}\n\n{body[:200]}\n\n⚡ Bist du bereit, alles zu veraendern?\n🔥 TREFF Sprachreisen – seit 1984 Grenzen sprengen\n📩 Trau dich: Link in Bio!",
        "wholesome": f"{flag} {headline}\n\n{body[:200]}\n\n🥰 Die schoensten Erinnerungen entstehen fernab von zuhause.\n💛 TREFF Sprachreisen – seit 1984 Familien verbinden\n📩 Link in Bio fuer mehr Liebe!",
    }

    caption = tone_captions.get(tone, tone_captions["jugendlich"])
    return caption


def _generate_tiktok_caption(headline: str, country_data: dict, category: str) -> str:
    """Generate a TikTok caption (shorter, hook-focused)."""
    hooks = [
        f"{country_data['flag']} {headline} 🔥",
        f"POV: Du machst ein Auslandsjahr in {country_data['name']} {country_data['flag']}",
        f"Dinge, die du nur in {country_data['name']} erlebst {country_data['flag']}✨",
        f"Auslandsjahr Check: {country_data['name']} Edition {country_data['flag']}",
    ]
    return random.choice(hooks)


def _regenerate_field_with_gemini(
    api_key: str,
    field: str,
    category: str,
    country: Optional[str] = None,
    topic: Optional[str] = None,
    tone: str = "jugendlich",
    slide_index: int = 0,
    current_headline: Optional[str] = None,
    current_body: Optional[str] = None,
) -> Optional[dict]:
    """Regenerate a single field using Gemini 2.5 Flash."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        country_name = COUNTRY_DATA.get(country, {}).get("name", country or "ein Land")
        category_name = CATEGORY_DISPLAY_NAMES.get(category, category)

        system_prompt = _build_gemini_system_prompt(tone)

        field_descriptions = {
            "headline": f"eine neue Slide-Headline (max 60 Zeichen) fuer Slide {slide_index}",
            "subheadline": "eine neue Subheadline (max 80 Zeichen)",
            "body_text": f"einen neuen Body-Text (max 200 Zeichen) fuer Slide {slide_index}",
            "cta_text": "einen neuen Call-to-Action Text (max 40 Zeichen)",
            "caption_instagram": "eine neue Instagram-Caption mit Emojis (150-300 Zeichen)",
            "caption_tiktok": "eine neue TikTok-Caption mit Hook (max 150 Zeichen)",
            "hashtags_instagram": "10-12 neue Instagram-Hashtags (Mix aus deutsch/englisch)",
            "hashtags_tiktok": "6-8 neue TikTok-Hashtags (inkl. #fyp #foryou)",
        }

        field_desc = field_descriptions.get(field, f"ein neues '{field}' Feld")

        context_parts = []
        if current_headline:
            context_parts.append(f"Aktuelle Headline: {current_headline}")
        if current_body:
            context_parts.append(f"Aktueller Body: {current_body[:200]}")
        if topic:
            context_parts.append(f"Thema: {topic}")

        context_str = "\n".join(context_parts) if context_parts else "Kein zusaetzlicher Kontext"

        content_prompt = f"""Generiere {field_desc} fuer einen TREFF Sprachreisen Post.

Kategorie: {category_name}
Land: {country_name}
{context_str}

Antworte NUR mit dem generierten Text, ohne Anfuehrungszeichen, ohne Erklaerungen, ohne JSON.
Nur der reine Text."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.9,
                max_output_tokens=512,
            ),
        )

        value = response.text.strip()
        # Remove quotes if Gemini wrapped the response
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        if not value:
            return None

        logger.info("Gemini field regeneration succeeded for field=%s", field)
        return {"field": field, "value": value, "source": "gemini"}

    except Exception as e:
        logger.warning("Gemini field regeneration failed: %s", e)
        return None


def regenerate_single_field(
    field: str,
    category: str,
    country: Optional[str] = None,
    topic: Optional[str] = None,
    key_points: Optional[str] = None,
    tone: str = "jugendlich",
    platform: str = "instagram_feed",
    slide_index: int = 0,
    slide_count: int = 1,
    current_headline: Optional[str] = None,
    current_body: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    """
    Regenerate a single text field without changing others.

    If api_key is provided, tries Gemini 2.5 Flash first, then falls back to rule-based.

    Supported fields:
    - headline: Regenerate just the headline for the given slide
    - subheadline: Regenerate just the subheadline for the given slide
    - body_text: Regenerate just the body text for the given slide
    - cta_text: Regenerate just the CTA text
    - caption_instagram: Regenerate just the Instagram caption
    - caption_tiktok: Regenerate just the TikTok caption
    - hashtags_instagram: Regenerate just the Instagram hashtags
    - hashtags_tiktok: Regenerate just the TikTok hashtags

    Returns dict with:
    - field: name of the regenerated field
    - value: new value for that field
    - source: "gemini" or "rule_based"
    """
    # Try Gemini first if API key is available
    if api_key:
        gemini_result = _regenerate_field_with_gemini(
            api_key=api_key,
            field=field,
            category=category,
            country=country,
            topic=topic,
            tone=tone,
            slide_index=slide_index,
            current_headline=current_headline,
            current_body=current_body,
        )
        if gemini_result:
            return gemini_result

    # Rule-based fallback
    if not country or country not in COUNTRY_DATA:
        country = random.choice(list(COUNTRY_DATA.keys()))

    c = COUNTRY_DATA[country]
    cat = CATEGORY_CONTENT.get(category, CATEGORY_CONTENT["laender_spotlight"])

    if field == "headline":
        if slide_index == 0:
            headline_template = random.choice(cat["headline_templates"])
            value = headline_template.format(
                country=c["name"],
                adj=c["adjective"],
                name=random.choice(ALUMNI_NAMES),
                year=2027,
                days=random.randint(30, 180),
                country_a=c["name"],
                country_b=COUNTRY_DATA[random.choice([k for k in COUNTRY_DATA if k != country])]["name"],
            )
        else:
            value = _generate_slide_headline(category, c, slide_index, slide_count)

    elif field == "subheadline":
        subheadline_template = random.choice(cat["subheadline_templates"])
        value = subheadline_template.format(
            country=c["name"],
            adj=c["adjective"],
        )

    elif field == "body_text":
        if slide_index == 0:
            body_intro = f"{topic}: " if topic else ""
            body_texts = BODY_TEXTS.get(category, BODY_TEXTS["laender_spotlight"])
            body_template = random.choice(body_texts)
            value = body_intro + body_template.format(
                country=c["name"],
                adj=c["adjective"],
            )
            if key_points:
                value = f"{value}\n\n{key_points}"
        else:
            value = _generate_slide_body(category, c, slide_index, slide_count)

    elif field == "cta_text":
        cta_template = random.choice(cat["cta_templates"])
        value = cta_template.format(country=c["name"])

    elif field == "caption_instagram":
        # Use the provided current headline/body or generate new ones for context
        headline = current_headline or "Dein Highschool-Jahr"
        body = current_body or ""
        value = _generate_instagram_caption(headline, body, c, category, tone)

    elif field == "caption_tiktok":
        headline = current_headline or "Dein Highschool-Jahr"
        value = _generate_tiktok_caption(headline, c, category)

    elif field == "hashtags_instagram":
        base_hashtags = random.sample(HASHTAGS_INSTAGRAM, 8)
        country_hashtags = HASHTAGS_COUNTRY.get(country, [])[:4]
        value = " ".join(base_hashtags + country_hashtags)

    elif field == "hashtags_tiktok":
        tiktok_tags = random.sample(HASHTAGS_TIKTOK, 6)
        country_tt = HASHTAGS_COUNTRY.get(country, [])[:2]
        value = " ".join(tiktok_tags + country_tt)

    else:
        raise ValueError(f"Unknown field: {field}. Supported: headline, subheadline, body_text, cta_text, caption_instagram, caption_tiktok, hashtags_instagram, hashtags_tiktok")

    return {"field": field, "value": value, "source": "rule_based"}
