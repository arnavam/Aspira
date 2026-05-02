"""
Centralized Prompt Definitions

These prompts are stored here temporarily. Later, they can be migrated
to Langfuse Prompt Management and fetched dynamically. Variable names 
in curly brackets match the variables that will be passed during compilation 
(which mirrors how Langfuse handles mustache/template variables).
"""

# System prompt for the query generation agent
QUERY_AGENT_SYSTEM_PROMPT = "You are a JSON generator. Output only valid JSON, nothing else."

# System prompt for the question generation agent
QUESTION_AGENT_SYSTEM_PROMPT = "You are an AI interviewer. Generate plain questions without numbering or formatting."

# Main prompt for query generation
# Variables: {context}, {answer}, {metadata_section}
QUERY_GENERATION_PROMPT = """Analyze this conversation and decide if web search is needed, and if the interview should conclude.

{metadata_section}

{context}


LATEST MESSAGE: "{answer}"

Respond with JSON only following this structure:
{{
  "skip": boolean,
  "reason": "string",
  "queries": ["query1", "query2"],
  "is_interview_complete": boolean
}}

Set "is_interview_complete" to true ONLY IF:
- You have sufficiently assessed the candidate's strengths, weaknesses, and fit for the role criteria mentioned above (if provided).
- Or, if no specific criteria were provided, you feel you have a solid general understanding of their professional background after a reasonable number of turns.

Set "skip" to true if:
- The latest message is nonsense/greeting/vague/short OR
- You are setting "is_interview_complete" to true (no need to search if we are ending).

Generate search queries that are relevant to the ENTIRE conversation context.

Respond with valid JSON only, no other text:"""

# Main prompt for generating the final interview questions
# Variables: {history_section}, {context_section}, {metadata_section}
INTERVIEW_QUESTION_PROMPT = """You are an AI recruiter conducting a professional interview.

{metadata_section}

{history_section}
{context_section}

Your goal is to evaluate the candidate's strengths, weaknesses, and fit for the role/company described above. If no specific role is provided, conduct a thorough general professional interview.

Review the history. If you have not gathered enough information to fulfill your evaluation criteria, ask a targeted follow-up question based on their previous answer to extract that information.

Generate exactly 3 relevant follow-up interview questions.
- Do NOT number the questions
- Do NOT use bullet points or asterisks
- Do NOT use markdown formatting (no ** or *)
- Just write plain questions, one per line"""
