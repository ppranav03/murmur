import re
import sys
from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=60,
)

def clean_script(text):
    # Drop a leading preamble line like "Here's a TLDR summary:"
    text = re.sub(r"^\s*here(?:'s| is)[^\n]*:\s*\n", "", text, flags=re.IGNORECASE)
    # Strip markdown headings, bullets, bold/italics and stray asterisks/underscores
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*•]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_]{1,3}", "", text)
    # Replace Unicode hyphens and dashes that Windows consoles can't print
    text = text.replace("‑", "-").replace("–", "-")
    text = re.sub(r"\s*—\s*", ", ", text)
    return text.strip()


def write_script(user_text):
    template = ChatPromptTemplate(messages=[
        ("system", """
        You are a helpful assistant and you will be given an article and
        summarize it into a 20-second read (about 50 words) adopting a TLDR format.

        Your output will be read aloud by a text-to-speech engine, so write plain spoken text only:
        no markdown, asterisks, headings, bullet points, or emojis.
        Do not add any preamble like "Here's a summary"; start directly with the script.

        The dialogue should be upbeat yet informational, adopting a style similar to NPR's Up-First podcast.
        """),
        ("user", "This is the article {article}")
    ])
    prompt_parameters = {"article": user_text}

    chain = template | llm
    response = chain.invoke(prompt_parameters)
    return clean_script(response.content)


class Post(BaseModel):
    title: str
    url: str
    why: str = Field(description="One sentence on why this post matters")


class Analysis(BaseModel):
    sentiment: Literal["positive", "mixed", "negative"]
    themes: list[str] = Field(description="3 to 5 short themes")
    notable_posts: list[Post] = Field(description="Up to 3 posts taken from the input")


# with_structured_output makes the model return an Analysis instead of free text
analyst = llm.with_structured_output(Analysis)

ANALYSIS_PROMPT = """You analyse what one source is saying about a topic today.
Report the overall sentiment, the main themes, and up to 3 notable posts.
Only cite posts that appear in the input, using their exact titles and URLs."""


async def analyze_posts(topic, source, posts):
    posts_text = "\n\n".join(f"{p['title']} ({p['url']})\n{p['text']}" for p in posts)
    result = await analyst.ainvoke([
        ("system", ANALYSIS_PROMPT),
        ("user", f"Topic: {topic}\nSource: {source}\n\n{posts_text}"),
    ])
    return result.model_dump()


if __name__ == "__main__":
    user_text = " ".join(sys.argv[1:]) or input("Enter a topic: ")
    print(write_script(user_text))
