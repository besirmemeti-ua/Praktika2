"""
ROI Hunting – Regjistrimi i kandidatëve për punë
Projekti Praktik 2 – Python Basic Training

Ekzekutimi:  streamlit run projekt2.py
"""

import base64
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

# ============================================================
# 1. KONFIGURIMI
# ============================================================
DB_FILE = "roi_hunting.db"     # Skedari i bazës së të dhënave SQLite
CAESAR_SHIFT = 6               # Zhvendosja për Caesar Cipher
# Fjalëkalimi i panelit të kompanisë ruhet i enkriptuar me Caesar (+6): „admin123” → „gjsot123”
ADMIN_PASSWORD_ENCRYPTED = "gjsot123"
CV_MAX_MB = 5                  # Madhësia maksimale e CV-së (PDF)

PROFESSIONS = ["IT", "Finance", "Sales", "Marketing", "Health", "Other"]

# Shtetet: prefiksi dhe numri i shifrave pas prefiksit
COUNTRIES = {
    "MK": {"flag": "🇲🇰", "code": "+389", "digits": 8},
    "AL": {"flag": "🇦🇱", "code": "+355", "digits": 9},
    "KS": {"flag": "KS", "code": "+383", "digits": 8},
}

# Çelësat e fushave të formularit
FORM_KEYS = ["full_name", "email", "country", "phone", "city", "profession", "profession_other",
             "experience", "linkedin", "github", "password", "password_confirm"]

# Hapat e formularit dhe fushat që kontrollohen në secilin hap
STEP_FIELDS = {
    1: ["full_name", "email", "phone", "city"],
    2: ["profession", "profession_other", "experience", "linkedin", "github", "cv"],
    3: ["password", "password_confirm"],
}

