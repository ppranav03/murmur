import re
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

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


if __name__ == "__main__":
    user_text = " ".join(sys.argv[1:]) or input("Enter a topic: ")
    print(write_script(user_text))
