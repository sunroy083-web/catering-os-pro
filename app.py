
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
from io import BytesIO

DB_PATH = "catering_mobile_pro.db"

st.set_page_config(
    page_title="CateringOS Mobile Pro",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
html, body, [class*="css"] {
    direction: rtl;
    text-align: right;
}
.block-container {
    padding-top: 0.8rem;
    padding-left: 0.8rem;
    padding-right: 0.8rem;
    max-width: 760px;
}
h1, h2, h3 {
    text-align: right;
}
.stButton > button {
    width: 100%;
    border-radius: 18px;
    padding: 0.85rem 1rem;
    font-size: 18px;
    font-weight: 800;
}
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    border-radius: 14px;
    font-size: 16px;
}
.card {
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    padding: 16px;
    margin: 10px 0;
    background: rgba(250,250,250,0.04);
}
.big {
    font-size: 30px;
    font-weight: 900;
    line-height: 1.2;
}
.muted {
    color: #7c8798;
    font-size: 14px;
}
.pill {
    display: inline-block;
    border: 1px solid #e5e7eb;
    border-radius: 999px;
    padding: 6px 12px;
    margin: 3px;
    font-size: 13px;
}
textarea {
    min-height: 150px;
}
</style>
""", unsafe_allow_html=True)

def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    c = conn()
    cur = c.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        name TEXT,
        phone TEXT,
        source TEXT,
        event_type TEXT,
        event_date TEXT,
        event_time TEXT,
        location TEXT,
        guests INTEGER,
        food_style TEXT,
        serving TEXT,
        budget TEXT,
        kosher TEXT,
        allergies TEXT,
        equipment TEXT,
        staff_needed TEXT,
        notes TEXT,
        status TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER,
        created_at TEXT,
        client_name TEXT,
        phone TEXT,
        event_type TEXT,
        event_date TEXT,
        event_time TEXT,
        location TEXT,
        guests INTEGER,
        food_style TEXT,
        serving TEXT,
        package_name TEXT,
        price_per_person REAL,
        staff_cost REAL,
        delivery_cost REAL,
        discount REAL,
        total_price REAL,
        paid REAL,
        notes TEXT,
        status TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        gram_per_person REAL,
        cost_per_kg REAL,
        default_on INTEGER
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price_per_person REAL,
        description TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        title TEXT,
        due_date TEXT,
        status TEXT
    )
    """)
    c.commit()
    seed(c)
    c.close()

def seed(c):
    cur = c.cursor()
    if pd.read_sql_query("SELECT COUNT(*) n FROM items", c)["n"][0] == 0:
        rows = [
            ("פרגית", "עיקרית", 180, 42, 1),
            ("קבב / בשר טחון", "עיקרית", 150, 38, 0),
            ("שניצלונים לילדים", "ילדים", 120, 35, 0),
            ("אורז", "תוספת", 120, 9, 1),
            ("תפוחי אדמה", "תוספת", 150, 8, 1),
            ("ירקות אנטיפסטי", "תוספת", 120, 12, 0),
            ("סלטים", "פתיחה", 150, 18, 1),
            ("טחינה / חומוס", "פתיחה", 80, 16, 1),
            ("לחם / חלות", "לחם", 70, 16, 1),
            ("קינוחים", "קינוח", 90, 28, 1),
            ("שתייה", "שתייה", 350, 4, 0),
            ("קרח", "ציוד/צריכה", 80, 5, 0),
        ]
        cur.executemany("INSERT INTO items (name, category, gram_per_person, cost_per_kg, default_on) VALUES (?, ?, ?, ?, ?)", rows)
    if pd.read_sql_query("SELECT COUNT(*) n FROM packages", c)["n"][0] == 0:
        rows = [
            ("בשרי בסיסי", 120, "תפריט בופה בסיסי: עיקרית, תוספות, סלטים ולחם"),
            ("בשרי פרימיום", 180, "תפריט עשיר לאירוע יוקרתי יותר"),
            ("חלבי אירוח", 110, "פסטות, קישים, סלטים, גבינות וקינוחים"),
            ("מגשי אירוח", 85, "מגשים מוכנים להגשה לבית או משרד"),
        ]
        cur.executemany("INSERT INTO packages (name, price_per_person, description) VALUES (?, ?, ?)", rows)
    c.commit()

