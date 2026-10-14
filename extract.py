
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


class SkillsExtraction(BaseModel):
    skills: list[str] = Field(
        description="Compétences techniques explicitement mentionnées"
    )


@lru_cache(maxsize=1)
def get_extractor():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite"
    )

    return llm.with_structured_output(
        SkillsExtraction,
        method="json_schema"
    )


def extract_skills(text: str) -> SkillsExtraction:
    return get_extractor().invoke(
        "Extrais uniquement les compétences techniques "
        "explicitement présentes dans ce texte. "
        "N'invente aucune compétence.\n\n"
        f"Texte : {text}"
    )
