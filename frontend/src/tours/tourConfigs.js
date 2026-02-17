/**
 * Page-level tour configurations.
 *
 * Each key corresponds to a route name (matching Vue Router name) or a custom
 * page key.  The value is an object with:
 *   - title:       Human-readable tour title (shown in header)
 *   - steps[]:     Array of { target, title, description, position }
 *
 * target uses CSS selectors – preferably [data-tour="..."] attributes that we
 * add to the relevant page elements.
 *
 * position: 'top' | 'bottom' | 'left' | 'right'
 *
 * Updated 2026-02-17: Added tours for Home Dashboard (new widgets), Create Hub,
 * Quick Create, Library, Students Hub, Analytics (Funnel/Heatmap).
 * Updated Calendar tour for Day view. Updated WelcomeFlow references.
 */

const tourConfigs = {
  // ─── Home Dashboard (Neue 6-Widget-Architektur) ─────────────
  dashboard: {
    title: 'Dashboard Tour – Deine Content-Zentrale',
    steps: [
      {
        target: '[data-tour="dashboard-stats"]',
        title: 'Willkommen im Dashboard!',
        description:
          'Das Dashboard ist deine Zentrale für alles rund um Social-Media-Content. Von hier aus startest du alle Workflows: Posts erstellen, planen, analysieren und optimieren. Die Quick-Stats oben zeigen dir auf einen Blick, wie viele Posts du diese Woche erstellt hast, wie viele geplant und wie viele noch als Entwurf bereitliegen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="quick-actions"]',
        title: 'Quick-Actions: Deine Shortcuts',
        description:
          'Mit diesen Buttons startest du direkt die wichtigsten Aktionen: "Post erstellen" führt zum Create Hub mit den 4 Erstellungsmodi, "Kalender" öffnet die volle Kalender-Ansicht zum Planen, und "Templates" bringt dich direkt zur Vorlagen-Bibliothek. Das Dashboard ist dein Startpunkt für jeden Workflow!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-content-queue"]',
        title: 'Content Queue: Was steht als Nächstes an?',
        description:
          'Die Content Queue zeigt dir die nächsten geplanten Posts in chronologischer Reihenfolge. So siehst du sofort, welcher Content als Nächstes veröffentlicht werden soll — mit Plattform-Icon, Titel, Kategorie und geplantem Datum. Ideal für einen schnellen Morgen-Check!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-student-inbox"]',
        title: 'Student Inbox: Frischer Content von Schülern',
        description:
          'Die Student Inbox sammelt neue Medien und Nachrichten von deinen Austausch-Schülern. Fotos, Videos und Updates landen hier automatisch und warten darauf, zu Posts verarbeitet zu werden. Klicke auf einen Eintrag, um ihn direkt in einen Post umzuwandeln!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-performance-pulse"]',
        title: 'Performance Pulse: Bist du auf Kurs?',
        description:
          'Der Performance Pulse zeigt dir dein Posting-Tempo der letzten Wochen als Mini-Sparkline. Der Trend-Indikator (steigend/stabil/fallend) verrät dir auf einen Blick, ob du dein Wochen-Ziel erreichst. Grün = on track, Rot = du musst nachlegen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-active-campaigns"]',
        title: 'Aktive Kampagnen',
        description:
          'Hier siehst du laufende Content-Kampagnen mit Fortschrittsbalken. Jede Kampagne zeigt, wie viele Posts bereits erstellt und geplant wurden — so behältst du den Überblick über mehrteilige Aktionen wie saisonale Kampagnen oder Bewerbungszeitraum-Pushes.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-pipeline"]',
        title: 'Pipeline: Content-Verarbeitungs-Funnel',
        description:
          'Die Pipeline zeigt den Verarbeitungsstatus deiner Medien als Funnel-Visualisierung: Wie viele Items warten auf Analyse, wie viele sind analysiert und bereit zur Verarbeitung, und wie viele wurden bereits zu Posts verarbeitet? So erkennst du Engpässe in deinem Content-Workflow.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-calendar"]',
        title: 'Mini-Kalender: Nächste 7 Tage',
        description:
          'Der Mini-Kalender zeigt die kommende Woche mit farbigen Punkten für geplante Posts. So erkennst du auf einen Blick, an welchen Tagen Content ansteht — und wo noch Lücken sind. Für die volle Kalender-Ansicht klicke auf "Kalender".',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-suggestions-widget"]',
        title: 'KI Content-Vorschläge',
        description:
          'Die KI analysiert deinen bisherigen Content und schlägt passende neue Themen vor — basierend auf Saison, Länder-Rotation, Kategorie-Balance und Content-Lücken. Klicke "Annehmen" um einen Vorschlag direkt als Post zu erstellen.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-recent-posts"]',
        title: 'Letzte Posts',
        description:
          'Hier siehst du deine neuesten Posts als Thumbnail-Grid mit Plattform-Icon, Titel und Status. Klicke auf einen Post, um ihn direkt zu bearbeiten. "Alle anzeigen" führt zum vollständigen Post-Archiv in der Bibliothek.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-series-status"]',
        title: 'Serien-Status',
        description:
          'Verfolge den Fortschritt deiner Story-Arcs (mehrteilige Content-Serien). Du siehst den Status jeder Serie, die aktuelle Episode und einen Fortschrittsbalken. So verpasst du keine Fortsetzung!',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-recycling"]',
        title: 'Content-Recycling',
        description:
          'Posts älter als 90 Tage erscheinen hier als Recycling-Vorschläge. Statt neuen Content zu erstellen, kannst du erfolgreiche alte Posts auffrischen und wiederverwenden. Evergreen-Posts eignen sich besonders gut dafür.',
        position: 'top',
      },
    ],
  },

  // ─── Create Hub (Mode-Selector) ────────────────────────────
  'create-hub': {
    title: 'Create Hub Tour – Content erstellen',
    steps: [
      {
        target: '[data-tour="create-hub"]',
        title: 'Willkommen im Create Hub!',
        description:
          'Der Create Hub ist dein Startpunkt für die Content-Erstellung. Hier wählst du, WIE du deinen nächsten Post erstellen möchtest — von der schnellen 2-Klick-Variante bis zur strategischen Multi-Post-Kampagne. Jeder Modus ist für einen anderen Anwendungsfall optimiert.',
        position: 'bottom',
      },
      {
        target: '[data-testid="create-card-blue"]',
        title: 'Quick Create: Schnell & Einfach (1-2 Min)',
        description:
          'Der klassische Schritt-für-Schritt-Editor: Kategorie wählen, Template aussuchen, KI-Texte generieren, anpassen und exportieren — alles in einem 9-Schritt-Wizard. Ideal für einzelne Posts, die du schnell erstellen möchtest. Der schnellste Weg vom Thema zum fertigen Post!',
        position: 'right',
      },
      {
        target: '[data-testid="create-card-purple"]',
        title: 'Smart Create: Upload-First (3-5 Min)',
        description:
          'Lade ein Foto hoch und lass die KI den Rest erledigen! Smart Create analysiert dein Bild automatisch, erkennt das Thema, schlägt passende Captions, Hashtags und Templates vor. Perfekt, wenn du ein tolles Schüler-Foto hast und daraus sofort einen Post machen willst.',
        position: 'left',
      },
      {
        target: '[data-testid="create-card-red"]',
        title: 'Video Create: Plattform-gerechte Videos (5 Min)',
        description:
          'Die unified Video-Pipeline: Lade ein Video hoch, füge automatisch TREFF Intro/Outro-Branding hinzu, wähle Lower Thirds und Musik aus, und exportiere in allen Formaten (9:16 für Reels/TikTok, 1:1 für Feed). Ein Schritt für alles!',
        position: 'right',
      },
      {
        target: '[data-testid="create-card-amber"]',
        title: 'Campaign Create: Multi-Post-Planung (10-15 Min)',
        description:
          'Plane eine mehrteilige Content-Kampagne: Definiere Ziel, Zeitraum und Plattformen, und lass die KI einen kompletten Post-Plan mit Timeline generieren. Ideal für saisonale Kampagnen, Bewerbungszeitraum-Pushes oder themenbezogene Content-Serien.',
        position: 'left',
      },
      {
        target: '[data-testid="recent-drafts-section"]',
        title: 'Letzte Entwürfe',
        description:
          'Unterhalb der Modi-Karten findest du deine 3 neuesten Entwürfe zum schnellen Weiterbearbeiten. Klicke auf einen Entwurf, um direkt in den Editor zu springen. So verlierst du nie den Faden bei angefangenen Posts!',
        position: 'top',
      },
    ],
  },

  // ─── Quick Create (Post-Wizard) ────────────────────────────
  'create-post': {
    title: 'Post-Wizard Tour',
    steps: [
      {
        target: '[data-tour="cp-content"]',
        title: 'Willkommen im Post-Wizard!',
        description:
          'Der Post-Ersteller führt dich in 9 Schritten durch den kompletten Prozess: Von der Kategorie-Auswahl über KI-Textgenerierung bis zum fertigen Export. Jeder Schritt baut auf dem vorherigen auf — so entsteht in Minuten ein professioneller Social-Media-Post mit konsistentem TREFF-Branding.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-1"]',
        title: 'Schritt 1: Kategorie wählen',
        description:
          'Wähle die Art deines Posts: Länder-Spotlight, Erfahrungsberichte, Tipps & Tricks, Fristen & CTA oder FAQ. Die Kategorie bestimmt, welche Templates und KI-Texte vorgeschlagen werden — so passt alles zusammen und dein Content-Mix bleibt ausgewogen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-2"]',
        title: 'Schritt 2: Template wählen',
        description:
          'Templates sind vorgefertigte Design-Vorlagen mit TREFF-Branding. Jedes Template hat ein festes Layout und bestimmt, wie viele Slides dein Post hat. Die richtige Vorlage spart Design-Arbeit und schafft Wiedererkennungswert.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-5"]',
        title: 'KI-Textgenerierung (Gemini AI)',
        description:
          'Hier generiert Google Gemini AI automatisch alle Texte: Headlines, Body-Texte, Captions und Hashtags — basierend auf Kategorie, Land und Thema. Du sparst Stunden an Copywriting und erhältst sofort professionelle Texte im richtigen Stil.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-7"]',
        title: 'Slide-Editor (Drag & Drop)',
        description:
          'Der Slide-Editor ist das Herzstück: Ordne Slides per Drag & Drop, bearbeite Texte direkt und füge neue Slides hinzu. Die Reihenfolge bestimmt die Story — der erste Slide muss fesseln (Hook), der letzte soll zum Handeln auffordern (CTA).',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-6"]',
        title: 'Captions & Hashtags',
        description:
          'Bearbeite Instagram- und TikTok-Captions getrennt voneinander (jede Plattform hat eigene Regeln). Gute Captions und Hashtags steigern die Reichweite enorm — nutze den Sparkle-Button für KI-optimierte Vorschläge.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-8"]',
        title: 'CTA: Call-to-Action',
        description:
          'Ein Call-to-Action fordert zum Handeln auf — z.B. "Jetzt bewerben!" oder "Link in Bio". Ohne CTA scrollen Nutzer weiter, MIT CTA steigt die Interaktionsrate! Die CTA-Bibliothek bietet 35 vorgefertigte CTAs in 4 Kategorien.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-3"]',
        title: 'Multi-Plattform: Instagram vs TikTok',
        description:
          'Wähle eine oder mehrere Plattformen gleichzeitig. Captions, Hashtags und Bild-Formate werden automatisch für jede Plattform angepasst — beim Export erhältst du separate, optimierte Dateien.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-tour-btn"]',
        title: 'Vorschau, Export & Speichern',
        description:
          'In Schritt 6 siehst du eine Live-Vorschau, in Schritt 8 wählst du ein Hintergrundbild, und in Schritt 9 exportierst du als PNG/ZIP, speicherst als Entwurf oder planst im Kalender. Tipp: Du kannst diese Tour jederzeit über diesen Button erneut starten!',
        position: 'bottom',
      },
    ],
  },

  // ─── Smart Create (Upload-First-Flow) ──────────────────────
  'smart-create': {
    title: 'Smart Create Tour – Upload-First',
    steps: [
      {
        target: '[data-testid="smart-create-view"]',
        title: 'Willkommen bei Smart Create!',
        description:
          'Smart Create ist der schnellste Weg von einem Foto zum fertigen Post: Lade ein Bild hoch, die KI analysiert es automatisch und generiert passende Vorschläge für Caption, Hashtags und Post-Typ. Du bearbeitest nur noch die Details — fertig!',
        position: 'bottom',
      },
      {
        target: '[data-testid="media-upload-zone"]',
        title: 'Schritt 1: Foto hochladen',
        description:
          'Ziehe ein Bild per Drag & Drop hierher oder klicke zum Auswählen. Unterstützte Formate: JPG, PNG, WebP (bis 20 MB). Die KI erkennt automatisch Inhalt, Stimmung und Kontext des Bildes — je besser das Foto, desto präziser die Vorschläge!',
        position: 'bottom',
      },
      {
        target: '[data-testid="smart-create-view"]',
        title: 'Schritt 2: KI-Analyse',
        description:
          'Nach dem Upload analysiert die KI dein Bild: Was ist zu sehen? Welches Land könnte es sein? Welcher Ton passt? Das Ergebnis: Post-Typ-Vorschläge, eine Caption, passende Hashtags und ein empfohlenes Template. Alles in Sekunden!',
        position: 'bottom',
      },
      {
        target: '[data-testid="smart-create-view"]',
        title: 'Schritt 3: Überprüfen & Anpassen',
        description:
          'Überprüfe und bearbeite die KI-Vorschläge: Wähle den passenden Post-Typ, passe die Caption an, entferne oder füge Hashtags hinzu. Wenn du zufrieden bist, speichere den Post als Entwurf oder plane ihn direkt im Kalender.',
        position: 'bottom',
      },
    ],
  },

  // ─── Calendar (Erweitert mit Day View) ─────────────────────
  calendar: {
    title: 'Kalender Tour – Content-Planung',
    steps: [
      {
        target: '[data-tour="cal-toolbar"]',
        title: 'Willkommen im Content-Kalender!',
        description:
          'Der Kalender ist dein zentrales Planungstool: Hier siehst du alle geplanten und ungeplanten Posts auf einen Blick, erkennst Content-Lücken und behältst den Überblick über Fristen und Serien. Lass uns die wichtigsten Funktionen kennenlernen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-views"]',
        title: 'Ansichten: Monat, Woche & Tag',
        description:
          'Der Kalender bietet drei Hauptansichten: "Monat" zeigt den klassischen Monatsüberblick mit allen Features. "Woche" zeigt eine detaillierte Wochenansicht mit Zeitslots von 06:00 bis 23:00 Uhr. "Tag" zeigt eine Tagesansicht mit Stunden-Timeline, Quick-Edit-Modal und Plattform-Farbcodierung. Wechsle je nach Planungsbedarf!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-grid"]',
        title: 'Drag & Drop: Posts per Maus planen',
        description:
          'Plane deine Posts einfach per Drag & Drop: Ziehe einen Entwurf aus der linken Seitenleiste auf ein Datum. Es öffnet sich ein Dialog zur Uhrzeitauswahl. Bereits geplante Posts kannst du durch Ziehen auf ein anderes Datum verschieben. In der Tagesansicht kannst du sogar auf Zeitslots klicken!',
        position: 'top',
      },
      {
        target: '[data-tour="cal-sidebar"]',
        title: 'Entwürfe-Sidebar: Ungeplante Posts',
        description:
          'In der linken Seitenleiste findest du alle Posts ohne Datum. Ziehe eine Karte auf ein Datum im Kalender, um den Post zu planen. Die Sidebar lässt sich einklappen, um mehr Platz für den Kalender zu schaffen.',
        position: 'right',
      },
      {
        target: '[data-tour="cal-gaps"]',
        title: 'Lücken-Erkennung',
        description:
          'Aktiviere die Lücken-Erkennung, um Tage ohne geplanten Content orange hervorzuheben. Regelmäßiges Posten ist entscheidend für den Instagram-Algorithmus — jede Lücke kostet Reichweite! Der Badge zeigt die Anzahl der Lücken-Tage.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-seasonal"]',
        title: 'Saisonale Marker',
        description:
          'Aktiviere saisonale Marker, um wichtige Termine direkt im Kalender zu sehen: Bewerbungsfristen, Abflugzeiten und Schuljahresstart in den Zielländern. Content rund um diese Termine erzeugt hohe Relevanz!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-mix"]',
        title: 'Content-Mix: Ausgewogene Kategorien',
        description:
          'Das Content-Mix-Panel analysiert die Verteilung deiner Posts nach Kategorie, Plattform und Land. Ein ausgewogener Mix hält deinen Feed abwechslungsreich. Keine Kategorie sollte mehr als 40% ausmachen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-arcs"]',
        title: 'Story-Arc Timeline',
        description:
          'Die Story-Arc-Timeline zeigt deine mehrteiligen Content-Serien als farbige Balken. So erkennst du auf einen Blick, ob alle Episoden terminiert sind und die Reihenfolge stimmt. Klicke auf einen Punkt, um zum Post-Editor zu springen.',
        position: 'bottom',
      },
    ],
  },

  // ─── Library (Unified Hub) ─────────────────────────────────
  library: {
    title: 'Bibliothek Tour – Alles an einem Ort',
    steps: [
      {
        target: '[data-tour="library-hub"]',
        title: 'Willkommen in der Bibliothek!',
        description:
          'Die Bibliothek vereint Assets, Templates und Posts an einem Ort. Über die drei Tabs oben wechselst du zwischen deinen Medien (Fotos, Videos), Design-Vorlagen und dem Post-Archiv. Die einheitliche Suche funktioniert tab-übergreifend!',
        position: 'bottom',
      },
      {
        target: '[data-testid="library-search"]',
        title: 'Einheitliche Suche',
        description:
          'Die Suchleiste passt sich automatisch an den aktiven Tab an: Im Assets-Tab suchst du nach Dateinamen und Tags, im Templates-Tab nach Vorlagennamen und Kategorien, im Posts-Tab nach Titeln und Status. Eine Suche — alle Inhalte!',
        position: 'bottom',
      },
      {
        target: '[data-testid="library-tab-assets"]',
        title: 'Tab 1: Assets – Deine Medien',
        description:
          'Im Assets-Tab verwaltest du alle hochgeladenen Bilder, Videos und Audio-Dateien. Lade neue Dateien per Drag & Drop hoch, organisiere sie mit Tags und Kategorien, und nutze den integrierten Crop-Tool und Video-Trimmer.',
        position: 'bottom',
      },
      {
        target: '[data-testid="library-tab-templates"]',
        title: 'Tab 2: Templates – Deine Vorlagen',
        description:
          'Im Templates-Tab findest du alle Design-Vorlagen für deine Posts. Filtere nach Kategorie und Plattform, öffne den Live-Preview-Editor zum Anpassen, oder erstelle komplett eigene Templates. Drei Sub-Tabs für Übersicht, Galerie und Editor.',
        position: 'bottom',
      },
      {
        target: '[data-testid="library-tab-history"]',
        title: 'Tab 3: Posts – Dein Archiv',
        description:
          'Im Posts-Tab findest du ALLE erstellten Posts — Entwürfe, geplante und veröffentlichte. Suche, filtere und sortiere dein Archiv, exportiere Posts als ZIP, dupliziere erfolgreiche Posts oder recycele alte Inhalte. Dein Content-Gedächtnis!',
        position: 'bottom',
      },
    ],
  },

  // ─── Students Hub ──────────────────────────────────────────
  students: {
    title: 'Schüler Tour – Deine Schüler-Datenbank',
    steps: [
      {
        target: '[data-tour="students-header"]',
        title: 'Warum eine Schüler-Datenbank?',
        description:
          'Echte Geschichten von echten Austausch-Schülern sind der beste Social-Media-Content! Hier sammelst du alle Infos über deine Teilnehmer — Name, Land, Schule, Bio und Fun-Facts. Diese Daten fließen automatisch in die KI-Textgenerierung ein.',
        position: 'bottom',
      },
      {
        target: '[data-tour="students-add-btn"]',
        title: 'Schüler anlegen',
        description:
          'Klicke auf "Student hinzufügen" für ein neues Profil. Pflichtfelder: Name und Land. Optional aber empfohlen: Stadt, Schule, Gastfamilie, Bio und Fun-Facts. Je mehr Details, desto authentischer und vielfältiger die KI-generierten Texte!',
        position: 'bottom',
      },
      {
        target: '[data-tour="students-personality"]',
        title: 'Persönlichkeits-Presets',
        description:
          'Jeder Schüler bekommt ein Persönlichkeits-Preset (witzig, emotional, motivierend...) und einen Humor-Level. Das steuert die KI-Textgenerierung — so klingt jeder Schüler in Posts anders und authentisch!',
        position: 'top',
      },
      {
        target: '[data-tour="students-list"]',
        title: 'Schüler-Karten & Pipeline',
        description:
          'Die Schüler-Karten zeigen auf einen Blick: Name, Land mit Flagge, Schule und einen Pipeline-Indikator, der anzeigt, wie viele Posts bereits für diesen Schüler erstellt wurden. Klicke auf eine Karte für das Detail-Profil — dort kannst du auch direkt einen Post für diesen Schüler starten!',
        position: 'top',
      },
      {
        target: '[data-tour="students-story-arc-hint"]',
        title: 'Story-Arcs: Schüler als Hauptfiguren',
        description:
          'Schüler sind die Hauptfiguren deiner Content-Serien! Ein Story-Arc erzählt die Geschichte eines Schülers über mehrere Posts — z.B. "Lisas Semester in Neuseeland". Lege zuerst Profile an, dann erstelle unter "Story-Arcs" mehrteilige Serien.',
        position: 'bottom',
      },
    ],
  },

  // ─── Analytics (Erweitert mit Funnel, Heatmap, Pillar-Balance) ──
  analytics: {
    title: 'Analytics Tour – Datenbasierte Content-Optimierung',
    steps: [
      {
        target: '[data-tour="analytics-header"]',
        title: 'Willkommen im Analytics-Dashboard!',
        description:
          'Das Analytics-Dashboard ist dein Kompass für datenbasierte Content-Optimierung. Hier siehst du auf einen Blick, wie aktiv du postest, ob du deine Ziele erreichst und wie ausgewogen dein Content-Mix ist. Ohne Daten postest du im Blindflug — mit Analytics erkennst du Muster und Chancen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-strategy"]',
        title: 'Strategie-Gesundheit: IST vs. SOLL',
        description:
          'Das Strategy Health Panel vergleicht deine tatsächliche Content-Verteilung mit deinen Zielwerten — wie ein Gesundheits-Check für deine Content-Strategie! Du siehst sofort, welche Content-Pillar (Informieren, Unterhalten, Inspirieren, Konvertieren) über- oder unterrepräsentiert sind.',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-goals"]',
        title: 'Zielverfolgung: Dein Fortschritt',
        description:
          'Die Fortschrittsbalken zeigen, wie nah du deinen Posting-Zielen bist — getrennt nach Woche und Monat. Grün = Ziel erreicht! Die Zielwerte konfigurierst du unter Einstellungen > Posting-Ziele. Der Wochenplaner hilft, Ziele systematisch zu erreichen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-frequency"]',
        title: 'Posting-Frequenz',
        description:
          'Das Liniendiagramm zeigt, wie oft du in einem Zeitraum gepostet hast. Wechsle zwischen 7 Tagen, 30 Tagen, Quartal und Jahr. Regelmäßigkeit ist der wichtigste Faktor für den Instagram-Algorithmus — Lücken kosten Reichweite!',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-heatmap"]',
        title: 'Aktivitäts-Heatmap',
        description:
          'Die Heatmap zeigt deine Posting-Aktivität im GitHub-Stil: Jedes Kästchen steht für einen Tag, die Farbe zeigt die Anzahl der Posts. So erkennst du sofort Phasen hoher und niedriger Aktivität über längere Zeiträume — und kannst Muster erkennen.',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-categories"]',
        title: 'Kategorieverteilung: Content-Mix',
        description:
          'Das Donut-Diagramm zeigt die Verteilung nach Kategorie: Länder-Spotlight, Erfahrungsberichte, Tipps & Tricks, FAQ und mehr. Ziel: Keine Kategorie über 40%. Ein ausgewogener Mix hält Follower interessiert und spricht verschiedene Zielgruppen an.',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-platforms"]',
        title: 'Plattformverteilung: Instagram vs. TikTok',
        description:
          'Die Donut-Charts zeigen, wie sich deine Posts auf Instagram Feed, Story und TikTok verteilen — plus eine Aufschlüsselung nach Format (Bild, Video, Carousel). So stellst du sicher, dass du beide Zielgruppen bedienst: Teenager auf TikTok UND Eltern auf Instagram.',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-reports"]',
        title: 'Report Generator',
        description:
          'Generiere ausführliche Reports für bestimmte Zeiträume — ideal für Team-Meetings, Quartals-Reviews oder Kundenberichte. Reports enthalten alle Charts, Statistiken und Empfehlungen als übersichtliche Zusammenfassung.',
        position: 'top',
      },
    ],
  },

  // ─── Templates ───────────────────────────────────────────
  templates: {
    title: 'Vorlagen Tour',
    steps: [
      {
        target: '[data-tour="tpl-header"]',
        title: 'Was sind Templates?',
        description:
          'Templates sind vorgefertigte Design-Vorlagen für deine Social-Media-Posts. Sie sorgen für ein konsistentes TREFF-Branding und sparen dir Zeit bei der Erstellung — jeder Post sieht professionell aus, ohne dass du jedes Mal bei null anfangen musst.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-filters"]',
        title: 'Template-Galerie filtern',
        description:
          'Nutze die Filter, um Vorlagen nach Kategorie (z.B. Länder-Spotlight, FAQ, Erfahrungsberichte) oder Plattform-Format (Instagram Feed, Story, TikTok) einzugrenzen. Die Galerie zeigt dir die Anzahl der Treffer und gruppiert Templates nach Kategorie.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-grid"]',
        title: 'Live-Preview-Editor',
        description:
          'Klicke auf ein Template, um den Live-Preview-Editor zu öffnen. Dort siehst du in Echtzeit, wie dein Post mit dem gewählten Template aussehen wird. Du kannst Texte, Farben und Schriftarten direkt anpassen — jede Änderung wird sofort in der Vorschau sichtbar.',
        position: 'top',
      },
      {
        target: '[data-tour="tpl-create-btn"]',
        title: 'Farben, Fonts & Brand-Identität',
        description:
          'Im Anpassungs-Panel des Editors kannst du Primär-, Sekundär- und Hintergrundfarben ändern, Überschrift- und Fließtext-Schriftarten wählen und alle Texte bearbeiten. Erstelle mit dem "+"-Button auch komplett eigene Templates mit eigenem HTML/CSS-Code.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-video-hint"]',
        title: 'Video-Templates',
        description:
          'Neben Post-Templates gibt es auch spezielle Video-Templates für Reels und TikToks. Diese findest du auf einer separaten Seite unter "Video-Branding" in der Seitenleiste — dort kannst du Intros, Outros, Lower Thirds und Overlay-Vorlagen verwalten.',
        position: 'top',
      },
    ],
  },

  // ─── Assets ──────────────────────────────────────────────
  assets: {
    title: 'Assets Tour – Deine Medienverwaltung',
    steps: [
      {
        target: '[data-tour="assets-header"]',
        title: 'Willkommen in der Asset-Bibliothek!',
        description:
          'Die Asset-Bibliothek ist deine zentrale Medienverwaltung. Hier lagerst du alle Bilder, Videos und Audio-Dateien, die du für deine Social-Media-Posts brauchst. Von hier aus kannst du Dateien hochladen, organisieren, bearbeiten und in Posts einbinden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-upload"]',
        title: 'Dateien hochladen – Drag & Drop',
        description:
          'Ziehe Bilder, Videos oder Audio-Dateien einfach per Drag & Drop in diesen Bereich — oder klicke zum Auswählen. Unterstützte Formate: JPG, PNG, WebP (bis 20 MB), MP4, MOV, WebM (bis 500 MB) und MP3, WAV, AAC (bis 50 MB). Unter dem Upload-Bereich kannst du direkt Kategorie, Land und Tags vergeben.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-grid"]',
        title: 'Crop-Tool & Video-Trimmer',
        description:
          'Bewege die Maus über ein Asset, um die Bearbeitungs-Buttons zu sehen: Bei Bildern erscheint ein Crop-Button zum Zuschneiden (z.B. auf Instagram-Formate 1:1, 4:5, 9:16). Bei Videos gibt es einen Trim-Button zum Kürzen und einen Audio-Mix-Button. So bereitest du Medien direkt hier für Social Media vor — ohne externe Tools.',
        position: 'top',
      },
      {
        target: '[data-tour="assets-filters"]',
        title: 'Kategorisierung, Tagging & Suche',
        description:
          'Nutze die Filter, um deine Assets schnell zu finden: Suche nach Dateiname oder Tags, filtere nach Kategorie (Logo, Hintergrund, Foto, Icon, Länderbild, Video), nach Land (USA, Kanada, Australien, Neuseeland, Irland) oder nach Dateityp (JPG, PNG, WebP, Video, Audio). Aktive Filter werden als Chips angezeigt und lassen sich einzeln entfernen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-tabs"]',
        title: 'Stock-Foto-Integration (Unsplash & Pexels)',
        description:
          'Klicke auf den Tab "Stock Fotos", um kostenlose Stock-Fotos von Unsplash oder Pexels zu durchsuchen. Gib einen englischen Suchbegriff ein (z.B. "highschool campus", "australia landscape") und importiere passende Fotos direkt in deine Bibliothek. So findest du schnell professionelle Bilder für deine Posts.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-usage-hint"]',
        title: 'Assets in Posts & Videos verwenden',
        description:
          'Deine Assets werden automatisch im Post-Editor (Schritt 5: Bild) zur Auswahl angeboten. Auch im Video-Composer, Video-Export und Thumbnail-Generator kannst du auf deine Bibliothek zugreifen. Tipp: Tagge deine Assets mit dem passenden Land und der Kategorie — so werden sie beim Erstellen eines Posts automatisch vorgefiltert!',
        position: 'top',
      },
    ],
  },

  // ─── History ─────────────────────────────────────────────
  history: {
    title: 'Post-Archiv Tour – Dein Content-Gedächtnis',
    steps: [
      {
        target: '[data-tour="history-header"]',
        title: 'Willkommen im Post-Archiv!',
        description:
          'Das Post-Archiv ist dein zentrales Content-Gedächtnis. Hier findest du ALLE jemals erstellten Posts — egal ob Entwurf, geplant oder bereits veröffentlicht. WARUM? Ein gut gepflegtes Archiv ist Gold wert: Du kannst erfolgreiche Posts wiederverwenden, saisonale Inhalte recyclen und jederzeit nachvollziehen, was du wann gepostet hast. So baust du langfristig eine konsistente Content-Strategie für TREFF Sprachreisen auf.',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-filters"]',
        title: 'Suche, Filter & Sortierung',
        description:
          'Mit der Suchleiste findest du Posts blitzschnell nach Titel oder Stichwort. Die Filter-Dropdowns grenzen nach Kategorie (z.B. Länder-Spotlight, FAQ), Plattform (Instagram Feed, Story, TikTok), Status (Entwurf, Geplant, Veröffentlicht), Land und Zeitraum ein. Die Sortierung lässt sich nach Erstelldatum, Aktualisierung, Titel oder geplantem Datum ordnen — aufsteigend oder absteigend. TIPP: Kombiniere Filter, um z.B. alle USA-Posts der letzten 30 Tage zu finden!',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-batch"]',
        title: 'Batch-Auswahl & ZIP-Export',
        description:
          'Klicke auf "Auswählen", um in den Mehrfachauswahl-Modus zu wechseln. Wähle einzelne Posts per Checkbox oder nutze "Alle auswählen" für die komplette Seite. Mit "Batch-Export" erhältst du alle ausgewählten Posts als ZIP-Datei — jeder Post wird als PNG-Bild gerendert, perfekt zum Versenden an Kunden oder für Backup-Zwecke. TIPP: Exportiere z.B. alle Posts einer Woche, um sie deinem Team zur Freigabe zu schicken.',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-actions"]',
        title: 'Post-Aktionen: Bearbeiten, Duplizieren & Löschen',
        description:
          'Jeder Post bietet dir mehrere Aktionen: Mit dem Stift-Icon (Bearbeiten) öffnest du den Post im Editor und kannst Text, Bilder oder Design ändern. Das Kopier-Icon (Duplizieren) erstellt eine exakte Kopie als neuen Entwurf — ideal für ähnliche Posts mit kleinen Anpassungen. Das Kalender-Icon ermöglicht direktes (Um-)Planen. Und das Papierkorb-Icon (Löschen) entfernt den Post nach Bestätigung endgültig.',
        position: 'top',
      },
      {
        target: '[data-tour="history-recycling"]',
        title: 'Content-Recycling: Alte Posts neu nutzen!',
        description:
          'Das Archiv ist dein Schlüssel zum Content-Recycling! Erfolgreiche Posts von letztem Jahr können mit kleinen Anpassungen erneut veröffentlicht werden. STRATEGIE: (1) Filtere nach "Veröffentlicht" und sortiere nach Engagement. (2) Dupliziere Top-Posts und aktualisiere Zahlen, Daten oder Bilder. (3) Plane den recycelten Post im Kalender für eine ruhige Woche. So sparst du Zeit und nutzt bewährte Inhalte optimal. Gehe zum Wochenplaner, um recycelte Posts strategisch einzuplanen!',
        position: 'top',
      },
    ],
  },

  // ─── Settings ────────────────────────────────────────────
  settings: {
    title: 'Einstellungen Tour – Dein Kontrollzentrum',
    steps: [
      {
        target: '[data-tour="settings-sections"]',
        title: 'Willkommen in den Einstellungen!',
        description:
          'Die Einstellungen sind dein Kontrollzentrum: Hier konfigurierst du alles, was die App an dein Unternehmen und deine Arbeitsweise anpasst — von Account-Daten über Brand-Farben und API-Schlüssel bis hin zu Posting-Zielen, Content-Mix und Hashtag-Strategien. Jede Änderung hier wirkt sich direkt auf Posts, Templates, KI-Generierung und Analytics aus. Lass uns die einzelnen Bereiche kennenlernen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-brand"]',
        title: 'Brand-Farben: Dein visuelles Branding',
        description:
          'Die drei Brand-Farben (Primär, Sekundär, Akzent) definieren das visuelle Erscheinungsbild deiner gesamten Content-Produktion. WARUM? Diese Farben fließen automatisch in alle Templates ein — Überschriften, Buttons, Hintergründe und Akzente nutzen deine Markenfarben für konsistentes Branding. Die Vorschau unten zeigt dir sofort, wie die Farben zusammenwirken. Standard: TREFF-Blau (#3B7AB1), TREFF-Gelb (#FDD000) und Weiß (#FFFFFF).',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-api-keys"]',
        title: 'API-Schlüssel: KI & Stock-Fotos freischalten',
        description:
          'Hier hinterlegst du die Schlüssel für externe Dienste: Der Google Gemini API-Schlüssel aktiviert die KI-Textgenerierung (Captions, Hashtags, Hooks) und KI-Bildgenerierung — ohne ihn funktioniert kein KI-Feature! Der OpenAI-Schlüssel ist ein optionaler Fallback für Textgenerierung. Der Unsplash-Schlüssel ermöglicht die Suche nach kostenlosen Stock-Fotos direkt in der Asset-Bibliothek. Alle Schlüssel werden verschlüsselt gespeichert und nie im Klartext angezeigt.',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-posting-goals"]',
        title: 'Posting-Ziele: Deine Content-Targets',
        description:
          'Hier definierst du deine Posting-Ziele: Posts pro Woche und Monat, bevorzugte Posting-Zeit und Plattform, sowie den Mindestabstand zwischen Story-Arc-Episoden. WARUM? Diese Ziele werden im Analytics-Dashboard als Fortschrittsbalken angezeigt — so siehst du jederzeit, ob du auf Kurs bist. Der KI-Wochenplaner nutzt die bevorzugte Plattform und Zeit als Basis für Vorschläge. Empfehlung: Starte mit 3-4 Posts pro Woche und steigere dich schrittweise.',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-content-mix"]',
        title: 'Content-Mix-Ziele: Ausgewogene Verteilung',
        description:
          'Der Ziel-Content-Mix bestimmt, wie sich deine Posts auf Plattformen und Länder verteilen sollen. Die Plattform-Verteilung (Instagram Feed, Story, TikTok) stellt sicher, dass du alle Kanäle bedienst. Die Länder-Verteilung (USA, Kanada, Australien, Neuseeland, Irland) sorgt dafür, dass kein Zielland vernachlässigt wird. WARUM? Das Analytics-Dashboard vergleicht deine tatsächliche Verteilung mit diesen Zielen und zeigt Abweichungen — so erkennst du, welche Länder oder Plattformen mehr Aufmerksamkeit brauchen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-hashtags"]',
        title: 'Hashtag-Manager: Deine Hashtag-Strategie',
        description:
          'Der Hashtag-Manager verwaltet vordefinierte Hashtag-Sets für verschiedene Länder und Kategorien. 17 Standard-Sets (TREFF Brand, Engagement Booster, länderspezifische Sets) sind bereits angelegt — du kannst eigene Sets erstellen, bearbeiten und filtern. WARUM? Im Post-Editor werden passende Hashtags automatisch vorgeschlagen, basierend auf Kategorie und Land des Posts. So nutzt du immer die richtigen Hashtags für maximale Reichweite, ohne jedes Mal neu zu recherchieren. Standard-Sets sind schützenswert und können nicht versehentlich gelöscht werden.',
        position: 'top',
      },
    ],
  },

  // ─── Story Arcs ──────────────────────────────────────────
  'story-arcs': {
    title: 'Story-Arcs Tour – Serien-Content',
    steps: [
      {
        target: '[data-tour="arcs-header"]',
        title: 'Was sind Story-Arcs?',
        description:
          'Story-Arcs sind mehrteilige Content-Serien, z.B. "Lenas Abenteuer in Kanada" als 8-teilige Serie. Serien-Content ist der stärkste Hebel für Follower-Bindung: Wer Teil 1 sieht, will Teil 2 sehen — und kommt aktiv zurück!',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-stats"]',
        title: 'Story-Arc-Übersicht',
        description:
          'Diese Statistik-Karten zeigen dir den Stand aller Serien: Wie viele sind aktiv, pausiert, als Entwurf oder abgeschlossen. So behältst du den Überblick, welche Serien Aufmerksamkeit brauchen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-wizard-btn"]',
        title: 'Story-Arc-Wizard',
        description:
          'Klicke hier, um eine neue Serie zu erstellen. Der Wizard führt dich Schritt für Schritt: Wähle einen Schüler als Protagonisten, lege Titel und Handlungsbogen fest, plane die Episoden und definiere den Erzählton.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-list"]',
        title: 'Episoden-Management',
        description:
          'Jede Karte zeigt eine Serie mit Cover-Bild, Status-Badge, Fortschrittsbalken. Klicke auf eine Karte für die Detail-Ansicht — dort kannst du Episoden verwalten und den Status ändern.',
        position: 'top',
      },
      {
        target: '[data-tour="arcs-filters"]',
        title: 'Filter & Kalender-Integration',
        description:
          'Filtere Serien nach Status, Land oder Schüler. Jede Episode wird als regulärer Post im Kalender eingeplant. Der Wochenplaner berücksichtigt automatisch, welche Episoden als nächstes fällig sind.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-students-hint"]',
        title: 'Zusammenhang mit Schülern',
        description:
          'Jede Story-Serie ist mit einem Schüler-Profil verknüpft. Das Profil liefert automatisch Namen, Land, Schule und Persönlichkeit für die KI-Textgenerierung. Tipp: Lege zuerst Schüler-Profile an!',
        position: 'top',
      },
    ],
  },

  // ─── Week Planner ────────────────────────────────────────
  'week-planner': {
    title: 'Wochenplaner Tour – KI-gestützter Content-Planer',
    steps: [
      {
        target: '[data-tour="wp-header"]',
        title: 'Was ist der Wochenplaner?',
        description:
          'Der Wochenplaner ist dein KI-gestützter Content-Assistent: Er analysiert deine bisherigen Posts, aktive Story-Serien, wiederkehrende Formate und saisonale Themen — und generiert daraus automatisch einen ausgewogenen Wochenplan mit optimalen Posting-Zeiten. Statt stundenlang zu planen, erhältst du in Sekunden einen kompletten Plan für die ganze Woche!',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-filters"]',
        title: 'Filter: Saison, Land & Formate',
        description:
          'Hier steuerst du, was die KI berücksichtigen soll: Wähle die Woche per Datumspicker oder Pfeil-Buttons, bestimme die Anzahl der Posts (2-7 pro Woche) und aktiviere die Checkboxen für "Wiederkehrende Formate" (z.B. Motivation Monday, Freitags-Fail) und "Story-Serien" (laufende mehrteilige Serien). Die KI berücksichtigt automatisch die aktuelle Saison und rotiert Länder gleichmäßig.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-generate"]',
        title: 'KI-Generierung starten',
        description:
          'Klicke auf "Plan generieren", um die KI loszuschicken! Sie prüft bereits geplante Posts für die gewählte Woche (damit nichts doppelt wird), berücksichtigt aktive Story-Arcs und deren nächste fällige Episoden, schlägt wiederkehrende Formate am richtigen Wochentag vor und füllt die restlichen Slots mit einem ausgewogenen Mix aus Kategorien und Ländern. Das Ergebnis: Ein 7-Tage-Raster mit konkreten Vorschlägen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-grid"]',
        title: 'Drag & Drop: Tages-Slots anpassen',
        description:
          'Jede Spalte steht für einen Wochentag (Montag bis Sonntag). Die farbigen Karten sind Content-Vorschläge mit Kategorie, Plattform, Land und Uhrzeit. Du kannst sie frei per Drag & Drop zwischen den Tagen verschieben — z.B. einen Post von Montag auf Mittwoch ziehen. Klicke das X auf einer Karte, um einen Vorschlag zu entfernen. Bereits geplante Posts (mit Pin-Icon) werden angezeigt, sind aber nicht verschiebbar.',
        position: 'top',
      },
      {
        target: '[data-tour="wp-adopt"]',
        title: 'Plan in den Kalender übernehmen',
        description:
          'Wenn du mit dem Plan zufrieden bist, klicke "Plan übernehmen" — alle Vorschläge werden als geplante Entwürfe im Content-Kalender erstellt. Die Posts erhalten automatisch das richtige Datum, die Uhrzeit, Kategorie, Land und Plattform. Serien-Episoden werden mit der korrekten Story-Arc-ID und Episodennummer verknüpft. Nach der Übernahme wirst du direkt zum Kalender weitergeleitet, wo du die Posts weiter bearbeiten kannst.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-legend"]',
        title: 'Zusammenspiel: Kalender & Formate',
        description:
          'Der Wochenplaner arbeitet Hand in Hand mit dem Content-Kalender und den Wiederkehrenden Formaten: Formate wie "Motivation Monday" werden automatisch am passenden Wochentag vorgeschlagen, Story-Serien-Episoden erscheinen in der richtigen Reihenfolge, und der Kalender zeigt dir nach der Übernahme sofort die Lücken-Erkennung und den Content-Mix. Tipp: Erstelle zuerst deine wiederkehrenden Formate unter "Wiederkehrende Formate" — der Wochenplaner nutzt sie dann automatisch!',
        position: 'top',
      },
    ],
  },

  // ─── Recurring Formats ───────────────────────────────────
  'recurring-formats': {
    title: 'Wiederkehrende Formate Tour',
    steps: [
      {
        target: '[data-tour="formats-header"]',
        title: 'Was sind wiederkehrende Formate?',
        description:
          'Wiederkehrende Formate sind regelmäßige Content-Rubriken für deine Social-Media-Kanäle — wie "Motivation Monday", "Freitags-Fail" oder "Throwback Thursday". WARUM? Feste Rubriken schaffen Wiedererkennungswert bei deinem Publikum und geben dir eine klare Struktur für die Woche. Follower wissen, was sie erwarten können, und kommen gezielt zurück. Hier verwaltest du alle deine Formate zentral.',
        position: 'bottom',
      },
      {
        target: '[data-tour="formats-create"]',
        title: 'Format erstellen: Name, Frequenz & Ton',
        description:
          'Klicke auf "+ Neues Format", um ein eigenes Format anzulegen. Vergib einen einprägsamen Namen (z.B. "Wusstest-du-Mittwoch"), wähle die Häufigkeit (täglich, wöchentlich, alle 2 Wochen, monatlich), lege den bevorzugten Wochentag und die Uhrzeit fest, und bestimme die Tonalität (jugendlich, witzig, emotional, motivierend, informativ, seriös). Eigene Hashtags werden automatisch bei jedem Post dieses Formats vorgeschlagen — so bleibt dein Branding konsistent.',
        position: 'bottom',
      },
      {
        target: '[data-tour="formats-ai-preview"]',
        title: 'KI-Textvorschlag: AI-Preview',
        description:
          'Der "KI-Text"-Button öffnet die KI-Textgenerierung für dieses Format. Gib optional ein Thema (z.B. "Trinkgeld-Kultur in den USA") und ein Zielland ein — die KI generiert dann einen passenden Titel, Caption-Text und Hashtags im Stil des Formats. WARUM? So bekommst du in Sekunden Content-Ideen, die zum Ton und Thema deines Formats passen. Die Vorschläge lassen sich direkt im Post-Editor weiterverwenden.',
        position: 'top',
      },
      {
        target: '[data-tour="formats-info"]',
        title: 'Kalender & Wochenplaner: Automatische Integration',
        description:
          'Aktive Formate werden automatisch im Content-Kalender als Platzhalter am bevorzugten Wochentag angezeigt. Der KI-Wochenplaner berücksichtigt deine Formate und schlägt passende Posts für die richtigen Tage vor — z.B. einen "Motivation Monday"-Post am Montag. WARUM? So musst du nicht jede Woche neu überlegen, welchen Content du wann postest. Die Formate bilden das Gerüst deiner Content-Strategie und füllen automatisch Lücken im Kalender.',
        position: 'top',
      },
      {
        target: '[data-tour="formats-list"]',
        title: 'Best Practices: Die richtige Balance',
        description:
          'Tipp: Starte mit 2-3 wiederkehrenden Formaten pro Woche — das ist ideal für Konsistenz ohne Überbelastung. Zu viele Formate fühlen sich für Follower repetitiv an und schränken deine Flexibilität für aktuelle Themen ein. Beispiel-Woche: Montag = "Motivation Monday" (motivierend), Mittwoch = "Wusstest-du-Mittwoch" (informativ), Freitag = "Freitags-Fail" (witzig). Deaktiviere Formate vorübergehend statt sie zu löschen — so kannst du sie später einfach reaktivieren.',
        position: 'bottom',
      },
    ],
  },

  // ═══════════════════════════════════════════════════════════
  // VIDEO-TOOL-SUITE TOURS
  // ═══════════════════════════════════════════════════════════

  'thumbnail-generator': {
    title: 'Thumbnail-Generator Tour',
    steps: [
      {
        target: '[data-tour="tg-header"]',
        title: 'Thumbnails erstellen',
        description:
          'Willkommen im Thumbnail-Generator! Erstelle ansprechende Thumbnails für deine Videos und Reels — mit Text-Overlays, TREFF-Branding und verschiedenen Layouts. Teil der Video-Tool-Suite: Thumbnails → Overlay → Schnitt → Branding → Export → Audio.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tg-hook-text"]',
        title: 'Hook-Text: Aufmerksamkeit gewinnen',
        description:
          'Gib hier deinen Hook-Text ein — den kurzen, knackigen Satz, der auf dem Thumbnail erscheint und sofort Aufmerksamkeit erregt. Nutze maximal 5-7 Wörter, z.B. "Dein Auslandsjahr wartet!" oder "5 Dinge, die niemand dir sagt". Der Hook entscheidet, ob Nutzer auf dein Video klicken.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tg-background"]',
        title: 'Hintergrund wählen',
        description:
          'Wähle einen Hintergrund für dein Thumbnail: Lade ein eigenes Foto hoch, wähle aus der TREFF-Asset-Bibliothek oder nutze einen einfarbigen Hintergrund in TREFF-Blau oder -Gelb. Eigene Fotos von Schülerinnen im Ausland wirken besonders authentisch und erzielen höhere Klickraten.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tg-export"]',
        title: 'Export-Optionen',
        description:
          'Exportiere dein Thumbnail als PNG oder JPG. Wähle die passende Größe: 1280x720 (YouTube/Standard), 1080x1080 (Instagram Feed), oder 1080x1920 (Stories/Reels). Du kannst auch mehrere Größen gleichzeitig exportieren für verschiedene Plattformen.',
        position: 'top',
      },
      {
        target: '[data-tour="tg-preview"]',
        title: 'Live-Vorschau',
        description:
          'Hier siehst du die Echtzeit-Vorschau deines Thumbnails. Alle Änderungen — Text, Hintergrund, Branding-Elemente — werden sofort sichtbar. Tipp: Prüfe, ob der Text auch auf kleinen Handybildschirmen gut lesbar ist.',
        position: 'left',
      },
    ],
  },

  'video-overlays': {
    title: 'Video-Overlay-Editor Tour',
    steps: [
      {
        target: '[data-tour="vo-header"]',
        title: 'Video-Overlay-Editor',
        description:
          'Willkommen im Overlay-Editor! Hier fügst du Text, Logos, Sticker und Animationen über deine Videos — ideal für TREFF-Branding, Untertitel und Call-to-Actions.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-video-select"]',
        title: 'Video auswählen',
        description:
          'Wähle das Video, dem du Overlays hinzufügen möchtest. Du kannst ein bereits hochgeladenes Video aus deiner Bibliothek wählen oder ein neues Video hochladen. Unterstützte Formate: MP4, MOV, WebM.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-layer-add"]',
        title: 'Layer hinzufügen',
        description:
          'Füge neue Overlay-Layer hinzu: Text-Layer für Titel und Untertitel, Bild-Layer für Logos und Sticker, oder Form-Layer für Hintergrundboxen. Jeder Layer kann einzeln positioniert, skaliert und zeitlich eingestellt werden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-layer-list"]',
        title: 'Layer-Verwaltung',
        description:
          'Hier siehst du alle aktiven Layer deines Videos. Ziehe Layer per Drag & Drop, um die Reihenfolge zu ändern. Klicke auf einen Layer, um seine Eigenschaften zu bearbeiten. Blende Layer temporär aus mit dem Augen-Icon.',
        position: 'right',
      },
      {
        target: '[data-tour="vo-preview"]',
        title: 'Video-Vorschau',
        description:
          'Die Echtzeit-Vorschau zeigt dein Video mit allen Overlays. Nutze die Zeitleiste, um zu verschiedenen Stellen zu springen und zu prüfen, ob Overlays zum richtigen Zeitpunkt erscheinen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-properties"]',
        title: 'Layer-Eigenschaften',
        description:
          'Bearbeite hier die Details des ausgewählten Layers: Schriftart, Farbe, Größe, Transparenz, Position, Start-/Endzeit und Animationseffekte. TREFF-Blau (#4C8BC2) und -Gelb (#FDD000) sind als Schnellfarben verfügbar.',
        position: 'left',
      },
      {
        target: '[data-tour="vo-render"]',
        title: 'Rendern & Exportieren',
        description:
          'Wenn alle Overlays sitzen, klicke auf "Rendern", um das finale Video mit allen Overlays zu erzeugen. Das gerenderte Video kann direkt im Video-Export weiterverarbeitet werden.',
        position: 'top',
      },
    ],
  },

  'video-composer': {
    title: 'Video-Composer Tour',
    steps: [
      {
        target: '[data-tour="vc-header"]',
        title: 'Video-Composer',
        description:
          'Willkommen im Video-Composer! Hier schneidest und kombinierst du mehrere Clips zu einem fertigen Video — perfekt für Reels, Zusammenschnitte und Story-Videos.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vc-library"]',
        title: 'Video-Bibliothek',
        description:
          'Durchsuche deine hochgeladenen Videos und wähle Clips für dein Projekt. Ziehe Videos per Drag & Drop in die Timeline. Tipp: Kurze Clips (5-15 Sek.) funktionieren am besten für Social-Media-Reels!',
        position: 'bottom',
      },
      {
        target: '[data-tour="vc-format"]',
        title: 'Ausgabeformat wählen',
        description:
          'Wähle das Seitenverhältnis: 9:16 (Reels/TikTok), 1:1 (Feed), 4:5 (Feed optimal), oder 16:9 (YouTube). Das Format bestimmt, wie deine Clips zugeschnitten werden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vc-timeline"]',
        title: 'Timeline: Clips anordnen',
        description:
          'Die Timeline ist das Herzstück des Composers. Ordne Clips in der gewünschten Reihenfolge an, kürze sie und füge Übergänge hinzu. Ideal sind 15-60 Sekunden für Reels.',
        position: 'top',
      },
      {
        target: '[data-tour="vc-compose"]',
        title: 'Video zusammensetzen',
        description:
          'Klicke auf "Zusammensetzen", um alle Clips zu einem finalen Video zu rendern. Das fertige Video kannst du anschließend im Video-Export für verschiedene Plattformen optimieren.',
        position: 'top',
      },
      {
        target: '[data-tour="vc-branding-link"]',
        title: 'Weiter zu Branding & Export',
        description:
          'Nach dem Zusammensetzen kannst du dein Video mit TREFF-Branding versehen, im Overlay-Editor Text hinzufügen, und im Audio-Mixer Hintergrundmusik einblenden.',
        position: 'bottom',
      },
    ],
  },

  'video-templates': {
    title: 'Video-Branding-Templates Tour',
    steps: [
      {
        target: '[data-tour="vt-header"]',
        title: 'Video-Branding-Templates',
        description:
          'Willkommen bei den Video-Branding-Templates! Hier verwaltest du wiederverwendbare Vorlagen für Intros, Outros, Texteinblendungen und Bauchbinden — alles im TREFF-Design.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-filters"]',
        title: 'Kategorien filtern',
        description:
          'Filtere Templates nach Kategorie: Intro (Vorspann), Outro (Abspann), Lower Third (Bauchbinde), Texteinblendung oder Übergang. So findest du schnell das passende Template.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-grid"]',
        title: 'Template-Galerie',
        description:
          'Durchstöbere die verfügbaren Templates in der Galerie. Jedes Template zeigt eine Vorschau, den Typ und anpassbare Felder. Klicke auf ein Template für Details.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-create"]',
        title: 'Eigenes Template erstellen',
        description:
          'Erstelle eigene Branding-Templates mit dem TREFF-Farbschema. Definiere Platzhalter für Text, Logo-Position und Animationen. Einmal erstellt, immer wieder nutzbar.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-apply"]',
        title: 'Template anwenden',
        description:
          'Wähle ein Template und passe die Platzhalter an. Klicke "Anwenden", um es auf dein aktuelles Video-Projekt zu übertragen. Änderungen sind sofort in der Vorschau sichtbar.',
        position: 'left',
      },
      {
        target: '[data-tour="vt-workflow"]',
        title: 'Workflow-Integration',
        description:
          'Templates lassen sich in jedem Schritt des Video-Workflows einsetzen: Intro vor dem Schnitt, Bauchbinden im Overlay-Editor, Outro am Ende. Konsistentes Branding stärkt die Markenwahrnehmung.',
        position: 'top',
      },
    ],
  },

  'video-export': {
    title: 'Video-Export Tour',
    steps: [
      {
        target: '[data-tour="ve-header"]',
        title: 'Video-Export',
        description:
          'Willkommen im Video-Export! Hier optimierst du deine Videos für verschiedene Plattformen — mit dem richtigen Seitenverhältnis, Fokuspunkt und Qualitätseinstellungen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-library"]',
        title: 'Video-Bibliothek',
        description:
          'Wähle das Video, das du exportieren möchtest. Du siehst alle hochgeladenen und gerenderten Videos mit Vorschaubild, Dauer und Dateigröße.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-aspect-ratio"]',
        title: 'Seitenverhältnis',
        description:
          'Wähle das Seitenverhältnis: 9:16 (Reels, TikTok, Stories), 1:1 (Feed quadratisch), 4:5 (Feed optimal), oder 16:9 (YouTube). Das Video wird entsprechend zugeschnitten.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-focus"]',
        title: 'Fokuspunkt setzen',
        description:
          'Beim Zuschnitt bestimmst du, welcher Bereich im Mittelpunkt bleibt. Setze den Fokuspunkt auf das Gesicht oder das wichtigste Element — so geht nichts Wesentliches verloren.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-platform"]',
        title: 'Plattform-Presets',
        description:
          'Wähle ein vorgefertigtes Preset für deine Zielplattform. Jedes Preset setzt automatisch die optimalen Einstellungen für Auflösung, Bitrate und maximale Dateigröße.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-quality"]',
        title: 'Qualitätseinstellungen',
        description:
          'Passe Auflösung (720p, 1080p, 4K), Bitrate und Komprimierung an. Für Social Media reicht 1080p mit mittlerer Bitrate — wichtiger ist schnelle Ladezeit auf Mobilgeräten.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-batch"]',
        title: 'Batch-Export',
        description:
          'Exportiere ein Video gleichzeitig in mehreren Formaten — z.B. 9:16 für Reels UND 1:1 für den Feed. Alle Varianten werden als ZIP heruntergeladen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-history"]',
        title: 'Export-Verlauf',
        description:
          'Im Verlauf findest du alle bisherigen Exporte mit Datum, Format und Dateigröße. Du kannst frühere Exporte erneut herunterladen oder mit denselben Einstellungen ein neues Video exportieren.',
        position: 'top',
      },
    ],
  },

  'audio-mixer': {
    title: 'Audio-Mixer Tour',
    steps: [
      {
        target: '[data-tour="am-header"]',
        title: 'Audio-Mixer',
        description:
          'Willkommen im Audio-Mixer! Hier fügst du Hintergrundmusik, Soundeffekte und Voiceover zu deinen Videos hinzu — und mischst alle Audio-Spuren professionell ab.',
        position: 'bottom',
      },
      {
        target: '[data-tour="am-video-select"]',
        title: 'Video auswählen',
        description:
          'Wähle das Video, dem du Audio hinzufügen möchtest. Das Original-Audio bleibt erhalten und kann separat in der Lautstärke geregelt oder stummgeschaltet werden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="am-audio-source"]',
        title: 'Audio-Quelle hinzufügen',
        description:
          'Füge Audio-Spuren hinzu: Wähle aus der lizenzfreien Musik-Bibliothek, lade eigene MP3/WAV-Dateien hoch, oder nimm ein Voiceover direkt im Browser auf.',
        position: 'bottom',
      },
      {
        target: '[data-tour="am-waveform"]',
        title: 'Wellenform-Ansicht',
        description:
          'Die Wellenform zeigt visuell den Lautstärke-Verlauf. Nutze sie, um laute und leise Stellen zu erkennen und Audio-Spuren präzise zu synchronisieren.',
        position: 'top',
      },
      {
        target: '[data-tour="am-mixer"]',
        title: 'Lautstärke-Mixer',
        description:
          'Regle die Lautstärke jeder Audio-Spur. Typische Mischung: Hintergrundmusik 20-30%, Voiceover 100%, Original-Audio 50%. So bleibt gesprochener Text verständlich.',
        position: 'left',
      },
      {
        target: '[data-tour="am-fade"]',
        title: 'Fade-Effekte',
        description:
          'Füge Fade-In und Fade-Out hinzu. Ein sanftes Einblenden (1-2 Sek.) und Ausblenden wirkt professionell und vermeidet abrupte Schnitte. Besonders wichtig bei Reels.',
        position: 'left',
      },
      {
        target: '[data-tour="am-output"]',
        title: 'Audio rendern',
        description:
          'Klicke auf "Audio rendern", um alle Spuren zusammenzufügen. Das Ergebnis wird automatisch mit dem Video verbunden. Danach kannst du das Video im Export für verschiedene Plattformen optimieren.',
        position: 'top',
      },
    ],
  },
}

export default tourConfigs
