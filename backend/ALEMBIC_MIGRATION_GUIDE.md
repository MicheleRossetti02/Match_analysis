# Sprint 3: Alembic Database Migration Guide

## Installazione Alembic

```bash
cd backend
pip install alembic
# oppure
pip install -r requirements.txt  # se alembic è già presente
```

## Setup Completato

✅ **Configurazione Alembic** preparata:
- `alembic.ini`: Configurazione principale (connessione SQLite)
- `alembic/env.py`: Collegamento ai modelli SQLAlchemy
- `alembic/script.py.mako`: Template per le migrazioni
- `alembic/versions/`: Directory per i file di migrazione

## Generazione Prima Migrazione

### Step 1: Migrazione Iniziale (Baseline)
```bash
cd backend
alembic revision --autogenerate -m "initial_schema_with_sprint1_2_features"
```

Questo genera:
- File in `alembic/versions/xxx_initial_schema.py`
- Include tutte le 18 nuove colonne:
  - **Sprint 1**: recency_weighted_points, xG features, momentum
  - **Sprint 2**: DC (5 colonne), Combo (8 colonne), Accuracy tracking (12 colonne)

### Step 2: Revisione Manuale
```bash
# Aprire il file generato in alembic/versions/
# Verificare che le 18 colonne siano presenti
```

### Step 3: Applicare la Migrazione
```bash
alembic upgrade head
```

### Step 4: Verifica
```bash
alembic current  # Mostra versione corrente
alembic history  # Mostra storico migrazioni
```

## Rollback (se necessario)
```bash
alembic downgrade -1  # Torna indietro di 1 versione
alembic downgrade base  # Torna all'inizio
```

## Comandi Utili

```bash
# Stato attuale
alembic current

# Storico completo
alembic history --verbose

# Crea migrazione vuota (per modifiche manuali)
alembic revision -m "custom_migration"

# Genera SQL senza applicare
alembic upgrade head --sql

# Test offline (genera SQL)
alembic upgrade head --sql > migration.sql
```

## Prossime Migrazioni

Quando modifichi `database.py`:
```bash
# 1. Modifica src/models/database.py
# 2. Genera migrazione automatica
alembic revision --autogenerate -m "add_new_column"
# 3. Revisiona il file generato
# 4. Applica
alembic upgrade head
```

## Note Importanti

⚠️ **SEMPRE** revisionare manualmente le migrazioni autogenerate prima di applicarle

✅ **Backuppare** il database prima di migrazioni in produzione

📝 **Versionare** i file di migrazione in Git

🔄 **Testare** rollback prima di deployare in produzione

## Integrazione con migrate_db.py

`migrate_db.py` può rimanere per backward compatibility, ma:
- ❌ Non usarlo per nuove modifiche
- ✅ Usa Alembic per tutte le future migrazioni
- 📅 Pianifica deprecazione di migrate_db.py dopo Sprint 3
