# Reddit Scraper mit Gemini AI - Setup Anleitung

## 🚀 **Vollständige Einrichtung**

### **1. Reddit API Credentials (bereits eingerichtet ✅)**
- ✅ Reddit App erstellt
- ✅ Credentials funktionieren

### **2. Gemini API Key einrichten**

#### **Schritt 1: Gemini API Key erhalten**
1. Gehe zu: https://makersuite.google.com/app/apikey
2. Logge dich mit deinem Google-Account ein
3. Klicke "Create API Key"
4. Kopiere den generierten API Key

#### **Schritt 2: API Key in Code einfügen**
Öffne `get_reddit.py` und ersetze Zeile 375:
```python
GEMINI_API_KEY = "dein_echter_gemini_api_key_hier"
```

### **3. System starten**

```bash
python3 get_reddit.py
```

## 🎯 **Was das System macht:**

### **Priorisierung der Subreddits:**
1. **Priority 1 (Study Abroad):**
   - r/Indians_StudyAbroad
   - r/studying_in_germany
   - r/tumunich
   - r/LMUMunich
   - r/InternationalStudents
   - r/AskAcademia

2. **Priority 2 (Immigration/Life):**
   - r/IWantOut
   - r/LifeInGermany
   - r/germany

3. **Priority 3 (General Europe):**
   - r/europe

### **Gemini AI Filtering:**
- Analysiert jeden Post und Kommentare
- Filtert nur relevante Inhalte für:
  - Immigration (Visas, Aufenthaltstitel, Staatsbürgerschaft)
  - Studium im Ausland (Bewerbungen, Universitätsprozesse)
  - Administrative/Organisatorische Prozesse
  - Professionelle Beratung für internationale Studenten/Immigranten

### **Sortierung:**
- Posts werden nach Priorität und Datum sortiert
- Neueste Posts zuerst
- Study Abroad Posts haben höchste Priorität

### **Output:**
- Einzelne JSON-Dateien pro Subreddit
- Eine kombinierte, sortierte JSON-Datei mit allen relevanten Posts
- Detaillierte Statistiken nach Priorität

## 📊 **Erwartete Ergebnisse:**
- Posts mit ≥50 Upvotes
- 5 Kommentare pro Post
- Nur relevante Inhalte (gefiltert durch Gemini AI)
- Sortiert nach Datum und Priorität
- Zeitraum: Bis 2022 zurück

## 🔧 **Anpassbare Parameter:**
```python
scraper.scrape_all_subreddits(
    num_upvotes_posts=50,   # Mindest-Upvotes
    num_replies_posts=5,    # Anzahl Kommentare
    limit=50                # Posts pro Subreddit
)
```
