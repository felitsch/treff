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
 */

const tourConfigs = {
  // ─── Dashboard ───────────────────────────────────────────
  dashboard: {
    title: 'Dashboard Tour – Deine Content-Zentrale',
    steps: [
      {
        target: '[data-tour="dashboard-stats"]',
        title: 'Willkommen im Dashboard!',
        description:
          'Das Dashboard ist deine Zentrale fuer alles rund um Social-Media-Content. Von hier aus startest du alle Workflows: Posts erstellen, planen, analysieren und optimieren. Lass uns die einzelnen Bereiche kennenlernen!',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-stats"]',
        title: 'Quick-Stats: Dein Ueberblick',
        description:
          'Diese Karten zeigen dir auf einen Blick: "Posts diese Woche" zaehlt alle Posts der aktuellen Woche, "Geplante Posts" zeigt vorbereitete Inhalte im Kalender, und "Gesamt Assets" zaehlt deine hochgeladenen Bilder und Videos.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-calendar"]',
        title: 'Mini-Kalender: Naechste 7 Tage',
        description:
          'Der Mini-Kalender zeigt die kommende Woche mit blauen Punkten fuer geplante Posts. So erkennst du auf einen Blick, an welchen Tagen Content ansteht – und wo noch Luecken sind. Fuer die volle Kalender-Ansicht nutze den Kalender-Button.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-recent-posts"]',
        title: 'Letzte Posts',
        description:
          'Hier siehst du deine neuesten Posts mit Plattform-Icon, Titel, Kategorie und Status (Entwurf, Geplant, Veroeffentlicht). Klicke auf einen Post, um ihn direkt zu bearbeiten. "Alle anzeigen" fuehrt zum vollstaendigen Post-Verlauf.',
        position: 'bottom',
      },
      {
        target: '[data-tour="dashboard-suggestions"]',
        title: 'KI Content-Vorschlaege',
        description:
          'Die KI analysiert deinen bisherigen Content und schlaegt passende neue Themen vor – basierend auf Saison, Laender-Rotation, Kategorie-Balance und Content-Luecken. Klicke "Annehmen" um einen Vorschlag direkt als Post zu erstellen, oder "Generieren" fuer neue Ideen.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-recycling"]',
        title: 'Content-Recycling',
        description:
          'Posts aelter als 90 Tage erscheinen hier als Recycling-Vorschlaege. Statt neuen Content zu erstellen, kannst du erfolgreiche alte Posts auffrischen und wiederverwenden. Evergreen-Posts eignen sich besonders gut dafuer.',
        position: 'top',
      },
      {
        target: '[data-tour="dashboard-series-status"]',
        title: 'Serien-Status',
        description:
          'Verfolge den Fortschritt deiner Story-Arcs (mehrteilige Content-Serien). Du siehst den Status jeder Serie, die aktuelle Episode, einen Fortschrittsbalken und wann die naechste Episode faellig ist. So verpasst du keine Fortsetzung!',
        position: 'top',
      },
      {
        target: '[data-tour="quick-actions"]',
        title: 'Quick-Actions: Deine Shortcuts',
        description:
          'Mit diesen Buttons startest du direkt die wichtigsten Aktionen: "Post erstellen" fuehrt zum Post-Editor mit KI-Unterstuetzung, "Kalender anzeigen" oeffnet die volle Kalender-Ansicht zum Planen und Terminieren. Das Dashboard ist dein Startpunkt fuer jeden Workflow!',
        position: 'bottom',
      },
    ],
  },

  // ─── Create Post (Ausfuehrliche Wizard-Tour) ─────────────
  'create-post': {
    title: 'Post-Wizard Tour',
    steps: [
      // Tour-Step 1: Ueberblick ueber den 9-Schritt-Wizard
      {
        target: '[data-tour="cp-content"]',
        title: 'Willkommen im Post-Wizard!',
        description:
          'Der Post-Ersteller fuehrt dich in 9 Schritten durch den kompletten Prozess: Von der Kategorie-Auswahl ueber KI-Textgenerierung bis zum fertigen Export. Jeder Schritt baut auf dem vorherigen auf — so entsteht in Minuten ein professioneller Social-Media-Post mit konsistentem TREFF-Branding. Die Schritt-Anzeige oben hilft dir, den Ueberblick zu behalten.',
        position: 'bottom',
      },
      // Tour-Step 2: Kategorie-Auswahl erklaeren
      {
        target: '[data-tour="cp-step-1"]',
        title: 'Schritt 1: Kategorie waehlen',
        description:
          'Im ersten Schritt waehlst du die Art deines Posts: Laender-Spotlight fuer Zielland-Infos, Erfahrungsberichte fuer Alumni-Stories, Tipps & Tricks fuer praktische Ratschlaege, Fristen & CTA fuer Bewerbungsfristen, oder FAQ fuer haeufige Fragen. WARUM? Die Kategorie bestimmt, welche Templates und KI-Texte vorgeschlagen werden — so passt alles perfekt zusammen und dein Content-Mix bleibt ausgewogen.',
        position: 'bottom',
      },
      // Tour-Step 3: Template-Auswahl erklaeren
      {
        target: '[data-tour="cp-step-2"]',
        title: 'Schritt 2: Template waehlen',
        description:
          'Templates sind vorgefertigte Design-Vorlagen mit TREFF-Branding. Jedes Template hat ein festes Layout (Headline, Body, CTA-Button) und bestimmt, wie viele Slides dein Post hat. WARUM? Unterschiedliche Templates betonen verschiedene Aspekte — ein "Laender-Spotlight" zeigt Fakten mit Flagge, ein "Erfahrungsbericht" betont den Schueler-Stil. Die richtige Vorlage spart Design-Arbeit und schafft Wiedererkennungswert.',
        position: 'bottom',
      },
      // Tour-Step 4: AI Textgenerierung erklaeren — was Gemini macht und wie man Ergebnisse anpassen kann
      {
        target: '[data-tour="cp-step-5"]',
        title: 'Schritt 5: KI-Textgenerierung (Gemini AI)',
        description:
          'Hier generiert Google Gemini AI automatisch alle Texte: Headlines, Body-Texte, Captions und Hashtags — basierend auf Kategorie, Land, Thema und Tonalitaet. WARUM KI? Du sparst Stunden an Copywriting und erhaelst sofort professionelle Texte im richtigen Stil. Ergebnisse anpassen: In Schritt 7 kannst du jedes einzelne Feld manuell bearbeiten oder per "Neu generieren"-Button von der KI ueberarbeiten lassen.',
        position: 'bottom',
      },
      // Tour-Step 5: Slide-Editor erklaeren (Drag-and-Drop, Bilder einfuegen, Text anpassen)
      {
        target: '[data-tour="cp-step-7"]',
        title: 'Schritt 7: Slide-Editor (Drag & Drop)',
        description:
          'Der Slide-Editor ist das Herzstuck des Wizards: Ordne deine Slides per Drag & Drop in die optimale Reihenfolge, bearbeite Headlines, Subheadlines und Body-Texte direkt, und fuege neue Slides hinzu oder entferne sie. WARUM? Die Reihenfolge der Slides bestimmt die Story deines Posts — der erste Slide muss fesseln (Hook), der letzte soll zum Handeln auffordern (CTA). Jedes Textfeld hat ein Zeichenlimit mit farbiger Warnung.',
        position: 'bottom',
      },
      // Tour-Step 6: Caption und Hashtags erklaeren (warum wichtig fuer Reichweite)
      {
        target: '[data-tour="cp-step-6"]',
        title: 'Captions & Hashtags (Reichweiten-Turbo)',
        description:
          'In Schritt 7 bearbeitest du Instagram- und TikTok-Captions getrennt voneinander, denn jede Plattform hat eigene Regeln (Instagram: max 2.200 Zeichen, TikTok: kuerzer und knackiger). WARUM? Gute Captions und Hashtags steigern die Reichweite enorm — der Algorithmus zeigt deinen Post mehr Menschen. Nutze den gruenen Sparkle-Button fuer KI-optimierte Hashtag-Vorschlaege und die Emoji-Strategie-Engine.',
        position: 'bottom',
      },
      // Tour-Step 7: CTA erklaeren (Call-to-Action fuer mehr Interaktion)
      {
        target: '[data-tour="cp-step-8"]',
        title: 'CTA: Call-to-Action (Warum unverzichtbar)',
        description:
          'Ein Call-to-Action fordert den Betrachter zum Handeln auf — z.B. "Jetzt bewerben!", "Link in Bio" oder "Speichern fuer spaeter". WARUM? Ohne CTA scrollen Nutzer einfach weiter, MIT CTA steigt die Interaktionsrate um bis zu 300%! In Schritt 7 findest du die CTA-Bibliothek mit 35 vorgefertigten CTAs in 4 Kategorien (Engagement, Conversion, Awareness, Traffic) — kontextbasiert vorgeschlagen fuer maximale Wirkung.',
        position: 'bottom',
      },
      // Tour-Step 8: Hook erklaeren (erster Satz/Slide der Aufmerksamkeit erregt)
      {
        target: '[data-tour="cp-step-9"]',
        title: 'Hook: Die ersten 2 Sekunden entscheiden',
        description:
          'Der Hook ist der allererste Satz oder die erste Slide deines Posts — er entscheidet in 1-2 Sekunden, ob jemand weiterliest oder weiterscrollt! WARUM? Instagram und TikTok zeigen deinen Post zunaechst nur kurz — nur ein fesselnder Hook stoppt den Daumen. Beispiele: "Wusstest du, dass...?", "Die 3 groessten Fehler beim Auslandsjahr" oder "Unpopular Opinion:...". Den Hook-Selector findest du in Schritt 5 nach der Textgenerierung.',
        position: 'bottom',
      },
      // Tour-Step 9: Interaktive Elemente und Engagement-Boost erklaeren
      {
        target: '[data-tour="cp-navigation"]',
        title: 'Interaktive Elemente & Engagement-Boost',
        description:
          'Interaktive Sticker wie Umfragen, Quizze, Slider und Frage-Sticker machen deine Instagram Stories lebendig. WARUM? Sie steigern die Verweildauer und werden vom Algorithmus bevorzugt — dein Post wird MEHR Menschen gezeigt! Der Engagement-Boost-Panel in der Vorschau analysiert deinen Post und schlaegt konkrete Verbesserungen vor: z.B. eine Frage am Ende, einen kontroversen Aufhaenger oder einen Countdown fuer Bewerbungsfristen.',
        position: 'top',
      },
      // Tour-Step 10: Multi-Plattform Anpassung erklaeren (Instagram vs TikTok)
      {
        target: '[data-tour="cp-step-3"]',
        title: 'Multi-Plattform: Instagram vs TikTok',
        description:
          'In Schritt 3 waehlst du eine oder mehrere Plattformen gleichzeitig. WARUM Multi-Plattform? Instagram Feed nutzt 1:1 oder 4:5-Format, Instagram Stories und TikTok nutzen 9:16 (Hochformat). Captions, Hashtags und Bild-Formate werden automatisch fuer jede Plattform angepasst — beim Export erhaelst du separate, optimierte Dateien. So erreichst du mit einem Workflow Teenager auf TikTok UND Eltern auf Instagram!',
        position: 'bottom',
      },
      // Tour-Step 11: Preview und Export erklaeren
      {
        target: '[data-tour="cp-tour-btn"]',
        title: 'Vorschau, Export & Speichern',
        description:
          'In Schritt 6 siehst du eine Live-Vorschau deines Posts mit Plattform-Wechsel. In Schritt 8 waehlst du optional ein Hintergrundbild aus der Asset-Bibliothek oder laesst die KI eines generieren. In Schritt 9 exportierst du den fertigen Post als PNG oder ZIP (bei Multi-Slides), speicherst ihn als Entwurf oder planst ihn direkt im Kalender. Tipp: Du kannst diese Tour jederzeit ueber diesen Button erneut starten!',
        position: 'bottom',
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

  // ─── Calendar ────────────────────────────────────────────
  calendar: {
    title: 'Kalender Tour – Content-Planung',
    steps: [
      // Tour-Step 1: Ueberblick Kalender als zentrales Planungstool
      {
        target: '[data-tour="cal-toolbar"]',
        title: 'Willkommen im Content-Kalender!',
        description:
          'Der Kalender ist dein zentrales Planungstool: Hier siehst du alle geplanten und ungeplanten Posts auf einen Blick, erkennst Content-Luecken und behaltst den Ueberblick ueber Fristen, Serien und wiederkehrende Formate. Von der Monatsansicht bis zur Warteschlange — alles an einem Ort. Lass uns die wichtigsten Funktionen kennenlernen!',
        position: 'bottom',
      },
      // Tour-Step 2: Ansichten erklaeren (Monat/Woche/Lanes/Queue)
      {
        target: '[data-tour="cal-views"]',
        title: 'Ansichten: Monat, Woche, Lanes & Queue',
        description:
          'Der Kalender bietet vier Ansichten fuer verschiedene Planungsbeduerfnisse: "Monat" zeigt den klassischen Monatsueberblick mit allen Features (Luecken, Fristen, Arcs). "Woche" zeigt eine detaillierte Wochenansicht mit Zeitslots von 06:00 bis 23:00 Uhr. "Lanes" trennt Posts nach Plattform (Instagram Feed, Stories, TikTok) in separate Spalten. "Warteschlange" listet alle geplanten Posts chronologisch auf — ideal zum schnellen Ueberpruefen.',
        position: 'bottom',
      },
      // Tour-Step 3: Drag-and-Drop Scheduling erklaeren
      {
        target: '[data-tour="cal-grid"]',
        title: 'Drag & Drop: Posts per Maus planen',
        description:
          'Plane deine Posts einfach per Drag & Drop: Ziehe einen Entwurf aus der linken Seitenleiste auf ein Datum im Kalender. Es oeffnet sich ein Dialog zur Uhrzeitauswahl. Bei Serien-Posts (Story-Arcs) wird automatisch geprueft, ob die Episoden-Reihenfolge stimmt — und du wirst gewarnt, falls nicht. Bereits geplante Posts kannst du durch erneutes Ziehen auf ein anderes Datum verschieben.',
        position: 'top',
      },
      // Tour-Step 4: Entwuerfe-Sidebar erklaeren
      {
        target: '[data-tour="cal-sidebar"]',
        title: 'Entwuerfe-Sidebar: Ungeplante Posts',
        description:
          'In der linken Seitenleiste findest du alle Posts, die noch kein Datum haben. Jede Karte zeigt Kategorie, Plattform und Status auf einen Blick. Ziehe eine Karte einfach auf ein Datum im Kalender, um den Post zu planen. Wenn alle Posts terminiert sind, erscheint hier ein "Alle Posts geplant!"-Hinweis. Die Sidebar laesst sich einklappen, um mehr Platz fuer den Kalender zu schaffen.',
        position: 'right',
      },
      // Tour-Step 5: Luecken-Erkennung erklaeren
      {
        target: '[data-tour="cal-gaps"]',
        title: 'Luecken-Erkennung: Nie wieder Posting-Pausen',
        description:
          'Aktiviere die Luecken-Erkennung, um Tage ohne geplanten Content orange hervorzuheben. WARUM? Regelmaessiges Posten ist entscheidend fuer den Instagram-Algorithmus — jede Luecke kostet Reichweite! Der Badge zeigt die Anzahl der Luecken-Tage an. Tipp: Nutze den KI-Wochenplaner, um Luecken schnell mit passenden Vorschlaegen zu fuellen.',
        position: 'bottom',
      },
      // Tour-Step 6: Saisonale Marker erklaeren
      {
        target: '[data-tour="cal-seasonal"]',
        title: 'Saisonale Marker: Fristen im Blick',
        description:
          'Aktiviere die saisonalen Marker, um wichtige Termine direkt im Kalender zu sehen: Bewerbungsfristen fuer Highschool-Programme, Abflugzeiten, Schuljahresstart in den Ziellaendern und weitere relevante Daten. WARUM? Content rund um diese Termine erzeugt hohe Relevanz und Dringlichkeit — ideal fuer Fristen-CTAs und Countdown-Posts. Die Marker sind farblich nach Kategorie kodiert.',
        position: 'bottom',
      },
      // Tour-Step 7: Content-Mix Panel erklaeren
      {
        target: '[data-tour="cal-mix"]',
        title: 'Content-Mix: Ausgewogene Kategorien',
        description:
          'Das Content-Mix-Panel analysiert die Verteilung deiner Posts nach Kategorie, Plattform und Land. WARUM? Ein ausgewogener Content-Mix sorgt dafuer, dass du nicht nur Laender-Spotlights postest, sondern auch Erfahrungsberichte, FAQ, Tipps und CTAs abwechselst. So sprichst du verschiedene Zielgruppen an und haltst deinen Feed abwechslungsreich. Das Panel zeigt Prozentwerte und Balkendiagramme fuer den aktuellen Monat.',
        position: 'bottom',
      },
      // Tour-Step 8: Story-Arc Timeline erklaeren
      {
        target: '[data-tour="cal-arcs"]',
        title: 'Story-Arc Timeline: Serien visualisieren',
        description:
          'Die Story-Arc-Timeline zeigt deine mehrteiligen Content-Serien als farbige Balken oberhalb des Kalenders. Jeder Balken repraesentiert eine Serie mit Episoden-Punkten an den geplanten Terminen. WARUM? So erkennst du auf einen Blick, ob alle Episoden terminiert sind, ob die Reihenfolge stimmt und ob genuegend Abstand zwischen den Teilen liegt. Klicke auf einen Episoden-Punkt, um direkt zum Post-Editor zu springen.',
        position: 'bottom',
      },
    ],
  },

  // ─── History ─────────────────────────────────────────────
  history: {
    title: 'Post-Verlauf Tour',
    steps: [
      {
        target: '[data-tour="history-filters"]',
        title: 'Filter & Suche',
        description:
          'Durchsuche deine Posts nach Titel, filtere nach Kategorie, Plattform, Status, Land oder Datum.',
        position: 'bottom',
      },
      {
        target: '[data-tour="history-list"]',
        title: 'Post-Liste',
        description:
          'Hier siehst du alle erstellten Posts mit Vorschaubild, Titel, Status und Aktionen (Bearbeiten, Duplizieren, Loeschen).',
        position: 'top',
      },
    ],
  },

  // ─── Analytics ───────────────────────────────────────────
  analytics: {
    title: 'Analytics Tour',
    steps: [
      {
        target: '[data-tour="analytics-header"]',
        title: 'Dein Content-Dashboard',
        description:
          'Behalte den Ueberblick ueber deine Posting-Aktivitaet, Ziel-Erreichung und Content-Mix.',
        position: 'bottom',
      },
      {
        target: '[data-tour="analytics-charts"]',
        title: 'Charts & Statistiken',
        description:
          'Visualisiere deine Posting-Frequenz, Kategorie-Verteilung und Plattform-Aufteilung ueber verschiedene Zeitraeume.',
        position: 'top',
      },
    ],
  },

  // ─── Settings ────────────────────────────────────────────
  settings: {
    title: 'Einstellungen Tour',
    steps: [
      {
        target: '[data-tour="settings-sections"]',
        title: 'Einstellungen verwalten',
        description:
          'Passe dein Profil, Branding-Farben, API-Schluessel, Posting-Ziele, Hashtag-Strategien und Tour-Einstellungen an.',
        position: 'bottom',
      },
    ],
  },

  // ─── Students ────────────────────────────────────────────
  students: {
    title: 'Schueler Tour – Deine Schueler-Datenbank',
    steps: [
      // Tour-Step 1: Warum eine Schueler-Datenbank (echte Geschichten = bester Content)
      {
        target: '[data-tour="students-header"]',
        title: 'Warum eine Schueler-Datenbank?',
        description:
          'Echte Geschichten von echten Austausch-Schuelern sind der beste Content fuer Social Media! Die Schueler-Datenbank ist das Herzstuck deiner Content-Strategie: Hier sammelst du alle Infos ueber deine Teilnehmer — Name, Land, Schule, Gastfamilie, Bio und Fun-Facts. Diese Daten fliessen automatisch in die KI-Textgenerierung ein, sodass jeder Post authentisch und persoenlich klingt. Statt generischer Werbung erstellst du so echte Erfahrungsberichte, die Teenager und Eltern gleichermassen ansprechen.',
        position: 'bottom',
      },
      // Tour-Step 2: Schueler anlegen erklaeren (Name, Land, Bio, Fun-Facts)
      {
        target: '[data-tour="students-add-btn"]',
        title: 'Schueler anlegen: Name, Land, Bio & Fun-Facts',
        description:
          'Klicke auf "Student hinzufuegen", um ein neues Profil zu erstellen. Pflichtfelder sind Name und Land — alles andere ist optional, macht den Content aber deutlich besser! Stadt und Schule geben Kontext ("Kitsilano Secondary in Vancouver"), die Gastfamilie personalisiert Stories, und Fun-Facts ("Spielt Eishockey", "Liebt Poutine") machen Posts nahbar und unterhaltsam. Je mehr Details du eintraegst, desto authentischer und vielfaeltiger werden die KI-generierten Texte.',
        position: 'bottom',
      },
      // Tour-Step 3: Persoenlichkeits-Presets erklaeren
      {
        target: '[data-tour="students-personality"]',
        title: 'Persoenlichkeits-Presets: Tonalitaet steuern',
        description:
          'Jeder Schueler bekommt ein Persoenlichkeits-Preset, das die KI-Textgenerierung steuert. Waehle einen Ton (z.B. witzig 😂, emotional 🥺, motivierend 💪, jugendlich ✨, storytelling 📖) und einen Humor-Level (1-5). WARUM? So klingt jeder Schueler in Posts anders und authentisch — ein witziger Schueler schreibt locker, ein emotionaler teilt Heimweh-Geschichten. Das Preset wird automatisch an die KI uebergeben, wenn du Posts fuer diesen Schueler erstellst.',
        position: 'top',
      },
      // Tour-Step 4: Zusammenhang mit Story-Arcs erklaeren (Schueler sind Hauptfiguren)
      {
        target: '[data-tour="students-story-arc-hint"]',
        title: 'Story-Arcs: Schueler als Hauptfiguren',
        description:
          'Schueler sind die Hauptfiguren deiner Content-Serien (Story-Arcs)! Ein Story-Arc erzaehlt die Geschichte eines Schuelers ueber mehrere Posts hinweg — z.B. "Lisas erstes Semester in Neuseeland" mit Episoden wie Ankunft, erster Schultag, Gastfamilien-Alltag und Abschied. Jeder Arc wird einem Schueler zugeordnet und nutzt dessen Profil-Daten und Persoenlichkeits-Preset. Gehe nach dem Anlegen von Schuelern zu "Story-Arcs", um mehrteilige Serien zu erstellen!',
        position: 'bottom',
      },
      // Tour-Step 5: Wie Schueler-Daten in Posts einfliessen
      {
        target: '[data-tour="students-list"]',
        title: 'Wie Schueler-Daten in Posts einfliessen',
        description:
          'Wenn du im Post-Wizard einen Schueler auswaehlst, passiert Folgendes: Die KI erhaelt automatisch Name, Land, Stadt, Schule, Bio, Fun-Facts und das Persoenlichkeits-Preset als Kontext. Daraus generiert sie personalisierte Texte wie "Jonathan erzaehlt von seinem Alltag an der Kitsilano Secondary in Vancouver" statt generischem "Ein Schueler berichtet...". Je mehr Schueler mit detaillierten Profilen du hier anlegst, desto abwechslungsreicher und authentischer wird dein gesamter Content-Feed!',
        position: 'top',
      },
    ],
  },

  // ─── Story Arcs (6-Step Detailed Tour) ──────────────────
  'story-arcs': {
    title: 'Story-Arcs Tour – Serien-Content',
    steps: [
      // Tour-Step 1: Was sind Story-Arcs und warum sind sie wichtig (Follower kommen zurueck)
      {
        target: '[data-tour="arcs-header"]',
        title: 'Was sind Story-Arcs? (Und warum sie Gold wert sind)',
        description:
          'Story-Arcs sind mehrteilige Content-Serien, z.B. "Lenas Abenteuer in Kanada" als 8-teilige Serie. WARUM? Serien-Content ist der staerkste Hebel fuer Follower-Bindung: Wer Teil 1 sieht, will Teil 2 sehen — und kommt aktiv zurueck! Das steigert die Verweildauer, die Algorithmus-Reichweite und baut eine emotionale Verbindung auf. Jede Serie erzaehlt die echte Geschichte eines TREFF-Teilnehmers.',
        position: 'bottom',
      },
      // Tour-Step 2: Story-Arc-Uebersicht erklaeren (Status, Fortschritt)
      {
        target: '[data-tour="arcs-stats"]',
        title: 'Story-Arc-Uebersicht: Status & Fortschritt',
        description:
          'Diese Statistik-Karten zeigen dir auf einen Blick den Stand aller Serien: Wie viele sind aktiv (laufen gerade), pausiert (temporaer gestoppt), als Entwurf (noch in Planung) oder bereits abgeschlossen. So behaelst du den Ueberblick, welche Serien Aufmerksamkeit brauchen und wo neue Episoden faellig sind.',
        position: 'bottom',
      },
      // Tour-Step 3: Story-Arc-Wizard erklaeren (Schueler waehlen, Episoden planen)
      {
        target: '[data-tour="arcs-wizard-btn"]',
        title: 'Story-Arc-Wizard: Neue Serie erstellen',
        description:
          'Klicke hier, um eine neue Serie zu erstellen. Der Wizard fuehrt dich Schritt fuer Schritt: Waehle einen Schueler als Protagonisten, lege Titel und Handlungsbogen fest, plane die Anzahl der Episoden, weise ein Zielland zu und definiere den Erzaehlton (emotional, informativ, humorvoll). Jede Serie bekommt automatisch eine Fortschrittsanzeige und Episoden-Nummerierung.',
        position: 'bottom',
      },
      // Tour-Step 4: Episoden-Management erklaeren
      {
        target: '[data-tour="arcs-list"]',
        title: 'Episoden-Management: Deine Serien im Ueberblick',
        description:
          'Jede Karte zeigt eine Serie mit Cover-Bild, Status-Badge, Laender-Flagge, Schueler-Name und Fortschrittsbalken (z.B. 3/8 Episoden). Klicke auf eine Karte, um die Detail-Ansicht zu oeffnen — dort kannst du einzelne Episoden verwalten, den Status aendern (aktiv/pausiert/abgeschlossen) und die Reihenfolge anpassen. Neue Episoden erstellst du direkt als Posts im Post-Wizard.',
        position: 'top',
      },
      // Tour-Step 5: Zusammenhang mit Kalender erklaeren (Episoden werden eingeplant)
      {
        target: '[data-tour="arcs-filters"]',
        title: 'Zusammenhang mit Kalender: Episoden einplanen',
        description:
          'Die Filter helfen dir, Serien nach Status, Land oder Schueler zu finden. Der wichtigste Zusammenhang: Jede Episode einer Serie wird als regulaerer Post im Kalender eingeplant! Nutze den Wochenplaner, um Episoden auf bestimmte Tage zu terminieren — er beruecksichtigt automatisch, welche Episoden als naechstes faellig sind. So verpasst du keine Fortsetzung und haelst deine Follower bei der Stange.',
        position: 'bottom',
      },
      // Tour-Step 6: Zusammenhang mit Students erklaeren
      {
        target: '[data-tour="arcs-students-hint"]',
        title: 'Zusammenhang mit Schuelern: Persoenliche Geschichten',
        description:
          'Jede Story-Serie ist mit einem Schueler-Profil verknuepft (z.B. "Lena, 16, USA"). Das Profil liefert automatisch den Namen, das Zielland, die Schule und die Persoenlichkeit fuer die KI-Textgenerierung. So klingen alle Episoden einer Serie konsistent und authentisch. Tipp: Lege zuerst Schueler-Profile unter "Schueler" an, damit du sie hier als Protagonisten auswaehlen kannst!',
        position: 'bottom',
      },
    ],
  },

  // ─── Week Planner ────────────────────────────────────────
  'week-planner': {
    title: 'Wochenplaner Tour – KI-gestuetzter Content-Planer',
    steps: [
      // Tour-Step 1: Was ist der Wochenplaner
      {
        target: '[data-tour="wp-header"]',
        title: 'Was ist der Wochenplaner?',
        description:
          'Der Wochenplaner ist dein KI-gestuetzter Content-Assistent: Er analysiert deine bisherigen Posts, aktive Story-Serien, wiederkehrende Formate und saisonale Themen — und generiert daraus automatisch einen ausgewogenen Wochenplan mit optimalen Posting-Zeiten. Statt stundenlang zu planen, erhaelst du in Sekunden einen kompletten Plan fuer die ganze Woche!',
        position: 'bottom',
      },
      // Tour-Step 2: Filter erklaeren (Saison, Land, Kategorie)
      {
        target: '[data-tour="wp-filters"]',
        title: 'Filter: Saison, Land & Formate',
        description:
          'Hier steuerst du, was die KI beruecksichtigen soll: Waehle die Woche per Datumspicker oder Pfeil-Buttons, bestimme die Anzahl der Posts (2-7 pro Woche) und aktiviere die Checkboxen fuer "Wiederkehrende Formate" (z.B. Motivation Monday, Freitags-Fail) und "Story-Serien" (laufende mehrteilige Serien). Die KI beruecksichtigt automatisch die aktuelle Saison und rotiert Laender gleichmaessig.',
        position: 'bottom',
      },
      // Tour-Step 3: AI-Generierung starten erklaeren
      {
        target: '[data-tour="wp-generate"]',
        title: 'KI-Generierung starten',
        description:
          'Klicke auf "Plan generieren", um die KI loszuschicken! Sie prueft bereits geplante Posts fuer die gewaehlte Woche (damit nichts doppelt wird), beruecksichtigt aktive Story-Arcs und deren naechste faellige Episoden, schlaegt wiederkehrende Formate am richtigen Wochentag vor und fuellt die restlichen Slots mit einem ausgewogenen Mix aus Kategorien und Laendern. Das Ergebnis: Ein 7-Tage-Raster mit konkreten Vorschlaegen.',
        position: 'bottom',
      },
      // Tour-Step 4: Drag-and-Drop Tages-Slots erklaeren
      {
        target: '[data-tour="wp-grid"]',
        title: 'Drag & Drop: Tages-Slots anpassen',
        description:
          'Jede Spalte steht fuer einen Wochentag (Montag bis Sonntag). Die farbigen Karten sind Content-Vorschlaege mit Kategorie, Plattform, Land und Uhrzeit. Du kannst sie frei per Drag & Drop zwischen den Tagen verschieben — z.B. einen Post von Montag auf Mittwoch ziehen. Klicke das X auf einer Karte, um einen Vorschlag zu entfernen. Bereits geplante Posts (mit Pin-Icon) werden angezeigt, sind aber nicht verschiebbar.',
        position: 'top',
      },
      // Tour-Step 5: 'In Kalender uebernehmen' erklaeren
      {
        target: '[data-tour="wp-adopt"]',
        title: 'Plan in den Kalender uebernehmen',
        description:
          'Wenn du mit dem Plan zufrieden bist, klicke "Plan uebernehmen" — alle Vorschlaege werden als geplante Entwuerfe im Content-Kalender erstellt. Die Posts erhalten automatisch das richtige Datum, die Uhrzeit, Kategorie, Land und Plattform. Serien-Episoden werden mit der korrekten Story-Arc-ID und Episodennummer verknuepft. Nach der Uebernahme wirst du direkt zum Kalender weitergeleitet, wo du die Posts weiter bearbeiten kannst.',
        position: 'bottom',
      },
      // Tour-Step 6: Zusammenhang mit Kalender und Recurring Formats erklaeren
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
      // Tour-Step 1: Was sind wiederkehrende Formate (regelmaessige Rubriken)
      {
        target: '[data-tour="formats-header"]',
        title: 'Was sind wiederkehrende Formate?',
        description:
          'Wiederkehrende Formate sind regelmaessige Content-Rubriken fuer deine Social-Media-Kanaele — wie "Motivation Monday", "Freitags-Fail" oder "Throwback Thursday". WARUM? Feste Rubriken schaffen Wiedererkennungswert bei deinem Publikum und geben dir eine klare Struktur fuer die Woche. Follower wissen, was sie erwarten koennen, und kommen gezielt zurueck. Hier verwaltest du alle deine Formate zentral.',
        position: 'bottom',
      },
      // Tour-Step 2: Format erstellen erklaeren (Name, Frequenz, Ton, Hashtags)
      {
        target: '[data-tour="formats-create"]',
        title: 'Format erstellen: Name, Frequenz & Ton',
        description:
          'Klicke auf "+ Neues Format", um ein eigenes Format anzulegen. Vergib einen einpraegsamen Namen (z.B. "Wusstest-du-Mittwoch"), waehle die Haeufigkeit (taeglich, woechentlich, alle 2 Wochen, monatlich), lege den bevorzugten Wochentag und die Uhrzeit fest, und bestimme die Tonalitaet (jugendlich, witzig, emotional, motivierend, informativ, serioess). Eigene Hashtags werden automatisch bei jedem Post dieses Formats vorgeschlagen — so bleibt dein Branding konsistent.',
        position: 'bottom',
      },
      // Tour-Step 3: AI-Preview erklaeren
      {
        target: '[data-tour="formats-ai-preview"]',
        title: 'KI-Textvorschlag: AI-Preview',
        description:
          'Der "KI-Text"-Button oeffnet die KI-Textgenerierung fuer dieses Format. Gib optional ein Thema (z.B. "Trinkgeld-Kultur in den USA") und ein Zielland ein — die KI generiert dann einen passenden Titel, Caption-Text und Hashtags im Stil des Formats. WARUM? So bekommst du in Sekunden Content-Ideen, die zum Ton und Thema deines Formats passen. Die Vorschlaege lassen sich direkt im Post-Editor weiterverwenden.',
        position: 'top',
      },
      // Tour-Step 4: Zusammenhang mit Kalender und Wochenplaner erklaeren
      {
        target: '[data-tour="formats-info"]',
        title: 'Kalender & Wochenplaner: Automatische Integration',
        description:
          'Aktive Formate werden automatisch im Content-Kalender als Platzhalter am bevorzugten Wochentag angezeigt. Der KI-Wochenplaner beruecksichtigt deine Formate und schlaegt passende Posts fuer die richtigen Tage vor — z.B. einen "Motivation Monday"-Post am Montag. WARUM? So musst du nicht jede Woche neu ueberlegen, welchen Content du wann postest. Die Formate bilden das Geruest deiner Content-Strategie und fuellen automatisch Luecken im Kalender.',
        position: 'top',
      },
      // Tour-Step 5: Best Practices erklaeren (nicht zu viele, 2-3 pro Woche ideal)
      {
        target: '[data-tour="formats-list"]',
        title: 'Best Practices: Die richtige Balance',
        description:
          'Tipp: Starte mit 2-3 wiederkehrenden Formaten pro Woche — das ist ideal fuer Konsistenz ohne Ueberbelastung. Zu viele Formate fuehlen sich fuer Follower repetitiv an und schraenken deine Flexibilitaet fuer aktuelle Themen ein. Beispiel-Woche: Montag = "Motivation Monday" (motivierend), Mittwoch = "Wusstest-du-Mittwoch" (informativ), Freitag = "Freitags-Fail" (witzig). Deaktiviere Formate voruebergehend statt sie zu loeschen — so kannst du sie spaeter einfach reaktivieren.',
        position: 'bottom',
      },
    ],
  },

  // ─── Video Export ────────────────────────────────────────
  'video-export': {
    title: 'Video-Export Tour',
    steps: [
      {
        target: '[data-tour="ve-header"]',
        title: 'Video-Export',
        description:
          'Exportiere deine Videos in verschiedenen Seitenverhaeltnissen (9:16, 1:1, 4:5) fuer Instagram Reels, Feed und TikTok.',
        position: 'bottom',
      },
    ],
  },

  // ─── Audio Mixer ─────────────────────────────────────────
  'audio-mixer': {
    title: 'Audio-Mixer Tour',
    steps: [
      {
        target: '[data-tour="am-header"]',
        title: 'Audio-Mixer',
        description:
          'Fuege Hintergrundmusik und Audio-Layer zu deinen Videos hinzu. Waehle aus der Musik-Bibliothek oder lade eigene Tracks hoch.',
        position: 'bottom',
      },
    ],
  },

  // ─── Thumbnail Generator ─────────────────────────────────
  'thumbnail-generator': {
    title: 'Thumbnail-Generator Tour',
    steps: [
      {
        target: '[data-tour="tg-header"]',
        title: 'Thumbnails erstellen',
        description:
          'Erstelle ansprechende Thumbnails fuer deine Videos und Reels mit Text-Overlays, TREFF-Branding und verschiedenen Layouts.',
        position: 'bottom',
      },
    ],
  },
}

export default tourConfigs
