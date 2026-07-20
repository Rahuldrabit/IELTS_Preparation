import asyncio
from shared.schemas import ExamOutput
from services.llm import get_llm_client, LLMClientError
from . import repository

def build_vlm_prompt() -> str:
    return """Analyze this IELTS exam page image carefully.

Your task:
1. Extract the reading passage text with paragraph IDs (A, B, C, D, etc.)
2. Identify all question groups and their types:
   - TRUE_FALSE_NOT_GIVEN
   - MATCHING_HEADINGS
   - SUMMARY_COMPLETION
   - MULTIPLE_CHOICE
   - SENTENCE_COMPLETION
   - FILL_BLANK
3. For each question, extract:
   - The question text
   - Options (if applicable)
   - The correct answer from the passage
   - The paragraph where the answer evidence is found (paragraph_anchor_id)
   - The evidence text (verbatim sentence(s))
   - Cognitive distractor analysis (why students might pick a wrong answer)

Requirements:
- Combine the passage into paragraphs labeled A, B, C, etc.
- Group questions by their section/type
- If you cannot determine a correct answer, make your best educated guess based on the passage
- Generate paragraph_anchor_id and evidence_text for every question

Return JSON matching the ExamOutput schema."""

async def process_import_job_vlm(import_id: int, file_paths: list[str], db_url: str, user_id: int = 1):
    from shared.database import async_session_maker
    
    async with async_session_maker() as db:
        try:
            await repository.update_job_status(db, import_id, "processing")
            
            client = get_gemma_client()
            prompt = build_vlm_prompt()

            for path in file_paths:
                if not path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
                    continue

                try:
                    exam: ExamOutput = await asyncio.to_thread(
                        client.generate_structured,
                        prompt=prompt,
                        schema=ExamOutput,
                        image_path=path,
                        temperature=0.0,
                    )

                    passage = await repository.store_exam_output(db, exam, user_id)
                    await repository.update_job_status(db, import_id, "completed", passage_id=passage.id)

                except GemmaClientError as e:
                    await repository.update_job_status(db, import_id, "failed", error_message=f"VLM processing failed: {str(e)}")
                    return

        except Exception as e:
            await repository.update_job_status(db, import_id, "failed", error_message=str(e))
