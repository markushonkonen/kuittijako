import streamlit as st
import pdfplumber

# Asetukset
IGNORE_WORDS = ["NORM.", "KAMPANJA", "RIVIALENNUS", "BONUSTA", "ALV"]

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Ostosten jako", layout="wide")
st.title("🧾 Ostosten jako")

uploaded_file = st.file_uploader("Lataa PDF-kuitti", type=["pdf"])

# 👉 Käyttäjän valittavissa olevat jakosuhteet
st.sidebar.subheader("⚖️ Yhteisten ostosten jako")
markus_share = st.sidebar.slider("Markuksen osuus (%)", min_value=0, max_value=100, value=60)
nella_share = 100 - markus_share

st.sidebar.write(f"Nellan osuus: {nella_share} %")

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
                options=["Yhteinen", "Markus", "Nella"],
                key=f"item_{idx}"
            )
            choices[(name, price)] = valinta

        if st.button("Laske jako"):
            markus_items, nella_items, shared_items = [], [], []

            for (name, price), owner in choices.items():
                if owner == "Markus":
                    markus_items.append((name, price))
                elif owner == "Nella":
                    nella_items.append((name, price))
                else:
                    shared_items.append((name, price))

            shared_total = sum(p for _, p in shared_items)
            markus_total = sum(p for _, p in markus_items) + (markus_share / 100) * shared_total
            nella_total = sum(p for _, p in nella_items) + (nella_share / 100) * shared_total

            st.subheader("💰 Loppulaskelma")
            st.write(f"**Markuksen maksettava:** {markus_total:.2f} €")
            st.write(f"**Nellan maksettava:** {nella_total:.2f} €")
            st.write(f"(Yhteisiä ostoksia {shared_total:.2f} € jaettu suhteessa {markus_share}/{nella_share})")

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
