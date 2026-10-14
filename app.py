
from uuid import uuid4

import streamlit as st
from langgraph.types import Command
from main import graph
from pypdf.errors import PdfReadError
from pdf_utils import extract_pdf_text

# 1. Configuration Streamlit
st.set_page_config(
    page_title="Assistant Recrutement IA",
    page_icon="📋",
    layout="centered"
)

st.title("Assistant IA de recrutement")
st.caption("LangGraph + Gemini + Pydantic + Streamlit")

st.info(
    "Prototype pédagogique : comparaison de compétences, "
    "avec validation humaine. Aucune décision de recrutement automatisée."
)


# 2. Données fictives
DEFAULT_CV = """
Data Analyst avec 3 ans d'expérience.
Compétences : Python, SQL et BigQuery.
"""

DEFAULT_JOB = """
Nous recherchons un Data Engineer.
Compétences requises : Python, SQL, Docker et Airflow.
"""


# 3. Initialiser la session
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())

if "stage" not in st.session_state:
    st.session_state.stage = "ready"

if "result" not in st.session_state:
    st.session_state.result = None

if "cv_input" not in st.session_state:
    st.session_state.cv_input = DEFAULT_CV

if "job_input" not in st.session_state:
    st.session_state.job_input = DEFAULT_JOB

if "upload_version" not in st.session_state:
    st.session_state.upload_version = 0

def get_config():
    return {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


# 4. Nouvelle analyse
with st.sidebar:
    st.header("Workflow LangGraph")

    st.write("1. Extraction Gemini")
    st.write("2. Comparaison")
    st.write("3. Validation humaine")
    st.write("4. Rapport")

    if st.button("Nouvelle analyse"):
        st.session_state.thread_id = str(uuid4())
        st.session_state.stage = "ready"
        st.session_state.result = None
        st.session_state.cv_input = DEFAULT_CV
        st.session_state.job_input = DEFAULT_JOB
        st.session_state.upload_version += 1
        st.rerun()


# 5. Formulaire
with st.form("recruitment_form"):

    st.subheader("Documents à analyser")

    cv_pdf = st.file_uploader(
        "Importer un CV en PDF (facultatif)",
        type=["pdf"],
        key=f"cv_pdf_{st.session_state.upload_version}",
        disabled=st.session_state.stage == "review"
    )

    job_pdf = st.file_uploader(
        "Importer une offre en PDF (facultatif)",
        type=["pdf"],
        key=f"job_pdf_{st.session_state.upload_version}",
        disabled=st.session_state.stage == "review"
    )

    st.caption(
        "Lorsqu'un PDF est importé, son contenu est "
        "prioritaire sur le texte saisi."
    )

    st.text_area(
        "CV du candidat",
        key="cv_input",
        height=140,
        disabled=st.session_state.stage == "review"
    )

    st.text_area(
        "Offre d'emploi",
        key="job_input",
        height=140,
        disabled=st.session_state.stage == "review"
    )

    submitted = st.form_submit_button(
        "Analyser les compétences",
        disabled=st.session_state.stage == "review"
    )


# 6. Lancer le workflow
if submitted:


    try:
        cv = (
            extract_pdf_text(cv_pdf)
            if cv_pdf is not None
            else st.session_state.cv_input.strip()
        )

        job = (
            extract_pdf_text(job_pdf)
            if job_pdf is not None
            else st.session_state.job_input.strip()
        )

    except (ValueError, PdfReadError) as error:
        st.error(f"Erreur de lecture PDF : {error}")
        st.stop()

    if not cv or not job:
        st.warning("Le CV et l'offre sont obligatoires.")

    else:
        # Nouveau thread pour chaque analyse
        st.session_state.thread_id = str(uuid4())

        with st.spinner("Exécution du workflow LangGraph..."):
            result = graph.invoke(
                {
                    "cv_text": cv,
                    "job_text": job
                },
                config=get_config()
            )

        st.session_state.result = result

        if "__interrupt__" in result:
            st.session_state.stage = "review"
        else:
            st.session_state.stage = "done"

        st.rerun()


# 7. Validation humaine
if st.session_state.stage == "review":

    interrupt_data = (
        st.session_state.result["__interrupt__"][0].value
    )

    st.warning("Workflow en pause : validation humaine requise")

    st.subheader("Résultat de la comparaison")

    st.write(
        "**Compétences retrouvées :**",
        ", ".join(interrupt_data["matched"]) or "Aucune"
    )

    st.write(
        "**Compétences non identifiées :**",
        ", ".join(interrupt_data["missing"]) or "Aucune"
    )

    col1, col2 = st.columns(2)

    decision = None

    with col1:
        if st.button("Approuver", type="primary"):
            decision = True

    with col2:
        if st.button("Demander une révision"):
            decision = False

    # Reprendre le graphe avec le même thread_id
    if decision is not None:

        with st.spinner("Reprise du workflow..."):
            result = graph.invoke(
                Command(resume=decision),
                config=get_config()
            )

        st.session_state.result = result
        st.session_state.stage = "done"
        st.rerun()


# 8. Rapport final
if st.session_state.stage == "done":

    st.success("Workflow terminé")

    st.subheader("Rapport d'adéquation")

    st.text(st.session_state.result["report"])
