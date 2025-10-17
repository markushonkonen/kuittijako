import streamlit as st
import pdfplumber

# --- Asetukset ---
IGNORE_WORDS = ["NORM.", "KAMPANJA", "RIVIALENNUS", "BONUSTA", "ALV", "Puh."]

# --- Streamlit UI ---
st.set_page_config(page_title="Ostosten jako", layout="wide")
st.title("🧾 Ostosten jako")

# Yhteisten ostosten jako – valinta sivupalkissa
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
    format_func=lambda x: x[0],
    index=2  # Oletus: 60/40
)
default_label, MARKUS_SHARE, NELLA_SHARE = split_option

# PDF-kuitin lataus
uploaded_file = st.file_uploader("Lataa PDF-kuitti", type=["pdf"])

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
            markus_total = 0
            nella_total = 0

            markus_items = []
            nella_items = []
            shared_items = []
            shared_5050_items = []

            for (name, price), choice in choices.items():
                if choice == "Markus":
                    markus_total += price
                    markus_items.append((name, price))
                elif choice == "Nella":
                    nella_total += price
                    nella_items.append((name, price))
                elif choice == "Yhteinen 50/50":
                    markus_total += price / 2
                    nella_total += price / 2
                    shared_5050_items.append((name, price))
                else:
                    markus_total += price * MARKUS_SHARE
                    nella_total += price * NELLA_SHARE
                    shared_items.append((name, price))

            total_shared = sum(p for _, p in shared_items)
            total_5050 = sum(p for _, p in shared_5050_items)

            st.subheader("💰 Loppulaskelma")
            st.write(f"**Markuksen maksettava:** {markus_total:.2f} €")
            st.write(f"**Nellan maksettava:** {nella_total:.2f} €")
            st.write(
                f"(Yhteisiä ostoksia: {total_shared:.2f} € jaettu suhteessa {default_label}, "
                f"{total_5050:.2f} € jaettu tasan)"
            )

            with st.expander("🧍 Markuksen tuotteet"):
                for n, p in markus_items:
                    st.write(f"{n} — {p:.2f} €")

            with st.expander("🧍‍♀️ Nellan tuotteet"):
                for n, p in nella_items:
                    st.write(f"{n} — {p:.2f} €")

            with st.expander(f"🤝 Yhteiset tuotteet ({default_label})"):
                for n, p in shared_items:
                    st.write(f"{n} — {p:.2f} €")

            with st.expander("🤝 Yhteiset tuotteet (50/50)"):
                for n, p in shared_5050_items:
                    st.write(f"{n} — {p:.2f} €")

    else:
        st.warning("Kuitista ei löytynyt käsiteltäviä tuotteita.")
