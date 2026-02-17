/**
 * Student-Content-Guide fuer TREFF Sprachreisen
 *
 * Definiert die Struktur und Regeln fuer Student-Generated-Content (SGC):
 * - 10 Content-Typen (Arrival Story, First Day at School, etc.)
 * - Frequenz-Erwartungen (1-2 Stuecke/Woche/Schueler)
 * - AI-Processing-Rules (auto-suggest Post-Typ aus hochgeladenem Media)
 * - Mapping zu Templates, Plattformen und Content Pillars
 * - Prompt-Templates fuer KI-Text-Generierung pro Content-Typ
 *
 * Integration:
 * - StudentsView.vue / StudentsHubView.vue (Student management)
 * - StoryArcsView.vue (Story arc planning)
 * - contentPipeline.js (Media analysis / processing)
 * - contentPillars.js (Pillar IDs)
 *
 * @module studentContentGuide
 * @see frontend/src/views/StudentsView.vue - Student management
 * @see frontend/src/views/StoryArcsView.vue - Story arc planning
 * @see frontend/src/stores/contentPipeline.js - Content pipeline
 * @see frontend/src/config/contentPillars.js - Content pillar definitions
 * @see frontend/src/config/seasonalCalendar.js - Seasonal calendar integration
 *
 * @typedef {Object} StudentContentType
 * @property {string} id - Unique identifier
 * @property {string} name - Display name (German)
 * @property {string} description - What this content type is about
 * @property {string} ideal_timing - When in the exchange period this content is most relevant
 * @property {string} timing_weeks - Approximate week range (e.g. "1-2" for weeks 1-2)
 * @property {string} suggested_format - Best format: Reel|Story|Carousel|Feed|Story-Serie
 * @property {string} suggested_template_category - Template category to use
 * @property {string} pillar_mapping - Content pillar ID from contentPillars.js
 * @property {PlatformMapping} platform_mapping - Which platforms suit this content type
 * @property {string[]} example_captions - Example caption texts
 * @property {string[]} media_indicators - Keywords/patterns in media that suggest this type
 * @property {AIPromptTemplate} prompt_template - KI prompt template for text generation
 * @property {string} emotional_tone - Emotional tone: excited|reflective|informative|nostalgic|humorous
 * @property {number} priority - Content priority (1=highest, 5=lowest) for the social media team
 *
 * @typedef {Object} PlatformMapping
 * @property {boolean} instagram_feed - Suitable for Instagram Feed
 * @property {boolean} instagram_story - Suitable for Instagram Story
 * @property {boolean} instagram_reel - Suitable for Instagram Reel
 * @property {boolean} tiktok - Suitable for TikTok
 * @property {string} best_platform - The single best platform for this type
 *
 * @typedef {Object} AIPromptTemplate
 * @property {string} system_context - System context for the AI
 * @property {string} user_prompt_template - User prompt template with {placeholders}
 * @property {string[]} tone_keywords - Keywords to guide the AI tone
 * @property {number} max_length - Maximum caption length in characters
 *
 * @typedef {Object} FrequencyConfig
 * @property {number} min_per_week - Minimum content pieces per week per student
 * @property {number} max_per_week - Maximum content pieces per week per student
 * @property {number} ideal_per_week - Ideal content pieces per week per student
 * @property {string} note - Additional note about frequency
 *
 * @typedef {Object} AIProcessingRule
 * @property {string} trigger - What triggers this rule
 * @property {string[]} media_patterns - Patterns in uploaded media metadata/content
 * @property {string} suggested_content_type - Content type ID to suggest
 * @property {number} confidence_threshold - Minimum confidence (0-1) to auto-suggest
 */

// ============================================================
// FREQUENCY EXPECTATIONS
// ============================================================

export const FREQUENCY_CONFIG = {
  min_per_week: 1,
  max_per_week: 2,
  ideal_per_week: 2,
  note: 'Ideal: 1 Reel/Feed-Post + 1 Story pro Woche pro Schueler. Qualitaet vor Quantitaet — lieber ein starkes Stueck als zwei mittlere.',
  monthly_minimum: 4,
  monthly_ideal: 8,
  total_during_stay: {
    half_year: '25-50 Content-Stuecke (ca. 5 Monate)',
    full_year: '50-100 Content-Stuecke (ca. 10 Monate)',
  },
  reminder_intervals: {
    first_reminder_days: 5,
    second_reminder_days: 10,
    escalation_days: 14,
  },
}

// ============================================================
// STUDENT CONTENT TYPES (10 Types)
// ============================================================