def run(query, params=()):
    c = conn()
    cur = c.cursor()
    cur.execute(query, params)
    c.commit()
    last = cur.lastrowid
    c.close()
    return last

def q(query, params=()):
    c = conn()
    df = pd.read_sql_query(query, c, params=params)
    c.close()
    return df

def money(x):
    try:
        return f"{float(x):,.0f} ₪"
    except:
        return "0 ₪"

def lead_card(row):
    st.markdown(f"""
    <div class="card">
      <b>{row['name']}</b> · {row['event_type']}<br>
      <span class="muted">{row['event_date']} · {row['guests']} אורחים · {row['location']}</span><br>
      <span class="pill">{row['status']}</span>
      <span class="pill">{row['food_style']}</span>
    </div>
    """, unsafe_allow_html=True)

def event_card(row):
    balance = float(row["total_price"] or 0) - float(row["paid"] or 0)
    st.markdown(f"""
    <div class="card">
      <b>{row['client_name']}</b> · {row['event_type']}<br>
      <span class="muted">{row['event_date']} {row['event_time']} · {row['guests']} אורחים</span><br>
      <span class="pill">סה״כ {money(row['total_price'])}</span>
      <span class="pill">יתרה {money(balance)}</span>
      <span class="pill">{row['status']}</span>
    </div>
    """, unsafe_allow_html=True)

def whatsapp_quote(lead, package, staff_cost, delivery_cost, discount):
    total = lead["guests"] * package["price_per_person"] + staff_cost + delivery_cost - discount
    return f"""היי {lead['name']}, איזה כיף שפניתם אלינו 🙏

לפי הפרטים:
• אירוע: {lead['event_type']}
• תאריך: {lead['event_date']}
• מיקום: {lead['location']}
• כמות: כ-{lead['guests']} אורחים
• סגנון: {lead['food_style']}
• הגשה: {lead['serving']}

ההצעה המומלצת:
{package['name']} — {package['description']}

מחיר:
{package['price_per_person']:.0f} ₪ לאדם × {lead['guests']} אורחים
צוות/מלצרים: {staff_cost:.0f} ₪
הובלה/ציוד: {delivery_cost:.0f} ₪
הנחה: {discount:.0f} ₪

סה״כ משוער: {total:,.0f} ₪

כשרות/אלרגיות:
{lead['kosher']} | {lead['allergies']}

כדי לדייק את ההצעה סופית, נשמח לוודא:
1. שעת האירוע
2. האם צריך שולחנות/כלים/חימום
3. כמות ילדים/צמחונים/טבעונים
4. האם יש חניה וגישה נוחה לפריקה
"""

def production_text(event):
    balance = float(event["total_price"] or 0) - float(event["paid"] or 0)
    return f"""🍽️ דף הפקה לאירוע

לקוח: {event['client_name']}
טלפון: {event['phone']}
אירוע: {event['event_type']}
תאריך: {event['event_date']}
שעה: {event['event_time']}
כתובת: {event['location']}
כמות אורחים: {event['guests']}
סגנון: {event['food_style']}
הגשה: {event['serving']}
חבילה: {event['package_name']}

כסף:
סה״כ: {money(event['total_price'])}
שולם: {money(event['paid'])}
יתרה: {money(balance)}

הערות:
{event['notes']}

צ׳ק ליסט:
□ לוודא כמות אורחים סופית
□ לוודא תפריט סופי
□ לבדוק אלרגיות וכשרות
□ להכין רשימת קניות
□ לשבץ צוות
□ להעמיס ציוד
□ לוודא כתובת וחניה
□ לוודא יתרה לתשלום
□ לצלם תוכן לשיווק אחרי האירוע
"""

def ai_prompt():
    return """אתה מנהל קייטרינג מקצועי וסוכן AI תפעולי.
קבל פרטי אירוע והחזר:
1. סיכום קצר וברור
2. שאלות חסרות ללקוח
3. הצעת תפריט מומלצת
4. רשימת קניות לפי קטגוריות
5. ציוד שצריך להעמיס
6. סיכונים באירוע
7. הודעת וואטסאפ ללקוח
8. משימות לצוות

פרטי האירוע:
[להדביק כאן]
"""

