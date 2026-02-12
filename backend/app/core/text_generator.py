"""
TREFF Sprachreisen - Text Content Generator

Generates structured German text content for social media posts based on
category, country, topic, and tone. This is a rule-based content engine
that produces real, brand-appropriate German text.

When a Gemini API key is configured, this module will be replaced by AI generation.
For now, it generates category-specific content using curated content templates.
"""

import random
from typing import Optional

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


def generate_text_content(
    category: str,
    country: Optional[str] = None,
    topic: Optional[str] = None,
    key_points: Optional[str] = None,
    tone: str = "jugendlich",
    platform: str = "instagram_feed",
    slide_count: int = 1,
) -> dict:
    """
    Generate structured text content for a social media post.

    Returns dict with:
    - slides: list of slide content objects
    - caption_instagram: Instagram caption
    - caption_tiktok: TikTok caption
    - hashtags_instagram: Instagram hashtags
    - hashtags_tiktok: TikTok hashtags
    - cta_text: Call-to-action text
    """
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
    """Generate an Instagram caption."""
    flag = country_data["flag"]

    if tone == "serioess":
        caption = f"{flag} {headline}\n\n{body[:200]}\n\nSeit 1984 begleitet TREFF Sprachreisen junge Menschen auf ihrem Weg ins Ausland. Vertrauen Sie auf 40 Jahre Erfahrung.\n\n📩 Kostenlose Beratung: Link in Bio"
    else:
        caption = f"{flag} {headline}\n\n{body[:200]}\n\n✨ Dein Abenteuer beginnt bei TREFF Sprachreisen!\n💙 Seit 1984 schicken wir Schueler in die Welt\n📩 Link in Bio fuer mehr Infos!"

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
) -> dict:
    """
    Regenerate a single text field without changing others.

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
    """
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

    return {"field": field, "value": value}
