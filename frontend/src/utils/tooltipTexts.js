/**
 * Central tooltip texts for the entire application.
 * Organized by view/section for maintainability.
 * i18n-ready: all texts in German, can be replaced with a translation system later.
 */

export const tooltipTexts = {
  // ─── Create Post Wizard ───────────────────────────────────────────
  createPost: {
    stepCategory: 'Waehle die Art des Posts. Jede Kategorie hat passende Templates und KI-Vorschlaege.',
    stepTemplate: 'Templates definieren das visuelle Layout deines Posts. Waehle eines, das zu deiner Kategorie passt.',
    stepPlatform: 'Verschiedene Plattformen haben unterschiedliche Formate: Instagram Feed (1:1/4:5), Story (9:16), TikTok (9:16). Du kannst mehrere gleichzeitig waehlen.',
    stepTopic: 'Beschreibe kurz, worum es im Post geht. Die KI nutzt diese Infos fuer die Textgenerierung.',
    stepKeyPoints: 'Stichpunkte helfen der KI, die wichtigsten Informationen in den Text einzubauen.',
    stepCountry: 'Waehle das Zielland, damit KI-Texte und Hashtags laenderspezifisch angepasst werden.',
    stepTone: 'Der Tonfall bestimmt den Schreibstil der KI. "Jugendlich" spricht Schueler an, "Serioes" ueberzeugt Eltern.',
    stepGenerate: 'Die KI generiert Text basierend auf Kategorie, Thema, Stichpunkten und Tonfall. Du kannst den Text danach frei bearbeiten.',
    stepPreview: 'Hier siehst du eine Live-Vorschau deines Posts, wie er auf der Plattform aussehen wird.',
    stepEdit: 'Bearbeite Ueberschriften, Texte, Captions und Hashtags. Aenderungen werden in der Vorschau sofort sichtbar.',
    stepBackground: 'Lade ein eigenes Bild hoch oder generiere ein KI-Bild als Hintergrund fuer deinen Post.',
    stepExport: 'Exportiere den fertigen Post als PNG/JPG. Bei mehreren Slides wird eine ZIP-Datei erstellt.',
    multiPlatform: 'Wenn aktiviert, werden Inhalte automatisch fuer jede Plattform angepasst (z.B. Hashtag-Laenge, Caption-Stil).',
    slides: 'Jeder Post kann aus mehreren Slides bestehen. Ziehe Slides per Drag & Drop in die gewuenschte Reihenfolge.',
    captionInstagram: 'Die Instagram-Caption erscheint unter deinem Post. Maximal 2.200 Zeichen, die ersten 125 sind am wichtigsten.',
    captionTiktok: 'Die TikTok-Caption ist kuerzer. Maximal 300 Zeichen, praegnant und mit Hashtags.',
    hashtagsInstagram: 'Nutze 20-30 relevante Hashtags fuer maximale Reichweite. Mische populaere und Nischen-Hashtags.',
    hashtagsTiktok: 'Auf TikTok reichen 3-5 starke Hashtags. Trending-Hashtags erhoehen die Sichtbarkeit.',
    cta: 'Der Call-to-Action animiert die Zielgruppe zur Interaktion: Kommentieren, Teilen, Link in Bio besuchen.',
    engagementBoost: 'Analysiert deinen Post und schlaegt Verbesserungen vor, um mehr Likes, Kommentare und Shares zu erzielen.',
    hookSelector: 'Ein starker Hook faengt die Aufmerksamkeit in den ersten Sekunden. Waehle einen passenden Aufhaenger.',
    interactiveElements: 'Fuege interaktive Story-Elemente wie Umfragen, Quiz oder Slider hinzu, um das Engagement zu steigern.',
    humorFormat: 'Humor-Formate machen Posts einpraegsamer. Waehle ein Format, das zum Thema passt.',
    aiImagePrompt: 'Beschreibe das gewuenschte Bild auf Englisch. Je detaillierter, desto besser das Ergebnis.',
    aiImageAspectRatio: 'Das Seitenverhaeltnis sollte zur Plattform passen: 1:1 fuer Feed, 9:16 fuer Stories/Reels.',
    exportQuality: 'Hoehere Qualitaet erzeugt groessere Dateien. "Hoch" fuer Print, "Standard" reicht fuer Social Media.',
    studentSelector: 'Verknuepfe einen Studenten mit dem Post. Die KI uebernimmt dann dessen Persoenlichkeits-Preset fuer die Textgenerierung.',
    storyArcSelector: 'Verknuepfe den Post mit einem Story-Arc, um ihn als Episode in eine Serie einzubetten.',
    cliffhanger: 'Ein Cliffhanger am Ende motiviert die Zielgruppe, auch den naechsten Post zu lesen.',
    ctaLibrary: 'Die CTA-Bibliothek enthaelt vorgefertigte Call-to-Actions, sortiert nach Engagement, Conversion, Awareness und Traffic.',
    hashtagSuggest: 'Die KI schlaegt basierend auf Thema, Land und Plattform passende Hashtags vor.',
  },

  // ─── Calendar ─────────────────────────────────────────────────────
  calendar: {
    gapDetection: 'Zeigt Tage ohne geplante Posts (Luecken). Regelmaessiges Posten ist wichtig fuer den Algorithmus.',
    contentMix: 'Analysiert die Verteilung deiner Post-Kategorien. Ein ausgewogener Mix erreicht verschiedene Zielgruppen.',
    seasonalMarkers: 'Markiert wichtige Termine wie Bewerbungsfristen, Schulferien und Events fuer zeitgerechtes Posting.',
    storyArcTimeline: 'Zeigt laufende Story-Serien als Zeitstrahl. Hilft, Episoden im richtigen Abstand zu planen.',
    dragDrop: 'Ziehe Posts per Drag & Drop auf ein neues Datum, um sie umzuplanen. Story-Arc-Episoden werden auf Reihenfolge geprueft.',
    recycling: 'Schlaegt erfolgreiche aeltere Posts vor, die recycelt werden koennen, um Luecken im Kalender zu fuellen.',
    episodeOrder: 'Story-Arc-Episoden muessen in der richtigen Reihenfolge veroeffentlicht werden. Konflikte werden rot markiert.',
  },

  // ─── Dashboard ────────────────────────────────────────────────────
  dashboard: {
    postsThisWeek: 'Anzahl der Posts, die in dieser Woche (Mo-So) erstellt oder veroeffentlicht wurden.',
    scheduledPosts: 'Posts, die fuer die Zukunft eingeplant sind und noch veroeffentlicht werden muessen.',
    totalAssets: 'Gesamtzahl der hochgeladenen Bilder, Videos und Medien in deiner Asset-Bibliothek.',
    totalPosts: 'Alle jemals erstellten Posts (Entwuerfe, geplante und veroeffentlichte).',
    next7Days: 'Zeigt die naechsten 7 Tage mit geplanten Posts. Leere Tage sind Posting-Luecken.',
    suggestions: 'KI-generierte Vorschlaege fuer neue Posts basierend auf deinem Content-Mix und Kalender.',
    recentPosts: 'Die zuletzt erstellten oder bearbeiteten Posts fuer schnellen Zugriff.',
    recyclingPanel: 'Zeigt aeltere Posts, die gut performt haben und recycelt werden koennten.',
    seriesStatus: 'Ueberblick ueber laufende Story-Serien und deren Fortschritt.',
  },

  // ─── Settings ─────────────────────────────────────────────────────
  settings: {
    email: 'Die E-Mail-Adresse, mit der du dich anmeldest. Wird auch fuer Benachrichtigungen verwendet.',
    displayName: 'Der Name, der in der App angezeigt wird. Kann jederzeit geaendert werden.',
    primaryColor: 'Die Hauptfarbe deiner Marke (Standard: TREFF-Blau #4C8BC2). Wird in Templates als Akzentfarbe verwendet.',
    secondaryColor: 'Die Zweitfarbe (Standard: TREFF-Gelb #FDD000). Fuer Highlights und CTAs.',
    accentColor: 'Zusaetzliche Akzentfarbe fuer Details und Hover-Effekte in Templates.',
    geminiApiKey: 'Dein Google Gemini API-Schluessel fuer KI-Textgenerierung und Bildgenerierung. Kostenlos bei Google AI Studio erhaeltlich.',
    openaiApiKey: 'Optionaler Fallback fuer Textgenerierung, falls Gemini nicht verfuegbar ist.',
    unsplashApiKey: 'Fuer Zugriff auf lizenzfreie Stockfotos von Unsplash als Hintergrundbilder.',
    postsPerWeek: 'Dein Posting-Ziel pro Woche. Das Dashboard zeigt den Fortschritt und die Kalender-Luecken-Erkennung basiert darauf.',
    postsPerMonth: 'Monatliches Posting-Ziel. Wird fuer die langfristige Fortschrittsanalyse verwendet.',
    minEpisodeGap: 'Mindestabstand in Tagen zwischen Story-Arc-Episoden. Verhindert, dass Episoden zu dicht aufeinander geplant werden.',
    hashtagSets: 'Verwaltung von Hashtag-Gruppen nach Laendern und Kategorien. Seeded Sets sind vordefiniert, eigene koennen erstellt werden.',
  },

  // ─── Analytics ────────────────────────────────────────────────────
  analytics: {
    overview: 'Ueberblick ueber deine Posting-Aktivitaet der letzten 30 Tage mit Trends und Vergleichen.',
    goalTracking: 'Zeigt deinen Fortschritt gegenueber deinen woechentlichen und monatlichen Posting-Zielen.',
    categoryDistribution: 'Verteilung deiner Posts nach Kategorien. Ein ausgewogener Mix ist empfohlen.',
    platformDistribution: 'Verteilung deiner Posts nach Plattformen (Instagram Feed, Story, TikTok).',
    countryDistribution: 'Zeigt, ueber welche Laender du am meisten postest. Alle 5 Laender sollten vertreten sein.',
    postingFrequency: 'Posting-Frequenz ueber die Zeit. Regelmaessigkeit ist wichtiger als Quantitaet.',
  },

  // ─── Video Tools ──────────────────────────────────────────────────
  video: {
    videoExport: 'Exportiere Videos in verschiedenen Formaten: 9:16 (Reel/TikTok), 1:1 (Feed), 4:5 (Portrait).',
    aspectRatio: 'Das Seitenverhaeltnis bestimmt den Zuschnitt: 9:16 fuer Hochformat (Stories/Reels), 1:1 fuer Quadrat (Feed), 4:5 fuer Portrait.',
    focusPoint: 'Bestimmt den Mittelpunkt des Zuschnitts. Verschiebe den Regler, um den Bildausschnitt anzupassen.',
    qualitySlider: 'Hoehere Qualitaet (> 80%) fuer wichtige Posts, niedrigere fuer Entwuerfe. Standard reicht fuer Social Media.',
    platformPreset: 'Plattform-Presets setzen automatisch das richtige Format und die maximale Videolaenge.',
    batchExport: 'Exportiere ein Video gleichzeitig in mehreren Formaten. Spart Zeit bei Multi-Plattform-Posts.',
    videoTemplates: 'Vorgefertigte Video-Templates mit TREFF-Branding (Intro/Outro, Farbschema, Logo).',
    audioMixer: 'Mische Hintergrundmusik, Sprachaufnahmen und Sound-Effekte fuer deine Videos.',
    overlayEditor: 'Fuege Text- und Bild-Overlays zu Videos hinzu (Titel, Untertitel, Logo, Sticker).',
    thumbnailGenerator: 'Erstelle ansprechende Thumbnails fuer Reels und TikToks mit Text und Branding.',
  },

  // ─── Story-Arcs & Recurring Formats ──────────────────────────────
  storyArcs: {
    arcOverview: 'Story-Arcs sind mehrteilige Serien (z.B. "Mein erstes Semester in den USA"). Jede Serie hat mehrere Episoden.',
    arcWizard: 'Der Wizard fuehrt dich Schritt fuer Schritt durch die Erstellung eines neuen Story-Arcs.',
    episodeList: 'Alle Episoden des Story-Arcs mit Status (Entwurf, Geplant, Veroeffentlicht).',
    progressBar: 'Zeigt den Fortschritt des Story-Arcs: wie viele Episoden bereits veroeffentlicht sind.',
    arcStatus: 'Draft = In Planung, Active = Wird veroeffentlicht, Completed = Alle Episoden gepostet.',
    recurringFormats: 'Wiederkehrende Formate wie "Motivation Monday" oder "Freitags-Fail" sorgen fuer Kontinuitaet und Wiedererkennungswert.',
    crossPostLink: 'Verknuepft Feed-Posts mit zugehoerigen Stories, damit Follower weitergeleitet werden koennen.',
  },

  // ─── Templates ────────────────────────────────────────────────────
  templates: {
    templateGallery: 'Alle verfuegbaren Templates, sortiert nach Kategorien. Waehle eines als Grundlage fuer deinen Post.',
    templatePreview: 'Vorschau des Templates mit Platzhalter-Daten. Das finale Design entsteht mit deinen eigenen Inhalten.',
    templateCategory: 'Templates sind nach Post-Kategorien gruppiert (Laender-Spotlight, Erfahrungsberichte, Infografiken, etc.).',
  },

  // ─── Assets ───────────────────────────────────────────────────────
  assets: {
    upload: 'Lade Bilder und Videos hoch (PNG, JPG, MP4, WebM). Maximale Dateigrösse: 50 MB.',
    search: 'Suche in deinen Assets nach Dateinamen oder Tags.',
    assetTypes: 'Filtere nach Medientyp: Bilder, Videos, oder alle Dateien.',
  },

  // ─── Week Planner ─────────────────────────────────────────────────
  weekPlanner: {
    postsPerWeek: 'Wie viele Posts pro Woche geplant werden sollen. Die KI verteilt sie ueber die Woche.',
    recurringToggle: 'Aktiviere wiederkehrende Formate (z.B. Motivation Monday), damit die KI sie einplant.',
    seriesToggle: 'Aktiviere Story-Serien, damit die KI die naechsten Episoden automatisch einplant.',
    adoptPlan: 'Uebernimmt alle Vorschlaege als Entwuerfe in den Kalender. Du kannst sie danach einzeln bearbeiten.',
    dragReorder: 'Verschiebe Vorschlaege per Drag & Drop zwischen Tagen, um die Planung anzupassen.',
  },

  // ─── Students ─────────────────────────────────────────────────────
  students: {
    personalityPreset: 'Das Persoenlichkeits-Preset steuert den KI-Schreibstil: Tonfall, Humor-Level, Emoji-Nutzung und Perspektive.',
    catchphrases: 'Wiederkehrende Phrasen oder Ausdruecke des Studenten, die die KI in Texte einbauen kann (max. 5).',
    studentLink: 'Verknuepfe Studenten mit Posts, damit ihre Erfahrungen authentisch erzaehlt werden.',
  },
}

export default tooltipTexts
