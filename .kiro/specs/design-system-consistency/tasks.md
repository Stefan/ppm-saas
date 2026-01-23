# Implementation Plan: Design System Consistency

## Overview

Dieser Plan beschreibt die schrittweise Implementierung eines konsistenten Designsystems für die ORKA PPM App. Die Implementierung erfolgt in vier Phasen: Design Token Setup, Basis-Komponenten, Testing-Infrastruktur und Migration bestehender Komponenten.

## Tasks

- [x] 1. Design Token System einrichten
  - [x] 1.1 Tailwind Config mit Design Tokens erweitern
    - Farb-Paletten (primary, neutral, semantic) in `tailwind.config.ts` definieren
    - Spacing-Scale (0-16 in 4px-Schritten) konfigurieren
    - Typografie-Tokens (fontSize, fontWeight, lineHeight) definieren
    - Shadow- und Border-Radius-Werte konfigurieren
    - Responsive Breakpoints (mobile, tablet, desktop) definieren
    - _Requirements: 4.1, 5.1, 5.2, 5.3, 6.1, 6.2, 6.4, 8.1, 9.1, 9.4_
  
  - [x] 1.2 CSS Custom Properties in design-system.css definieren
    - CSS-Variablen für Farben erstellen
    - CSS-Variablen für Spacing erstellen
    - CSS-Variablen für Typografie erstellen
    - _Requirements: 9.1_
  
  - [x] 1.3 TypeScript-Typen für Design Tokens erstellen
    - `types/design-system.ts` mit ColorScale, SemanticColors, SpacingScale erstellen
    - DesignTokens Interface definieren
    - `types/components.ts` mit ButtonVariant, ComponentSize, ShadowSize erstellen
    - _Requirements: 9.1_

- [x] 2. Utility-Funktionen implementieren
  - [x] 2.1 cn-Funktion in lib/design-system.ts implementieren
    - clsx und tailwind-merge installieren
    - cn-Funktion implementieren, die beide kombiniert
    - TypeScript-Typen für ClassValue exportieren
    - _Requirements: 10.3_
  
  - [x] 2.2 Unit-Tests für cn-Funktion schreiben
    - Test: cn kombiniert mehrere Klassen korrekt
    - Test: cn löst Tailwind-Konflikte auf (z.B. px-4 überschreibt px-2)
    - Test: cn behandelt bedingte Klassen korrekt
    - _Requirements: 10.3_

- [x] 3. Button-Komponente implementieren
  - [x] 3.1 Button-Komponente in components/ui/button.tsx erstellen
    - ButtonProps Interface mit variant, size, disabled definieren
    - buttonVariants Objekt mit allen Varianten-Kombinationen erstellen
    - buttonBaseStyles mit Focus-Ring, Border-Radius, Transitions definieren
    - Button-Komponente mit cn-Funktion implementieren
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_
  
  - [x] 3.2 Property-Tests für Button-Komponente schreiben
    - **Property 1: Button-Varianten sind auf definierte Werte beschränkt**
    - **Validates: Requirements 1.1**
  
  - [x] 3.3 Property-Test für Button-Größen schreiben
    - **Property 2: Button-Größen sind auf definierte Werte beschränkt**
    - **Validates: Requirements 1.7**
  
  - [x] 3.4 Property-Test für Button-Farben schreiben
    - **Property 4: Button-Farben stammen aus Design Tokens**
    - **Validates: Requirements 1.3**
  
  - [x] 3.5 Property-Test für Button Hover-States schreiben
    - **Property 5: Buttons haben Hover-States**
    - **Validates: Requirements 1.4**
  
  - [x] 3.6 Property-Test für Button Focus-Rings schreiben
    - **Property 7: Interaktive Elemente haben Focus-Rings**
    - **Validates: Requirements 1.6**
  
  - [x] 3.7 Property-Test für Button Disabled-State schreiben
    - **Property 16: Disabled Buttons haben visuell erkennbaren State**
    - **Validates: Requirements 7.3**
  
  - [x] 3.8 Unit-Tests für Button-Komponente schreiben
    - Test: Button rendert mit primary Variante korrekt
    - Test: Button rendert mit allen Größen korrekt
    - Test: Button ist disabled wenn disabled=true
    - Test: Button akzeptiert custom className
    - Test: Button leitet onClick-Handler korrekt weiter
    - _Requirements: 1.1, 1.7, 7.3_