export const STUDENT_CONTENT_TYPES = [
  // ─── 1. ARRIVAL STORY ─────────────────────────────
  {
    id: 'arrival_story',
    name: 'Ankunfts-Story',
    description: 'Der erste Moment im neuen Land: Ankunft am Flughafen, erstes Treffen mit der Gastfamilie, erste Eindruecke. Hochemotionaler Content mit starker Identifikation.',
    ideal_timing: 'Tag 1-3 nach Ankunft',
    timing_weeks: '1',
    suggested_format: 'Reel',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_reel',
    },
    example_captions: [
      'Der Moment, in dem ich zum ersten Mal amerikanischen Boden betreten habe... unbeschreiblich! \u{2708}\u{FE0F}\u{1F1FA}\u{1F1F8} Danke @treff_sprachreisen fuer dieses Abenteuer! #auslandsjahr #highschoolyear #treffsprachreisen',
      'Meine Gastfamilie hat mich am Flughafen mit einem Willkommens-Schild abgeholt \u{1F62D}\u{2764}\u{FE0F} Ich konnte die Traenen nicht zurueckhalten! #gastfamilie #ankunft #neuesabenteuer',
      'Nach 12 Stunden Flug endlich in Neuseeland! Der erste Blick aus dem Flugzeug... diese Berge! \u{1F3D4}\u{FE0F}\u{1F1F3}\u{1F1FF} #neuseeland #exchangestudent #treff',
    ],
    media_indicators: ['airport', 'airplane', 'luggage', 'welcome sign', 'arrival', 'flughafen', 'koffer', 'willkommen'],
    emotional_tone: 'excited',
    priority: 1,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine emotionale, authentische Instagram-Caption fuer die Ankunft eines Austauschschuelers im Gastland. Ton: aufgeregt, dankbar, ein bisschen nervoess. Zielgruppe: 14-18-jaehrige deutsche Schueler und deren Eltern.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name}, der/die gerade in {country} angekommen ist. Die Gastfamilie heisst {host_family}. Besondere erste Eindruecke: {first_impressions}. Verwende 2-4 passende Emojis und 3-5 Hashtags.',
      tone_keywords: ['aufgeregt', 'dankbar', 'ueberwaeeltigt', 'neues Abenteuer', 'erster Eindruck'],
      max_length: 500,
    },
  },

  // ─── 2. FIRST DAY AT SCHOOL ───────────────────────
  {
    id: 'first_day_school',
    name: 'Erster Schultag',
    description: 'Der erste Tag an der neuen Highschool: Schulgebaeude, Klassenzimmer, neue Mitschueler, Stundenplan, Schuluniform (falls vorhanden). Sehr relatable fuer die Zielgruppe.',
    ideal_timing: 'Woche 1-2 nach Schulbeginn',
    timing_weeks: '2-3',
    suggested_format: 'Carousel',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_feed',
    },
    example_captions: [
      'Mein erster Tag an der Westlake High! \u{1F3EB} Hier hat man tatsaechlich einen EIGENEN Spind wie im Film! Und die Cafeteria... wow. #highschool #ersterschultag #usaexchange',
      'Erster Schultag in Kanada und ich verstehe die Haelfte nicht \u{1F605} Aber alle sind mega freundlich! Die Schule hat einen eigenen Eishockey-Rink! \u{1F3D2}\u{1F1E8}\u{1F1E6}',
      'Tag 1 an der irischen Schule: Schuluniform an, Nervositaet auf 100, aber meine Klasse hat mich sofort aufgenommen! \u{2618}\u{FE0F}\u{1F4DA} #ireland #exchangestudent',
    ],
    media_indicators: ['school', 'classroom', 'locker', 'uniform', 'backpack', 'schule', 'klasse', 'schulgebaeude', 'stundenplan'],
    emotional_tone: 'excited',
    priority: 1,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine begeisterte, authentische Caption ueber den ersten Schultag im Ausland. Ton: aufgeregt, leicht nervoess, neugierig. Die Caption soll deutschen Schuelern Lust auf ein Auslandsjahr machen.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name}s ersten Schultag an der {school_name} in {country}. Besonderheiten der Schule: {school_highlights}. Faecher: {subjects}. Verwende 2-4 Emojis und 3-5 Hashtags.',
      tone_keywords: ['aufgeregt', 'neugierig', 'beeindruckt', 'anders als gedacht', 'Highschool-Feeling'],
      max_length: 500,
    },
  },

  // ─── 3. HOST FAMILY MOMENT ────────────────────────
  {
    id: 'host_family_moment',
    name: 'Gastfamilien-Moment',
    description: 'Schoene Momente mit der Gastfamilie: gemeinsames Kochen, Ausfluege, Traditionen, Geburtstage, Alltag. Zeigt das echte Gastfamilien-Erlebnis und baut Vertrauen bei Eltern auf.',
    ideal_timing: 'Ab Woche 2, durchgehend',
    timing_weeks: '2-44',
    suggested_format: 'Story',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: false,
      tiktok: false,
      best_platform: 'instagram_story',
    },
    example_captions: [
      'Sonntagsbrunch mit meiner Host Family \u{1F95E}\u{2764}\u{FE0F} Wir haben Pancakes gemacht und meine Gastmutter hat mir das Rezept ihrer Oma gezeigt! #gastfamilie #homestay #familymoments',
      'Meine Gastfamilie hat mir zum Geburtstag einen Kuchen gebacken und das ganze Haus dekoriert \u{1F382}\u{1F62D} Ich fuehl mich hier wirklich zuhause! #birthday #hostfamily #treffsprachreisen',
      'Thanksgiving-Dinner mit meiner Host Family: Turkey, Pie und so viel Liebe! \u{1F983}\u{2764}\u{FE0F} Danke fuer alles, ihr seid meine zweite Familie geworden. #thanksgiving #grateful',
    ],
    media_indicators: ['family', 'dinner', 'cooking', 'birthday', 'holiday', 'gastfamilie', 'essen', 'zusammen', 'gemeinsam', 'feier'],
    emotional_tone: 'reflective',
    priority: 2,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine warmherzige Caption ueber einen schoenen Moment mit der Gastfamilie. Ton: dankbar, herzlich, authentisch. Wichtig: Eltern lesen mit — zeige dass die Gastfamilie liebevoll und fuersorgend ist.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer einen besonderen Moment von {student_name} mit der Gastfamilie {host_family} in {country}. Anlass: {occasion}. Was passiert ist: {description}. Verwende 2-3 Emojis und 3-4 Hashtags.',
      tone_keywords: ['dankbar', 'herzlich', 'zweite Familie', 'Zuhause-Gefuehl', 'Tradition'],
      max_length: 450,
    },
  },

  // ─── 4. CULTURAL SHOCK / CULTURAL DISCOVERY ───────
  {
    id: 'cultural_shock',
    name: 'Kultur-Schock & Entdeckungen',
    description: 'Ueberraschende kulturelle Unterschiede: Essen, Gewohnheiten, Schulsystem, Verkehrsregeln, Social Norms. Unterhaltsam und lehrreich zugleich.',
    ideal_timing: 'Woche 2-8 (Phase des Kulturschocks)',
    timing_weeks: '2-8',
    suggested_format: 'Reel',
    suggested_template_category: 'laender_spotlight',
    pillar_mapping: 'laender_spotlight',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'tiktok',
    },
    example_captions: [
      'Dinge die in den USA normal sind aber mich SCHOCKIERT haben \u{1F92F}: 1) Schuhe im Haus 2) Red Cups sind ECHT 3) Schulbusse sind wirklich gelb 4) Alles ist XXL #cultureshock #usa #deutscherimausland',
      'Niemand hat mich gewarnt dass man in Australien zum Fruehstueck VEGEMITE isst \u{1F635} Ich sag nur: Es ist... ein Erlebnis \u{1F602} #australia #vegemite #cultureshock #exchangelife',
      'In Kanada fragt man nicht "Wie geht\'s?" — man sagt "How\'s it going, eh?" UND WARTET NICHT AUF EINE ANTWORT \u{1F602}\u{1F1E8}\u{1F1E6} #kanada #kulturschock #canadianlife',
    ],
    media_indicators: ['different', 'weird', 'surprise', 'culture', 'food', 'strange', 'komisch', 'anders', 'verrueckt', 'ueberraschung'],
    emotional_tone: 'humorous',
    priority: 2,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine unterhaltsame Caption ueber kulturelle Unterschiede und Ueberraschungen. Ton: humorvoll, staunend, selbstironisch. Der Content soll viral-faehig sein und zum Teilen einladen.',
      user_prompt_template: 'Schreibe eine lustige Instagram-Caption ueber kulturelle Unterschiede die {student_name} in {country} entdeckt hat: {cultural_differences}. Mach es als Liste oder Vergleich "Deutschland vs. {country}". Verwende 2-4 Emojis und 4-6 Hashtags.',
      tone_keywords: ['schockiert', 'lustig', 'so anders', 'wusstet ihr dass', 'expectation vs reality'],
      max_length: 500,
    },
  },

  // ─── 5. HOLIDAY ABROAD ────────────────────────────
  {
    id: 'holiday_abroad',
    name: 'Feiertag im Ausland',
    description: 'Feiertage und besondere Anlaesse im Gastland erleben: Thanksgiving, Halloween, 4th of July, Christmas, Waitangi Day etc. Hochemotional und saisonaler Evergreen-Content.',
    ideal_timing: 'Zu den jeweiligen Feiertagen (siehe seasonalCalendar.js)',
    timing_weeks: 'variabel',
    suggested_format: 'Carousel',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_feed',
    },
    example_captions: [
      'Mein erstes Thanksgiving! \u{1F983} 20 Leute, ein riesiger Truthahn, drei verschiedene Pies und ganz viel Dankbarkeit. Ich bin so froh hier zu sein! #thanksgiving #usaexchange #grateful',
      'Weihnachten in Australien = 35 Grad und BBQ am Strand \u{1F3D6}\u{FE0F}\u{1F384} Das ist so surreal aber gleichzeitig mega cool! #christmasinaustralia #summerchristmas',
      'Halloween in Irland — dem URSPRUNGSLAND! \u{1F383}\u{2618}\u{FE0F} Wir waren Trick or Treating und die Dekorationen hier sind naechstes Level! #halloween #ireland #spookyseason',
    ],
    media_indicators: ['holiday', 'celebration', 'christmas', 'thanksgiving', 'halloween', 'feiertag', 'feier', 'dekoration', 'tradition'],
    emotional_tone: 'excited',
    priority: 2,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine begeisterte Caption ueber einen Feiertag im Ausland. Ton: staunend, dankbar, kulturell interessiert. Zeige wie besonders es ist, Feiertage in einer anderen Kultur zu erleben.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name}, der/die {holiday_name} in {country} erlebt hat. Was sie gemacht haben: {activities}. Besonderheiten: {highlights}. Verwende 2-4 Emojis und 3-5 Hashtags.',
      tone_keywords: ['zum ersten Mal', 'unglaublich', 'Tradition', 'so anders als zuhause', 'unvergesslich'],
      max_length: 500,
    },
  },

  // ─── 6. SCHOOL EVENT ──────────────────────────────
  {
    id: 'school_event',
    name: 'Schul-Event',
    description: 'Besondere Schulevents: Prom, Homecoming, Spirit Week, Sportevents, Schultheater, Field Trips, Graduation. Das "Highschool-Film-Gefuehl" in echt.',
    ideal_timing: 'Bei Events (variabel, ca. monatlich)',
    timing_weeks: 'variabel',
    suggested_format: 'Reel',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_reel',
    },
    example_captions: [
      'HOMECOMING DANCE! \u{1F483}\u{1F57A} Das ist wirklich wie im Film! Corsage, Limo, Gym voller Lichterketten... ich kann es immer noch nicht glauben! #homecoming #highschool #americandream',
      'Unser Football-Team hat das Finale gewonnen und die ganze Schule ist AUSGERASTET! \u{1F3C8}\u{1F525} Spirit Week war der absolute Wahnsinn! #fridaynightlights #schoolspirit',
      'Field Trip zum Grand Canyon mit meinem Geographie-Kurs! \u{1F3DC}\u{FE0F} In Deutschland machen wir Ausfluege ins Museum, hier faehrt man zum Grand Canyon \u{1F602} #fieldtrip #grandcanyon #highschoolusa',
    ],
    media_indicators: ['prom', 'homecoming', 'dance', 'sports', 'game', 'field trip', 'spirit', 'graduation', 'schulfest', 'sport', 'team'],
    emotional_tone: 'excited',
    priority: 3,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine energiegeladene Caption ueber ein Schulevent im Ausland. Ton: aufgeregt, begeistert, "like in the movies". Ziel: Jugendlichen zeigen wie epic Highschool im Ausland ist.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name} bei {event_name} an der {school_name} in {country}. Was passiert ist: {event_description}. Verwende 3-4 Emojis und 4-5 Hashtags.',
      tone_keywords: ['wie im Film', 'unglaublich', 'School Spirit', 'einmalig', 'Highschool-Feeling'],
      max_length: 500,
    },
  },

  // ─── 7. FAREWELL / ABSCHIED ───────────────────────
  {
    id: 'farewell',
    name: 'Abschied & Abreise',
    description: 'Der emotionale Abschied: letzte Tage mit der Gastfamilie, Abschied von Freunden, Rueckflug. Der emotionalste Content ueberhaupt — extrem hohe Engagement-Raten.',
    ideal_timing: 'Letzte 1-2 Wochen vor Abreise',
    timing_weeks: '42-44',
    suggested_format: 'Reel',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_reel',
    },
    example_captions: [
      'Heute ist mein letzter Tag in den USA und ich bin ein absolutes Wrack \u{1F62D} 10 Monate die mein Leben veraendert haben. Danke an alle die dieses Jahr so besonders gemacht haben \u{2764}\u{FE0F} #abschied #auslandsjahr #thankful',
      'Flughafen. Traenen. Aber auch: unendliche Dankbarkeit. \u{2708}\u{FE0F}\u{1F62D}\u{2764}\u{FE0F} Australien, du hast mein Herz gestohlen. Ich komme zurueck! #farewell #australia #comingback',
      'Meine Gastfamilie hat gesagt: "Du bist jetzt Teil unserer Familie. Fuer immer." Ich heule seit Stunden. \u{1F62D}\u{1F3E0}\u{2764}\u{FE0F} #gastfamilie #danke #forever #treffsprachreisen',
    ],
    media_indicators: ['goodbye', 'farewell', 'last day', 'crying', 'airport', 'suitcase', 'abschied', 'letzter tag', 'tschuess', 'traenen', 'danke'],
    emotional_tone: 'nostalgic',
    priority: 1,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine zutiefst emotionale Caption ueber den Abschied. Ton: nostalgisch, dankbar, emotional. Diese Captions generieren die hoechsten Engagement-Raten — lass die Emotionen zu!',
      user_prompt_template: 'Schreibe eine emotionale Instagram-Caption fuer {student_name}s Abschied aus {country} nach {duration} Monaten. Gastfamilie: {host_family}. Besondere Momente: {special_memories}. Verwende 2-3 Emojis und 3-4 Hashtags.',
      tone_keywords: ['danke', 'fuer immer', 'zweites Zuhause', 'Traenen', 'unvergesslich', 'veraendert'],
      max_length: 500,
    },
  },

  // ─── 8. ALUMNI REUNION / RUECKBLICK ───────────────
  {
    id: 'alumni_reunion',
    name: 'Alumni-Rueckblick & Reunion',
    description: 'Ehemalige Austauschschueler blicken zurueck: Reunion-Events, "Vorher/Nachher", persoenliche Entwicklung, Besuche bei der Gastfamilie, Fernfreundschaften die geblieben sind.',
    ideal_timing: 'Ab 3 Monate nach Rueckkehr, jaehrliche Wiederkehr',
    timing_weeks: '50+',
    suggested_format: 'Carousel',
    suggested_template_category: 'erfahrungsberichte',
    pillar_mapping: 'erfahrungsberichte',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: false,
      best_platform: 'instagram_feed',
    },
    example_captions: [
      'Vor genau einem Jahr stand ich am Flughafen mit einem Koffer und tausend Fragezeichen. Heute bin ich ein anderer Mensch \u{2764}\u{FE0F} Swipe fuer mein Vorher/Nachher! #throwback #auslandsjahr #personalegrowth',
      'REUNION! Meine Host-Schwester ist fuer 2 Wochen nach Deutschland gekommen! \u{1F62D}\u{2764}\u{FE0F}\u{1F1E9}\u{1F1EA}\u{1F1FA}\u{1F1F8} Es fuehlt sich an als waere es gestern gewesen! #reunion #hostfamily #friendship',
      'TREFF Alumni-Treffen 2026! 30 ehemalige Austauschschueler, 1000 Geschichten \u{1F30D}\u{2764}\u{FE0F} Wenn ihr euch fragt ob es das wert war: ABSOLUT. #treffsprachreisen #alumni #worthit',
    ],
    media_indicators: ['reunion', 'throwback', 'before after', 'visit', 'alumni', 'rueckblick', 'vorher nachher', 'wiedersehen', 'besuch'],
    emotional_tone: 'nostalgic',
    priority: 3,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine reflektierende Caption aus der Alumni-Perspektive. Ton: nostalgisch, dankbar, inspirierend. Ziel: Unentschlossenen zeigen, wie lebensvereendernd ein Auslandsjahr sein kann.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name}, der/die vor {time_since} aus {country} zurueckgekommen ist. Anlass: {occasion}. Groesste Veraenderung: {biggest_change}. Verwende 2-3 Emojis und 3-5 Hashtags.',
      tone_keywords: ['Rueckblick', 'veraendert', 'dankbar', 'wuerde es jederzeit wieder tun', 'beste Entscheidung'],
      max_length: 500,
    },
  },

  // ─── 9. TRAVEL & ADVENTURE ────────────────────────
  {
    id: 'travel_adventure',
    name: 'Reise & Abenteuer',
    description: 'Ausfluege, Road Trips, Wochenend-Trips, Naturerlebnisse: Nationalparks, Straende, Staedte. Zeigt das Abenteuer-Element des Austauschjahres — perfekt fuer Fernweh-Content.',
    ideal_timing: 'Ab Woche 3, bei Reisen und Ausfluegen',
    timing_weeks: '3-44',
    suggested_format: 'Reel',
    suggested_template_category: 'laender_spotlight',
    pillar_mapping: 'laender_spotlight',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_reel',
    },
    example_captions: [
      'Road Trip nach San Francisco! Golden Gate Bridge in echt ist noch beeindruckender als auf den Fotos \u{1F309}\u{1F1FA}\u{1F1F8} #sanfrancisco #roadtrip #goldengatebridge #exchangelife',
      'Wochenendtrip nach Niagara Falls mit meiner Gastfamilie! Der Sound von dem Wasser ist UNGLAUBLICH \u{1F4A6}\u{1F1E8}\u{1F1E6} #niagarafalls #kanada #abenteuer',
      'Snorkelling am Great Barrier Reef! \u{1F420}\u{1F3DD}\u{FE0F} Das war auf meiner Bucket-List seit ich 10 bin! #greatbarrierreef #australia #bucketlist #exchangeperks',
    ],
    media_indicators: ['travel', 'trip', 'nature', 'beach', 'mountain', 'city', 'landmark', 'road trip', 'reise', 'ausflug', 'strand', 'berge', 'natur', 'nationalpark'],
    emotional_tone: 'excited',
    priority: 2,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine begeisterte Caption ueber ein Reise-Abenteuer. Ton: abenteuerlustig, staunend, Fernweh-ausloeesend. Mach Lust auf Entdeckungen!',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name}s Ausflug nach/zum {destination} in {country}. Was sie erlebt haben: {experience}. Verwende 2-4 Emojis und 3-5 Hashtags.',
      tone_keywords: ['Abenteuer', 'atemberaubend', 'Bucket List', 'Fernweh', 'unglaublich'],
      max_length: 450,
    },
  },

  // ─── 10. LANGUAGE MILESTONE ───────────────────────
  {
    id: 'language_milestone',
    name: 'Sprach-Meilenstein',
    description: 'Fortschritte in der Fremdsprache: erster Witz auf Englisch, Traum auf Englisch, Slang gelernt, Schulpraesentation gehalten. Zeigt den bildungsrelevanten Wert des Programms.',
    ideal_timing: 'Ab Monat 2, bei Meilensteinen',
    timing_weeks: '8-44',
    suggested_format: 'Carousel',
    suggested_template_category: 'tipps_tricks',
    pillar_mapping: 'tipps_tricks',
    platform_mapping: {
      instagram_feed: true,
      instagram_story: true,
      instagram_reel: true,
      tiktok: true,
      best_platform: 'instagram_feed',
    },
    example_captions: [
      'Heute habe ich zum ersten Mal auf Englisch GETRAEUMT \u{1F62E}\u{1F4AD} Ich glaube mein Gehirn hat den Switch gemacht! #languageprogress #dreaminenglish #auslandsjahr',
      'Ich habe einen Witz auf Englisch gemacht und ALLE haben gelacht! \u{1F602} Das war der Moment wo ich wusste: Ich bin angekommen \u{2764}\u{FE0F} #milestone #englisch #fluent',
      'Meine Englisch-Lehrerin in Deutschland haette Traenen in den Augen wenn sie meinen australischen Akzent hoeren wuerde \u{1F602}\u{1F1E6}\u{1F1FA} No worries mate! #aussieaccent #languagegoals',
    ],
    media_indicators: ['language', 'english', 'speaking', 'presentation', 'report card', 'grades', 'sprache', 'englisch', 'praesentation', 'zeugnis', 'noten'],
    emotional_tone: 'reflective',
    priority: 3,
    prompt_template: {
      system_context: 'Du bist ein Social-Media-Texter fuer TREFF Sprachreisen. Schreibe eine stolze Caption ueber einen Sprach-Meilenstein. Ton: stolz, erstaunt, motivierend. Zeige Eltern den Bildungswert und Schuelern den coolen Aspekt.',
      user_prompt_template: 'Schreibe eine Instagram-Caption fuer {student_name}s Sprach-Meilenstein in {country}: {milestone_description}. Wie lange sie dort sind: {duration_weeks} Wochen. Verwende 2-3 Emojis und 3-4 Hashtags.',
      tone_keywords: ['stolz', 'Fortschritt', 'Meilenstein', 'fliesssend', 'angekommen'],
      max_length: 450,
    },
  },
]

