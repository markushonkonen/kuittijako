import streamlit as st
import pdfplumber

# Asetukset
IGNORE_WORDS = ["NORM.", "KAMPANJA", "RIVIALENNUS", "BONUSTA", "ALV"]

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Ostosten jako", layout="wide")
st.title("🧾 Ostosten jako")

uploaded_file = st.file_uploader("Lataa PDF-kuitti", type=["pdf"])

# 🔻 1. Valitaan yleinen yhteinen jako (valikosta)
st.sidebar.subheader("⚖️ Yhteisten ostosten jako (oletus)")
split_option = st.sidebar.selectbox(
    "Valitse jako Markus / Nella",
    options=[
        ("50/50", 0.5, 0.5),
        ("55/45", 0.55, 0.45),
        ("60/40", 0.6, 0.4),
        ("65/35", 0.65, 0.35),
        ("70/30", 0.7, 0.3)
    ],
    format_func=lambda x: x[0]
)
default_label, MARKUS_SHARE, NELLA_SHARE = split_option

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        text = "".join(page.extract_text() for page in pdf.pages if page.extract_text())

    lines = text.splitlines()
    products = []

    for line in lines:
        clean_line = line.strip().upper()
        if "YHTEENSÄ" in clean_line:
            break
        if any(word in clean_line for word in IGNORE_WORDS):
            continue

        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            name, price = parts
            try:
                price_val = float(price.replace(",", "."))
                if price_val > 0 and len(name.strip()) > 2:
                    products.append((name.strip(), price_val))
            except ValueError:
                continue

    if products:
        st.success(f"Luettiin kuitti onnistuneesti – {len(products)} tuotetta löydetty.")
        st.divider()

        choices = {}
        for idx, (name, price) in enumerate(products):
            valinta = st.selectbox(
                f"{name} — {price:.2f} €",
                options=[
                    f"Yhteinen ({default_label})",
                    "Yhteinen 50/50",
                    "Markus",
                    "Nella"
                ],
                key=f"item_{idx}"
            )
            choices[(name, price)] = valinta

        if st.button("Laske jako"):
            markus_items, nella_items, shared_items = [], [], []
            shared_total_markus = 0
            shared_total_nella = 0

            for (name, price), owner in choices.items():
                if owner == "Markus":
                    markus_items.append((name, price))
                elif owner == "Nella":
                    nella_items.append((name, price))
                elif owner == "Yhteinen 50/50":
                    shared_items.append((name, price))
                    shared_total_markus += price * 0.5
                    shared_total_nella += price * 0.5
                elif owner.startswith("Yhteinen"):
                    shared_items.append((name, price))
                    shared_total_markus += price * MARKUS_SHARE
                    shared_total_nella += price * NELLA_SHARE

            markus_total = sum(p for _, p in markus_items) + shared_total_markus
            nella_total = sum(p for _, p in nella_items) + shared_total_nella

            st.subheader("💰 Loppulaskelma")
            st.write(f"**Markuksen maksettava:** {markus_total:.2f} €")
            st.write(f"**Nellan maksettava:** {nella_total:.2f} €")
            st.write(
                f"(Yhteisiä ostoksia {shared_total_markus + shared_total_nella:.2f} € jaettu "
                f"valinnoilla: {default_label} ja 50/50)"
            )

            with st.expander("🧍 Markuksen tuotteet"):
                for n, p in markus_items:
                    st.write(f"{n} — {p:.2f} €")

            with st.expander("🧍‍♀️ Nellan tuotteet"):
                for n, p in nella_items:
                    st.write(f"{n} — {p:.2f} €")

            with st.expander("🤝 Yhteiset tuotteet"):
                for n, p in shared_items:
                    st.write(f"{n} — {p:.2f} €")
    else:
        st.warning("Kuitista ei löytynyt käsiteltäviä tuotteita.")
