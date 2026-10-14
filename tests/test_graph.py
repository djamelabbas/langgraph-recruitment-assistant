
from uuid import uuid4
from types import SimpleNamespace

import pytest
import main
from langgraph.types import Command


# Simuler Gemini sans appel API
def fake_extract_skills(text):
    skills = {
        "CV_TEST": ["Python", "SQL"],
        "OFFRE_TEST": ["Python", "Docker"],
        "OFFRE_COMPLETE": ["Python", "SQL"]
    }

    return SimpleNamespace(skills=skills[text])


# Remplacer Gemini automatiquement pendant les tests
@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    monkeypatch.setattr(
        main, "extract_skills", fake_extract_skills
    )


# Nouveau thread pour chaque test
def new_config():
    return {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }


# TEST 1 et 2 : interruption puis reprise
@pytest.mark.parametrize(
    "decision, expected_status",
    [
        (True, "Validée"),
        (False, "Révision demandée")
    ]
)
def test_human_review(decision, expected_status):
    config = new_config()

    # Démarrer le workflow
    result = main.graph.invoke({
        "cv_text": "CV_TEST",
        "job_text": "OFFRE_TEST"
    }, config=config)

    # Vérifier l'interruption
    assert "__interrupt__" in result

    request = result["__interrupt__"][0].value

    assert request["matched"] == ["Python"]
    assert request["missing"] == ["Docker"]

    # Reprendre le workflow
    result = main.graph.invoke(
        Command(resume=decision),
        config=config
    )

    assert "__interrupt__" not in result
    assert result["review_status"] == expected_status
    assert expected_status in result["report"]


# TEST 3 : aucun besoin de validation
def test_workflow_without_review():
    config = new_config()

    result = main.graph.invoke({
        "cv_text": "CV_TEST",
        "job_text": "OFFRE_COMPLETE"
    }, config=config)

    assert "__interrupt__" not in result
    assert result["missing"] == []
    assert result["matched"] == ["Python", "SQL"]
    assert "Non nécessaire" in result["report"]
