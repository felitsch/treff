"""Seed default humor/meme formats for the Humor-Templates feature."""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.humor_format import HumorFormat

logger = logging.getLogger(__name__)

# The 10 humor formats as specified in the feature requirements
HUMOR_FORMATS = [
    {
        "name": "Expectation vs Reality",
        "description": "Zeigt den Unterschied zwischen Erwartungen ans Auslandsjahr und der Realitaet. Zwei-Panel-Format, das humorvoll Klischees mit der tatsaechlichen Erfahrung kontrastiert.",
        "template_structure": json.dumps({
            "layout": "two_panel",
            "panels": [
                {"label": "Expectation", "position": "left_or_top"},
                {"label": "Reality", "position": "right_or_bottom"}
            ],
            "fields": ["expectation_text", "reality_text", "topic"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Gastfamilie in den USA",
            "expectation_text": "Riesiges Haus mit Pool, perfekte Familie wie im Film 🏠✨",
            "reality_text": "Liebevolle Familie, die dich zum 5. Mal fragt ob du Erdnussbutter magst 🥜😅",
            "caption": "Expectation vs Reality: Gastfamilie Edition 😂🇺🇸 Aber ehrlich - die Realitaet ist SO viel besser als jeder Film! #TREFFSprachreisen #Auslandsjahr #ExpectationVsReality",
            "hashtags": ["#TREFFSprachreisen", "#ExpectationVsReality", "#Auslandsjahr", "#Gastfamilie", "#USA"]
        }),
        "platform_fit": "both",
        "icon": "🤣"
    },
    {
        "name": "POV: Dein erster Tag...",
        "description": "Point-of-View Format, das den Zuschauer in eine bestimmte Situation versetzt. Ideal fuer Reels/TikTok als Video-Storyboard oder fuer statische Posts mit immersivem Text.",
        "template_structure": json.dumps({
            "layout": "pov_storyboard",
            "panels": [
                {"label": "POV Setup", "position": "header"},
                {"label": "Scene Description", "position": "body"},
                {"label": "Punchline", "position": "footer"}
            ],
            "fields": ["pov_title", "scene_text", "punchline"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Erster Schultag in Australien",
            "pov_title": "POV: Dein erster Tag an einer australischen High School",
            "scene_text": "Alle tragen Schuluniformen. Du traegst deine coolste Streetwear. Alle starren. 👀",
            "punchline": "Plot Twist: Am naechsten Tag liebst du die Uniform weil du morgens 30 Min laenger schlafen kannst 😴💪",
            "caption": "POV: Dein erster Tag an der High School in Australien 🇦🇺 Wer kennt's? 😂 #TREFFSprachreisen #POV #Australien #HighSchool",
            "hashtags": ["#TREFFSprachreisen", "#POV", "#Australien", "#HighSchool", "#SchoolUniform"]
        }),
        "platform_fit": "both",
        "icon": "👁️"
    },
    {
        "name": "Dinge die dir niemand sagt ueber...",
        "description": "Listicle-Format mit insider Wissen und ueberraschenden Fakten ueber das Auslandsjahr. Mehrere Slides als Carousel oder einzelner Post.",
        "template_structure": json.dumps({
            "layout": "listicle",
            "panels": [
                {"label": "Title Slide", "position": "cover"},
                {"label": "Thing 1-5", "position": "body_slides"}
            ],
            "fields": ["title", "things_list", "conclusion"],
            "slide_count": 3
        }),
        "example_text": json.dumps({
            "topic": "Kanada",
            "title": "5 Dinge die dir NIEMAND sagt ueber ein Auslandsjahr in Kanada 🇨🇦",
            "things_list": [
                "Du wirst 'sorry' so oft sagen dass es dein neues Lieblingswort wird 🍁",
                "Poutine (Pommes mit Kaese und Sosse) wird dein Comfort Food 🍟",
                "Minus 30 Grad fuehlen sich irgendwann 'normal' an ❄️",
                "Dein Englisch wird einen kanadischen Akzent bekommen, eh? 🗣️",
                "Du wirst Hockey verstehen und lieben lernen 🏒"
            ],
            "conclusion": "Das Beste? All das macht dein Auslandsjahr unvergesslich! 🫶",
            "caption": "Dinge die dir niemand sagt ueber Kanada... 🇨🇦🤫 Was wuerdest DU noch hinzufuegen? #TREFFSprachreisen #Kanada #Auslandsjahr",
            "hashtags": ["#TREFFSprachreisen", "#Kanada", "#Auslandsjahr", "#DieDirNiemandSagt", "#HighSchool"]
        }),
        "platform_fit": "both",
        "icon": "🤫"
    },
    {
        "name": "Starter Pack",
        "description": "Das klassische Starter-Pack Meme-Format. Zeigt typische Gegenstaende/Erfahrungen die zu einem bestimmten Auslandsjahr-Thema gehoeren.",
        "template_structure": json.dumps({
            "layout": "grid_4",
            "panels": [
                {"label": "Title", "position": "header"},
                {"label": "Item 1", "position": "top_left"},
                {"label": "Item 2", "position": "top_right"},
                {"label": "Item 3", "position": "bottom_left"},
                {"label": "Item 4", "position": "bottom_right"}
            ],
            "fields": ["title", "items"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "USA Exchange Student",
            "title": "Das 'Austauschschueler in den USA' Starter Pack 🇺🇸",
            "items": [
                "XXL-Portionen in der Cafeteria 🍔",
                "Yellow School Bus jeden Morgen 🚌",
                "'Where is Germany? Is that near France?' 🗺️",
                "Pep Rally und Football Freitagabend 🏈"
            ],
            "caption": "Das Starter Pack das jeder TREFF-Schueler kennt 😂🇺🇸 Markiere jemanden der das kennt! #TREFFSprachreisen #StarterPack #USA #Auslandsjahr",
            "hashtags": ["#TREFFSprachreisen", "#StarterPack", "#USA", "#ExchangeStudent", "#Auslandsjahr"]
        }),
        "platform_fit": "instagram",
        "icon": "📦"
    },
    {
        "name": "Ich wenn...",
        "description": "Relatable Reaktions-Format mit 'Ich wenn...' Szenario. Zeigt eine lustige Situation die alle Austauschschueler kennen.",
        "template_structure": json.dumps({
            "layout": "reaction",
            "panels": [
                {"label": "Situation", "position": "header"},
                {"label": "Reaction", "position": "body"}
            ],
            "fields": ["situation", "reaction_text"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Heimweh vs Abenteuer",
            "situation": "Ich wenn meine Eltern fragen ob ich Heimweh habe...",
            "reaction_text": "...waehrend ich gerade auf einem Roadtrip zum Grand Canyon bin 🏜️✌️",
            "caption": "Ich wenn... 😂 Sorry Mama, mir geht's SEHR gut hier 🇺🇸🫶 #TREFFSprachreisen #Auslandsjahr #IchWenn #Meme",
            "hashtags": ["#TREFFSprachreisen", "#IchWenn", "#Auslandsjahr", "#Heimweh", "#Abenteuer"]
        }),
        "platform_fit": "both",
        "icon": "😅"
    },
    {
        "name": "TREFF Mythbusters",
        "description": "Raeumt mit Vorurteilen und Mythen ueber das Auslandsjahr auf. Format: Mythos -> Fakt, ideal um Eltern und Schueler zu informieren.",
        "template_structure": json.dumps({
            "layout": "myth_fact",
            "panels": [
                {"label": "Myth", "position": "top"},
                {"label": "Fact", "position": "bottom"},
                {"label": "TREFF Verdict", "position": "footer"}
            ],
            "fields": ["myth", "fact", "verdict"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Kosten Auslandsjahr",
            "myth": "MYTHOS: Ein Auslandsjahr ist nur was fuer Reiche 💰❌",
            "fact": "FAKT: Mit Stipendien, Ratenzahlung und verschiedenen Programm-Optionen ist ein Auslandsjahr fuer viele Familien moeglich! ✅",
            "verdict": "TREFF beratet euch zu allen Finanzierungsmoeglichkeiten - seit 1984! 🫶",
            "caption": "TREFF Mythbusters 🔍 Dieser Mythos haelt sich hartnackig - aber wir raeumen damit auf! 💪 Schreib uns fuer eine kostenlose Beratung. #TREFFSprachreisen #Mythbusters #Auslandsjahr #Stipendium",
            "hashtags": ["#TREFFSprachreisen", "#Mythbusters", "#Auslandsjahr", "#Stipendium", "#Finanzierung"]
        }),
        "platform_fit": "both",
        "icon": "🔍"
    },
    {
        "name": "Gastfamilien-Bingo",
        "description": "Bingo-Karten-Format mit typischen Erlebnissen in der Gastfamilie. Interaktiv und teilbar, regt zum Markieren und Kommentieren an.",
        "template_structure": json.dumps({
            "layout": "bingo_grid",
            "panels": [
                {"label": "Title", "position": "header"},
                {"label": "Bingo Items (9 or 16)", "position": "grid"}
            ],
            "fields": ["title", "bingo_items"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Gastfamilie allgemein",
            "title": "Gastfamilien-BINGO! Wie viele hast du? 🎯",
            "bingo_items": [
                "Host Mom fragt 'Are you hungry?' 🍽️",
                "Erklaere zum 10. Mal wie man deinen Namen ausspricht 🗣️",
                "Erstes Thanksgiving/Weihnachten im Ausland 🦃",
                "Host Dad zeigt dir 'echtes' BBQ 🥩",
                "FREE SPACE: Du vermisst deutsches Brot 🍞",
                "Video-Call mit Eltern bei dem du Slang benutzt 📱",
                "Host-Geschwister zeigen dir TikTok-Trends 📲",
                "'In Germany we do it differently...' 🇩🇪",
                "Du kochst fuer die Gastfamilie (Schnitzel!) 🍳"
            ],
            "caption": "Gastfamilien-BINGO! 🎯 Screenshot machen und ankreuzen was du schon erlebt hast! 📸 Markiere deinen Exchange-Buddy! #TREFFSprachreisen #Bingo #Gastfamilie #Auslandsjahr",
            "hashtags": ["#TREFFSprachreisen", "#Bingo", "#Gastfamilie", "#ExchangeStudent", "#Auslandsjahr"]
        }),
        "platform_fit": "instagram",
        "icon": "🎯"
    },
    {
        "name": "Culture Shock Ranking",
        "description": "Ranking-Format das Culture-Shock Erfahrungen von mild bis wild sortiert. Interaktiv: Zuschauer koennen ihre eigene Reihenfolge kommentieren.",
        "template_structure": json.dumps({
            "layout": "ranking_list",
            "panels": [
                {"label": "Title", "position": "header"},
                {"label": "Rankings (mild to wild)", "position": "body"}
            ],
            "fields": ["title", "rankings", "cta"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Culture Shock USA",
            "title": "Culture Shock Ranking: USA Edition 🇺🇸📊",
            "rankings": [
                {"level": "mild", "text": "Alles ist RIESIG (Portionen, Autos, Haeuser) 🏠"},
                {"level": "medium", "text": "Small Talk mit JEDEM, sogar im Aufzug 🗣️"},
                {"level": "spicy", "text": "Schuhe im Haus anlassen?! 👟"},
                {"level": "wild", "text": "Sweet Tea = Zucker mit etwas Tee-Geschmack 🍵😱"},
                {"level": "extreme", "text": "Cheese in der Spruehdose... 🧀💀"}
            ],
            "cta": "Was war DEIN groesster Culture Shock? Schreib's in die Kommentare! ⬇️",
            "caption": "Culture Shock Ranking USA 🇺🇸 Von mild bis WILD 😱 Stimmst du zu? 📊 #TREFFSprachreisen #CultureShock #USA #Ranking",
            "hashtags": ["#TREFFSprachreisen", "#CultureShock", "#USA", "#Ranking", "#Auslandsjahr"]
        }),
        "platform_fit": "both",
        "icon": "📊"
    },
    {
        "name": "Rate das Land",
        "description": "Quiz-Format: Beschreibung oder Fun Facts werden gezeigt und der Zuschauer muss erraten welches Land gemeint ist. Interaktiv und engagement-foerdernd.",
        "template_structure": json.dumps({
            "layout": "quiz",
            "panels": [
                {"label": "Question/Clue", "position": "body"},
                {"label": "Answer Reveal", "position": "next_slide"}
            ],
            "fields": ["clues", "answer_country", "fun_fact"],
            "slide_count": 2
        }),
        "example_text": json.dumps({
            "topic": "Neuseeland",
            "clues": [
                "Hier gibt es mehr Schafe als Menschen 🐑",
                "Die Ureinwohner heissen Maori 🏔️",
                "Ein beruehmter Regisseur hat hier Mittelerde erschaffen 🧙‍♂️",
                "Die Nationalsport-Mannschaft macht vor jedem Spiel einen Haka-Tanz 💪"
            ],
            "answer_country": "Neuseeland 🇳🇿",
            "fun_fact": "TREFF bietet Highschool-Aufenthalte in Neuseeland ab 17.900 EUR! Die Schulsemester starten im Januar und Juli.",
            "caption": "RATE DAS LAND! 🤔🌍 Kannst du erraten welches Land gemeint ist? Antwort auf Slide 2! ➡️ #TREFFSprachreisen #RateDasLand #Quiz #Auslandsjahr",
            "hashtags": ["#TREFFSprachreisen", "#RateDasLand", "#Quiz", "#Neuseeland", "#Auslandsjahr"]
        }),
        "platform_fit": "instagram",
        "icon": "🌍"
    },
    {
        "name": "Was Eltern denken vs. Was wirklich passiert",
        "description": "Zwei-Perspektiven-Format das die Sorgen der Eltern mit der tatsaechlichen (positiven) Realitaet kontrastiert. Ideal um Eltern zu beruhigen und gleichzeitig Schueler anzusprechen.",
        "template_structure": json.dumps({
            "layout": "two_panel",
            "panels": [
                {"label": "Was Eltern denken", "position": "left_or_top"},
                {"label": "Was wirklich passiert", "position": "right_or_bottom"}
            ],
            "fields": ["parent_fear", "reality", "reassurance"],
            "slide_count": 1
        }),
        "example_text": json.dumps({
            "topic": "Sicherheit im Ausland",
            "parent_fear": "Was Eltern denken: 'Mein Kind ist ganz allein am anderen Ende der Welt!' 😰",
            "reality": "Was wirklich passiert: Gastfamilie adoptiert dich praktisch, Coordinator checkt woechentlich, TREFF-Notfallnummer 24/7 📞🏠",
            "reassurance": "Seit 1984 betreut TREFF Schueler im Ausland - mit persoenlicher Begleitung von Anfang bis Ende. 🫶",
            "caption": "Was Eltern denken vs. Was wirklich passiert 😂🫶 Liebe Eltern: Wir verstehen eure Sorgen - deshalb ist Betreuung unser #1 Versprechen! #TREFFSprachreisen #Eltern #Auslandsjahr #Sicherheit",
            "hashtags": ["#TREFFSprachreisen", "#ElternVsRealitaet", "#Auslandsjahr", "#Sicherheit", "#Betreuung"]
        }),
        "platform_fit": "both",
        "icon": "👨‍👩‍👧"
    }
]


async def seed_humor_formats(session: AsyncSession) -> int:
    """Seed default humor formats if not already present.

    Returns the number of formats seeded.
    """
    # Check if humor formats already exist
    result = await session.execute(select(func.count(HumorFormat.id)))
    existing_count = result.scalar() or 0

    if existing_count > 0:
        logger.info(f"Humor formats already seeded ({existing_count} found), skipping.")
        return 0

    count = 0
    for fmt_data in HUMOR_FORMATS:
        humor_format = HumorFormat(
            name=fmt_data["name"],
            description=fmt_data["description"],
            template_structure=fmt_data["template_structure"],
            example_text=fmt_data["example_text"],
            platform_fit=fmt_data["platform_fit"],
            icon=fmt_data.get("icon", "😄"),
        )
        session.add(humor_format)
        count += 1

    await session.commit()
    logger.info(f"Seeded {count} humor formats")
    return count
