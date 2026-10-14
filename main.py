
from typing import TypedDict, NotRequired, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from extract import extract_skills


# 1. Etat partage
class RecruitmentState(TypedDict):
    cv_text: str
    job_text: str
    cv_skills: NotRequired[list[str]]
    job_skills: NotRequired[list[str]]
    matched: NotRequired[list[str]]
    missing: NotRequired[list[str]]
    report: NotRequired[str]
    review_required: NotRequired[bool]
    review_status: NotRequired[str]


# 2. Extraction du CV
def extract_cv(state: RecruitmentState):
    result = extract_skills(state["cv_text"])
    return {"cv_skills": result.skills}


# 3. Extraction de l'offre
def extract_job(state: RecruitmentState):
    result = extract_skills(state["job_text"])
    return {"job_skills": result.skills}


# 4. Comparaison
def compare_skills(state: RecruitmentState):
    cv = {s.lower() for s in state["cv_skills"]}

    matched = [
        s for s in state["job_skills"]
        if s.lower() in cv
    ]

    missing = [
        s for s in state["job_skills"]
        if s.lower() not in cv
    ]

    return {"matched": matched, "missing": missing}


# Routage selon les compétences non identifiées
def route_after_comparison(
    state: RecruitmentState
) -> Literal["review", "report"]:

    if state["missing"]:
        return "review"

    return "report"


# Marquer le rapport comme nécessitant une vérification
def flag_review(state: RecruitmentState):
    print(">> Vérification humaine recommandée")
    return {"review_required": True}

def human_review(state: RecruitmentState):
    decision = interrupt({
        "message": "Valider l'analyse des compétences ?",
        "matched": state["matched"],
        "missing": state["missing"]
    })

    return {
        "review_required": True,
        "review_status": (
            "Validée" if decision else "Révision demandée"
        )
    }

# 5. Generation du rapport
def generate_report(state: RecruitmentState):
    status = state.get("review_status", "Non nécessaire")

    report = (
        f"Compétences retrouvées : {', '.join(state['matched'])}\n"
        f"Compétences non identifiées : {', '.join(state['missing'])}\n"
        f"Vérification humaine : {status}"
    )

    return {"report": report}

# 6. Construction du graphe
builder = StateGraph(RecruitmentState)

builder.add_node("extract_cv", extract_cv)
builder.add_node("extract_job", extract_job)
builder.add_node("comparison", compare_skills)
builder.add_node("human_review", human_review)
builder.add_node("report", generate_report)

builder.add_edge(START, "extract_cv")
builder.add_edge("extract_cv", "extract_job")
builder.add_edge("extract_job", "comparison")
builder.add_conditional_edges(
    "comparison",
    route_after_comparison,
    {
        "review": "human_review",
        "report": "report"
    }
)

builder.add_edge("human_review", "report")
builder.add_edge("report", END)

graph = builder.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    # 7. Execution avec Human-in-the-loop

    config = {
        "configurable": {
            "thread_id": "recruitment-demo-1"
        }
    }

    result = graph.invoke({
        "cv_text": """
        Data Analyst avec 3 ans d'expérience.
        Compétences : Python, SQL et BigQuery.
        """,
        "job_text": """
        Nous recherchons un Data Engineer.
        Compétences requises : Python, SQL, Docker et Airflow.
        """
    }, config=config)

    # Vérifier si LangGraph est en pause
    if "__interrupt__" in result:

        request = result["__interrupt__"][0].value

        print("\n--- WORKFLOW EN PAUSE ---")
        print("Compétences retrouvées :", request["matched"])
        print("Compétences non identifiées :", request["missing"])

        decision = input("\nValider cette analyse ? (o/n) : ").strip().lower()

        while decision not in ("o", "n"):
            decision = input("Répondre par o ou n : ").strip().lower()

        # Reprendre le même workflow
        result = graph.invoke(
            Command(resume=(decision == "o")),
            config=config
        )

    print("\n--- RAPPORT FINAL ---")
    print(result["report"])