// ============================================================
// AI PROCESSING RULES
// (Auto-suggest content type from uploaded media)
// ============================================================

export const AI_PROCESSING_RULES = [
  {
    trigger: 'image_upload',
    media_patterns: ['airport', 'airplane', 'luggage', 'arrival', 'welcome', 'flughafen', 'koffer'],
    suggested_content_type: 'arrival_story',
    confidence_threshold: 0.7,
    fallback_type: 'travel_adventure',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['school', 'classroom', 'locker', 'textbook', 'backpack', 'uniform', 'schule', 'klasse'],
    suggested_content_type: 'first_day_school',
    confidence_threshold: 0.7,
    fallback_type: 'school_event',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['family', 'dinner', 'cooking', 'home', 'living room', 'kitchen', 'gastfamilie', 'essen', 'zuhause'],
    suggested_content_type: 'host_family_moment',
    confidence_threshold: 0.6,
    fallback_type: 'cultural_shock',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['prom', 'homecoming', 'dance', 'sports', 'game', 'rally', 'field trip', 'concert', 'sport', 'team'],
    suggested_content_type: 'school_event',
    confidence_threshold: 0.7,
    fallback_type: 'travel_adventure',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['holiday', 'christmas', 'thanksgiving', 'halloween', 'celebration', 'feiertag', 'weihnachten', 'dekoration'],
    suggested_content_type: 'holiday_abroad',
    confidence_threshold: 0.75,
    fallback_type: 'host_family_moment',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['landscape', 'beach', 'mountain', 'city', 'landmark', 'road trip', 'nature', 'strand', 'berge', 'natur', 'nationalpark'],
    suggested_content_type: 'travel_adventure',
    confidence_threshold: 0.65,
    fallback_type: 'cultural_shock',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['goodbye', 'farewell', 'crying', 'hugging', 'last day', 'suitcase', 'abschied', 'tschuess', 'traenen'],
    suggested_content_type: 'farewell',
    confidence_threshold: 0.7,
    fallback_type: 'host_family_moment',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['reunion', 'throwback', 'before after', 'alumni', 'visit', 'wiedersehen', 'rueckblick'],
    suggested_content_type: 'alumni_reunion',
    confidence_threshold: 0.7,
    fallback_type: 'host_family_moment',
  },
  {
    trigger: 'image_upload',
    media_patterns: ['report card', 'presentation', 'grades', 'certificate', 'zeugnis', 'praesentation', 'noten', 'urkunde'],
    suggested_content_type: 'language_milestone',
    confidence_threshold: 0.65,
    fallback_type: 'school_event',
  },
  {
    trigger: 'video_upload',
    media_patterns: ['speaking', 'interview', 'selfie video', 'vlog', 'reaction'],
    suggested_content_type: 'cultural_shock',
    confidence_threshold: 0.5,
    fallback_type: 'travel_adventure',
  },
]

