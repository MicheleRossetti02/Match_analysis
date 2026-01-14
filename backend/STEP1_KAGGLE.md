# 🔑 Step 1: Setup Kaggle API Token

## 📍 Stato Attuale
**Browser aperto su:** https://www.kaggle.com/account

---

## ✅ Cosa Fare Ora (3 minuti)

### 1️⃣ Login su Kaggle

Se non sei già loggato:
- Usa Google / Email / GitHub per accedere

### 2️⃣ Vai alla Sezione API

Nella pagina aperta nel browser:
- Scroll down fino a trovare la sezione **"API"**
- Vedrai un bottone **"Create New API Token"**

### 3️⃣ Genera Token

1. Clicca **"Create New API Token"**
2. Si scaricherà automaticamente un file **`kaggle.json`**
3. Il file andrà nella cartella Download

### 4️⃣ Installa il Token

Apri il Terminale ed esegui:

```bash
# Crea directory .kaggle
mkdir -p ~/.kaggle

# Sposta il file
mv ~/Downloads/kaggle.json ~/.kaggle/

# Imposta permessi
chmod 600 ~/.kaggle/kaggle.json
```

### 5️⃣ Verifica Setup

```bash
cd /Users/michelerossetti/Documents/Apps/Match_analysis/backend
./venv/bin/python check_kaggle_setup.py
```

**Output atteso:**
```
✅ Kaggle library installed
✅ Kaggle API token found
✅ Authentication successful!
🎉 KAGGLE IS READY TO USE!
```

---

## 🎯 Dopo questo Step

Una volta completato, dimmi **"fatto"** e passeremo allo **Step 2: Download Dataset**.

---

## 🐛 Problemi?

**File non si scarica?**
- Riprova a cliccare "Create New API Token"
- Controlla la cartella Downloads

**Errore permessi?**
- Assicurati di eseguire `chmod 600`
- Su Windows, salta questo comando

**Autenticazione fallita?**
- Verifica che `kaggle.json` sia in `~/.kaggle/`
- Controlla il contenuto del file (deve essere JSON valido)