# ============================================================
# 2. PËRKTHIMET (AL / EN)
# ============================================================
TEXTS = {
    "AL": {
        "tagline": "Regjistrohu në bazën tonë të kandidatëve dhe gjej punën që të përshtatet.",
        "menu": "Menyja",
        "nav_register": "Regjistrimi",
        "nav_admin": "Paneli i kompanisë",
        "required_note": "Fushat me * janë të detyrueshme.",
        "full_name": "Emri dhe mbiemri *",
        "email": "Email *",
        "country": "Shteti *",
        "phone": "Numri i telefonit *",
        "city": "Qyteti *",
        "profession": "Fusha e profesionit *",
        "choose": "Zgjidhni...",
        "profession_other": "Shkruani profesionin tuaj *",
        "ph_profession_other": "Arkitekt",
        "experience": "Vitet e përvojës *",
        "linkedin": "Linku i LinkedIn (opsional)",
        "cv": "CV në PDF (opsionale, deri në {n} MB)",
        "cv_format": "Skedari nuk është PDF i vlefshëm.",
        "hint_cv_format": "Ruajeni CV-në si PDF (File → Save as PDF) dhe ngarkojeni sërish.",
        "cv_size": "CV-ja është më e madhe se {n} MB.",
        "hint_cv_size": "Kompresojeni PDF-në ose hiqni fotot e mëdha, pastaj ngarkojeni sërish.",
        "cv_select": "Zgjidhni kandidatin për të shkarkuar CV-në",
        "cv_download": "Shkarko CV-në",
        "col_cv_name": "CV",
        "password": "Fjalëkalimi *",
        "password_confirm": "Konfirmo fjalëkalimin *",
        "submit": "Regjistrohu",
        "step_1": "Të dhënat personale",
        "step_2": "Profili profesional",
        "step_3": "Llogaria",
        "step_of": "Hapi {n} nga {total}",
        "steps_label": "Hapat e regjistrimit",
        "next": "Vazhdo",
        "back": "Kthehu",
        "success_title": "Regjistrimi u krye!",
        "ph_full_name": "Besir Memeti",
        "ph_email": "emri@gmail.com",
        "ph_city": "Gostivar",
        "ph_experience": "0 - 10",
        "ph_linkedin": "https://www.linkedin.com/in/...",
        "github": "Linku i GitHub (opsional)",
        "ph_github": "https://github.com/...",
        "MK": "Maqedonia e Veriut", "AL": "Shqipëria", "KS": "Kosova",
        "IT": "IT", "Finance": "Financë", "Sales": "Shitje",
        "Marketing": "Marketing", "Health": "Shëndetësi", "Other": "Tjetër",
        "ok": "Në rregull",
        # Gabimet: arsyeja (çelësi) dhe udhëzimi se çfarë duhet bërë (hint_...)
        "required": "Kjo fushë është e zbrazët.",
        "hint_full_name": "Shkruani emrin dhe mbiemrin tuaj, p.sh. Besir Memeti.",
        "hint_email": "Shkruani adresën tuaj të emailit, p.sh. emri@gmail.com.",
        "hint_phone": "Shkruani numrin pa prefiksin e shtetit, p.sh. 70123456.",
        "hint_city": "Shkruani qytetin ku jetoni.",
        "hint_profession": "Zgjidhni një fushë nga lista; nëse nuk e gjeni, zgjidhni „Tjetër”.",
        "hint_profession_other": "Shkruani emrin e profesionit tuaj.",
        "hint_experience": "Shkruani numrin e viteve të përvojës, nga 0 deri në 10.",
        "hint_password": "Zgjidhni një fjalëkalim për llogarinë tuaj.",
        "hint_password_confirm": "Shkruani sërish të njëjtin fjalëkalim.",
        "email_format": "Adresa e emailit nuk është e plotë.",
        "hint_email_format": "Emaili duhet të ketë „@” dhe domenin me pikë, p.sh. emri@gmail.com.",
        "email_exists": "Ky email është i regjistruar tashmë.",
        "hint_email_exists": "Përdorni një email tjetër. Nëse ky është emaili juaj, ju jeni të regjistruar.",
        "phone_digits": "Numri përmban shkronja ose simbole.",
        "hint_phone_digits": "Shkruani vetëm shifra (hapësirat dhe vizat lejohen).",
        "phone_length": "Numri ka {got} shifra, por për {country} duhen {n}.",
        "hint_phone_length": "Mos e shkruani prefiksin {code}; zeroja në fillim hiqet vetë.",
        "exp_number": "Vlera nuk është numër i plotë.",
        "hint_exp_number": "Shkruani vetëm numrin e viteve, p.sh. 3 (pa presje dhe pa tekst).",
        "exp_range": "Vitet e përvojës janë jashtë kufirit 0–10.",
        "hint_exp_range": "Shkruani një numër nga 0 deri në 10; nëse keni më shumë përvojë, shkruani 10.",
        "linkedin_format": "Linku i LinkedIn nuk është i vlefshëm.",
        "hint_linkedin_format": "Kopjoni linkun e plotë të profilit që fillon me https://, p.sh. https://www.linkedin.com/in/emri.",
        "github_format": "Linku i GitHub nuk është i vlefshëm.",
        "hint_github_format": "Linku duhet të fillojë me https://github.com/, p.sh. https://github.com/emri.",
        "password_mismatch": "Fjalëkalimet nuk përputhen.",
        "hint_password_mismatch": "Shkruani në këtë fushë saktësisht të njëjtin fjalëkalim si më lart.",
        "success": "Profili juaj u regjistrua me sukses! Do t’ju njoftojmë për pozitat që përputhen me profilin tuaj.",
        # Paneli i kompanisë
        "admin_title": "Paneli i kompanisë",
        "admin_tagline": "Pasqyra e kandidatëve të regjistruar në bazën e të dhënave.",
        "admin_login": "Hyni për të parë kandidatët e regjistruar",
        "admin_password": "Fjalëkalimi i administratorit",
        "login": "Hyr",
        "logout": "Dil",
        "wrong_admin": "Fjalëkalim i gabuar.",
        "no_data": "Ende nuk ka kandidatë të regjistruar.",
        "total": "Kandidatë gjithsej",
        "filtered": "Sipas filtrave",
        "professions_count": "Profesione",
        "filter_prof": "Filtro sipas profesionit",
        "filter_city": "Filtro sipas qytetit",
        "by_profession": "Kandidatë sipas profesionit",
        "download": "Shkarko listën (CSV)",
        "col_id": "ID", "col_full_name": "Emri dhe mbiemri", "col_email": "Email",
        "col_phone": "Telefoni", "col_city": "Qyteti", "col_profession": "Profesioni",
        "col_experience": "Vitet e përvojës", "col_linkedin": "LinkedIn", "col_github": "GitHub",
        "col_created_at": "Data e regjistrimit",
    },
    "EN": {
        "tagline": "Join our candidate database and find the job that fits you.",
        "menu": "Menu",
        "nav_register": "Registration",
        "nav_admin": "Company panel",
        "required_note": "Fields marked with * are required.",
        "full_name": "Full name *",
        "email": "Email *",
        "country": "Country *",
        "phone": "Phone number *",
        "city": "City *",
        "profession": "Professional field *",
        "choose": "Choose...",
        "profession_other": "Enter your profession *",
        "ph_profession_other": "Architect",
        "experience": "Years of experience *",
        "linkedin": "LinkedIn profile link (optional)",
        "cv": "CV in PDF (optional, up to {n} MB)",
        "cv_format": "The file is not a valid PDF.",
        "hint_cv_format": "Save your CV as a PDF (File → Save as PDF) and upload it again.",
        "cv_size": "The CV is larger than {n} MB.",
        "hint_cv_size": "Compress the PDF or remove large images, then upload it again.",
        "cv_select": "Choose a candidate to download their CV",
        "cv_download": "Download CV",
        "col_cv_name": "CV",
        "password": "Password *",
        "password_confirm": "Confirm password *",
        "submit": "Register",
        "step_1": "Personal details",
        "step_2": "Professional profile",
        "step_3": "Account",
        "step_of": "Step {n} of {total}",
        "steps_label": "Registration steps",
        "next": "Continue",
        "back": "Back",
        "success_title": "Registration complete!",
        "ph_full_name": "John Smith",
        "ph_email": "name@gmail.com",
        "ph_city": "Gostivar",
        "ph_experience": "0 - 10",
        "ph_linkedin": "https://www.linkedin.com/in/...",
        "github": "GitHub profile link (optional)",
        "ph_github": "https://github.com/...",
        "MK": "North Macedonia", "AL": "Albania", "KS": "Kosovo",
        "IT": "IT", "Finance": "Finance", "Sales": "Sales",
        "Marketing": "Marketing", "Health": "Healthcare", "Other": "Other",
        "ok": "Looks good",
        # Errors: the reason (key) and what to do about it (hint_...)
        "required": "This field is empty.",
        "hint_full_name": "Enter your first and last name, e.g. John Smith.",
        "hint_email": "Enter your email address, e.g. name@gmail.com.",
        "hint_phone": "Enter the number without the country prefix, e.g. 70123456.",
        "hint_city": "Enter the city you live in.",
        "hint_profession": "Choose a field from the list; if yours is missing, choose “Other”.",
        "hint_profession_other": "Enter the name of your profession.",
        "hint_experience": "Enter your years of experience, from 0 to 10.",
        "hint_password": "Choose a password for your account.",
        "hint_password_confirm": "Enter the same password again.",
        "email_format": "The email address is incomplete.",
        "hint_email_format": "An email needs “@” and a domain with a dot, e.g. name@gmail.com.",
        "email_exists": "This email is already registered.",
        "hint_email_exists": "Use a different email. If this is your email, you are already registered.",
        "phone_digits": "The number contains letters or symbols.",
        "hint_phone_digits": "Use digits only (spaces and dashes are allowed).",
        "phone_length": "The number has {got} digits, but {country} needs {n}.",
        "hint_phone_length": "Leave out the {code} prefix; a leading zero is removed automatically.",
        "exp_number": "The value is not a whole number.",
        "hint_exp_number": "Enter only the number of years, e.g. 3 (no decimals or text).",
        "exp_range": "Years of experience are outside the 0–10 range.",
        "hint_exp_range": "Enter a number from 0 to 10; if you have more experience, enter 10.",
        "linkedin_format": "The LinkedIn link is not valid.",
        "hint_linkedin_format": "Copy the full profile link starting with https://, e.g. https://www.linkedin.com/in/name.",
        "github_format": "The GitHub link is not valid.",
        "hint_github_format": "The link must start with https://github.com/, e.g. https://github.com/name.",
        "password_mismatch": "Passwords do not match.",
        "hint_password_mismatch": "Type exactly the same password as above in this field.",
        "success": "Your profile has been registered successfully! We will notify you about positions that match your profile.",
        # Company panel
        "admin_title": "Company panel",
        "admin_tagline": "Overview of the candidates registered in the database.",
        "admin_login": "Log in to view registered candidates",
        "admin_password": "Administrator password",
        "login": "Log in",
        "logout": "Log out",
        "wrong_admin": "Wrong password.",
        "no_data": "No candidates registered yet.",
        "total": "Total candidates",
        "filtered": "Matching filters",
        "professions_count": "Professions",
        "filter_prof": "Filter by profession",
        "filter_city": "Filter by city",
        "by_profession": "Candidates by profession",
        "download": "Download list (CSV)",
        "col_id": "ID", "col_full_name": "Full name", "col_email": "Email",
        "col_phone": "Phone", "col_city": "City", "col_profession": "Profession",
        "col_experience": "Years of experience", "col_linkedin": "LinkedIn", "col_github": "GitHub",
        "col_created_at": "Registered on",
    },
}


def t(key, **params):
    """Kthen tekstin në gjuhën e zgjedhur."""
    lang = st.session_state.get("lang", "AL")
    text = TEXTS[lang].get(key, key)
    return text.format(**params) if params else text


def profession_label(profession):
    """Përkthen profesionet e listës; profesioni i shkruar nga kandidati mbetet siç është."""
    return t(profession) if profession in PROFESSIONS else profession


