/**
 * Central tooltip texts for the entire application.
 * Organized by view/section for maintainability.
 * i18n-ready: all texts in German, can be replaced with a translation system later.
 */

export const tooltipTexts = {
  // ─── Create Post Wizard ───────────────────────────────────────────
  createPost: {
    stepCategory: 'Wähle die Art des Posts. Jede Kategorie hat passende Templates und KI-Vorschläge.',
    stepTemplate: 'Templates definieren das visuelle Layout deines Posts. Wähle eines, das zu deiner Kategorie passt.',
    stepPlatform: 'Verschiedene Plattformen haben unterschiedliche Formate: Instagram Feed (1:1/4:5), Story (9:16), TikTok (9:16). Du kannst mehrere gleichzeitig wählen.',
    stepTopic: 'Beschreibe kurz, worum es im Post geht. Die KI nutzt diese Infos für die Textgenerierung.',
    stepKeyPoints: 'Stichpunkte helfen der KI, die wichtigsten Informationen in den Text einzubauen.',
    stepCountry: 'Wähle das Zielland, damit KI-Texte und Hashtags länderspezifisch angepasst werden.',
    stepTone: 'Der Tonfall bestimmt den Schreibstil der KI. "Jugendlich" spricht Schüler an, "Seriös" überzeugt Eltern.',
    stepGenerate: 'Die KI generiert Text basierend auf Kategorie, Thema, Stichpunkten und Tonfall. Du kannst den Text danach frei bearbeiten.',
    stepPreview: 'Hier siehst du eine Live-Vorschau deines Posts, wie er auf der Plattform aussehen wird.',
    stepEdit: 'Bearbeite Überschriften, Texte, Captions und Hashtags. Änderungen werden in der Vorschau sofort sichtbar.',
    stepBackground: 'Lade ein eigenes Bild hoch oder generiere ein KI-Bild als Hintergrund für deinen Post.',
    stepExport: 'Exportiere den fertigen Post als PNG/JPG. Bei mehreren Slides wird eine ZIP-Datei erstellt.',
    multiPlatform: 'Wenn aktiviert, werden Inhalte automatisch für jede Plattform angepasst (z.B. Hashtag-Länge, Caption-Stil).',
    slides: 'Jeder Post kann aus mehreren Slides bestehen. Ziehe Slides per Drag & Drop in die gewünschte Reihenfolge.',
    captionInstagram: 'Die Instagram-Caption erscheint unter deinem Post. Maximal 2.200 Zeichen, die ersten 125 sind am wichtigsten.',
    captionTiktok: 'Die TikTok-Caption ist kürzer. Maximal 300 Zeichen, prägnant und mit Hashtags.',
    hashtagsInstagram: 'Nutze 20-30 relevante Hashtags für maximale Reichweite. Mische populäre und Nischen-Hashtags.',
    hashtagsTiktok: 'Auf TikTok reichen 3-5 starke Hashtags. Trending-Hashtags erhöhen die Sichtbarkeit.',
    cta: 'Der Call-to-Action animiert die Zielgruppe zur Interaktion: Kommentieren, Teilen, Link in Bio besuchen.',
    engagementBoost: 'Analysiert deinen Post und schlägt Verbesserungen vor, um mehr Likes, Kommentare und Shares zu erzielen.',
    hookSelector: 'Ein starker Hook fängt die Aufmerksamkeit in den ersten Sekunden. Wähle einen passenden Aufhänger.',
    interactiveElements: 'Füge interaktive Story-Elemente wie Umfragen, Quiz oder Slider hinzu, um das Engagement zu steigern.',
    humorFormat: 'Humor-Formate machen Posts einprägsamer. Wähle ein Format, das zum Thema passt.',
    aiImagePrompt: 'Beschreibe das gewünschte Bild auf Englisch. Je detaillierter, desto besser das Ergebnis.',
    aiImageAspectRatio: 'Das Seitenverhältnis sollte zur Plattform passen: 1:1 für Feed, 9:16 für Stories/Reels.',
    exportQuality: 'Höhere Qualität erzeugt größere Dateien. "Hoch" für Print, "Standard" reicht für Social Media.',
    studentSelector: 'Verknüpfe einen Studenten mit dem Post. Die KI übernimmt dann dessen Persönlichkeits-Preset für die Textgenerierung.',
    storyArcSelector: 'Verknüpfe den Post mit einem Story-Arc, um ihn als Episode in eine Serie einzubetten.',
    cliffhanger: 'Ein Cliffhanger am Ende motiviert die Zielgruppe, auch den nächsten Post zu lesen.',
    ctaLibrary: 'Die CTA-Bibliothek enthält vorgefertigte Call-to-Actions, sortiert nach Engagement, Conversion, Awareness und Traffic.',
    hashtagSuggest: 'Die KI schlägt basierend auf Thema, Land und Plattform passende Hashtags vor.',
  },

  // ─── Calendar ─────────────────────────────────────────────────────
  calendar: {
    gapDetection: 'Zeigt Tage ohne geplante Posts (Lücken). Regelmäßiges Posten ist wichtig für den Algorithmus.',
    contentMix: 'Analysiert die Verteilung deiner Post-Kategorien. Ein ausgewogener Mix erreicht verschiedene Zielgruppen.',
    seasonalMarkers: 'Markiert wichtige Termine wie Bewerbungsfristen, Schulferien und Events für zeitgerechtes Posting.',
    storyArcTimeline: 'Zeigt laufende Story-Serien als Zeitstrahl. Hilft, Episoden im richtigen Abstand zu planen.',
    dragDrop: 'Ziehe Posts per Drag & Drop auf ein neues Datum, um sie umzuplanen. Story-Arc-Episoden werden auf Reihenfolge geprüft.',
    recycling: 'Schlägt erfolgreiche ältere Posts vor, die recycelt werden können, um Lücken im Kalender zu füllen.',
    episodeOrder: 'Story-Arc-Episoden müssen in der richtigen Reihenfolge veröffentlicht werden. Konflikte werden rot markiert.',
  },

  // ─── Dashboard ────────────────────────────────────────────────────
  dashboard: {
    postsThisWeek: 'Anzahl der Posts, die in dieser Woche (Mo-So) erstellt oder veröffentlicht wurden.',
    scheduledPosts: 'Posts, die für die Zukunft eingeplant sind und noch veröffentlicht werden müssen.',
    draftPosts: 'Posts im Entwurf-Status, die noch bearbeitet oder geplant werden können.',
    totalAssets: 'Gesamtzahl der hochgeladenen Bilder, Videos und Medien in deiner Asset-Bibliothek.',
    totalPosts: 'Alle jemals erstellten Posts (Entwürfe, geplante und veröffentlichte).',
    next7Days: 'Zeigt die nächsten 7 Tage mit geplanten Posts. Leere Tage sind Posting-Lücken.',
    suggestions: 'KI-generierte Vorschläge für neue Posts basierend auf deinem Content-Mix und Kalender.',
    recentPosts: 'Die zuletzt erstellten oder bearbeiteten Posts für schnellen Zugriff.',
    recyclingPanel: 'Zeigt ältere Posts, die gut performt haben und recycelt werden könnten.',
    seriesStatus: 'Überblick über laufende Story-Serien und deren Fortschritt.',
  },

  // ─── Settings ─────────────────────────────────────────────────────
  settings: {
    email: 'Die E-Mail-Adresse, mit der du dich anmeldest. Wird auch für Benachrichtigungen verwendet.',
    displayName: 'Der Name, der in der App angezeigt wird. Kann jederzeit geändert werden.',
    primaryColor: 'Die Hauptfarbe deiner Marke (Standard: TREFF-Blau #4C8BC2). Wird in Templates als Akzentfarbe verwendet.',
    secondaryColor: 'Die Zweitfarbe (Standard: TREFF-Gelb #FDD000). Für Highlights und CTAs.',
    accentColor: 'Zusätzliche Akzentfarbe für Details und Hover-Effekte in Templates.',
    geminiApiKey: 'Dein Google Gemini API-Schlüssel für KI-Textgenerierung und Bildgenerierung. Kostenlos bei Google AI Studio erhältlich.',
    openaiApiKey: 'Optionaler Fallback für Textgenerierung, falls Gemini nicht verfügbar ist.',
    unsplashApiKey: 'Für Zugriff auf lizenzfreie Stockfotos von Unsplash als Hintergrundbilder.',
    postsPerWeek: 'Dein Posting-Ziel pro Woche. Das Dashboard zeigt den Fortschritt und die Kalender-Lücken-Erkennung basiert darauf.',
    postsPerMonth: 'Monatliches Posting-Ziel. Wird für die langfristige Fortschrittsanalyse verwendet.',
    minEpisodeGap: 'Mindestabstand in Tagen zwischen Story-Arc-Episoden. Verhindert, dass Episoden zu dicht aufeinander geplant werden.',
    hashtagSets: 'Verwaltung von Hashtag-Gruppen nach Ländern und Kategorien. Seeded Sets sind vordefiniert, eigene können erstellt werden.',
  },

  // ─── Analytics ────────────────────────────────────────────────────
  analytics: {
    overview: 'Überblick über deine Posting-Aktivität der letzten 30 Tage mit Trends und Vergleichen.',
    goalTracking: 'Zeigt deinen Fortschritt gegenüber deinen wöchentlichen und monatlichen Posting-Zielen.',
    categoryDistribution: 'Verteilung deiner Posts nach Kategorien. Ein ausgewogener Mix ist empfohlen.',
    platformDistribution: 'Verteilung deiner Posts nach Plattformen (Instagram Feed, Story, TikTok).',
    countryDistribution: 'Zeigt, über welche Länder du am meisten postest. Alle 5 Länder sollten vertreten sein.',
    postingFrequency: 'Posting-Frequenz über die Zeit. Regelmäßigkeit ist wichtiger als Quantität.',
  },

  // ─── Video Tools ──────────────────────────────────────────────────
  video: {
    videoExport: 'Exportiere Videos in verschiedenen Formaten: 9:16 (Reel/TikTok), 1:1 (Feed), 4:5 (Portrait).',
    aspectRatio: 'Das Seitenverhältnis bestimmt den Zuschnitt: 9:16 für Hochformat (Stories/Reels), 1:1 für Quadrat (Feed), 4:5 für Portrait.',
    focusPoint: 'Bestimmt den Mittelpunkt des Zuschnitts. Verschiebe den Regler, um den Bildausschnitt anzupassen.',
    qualitySlider: 'Höhere Qualität (> 80%) für wichtige Posts, niedrigere für Entwürfe. Standard reicht für Social Media.',
    platformPreset: 'Plattform-Presets setzen automatisch das richtige Format und die maximale Videolänge.',
    batchExport: 'Exportiere ein Video gleichzeitig in mehreren Formaten. Spart Zeit bei Multi-Plattform-Posts.',
    videoTemplates: 'Vorgefertigte Video-Templates mit TREFF-Branding (Intro/Outro, Farbschema, Logo).',
    audioMixer: 'Mische Hintergrundmusik, Sprachaufnahmen und Sound-Effekte für deine Videos.',
    overlayEditor: 'Füge Text- und Bild-Overlays zu Videos hinzu (Titel, Untertitel, Logo, Sticker).',
    thumbnailGenerator: 'Erstelle ansprechende Thumbnails für Reels und TikToks mit Text und Branding.',
  },

  // ─── Story-Arcs & Recurring Formats ──────────────────────────────
  storyArcs: {
    arcOverview: 'Story-Arcs sind mehrteilige Serien (z.B. "Mein erstes Semester in den USA"). Jede Serie hat mehrere Episoden.',
    arcWizard: 'Der Wizard führt dich Schritt für Schritt durch die Erstellung eines neuen Story-Arcs.',
    episodeList: 'Alle Episoden des Story-Arcs mit Status (Entwurf, Geplant, Veröffentlicht).',
    progressBar: 'Zeigt den Fortschritt des Story-Arcs: wie viele Episoden bereits veröffentlicht sind.',
    arcStatus: 'Draft = In Planung, Active = Wird veröffentlicht, Completed = Alle Episoden gepostet.',
    recurringFormats: 'Wiederkehrende Formate wie "Motivation Monday" oder "Freitags-Fail" sorgen für Kontinuität und Wiedererkennungswert.',
    crossPostLink: 'Verknüpft Feed-Posts mit zugehörigen Stories, damit Follower weitergeleitet werden können.',
  },

  // ─── Templates ────────────────────────────────────────────────────
  templates: {
    templateGallery: 'Alle verfügbaren Templates, sortiert nach Kategorien. Wähle eines als Grundlage für deinen Post.',
    templatePreview: 'Vorschau des Templates mit Platzhalter-Daten. Das finale Design entsteht mit deinen eigenen Inhalten.',
    templateCategory: 'Templates sind nach Post-Kategorien gruppiert (Länder-Spotlight, Erfahrungsberichte, Infografiken, etc.).',
  },

  // ─── Assets ───────────────────────────────────────────────────────
  assets: {
    upload: 'Lade Bilder und Videos hoch (PNG, JPG, MP4, WebM). Maximale Dateigröße: 50 MB.',
    search: 'Suche in deinen Assets nach Dateinamen oder Tags.',
    assetTypes: 'Filtere nach Medientyp: Bilder, Videos, oder alle Dateien.',
  },

  // ─── Week Planner ─────────────────────────────────────────────────
  weekPlanner: {
    postsPerWeek: 'Wie viele Posts pro Woche geplant werden sollen. Die KI verteilt sie über die Woche.',
    recurringToggle: 'Aktiviere wiederkehrende Formate (z.B. Motivation Monday), damit die KI sie einplant.',
    seriesToggle: 'Aktiviere Story-Serien, damit die KI die nächsten Episoden automatisch einplant.',
    adoptPlan: 'Übernimmt alle Vorschläge als Entwürfe in den Kalender. Du kannst sie danach einzeln bearbeiten.',
    dragReorder: 'Verschiebe Vorschläge per Drag & Drop zwischen Tagen, um die Planung anzupassen.',
  },

  // ─── Students ─────────────────────────────────────────────────────
  students: {
    personalityPreset: 'Das Persönlichkeits-Preset steuert den KI-Schreibstil: Tonfall, Humor-Level, Emoji-Nutzung und Perspektive.',
    catchphrases: 'Wiederkehrende Phrasen oder Ausdrücke des Studenten, die die KI in Texte einbauen kann (max. 5).',
    studentLink: 'Verknüpfe Studenten mit Posts, damit ihre Erfahrungen authentisch erzählt werden.',
  },
}

export default tooltipTexts
