CONVERSATION_ARCHIVE_PROMPT = """
The current conversation has grown too long, and the following is a segment of the dialogue that needs to be summarized.

Please summarize this content according to the following criteria:

1.  **Core Points & Current State**: Extract the **main topics discussed, key information, any conclusions reached, decisions made, and importantly, the current state or intermediate results of any ongoing tasks** within this dialogue segment.
2.  **Unresolved Matters/Future Directions**: Identify any **open questions, pending tasks, points of disagreement, or areas that could be explored further** that are still pending.
3.  **Concise Format**: The summary should be **brief and to the point**, maintaining information density while avoiding redundancy.

After the summary, please provide 1-2 **follow-up questions or discussion points** so we can continue the conversation based on the current state.


---
{last_summary}
---
{conversation}
---
"""