# ============================================================
# 3. ENKRIPTIMI – CAESAR CIPHER (+6)
# ============================================================
def caesar_encrypt(text, shift=CAESAR_SHIFT):
    """
    Zhvendos çdo shkronjë për 'shift' pozicione (A→G, U→A).
    Shifrat, simbolet dhe shkronjat jashtë A–Z (p.sh. ë, ç) mbeten të pandryshuara.
    Shënim: Caesar Cipher përdoret këtu për qëllime mësimore.
    Në sisteme reale fjalëkalimet ruhen me hashing (p.sh. bcrypt).
    """
    result = ""
    for ch in text:
        if "A" <= ch <= "Z":
            result += chr((ord(ch) - ord("A") + shift) % 26 + ord("A"))
        elif "a" <= ch <= "z":
            result += chr((ord(ch) - ord("a") + shift) % 26 + ord("a"))
        else:
            result += ch
    return result


# ============================================================
# 4. BAZA E TË DHËNAVE – SQLite
# ============================================================
def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    """Krijon tabelën e kandidatëve nëse nuk ekziston."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT NOT NULL,
            email       TEXT NOT NULL UNIQUE,
            phone       TEXT NOT NULL,
            city        TEXT NOT NULL,
            profession  TEXT NOT NULL,
            experience  INTEGER NOT NULL,
            linkedin    TEXT,
            password    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            cv_name     TEXT,
            cv_data     BLOB,
            github      TEXT
        )
    """)
    # Bazat e krijuara më parë nuk i kanë kolonat e CV-së
    columns = [row[1] for row in conn.execute("PRAGMA table_info(candidates)")]
    if "cv_name" not in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN cv_name TEXT")
        conn.execute("ALTER TABLE candidates ADD COLUMN cv_data BLOB")
    if "github" not in columns:
        conn.execute("ALTER TABLE candidates ADD COLUMN github TEXT")
    conn.commit()
    conn.close()


def email_exists(email):
    """Kontrollon nëse emaili është regjistruar më parë."""
    conn = get_connection()
    row = conn.execute("SELECT 1 FROM candidates WHERE email = ?",
                       (email.strip().lower(),)).fetchone()
    conn.close()
    return row is not None


