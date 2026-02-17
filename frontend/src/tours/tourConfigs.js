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
          'Das Dashboard ist deine Zentrale fuer alles rund um Social-Media-Content. Von hier aus startest du alle Workflows: Posts erstellen, planen, analysieren und optimieren. Die Quick-Stats oben zeigen dir auf einen Blick, wie viele Posts du diese Woche erstellt hast, wie viele geplant und wie viele noch als Entwurf bereitliegen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="quick-actions"]',
        title: 'Quick-Actions: Deine Shortcuts',
        description:
          'Mit diesen Buttons startest du direkt die wichtigsten Aktionen: "Post erstellen" fuehrt zum Create Hub mit den 4 Erstellungsmodi, "Kalender" oeffnet die volle Kalender-Ansicht zum Planen, und "Templates" bringt dich direkt zur Vorlagen-Bibliothek. Das Dashboard ist dein Startpunkt fuer jeden Workflow!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-content-queue"]',
        title: 'Content Queue: Was steht als Naechstes an?',
        description:
          'Die Content Queue zeigt dir die naechsten geplanten Posts in chronologischer Reihenfolge. So siehst du sofort, welcher Content als Naechstes veroeffentlicht werden soll — mit Plattform-Icon, Titel, Kategorie und geplantem Datum. Ideal fuer einen schnellen Morgen-Check!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-student-inbox"]',
        title: 'Student Inbox: Frischer Content von Schuelern',
        description:
          'Die Student Inbox sammelt neue Medien und Nachrichten von deinen Austausch-Schuelern. Fotos, Videos und Updates landen hier automatisch und warten darauf, zu Posts verarbeitet zu werden. Klicke auf einen Eintrag, um ihn direkt in einen Post umzuwandeln!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-performance-pulse"]',
        title: 'Performance Pulse: Bist du auf Kurs?',
        description:
          'Der Performance Pulse zeigt dir dein Posting-Tempo der letzten Wochen als Mini-Sparkline. Der Trend-Indikator (steigend/stabil/fallend) verraet dir auf einen Blick, ob du dein Wochen-Ziel erreichst. Gruen = on track, Rot = du musst nachlegen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-active-campaigns"]',
        title: 'Aktive Kampagnen',
        description:
          'Hier siehst du laufende Content-Kampagnen mit Fortschrittsbalken. Jede Kampagne zeigt, wie viele Posts bereits erstellt und geplant wurden — so behaelst du den Ueberblick ueber mehrteilige Aktionen wie saisonale Kampagnen oder Bewerbungszeitraum-Pushes.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-pipeline"]',
        title: 'Pipeline: Content-Verarbeitungs-Funnel',
        description:
          'Die Pipeline zeigt den Verarbeitungsstatus deiner Medien als Funnel-Visualisierung: Wie viele Items warten auf Analyse, wie viele sind analysiert und bereit zur Verarbeitung, und wie viele wurden bereits zu Posts verarbeitet? So erkennst du Engpaesse in deinem Content-Workflow.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-calendar"]',
        title: 'Mini-Kalender: Naechste 7 Tage',
        description:
          'Der Mini-Kalender zeigt die kommende Woche mit farbigen Punkten fuer geplante Posts. So erkennst du auf einen Blick, an welchen Tagen Content ansteht — und wo noch Luecken sind. Fuer die volle Kalender-Ansicht klicke auf "Kalender".',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-suggestions-widget"]',
        title: 'KI Content-Vorschlaege',
        description:
          'Die KI analysiert deinen bisherigen Content und schlaegt passende neue Themen vor — basierend auf Saison, Laender-Rotation, Kategorie-Balance und Content-Luecken. Klicke "Annehmen" um einen Vorschlag direkt als Post zu erstellen.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-recent-posts"]',
        title: 'Letzte Posts',
        description:
          'Hier siehst du deine neuesten Posts als Thumbnail-Grid mit Plattform-Icon, Titel und Status. Klicke auf einen Post, um ihn direkt zu bearbeiten. "Alle anzeigen" fuehrt zum vollstaendigen Post-Archiv in der Bibliothek.',
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
          'Posts aelter als 90 Tage erscheinen hier als Recycling-Vorschlaege. Statt neuen Content zu erstellen, kannst du erfolgreiche alte Posts auffrischen und wiederverwenden. Evergreen-Posts eignen sich besonders gut dafuer.',
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
          'Der Create Hub ist dein Startpunkt fuer die Content-Erstellung. Hier waehlst du, WIE du deinen naechsten Post erstellen moechtest — von der schnellen 2-Klick-Variante bis zur strategischen Multi-Post-Kampagne. Jeder Modus ist fuer einen anderen Anwendungsfall optimiert.',
        position: 'bottom',
      },
      {
        target: '[data-testid="create-card-blue"]',
        title: 'Quick Create: Schnell & Einfach (1-2 Min)',
        description:
          'Der klassische Schritt-fuer-Schritt-Editor: Kategorie waehlen, Template aussuchen, KI-Texte generieren, anpassen und exportieren — alles in einem 9-Schritt-Wizard. Ideal fuer einzelne Posts, die du schnell erstellen moechtest. Der schnellste Weg vom Thema zum fertigen Post!',
        position: 'right',
      },
      {
        target: '[data-testid="create-card-purple"]',
        title: 'Smart Create: Upload-First (3-5 Min)',
        description:
          'Lade ein Foto hoch und lass die KI den Rest erledigen! Smart Create analysiert dein Bild automatisch, erkennt das Thema, schlaegt passende Captions, Hashtags und Templates vor. Perfekt, wenn du ein tolles Schueler-Foto hast und daraus sofort einen Post machen willst.',
        position: 'left',
      },
      {
        target: '[data-testid="create-card-red"]',
        title: 'Video Create: Plattform-gerechte Videos (5 Min)',
        description:
          'Die unified Video-Pipeline: Lade ein Video hoch, fuege automatisch TREFF Intro/Outro-Branding hinzu, waehle Lower Thirds und Musik aus, und exportiere in allen Formaten (9:16 fuer Reels/TikTok, 1:1 fuer Feed). Ein Schritt fuer alles!',
        position: 'right',
      },
      {
        target: '[data-testid="create-card-amber"]',
        title: 'Campaign Create: Multi-Post-Planung (10-15 Min)',
        description:
          'Plane eine mehrteilige Content-Kampagne: Definiere Ziel, Zeitraum und Plattformen, und lass die KI einen kompletten Post-Plan mit Timeline generieren. Ideal fuer saisonale Kampagnen, Bewerbungszeitraum-Pushes oder themenbezogene Content-Serien.',
        position: 'left',
      },
      {
        target: '[data-testid="recent-drafts-section"]',
        title: 'Letzte Entwuerfe',
        description:
          'Unterhalb der Modi-Karten findest du deine 3 neuesten Entwuerfe zum schnellen Weiterbearbeiten. Klicke auf einen Entwurf, um direkt in den Editor zu springen. So verlierst du nie den Faden bei angefangenen Posts!',
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
          'Der Post-Ersteller fuehrt dich in 9 Schritten durch den kompletten Prozess: Von der Kategorie-Auswahl ueber KI-Textgenerierung bis zum fertigen Export. Jeder Schritt baut auf dem vorherigen auf — so entsteht in Minuten ein professioneller Social-Media-Post mit konsistentem TREFF-Branding.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-1"]',
        title: 'Schritt 1: Kategorie waehlen',
        description:
          'Waehle die Art deines Posts: Laender-Spotlight, Erfahrungsberichte, Tipps & Tricks, Fristen & CTA oder FAQ. Die Kategorie bestimmt, welche Templates und KI-Texte vorgeschlagen werden — so passt alles zusammen und dein Content-Mix bleibt ausgewogen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-2"]',
        title: 'Schritt 2: Template waehlen',
        description:
          'Templates sind vorgefertigte Design-Vorlagen mit TREFF-Branding. Jedes Template hat ein festes Layout und bestimmt, wie viele Slides dein Post hat. Die richtige Vorlage spart Design-Arbeit und schafft Wiedererkennungswert.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-5"]',
        title: 'KI-Textgenerierung (Gemini AI)',
        description:
          'Hier generiert Google Gemini AI automatisch alle Texte: Headlines, Body-Texte, Captions und Hashtags — basierend auf Kategorie, Land und Thema. Du sparst Stunden an Copywriting und erhaelst sofort professionelle Texte im richtigen Stil.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-7"]',
        title: 'Slide-Editor (Drag & Drop)',
        description:
          'Der Slide-Editor ist das Herzstuck: Ordne Slides per Drag & Drop, bearbeite Texte direkt und fuege neue Slides hinzu. Die Reihenfolge bestimmt die Story — der erste Slide muss fesseln (Hook), der letzte soll zum Handeln auffordern (CTA).',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-step-6"]',
        title: 'Captions & Hashtags',
        description:
          'Bearbeite Instagram- und TikTok-Captions getrennt voneinander (jede Plattform hat eigene Regeln). Gute Captions und Hashtags steigern die Reichweite enorm — nutze den Sparkle-Button fuer KI-optimierte Vorschlaege.',
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
          'Waehle eine oder mehrere Plattformen gleichzeitig. Captions, Hashtags und Bild-Formate werden automatisch fuer jede Plattform angepasst — beim Export erhaelst du separate, optimierte Dateien.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cp-tour-btn"]',
        title: 'Vorschau, Export & Speichern',
        description:
          'In Schritt 6 siehst du eine Live-Vorschau, in Schritt 8 waehlst du ein Hintergrundbild, und in Schritt 9 exportierst du als PNG/ZIP, speicherst als Entwurf oder planst im Kalender. Tipp: Du kannst diese Tour jederzeit ueber diesen Button erneut starten!',
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
          'Smart Create ist der schnellste Weg von einem Foto zum fertigen Post: Lade ein Bild hoch, die KI analysiert es automatisch und generiert passende Vorschlaege fuer Caption, Hashtags und Post-Typ. Du bearbeitest nur noch die Details — fertig!',
        position: 'bottom',
      },
      {
        target: '[data-testid="media-upload-zone"]',
        title: 'Schritt 1: Foto hochladen',
        description:
          'Ziehe ein Bild per Drag & Drop hierher oder klicke zum Auswaehlen. Unterstuetzte Formate: JPG, PNG, WebP (bis 20 MB). Die KI erkennt automatisch Inhalt, Stimmung und Kontext des Bildes — je besser das Foto, desto praeziser die Vorschlaege!',
        position: 'bottom',
      },
      {
        target: '[data-testid="smart-create-view"]',
        title: 'Schritt 2: KI-Analyse',
        description:
          'Nach dem Upload analysiert die KI dein Bild: Was ist zu sehen? Welches Land koennte es sein? Welcher Ton passt? Das Ergebnis: Post-Typ-Vorschlaege, eine Caption, passende Hashtags und ein empfohlenes Template. Alles in Sekunden!',
        position: 'bottom',
      },
      {
        target: '[data-testid="smart-create-view"]',
        title: 'Schritt 3: Ueberpruefen & Anpassen',
        description:
          'Ueberpruefen und bearbeite die KI-Vorschlaege: Waehle den passenden Post-Typ, passe die Caption an, entferne oder fuege Hashtags hinzu. Wenn du zufrieden bist, speichere den Post als Entwurf oder plane ihn direkt im Kalender.',
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
          'Der Kalender ist dein zentrales Planungstool: Hier siehst du alle geplanten und ungeplanten Posts auf einen Blick, erkennst Content-Luecken und behaltst den Ueberblick ueber Fristen und Serien. Lass uns die wichtigsten Funktionen kennenlernen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-views"]',
        title: 'Ansichten: Monat, Woche & Tag',
        description:
          'Der Kalender bietet drei Hauptansichten: "Monat" zeigt den klassischen Monatsueberblick mit allen Features. "Woche" zeigt eine detaillierte Wochenansicht mit Zeitslots von 06:00 bis 23:00 Uhr. "Tag" zeigt eine Tagesansicht mit Stunden-Timeline, Quick-Edit-Modal und Plattform-Farbcodierung. Wechsle je nach Planungsbedarf!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-grid"]',
        title: 'Drag & Drop: Posts per Maus planen',
        description:
          'Plane deine Posts einfach per Drag & Drop: Ziehe einen Entwurf aus der linken Seitenleiste auf ein Datum. Es oeffnet sich ein Dialog zur Uhrzeitauswahl. Bereits geplante Posts kannst du durch Ziehen auf ein anderes Datum verschieben. In der Tagesansicht kannst du sogar auf Zeitslots klicken!',
        position: 'top',
      },
      {
        target: '[data-tour="cal-sidebar"]',
        title: 'Entwuerfe-Sidebar: Ungeplante Posts',
        description:
          'In der linken Seitenleiste findest du alle Posts ohne Datum. Ziehe eine Karte auf ein Datum im Kalender, um den Post zu planen. Die Sidebar laesst sich einklappen, um mehr Platz fuer den Kalender zu schaffen.',
        position: 'right',
      },
      {
        target: '[data-tour="cal-gaps"]',
        title: 'Luecken-Erkennung',
        description:
          'Aktiviere die Luecken-Erkennung, um Tage ohne geplanten Content orange hervorzuheben. Regelmaessiges Posten ist entscheidend fuer den Instagram-Algorithmus — jede Luecke kostet Reichweite! Der Badge zeigt die Anzahl der Luecken-Tage.',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-seasonal"]',
        title: 'Saisonale Marker',
        description:
          'Aktiviere saisonale Marker, um wichtige Termine direkt im Kalender zu sehen: Bewerbungsfristen, Abflugzeiten und Schuljahresstart in den Ziellaendern. Content rund um diese Termine erzeugt hohe Relevanz!',
        position: 'bottom',
      },
      {
        target: '[data-tour="cal-mix"]',
        title: 'Content-Mix: Ausgewogene Kategorien',
        description:
          'Das Content-Mix-Panel analysiert die Verteilung deiner Posts nach Kategorie, Plattform und Land. Ein ausgewogener Mix haelt deinen Feed abwechslungsreich. Keine Kategorie sollte mehr als 40% ausmachen!',
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
          'Die Bibliothek vereint Assets, Templates und Posts an einem Ort. Ueber die drei Tabs oben wechselst du zwischen deinen Medien (Fotos, Videos), Design-Vorlagen und dem Post-Archiv. Die einheitliche Suche funktioniert tab-uebergreifend!',
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
          'Im Templates-Tab findest du alle Design-Vorlagen fuer deine Posts. Filtere nach Kategorie und Plattform, oeffne den Live-Preview-Editor zum Anpassen, oder erstelle komplett eigene Templates. Drei Sub-Tabs fuer Uebersicht, Galerie und Editor.',
        position: 'bottom',
      },
      {
        target: '[data-testid="library-tab-history"]',
        title: 'Tab 3: Posts – Dein Archiv',
        description:
          'Im Posts-Tab findest du ALLE erstellten Posts — Entwuerfe, geplante und veroeffentlichte. Suche, filtere und sortiere dein Archiv, exportiere Posts als ZIP, dupliziere erfolgreiche Posts oder recycele alte Inhalte. Dein Content-Gedaechtnis!',
        position: 'bottom',
      },
    ],
  },

  // ─── Students Hub ──────────────────────────────────────────
  students: {
    title: 'Schueler Tour – Deine Schueler-Datenbank',
    steps: [
      {
        target: '[data-tour="students-header"]',
        title: 'Warum eine Schueler-Datenbank?',
        description:
          'Echte Geschichten von echten Austausch-Schuelern sind der beste Social-Media-Content! Hier sammelst du alle Infos ueber deine Teilnehmer — Name, Land, Schule, Bio und Fun-Facts. Diese Daten fliessen automatisch in die KI-Textgenerierung ein.',
        position: 'bottom',
      },
      {
        target: '[data-tour="students-add-btn"]',
        title: 'Schueler anlegen',
        description:
          'Klicke auf "Student hinzufuegen" fuer ein neues Profil. Pflichtfelder: Name und Land. Optional aber empfohlen: Stadt, Schule, Gastfamilie, Bio und Fun-Facts. Je mehr Details, desto authentischer und vielfaeltiger die KI-generierten Texte!',
        position: 'bottom',
      },
      {
        target: '[data-tour="students-personality"]',
        title: 'Persoenlichkeits-Presets',
        description:
          'Jeder Schueler bekommt ein Persoenlichkeits-Preset (witzig, emotional, motivierend...) und einen Humor-Level. Das steuert die KI-Textgenerierung — so klingt jeder Schueler in Posts anders und authentisch!',
        position: 'top',
      },
      {
        target: '[data-tour="students-list"]',
        title: 'Schueler-Karten & Pipeline',
        description:
          'Die Schueler-Karten zeigen auf einen Blick: Name, Land mit Flagge, Schule und einen Pipeline-Indikator, der anzeigt, wie viele Posts bereits fuer diesen Schueler erstellt wurden. Klicke auf eine Karte fuer das Detail-Profil — dort kannst du auch direkt einen Post fuer diesen Schueler starten!',
        position: 'top',
      },
      {
        target: '[data-tour="students-story-arc-hint"]',
        title: 'Story-Arcs: Schueler als Hauptfiguren',
        description:
          'Schueler sind die Hauptfiguren deiner Content-Serien! Ein Story-Arc erzaehlt die Geschichte eines Schuelers ueber mehrere Posts — z.B. "Lisas Semester in Neuseeland". Lege zuerst Profile an, dann erstelle unter "Story-Arcs" mehrteilige Serien.',
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
          'Das Analytics-Dashboard ist dein Kompass fuer datenbasierte Content-Optimierung. Hier siehst du auf einen Blick, wie aktiv du postest, ob du deine Ziele erreichst und wie ausgewogen dein Content-Mix ist. Ohne Daten postest du im Blindflug — mit Analytics erkennst du Muster und Chancen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-strategy"]',
        title: 'Strategie-Gesundheit: IST vs. SOLL',
        description:
          'Das Strategy Health Panel vergleicht deine tatsaechliche Content-Verteilung mit deinen Zielwerten — wie ein Gesundheits-Check fuer deine Content-Strategie! Du siehst sofort, welche Content-Pillar (Informieren, Unterhalten, Inspirieren, Konvertieren) ueber- oder unterrepresentiert sind.',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-goals"]',
        title: 'Zielverfolgung: Dein Fortschritt',
        description:
          'Die Fortschrittsbalken zeigen, wie nah du deinen Posting-Zielen bist — getrennt nach Woche und Monat. Gruen = Ziel erreicht! Die Zielwerte konfigurierst du unter Einstellungen > Posting-Ziele. Der Wochenplaner hilft, Ziele systematisch zu erreichen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-frequency"]',
        title: 'Posting-Frequenz',
        description:
          'Das Liniendiagramm zeigt, wie oft du in einem Zeitraum gepostet hast. Wechsle zwischen 7 Tagen, 30 Tagen, Quartal und Jahr. Regelmaessigkeit ist der wichtigste Faktor fuer den Instagram-Algorithmus — Luecken kosten Reichweite!',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-heatmap"]',
        title: 'Aktivitaets-Heatmap',
        description:
          'Die Heatmap zeigt deine Posting-Aktivitaet im GitHub-Stil: Jedes Kaestchen steht fuer einen Tag, die Farbe zeigt die Anzahl der Posts. So erkennst du sofort Phasen hoher und niedriger Aktivitaet ueber laengere Zeitraeume — und kannst Muster erkennen.',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-categories"]',
        title: 'Kategorieverteilung: Content-Mix',
        description:
          'Das Donut-Diagramm zeigt die Verteilung nach Kategorie: Laender-Spotlight, Erfahrungsberichte, Tipps & Tricks, FAQ und mehr. Ziel: Keine Kategorie ueber 40%. Ein ausgewogener Mix haelt Follower interessiert und spricht verschiedene Zielgruppen an.',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-platforms"]',
        title: 'Plattformverteilung: Instagram vs. TikTok',
        description:
          'Die Donut-Charts zeigen, wie sich deine Posts auf Instagram Feed, Story und TikTok verteilen — plus eine Aufschluesselung nach Format (Bild, Video, Carousel). So stellst du sicher, dass du beide Zielgruppen bedienst: Teenager auf TikTok UND Eltern auf Instagram.',
        position: 'top',
      },
      {
        target: '[data-tour="analytics-reports"]',
        title: 'Report Generator',
        description:
          'Generiere ausfuehrliche Reports fuer bestimmte Zeitraeume — ideal fuer Team-Meetings, Quartals-Reviews oder Kundenberichte. Reports enthalten alle Charts, Statistiken und Empfehlungen als uebersichtliche Zusammenfassung.',
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
          'Templates sind vorgefertigte Design-Vorlagen fuer deine Social-Media-Posts. Sie sorgen fuer ein konsistentes TREFF-Branding und sparen dir Zeit bei der Erstellung — jeder Post sieht professionell aus, ohne dass du jedes Mal bei null anfangen musst.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-filters"]',
        title: 'Template-Galerie filtern',
        description:
          'Nutze die Filter, um Vorlagen nach Kategorie (z.B. Laender-Spotlight, FAQ, Erfahrungsberichte) oder Plattform-Format (Instagram Feed, Story, TikTok) einzugrenzen. Die Galerie zeigt dir die Anzahl der Treffer und gruppiert Templates nach Kategorie.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-grid"]',
        title: 'Live-Preview-Editor',
        description:
          'Klicke auf ein Template, um den Live-Preview-Editor zu oeffnen. Dort siehst du in Echtzeit, wie dein Post mit dem gewaehlten Template aussehen wird. Du kannst Texte, Farben und Schriftarten direkt anpassen — jede Aenderung wird sofort in der Vorschau sichtbar.',
        position: 'top',
      },
      {
        target: '[data-tour="tpl-create-btn"]',
        title: 'Farben, Fonts & Brand-Identitaet',
        description:
          'Im Anpassungs-Panel des Editors kannst du Primaer-, Sekundaer- und Hintergrundfarben aendern, Ueberschrift- und Fliesstext-Schriftarten waehlen und alle Texte bearbeiten. Erstelle mit dem "+"-Button auch komplett eigene Templates mit eigenem HTML/CSS-Code.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tpl-video-hint"]',
        title: 'Video-Templates',
        description:
          'Neben Post-Templates gibt es auch spezielle Video-Templates fuer Reels und TikToks. Diese findest du auf einer separaten Seite unter "Video-Branding" in der Seitenleiste — dort kannst du Intros, Outros, Lower Thirds und Overlay-Vorlagen verwalten.',
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
          'Die Asset-Bibliothek ist deine zentrale Medienverwaltung. Hier lagerst du alle Bilder, Videos und Audio-Dateien, die du fuer deine Social-Media-Posts brauchst. Von hier aus kannst du Dateien hochladen, organisieren, bearbeiten und in Posts einbinden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-upload"]',
        title: 'Dateien hochladen – Drag & Drop',
        description:
          'Ziehe Bilder, Videos oder Audio-Dateien einfach per Drag & Drop in diesen Bereich — oder klicke zum Auswaehlen. Unterstuetzte Formate: JPG, PNG, WebP (bis 20 MB), MP4, MOV, WebM (bis 500 MB) und MP3, WAV, AAC (bis 50 MB). Unter dem Upload-Bereich kannst du direkt Kategorie, Land und Tags vergeben.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-grid"]',
        title: 'Crop-Tool & Video-Trimmer',
        description:
          'Bewege die Maus ueber ein Asset, um die Bearbeitungs-Buttons zu sehen: Bei Bildern erscheint ein Crop-Button zum Zuschneiden (z.B. auf Instagram-Formate 1:1, 4:5, 9:16). Bei Videos gibt es einen Trim-Button zum Kuerzen und einen Audio-Mix-Button. So bereitest du Medien direkt hier fuer Social Media vor — ohne externe Tools.',
        position: 'top',
      },
      {
        target: '[data-tour="assets-filters"]',
        title: 'Kategorisierung, Tagging & Suche',
        description:
          'Nutze die Filter, um deine Assets schnell zu finden: Suche nach Dateiname oder Tags, filtere nach Kategorie (Logo, Hintergrund, Foto, Icon, Laenderbild, Video), nach Land (USA, Kanada, Australien, Neuseeland, Irland) oder nach Dateityp (JPG, PNG, WebP, Video, Audio). Aktive Filter werden als Chips angezeigt und lassen sich einzeln entfernen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="assets-tabs"]',
        title: 'Stock-Foto-Integration (Unsplash & Pexels)',
        description:
          'Klicke auf den Tab "Stock Fotos", um kostenlose Stock-Fotos von Unsplash oder Pexels zu durchsuchen. Gib einen englischen Suchbegriff ein (z.B. "highschool campus", "australia landscape") und importiere passende Fotos direkt in deine Bibliothek. So findest du schnell professionelle Bilder fuer deine Posts.',
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
    title: 'Post-Archiv Tour – Dein Content-Gedaechtnis',
    steps: [
      {
        target: '[data-tour="history-header"]',
        title: 'Willkommen im Post-Archiv!',
        description:
          'Das Post-Archiv ist dein zentrales Content-Gedaechtnis. Hier findest du ALLE jemals erstellten Posts — egal ob Entwurf, geplant oder bereits veroeffentlicht. WARUM? Ein gut gepflegtes Archiv ist Gold wert: Du kannst erfolgreiche Posts wiederverwenden, saisonale Inhalte recyclen und jederzeit nachvollziehen, was du wann gepostet hast. So baust du langfristig eine konsistente Content-Strategie fuer TREFF Sprachreisen auf.',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-filters"]',
        title: 'Suche, Filter & Sortierung',
        description:
          'Mit der Suchleiste findest du Posts blitzschnell nach Titel oder Stichwort. Die Filter-Dropdowns grenzen nach Kategorie (z.B. Laender-Spotlight, FAQ), Plattform (Instagram Feed, Story, TikTok), Status (Entwurf, Geplant, Veroeffentlicht), Land und Zeitraum ein. Die Sortierung laesst sich nach Erstelldatum, Aktualisierung, Titel oder geplantem Datum ordnen — aufsteigend oder absteigend. TIPP: Kombiniere Filter, um z.B. alle USA-Posts der letzten 30 Tage zu finden!',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-batch"]',
        title: 'Batch-Auswahl & ZIP-Export',
        description:
          'Klicke auf "Auswaehlen", um in den Mehrfachauswahl-Modus zu wechseln. Waehle einzelne Posts per Checkbox oder nutze "Alle auswaehlen" fuer die komplette Seite. Mit "Batch-Export" erhaelst du alle ausgewaehlten Posts als ZIP-Datei — jeder Post wird als PNG-Bild gerendert, perfekt zum Versenden an Kunden oder fuer Backup-Zwecke. TIPP: Exportiere z.B. alle Posts einer Woche, um sie deinem Team zur Freigabe zu schicken.',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-actions"]',
        title: 'Post-Aktionen: Bearbeiten, Duplizieren & Loeschen',
        description:
          'Jeder Post bietet dir mehrere Aktionen: Mit dem Stift-Icon (Bearbeiten) oeffnest du den Post im Editor und kannst Text, Bilder oder Design aendern. Das Kopier-Icon (Duplizieren) erstellt eine exakte Kopie als neuen Entwurf — ideal fuer aehnliche Posts mit kleinen Anpassungen. Das Kalender-Icon ermoeglicht direktes (Um-)Planen. Und das Papierkorb-Icon (Loeschen) entfernt den Post nach Bestaetigung endgueltig.',
        position: 'top',
      },
      {
        target: '[data-tour="history-recycling"]',
        title: 'Content-Recycling: Alte Posts neu nutzen!',
        description:
          'Das Archiv ist dein Schluessel zum Content-Recycling! Erfolgreiche Posts von letztem Jahr koennen mit kleinen Anpassungen erneut veroeffentlicht werden. STRATEGIE: (1) Filtere nach "Veroeffentlicht" und sortiere nach Engagement. (2) Dupliziere Top-Posts und aktualisiere Zahlen, Daten oder Bilder. (3) Plane den recycelten Post im Kalender fuer eine ruhige Woche. So sparst du Zeit und nutzt bewaehrte Inhalte optimal. Gehe zum Wochenplaner, um recycelte Posts strategisch einzuplanen!',
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
          'Die Einstellungen sind dein Kontrollzentrum: Hier konfigurierst du alles, was die App an dein Unternehmen und deine Arbeitsweise anpasst — von Account-Daten ueber Brand-Farben und API-Schluessel bis hin zu Posting-Zielen, Content-Mix und Hashtag-Strategien. Jede Aenderung hier wirkt sich direkt auf Posts, Templates, KI-Generierung und Analytics aus. Lass uns die einzelnen Bereiche kennenlernen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-brand"]',
        title: 'Brand-Farben: Dein visuelles Branding',
        description:
          'Die drei Brand-Farben (Primaer, Sekundaer, Akzent) definieren das visuelle Erscheinungsbild deiner gesamten Content-Produktion. WARUM? Diese Farben fliessen automatisch in alle Templates ein — Ueberschriften, Buttons, Hintergruende und Akzente nutzen deine Markenfarben fuer konsistentes Branding. Die Vorschau unten zeigt dir sofort, wie die Farben zusammenwirken. Standard: TREFF-Blau (#3B7AB1), TREFF-Gelb (#FDD000) und Weiss (#FFFFFF).',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-api-keys"]',
        title: 'API-Schluessel: KI & Stock-Fotos freischalten',
        description:
          'Hier hinterlegst du die Schluessel fuer externe Dienste: Der Google Gemini API-Schluessel aktiviert die KI-Textgenerierung (Captions, Hashtags, Hooks) und KI-Bildgenerierung — ohne ihn funktioniert kein KI-Feature! Der OpenAI-Schluessel ist ein optionaler Fallback fuer Textgenerierung. Der Unsplash-Schluessel ermoeglicht die Suche nach kostenlosen Stock-Fotos direkt in der Asset-Bibliothek. Alle Schluessel werden verschluesselt gespeichert und nie im Klartext angezeigt.',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-posting-goals"]',
        title: 'Posting-Ziele: Deine Content-Targets',
        description:
          'Hier definierst du deine Posting-Ziele: Posts pro Woche und Monat, bevorzugte Posting-Zeit und Plattform, sowie den Mindestabstand zwischen Story-Arc-Episoden. WARUM? Diese Ziele werden im Analytics-Dashboard als Fortschrittsbalken angezeigt — so siehst du jederzeit, ob du auf Kurs bist. Der KI-Wochenplaner nutzt die bevorzugte Plattform und Zeit als Basis fuer Vorschlaege. Empfehlung: Starte mit 3-4 Posts pro Woche und steigere dich schrittweise.',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-content-mix"]',
        title: 'Content-Mix-Ziele: Ausgewogene Verteilung',
        description:
          'Der Ziel-Content-Mix bestimmt, wie sich deine Posts auf Plattformen und Laender verteilen sollen. Die Plattform-Verteilung (Instagram Feed, Story, TikTok) stellt sicher, dass du alle Kanaele bedienst. Die Laender-Verteilung (USA, Kanada, Australien, Neuseeland, Irland) sorgt dafuer, dass kein Zielland vernachlaessigt wird. WARUM? Das Analytics-Dashboard vergleicht deine tatsaechliche Verteilung mit diesen Zielen und zeigt Abweichungen — so erkennst du, welche Laender oder Plattformen mehr Aufmerksamkeit brauchen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="settings-hashtags"]',
        title: 'Hashtag-Manager: Deine Hashtag-Strategie',
        description:
          'Der Hashtag-Manager verwaltet vordefinierte Hashtag-Sets fuer verschiedene Laender und Kategorien. 17 Standard-Sets (TREFF Brand, Engagement Booster, laenderspezifische Sets) sind bereits angelegt — du kannst eigene Sets erstellen, bearbeiten und filtern. WARUM? Im Post-Editor werden passende Hashtags automatisch vorgeschlagen, basierend auf Kategorie und Land des Posts. So nutzt du immer die richtigen Hashtags fuer maximale Reichweite, ohne jedes Mal neu zu recherchieren. Standard-Sets sind schuetzwuerdig und koennen nicht versehentlich geloescht werden.',
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
          'Story-Arcs sind mehrteilige Content-Serien, z.B. "Lenas Abenteuer in Kanada" als 8-teilige Serie. Serien-Content ist der staerkste Hebel fuer Follower-Bindung: Wer Teil 1 sieht, will Teil 2 sehen — und kommt aktiv zurueck!',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-stats"]',
        title: 'Story-Arc-Uebersicht',
        description:
          'Diese Statistik-Karten zeigen dir den Stand aller Serien: Wie viele sind aktiv, pausiert, als Entwurf oder abgeschlossen. So behaelst du den Ueberblick, welche Serien Aufmerksamkeit brauchen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-wizard-btn"]',
        title: 'Story-Arc-Wizard',
        description:
          'Klicke hier, um eine neue Serie zu erstellen. Der Wizard fuehrt dich Schritt fuer Schritt: Waehle einen Schueler als Protagonisten, lege Titel und Handlungsbogen fest, plane die Episoden und definiere den Erzaehlton.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-list"]',
        title: 'Episoden-Management',
        description:
          'Jede Karte zeigt eine Serie mit Cover-Bild, Status-Badge, Fortschrittsbalken. Klicke auf eine Karte fuer die Detail-Ansicht — dort kannst du Episoden verwalten und den Status aendern.',
        position: 'top',
      },
      {
        target: '[data-tour="arcs-filters"]',
        title: 'Filter & Kalender-Integration',
        description:
          'Filtere Serien nach Status, Land oder Schueler. Jede Episode wird als regulaerer Post im Kalender eingeplant. Der Wochenplaner beruecksichtigt automatisch, welche Episoden als naechstes faellig sind.',
        position: 'bottom',
      },
      {
        target: '[data-tour="arcs-students-hint"]',
        title: 'Zusammenhang mit Schuelern',
        description:
          'Jede Story-Serie ist mit einem Schueler-Profil verknuepft. Das Profil liefert automatisch Namen, Land, Schule und Persoenlichkeit fuer die KI-Textgenerierung. Tipp: Lege zuerst Schueler-Profile an!',
        position: 'top',
      },
    ],
  },

  // ─── Week Planner ────────────────────────────────────────
  'week-planner': {
    title: 'Wochenplaner Tour – KI-gestuetzter Content-Planer',
    steps: [
      {
        target: '[data-tour="wp-header"]',
        title: 'Was ist der Wochenplaner?',
        description:
          'Der Wochenplaner ist dein KI-gestuetzter Content-Assistent: Er analysiert deine bisherigen Posts, aktive Story-Serien, wiederkehrende Formate und saisonale Themen — und generiert daraus automatisch einen ausgewogenen Wochenplan mit optimalen Posting-Zeiten. Statt stundenlang zu planen, erhaelst du in Sekunden einen kompletten Plan fuer die ganze Woche!',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-filters"]',
        title: 'Filter: Saison, Land & Formate',
        description:
          'Hier steuerst du, was die KI beruecksichtigen soll: Waehle die Woche per Datumspicker oder Pfeil-Buttons, bestimme die Anzahl der Posts (2-7 pro Woche) und aktiviere die Checkboxen fuer "Wiederkehrende Formate" (z.B. Motivation Monday, Freitags-Fail) und "Story-Serien" (laufende mehrteilige Serien). Die KI beruecksichtigt automatisch die aktuelle Saison und rotiert Laender gleichmaessig.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-generate"]',
        title: 'KI-Generierung starten',
        description:
          'Klicke auf "Plan generieren", um die KI loszuschicken! Sie prueft bereits geplante Posts fuer die gewaehlte Woche (damit nichts doppelt wird), beruecksichtigt aktive Story-Arcs und deren naechste faellige Episoden, schlaegt wiederkehrende Formate am richtigen Wochentag vor und fuellt die restlichen Slots mit einem ausgewogenen Mix aus Kategorien und Laendern. Das Ergebnis: Ein 7-Tage-Raster mit konkreten Vorschlaegen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-grid"]',
        title: 'Drag & Drop: Tages-Slots anpassen',
        description:
          'Jede Spalte steht fuer einen Wochentag (Montag bis Sonntag). Die farbigen Karten sind Content-Vorschlaege mit Kategorie, Plattform, Land und Uhrzeit. Du kannst sie frei per Drag & Drop zwischen den Tagen verschieben — z.B. einen Post von Montag auf Mittwoch ziehen. Klicke das X auf einer Karte, um einen Vorschlag zu entfernen. Bereits geplante Posts (mit Pin-Icon) werden angezeigt, sind aber nicht verschiebbar.',
        position: 'top',
      },
      {
        target: '[data-tour="wp-adopt"]',
        title: 'Plan in den Kalender uebernehmen',
        description:
          'Wenn du mit dem Plan zufrieden bist, klicke "Plan uebernehmen" — alle Vorschlaege werden als geplante Entwuerfe im Content-Kalender erstellt. Die Posts erhalten automatisch das richtige Datum, die Uhrzeit, Kategorie, Land und Plattform. Serien-Episoden werden mit der korrekten Story-Arc-ID und Episodennummer verknuepft. Nach der Uebernahme wirst du direkt zum Kalender weitergeleitet, wo du die Posts weiter bearbeiten kannst.',
        position: 'bottom',
      },
      {
        target: '[data-tour="wp-legend"]',
        title: 'Zusammenspiel: Kalender & Formate',
        description:
          'Der Wochenplaner arbeitet Hand in Hand mit dem Content-Kalender und den Wiederkehrenden Formaten: Formate wie "Motivation Monday" werden automatisch am passenden Wochentag vorgeschlagen, Story-Serien-Episoden erscheinen in der richtigen Reihenfolge, und der Kalender zeigt dir nach der Uebernahme sofort die Luecken-Erkennung und den Content-Mix. Tipp: Erstelle zuerst deine wiederkehrenden Formate unter "Wiederkehrende Formate" — der Wochenplaner nutzt sie dann automatisch!',
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
          'Wiederkehrende Formate sind regelmaessige Content-Rubriken fuer deine Social-Media-Kanaele — wie "Motivation Monday", "Freitags-Fail" oder "Throwback Thursday". WARUM? Feste Rubriken schaffen Wiedererkennungswert bei deinem Publikum und geben dir eine klare Struktur fuer die Woche. Follower wissen, was sie erwarten koennen, und kommen gezielt zurueck. Hier verwaltest du alle deine Formate zentral.',
        position: 'bottom',
      },
      {
        target: '[data-tour="formats-create"]',
        title: 'Format erstellen: Name, Frequenz & Ton',
        description:
          'Klicke auf "+ Neues Format", um ein eigenes Format anzulegen. Vergib einen einpraegsamen Namen (z.B. "Wusstest-du-Mittwoch"), waehle die Haeufigkeit (taeglich, woechentlich, alle 2 Wochen, monatlich), lege den bevorzugten Wochentag und die Uhrzeit fest, und bestimme die Tonalitaet (jugendlich, witzig, emotional, motivierend, informativ, serioess). Eigene Hashtags werden automatisch bei jedem Post dieses Formats vorgeschlagen — so bleibt dein Branding konsistent.',
        position: 'bottom',
      },
      {
        target: '[data-tour="formats-ai-preview"]',
        title: 'KI-Textvorschlag: AI-Preview',
        description:
          'Der "KI-Text"-Button oeffnet die KI-Textgenerierung fuer dieses Format. Gib optional ein Thema (z.B. "Trinkgeld-Kultur in den USA") und ein Zielland ein — die KI generiert dann einen passenden Titel, Caption-Text und Hashtags im Stil des Formats. WARUM? So bekommst du in Sekunden Content-Ideen, die zum Ton und Thema deines Formats passen. Die Vorschlaege lassen sich direkt im Post-Editor weiterverwenden.',
        position: 'top',
      },
      {
        target: '[data-tour="formats-info"]',
        title: 'Kalender & Wochenplaner: Automatische Integration',
        description:
          'Aktive Formate werden automatisch im Content-Kalender als Platzhalter am bevorzugten Wochentag angezeigt. Der KI-Wochenplaner beruecksichtigt deine Formate und schlaegt passende Posts fuer die richtigen Tage vor — z.B. einen "Motivation Monday"-Post am Montag. WARUM? So musst du nicht jede Woche neu ueberlegen, welchen Content du wann postest. Die Formate bilden das Geruest deiner Content-Strategie und fuellen automatisch Luecken im Kalender.',
        position: 'top',
      },
      {
        target: '[data-tour="formats-list"]',
        title: 'Best Practices: Die richtige Balance',
        description:
          'Tipp: Starte mit 2-3 wiederkehrenden Formaten pro Woche — das ist ideal fuer Konsistenz ohne Ueberbelastung. Zu viele Formate fuehlen sich fuer Follower repetitiv an und schraenken deine Flexibilitaet fuer aktuelle Themen ein. Beispiel-Woche: Montag = "Motivation Monday" (motivierend), Mittwoch = "Wusstest-du-Mittwoch" (informativ), Freitag = "Freitags-Fail" (witzig). Deaktiviere Formate voruebergehend statt sie zu loeschen — so kannst du sie spaeter einfach reaktivieren.',
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
          'Willkommen im Thumbnail-Generator! Erstelle ansprechende Thumbnails fuer deine Videos und Reels — mit Text-Overlays, TREFF-Branding und verschiedenen Layouts. Teil der Video-Tool-Suite: Thumbnails → Overlay → Schnitt → Branding → Export → Audio.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tg-hook-text"]',
        title: 'Hook-Text: Aufmerksamkeit gewinnen',
        description:
          'Gib hier deinen Hook-Text ein — den kurzen, knackigen Satz, der auf dem Thumbnail erscheint und sofort Aufmerksamkeit erregt. Nutze maximal 5-7 Woerter, z.B. "Dein Auslandsjahr wartet!" oder "5 Dinge, die niemand dir sagt". Der Hook entscheidet, ob Nutzer auf dein Video klicken.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tg-background"]',
        title: 'Hintergrund waehlen',
        description:
          'Waehle einen Hintergrund fuer dein Thumbnail: Lade ein eigenes Foto hoch, waehle aus der TREFF-Asset-Bibliothek oder nutze einen einfarbigen Hintergrund in TREFF-Blau oder -Gelb. Eigene Fotos von Schuelerinnen im Ausland wirken besonders authentisch und erzielen hoehere Klickraten.',
        position: 'bottom',
      },
      {
        target: '[data-tour="tg-export"]',
        title: 'Export-Optionen',
        description:
          'Exportiere dein Thumbnail als PNG oder JPG. Waehle die passende Groesse: 1280x720 (YouTube/Standard), 1080x1080 (Instagram Feed), oder 1080x1920 (Stories/Reels). Du kannst auch mehrere Groessen gleichzeitig exportieren fuer verschiedene Plattformen.',
        position: 'top',
      },
      {
        target: '[data-tour="tg-preview"]',
        title: 'Live-Vorschau',
        description:
          'Hier siehst du die Echtzeit-Vorschau deines Thumbnails. Alle Aenderungen — Text, Hintergrund, Branding-Elemente — werden sofort sichtbar. Tipp: Pruefe, ob der Text auch auf kleinen Handybildschirmen gut lesbar ist.',
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
          'Willkommen im Overlay-Editor! Hier fügst du Text, Logos, Sticker und Animationen ueber deine Videos — ideal fuer TREFF-Branding, Untertitel und Call-to-Actions.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-video-select"]',
        title: 'Video auswaehlen',
        description:
          'Waehle das Video, dem du Overlays hinzufuegen moechtest. Du kannst ein bereits hochgeladenes Video aus deiner Bibliothek waehlen oder ein neues Video hochladen. Unterstuetzte Formate: MP4, MOV, WebM.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-layer-add"]',
        title: 'Layer hinzufuegen',
        description:
          'Fuege neue Overlay-Layer hinzu: Text-Layer fuer Titel und Untertitel, Bild-Layer fuer Logos und Sticker, oder Form-Layer fuer Hintergrundboxen. Jeder Layer kann einzeln positioniert, skaliert und zeitlich eingestellt werden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-layer-list"]',
        title: 'Layer-Verwaltung',
        description:
          'Hier siehst du alle aktiven Layer deines Videos. Ziehe Layer per Drag & Drop, um die Reihenfolge zu aendern. Klicke auf einen Layer, um seine Eigenschaften zu bearbeiten. Blende Layer temporaer aus mit dem Augen-Icon.',
        position: 'right',
      },
      {
        target: '[data-tour="vo-preview"]',
        title: 'Video-Vorschau',
        description:
          'Die Echtzeit-Vorschau zeigt dein Video mit allen Overlays. Nutze die Zeitleiste, um zu verschiedenen Stellen zu springen und zu pruefen, ob Overlays zum richtigen Zeitpunkt erscheinen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vo-properties"]',
        title: 'Layer-Eigenschaften',
        description:
          'Bearbeite hier die Details des ausgewaehlten Layers: Schriftart, Farbe, Groesse, Transparenz, Position, Start-/Endzeit und Animationseffekte. TREFF-Blau (#4C8BC2) und -Gelb (#FDD000) sind als Schnellfarben verfuegbar.',
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
          'Willkommen im Video-Composer! Hier schneidest und kombinierst du mehrere Clips zu einem fertigen Video — perfekt fuer Reels, Zusammenschnitte und Story-Videos.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vc-library"]',
        title: 'Video-Bibliothek',
        description:
          'Durchsuche deine hochgeladenen Videos und waehle Clips fuer dein Projekt. Ziehe Videos per Drag & Drop in die Timeline. Tipp: Kurze Clips (5-15 Sek.) funktionieren am besten fuer Social-Media-Reels!',
        position: 'bottom',
      },
      {
        target: '[data-tour="vc-format"]',
        title: 'Ausgabeformat waehlen',
        description:
          'Waehle das Seitenverhaeltnis: 9:16 (Reels/TikTok), 1:1 (Feed), 4:5 (Feed optimal), oder 16:9 (YouTube). Das Format bestimmt, wie deine Clips zugeschnitten werden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vc-timeline"]',
        title: 'Timeline: Clips anordnen',
        description:
          'Die Timeline ist das Herzstuck des Composers. Ordne Clips in der gewuenschten Reihenfolge an, kuerze sie und fuege Uebergaenge hinzu. Ideal sind 15-60 Sekunden fuer Reels.',
        position: 'top',
      },
      {
        target: '[data-tour="vc-compose"]',
        title: 'Video zusammensetzen',
        description:
          'Klicke auf "Zusammensetzen", um alle Clips zu einem finalen Video zu rendern. Das fertige Video kannst du anschliessend im Video-Export fuer verschiedene Plattformen optimieren.',
        position: 'top',
      },
      {
        target: '[data-tour="vc-branding-link"]',
        title: 'Weiter zu Branding & Export',
        description:
          'Nach dem Zusammensetzen kannst du dein Video mit TREFF-Branding versehen, im Overlay-Editor Text hinzufuegen, und im Audio-Mixer Hintergrundmusik einblenden.',
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
          'Willkommen bei den Video-Branding-Templates! Hier verwaltest du wiederverwendbare Vorlagen fuer Intros, Outros, Texteinblendungen und Bauchbinden — alles im TREFF-Design.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-filters"]',
        title: 'Kategorien filtern',
        description:
          'Filtere Templates nach Kategorie: Intro (Vorspann), Outro (Abspann), Lower Third (Bauchbinde), Texteinblendung oder Uebergang. So findest du schnell das passende Template.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-grid"]',
        title: 'Template-Galerie',
        description:
          'Durchstoebre die verfuegbaren Templates in der Galerie. Jedes Template zeigt eine Vorschau, den Typ und anpassbare Felder. Klicke auf ein Template fuer Details.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-create"]',
        title: 'Eigenes Template erstellen',
        description:
          'Erstelle eigene Branding-Templates mit dem TREFF-Farbschema. Definiere Platzhalter fuer Text, Logo-Position und Animationen. Einmal erstellt, immer wieder nutzbar.',
        position: 'bottom',
      },
      {
        target: '[data-tour="vt-apply"]',
        title: 'Template anwenden',
        description:
          'Waehle ein Template und passe die Platzhalter an. Klicke "Anwenden", um es auf dein aktuelles Video-Projekt zu uebertragen. Aenderungen sind sofort in der Vorschau sichtbar.',
        position: 'left',
      },
      {
        target: '[data-tour="vt-workflow"]',
        title: 'Workflow-Integration',
        description:
          'Templates lassen sich in jedem Schritt des Video-Workflows einsetzen: Intro vor dem Schnitt, Bauchbinden im Overlay-Editor, Outro am Ende. Konsistentes Branding staerkt die Markenwahrnehmung.',
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
          'Willkommen im Video-Export! Hier optimierst du deine Videos fuer verschiedene Plattformen — mit dem richtigen Seitenverhaeltnis, Fokuspunkt und Qualitaetseinstellungen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-library"]',
        title: 'Video-Bibliothek',
        description:
          'Waehle das Video, das du exportieren moechtest. Du siehst alle hochgeladenen und gerenderten Videos mit Vorschaubild, Dauer und Dateigroesse.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-aspect-ratio"]',
        title: 'Seitenverhaeltnis',
        description:
          'Waehle das Seitenverhaeltnis: 9:16 (Reels, TikTok, Stories), 1:1 (Feed quadratisch), 4:5 (Feed optimal), oder 16:9 (YouTube). Das Video wird entsprechend zugeschnitten.',
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
          'Waehle ein vorgefertigtes Preset fuer deine Zielplattform. Jedes Preset setzt automatisch die optimalen Einstellungen fuer Aufloesung, Bitrate und maximale Dateigroesse.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-quality"]',
        title: 'Qualitaetseinstellungen',
        description:
          'Passe Aufloesung (720p, 1080p, 4K), Bitrate und Komprimierung an. Fuer Social Media reicht 1080p mit mittlerer Bitrate — wichtiger ist schnelle Ladezeit auf Mobilgeraeten.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-batch"]',
        title: 'Batch-Export',
        description:
          'Exportiere ein Video gleichzeitig in mehreren Formaten — z.B. 9:16 fuer Reels UND 1:1 fuer den Feed. Alle Varianten werden als ZIP heruntergeladen.',
        position: 'bottom',
      },
      {
        target: '[data-tour="ve-history"]',
        title: 'Export-Verlauf',
        description:
          'Im Verlauf findest du alle bisherigen Exporte mit Datum, Format und Dateigroesse. Du kannst fruehere Exporte erneut herunterladen oder mit denselben Einstellungen ein neues Video exportieren.',
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
        title: 'Video auswaehlen',
        description:
          'Waehle das Video, dem du Audio hinzufuegen moechtest. Das Original-Audio bleibt erhalten und kann separat in der Lautstaerke geregelt oder stummgeschaltet werden.',
        position: 'bottom',
      },
      {
        target: '[data-tour="am-audio-source"]',
        title: 'Audio-Quelle hinzufuegen',
        description:
          'Fuege Audio-Spuren hinzu: Waehle aus der lizenzfreien Musik-Bibliothek, lade eigene MP3/WAV-Dateien hoch, oder nimm ein Voiceover direkt im Browser auf.',
        position: 'bottom',
      },
      {
        target: '[data-tour="am-waveform"]',
        title: 'Wellenform-Ansicht',
        description:
          'Die Wellenform zeigt visuell den Lautstaerke-Verlauf. Nutze sie, um laute und leise Stellen zu erkennen und Audio-Spuren praezise zu synchronisieren.',
        position: 'top',
      },
      {
        target: '[data-tour="am-mixer"]',
        title: 'Lautstaerke-Mixer',
        description:
          'Regle die Lautstaerke jeder Audio-Spur. Typische Mischung: Hintergrundmusik 20-30%, Voiceover 100%, Original-Audio 50%. So bleibt gesprochener Text verstaendlich.',
        position: 'left',
      },
      {
        target: '[data-tour="am-fade"]',
        title: 'Fade-Effekte',
        description:
          'Fuege Fade-In und Fade-Out hinzu. Ein sanftes Einblenden (1-2 Sek.) und Ausblenden wirkt professionell und vermeidet abrupte Schnitte. Besonders wichtig bei Reels.',
        position: 'left',
      },
      {
        target: '[data-tour="am-output"]',
        title: 'Audio rendern',
        description:
          'Klicke auf "Audio rendern", um alle Spuren zusammenzufuegen. Das Ergebnis wird automatisch mit dem Video verbunden. Danach kannst du das Video im Export fuer verschiedene Plattformen optimieren.',
        position: 'top',
      },
    ],
  },
}

export default tourConfigs
