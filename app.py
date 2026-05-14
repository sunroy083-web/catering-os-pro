
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
from io import BytesIO

DB_PATH = "catering_os_pro.db"

st.set_page_config(
    page_title="CateringOS Pro",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
html, body, [class*="css"] { direction: rtl; text-align: right; }
textarea, input, select { direction: rtl; text-align: right; }
.main .block-container { padding-top: 1.2rem; }
.card {
    padding: 18px;
    border-radius: 18px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    margin-bottom: 12px;
}
.title {font-size: 34px; font-weight: 900; margin-bottom: 0px;}
.muted {color: #64748b; font-size: 14px;}
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
        name TEXT, phone TEXT, source TEXT, event_type TEXT, event_date TEXT,
        location TEXT, guests INTEGER, food_style TEXT, serving TEXT, budget TEXT,
        kosher TEXT, allergies TEXT, notes TEXT, status TEXT, ai_summary TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, category TEXT, food_style TEXT, gram_per_person REAL,
        cost_per_kg REAL, sale_price_extra REAL, notes TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, description TEXT, price_per_person REAL, min_guests INTEGER, notes TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER, client_name TEXT, phone TEXT, event_type TEXT, event_date TEXT,
        event_time TEXT, location TEXT, guests INTEGER, package_name TEXT,
        price_per_person REAL, staff_cost REAL, delivery_cost REAL, discount REAL,
        total_price REAL, paid REAL, production_notes TEXT, status TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER, title TEXT, owner TEXT, due_date TEXT, status TEXT, notes TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lead_id INTEGER, client_name TEXT, phone TEXT, due_date TEXT, reason TEXT,
        message TEXT, status TEXT
    )""")
    c.commit()
    seed_data(c)
    c.close()

def table_count(c, table):
    return pd.read_sql_query(f"SELECT COUNT(*) as n FROM {table}", c)["n"].iloc[0]

def seed_data(c):
    if table_count(c, "menu_items") == 0:
        rows = [
            ("פרגית", "עיקרית", "בשרי", 180, 42, 0, "מתאים לבופה"),
            ("שניצלונים לילדים", "ילדים", "בשרי", 120, 35, 0, ""),
            ("אורז", "תוספת", "כללי", 120, 9, 0, ""),
            ("תפוחי אדמה", "תוספת", "כללי", 150, 8, 0, ""),
            ("סלטים", "פתיחה", "כללי", 150, 18, 0, "סך כל הסלטים"),
            ("לחם / חלות", "לחם", "כללי", 70, 16, 0, ""),
            ("קינוחים", "קינוח", "כללי", 90, 28, 0, ""),
            ("פסטה", "עיקרית", "חלבי", 180, 12, 0, ""),
            ("קישים", "עיקרית", "חלבי", 120, 35, 0, ""),
            ("גבינות", "פתיחה", "חלבי", 80, 55, 0, ""),
        ]
        c.executemany("""INSERT INTO menu_items 
            (name, category, food_style, gram_per_person, cost_per_kg, sale_price_extra, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)""", rows)
    if table_count(c, "packages") == 0:
        rows = [
            ("בשרי בסיסי", "בופה בשרי לאירועים משפחתיים", 120, 40, "כולל עיקריות, תוספות וסלטים"),
            ("בשרי פרימיום", "תפריט עשיר עם יותר בחירה ובשרים משודרגים", 180, 50, "מתאים לבר מצווה/אירוע יוקרתי"),
            ("חלבי אירוח", "פסטות, קישים, סלטים, גבינות וקינוחים", 110, 30, "מתאים לבראנץ׳/אירוע חברה"),
            ("מגשי אירוח", "מגשים מוכנים להגשה", 85, 20, "מתאים למשרדים ובתים"),
        ]
        c.executemany("""INSERT INTO packages (name, description, price_per_person, min_guests, notes)
                         VALUES (?, ?, ?, ?, ?)""", rows)
    c.commit()

def df_query(query, params=()):
    c = conn()
    df = pd.read_sql_query(query, c, params=params)
    c.close()
    return df

def execute(query, params=()):
    c = conn()
    cur = c.cursor()
    cur.execute(query, params)
    c.commit()
    last_id = cur.lastrowid
    c.close()
    return last_id

def export_excel():
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for table in ["leads", "events", "menu_items", "packages", "tasks", "followups"]:
            df_query(f"SELECT * FROM {table}").to_excel(writer, index=False, sheet_name=table[:31])
    return buffer.getvalue()

def lead_summary_text(lead):
    return f"""
סיכום ליד:
לקוח: {lead.get('name')}
טלפון: {lead.get('phone')}
אירוע: {lead.get('event_type')} בתאריך {lead.get('event_date')}
מיקום: {lead.get('location')}
כמות: {lead.get('guests')} אורחים
סגנון: {lead.get('food_style')}
הגשה: {lead.get('serving')}
תקציב: {lead.get('budget')}
כשרות: {lead.get('kosher')}
אלרגיות: {lead.get('allergies')}
הערות: {lead.get('notes')}

שאלות שחסרות לרוב:
1. שעה מדויקת.
2. האם צריך ציוד/שולחנות/כלים.
3. האם צריך מלצרים.
4. האם יש ילדים/צמחונים/טבעונים.
5. האם יש גישה נוחה לפריקה וחניה.
6. האם המחיר צריך לכלול מע״מ/הובלה.
"""

def quote_text(lead, package, staff_cost, delivery_cost, discount):
    total = lead["guests"] * package["price_per_person"] + staff_cost + delivery_cost - discount
    return f"""שלום {lead['name']},

בהמשך לפנייתך לגבי {lead['event_type']} בתאריך {lead['event_date']} ב{lead['location']},
נשמח לתת לכם מענה לקייטרינג {lead['food_style']} עבור כ-{lead['guests']} אורחים.

הצעה מומלצת: {package['name']}
{package['description']}

מה כלול:
• התאמת תפריט לאופי האירוע
• תיאום מלא לפני האירוע
• הכנת דף הפקה מסודר לצוות
• התייחסות לכשרות, אלרגיות והערות מיוחדות
• צורת הגשה: {lead['serving']}

מחיר:
{package['price_per_person']:.0f} ₪ לאדם × {lead['guests']} אורחים
צוות/מלצרים: {staff_cost:.0f} ₪
הובלה/ציוד: {delivery_cost:.0f} ₪
הנחה: {discount:.0f} ₪

סה״כ משוער: {total:,.0f} ₪

הערות:
כשרות: {lead['kosher']}
אלרגיות: {lead['allergies']}
{lead['notes']}

נשמח לסגור איתך תפריט סופי ולהתקדם.
"""

def ai_prompt_pack(lead):
    return f"""העתק את זה ל-ChatGPT / Claude:

אתה סוכן AI מקצועי לקייטרינג. תפקידך להפוך ליד להצעת מחיר ודף הפקה.
נתוני הליד:
{lead_summary_text(lead)}

החזר:
1. סיכום מנהלים קצר.
2. שאלות חסרות ללקוח.
3. הצעת תפריט ראשונית.
4. סיכונים שצריך לשים לב אליהם.
5. הודעת וואטסאפ ללקוח.
6. משימות לצוות.
"""

def production_doc(event):
    return f"""דף הפקה לאירוע

לקוח: {event['client_name']}
טלפון: {event['phone']}
סוג אירוע: {event['event_type']}
תאריך: {event['event_date']}
שעה: {event['event_time']}
כתובת: {event['location']}
כמות אורחים: {event['guests']}
חבילה: {event['package_name']}

מחיר:
מחיר לאדם: {event['price_per_person']:.0f} ₪
סה״כ: {event['total_price']:.0f} ₪
שולם: {event['paid']:.0f} ₪
יתרה: {event['total_price'] - event['paid']:.0f} ₪

הערות הפקה:
{event['production_notes']}

צ׳ק ליסט:
□ לוודא תפריט סופי
□ לוודא כמות אורחים סופית
□ לוודא כשרות ואלרגיות
□ להדפיס דף הפקה
□ להכין רשימת קניות
□ לשבץ צוות
□ לוודא שעת יציאה
□ לבדוק כתובת וחניה
□ לבדוק יתרה לתשלום
"""

init_db()

st.sidebar.title("🍽️ CateringOS Pro")
page = st.sidebar.radio("ניווט", [
    "דשבורד",
    "לידים",
    "סוכן הצעות מחיר",
    "אירועים ודפי הפקה",
    "רשימת קניות חכמה",
    "תפריטים ומחירון",
    "משימות ופולואפים",
    "AI Lab",
    "ייצוא וגיבוי"
])

st.sidebar.download_button("⬇️ גיבוי מלא לאקסל", data=export_excel(), file_name="catering_os_backup.xlsx")

st.markdown('<p class="title">CateringOS Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="muted">מערכת AI/אוטומציה פנימית לקייטרינג: מכירות, אירועים, הפקה, קניות, משימות ודאטה.</p>', unsafe_allow_html=True)

if page == "דשבורד":
    leads = df_query("SELECT * FROM leads")
    events = df_query("SELECT * FROM events")
    followups = df_query("SELECT * FROM followups")
    tasks = df_query("SELECT * FROM tasks")
    today = str(date.today())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("לידים", len(leads))
    c2.metric("אירועים סגורים", len(events))
    c3.metric("מחזור משוער", f"{events['total_price'].sum():,.0f} ₪" if len(events) else "0 ₪")
    c4.metric("פולואפים פתוחים", len(followups[followups["status"] != "בוצע"]) if len(followups) else 0)

    st.subheader("מה דורש טיפול עכשיו")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### פולואפים")
        if len(followups):
            st.dataframe(followups[followups["status"] != "בוצע"].sort_values("due_date"), use_container_width=True)
        else:
            st.info("אין פולואפים כרגע.")
    with col2:
        st.markdown("### משימות")
        if len(tasks):
            st.dataframe(tasks[tasks["status"] != "בוצע"].sort_values("due_date"), use_container_width=True)
        else:
            st.info("אין משימות כרגע.")

elif page == "לידים":
    st.header("מערכת לידים")
    with st.form("lead_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("שם לקוח")
            phone = st.text_input("טלפון")
            source = st.selectbox("מקור פנייה", ["וואטסאפ", "אינסטגרם", "טלפון", "אתר", "חבר/המלצה", "אחר"])
            event_type = st.selectbox("סוג אירוע", ["בר מצווה", "בת מצווה", "חתונה קטנה", "שבת חתן", "אירוע חברה", "יום הולדת", "אזכרה", "אחר"])
        with c2:
            event_date = st.date_input("תאריך אירוע")
            location = st.text_input("מיקום")
            guests = st.number_input("כמות אורחים", min_value=1, value=80)
            food_style = st.selectbox("סגנון אוכל", ["בשרי", "חלבי", "מגשי אירוח", "טבעוני/צמחוני", "מעורב"])
        with c3:
            serving = st.selectbox("צורת הגשה", ["בופה", "הגשה לשולחן", "מגשים", "דוכנים", "אחר"])
            budget = st.text_input("תקציב")
            kosher = st.text_input("כשרות")
            allergies = st.text_input("אלרגיות / רגישויות")
        notes = st.text_area("הערות")
        submitted = st.form_submit_button("שמור ליד")

    if submitted:
        lead_dict = {
            "name": name, "phone": phone, "source": source, "event_type": event_type,
            "event_date": str(event_date), "location": location, "guests": int(guests),
            "food_style": food_style, "serving": serving, "budget": budget,
            "kosher": kosher, "allergies": allergies, "notes": notes
        }
        ai_summary = lead_summary_text(lead_dict)
        lead_id = execute("""INSERT INTO leads 
        (created_at, name, phone, source, event_type, event_date, location, guests, food_style, serving, budget, kosher, allergies, notes, status, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(), name, phone, source, event_type, str(event_date), location, guests, food_style, serving, budget, kosher, allergies, notes, "חדש", ai_summary))
        execute("""INSERT INTO followups (lead_id, client_name, phone, due_date, reason, message, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (lead_id, name, phone, str(date.today() + timedelta(days=1)), "פולואפ ליד חדש",
                 f"היי {name}, רציתי לוודא שקיבלת את הפרטים לגבי הקייטרינג ונשמח להתקדם להצעה מסודרת.", "פתוח"))
        st.success("הליד נשמר ונוצר פולואפ למחר.")

    leads = df_query("SELECT * FROM leads ORDER BY id DESC")
    st.dataframe(leads, use_container_width=True)

elif page == "סוכן הצעות מחיר":
    st.header("סוכן הצעות מחיר")
    leads = df_query("SELECT * FROM leads ORDER BY id DESC")
    packages = df_query("SELECT * FROM packages")
    if len(leads) == 0:
        st.warning("קודם תכניס ליד.")
    else:
        lead_label = st.selectbox("בחר ליד", [f"{r.id} | {r.name} | {r.event_type} | {r.guests} אורחים" for r in leads.itertuples()])
        lead_id = int(lead_label.split("|")[0].strip())
        lead = leads[leads["id"] == lead_id].iloc[0].to_dict()

        package_label = st.selectbox("בחר חבילה", [f"{r.id} | {r.name} | {r.price_per_person:.0f} ₪ לאדם" for r in packages.itertuples()])
        package_id = int(package_label.split("|")[0].strip())
        package = packages[packages["id"] == package_id].iloc[0].to_dict()

        c1, c2, c3 = st.columns(3)
        staff_cost = c1.number_input("צוות/מלצרים", min_value=0.0, value=0.0, step=50.0)
        delivery_cost = c2.number_input("הובלה/ציוד", min_value=0.0, value=250.0, step=50.0)
        discount = c3.number_input("הנחה", min_value=0.0, value=0.0, step=50.0)

        total = lead["guests"] * package["price_per_person"] + staff_cost + delivery_cost - discount
        st.metric("סה״כ הצעה", f"{total:,.0f} ₪")

        quote = quote_text(lead, package, staff_cost, delivery_cost, discount)
        st.text_area("הצעת מחיר מוכנה", quote, height=430)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("הפוך לאירוע סגור"):
                event_id = execute("""INSERT INTO events 
                (lead_id, client_name, phone, event_type, event_date, event_time, location, guests, package_name, price_per_person, staff_cost, delivery_cost, discount, total_price, paid, production_notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (lead["id"], lead["name"], lead["phone"], lead["event_type"], lead["event_date"], "", lead["location"], lead["guests"], package["name"], package["price_per_person"], staff_cost, delivery_cost, discount, total, 0, lead["notes"], "סגור"))
                for title, days in [("לוודא כמות אורחים סופית", -7), ("לסגור תפריט סופי", -5), ("להכין רשימת קניות", -3), ("לשבץ צוות", -3), ("לוודא ציוד והעמסה", -1)]:
                    try:
                        due = str(datetime.fromisoformat(lead["event_date"]).date() + timedelta(days=days))
                    except Exception:
                        due = str(date.today())
                    execute("""INSERT INTO tasks (event_id, title, owner, due_date, status, notes)
                               VALUES (?, ?, ?, ?, ?, ?)""", (event_id, title, "", due, "פתוח", "נוצר אוטומטית"))
                execute("UPDATE leads SET status=? WHERE id=?", ("נסגר", lead["id"]))
                st.success("נוצר אירוע + משימות אוטומטיות.")
        with col_b:
            st.text_area("פרומפט AI מתקדם", ai_prompt_pack(lead), height=240)

elif page == "אירועים ודפי הפקה":
    st.header("אירועים ודפי הפקה")
    events = df_query("SELECT * FROM events ORDER BY event_date DESC")
    if len(events) == 0:
        st.info("אין אירועים עדיין.")
    else:
        st.dataframe(events, use_container_width=True)
        event_label = st.selectbox("בחר אירוע לדף הפקה", [f"{r.id} | {r.client_name} | {r.event_type} | {r.event_date}" for r in events.itertuples()])
        event_id = int(event_label.split("|")[0].strip())
        event = events[events["id"] == event_id].iloc[0].to_dict()

        new_notes = st.text_area("הערות הפקה", event["production_notes"] or "", height=120)
        paid = st.number_input("שולם", min_value=0.0, value=float(event["paid"] or 0), step=100.0)
        event_time = st.text_input("שעת אירוע", event["event_time"] or "")
        if st.button("עדכן אירוע"):
            execute("UPDATE events SET production_notes=?, paid=?, event_time=? WHERE id=?", (new_notes, paid, event_time, event_id))
            st.success("עודכן. רענן/בחר שוב כדי לראות.")
        event["production_notes"] = new_notes
        event["paid"] = paid
        event["event_time"] = event_time
        st.text_area("דף הפקה מוכן להעתקה", production_doc(event), height=500)

elif page == "רשימת קניות חכמה":
    st.header("רשימת קניות חכמה")
    events = df_query("SELECT * FROM events ORDER BY event_date DESC")
    menu = df_query("SELECT * FROM menu_items")
    if len(events) == 0:
        guests = st.number_input("כמות אורחים", min_value=1, value=80)
        event_name = "אירוע ידני"
    else:
        event_label = st.selectbox("בחר אירוע", [f"{r.id} | {r.client_name} | {r.event_date} | {r.guests} אורחים" for r in events.itertuples()])
        event_id = int(event_label.split("|")[0].strip())
        ev = events[events["id"] == event_id].iloc[0]
        guests = int(ev["guests"])
        event_name = f"{ev['client_name']} - {ev['event_date']}"

    st.write(f"חישוב עבור: **{event_name}**, **{guests} אורחים**")
    edited = st.data_editor(menu[["name", "category", "food_style", "gram_per_person", "cost_per_kg", "notes"]], num_rows="dynamic", use_container_width=True)
    edited["quantity_kg"] = (edited["gram_per_person"] * guests / 1000).round(2)
    edited["estimated_cost"] = (edited["quantity_kg"] * edited["cost_per_kg"]).round(2)
    st.metric("עלות חומרי גלם משוערת", f"{edited['estimated_cost'].sum():,.0f} ₪")
    st.dataframe(edited, use_container_width=True)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        edited.to_excel(writer, index=False, sheet_name="רשימת קניות")
    st.download_button("הורד רשימת קניות", data=buffer.getvalue(), file_name="shopping_list.xlsx")

elif page == "תפריטים ומחירון":
    st.header("תפריטים ומחירון")
    st.subheader("פריטי תפריט")
    menu = df_query("SELECT * FROM menu_items")
    st.dataframe(menu, use_container_width=True)
    with st.expander("הוסף פריט תפריט"):
        with st.form("add_menu"):
            c1, c2, c3 = st.columns(3)
            name = c1.text_input("שם פריט")
            category = c2.text_input("קטגוריה")
            food_style = c3.text_input("סגנון")
            gram = c1.number_input("גרם לאדם", min_value=0.0, value=100.0)
            cost = c2.number_input("עלות לק״ג", min_value=0.0, value=10.0)
            notes = c3.text_input("הערות")
            if st.form_submit_button("הוסף"):
                execute("""INSERT INTO menu_items (name, category, food_style, gram_per_person, cost_per_kg, sale_price_extra, notes)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""", (name, category, food_style, gram, cost, 0, notes))
                st.success("נוסף.")

    st.subheader("חבילות מחיר")
    packages = df_query("SELECT * FROM packages")
    st.dataframe(packages, use_container_width=True)
    with st.expander("הוסף חבילה"):
        with st.form("add_package"):
            p_name = st.text_input("שם חבילה")
            desc = st.text_area("תיאור")
            price = st.number_input("מחיר לאדם", min_value=0.0, value=120.0)
            min_g = st.number_input("מינימום אורחים", min_value=1, value=30)
            notes = st.text_input("הערות")
            if st.form_submit_button("הוסף חבילה"):
                execute("""INSERT INTO packages (name, description, price_per_person, min_guests, notes)
                           VALUES (?, ?, ?, ?, ?)""", (p_name, desc, price, min_g, notes))
                st.success("נוספה.")

elif page == "משימות ופולואפים":
    st.header("משימות ופולואפים")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("משימות")
        tasks = df_query("SELECT * FROM tasks ORDER BY due_date")
        st.dataframe(tasks, use_container_width=True)
        if len(tasks):
            task_id = st.number_input("ID משימה לסימון כבוצע", min_value=1, value=int(tasks["id"].iloc[0]))
            if st.button("סמן משימה כבוצעה"):
                execute("UPDATE tasks SET status=? WHERE id=?", ("בוצע", task_id))
                st.success("סומן.")
    with c2:
        st.subheader("פולואפים")
        followups = df_query("SELECT * FROM followups ORDER BY due_date")
        st.dataframe(followups, use_container_width=True)
        if len(followups):
            f_id = st.number_input("ID פולואפ לסימון כבוצע", min_value=1, value=int(followups["id"].iloc[0]))
            if st.button("סמן פולואפ כבוצע"):
                execute("UPDATE followups SET status=? WHERE id=?", ("בוצע", f_id))
                st.success("סומן.")

elif page == "AI Lab":
    st.header("AI Lab - פרומפטים וסוכנים")
    st.info("המערכת לא מחוברת כרגע ל-API בתשלום. כאן יש סוכנים מוכנים להעתקה ל-ChatGPT/Claude.")
    agents = {
        "סוכן מכירות": """אתה סוכן מכירות לקייטרינג. קבל פרטי ליד והחזר הודעת וואטסאפ, שאלות חסרות והצעה ראשונית.""",
        "סוכן תפעול": """אתה מנהל תפעול לקייטרינג. קבל פרטי אירוע והחזר דף הפקה, רשימת ציוד, סיכונים ומשימות.""",
        "סוכן קניות": """אתה מנהל רכש. קבל תפריט וכמות אורחים והחזר רשימת קניות מחושבת לפי גרמים לאדם, כולל מרווח ביטחון.""",
        "סוכן שיווק": """אתה מנהל שיווק לקייטרינג. צור 10 רעיונות לרילסים, 5 סטוריז ו-3 הודעות מכירה לפי סוג האירוע.""",
        "סוכן ניתוח עסקי": """אתה אנליסט עסקי. קבל טבלת לידים/אירועים והחזר תובנות: מקורות טובים, אחוז סגירה, מחיר ממוצע ואיפה לשפר."""
    }
    selected_agent = st.selectbox("בחר סוכן", list(agents.keys()))
    context = st.text_area("הדבק כאן נתונים", height=180)
    prompt = f"{agents[selected_agent]}\n\nנתונים:\n{context}\n\nהחזר תשובה בעברית, מסודרת, פרקטית וקצרה."
    st.text_area("פרומפט מוכן", prompt, height=260)

elif page == "ייצוא וגיבוי":
    st.header("ייצוא וגיבוי")
    st.download_button("הורד גיבוי מלא לאקסל", data=export_excel(), file_name=f"catering_os_backup_{date.today()}.xlsx")
    st.subheader("טבלאות")
    for table in ["leads", "events", "menu_items", "packages", "tasks", "followups"]:
        with st.expander(table):
            st.dataframe(df_query(f"SELECT * FROM {table}"), use_container_width=True)
