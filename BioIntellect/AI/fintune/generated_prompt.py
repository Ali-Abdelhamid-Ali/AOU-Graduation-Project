DEFAULT_QA_NUM_RECORDS = 30


def chunking_prompt_template(raw_text: str,
                             min_chars: int = 800,
                             max_chars: int = 3500) -> str:
    return f"""
ROLE
You are a medical-document semantic chunker.
You split clinical text into self-contained chunks that preserve meaning and are safe for downstream clinical QA generation.

NON-NEGOTIABLE GOAL
Each chunk MUST be understandable on its own without needing the next/previous chunk.
Never create a chunk that ends mid-sentence, mid-list item, mid-table row, or mid-recommendation.

INPUT ASSUMPTIONS
- The input may contain page markers (e.g., [PAGE 12]) and formatting artifacts from PDF extraction.
- The text may contain headings, subheadings, bullet lists, numbered recommendations, tables, footnotes, and references.

CHUNKING RULES (STRICT)
A) Boundary rules (prefer in this order):
   1) Hard boundary at major headings / section titles.
   2) Boundary at paragraph breaks when the paragraph is a complete idea.
   3) Boundary when the topic shifts (different condition, population, intervention, setting, timeframe, or outcome).
   4) Keep numbered/bulleted lists WITH their lead-in sentence(s). Do not split list from its introduction.
   5) Keep tables with: caption/title + column headers + all rows + footnotes, as ONE chunk when possible.
   6) If a section contains cross-references ("see table X", "above", "below") ensure the referenced content is inside the same chunk; otherwise mark it as missing (see rule D).

B) Size rules:
   - Target chunk size: {min_chars} to {max_chars} characters.
   - If a coherent unit is slightly smaller/larger, prefer preserving meaning over size.
   - If a unit is too large, split only at subheadings or paragraph boundaries that preserve completeness.

C) Self-containment rules:
   - If a chunk starts with pronouns or deictic references ("this", "that", "above"), prepend the minimal necessary preceding heading line(s) to make it standalone.
   - Include the nearest parent heading(s) when they disambiguate scope (condition/population/setting).

D) Missing-reference handling:
   - If the text references missing material not present in the input (e.g., "Table 3" not included), DO NOT invent it.
   - Add a short line at the end of that chunk:
     "MISSING_REFERENCE: <what is referenced>"
   - Do NOT add any other commentary.

OUTPUT FORMAT (STRICT)
Return ONLY valid JSON.
Return ONLY a JSON array named implicitly (no wrapper keys).
Each element MUST be an object with EXACTLY these keys:
  - "chunk_id"   (string, sequential like "c0001")
  - "chunk_title" (string; may be empty "")
  - "chunk_text" (string; the full chunk text)
No other keys. No markdown. No extra text.

QUALITY CHECK BEFORE FINAL OUTPUT
rify every chunk ends at a natural boundary (sentence/paragraph/list/table).
- Verify every chunk is self-contained (readable without neighbors).
- Verify JSON validity.

DATA
{raw_text}
""".strip()

def qa_prompt_template(
    chunk_text: str,
    num_records: int = DEFAULT_QA_NUM_RECORDS,
) -> str:
    return f"""
ROLE
You are a clinical training-data generator for instruction fine-tuning.
You generate high-value, clinically actionable (but non-personalized) Q/A pairs from ONE provided chunk.
You must be precise, conservative, and strictly evidence-grounded.

PRIMARY OBJECTIVE
Generate EXACTLY {num_records} medically-focused question–answer pairs from the chunk.
Questions MUST be general clinical questions (doctor/nurse style) — NOT questions about the PDF/document.
Answers MUST be supported by the chunk text alone.

ABSOLUTE SAFETY + GROUNDING RULES
1) NO outside knowledge. Do not use medical facts that are not explicitly in the chunk.
2) NO patient-specific advice. If a question implies personal diagnosis/treatment, answer:
   "Cannot provide patient-specific medical advice. Not stated in the provided chunk."
3) NO fabrication of numbers, doses, thresholds, contraindications, durations, test names, or risk estimates.
4) Preserve recommendation strength wording exactly (e.g., "offer", "consider", "do not offer/do not").
5) If the chunk does not contain the needed info, the answer MUST say:
   "Not stated in the provided chunk."
6) Every answer MUST end with:
   Evidence: "<5–25 word exact quote from the chunk>"
   - Quote must be verbatim and must support the answer.
   - If truly impossible, write: Evidence: "Not stated in the provided chunk."

QUESTION DESIGN (STRICT)
- Questions must be medical/clinical. Examples:
  - assessment/triage, indications/contraindications, eligibility criteria
  - monitoring/follow-up, safety warnings, red flags (ONLY if present)
  - workflow responsibilities (doctor/nurse roles) ONLY if present
  - definitions/criteria stated in the chunk
  - timing windows, thresholds, dosing instructions (ONLY if present)
- DO NOT ask about the document structure (chapters, PDF, page numbers, "what does the guideline say about itself"),
  unless the chunk has ONLY scope/disclaimer content; then ask about scope/limitations in a healthcare context.

ANSWER QUALITY REQUIREMENTS
- Answers must be clear and clinically formatted as plain text (no markdown).
- Use a compact structure when applicable:
  1) Direct answer (1–2 sentences)
  2) Details (bullet-like lines using hyphens "-" is allowed as plain text)
  3) Exceptions / "Do not" items (ONLY if stated)
- Do NOT define medical terms unless the chunk defines them.
  If a key term appears but is not defined in the chunk, add a final line before Evidence:
  "Term not defined in chunk: <term1>, <term2>"

COVERAGE PLANNING (MANDATORY)
Before writing final Q/A, internally identify "atomic facts" and make a coverage plan:
- Spread across distinct facts/topics; avoid duplicates/paraphrases.
- Prioritize decision-relevant items: do-not rules, criteria, timing, thresholds, responsibilities, subgroups.
- If the chunk contains numbered recommendations (e.g., 1.2.2), include the number in BOTH question and answer.

OUTPUT FORMAT (STRICT)
Return ONLY valid JSON.
Return ONLY a JSON array with EXACTLY {num_records} objects.
Each object MUST have EXACTLY two keys:
  - "question"
  - "answer"
No markdown. No extra keys. No extra text.

CHUNK
{chunk_text}
""".strip()

if __name__ == "__main__":
    print(qa_prompt_template("ALi", 12), chunking_prompt_template("ALi"))
