"""Standalone AIOS Streamlit workspace with an embedded FastAPI server.

Run: streamlit run streamlit_app.py
"""

from __future__ import annotations

import atexit
import os
from collections.abc import Iterator
from html import escape
from pathlib import Path
from threading import Thread
from time import monotonic, sleep
from typing import Any

import httpx
import streamlit as st

st.set_page_config(page_title="AIOS", page_icon="◈", layout="wide")


def style() -> None:
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    html,body,[class*="css"]{font-family:Manrope,sans-serif}.stApp{background:#f7f8fb;color:#172033}.block-container{max-width:1120px;padding:3rem 2.4rem 4rem}#MainMenu,footer,header{visibility:hidden}
    [data-testid="stSidebar"]{background:#12192a;border:0}[data-testid="stSidebar"] *{color:#edf0f8}[data-testid="stSidebar"] .stTextInput input{background:#20293b!important;color:#fff!important;border-color:#354157!important}
    h1{font-size:2rem!important;font-weight:800!important;letter-spacing:-.055em}.mono{color:#778196;font:500 .7rem 'DM Mono',monospace;text-transform:uppercase;letter-spacing:.1em}.brand{color:#fff;font-size:1.3rem;font-weight:800;letter-spacing:-.06em;padding:.1rem 0 1.6rem}.mark{background:#6b63f6;border-radius:8px;display:inline-grid;place-items:center;width:28px;height:28px;margin-right:8px}
    .panel{background:#fff;border:1px solid #e4e9f0;border-radius:15px;padding:1.2rem}.empty{background:#fbfcfe;border:1px dashed #ccd4e1;border-radius:14px;padding:1.8rem;text-align:center;color:#7a8497}.context{background:#152033;color:#f4f6fc;border-radius:14px;padding:1.15rem 1.25rem;line-height:1.7}.context-label{color:#bdbaff;font:500 .67rem 'DM Mono',monospace;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.55rem}
    .stButton button{border-radius:9px;font-weight:700}
    button[kind="primary"],button[kind="primaryFormSubmit"]{background:#5d55e8!important;border-color:#5d55e8!important;color:#fff!important}
    button[kind="primary"]:hover,button[kind="primaryFormSubmit"]:hover{background:#4b43cf!important;border-color:#4b43cf!important}
    .stButton button[kind="tertiary"]{color:#5147d9;background:transparent;border:0;padding:.25rem .4rem}
    [data-testid="stTextInputRootElement"],[data-testid="stTextArea"] textarea{background:#fff!important;border:1px solid #d8dfea!important;border-radius:9px!important;box-shadow:none!important}
    [data-testid="stTextInputRootElement"]:focus-within,[data-testid="stTextArea"] textarea:focus{border-color:#6255e8!important;box-shadow:0 0 0 1px #6255e8!important}
    .stTextInput input,.stTextArea textarea{background:#fff!important;color:#172033!important}
    [data-testid="stWidgetLabel"] p{color:#394254!important;font-weight:600!important}
    .stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#81899a!important;opacity:1}
    [data-testid="stSelectbox"] [data-baseweb="select"]>div{background:#fff!important;color:#172033!important;border-radius:9px!important;border-color:#d8dfea!important}
    .stTabs [data-baseweb="tab-list"]{gap:1.4rem}.stTabs [data-baseweb="tab"]{font-weight:700}
    .auth-brand{display:flex;align-items:center;gap:.65rem;margin-bottom:2.2rem;color:#172033;font-weight:800;font-size:1.2rem;letter-spacing:-.04em}.auth-brand-mark{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:#6255e8;color:#fff}
    .auth-feature{margin:.8rem 0;color:#5f687a}.auth-feature strong{color:#263047}
    @media(max-width:640px){.block-container{padding:1.2rem 1rem 2.5rem}h1{font-size:1.7rem!important}}
    </style>""", unsafe_allow_html=True)


def stop_backend(server: Any, thread: Thread) -> None:
    server.should_exit = True
    thread.join(timeout=10)


@st.cache_resource(show_spinner=False)
def start_backend() -> tuple[str, bool]:
    """Upgrade the database and start the API once for this Streamlit process."""
    external_api_url = os.getenv("AIOS_API_URL")
    if external_api_url:
        base_url = external_api_url.rstrip("/")
        if not base_url.endswith("/api/v1"):
            base_url += "/api/v1"
        return base_url, False

    try:
        from alembic import command
        from alembic.config import Config
        from app.core.config import settings

        project_root = Path(__file__).resolve().parent
        migration_config = Config(str(project_root / "alembic.ini"))
        command.upgrade(migration_config, "head")
    except Exception as error:
        raise RuntimeError(
            "AIOS could not upgrade its database. Check the database settings in "
            "your environment configuration and confirm that the database is available."
        ) from error

    base_url = f"http://127.0.0.1:{settings.PORT}/api/v1"
    health_url = f"{base_url}/health/health"

    try:
        response = httpx.get(health_url, timeout=2)
        if response.is_success:
            return base_url, False
    except httpx.RequestError:
        pass

    try:
        from app.main import app as fastapi_app
        import uvicorn
    except Exception as error:
        raise RuntimeError(
            "AIOS database migrations completed, but the application could not start. "
            "Check the application logs and environment configuration."
        ) from error

    server = uvicorn.Server(
        uvicorn.Config(
            fastapi_app,
            host="127.0.0.1",
            port=settings.PORT,
            log_level="warning",
            access_log=False,
        )
    )
    thread = Thread(target=server.run, name="aios-api", daemon=True)
    thread.start()
    atexit.register(stop_backend, server, thread)

    deadline = monotonic() + 60
    while monotonic() < deadline:
        if not thread.is_alive():
            raise RuntimeError(
                "AIOS could not start. Check the application logs and confirm the "
                "configured supporting services are available."
            )
        try:
            response = httpx.get(health_url, timeout=2)
            if response.is_success:
                return base_url, True
        except httpx.RequestError:
            pass
        sleep(0.4)

    stop_backend(server, thread)
    raise RuntimeError(
        "AIOS did not finish starting in time. Confirm the configured database, "
        "cache, vector store, and MCP services are available."
    )


def url(path: str) -> str:
    return f"{st.session_state.api_url.rstrip('/')}/{path.lstrip('/')}"


def api(method: str, path: str, **kwargs: Any) -> Any:
    headers = kwargs.pop("headers", {})
    if token := st.session_state.get("access_token"):
        headers["Authorization"] = "Bearer " + token
    try:
        response = httpx.request(method, url(path), headers=headers, timeout=120, **kwargs)
    except httpx.RequestError as error:
        raise RuntimeError("AIOS is temporarily unavailable. Check that the app and its services are running.") from error
    if response.status_code == 204:
        return None
    if response.is_error:
        try: detail = response.json().get("detail", response.text)
        except ValueError: detail = response.text
        raise RuntimeError(str(detail))
    data = response.json()
    return data["data"] if isinstance(data, dict) and data.get("success") and "data" in data else data


def api_stream(path: str, **kwargs: Any) -> Iterator[str]:
    headers = kwargs.pop("headers", {})
    if token := st.session_state.get("access_token"):
        headers["Authorization"] = "Bearer " + token
    try:
        with httpx.stream("POST", url(path), headers=headers, timeout=120, **kwargs) as response:
            if response.is_error:
                try:
                    detail = response.json().get("detail", response.text)
                except ValueError:
                    detail = response.text
                raise RuntimeError(str(detail))
            for line in response.iter_lines():
                if line.startswith("data:"):
                    chunk = line[5:].lstrip()
                    if chunk == "[DONE]":
                        break
                    yield chunk
                elif line:
                    yield "\n" + line
                else:
                    yield "\n"
    except httpx.RequestError as error:
        raise RuntimeError("AIOS is temporarily unavailable. Check that the app and its services are running.") from error


def refresh() -> list[str]:
    errors = []
    for endpoint, key in (("/knowledge-bases", "knowledge_bases"), ("/agents", "agents"), ("/conversations", "conversations")):
        try:
            st.session_state[key] = api("GET", endpoint)
        except RuntimeError as error:
            st.session_state[key] = []
            errors.append(f"{endpoint}: {error}")
    return errors


def header(title: str, copy: str) -> None:
    st.title(title)
    st.caption(copy)


def login() -> None:
    if st.session_state.pop("return_to_signin", False):
        st.session_state.auth_mode = "Sign in"
        st.session_state.login_password = ""
        st.session_state.register_password = ""

    st.session_state.setdefault("auth_mode", "Sign in")
    intro, form_column = st.columns([1.05, .95], gap="large")
    with intro:
        st.markdown(
            '<div class="auth-brand"><span class="auth-brand-mark">◈</span>AIOS</div>'
            '<div class="mono">YOUR ORGANIZATION WORKSPACE</div>',
            unsafe_allow_html=True,
        )
        st.title("Knowledge and AI, in one workspace.")
        st.markdown(
            "Bring your organization’s knowledge together and make it useful with AI.",
            unsafe_allow_html=False,
        )
        st.markdown(
            '<div class="auth-feature">• &nbsp;<strong>Knowledge bases</strong> · organize and search PDF documents</div>'
            '<div class="auth-feature">• &nbsp;<strong>AI agents</strong> · configure assistants for your team</div>'
            '<div class="auth-feature">• &nbsp;<strong>Conversations</strong> · work with organizational knowledge</div>',
            unsafe_allow_html=True,
        )

    notice = st.session_state.pop("auth_notice", None)
    if notice and st.session_state.auth_mode == "Sign in":
        st.success(notice)

    with form_column:
        if st.session_state.auth_mode == "Sign in":
            switch_text, switch_button = st.columns([1, 1.3], vertical_alignment="center")
            with switch_text:
                st.markdown("New to AIOS?")
            with switch_button:
                if st.button("Create account", type="tertiary", key="show_register", use_container_width=True):
                    st.session_state.auth_mode = "Create account"
                    st.rerun()
            with st.container(border=True):
                st.subheader("Welcome back")
                st.caption("Sign in to continue to your workspace.")
                with st.form("login"):
                    email = st.text_input(
                        "Email",
                        value=st.session_state.get("pending_login_email", ""),
                        placeholder="you@company.com",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="login_password",
                        placeholder="Enter your password",
                    )
                    submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                if submit:
                    try:
                        tokens = api("POST", "/auth/login", json={"email": email, "password": password})
                        st.session_state.access_token = tokens["access_token"]
                        st.session_state.refresh_token = tokens["refresh_token"]
                        st.session_state.user = api("GET", "/auth/me")
                        st.session_state.resource_errors = refresh()
                        st.rerun()
                    except (RuntimeError, KeyError) as error:
                        st.error(str(error))
            return

        switch_text, switch_button = st.columns([1.3, 1], vertical_alignment="center")
        with switch_text:
            st.markdown("Already have an account?")
        with switch_button:
            if st.button("Sign in", type="tertiary", key="show_login", use_container_width=True):
                st.session_state.auth_mode = "Sign in"
                st.rerun()

        with st.container(border=True):
            st.subheader("Create your account")
            st.caption("Set up your account and organization workspace.")

            try:
                organizations = api("GET", "/organizations")
                organizations_loaded = True
            except RuntimeError as error:
                organizations = []
                organizations_loaded = False
                st.error(f"Organizations could not be loaded. Please try again. Details: {error}")

            organization_choices = {
                f"{item['name']} · {item['id']}": item["id"] for item in organizations
            }
            create_organization = "Create a new organization"
            organization_names = [*organization_choices, create_organization]
            selected_organization = st.selectbox(
                "Organization",
                organization_names,
                key="register_organization",
                disabled=not organizations_loaded,
            )

            with st.form("register"):
                full_name = st.text_input(
                    "Full name",
                    key="register_full_name",
                    placeholder="Enter your full name",
                )
                new_email = st.text_input(
                    "Work email",
                    key="register_email",
                    placeholder="you@company.com",
                )
                new_password = st.text_input(
                    "Password",
                    type="password",
                    key="register_password",
                    placeholder="Create a password (at least 8 characters)",
                )
                organization_name = None
                organization_description = None
                if selected_organization == create_organization:
                    organization_name = st.text_input(
                        "New organization name",
                        placeholder="Enter your organization name",
                    )
                    organization_description = st.text_area(
                        "Organization description (optional)",
                        placeholder="Describe your organization",
                    )
                register = st.form_submit_button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                    disabled=not organizations_loaded,
                )
            if register:
                try:
                    if len(full_name.strip()) < 2:
                        raise RuntimeError("Enter your full name (at least 2 characters).")
                    if "@" not in new_email:
                        raise RuntimeError("Enter a valid email address.")
                    if len(new_password) < 8:
                        raise RuntimeError("Password must be at least 8 characters.")
                    if (
                        selected_organization == create_organization
                        and len((organization_name or "").strip()) < 2
                    ):
                        raise RuntimeError(
                            "Enter an organization name (at least 2 characters)."
                        )
                    if selected_organization == create_organization:
                        organization = api(
                            "POST",
                            "/organizations",
                            json={
                                "name": organization_name,
                                "description": organization_description or None,
                            },
                        )
                        organization_id = organization["id"]
                    else:
                        organization_id = organization_choices[selected_organization]
                    api(
                        "POST",
                        "/auth/register",
                        json={
                            "organization_id": organization_id,
                            "full_name": full_name,
                            "email": new_email,
                            "password": new_password,
                        },
                    )
                    st.session_state.pending_login_email = new_email
                    st.session_state.auth_notice = (
                        "Your account was created. Sign in below to continue."
                    )
                    st.session_state.return_to_signin = True
                    st.rerun()
                except (RuntimeError, KeyError) as error:
                    st.error(str(error))


def navigation() -> str:
    with st.sidebar:
        st.markdown('<div class="brand"><span class="mark">◈</span>AIOS</div>', unsafe_allow_html=True)
        st.caption(st.session_state.get("user", {}).get("email", "Authenticated session"))
        view = st.radio("Workspace", ["Assistant", "Knowledge bases", "Agents", "Organizations", "Account"], label_visibility="collapsed")
        for error in st.session_state.get("resource_errors", []):
            st.warning(f"Resource unavailable: {error}")
        if st.button("Refresh resources", use_container_width=True):
            st.session_state.resource_errors = refresh()
            st.rerun()
        if st.button("Sign out", use_container_width=True):
            try:
                api("POST", "/auth/logout", json={"refresh_token": st.session_state.refresh_token})
            except RuntimeError as error:
                st.error(f"Could not sign out cleanly: {error}")
            else:
                st.session_state.clear()
                st.rerun()
    return view


def retrieval() -> None:
    header("Search knowledge", "Find relevant passages in your organization’s processed documents.")
    bases = st.session_state.get("knowledge_bases", [])
    if not bases:
        st.markdown('<div class="empty">No knowledge bases returned. Create a knowledge base and process a PDF first.</div>', unsafe_allow_html=True); return
    choices = {f"{item['name']} · {item['id']}": item["id"] for item in bases}
    with st.form("query"):
        base = st.selectbox("Knowledge base", list(choices))
        query = st.text_area(
            "Question",
            height=100,
            placeholder="Ask a question about your organization’s documents",
        )
        send = st.form_submit_button("Run retrieval", type="primary")
    if send:
        try: st.session_state.query_result = api("POST", "/query", json={"query": query, "knowledge_base_id": choices[base]})
        except RuntimeError as error: st.error(str(error))
    if result := st.session_state.get("query_result"):
        context = escape(result.get("context", "")).replace("\n", "<br>") or "No context returned."
        st.markdown('<div class="context"><div class="context-label">context</div>'+context+"</div>", unsafe_allow_html=True)
        st.subheader("Sources")
        for i, source in enumerate(result.get("sources", []), 1):
            pages = ", ".join(map(str, source.get("page_numbers", []))) or "not supplied"
            with st.expander(f"Source {i} · page numbers: {pages}"): st.write(source.get("text", ""))


def knowledge_bases() -> None:
    header("Knowledge bases", "Organize PDF documents so your team can search trusted information.")
    create_tab, browse_tab, manage_tab = st.tabs(["Create", "Documents", "Manage"])
    with create_tab:
        with st.form("new_kb", clear_on_submit=True):
            name = st.text_input("Knowledge base name", placeholder="e.g. Product documentation")
            description = st.text_area(
                "Description (optional)",
                placeholder="What information will this knowledge base contain?",
            )
            create = st.form_submit_button("Create knowledge base", type="primary")
        if create:
            try: api("POST", "/knowledge-bases", json={"name": name, "description": description or None}); refresh(); st.rerun()
            except RuntimeError as error: st.error(str(error))
    with browse_tab:
        bases = st.session_state.get("knowledge_bases", [])
        if not bases:
            st.markdown('<div class="empty">No knowledge bases returned.</div>', unsafe_allow_html=True)
        else:
            options = {f"{item['name']} · {item['id']}": item for item in bases}
            base = options[st.selectbox("Knowledge base", list(options))]
            try:
                documents = api("GET", f"/knowledge-bases/{base['id']}/documents")
            except RuntimeError as error:
                st.error(str(error))
                documents = []
            left, right = st.columns([1.4, 1])
            with left:
                for doc in documents:
                    with st.container(border=True):
                        x, y, z = st.columns([3, 1, 1])
                        x.markdown(f"**{doc['filename']}**  \n{doc.get('file_size','')} · {doc.get('status','unknown')}")
                        if y.button("Process", key=f"p-{doc['id']}"):
                            try:
                                api("POST", f"/documents/{doc['id']}/process")
                                st.success("Processing accepted.")
                            except RuntimeError as error:
                                st.error(str(error))
                        if z.button("Delete", key=f"d-{doc['id']}"):
                            try:
                                api("DELETE", f"/documents/{doc['id']}")
                                st.rerun()
                            except RuntimeError as error:
                                st.error(str(error))
                if not documents:
                    st.markdown('<div class="empty">No documents returned.</div>', unsafe_allow_html=True)
            with right:
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                st.subheader("Upload PDF")
                st.caption("`POST /knowledge-bases/{id}/documents`")
                file = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
                if st.button("Upload", type="primary", disabled=file is None, use_container_width=True):
                    try:
                        api(
                            "POST",
                            f"/knowledge-bases/{base['id']}/documents",
                            files={"file": (file.name, file.getvalue(), file.type or "application/pdf")},
                        )
                        st.rerun()
                    except RuntimeError as error:
                        st.error(str(error))
                st.markdown("</div>", unsafe_allow_html=True)
    with manage_tab:
        bases = st.session_state.get("knowledge_bases", [])
        if not bases:
            st.markdown('<div class="empty">Create a knowledge base to manage it here.</div>', unsafe_allow_html=True)
        else:
            options = {f"{item['name']} · {item['id']}": item for item in bases}
            base = options[st.selectbox("Knowledge base to manage", list(options))]
            with st.form("update_knowledge_base"):
                name = st.text_input(
                    "Knowledge base name",
                    base["name"],
                    placeholder="Enter a name for this knowledge base",
                )
                description = st.text_area(
                    "Description (optional)",
                    base.get("description") or "",
                    placeholder="Describe this knowledge base",
                )
                save = st.form_submit_button("Save changes", type="primary")
            if save:
                try:
                    api(
                        "PATCH",
                        f"/knowledge-bases/{base['id']}",
                        json={"name": name, "description": description or None},
                    )
                    refresh()
                    st.rerun()
                except RuntimeError as error:
                    st.error(str(error))
            confirm_delete = st.checkbox("I understand this removes the knowledge base from the workspace.")
            if st.button("Delete knowledge base", disabled=not confirm_delete):
                try:
                    api("DELETE", f"/knowledge-bases/{base['id']}")
                    refresh()
                    st.rerun()
                except RuntimeError as error:
                    st.error(str(error))


def agents() -> None:
    header("Agents", "Configure AI assistants for your organization.")
    create_tab, manage_tab = st.tabs(["Create", "Manage"])
    with create_tab:
        with st.form("new_agent", clear_on_submit=True):
            name=st.text_input("Agent name", placeholder="e.g. Research assistant"); description=st.text_area("Description (optional)", placeholder="What should this agent help with?"); prompt=st.text_area("System prompt", height=140, placeholder="Describe the agent’s role, instructions, and response style"); model=st.text_input("Model", "gpt-4.1-mini", placeholder="Model identifier"); temperature=st.slider("Temperature",0.,2.,.7,.1)
            create=st.form_submit_button("Create agent",type="primary")
        if create:
            try: api("POST","/agents",json={"name":name,"description":description or None,"system_prompt":prompt,"model":model,"temperature":temperature}); refresh(); st.rerun()
            except RuntimeError as error: st.error(str(error))
    with manage_tab:
        records=st.session_state.get("agents",[])
        if not records: st.markdown('<div class="empty">No agents returned.</div>',unsafe_allow_html=True); return
        options={f"{item['name']} · {item['id']}":item for item in records}; agent=options[st.selectbox("Agent",list(options))]
        with st.form("update_agent"):
            name=st.text_input("Agent name",agent["name"], placeholder="Enter an agent name"); description=st.text_area("Description (optional)",agent.get("description") or "", placeholder="Describe what this agent does"); prompt=st.text_area("System prompt",agent["system_prompt"],height=140, placeholder="Instructions for the agent"); model=st.text_input("Model",agent["model"], placeholder="Model identifier"); temperature=st.slider("Temperature",0.,2.,float(agent["temperature"]),.1); active=st.checkbox("Active",agent["is_active"])
            save=st.form_submit_button("Save changes",type="primary")
        if save:
            try: api("PATCH",f"/agents/{agent['id']}",json={"name":name,"description":description or None,"system_prompt":prompt,"model":model,"temperature":temperature,"is_active":active}); refresh(); st.rerun()
            except RuntimeError as error: st.error(str(error))
        if st.button("Delete agent"):
            try: api("DELETE",f"/agents/{agent['id']}"); refresh(); st.rerun()
            except RuntimeError as error: st.error(str(error))


def conversations() -> None:
    header("AI assistant", "Chat with an AI agent that can use your organization’s knowledge.")
    create_tab, messages_tab = st.tabs(["Create", "Messages"]); agents=st.session_state.get("agents",[]); records=st.session_state.get("conversations",[])
    with create_tab:
        if not agents: st.info("Create an agent first.")
        else:
            options={f"{item['name']} · {item['id']}":item["id"] for item in agents}
            with st.form("new_conversation",clear_on_submit=True): selected=st.selectbox("Agent",list(options)); title=st.text_input("Title (optional)", placeholder="Add a title or leave blank"); create=st.form_submit_button("Create conversation",type="primary")
            if create:
                try: api("POST","/conversations",json={"agent_id":options[selected],"title":title or None}); refresh(); st.rerun()
                except RuntimeError as error: st.error(str(error))
    with messages_tab:
        if not records: st.markdown('<div class="empty">No conversations returned.</div>',unsafe_allow_html=True); return
        options={f"{item['title']} · {item['status']} · {item['id']}":item for item in records}; conversation=options[st.selectbox("Conversation",list(options))]
        try: messages=api("GET",f"/conversations/{conversation['id']}/messages")
        except RuntimeError as error: st.error(str(error)); messages=[]
        for message in messages:
            with st.chat_message("assistant" if message["role"]=="assistant" else "user"): st.write(message["content"])
        with st.expander("Conversation settings"):
            with st.form("update_conversation"):
                title = st.text_input(
                    "Conversation title",
                    conversation["title"],
                    placeholder="Enter a conversation title",
                )
                save_title = st.form_submit_button("Rename conversation")
            if save_title:
                try:
                    api("PATCH", f"/conversations/{conversation['id']}", json={"title": title})
                    refresh()
                    st.rerun()
                except RuntimeError as error:
                    st.error(str(error))
        with st.form("message",clear_on_submit=True): content=st.text_area("Message",height=85, placeholder="Type your message to the AI agent"); send=st.form_submit_button("Send message",type="primary")
        if send:
            if not content.strip():
                st.error("Enter a message before sending.")
            else:
                try:
                    with st.chat_message("user"):
                        st.write(content)
                    with st.chat_message("assistant"):
                        st.write_stream(
                            api_stream(
                                f"/conversations/{conversation['id']}/messages/stream",
                                json={"content": content},
                            )
                        )
                    st.session_state.resource_errors = refresh()
                except RuntimeError as error:
                    st.error(str(error))
        a,b=st.columns(2)
        if a.button("Archive"):
            try: api("POST",f"/conversations/{conversation['id']}/archive"); refresh(); st.rerun()
            except RuntimeError as error: st.error(str(error))
        if b.button("Delete"):
            try: api("DELETE",f"/conversations/{conversation['id']}"); refresh(); st.rerun()
            except RuntimeError as error: st.error(str(error))


def assistant() -> None:
    chat_tab, retrieval_tab = st.tabs(["Agent chat", "Search knowledge"])
    with chat_tab:
        conversations()
    with retrieval_tab:
        retrieval()


def organizations() -> None:
    header("Organizations", "Manage the organizations available to this workspace.")
    try: records=api("GET","/organizations")
    except RuntimeError as error: st.error(str(error)); return
    create_tab, manage_tab = st.tabs(["Create", "Manage"])
    with create_tab:
        with st.form("org",clear_on_submit=True): name=st.text_input("Organization name", placeholder="Enter your organization name"); description=st.text_area("Description (optional)", placeholder="Describe your organization"); create=st.form_submit_button("Create organization",type="primary")
        if create:
            try: api("POST","/organizations",json={"name":name,"description":description or None}); st.rerun()
            except RuntimeError as error: st.error(str(error))
    with manage_tab:
        if records:
            options = {f"{item['name']} · {item['id']}": item for item in records}
            organization = options[st.selectbox("Organization", list(options))]
            with st.form("update_organization"):
                name = st.text_input(
                    "Organization name",
                    organization["name"],
                    placeholder="Enter an organization name",
                )
                description = st.text_area(
                    "Description (optional)",
                    organization.get("description") or "",
                    placeholder="Describe your organization",
                )
                save = st.form_submit_button("Save changes", type="primary")
            if save:
                try:
                    api("PATCH", f"/organizations/{organization['id']}", json={"name": name, "description": description or None})
                    st.rerun()
                except RuntimeError as error:
                    st.error(str(error))
            confirm_delete = st.checkbox("I understand this permanently deletes the selected organization.")
            if st.button("Delete organization", type="secondary", disabled=not confirm_delete):
                try:
                    api("DELETE", f"/organizations/{organization['id']}")
                    st.rerun()
                except RuntimeError as error:
                    st.error(str(error))
        else:
            st.markdown('<div class="empty">No organizations returned.</div>',unsafe_allow_html=True)


def account() -> None:
    header("Account", "View your account details and refresh your session.")
    st.json(st.session_state.get("user",{}))
    if st.button("Refresh access token"):
        try:
            tokens=api("POST","/auth/refresh",json={"refresh_token":st.session_state.get("refresh_token")}); st.session_state.access_token=tokens["access_token"]; st.session_state.refresh_token=tokens.get("refresh_token"); st.success("Token refreshed.")
        except RuntimeError as error: st.error(str(error))


def main() -> None:
    style()
    try:
        with st.spinner("Preparing AIOS: upgrading database and starting the API…"):
            api_url, embedded_api = start_backend()
    except RuntimeError as error:
        st.error(str(error))
        st.info(
            "The Streamlit interface starts the AIOS API automatically. PostgreSQL "
            "and the services configured in `.env` must be available."
        )
        st.stop()
    st.session_state.api_url = api_url
    st.session_state.embedded_api = embedded_api
    if not st.session_state.get("access_token"): login(); return
    view=navigation(); {"Assistant":assistant,"Knowledge bases":knowledge_bases,"Agents":agents,"Organizations":organizations,"Account":account}[view]()


if __name__ == "__main__": main()
