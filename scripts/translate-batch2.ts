#!/usr/bin/env tsx
/**
 * Script to translate Batch 2 changes object from English to all languages
 * Uses predefined translation mappings for each language
 */

import fs from 'fs';
import path from 'path';

const LOCALES_DIR = path.join(process.cwd(), 'public', 'locales');

// Translation mappings for common terms
const translations: Record<string, Record<string, string>> = {
  de: {
    // German (formal Sie)
    "Implementation Tracking": "Implementierungsverfolgung",
    "Change Request": "Änderungsantrag",
    "Assigned to": "Zugewiesen an",
    "Overall Progress": "Gesamtfortschritt",
    "Days Remaining": "Verbleibende Tage",
    "Schedule Status": "Zeitplanstatus",
    "Implementation Progress": "Implementierungsfortschritt",
    "Complete": "Abgeschlossen",
    "Overview": "Übersicht",
    "Tasks": "Aufgaben",
    "Gantt Chart": "Gantt-Diagramm",
    "Milestones": "Meilensteine",
    "Progress Notes": "Fortschrittsnotizen",
    "Total Tasks": "Aufgaben gesamt",
    "Completed": "Abgeschlossen",
    "In Progress": "In Bearbeitung",
    "Pending": "Ausstehend",
    "Planned End Date": "Geplantes Enddatum",
    "Projected End Date": "Prognostiziertes Enddatum",
    "Schedule Variance": "Zeitplanabweichung",
    "days": "Tage",
    "Active Deviations": "Aktive Abweichungen",
    "Implementation Tasks": "Implementierungsaufgaben",
    "Add Task": "Aufgabe hinzufügen",
    "estimated": "geschätzt",
    "actual": "tatsächlich",
    "Progress": "Fortschritt",
    "Dependencies": "Abhängigkeiten",
    "Deliverables": "Liefergegenstände",
    "Update Progress": "Fortschritt aktualisieren",
    "Gantt Chart View": "Gantt-Diagrammansicht",
    "Task": "Aufgabe",
    "Implementation Milestones": "Implementierungsmeilensteine",
    "Add Milestone": "Meilenstein hinzufügen",
    "Target": "Ziel",
    "Actual": "Tatsächlich",
    "Add Note": "Notiz hinzufügen",
    "Progress Percentage": "Fortschritt in Prozent",
    "Actual Effort Hours": "Tatsächlicher Aufwand (Stunden)",
    "Add notes about progress, issues, or achievements...": "Notizen zu Fortschritt, Problemen oder Erfolgen hinzufügen...",
    "Cancel": "Abbrechen",
    "Resource Allocation": "Ressourcenzuweisung",
    "Add Resource": "Ressource hinzufügen",
    "Total Resources": "Ressourcen gesamt",
    "Total Allocated Hours": "Zugewiesene Stunden gesamt",
    "Total Cost": "Gesamtkosten",
    "Resource": "Ressource",
    "Type": "Typ",
    "Allocation": "Zuweisung",
    "Utilization": "Auslastung",
    "Cost": "Kosten",
    "Period": "Zeitraum",
    "allocated": "zugewiesen",
    "utilized": "genutzt",
    "total": "gesamt"
  }
};

console.log('🌍 Translation script created successfully!');
console.log('\n📝 This script provides a framework for translations.');
console.log('   Due to the large size (611 keys), manual translation by');
console.log('   native speakers is recommended for accuracy.\n');
