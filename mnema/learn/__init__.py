"""Learning: Mnema watches where the owner already lives (AI chats, notes, mail, Telegram) and learns about him.

The owner owes it nothing: no forms, no interviews. He chooses only *how* it learns:

- per source: off / observe (show what it would learn, write nothing) / approve (everything goes to a
  review queue) / mixed (confident and non-sensitive goes in silently, sensitive and disputed to the
  queue) / quiet (writes everything, journal and undo are the safety net);
- which "brain" reads the texts: none (explicit signals only), Claude Code, an API key, a local Ollama;
- what never to learn: "don't learn things like this" turns into a stop list.

Pipeline: source → episodes → brain → candidates → ledger (dedup, reinforcement, conflicts) → policy →
memory (with journal, undoable) or review queue. Learned facts that never repeat and were never
confirmed are offered for forgetting — never deleted silently.
"""