// ============================================================
// STUDENT CONTENT LIFECYCLE
// (Timing guide for the social media team)
// ============================================================

export const CONTENT_LIFECYCLE = {
  pre_departure: {
    label: 'Vor der Abreise',
    weeks: '-4 bis -1',
    content_types: ['arrival_story'],
    description: 'Vorbereitungs-Content: Packen, Abschied von Freunden, Vorfreude. Noch KEIN Student-Content — TREFF-Team erstellt Inhalte.',
    team_action: 'Bereite Templates und Hashtag-Sets vor fuer den Schueler.',
  },
  arrival_phase: {
    label: 'Ankunft (Woche 1-2)',
    weeks: '1-2',
    content_types: ['arrival_story', 'first_day_school'],
    description: 'Emotionalste Phase — hohe Engagement-Raten. Schnell reagieren auf eingehende Medien!',
    team_action: 'Schnelle Bearbeitung: Max. 24h von Upload bis Post.',
  },
  settling_in: {
    label: 'Einleben (Woche 3-8)',
    weeks: '3-8',
    content_types: ['host_family_moment', 'cultural_shock', 'school_event', 'travel_adventure'],
    description: 'Kulturschock-Phase — unterhaltsamer Content ueber Unterschiede. Regelmaessiger Content-Fluss.',
    team_action: 'Ermutige Schueler, kulturelle Unterschiede zu dokumentieren.',
  },
  daily_life: {
    label: 'Alltag (Woche 9-36)',
    weeks: '9-36',
    content_types: ['host_family_moment', 'school_event', 'holiday_abroad', 'travel_adventure', 'language_milestone'],
    description: 'Laengste Phase — Content wird alltaeglicher. Gezielt nach besonderen Momenten fragen!',
    team_action: 'Proaktiv Reminder senden bei Feiertagen und Events. Storytelling-Boegen planen.',
  },
  farewell_phase: {
    label: 'Abschied (Woche 37-44)',
    weeks: '37-44',
    content_types: ['farewell', 'language_milestone'],
    description: 'Hochemotionaler Content — Abschiede generieren die hoechsten Engagement-Raten.',
    team_action: 'Frueh planen! Schueler bitten, letzte Wochen bewusst zu dokumentieren.',
  },
  alumni_phase: {
    label: 'Alumnus (ab Woche 50)',
    weeks: '50+',
    content_types: ['alumni_reunion'],
    description: 'Rueckblick-Content und Reunions. Evergreen-Content der immer funktioniert.',
    team_action: 'Jaehrliche Alumni-Interviews planen. Vorher/Nachher-Content kuratieren.',
  },
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

/**
 * Get a content type by ID.
 * @param {string} id - Content type ID
 * @returns {StudentContentType|undefined}
 */
export function getContentTypeById(id) {
  return STUDENT_CONTENT_TYPES.find(ct => ct.id === id)
}

/**
 * Get all content type IDs.
 * @returns {string[]}
 */
export function getContentTypeIds() {
  return STUDENT_CONTENT_TYPES.map(ct => ct.id)
}

/**
 * Get content types suitable for a specific platform.
 * @param {'instagram_feed'|'instagram_story'|'instagram_reel'|'tiktok'} platform
 * @returns {StudentContentType[]}
 */
export function getContentTypesForPlatform(platform) {
  return STUDENT_CONTENT_TYPES.filter(ct => ct.platform_mapping[platform])
}

/**
 * Get content types for a specific lifecycle phase.
 * @param {string} phase - Phase key from CONTENT_LIFECYCLE
 * @returns {StudentContentType[]}
 */
export function getContentTypesForPhase(phase) {
  const lifecycle = CONTENT_LIFECYCLE[phase]
  if (!lifecycle) return []
  return lifecycle.content_types
    .map(id => getContentTypeById(id))
    .filter(Boolean)
}

/**
 * Suggest a content type based on media indicators.
 * Matches keywords in the provided description against each type's media_indicators.
 *
 * @param {string} mediaDescription - Description or tags of the uploaded media
 * @returns {{ contentType: StudentContentType, score: number }[]} Sorted by score (highest first)
 */
export function suggestContentType(mediaDescription) {
  const desc = mediaDescription.toLowerCase()
  const results = []

  for (const ct of STUDENT_CONTENT_TYPES) {
    let matchCount = 0
    for (const indicator of ct.media_indicators) {
      if (desc.includes(indicator.toLowerCase())) {
        matchCount++
      }
    }
    if (matchCount > 0) {
      const score = matchCount / ct.media_indicators.length
      results.push({ contentType: ct, score })
    }
  }

  return results.sort((a, b) => b.score - a.score)
}

/**
 * Get the AI processing rule for a media upload.
 * @param {string[]} detectedLabels - Labels/tags detected in the uploaded media
 * @returns {{ rule: AIProcessingRule, contentType: StudentContentType, confidence: number }|null}
 */
export function getAIProcessingRule(detectedLabels) {
  const labelsLower = detectedLabels.map(l => l.toLowerCase())

  let bestMatch = null
  let bestScore = 0

  for (const rule of AI_PROCESSING_RULES) {
    let matchCount = 0
    for (const pattern of rule.media_patterns) {
      if (labelsLower.some(l => l.includes(pattern.toLowerCase()))) {
        matchCount++
      }
    }
    if (matchCount > 0) {
      const score = matchCount / rule.media_patterns.length
      if (score >= rule.confidence_threshold && score > bestScore) {
        bestScore = score
        bestMatch = {
          rule,
          contentType: getContentTypeById(rule.suggested_content_type),
          confidence: score,
        }
      }
    }
  }

  return bestMatch
}

/**
 * Get content types sorted by priority (highest priority first).
 * @returns {StudentContentType[]}
 */
export function getContentTypesByPriority() {
  return [...STUDENT_CONTENT_TYPES].sort((a, b) => a.priority - b.priority)
}

/**
 * Build a prompt for AI text generation based on content type and variables.
 * @param {string} contentTypeId - Content type ID
 * @param {Object} variables - Variables to fill into the prompt template
 * @returns {{ system: string, user: string, maxLength: number }|null}
 */
export function buildAIPrompt(contentTypeId, variables = {}) {
  const ct = getContentTypeById(contentTypeId)
  if (!ct) return null

  let userPrompt = ct.prompt_template.user_prompt_template
  for (const [key, value] of Object.entries(variables)) {
    userPrompt = userPrompt.replace(`{${key}}`, value)
  }

  return {
    system: ct.prompt_template.system_context,
    user: userPrompt,
    maxLength: ct.prompt_template.max_length,
  }
}