def export_all():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for t in ["leads", "events", "items", "packages", "tasks"]:
            q(f"SELECT * FROM {t}").to_excel(writer, index=False, sheet_name=t)
    return buffer.getvalue()

init_db()

st.markdown('<div class="big">🍽️ CateringOS Mobile Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="muted">מערכת מובייל לקייטרינג: לידים, הצעות, אירועים, קניות, הפקה ו-AI.</div>', unsafe_allow_html=True)

menu = st.radio(
    "ניווט",
    ["🏠 בית", "➕ ליד", "💬 הצעה", "📅 אירועים", "🛒 קניות", "✅ משימות", "🤖 AI", "⚙️ הגדרות"],
    horizontal=False,
    label_visibility="collapsed"
)

if menu == "🏠 בית":
    leads = q("SELECT * FROM leads ORDER BY id DESC")
    events = q("SELECT * FROM events ORDER BY event_date DESC")
    tasks = q("SELECT * FROM tasks WHERE status!='בוצע' ORDER BY due_date")
    c1, c2 = st.columns(2)
    c1.metric("לידים", len(leads))
    c2.metric("אירועים", len(events))
    c3, c4 = st.columns(2)
    c3.metric("משימות פתוחות", len(tasks))
    c4.metric("מחזור", money(events["total_price"].sum() if len(events) else 0))

    st.subheader("פעולות מהירות")
    st.info("בחר למעלה: ➕ ליד חדש, 💬 הצעה, 📅 אירועים, 🛒 קניות.")

    st.subheader("לידים אחרונים")
    if len(leads):
        for _, row in leads.head(5).iterrows():
            lead_card(row)
    else:
        st.write("אין לידים עדיין.")