- [x] 4. Input-Komponente implementieren
  - [x] 4.1 Input-Komponente in components/ui/input.tsx erstellen
    - InputProps Interface mit size, error, errorMessage, label definieren
    - inputVariants Objekt mit Größen-Varianten erstellen
    - inputBaseStyles mit Border, Focus-Ring, Placeholder-Farbe definieren
    - inputErrorStyles für Error-State definieren
    - Input-Komponente mit Label und Fehlermeldung implementieren
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  
  - [x] 4.2 Property-Tests für Input-Komponente schreiben
    - **Property 8: Input-Größen sind auf definierte Werte beschränkt**
    - **Validates: Requirements 2.6**
  
  - [x] 4.3 Property-Test für Input Border-Style schreiben
    - **Property 9: Input hat einheitlichen Border-Style**
    - **Validates: Requirements 2.2**
  
  - [x] 4.4 Property-Test für Input Placeholder-Kontrast schreiben
    - **Property 10: Placeholder-Farbe erfüllt Kontrast-Anforderungen**
    - **Validates: Requirements 2.4**
  
  - [x] 4.5 Property-Test für Input Error-State schreiben
    - **Property 11: Input im Error-State zeigt visuelles Feedback**
    - **Validates: Requirements 2.5**
  
  - [x] 4.6 Unit-Tests für Input-Komponente schreiben
    - Test: Input rendert mit Label korrekt
    - Test: Input zeigt Fehlermeldung bei error=true
    - Test: Input akzeptiert alle Standard-HTML-Input-Props
    - Test: Input rendert mit allen Größen korrekt
    - _Requirements: 2.5, 2.6_

- [x] 5. Card-Komponente implementieren
  - [x] 5.1 Card-Komponente in components/ui/card.tsx erstellen
    - CardProps Interface mit padding, shadow, border definieren
    - CardHeaderProps und CardContentProps Interfaces definieren
    - cardVariants Objekt mit padding und shadow Varianten erstellen
    - Card, CardHeader, CardContent Komponenten implementieren
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [x] 5.2 Property-Tests für Card-Komponente schreiben
    - **Property 12: Card verwendet Shadow aus Design Tokens**
    - **Validates: Requirements 3.2**
  
  - [x] 5.3 Property-Test für CardHeader schreiben
    - **Property 13: CardHeader hat konsistente Styles**
    - **Validates: Requirements 3.4**
  
  - [x] 5.4 Property-Test für Card Border schreiben
    - **Property 14: Card mit Border verwendet konsistente Border-Styles**
    - **Validates: Requirements 3.5**
  
  - [x] 5.5 Unit-Tests für Card-Komponente schreiben
    - Test: Card rendert mit allen Padding-Varianten korrekt
    - Test: Card rendert mit allen Shadow-Varianten korrekt
    - Test: Card zeigt Border bei border=true
    - Test: CardHeader rendert mit Bottom-Border
    - Test: Card mit CardHeader und CardContent rendert korrekt
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 6. Checkpoint - Basis-Komponenten testen
  - Alle Property-Tests und Unit-Tests für Button, Input, Card ausführen
  - Sicherstellen, dass alle Tests bestehen
  - Bei Problemen: Komponenten anpassen und erneut testen
  - Fragen an den Benutzer stellen, falls Unklarheiten auftreten