def save_candidate(data):
    """Ruan kandidatin në bazë. Kthen False nëse emaili ekziston tashmë."""
    conn = get_connection()
    cv = data["cv"]
    try:
        conn.execute("""
            INSERT INTO candidates
                (full_name, email, phone, city, profession, experience,
                 linkedin, github, password, created_at, cv_name, cv_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["full_name"].strip(),
            data["email"].strip().lower(),
            data["phone_full"],
            data["city"].strip(),
            data["profession_other"].strip() if data["profession"] == "Other" else data["profession"],
            int(data["experience"]),
            data["linkedin"].strip() or None,
            data["github"].strip() or None,
            caesar_encrypt(data["password"]),   # fjalëkalimi i enkriptuar
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            cv.name if cv else None,
            cv.getvalue() if cv else None,
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def load_candidates():
    """Lexon kandidatët (pa fjalëkalim) për panelin e kompanisë."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, full_name, email, phone, city, profession,
               experience, linkedin, github, created_at, cv_name
        FROM candidates ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def load_cv(candidate_id):
    """Lexon përmbajtjen e CV-së së një kandidati."""
    conn = get_connection()
    row = conn.execute("SELECT cv_data FROM candidates WHERE id = ?",
                       (candidate_id,)).fetchone()
    conn.close()
    return row[0]


# ============================================================
# 5. VALIDIMI
# ============================================================
def clean_phone(phone):
    """Heq hapësirat, vizat dhe zeron në fillim (070... → 70...)."""
    for ch in " -/()":
        phone = phone.replace(ch, "")
    return phone.lstrip("0")


def validate_email(email):
    if not email.strip():
        return ("required", {})
    if "@" not in email or "." not in email:
        return ("email_format", {})
    if email_exists(email):
        return ("email_exists", {})
    return None


def validate_phone(country, phone):
    if not phone.strip():
        return ("required", {})
    number = clean_phone(phone)
    if not number.isdigit():
        return ("phone_digits", {})
    needed = COUNTRIES[country]["digits"]
    if len(number) != needed:
        return ("phone_length", {"country": country, "n": needed, "got": len(number),
                                 "code": COUNTRIES[country]["code"]})
    return None


def validate_experience(value):
    if not value.strip():
        return ("required", {})
    try:
        years = int(value.strip())
    except ValueError:
        return ("exp_number", {})
    if years < 0 or years > 10:
        return ("exp_range", {})
    return None


def validate_linkedin(link):
    if link.strip() and not link.strip().startswith("https://"):
        return ("linkedin_format", {})
    return None


def validate_github(link):
    if link.strip() and not link.strip().startswith("https://github.com/"):
        return ("github_format", {})
    return None


def validate_cv(cv):
    if not cv.getvalue().startswith(b"%PDF-"):
        return ("cv_format", {})
    if cv.size > CV_MAX_MB * 1024 * 1024:
        return ("cv_size", {"n": CV_MAX_MB})
    return None


def validate(data):
    """
    Kontrollon të gjitha fushat.
    Kthen fjalor: fusha → None (e saktë) ose (çelësi_i_gabimit, parametrat).
    """
    results = {}
    results["full_name"] = None if data["full_name"].strip() else ("required", {})
    results["email"] = validate_email(data["email"])
    results["phone"] = validate_phone(data["country"], data["phone"])
    results["city"] = None if data["city"].strip() else ("required", {})
    results["profession"] = None if data["profession"] else ("required", {})
    if data["profession"] == "Other":       # Profesioni shkruhet vetëm kur zgjidhet „Tjetër”
        results["profession_other"] = None if data["profession_other"].strip() else ("required", {})
    results["experience"] = validate_experience(data["experience"])
    if data["linkedin"].strip():            # LinkedIn kontrollohet vetëm nëse plotësohet
        results["linkedin"] = validate_linkedin(data["linkedin"])
    if data["github"].strip():              # GitHub kontrollohet vetëm nëse plotësohet
        results["github"] = validate_github(data["github"])
    if data["cv"]:                          # CV-ja kontrollohet vetëm nëse ngarkohet
        results["cv"] = validate_cv(data["cv"])
    results["password"] = None if data["password"] else ("required", {})
    if not data["password_confirm"]:
        results["password_confirm"] = ("required", {})
    elif data["password_confirm"] != data["password"]:
        results["password_confirm"] = ("password_mismatch", {})
    else:
        results["password_confirm"] = None
    return results


# ============================================================
# 6. DIZAJNI (SFONDI DHE CSS)
# ============================================================
def workstation(x, y, scale, shirt, hair, skin):
    """Vizaton një punonjës nga pas, ulur në tavolinë përballë monitorit me kod."""
    return f"""
    <g transform="translate({x} {y}) scale({scale})">
        <rect x="-112" y="-96" width="224" height="9" rx="2" fill="#c9a77c"/>
        <rect x="-104" y="-87" width="7" height="87" fill="#4a3a2d"/>
        <rect x="97" y="-87" width="7" height="87" fill="#4a3a2d"/>
        <rect x="-6" y="-116" width="12" height="20" fill="#26332f"/>
        <rect x="-58" y="-184" width="116" height="70" rx="4" fill="#26332f"/>
        <rect x="-53" y="-179" width="106" height="60" fill="#0f2622"/>
        <rect x="-47" y="-173" width="52" height="4" fill="#f4b13d"/>
        <rect x="-47" y="-164" width="78" height="4" fill="#7fd1b9"/>
        <rect x="-39" y="-155" width="60" height="4" fill="#e6efe9"/>
        <rect x="-39" y="-146" width="82" height="4" fill="#7fd1b9"/>
        <rect x="-47" y="-137" width="40" height="4" fill="#f4b13d"/>
        <rect x="78" y="-112" width="16" height="16" rx="2" fill="#f4efe3"/>
        <rect x="-4" y="-22" width="8" height="18" fill="#26332f"/>
        <rect x="-26" y="-6" width="52" height="6" rx="3" fill="#26332f"/>
        <rect x="-28" y="-100" width="56" height="62" rx="20" fill="{shirt}"/>
        <rect x="-6" y="-112" width="12" height="14" fill="{skin}"/>
        <circle cy="-124" r="16" fill="{skin}"/>
        <path d="M-16 -124a16 16 0 0 1 32 0c0 5-3 10-5 12h-22c-2-2-5-7-5-12z" fill="{hair}"/>
        <rect x="-33" y="-70" width="66" height="50" rx="10" fill="#1c2b27"/>
    </g>"""


def plant(x, y, scale):
    """Vizaton një bimë zyre në vazo."""
    return f"""
    <g transform="translate({x} {y}) scale({scale})">
        <path d="M0 -40C-34 -60 -36 -100 -26 -122C-10 -100 -2 -72 0 -40Z" fill="#2f7d63"/>
        <path d="M0 -40C34 -60 36 -100 26 -122C10 -100 2 -72 0 -40Z" fill="#2f7d63"/>
        <path d="M0 -40C-12 -80 -8 -120 0 -144C8 -120 12 -80 0 -40Z" fill="#3f9877"/>
        <path d="M-20 -42h40l-6 42h-28z" fill="#e8dfcc"/>
    </g>"""


def skyline():
    """Vizaton ndërtesat e qytetit që duken poshtë dritareve të katit të lartë."""
    parts = []
    far = [(0, 90, 400), (110, 70, 450), (200, 110, 370), (340, 80, 430), (450, 120, 390), (600, 70, 460),
           (700, 100, 360), (830, 90, 440), (950, 120, 380), (1100, 80, 430), (1210, 110, 370),
           (1350, 90, 450), (1460, 140, 400)]
    near = [(40, 130, 520), (220, 100, 490), (380, 150, 540), (570, 110, 500), (740, 140, 530),
            (930, 110, 490), (1090, 150, 530), (1280, 120, 500), (1440, 160, 530)]
    for x, width, top in far:
        parts.append(f'<rect x="{x}" y="{top}" width="{width}" height="{640 - top}" fill="#2c5a58"/>')
    for x, width, top in near:
        parts.append(f'<rect x="{x}" y="{top}" width="{width}" height="{640 - top}" fill="#173d39"/>')
        for row in range(top + 14, 610, 22):
            for col in range(x + 12, x + width - 14, 22):
                if (row + col) % 3 == 0:    # vetëm disa dritare janë të ndezura
                    parts.append(f'<rect x="{col}" y="{row}" width="10" height="12" fill="#f4b13d" opacity=".8"/>')
    return "".join(parts)


def office_background():
    """Ndërton skenën e zyrës IT në kat të lartë dhe e kthen si URI për CSS."""
    window_frames = "".join(f'<rect x="{x}" y="70" width="10" height="550" fill="#0d2a25"/>'
                            for x in range(0, 1601, 200))
    lamps = "".join(f"""
        <rect x="{x - 1}" y="70" width="3" height="60" fill="#0d2a25"/>
        <path d="M{x - 34} 160l14-30h40l14 30z" fill="#f4b13d"/>
        <path d="M{x - 34} 160h68l70 180h-208z" fill="#ffe2a6" opacity=".08"/>""" for x in (300, 800, 1300))
    back_row = [
        (120, "#3f9877", "#2b1d14", "#e2b48c"), (400, "#e4572e", "#111111", "#a86f47"),
        (680, "#f4efe3", "#6b3e1f", "#f0c8a4"), (960, "#2f6db0", "#3a2a1c", "#c98f64"),
        (1240, "#f4b13d", "#111111", "#e2b48c"), (1500, "#7a4fa3", "#8a5a2b", "#f0c8a4"),
    ]
    front_row = [
        (250, "#2f6db0", "#3a2a1c", "#f0c8a4"), (800, "#3f9877", "#111111", "#a86f47"),
        (1370, "#e4572e", "#6b3e1f", "#e2b48c"),
    ]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice">
    <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#17404a"/><stop offset=".6" stop-color="#4b8f8c"/>
            <stop offset="1" stop-color="#f6c978"/>
        </linearGradient>
        <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#8a6a4c"/><stop offset="1" stop-color="#4a3424"/>
        </linearGradient>
    </defs>
    <rect y="70" width="1600" height="570" fill="url(#sky)"/>
    <circle cx="1150" cy="420" r="70" fill="#ffe2a6" opacity=".85"/>
    {skyline()}
    {window_frames}
    <rect y="612" width="1600" height="28" fill="#0d2a25"/>
    <rect y="640" width="1600" height="260" fill="url(#floor)"/>
    <rect width="1600" height="70" fill="#0d2a25"/>
    {lamps}
    {plant(20, 720, 1)}{plant(1580, 720, 1)}
    {"".join(workstation(x, 720, .8, *person) for x, *person in back_row)}
    {"".join(workstation(x, 890, 1.2, *person) for x, *person in front_row)}
    </svg>"""
    return svg_uri(svg)


def svg_uri(svg):
    """Kthen vizatimin SVG si URI që mund të përdoret në CSS."""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def profile_card(x, y, angle, opacity, avatar):
    """Vizaton një kartë të profilit të kandidatit."""
    return f"""
    <g transform="translate({x} {y}) rotate({angle})" opacity="{opacity}">
        <rect x="-62" y="-78" width="124" height="156" rx="16" fill="#fbf7ee"/>
        <circle cy="-40" r="22" fill="{avatar}"/>
        <circle cy="-46" r="8" fill="#fbf7ee"/>
        <path d="M-13 -25a13 12 0 0 1 26 0z" fill="#fbf7ee"/>
        <rect x="-38" y="-4" width="76" height="8" rx="4" fill="#12372f"/>
        <rect x="-44" y="14" width="88" height="6" rx="3" fill="#b9c7bf"/>
        <rect x="-44" y="28" width="66" height="6" rx="3" fill="#b9c7bf"/>
        <rect x="-44" y="48" width="34" height="14" rx="7" fill="#7fd1b9"/>
        <rect x="-5" y="48" width="34" height="14" rx="7" fill="#f4b13d"/>
    </g>"""


def hero_art():
    """Ndërton ilustrimin e kokës: kandidatë dhe profili i përzgjedhur."""
    sparkle = "M0 -9L2.5 -2.5L9 0L2.5 2.5L0 9L-2.5 2.5L-9 0L-2.5 -2.5Z"
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200">
    {profile_card(82, 106, -13, .55, "#3f9877")}
    {profile_card(218, 106, 13, .55, "#2f6db0")}
    {profile_card(150, 100, 0, 1, "#e4572e")}
    <circle cx="202" cy="42" r="19" fill="#f4b13d"/>
    <path d="M193 42l7 7l12-14" fill="none" stroke="#12372f" stroke-width="4"
          stroke-linecap="round" stroke-linejoin="round"/>
    <path d="{sparkle}" transform="translate(42 30)" fill="#f4b13d"/>
    <path d="{sparkle}" transform="translate(268 26) scale(.7)" fill="#ffffff"/>
    <path d="{sparkle}" transform="translate(276 176) scale(.9)" fill="#f4b13d"/>
    </svg>"""
    return svg_uri(svg)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
:root {
    --forest: #12372f; --pine: #1e5a4c; --amber: #f4b13d; --amber-dark: #e29a1f;
    --cream: #fbf7ee; --sand: #e8dfcc; --ink: #1c2b27; --muted: #5f6d67;
    --ok: #15803d; --err: #c0321f;
    --ease-out: cubic-bezier(.22, 1, .36, 1);
}
.stApp, .stApp div, .stApp p, .stApp label, .stApp input, .stApp textarea, .stApp button {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
/* Shtresa e çelët e zbeh skenën e zyrës që të mos e rëndojë përmbajtjen */
.stApp {
    background:
        linear-gradient(rgba(251, 247, 238, .72), rgba(251, 247, 238, .72)) fixed,
        var(--cream) url("__OFFICE_BG__") center bottom / cover no-repeat fixed;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 880px; padding-top: 5.5rem; padding-bottom: 4rem; }
/* Paneli i kompanisë ka tekst direkt mbi faqe, ndaj i duhet sfond i lexueshëm */
.block-container:has(.hero.admin) {
    max-width: 960px; margin-top: 4.5rem; padding-top: 1.5rem;
    background: rgba(251, 247, 238, .96); border-radius: 24px;
}
[data-testid="stAlert"] { background: #fff; border-radius: 12px; }

/* Fokusi i dukshëm për përdoruesit e tastierës */
.stApp button:focus-visible, .stApp a:focus-visible {
    outline: 3px solid var(--pine) !important; outline-offset: 3px;
}

/* Butonat dytësorë (Kthehu, Dil) */
.stButton > button[data-testid="stBaseButton-secondary"] {
    background: transparent !important; color: var(--forest) !important;
    border: 2px solid var(--sand) !important;
}
.stButton > button[data-testid="stBaseButton-secondary"]:hover {
    background: var(--sand) !important; box-shadow: none !important;
}

/* Zgjedhja e gjuhës lart djathtas */
.st-key-lang_switch {
    position: fixed; top: .7rem; right: 3.5rem; z-index: 1000000; width: auto !important;
    flex-wrap: nowrap; gap: .4rem; padding: .3rem; border-radius: 999px;
    background: rgba(255, 255, 255, .95); box-shadow: 0 6px 18px rgba(13, 42, 37, .3);
}
.st-key-lang_switch .stButton { width: auto !important; }
.st-key-lang_switch .stButton > button {
    display: flex; align-items: center; width: auto; min-height: 0; padding: .3rem .7rem !important;
    background: transparent !important; color: var(--forest) !important; border: none !important;
    transform: none !important; box-shadow: none !important;
}
.st-key-lang_switch .stButton > button:hover { background: var(--sand) !important; }
.st-key-lang_switch .stButton > button[data-testid="stBaseButton-primary"] { background: var(--forest) !important; }
.st-key-lang_switch .stButton > button[data-testid="stBaseButton-primary"] p { color: #fff; }
.st-key-lang_switch .stButton > button::before {
    content: ""; flex: none; width: 20px; height: 15px; margin-right: .4rem; border-radius: 2px;
    background: center / cover no-repeat;
}
.st-key-lang_AL .stButton > button::before { background-image: url("https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/4x3/al.svg"); }
.st-key-lang_EN .stButton > button::before { background-image: url("https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/4x3/gb.svg"); }

.hero {
    position: relative; overflow: hidden;
    background: linear-gradient(125deg, rgba(18, 55, 47, .94) 0%, rgba(30, 90, 76, .88) 100%);
    color: #fff; padding: 2.6rem 2.4rem; border-radius: 24px;
    margin-bottom: 1.75rem; box-shadow: 0 18px 40px rgba(18, 55, 47, .28);
}
/* Ilustrimi me profile kandidatësh në anën e djathtë të kokës */
.hero::after {
    content: ""; position: absolute; top: 50%; right: 1.2rem; width: 15rem; height: 10rem;
    transform: translateY(-50%); pointer-events: none;
    background: url("__HERO_ART__") center / contain no-repeat;
    animation: artIn .8s .15s var(--ease-out) both;
}
.hero h1, .hero p { position: relative; z-index: 1; max-width: 72%; }
.hero h1 {
    color: #fff; margin: 0; padding: 0; font-family: 'Fraunces', serif;
    font-size: 2.6rem; font-weight: 700; line-height: 1.1; letter-spacing: -.01em;
}
.hero h1, .hero h1 span { color: var(--amber); }
.hero p { margin: .7rem 0 0; color: #e6efe9; font-size: 1.08rem; }

[data-testid="stForm"], .st-key-registration_form {
    background: #fff; border: 1px solid var(--sand); border-top: 5px solid var(--amber);
    border-radius: 20px; padding: 2.2rem; box-shadow: 0 10px 30px rgba(18, 55, 47, .08);
}
/* Fushat që hyjnë anash gjatë kalimit nuk duhet të krijojnë shirit horizontal */
.st-key-registration_form { overflow: hidden; }
.stApp .section-title {
    font-family: 'Fraunces', serif; font-size: 1.45rem; font-weight: 600;
    color: var(--forest); margin-bottom: 0;
}
.title-icon { display: inline-flex; width: 1.1em; height: 1.1em; margin-right: .45rem; vertical-align: -.12em; color: var(--amber-dark); }
.stApp .eyebrow {
    margin: 0 0 .15rem; color: var(--pine); font-size: .75rem; font-weight: 700;
    letter-spacing: .12em; text-transform: uppercase;
}
.note { color: var(--muted); font-size: .88rem; margin-bottom: 1rem; }

.ok, .err {
    display: flex; align-items: center; gap: .35rem;
    font-size: .85rem; font-weight: 500; margin: -.5rem 0 .6rem;
}
.ok svg, .err svg { flex: none; width: 16px; height: 16px; }
.err { align-items: flex-start; }
.err svg { margin-top: .1rem; }
.err strong { display: block; font-weight: 700; }
.err span { display: block; margin-top: .1rem; font-size: .8rem; line-height: 1.4; }
.ok  { color: var(--ok); animation: statusIn .25s var(--ease-out) both; }
.err { color: var(--err); animation: statusShake .4s var(--ease-out) both; }

.stFormSubmitButton > button, .stButton > button, .stDownloadButton > button {
    background: var(--amber) !important;
    color: var(--forest) !important; border: none !important; border-radius: 999px !important;
    padding: .7rem 2rem !important; width: 100%;
    transition: transform .15s ease, box-shadow .15s ease, background .15s ease;
}
.stFormSubmitButton > button p, .stButton > button p, .stDownloadButton > button p {
    font-weight: 700 !important;
}
.stFormSubmitButton > button:hover, .stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--amber-dark) !important;
    transform: translateY(-2px); box-shadow: 0 10px 20px rgba(226, 154, 31, .35);
}
.stButton > button:active, .stDownloadButton > button:active { transform: translateY(0) scale(.98); }

/* Treguesi i hapave të regjistrimit */
.stepper { position: relative; margin: 0 0 1.8rem; }
.stepper ol {
    position: relative; z-index: 1; display: grid; grid-template-columns: repeat(3, 1fr);
    margin: 0; padding: 0; list-style: none;
}
.stepper li {
    display: flex; flex-direction: column; align-items: center; gap: .45rem;
    margin: 0; padding: 0; text-align: center;
}
.stepper .dot {
    display: grid; place-items: center; width: 2.4rem; height: 2.4rem; border-radius: 50%;
    background: #fff; border: 2px solid var(--sand); color: var(--muted); font-weight: 700;
    transition: background .3s ease, border-color .3s ease, color .3s ease;
}
.stepper .dot svg { width: 1.1rem; height: 1.1rem; }
.stepper .lbl { color: var(--muted); font-size: .82rem; font-weight: 600; line-height: 1.3; }
.stepper li.active .dot {
    background: var(--forest); border-color: var(--forest); color: #fff;
    box-shadow: 0 0 0 6px rgba(30, 90, 76, .14); animation: dotPop .45s var(--ease-out);
}
.stepper li.active .lbl { color: var(--forest); }
.stepper li.done .dot { background: var(--amber); border-color: var(--amber); color: var(--forest); }
.stepper-track {
    position: absolute; top: 1.2rem; left: calc(100% / 6); right: calc(100% / 6);
    height: 3px; margin-top: -1.5px; border-radius: 3px; background: var(--sand); overflow: hidden;
}
/* Vija mbushet nga hapi i mëparshëm te hapi aktual */
.stepper-fill {
    height: 100%; background: var(--pine); transform-origin: left center;
    transform: scaleX(var(--to)); animation: fillTo .6s var(--ease-out);
}

/* Hapat e formularit: rreshtat hyjnë njëri pas tjetrit nga drejtimi i lëvizjes */
[class*="st-key-step_"] > div { animation: stepIn .45s var(--ease-out) both; }
[class*="st-key-step_"] > div:nth-child(2) { animation-delay: .05s; }
[class*="st-key-step_"] > div:nth-child(3) { animation-delay: .1s; }
[class*="st-key-step_"] > div:nth-child(4) { animation-delay: .15s; }
[class*="st-key-step_"] > div:nth-child(5) { animation-delay: .2s; }
[class*="st-key-step_"] > div:nth-child(n+6) { animation-delay: .25s; }

/* Kartela e suksesit me shenjën që vizatohet */
.success-card {
    display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; padding: 1.1rem 1.3rem;
    background: #fff; border: 1px solid #bfe3cc; border-left: 5px solid var(--ok); border-radius: 16px;
    box-shadow: 0 10px 30px rgba(21, 128, 61, .12); animation: popIn .55s var(--ease-out) both;
}
.success-card svg { flex: none; width: 48px; height: 48px; stroke: var(--ok); }
.success-card circle { stroke-dasharray: 145; stroke-dashoffset: 145; animation: draw .6s .15s ease-out forwards; }
.success-card path { stroke-dasharray: 32; stroke-dashoffset: 32; animation: draw .35s .65s ease-out forwards; }
.success-card strong { display: block; color: var(--forest); font-family: 'Fraunces', serif; font-size: 1.2rem; }
.success-card p { margin: .15rem 0 0; color: var(--ink); }

[data-testid="stMetric"] {
    background: #fff; border: 1px solid var(--sand); border-left: 5px solid var(--pine);
    border-radius: 16px; padding: 1rem 1.2rem;
}
[data-testid="stMetricValue"] div { font-family: 'Fraunces', serif; color: var(--forest); }
.st-key-metrics [data-testid="stColumn"] { animation: riseIn .45s var(--ease-out) both; }
.st-key-metrics [data-testid="stColumn"]:nth-child(2) { animation-delay: .08s; }
.st-key-metrics [data-testid="stColumn"]:nth-child(3) { animation-delay: .16s; }

[data-testid="stSidebar"] { background: var(--forest); }
[data-testid="stSidebar"] * { color: #f4efe3 !important; }
[data-testid="stSidebar"] h2 { font-size: 1.35rem; font-weight: 800; letter-spacing: -.01em; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    font-size: .72rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; opacity: .7;
}
[data-testid="stSidebar"] [role="radiogroup"] { gap: .35rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    width: 100%; margin: 0; padding: .7rem .9rem; border-radius: 10px; cursor: pointer;
    transition: background .2s ease, transform .2s var(--ease-out);
}
[data-testid="stSidebar"] [role="radiogroup"] label > div > div:first-child:not([data-testid="stMarkdownContainer"]) { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label p { font-size: .95rem; font-weight: 600; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255, 255, 255, .1); transform: translateX(3px); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--amber); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * { color: var(--forest) !important; }

/* Kalimi ndërmjet faqeve: dy emra të ndryshëm që animacioni të niset sërish */
.st-key-page_0 { animation: pageIn0 .5s var(--ease-out) both; }
.st-key-page_1 { animation: pageIn1 .5s var(--ease-out) both; }

@keyframes pageIn0 { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
@keyframes pageIn1 { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: none; } }
@keyframes artIn { from { opacity: 0; transform: translateY(-50%) translateX(28px) scale(.95); } }
@keyframes stepIn { from { opacity: 0; transform: translateX(var(--dx, 28px)); } to { opacity: 1; transform: none; } }
@keyframes fillTo { from { transform: scaleX(var(--from)); } to { transform: scaleX(var(--to)); } }
@keyframes dotPop { from { transform: scale(.7); } }
@keyframes statusIn { from { opacity: 0; transform: translateY(-4px); } }
@keyframes statusShake {
    0% { opacity: 0; } 25% { opacity: 1; transform: translateX(-4px); }
    50% { transform: translateX(4px); } 75% { transform: translateX(-2px); } 100% { transform: none; }
}
@keyframes popIn { from { opacity: 0; transform: translateY(-10px) scale(.97); } to { opacity: 1; transform: none; } }
@keyframes draw { to { stroke-dashoffset: 0; } }
@keyframes riseIn { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

/* Kush ka zgjedhur më pak lëvizje në sistem e sheh menjëherë gjendjen përfundimtare */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .01ms !important; animation-delay: 0s !important;
        transition-duration: .01ms !important;
    }
}

@media (max-width: 640px) {
    .hero { padding: 2rem 1.5rem; }
    .hero::after { opacity: .25; }
    .hero h1, .hero p { max-width: 100%; }
    .hero h1 { font-size: 2rem; }
    [data-testid="stForm"], .st-key-registration_form { padding: 1.4rem; }
    .stepper .lbl { font-size: .72rem; }
}
</style>
"""

# Ikonat SVG (në vend të emoji-ve)
ICON_OK = ('<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 10.5l3.2 3.2L15 7" fill="none" '
           'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>')
ICON_ERR = ('<svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" fill="none" '
            'stroke="currentColor" stroke-width="2"/><path d="M10 5.8v5M10 14v.2" stroke="currentColor" '
            'stroke-width="2.2" stroke-linecap="round"/></svg>')
ICON_LOCK = ('<svg class="title-icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="4.5" y="10.5" width="15" '
             'height="10" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" '
             'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>')
ICON_SUCCESS = ('<svg viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="23" fill="none" stroke-width="3"/>'
                '<path d="M15 27l7 7 15-15" fill="none" stroke-width="4" stroke-linecap="round" '
                'stroke-linejoin="round"/></svg>')


def set_language(lang):
    st.session_state["lang"] = lang


def language_switch():
    """Shfaq butonat AL / EN me flamur në këndin lart djathtas."""
    current = st.session_state.setdefault("lang", "AL")
    with st.container(key="lang_switch", horizontal=True):
        for lang in TEXTS:
            st.button(lang, key=f"lang_{lang}", type="primary" if lang == current else "secondary",
                      on_click=set_language, args=(lang,))


def show_header(title=None, tagline_key="tagline"):
    st.markdown(f"""
        <div class="hero{' admin' if title else ''}">
            <h1>ROI Hunting{(' – ' + title) if title else ''}</h1>
            <p>{t(tagline_key)}</p>
        </div>
    """, unsafe_allow_html=True)


def show_status(field):
    """Shfaq shenjën e gjelbër, ose me të kuqe arsyen e gabimit dhe çfarë duhet bërë."""
    results = st.session_state.get("results")
    if not results or field not in results:
        return
    error = results[field]
    if error is None:
        st.markdown(f'<div class="ok">{ICON_OK} {t("ok")}</div>', unsafe_allow_html=True)
    else:
        key, params = error
        if "country" in params:     # përkthe emrin e shtetit
            params = {**params, "country": t(params["country"])}
        hint = t(f"hint_{field}") if key == "required" else t(f"hint_{key}", **params)
        st.markdown(f'<div class="err" role="alert">{ICON_ERR}<div><strong>{t(key, **params)}</strong>'
                    f'<span>{hint}</span></div></div>', unsafe_allow_html=True)


def show_stepper(step):
    """Treguesi i hapave; vija e progresit lëviz nga hapi i shfaqur më parë te hapi aktual."""
    total = len(STEP_FIELDS)
    before = st.session_state.get("step_shown", step)
    items = ""
    for n in STEP_FIELDS:
        state = "done" if n < step else "active" if n == step else "todo"
        mark = ICON_OK if n < step else str(n)
        current = ' aria-current="step"' if n == step else ""
        items += f'<li class="{state}"{current}><span class="dot">{mark}</span><span class="lbl">{t(f"step_{n}")}</span></li>'
    st.markdown(
        f'<nav class="stepper" aria-label="{t("steps_label")}" '
        f'style="--from:{(before - 1) / (total - 1)};--to:{(step - 1) / (total - 1)}">'
        f'<div class="stepper-track"><div class="stepper-fill"></div></div><ol>{items}</ol></nav>',
        unsafe_allow_html=True)
    st.session_state["step_shown"] = step


def step_heading(n):
    st.markdown(f'<p class="eyebrow">{t("step_of", n=n, total=len(STEP_FIELDS))}</p>'
                f'<p class="section-title">{t(f"step_{n}")}</p>'
                f'<p class="note">{t("required_note")}</p>', unsafe_allow_html=True)


# ============================================================
# 7. FAQJA 1 – REGJISTRIMI I KANDIDATIT
# ============================================================
def collect_data():
    """Mbledh vlerat e formularit nga session_state."""
    data = {key: st.session_state.get(key) or "" for key in FORM_KEYS}
    data["country"] = st.session_state.get("country", "MK")
    data["profession"] = st.session_state.get("profession")
    data["cv"] = st.session_state.get(f"cv_{st.session_state.get('cv_version', 0)}")
    return data


def go_to(step, direction):
    st.session_state["step"] = step
    st.session_state["direction"] = direction


def next_step(step):
    """Kontrollon fushat e hapit aktual dhe kalon te hapi tjetër vetëm nëse janë të sakta."""
    st.session_state["success"] = False
    results = validate(collect_data())
    step_results = {field: results[field] for field in STEP_FIELDS[step] if field in results}
    # Rezultatet e vjetra të këtij hapi zëvendësohen (p.sh. „Tjetër” që nuk zgjidhet më)
    previous = {field: error for field, error in (st.session_state.get("results") or {}).items()
                if field not in STEP_FIELDS[step]}
    st.session_state["results"] = {**previous, **step_results}
    if all(error is None for error in step_results.values()):
        go_to(step + 1, "forward")


def submit():
    data = collect_data()
    results = validate(data)
    if all(error is None for error in results.values()):
        data["phone_full"] = f"{COUNTRIES[data['country']]['code']} {clean_phone(data['phone'])}"
        if save_candidate(data):
            st.session_state.update(success=True, results=None, clear_form=True)
            go_to(1, "forward")
            return
        results["email"] = ("email_exists", {})
    st.session_state["results"] = results
    # Kthehu te hapi i parë që ka gabim
    first_bad = next(n for n in STEP_FIELDS if any(results.get(field) for field in STEP_FIELDS[n]))
    if first_bad != st.session_state["step"]:
        go_to(first_bad, "back")


def registration_page():
    show_header()

    # Pas regjistrimit të suksesshëm, pastrohet formulari
    if st.session_state.pop("clear_form", False):
        for key in FORM_KEYS:
            st.session_state.pop(key, None)
        # Ngarkuesi i skedarëve pastrohet vetëm me çelës të ri
        st.session_state["cv_version"] = st.session_state.get("cv_version", 0) + 1

    if st.session_state.get("success"):
        st.markdown(f'<div class="success-card" role="status">{ICON_SUCCESS}'
                    f'<div><strong>{t("success_title")}</strong><p>{t("success")}</p></div></div>',
                    unsafe_allow_html=True)

    step = st.session_state.setdefault("step", 1)
    shift = "28px" if st.session_state.get("direction", "forward") == "forward" else "-28px"
    # Të gjithë hapat vizatohen, por shfaqet vetëm hapi aktual: kështu fushat (edhe CV-ja) ruajnë vlerat
    hidden = ", ".join(f".st-key-step_{n}" for n in STEP_FIELDS if n != step)
    # Fushat me gabim marrin kornizë të kuqe
    errors = [field for field, error in (st.session_state.get("results") or {}).items() if error]
    error_css = "".join(f".st-key-{field} [data-baseweb] {{ border-color: var(--err) !important; }}" for field in errors)
    st.markdown(f"<style>{hidden} {{ display: none !important; }} .st-key-step_{step} {{ --dx: {shift}; }}"
                f"{error_css}</style>", unsafe_allow_html=True)

    # Pa st.form, që fusha „Tjetër” të shfaqet menjëherë pas zgjedhjes
    with st.container(key="registration_form"):
        show_stepper(step)

        # Hapi 1: Të dhënat personale
        with st.container(key="step_1"):
            step_heading(1)
            c1, c2 = st.columns(2)
            with c1:
                st.text_input(t("full_name"), key="full_name", placeholder=t("ph_full_name"))
                show_status("full_name")
            with c2:
                st.text_input(t("email"), key="email", placeholder=t("ph_email"))
                show_status("email")

            c1, c2, c3 = st.columns([1.3, 1.7, 2])
            with c1:
                country = st.selectbox(
                    t("country"), list(COUNTRIES.keys()), key="country",
                    format_func=lambda c: f"{COUNTRIES[c]['flag']} {COUNTRIES[c]['code']}",
                    help=" | ".join(f"{COUNTRIES[c]['code']} = {t(c)}" for c in COUNTRIES),
                )
            with c2:
                st.text_input(t("phone"), key="phone", placeholder="X" * COUNTRIES[country]["digits"])
                show_status("phone")
            with c3:
                st.text_input(t("city"), key="city", placeholder=t("ph_city"))
                show_status("city")

        # Hapi 2: Profili profesional
        with st.container(key="step_2"):
            step_heading(2)
            c1, c2 = st.columns(2)
            with c1:
                profession = st.selectbox(t("profession"), PROFESSIONS, index=None, key="profession",
                                          placeholder=t("choose"), format_func=t)
                show_status("profession")
                if profession == "Other":
                    st.text_input(t("profession_other"), key="profession_other",
                                  placeholder=t("ph_profession_other"), max_chars=50)
                    show_status("profession_other")
            with c2:
                st.text_input(t("experience"), key="experience", placeholder=t("ph_experience"))
                show_status("experience")

            c1, c2 = st.columns(2)
            with c1:
                st.text_input(t("linkedin"), key="linkedin", placeholder=t("ph_linkedin"))
                show_status("linkedin")
            with c2:
                st.text_input(t("github"), key="github", placeholder=t("ph_github"))
                show_status("github")

            st.file_uploader(t("cv", n=CV_MAX_MB), type=["pdf"],
                             key=f"cv_{st.session_state.get('cv_version', 0)}")
            show_status("cv")

        # Hapi 3: Llogaria
        with st.container(key="step_3"):
            step_heading(3)
            c1, c2 = st.columns(2)
            with c1:
                st.text_input(t("password"), key="password", type="password")
                show_status("password")
            with c2:
                st.text_input(t("password_confirm"), key="password_confirm", type="password")
                show_status("password_confirm")

        # Butonat e lëvizjes ndërmjet hapave
        c1, c2 = st.columns(2)
        with c1:
            if step > 1:
                st.button(t("back"), key="back", icon=":material/arrow_back:",
                          on_click=go_to, args=(step - 1, "back"))
        with c2:
            if step < len(STEP_FIELDS):
                st.button(t("next"), key="next", type="primary", on_click=next_step, args=(step,))
            else:
                st.button(t("submit"), key="submit", type="primary", icon=":material/how_to_reg:",
                          on_click=submit)


# ============================================================
# 8. FAQJA 2 – PANELI I KOMPANISË
# ============================================================
def admin_page():
    show_header(t("admin_title"), "admin_tagline")

    # Hyrja me fjalëkalim
    if not st.session_state.get("admin_ok"):
        with st.form("admin_login"):
            st.markdown(f'<p class="section-title">{ICON_LOCK}{t("admin_login")}</p>', unsafe_allow_html=True)
            password = st.text_input(t("admin_password"), type="password")
            if st.form_submit_button(t("login"), icon=":material/login:"):
                # Fjalëkalimi i shkruar enkriptohet dhe krahasohet me atë të ruajtur
                if caesar_encrypt(password) == ADMIN_PASSWORD_ENCRYPTED:
                    st.session_state["admin_ok"] = True
                    st.rerun()
                else:
                    st.error(t("wrong_admin"), icon=":material/error:")
        return

    df = load_candidates()
    if df.empty:
        st.info(t("no_data"), icon=":material/info:")
    else:
        # Filtrat
        c1, c2 = st.columns(2)
        with c1:
            custom = sorted(set(df["profession"]) - set(PROFESSIONS))
            prof_filter = st.multiselect(t("filter_prof"), PROFESSIONS + custom, format_func=profession_label)
        with c2:
            city_filter = st.multiselect(t("filter_city"), sorted(df["city"].unique()))

        filtered = df.copy()
        if prof_filter:
            filtered = filtered[filtered["profession"].isin(prof_filter)]
        if city_filter:
            filtered = filtered[filtered["city"].isin(city_filter)]

        # Statistikat
        with st.container(key="metrics"):
            m1, m2, m3 = st.columns(3)
            m1.metric(t("total"), len(df))
            m2.metric(t("filtered"), len(filtered))
            m3.metric(t("professions_count"), df["profession"].nunique())

        # Tabela (me emra kolonash dhe profesione të përkthyera)
        table = filtered.copy()
        table["profession"] = table["profession"].map(profession_label)
        table = table.rename(columns={col: t(f"col_{col}") for col in table.columns})
        st.dataframe(table, hide_index=True, column_config={
            t("col_linkedin"): st.column_config.LinkColumn(),
            t("col_github"): st.column_config.LinkColumn(),
        })

        # Shkarkimi i CV-së
        with_cv = filtered[filtered["cv_name"].notna()]
        if not with_cv.empty:
            names = dict(zip(with_cv["id"], with_cv["full_name"] + " – " + with_cv["cv_name"]))
            cv_id = st.selectbox(t("cv_select"), list(names), format_func=names.get)
            st.download_button(t("cv_download"), load_cv(cv_id), icon=":material/download:",
                               file_name=with_cv.set_index("id").at[cv_id, "cv_name"],
                               mime="application/pdf")

        # Grafiku sipas profesionit
        st.markdown(f'<p class="section-title">{t("by_profession")}</p>', unsafe_allow_html=True)
        counts = df["profession"].map(profession_label).value_counts()
        st.bar_chart(counts, color="#1e5a4c")

        # Shkarkimi
        st.download_button(t("download"), table.to_csv(index=False).encode("utf-8-sig"),
                           icon=":material/download:",
                           file_name="kandidatet_roi_hunting.csv", mime="text/csv")

    st.write("")
    if st.button(t("logout"), icon=":material/logout:"):
        st.session_state["admin_ok"] = False
        st.rerun()


# ============================================================
# 9. NISJA E APLIKACIONIT
# ============================================================
def main():
    st.set_page_config(page_title="ROI Hunting", page_icon="🎯", layout="centered")
    css = CSS.replace("__OFFICE_BG__", office_background()).replace("__HERO_ART__", hero_art())
    st.markdown(css, unsafe_allow_html=True)
    init_db()
    language_switch()

    with st.sidebar:
        st.markdown("## ROI Hunting")
        # Menyja ruan indeksin e faqes, që të mos humbet kur ndërrohet gjuha
        labels = [f":material/person_add: {t('nav_register')}", f":material/dashboard: {t('nav_admin')}"]
        choice = st.radio(t("menu"), labels, index=st.session_state.get("page_index", 0))
        st.session_state["page_index"] = labels.index(choice)

    page = st.session_state["page_index"]
    with st.container(key=f"page_{page}"):
        if page == 0:
            registration_page()
        else:
            admin_page()


if __name__ == "__main__":
    main()
