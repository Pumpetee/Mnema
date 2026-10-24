"""Nothing is hidden by default since 23.10.2026: tests of the hiding itself lock the topics the way the owner would."""

from mnema.clients import load_clients, save_clients

CLOUD = ("chatgpt", "gemini", "openrouter", "cursor")


def lock_cloud(vault, tags=("money", "health", "private")) -> None:
    """The owner hides money, health and private from ChatGPT, Gemini, OpenRouter and Cursor."""
    cl = load_clients(vault)
    for cid in CLOUD:
        cl[cid].deny_tags = list(tags)
    save_clients(vault, cl)