- [x] 7. Übergreifende Property-Tests implementieren
  - [x] 7.1 Property-Test für Spacing-Konsistenz schreiben
    - **Property 3: Alle Komponenten verwenden Spacing aus Design Tokens**
    - **Validates: Requirements 1.2, 2.1, 3.1, 4.2**
  
  - [x] 7.2 Property-Test für Border-Radius-Konsistenz schreiben
    - **Property 6: Alle Komponenten verwenden Border-Radius aus Design Tokens**
    - **Validates: Requirements 1.5, 3.3**
  
  - [x] 7.3 Property-Test für Textfarben-Kontrast schreiben
    - **Property 15: Textfarben erfüllen WCAG AA Kontrast-Anforderungen**
    - **Validates: Requirements 5.4, 6.3, 7.2**
    - Kontrast-Berechnung für alle definierten Textfarben implementieren
    - Mindestens 4.5:1 für normalen Text, 3:1 für großen Text prüfen
  
  - [x] 7.4 Property-Test für Mindestgröße interaktiver Elemente schreiben
    - **Property 17: Interaktive Elemente haben Mindestgröße**
    - **Validates: Requirements 7.4, 8.3**
    - Für Button und Input: kleinste Größe sollte mindestens 44x44px ergeben
  
  - [x] 7.5 Property-Test für keine inline Styles schreiben
    - **Property 18: Komponenten verwenden keine inline Tailwind-Styles**
    - **Validates: Requirements 10.2**
    - Quellcode-Analyse: keine hartcodierten className-Strings in Komponenten

- [x] 8. Storybook-Dokumentation erstellen
  - [x] 8.1 Storybook konfigurieren
    - Storybook für React + Tailwind installieren
    - Tailwind Config in Storybook einbinden
    - _Requirements: N/A (Developer Experience)_
  
  - [x] 8.2 Stories für alle Komponenten erstellen
    - Button.stories.tsx mit allen Varianten und Größen
    - Input.stories.tsx mit allen Zuständen (normal, error, disabled)
    - Card.stories.tsx mit verschiedenen Konfigurationen
    - _Requirements: N/A (Developer Experience)_

- [x] 9. Bestehende Komponenten identifizieren und migrieren
  - [x] 9.1 Audit durchführen: Alle Komponenten mit inkonsistenten Styles finden
    - Suche nach inline className-Strings mit inkonsistenten Werten
    - Liste von zu migrierenden Komponenten erstellen
    - Priorität nach Häufigkeit der Verwendung festlegen
    - _Requirements: 10.1, 10.2_
  
  - [x] 9.2 High-Priority Komponenten migrieren
    - Identifizierte Komponenten auf neue Button/Input/Card-Komponenten umstellen
    - Inline Tailwind-Klassen durch Design System Komponenten ersetzen
    - Funktionalität durch Tests verifizieren
    - _Requirements: 10.1, 10.2, 10.4_
  
  - [x] 9.3 Globale Styles in globals.css aufräumen
    - Redundante Styles entfernen, die jetzt durch Design Tokens abgedeckt sind
    - Basis-Typografie-Styles konsolidieren
    - Sicherstellen, dass nur globale Resets und Basis-Styles bleiben
    - _Requirements: 9.1_

- [x] 10. Final Checkpoint - Vollständige Test-Suite ausführen
  - Alle Property-Tests ausführen (mindestens 100 Iterationen pro Test)
  - Alle Unit-Tests ausführen
  - Visuelle Überprüfung aller Komponenten in verschiedenen Breakpoints
  - Accessibility-Tests mit axe-core durchführen
  - Bei Problemen: Komponenten anpassen und erneut testen
  - Fragen an den Benutzer stellen, falls Unklarheiten auftreten

- [x] 11. ESLint-Rules für Design System Compliance einrichten
  - [x] 11.1 Custom ESLint-Rule erstellen
    - Rule: Warnung bei direkter Verwendung von Tailwind-Farben statt Design Tokens
    - Rule: Warnung bei direkter Verwendung von Spacing-Werten statt Design Tokens
    - _Requirements: 10.4_
  
  - [x] 11.2 ESLint-Config aktualisieren
    - Custom Rules in ESLint-Config einbinden
    - Auto-Fix für einfache Fälle konfigurieren
    - _Requirements: 10.4_

## Notes

- Alle Tasks sind verpflichtend für eine umfassende Implementierung mit vollständiger Test-Abdeckung
- Jeder Task referenziert spezifische Requirements für Nachvollziehbarkeit
- Checkpoints stellen sicher, dass die Implementierung schrittweise validiert wird
- Property-Tests validieren universelle Korrektheitseigenschaften
- Unit-Tests validieren spezifische Beispiele und Edge Cases
- Die Migration bestehender Komponenten erfolgt schrittweise, um Risiken zu minimieren
- Storybook und ESLint-Rules verbessern die Developer Experience und Code-Qualität erheblich
