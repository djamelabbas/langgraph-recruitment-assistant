
import pytest

from main import (
    compare_skills,
    route_after_comparison,
    generate_report
)


# TEST 1 : Comparaison des compétences
def test_comparison():
    state = {
        "cv_skills": ["Python", "SQL", "BigQuery"],
        "job_skills": ["Python", "SQL", "Docker"]
    }

    result = compare_skills(state)

    assert result["matched"] == ["Python", "SQL"]
    assert result["missing"] == ["Docker"]


# TEST 2 : Insensibilité à la casse
def test_case_insensitive():
    state = {
        "cv_skills": ["python", "sql"],
        "job_skills": ["Python", "SQL"]
    }

    result = compare_skills(state)

    assert result["matched"] == ["Python", "SQL"]
    assert result["missing"] == []


# TEST 3 : Toutes les compétences sont présentes
def test_all_skills_matched():
    state = {
        "cv_skills": ["Python", "SQL", "Docker"],
        "job_skills": ["Python", "Docker"]
    }

    result = compare_skills(state)

    assert result["missing"] == []


# TESTS 4 et 5 : Routage conditionnel
@pytest.mark.parametrize(
    "missing, expected",
    [
        (["Docker"], "review"),
        ([], "report")
    ]
)
def test_conditional_routing(missing, expected):
    state = {"missing": missing}

    assert route_after_comparison(state) == expected


# TEST 6 : Rapport après validation humaine
def test_approved_report():
    state = {
        "matched": ["Python", "SQL"],
        "missing": ["Docker"],
        "review_status": "Validée"
    }

    result = generate_report(state)

    assert "Python" in result["report"]
    assert "Docker" in result["report"]
    assert "Validée" in result["report"]


# TEST 7 : Rapport avec demande de révision
def test_revision_report():
    state = {
        "matched": ["Python"],
        "missing": ["Airflow"],
        "review_status": "Révision demandée"
    }

    result = generate_report(state)

    assert "Révision demandée" in result["report"]
