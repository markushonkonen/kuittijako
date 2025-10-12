import streamlit as st
import pdfplumber
import io
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Asetukset
MARKUS_SHARE = 0.6
NELLA_SHARE = 0.4
IGNORE_WORDS = ["NORM.", "KAMPANJA", "RIVIALENNUS", "BONUSTA", "ALV"]
FOLDER_ID = "1JJF8PLHgShBos2veSsub-R7LeZSaGxn1"

@st.cache_resource
def get_drive_service():
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds)

def get_latest_receipt(service):
    query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf'"
    results = service.files().list(q=query, orderBy="createdTime desc", pageSize=1, fields="files(id, name)").execute()
    items = results.get("files", [])
    if not items:
        st.error("Ei löytynyt yhtään kuittia Drive-kansiosta.")
        st.stop()
    return items[0]

def download_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

def parse_receipt(pdf_file):
    products = []
    with pdfplumber.open(pdf_file) as pdf:
        text = "".join(page.extract_text() for page in pdf.pages)
    lines = text.splitlines()

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
    return products

# ---------- Streamlit UI ----------
st.title("🧾 Ostosten jako")

service = get_drive_service()
receipt = get_latest_receipt(service)
pdf_file = download_file(service, receipt["id"])
products = parse_receipt(pdf_file)

st.success(f"Ladattiin uusin kuitti: {receipt['name']} (tuotteita: {len(products)})")
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

    markus_total = sum(p for _, p in markus_items) + MARKUS_SHARE * sum(p for _, p in shared_items)
    nella_total = sum(p for _, p in nella_items) + NELLA_SHARE * sum(p for _, p in shared_items)

    st.subheader("💰 Loppulaskelma")
    st.write(f"**Markuksen maksettava:** {markus_total:.2f} €")
    st.write(f"**Nellan maksettava:** {nella_total:.2f} €")
    st.write(f"(Yhteisiä ostoksia {sum(p for _, p in shared_items):.2f} € jaettu suhteessa 60/40)")

    with st.expander("🧍 Markuksen tuotteet"):
        for n, p in markus_items:
            st.write(f"{n} — {p:.2f} €")

    with st.expander("🧍‍♀️ Nellan tuotteet"):
        for n, p in nella_items:
            st.write(f"{n} — {p:.2f} €")

    with st.expander("🤝 Yhteiset tuotteet"):
        for n, p in shared_items:
            st.write(f"{n} — {p:.2f} €")