elif menu == "➕ ליד":
    st.subheader("➕ ליד חדש")
    with st.form("lead_form", clear_on_submit=True):
        name = st.text_input("שם לקוח")
        phone = st.text_input("טלפון")
        source = st.selectbox("מקור", ["וואטסאפ", "אינסטגרם", "טלפון", "אתר", "המלצה", "אחר"])
        event_type = st.selectbox("סוג אירוע", ["בר מצווה", "בת מצווה", "חתונה קטנה", "שבת חתן", "אירוע חברה", "יום הולדת", "אזכרה", "אחר"])
        event_date = st.date_input("תאריך")
        event_time = st.text_input("שעה", placeholder="לדוגמה 19:30")
        location = st.text_input("מיקום")
        guests = st.number_input("כמות אורחים", min_value=1, value=80)
        food_style = st.selectbox("סגנון אוכל", ["בשרי", "חלבי", "מגשי אירוח", "טבעוני/צמחוני", "מעורב"])
        serving = st.selectbox("הגשה", ["בופה", "הגשה לשולחן", "מגשים", "דוכנים", "אחר"])
        budget = st.text_input("תקציב")
        kosher = st.text_input("כשרות")
        allergies = st.text_input("אלרגיות")
        equipment = st.text_input("ציוד נדרש")
        staff_needed = st.text_input("צוות/מלצרים")
        notes = st.text_area("הערות")
        if st.form_submit_button("שמור ליד"):
            run("""INSERT INTO leads 
            (created_at,name,phone,source,event_type,event_date,event_time,location,guests,food_style,serving,budget,kosher,allergies,equipment,staff_needed,notes,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().isoformat(), name, phone, source, event_type, str(event_date), event_time, location, guests, food_style, serving, budget, kosher, allergies, equipment, staff_needed, notes, "חדש"))
            st.success("הליד נשמר ✅")

    st.subheader("כל הלידים")
    leads = q("SELECT * FROM leads ORDER BY id DESC")
    for _, row in leads.iterrows():
        lead_card(row)

elif menu == "💬 הצעה":
    st.subheader("💬 סוכן הצעות מחיר")
    leads = q("SELECT * FROM leads ORDER BY id DESC")
    packages = q("SELECT * FROM packages ORDER BY id")
    if len(leads) == 0:
        st.warning("אין לידים. קודם תוסיף ליד.")
    else:
        lead_choice = st.selectbox("בחר ליד", [f"{r.id} | {r.name} | {r.event_type} | {r.guests}" for r in leads.itertuples()])
        lead_id = int(lead_choice.split("|")[0].strip())
        lead = leads[leads.id == lead_id].iloc[0].to_dict()

        pack_choice = st.selectbox("בחר חבילה", [f"{r.id} | {r.name} | {r.price_per_person:.0f} ₪" for r in packages.itertuples()])
        pack_id = int(pack_choice.split("|")[0].strip())
        package = packages[packages.id == pack_id].iloc[0].to_dict()

        staff_cost = st.number_input("צוות/מלצרים", min_value=0.0, value=0.0, step=50.0)
        delivery_cost = st.number_input("הובלה/ציוד", min_value=0.0, value=250.0, step=50.0)
        discount = st.number_input("הנחה", min_value=0.0, value=0.0, step=50.0)
        total = lead["guests"] * package["price_per_person"] + staff_cost + delivery_cost - discount
        st.metric("סה״כ הצעה", money(total))

        txt = whatsapp_quote(lead, package, staff_cost, delivery_cost, discount)
        st.text_area("הודעת וואטסאפ מוכנה", txt, height=390)

        if st.button("סגור והפוך לאירוע"):
            event_id = run("""INSERT INTO events
            (lead_id,created_at,client_name,phone,event_type,event_date,event_time,location,guests,food_style,serving,package_name,price_per_person,staff_cost,delivery_cost,discount,total_price,paid,notes,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (lead["id"], datetime.now().isoformat(), lead["name"], lead["phone"], lead["event_type"], lead["event_date"], lead["event_time"], lead["location"], lead["guests"], lead["food_style"], lead["serving"], package["name"], package["price_per_person"], staff_cost, delivery_cost, discount, total, 0, lead["notes"], "סגור"))
            run("UPDATE leads SET status='נסגר' WHERE id=?", (lead["id"],))
            for title, days in [("לוודא כמות אורחים", -7), ("לסגור תפריט", -5), ("להכין קניות", -3), ("לשבץ צוות", -2), ("העמסה וציוד", -1)]:
                try:
                    due = str(datetime.fromisoformat(lead["event_date"]).date() + timedelta(days=days))
                except:
                    due = str(date.today())
                run("INSERT INTO tasks (event_id,title,due_date,status) VALUES (?,?,?,?)", (event_id, title, due, "פתוח"))
            st.success("נוצר אירוע + משימות ✅")

elif menu == "📅 אירועים":
    st.subheader("📅 אירועים ודפי הפקה")
    events = q("SELECT * FROM events ORDER BY event_date DESC")
    if len(events) == 0:
        st.info("אין אירועים סגורים.")
    else:
        for _, row in events.iterrows():
            event_card(row)
        choice = st.selectbox("בחר אירוע", [f"{r.id} | {r.client_name} | {r.event_date}" for r in events.itertuples()])
        event_id = int(choice.split("|")[0].strip())
        event = events[events.id == event_id].iloc[0].to_dict()

        paid = st.number_input("עדכן שולם", min_value=0.0, value=float(event["paid"] or 0), step=100.0)
        notes = st.text_area("הערות הפקה", event["notes"] or "")
        if st.button("עדכן אירוע"):
            run("UPDATE events SET paid=?, notes=? WHERE id=?", (paid, notes, event_id))
            st.success("עודכן ✅")
            event["paid"] = paid
            event["notes"] = notes

        st.text_area("דף הפקה מוכן", production_text(event), height=450)

elif menu == "🛒 קניות":
    st.subheader("🛒 רשימת קניות חכמה")
    events = q("SELECT * FROM events ORDER BY event_date DESC")
    items = q("SELECT * FROM items ORDER BY category, name")
    if len(events):
        choice = st.selectbox("בחר אירוע", [f"{r.id} | {r.client_name} | {r.event_date} | {r.guests} אורחים" for r in events.itertuples()])
        event_id = int(choice.split("|")[0].strip())
        ev = events[events.id == event_id].iloc[0]
        guests = int(ev["guests"])
    else:
        guests = st.number_input("כמות אורחים", min_value=1, value=80)

    buffer_percent = st.slider("מרווח ביטחון באחוזים", 0, 30, 10)
    only_default = st.toggle("רק פריטים בסיסיים", value=True)
    if only_default:
        items = items[items.default_on == 1]

    calc = items.copy()
    calc["כמות ק״ג"] = (calc["gram_per_person"] * guests / 1000 * (1 + buffer_percent/100)).round(2)
    calc["עלות משוערת"] = (calc["כמות ק״ג"] * calc["cost_per_kg"]).round(0)
    calc = calc.rename(columns={
        "name": "פריט",
        "category": "קטגוריה",
        "gram_per_person": "גרם לאדם",
        "cost_per_kg": "עלות לק״ג"
    })
    st.metric("עלות חומרי גלם משוערת", money(calc["עלות משוערת"].sum()))
    st.dataframe(calc[["פריט","קטגוריה","גרם לאדם","כמות ק״ג","עלות לק״ג","עלות משוערת"]], use_container_width=True, hide_index=True)
    out = BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        calc.to_excel(writer, index=False, sheet_name="קניות")
    st.download_button("הורד קניות לאקסל", out.getvalue(), file_name="shopping_list.xlsx")

elif menu == "✅ משימות":
    st.subheader("✅ משימות")
    tasks = q("SELECT * FROM tasks ORDER BY due_date")
    if len(tasks) == 0:
        st.info("אין משימות.")
    else:
        for _, row in tasks.iterrows():
            st.markdown(f"<div class='card'><b>{row['title']}</b><br><span class='muted'>{row['due_date']} · {row['status']}</span></div>", unsafe_allow_html=True)
        task_id = st.number_input("ID משימה לסימון כבוצע", min_value=1, value=int(tasks.id.iloc[0]))
        if st.button("סמן כבוצע"):
            run("UPDATE tasks SET status='בוצע' WHERE id=?", (task_id,))
            st.success("בוצע ✅")

elif menu == "🤖 AI":
    st.subheader("🤖 AI Lab")
    st.write("פה יש פרומפטים מוכנים. מדביקים ל-ChatGPT/Claude ומקבלים תוצאה.")
    prompt_type = st.selectbox("בחר סוכן", ["סוכן קייטרינג מלא", "סוכן מכירות", "סוכן דף הפקה", "סוכן קניות", "סוכן שיווק"])
    data = st.text_area("הדבק פרטי אירוע / ליד")
    base_prompt = ai_prompt()
    if prompt_type == "סוכן מכירות":
        base_prompt = "אתה איש מכירות לקייטרינג. צור הודעת וואטסאפ, שאלות חסרות והצעה ראשונית לפי הנתונים."
    elif prompt_type == "סוכן דף הפקה":
        base_prompt = "אתה מנהל הפקה לקייטרינג. צור דף הפקה, ציוד, משימות וסיכונים לפי הנתונים."
    elif prompt_type == "סוכן קניות":
        base_prompt = "אתה מנהל רכש לקייטרינג. צור רשימת קניות לפי כמות אורחים, קטגוריות ומרווח ביטחון."
    elif prompt_type == "סוכן שיווק":
        base_prompt = "אתה מנהל שיווק לקייטרינג. צור רעיונות לרילסים, סטוריז ופוסטים לפי האירוע."
    final_prompt = f"{base_prompt}\n\nנתונים:\n{data}\n\nענה בעברית, קצר, פרקטי ומסודר."
    st.text_area("פרומפט מוכן להעתקה", final_prompt, height=300)

elif menu == "⚙️ הגדרות":
    st.subheader("⚙️ הגדרות וגיבוי")
    st.download_button("⬇️ הורד גיבוי מלא לאקסל", export_all(), file_name="catering_mobile_backup.xlsx")
    st.info("ב-Streamlit הנתונים יכולים להתאפס אם האפליקציה נרדמת. לעבודה עסקית קבועה צריך לחבר Google Sheets/Database.")
    st.subheader("מחירונים")
    st.dataframe(q("SELECT * FROM packages"), use_container_width=True, hide_index=True)
    st.subheader("פריטי קניות")
    st.dataframe(q("SELECT * FROM items"), use_container_width=True, hide_index=True)
