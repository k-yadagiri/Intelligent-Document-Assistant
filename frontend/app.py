"""
app.py
Module 7 - Streamlit Frontend.

A single-page UI that talks to the FastAPI backend (api.py) purely
over HTTP, the same way any external client would. This is intentional:
the frontend has zero direct access to the database, auth logic, or
RAG pipeline - everything goes through the REST API, which keeps the
architecture clean (frontend and backend are fully decoupled and could
run on different machines).

Run the backend first:  uvicorn api:app --reload
Then run this:           streamlit run app.py
"""

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Intelligent Document Assistant", page_icon="📄", layout="wide")

# ---------- Session state ----------
# Streamlit reruns this whole script on every interaction, so anything
# that needs to survive between reruns (login token, selected doc, etc.)
# has to live in st.session_state rather than a plain variable.
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = None


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.token}"}


def safe_error_detail(resp: requests.Response) -> str:
    """
    Safely pulls a readable error message out of a response, whether
    the backend sent proper JSON ({"detail": "..."}) or, if something
    crashed unexpectedly, plain text/HTML. Prevents the frontend from
    crashing just because the error itself wasn't formatted as JSON.
    """
    try:
        return resp.json().get("detail", f"Request failed ({resp.status_code})")
    except ValueError:
        text = resp.text.strip()
        return text[:300] if text else f"Request failed with status {resp.status_code}"


# ============================================================
# LOGIN / SIGNUP SCREEN  (shown only when not logged in)
# ============================================================

def login_signup_screen():
    st.title("📄 Intelligent Document Assistant")
    st.caption("Upload a document, then ask questions about it - answers come only from what you uploaded.")

    tab_login, tab_signup = st.tabs(["Login", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            # /login expects form-encoded data (OAuth2PasswordRequestForm),
            # not JSON - that's why this uses `data=` not `json=`.
            resp = requests.post(f"{API_URL}/login", data={"username": username, "password": password})
            if resp.status_code == 200:
                st.session_state.token = resp.json()["access_token"]
                st.session_state.username = username
                st.rerun()
            else:
                st.error(safe_error_detail(resp))

    with tab_signup:
        with st.form("signup_form"):
            username = st.text_input("Username", key="signup_username")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            submitted = st.form_submit_button("Create account", use_container_width=True)

        if submitted:
            resp = requests.post(
                f"{API_URL}/signup",
                json={"username": username, "email": email, "password": password},
            )
            if resp.status_code == 201:
                st.success("Account created! Please log in.")
            else:
                st.error(safe_error_detail(resp))


# ============================================================
# MAIN APP  (shown after login)
# ============================================================

def main_app():
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        if st.button("Log out", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.selected_doc_id = None
            st.rerun()

        st.divider()
        st.subheader("Upload a document")
        uploaded_file = st.file_uploader("PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
        if uploaded_file is not None and st.button("Upload & index", use_container_width=True):
            with st.spinner("Extracting text and building the search index... this can take a bit on first run."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                resp = requests.post(f"{API_URL}/upload", headers=auth_headers(), files=files)
            if resp.status_code == 201:
                st.success(f"Indexed: {resp.json()['filename']}")
                st.session_state.selected_doc_id = resp.json()["id"]
                st.rerun()
            else:
                st.error(safe_error_detail(resp))

        st.divider()
        st.subheader("Your documents")
        docs_resp = requests.get(f"{API_URL}/documents", headers=auth_headers())
        docs = docs_resp.json() if docs_resp.status_code == 200 else []

        if not docs:
            st.info("No documents yet - upload one above.")
        else:
            for doc in docs:
                label = f"📄 {doc['filename']}"
                if st.button(label, key=f"doc_{doc['id']}", use_container_width=True):
                    st.session_state.selected_doc_id = doc["id"]
                    st.rerun()

    # ---------- Main panel: chat with the selected document ----------
    if st.session_state.selected_doc_id is None:
        st.title("📄 Intelligent Document Assistant")
        st.info("Upload a document or select one from the sidebar to start chatting.")
        return

    doc_id = st.session_state.selected_doc_id
    selected_doc = next((d for d in docs if d["id"] == doc_id), None)
    doc_name = selected_doc["filename"] if selected_doc else f"Document #{doc_id}"

    st.title(f"💬 Chat — {doc_name}")

    # Load and display existing history for this document
    history_resp = requests.get(f"{API_URL}/history/{doc_id}", headers=auth_headers())
    history = history_resp.json() if history_resp.status_code == 200 else []

    for entry in history:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            st.write(entry["answer"])
            if st.button("🗑️ Delete this exchange", key=f"del_{entry['id']}"):
                requests.delete(f"{API_URL}/history/{entry['id']}", headers=auth_headers())
                st.rerun()

    question = st.chat_input("Ask a question about this document...")
    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/chat",
                        headers=auth_headers(),
                        json={"document_id": doc_id, "question": question},
                        timeout=60,  # first Gemini call / cold model load can be slow
                    )
                except requests.exceptions.ConnectionError:
                    st.error(
                        "Can't reach the backend. Make sure `uvicorn api:app --reload` "
                        "is still running in your backend terminal."
                    )
                    st.stop()
                except requests.exceptions.Timeout:
                    st.error("The request timed out. The model may still be loading - try again.")
                    st.stop()
            if resp.status_code == 200:
                st.write(resp.json()["answer"])
                st.rerun()  # refresh so the new exchange shows up via /history above
            else:
                st.error(safe_error_detail(resp))


# ============================================================
# ENTRY POINT
# ============================================================

if st.session_state.token is None:
    login_signup_screen()
else:
    main_app()

