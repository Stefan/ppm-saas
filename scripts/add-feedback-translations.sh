#!/bin/bash

# This script adds feedback translations to all 6 language files
# It's a template - actual translations should be reviewed by native speakers

echo "🌍 Adding feedback translations to all language files..."

# The translations will be added programmatically
# For now, documenting the structure needed

cat << 'EOF'

Feedback Translation Structure Needed:
=====================================

German (de.json):
- feedback.title: "Feedback & Ideen"
- feedback.subtitle: "Teilen Sie Ihre Ideen und melden Sie Probleme, um die Plattform zu verbessern"
- feedback.suggestFeature: "Feature vorschlagen"
- feedback.reportBug: "Fehler melden"

French (fr.json):
- feedback.title: "Commentaires & Idées"
- feedback.subtitle: "Partagez vos idées et signalez les problèmes pour améliorer la plateforme"
- feedback.suggestFeature: "Suggérer une fonctionnalité"
- feedback.reportBug: "Signaler un bug"

Spanish (es.json):
- feedback.title: "Comentarios e Ideas"
- feedback.subtitle: "Comparte tus ideas y reporta problemas para mejorar la plataforma"
- feedback.suggestFeature: "Sugerir Función"
- feedback.reportBug: "Reportar Error"

Polish (pl.json):
- feedback.title: "Opinie i Pomysły"
- feedback.subtitle: "Podziel się swoimi pomysłami i zgłoś problemy, aby pomóc ulepszyć platformę"
- feedback.suggestFeature: "Zaproponuj Funkcję"
- feedback.reportBug: "Zgłoś Błąd"

Swiss German (gsw.json):
- feedback.title: "Feedback & Idee"
- feedback.subtitle: "Teil dyni Idee und mäld Problem zum d Plattform verbessere"
- feedback.suggestFeature: "Feature vorschlaa"
- feedback.reportBug: "Fähler mälde"

EOF

echo "✅ Translation structure documented"
echo "⚠️  Manual addition required for quality assurance"
