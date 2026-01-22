"""
Script to copy paragraph.content to paragraph_contents.explain_text
for all paragraphs that don't have ParagraphContent records.
"""
import asyncio
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.paragraph import Paragraph
from app.models.paragraph_content import ParagraphContent


def calculate_source_hash(content: str, summary: str = None, learning_objective: str = None) -> str:
    """Calculate hash from paragraph content."""
    source_text = f"{content or ''}"
    source_text += f"|{summary or ''}"
    source_text += f"|{learning_objective or ''}"
    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


async def copy_content_to_paragraph_contents():
    """Copy paragraph content to paragraph_contents explain_text."""
    async with AsyncSessionLocal() as db:
        # Get all paragraphs with their textbook info to determine language
        query = text("""
            SELECT
                p.id as paragraph_id,
                p.content,
                p.summary,
                p.learning_objective,
                p.title,
                t.id as textbook_id,
                t.title as textbook_title
            FROM paragraphs p
            JOIN chapters c ON c.id = p.chapter_id
            JOIN textbooks t ON t.id = c.textbook_id
            WHERE p.is_deleted = false
            AND p.content IS NOT NULL
            AND LENGTH(p.content) > 0
            ORDER BY t.id, p.id
        """)

        result = await db.execute(query)
        paragraphs = result.fetchall()

        print(f"Found {len(paragraphs)} paragraphs with content")

        # Language mapping based on textbook
        # Russian textbooks: 11
        # Kazakh textbooks: 15
        textbook_languages = {
            11: "ru",
            15: "kk",
        }

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for p in paragraphs:
            paragraph_id = p.paragraph_id
            content = p.content
            summary = p.summary
            learning_objective = p.learning_objective
            textbook_id = p.textbook_id

            # Determine language based on textbook
            language = textbook_languages.get(textbook_id, "ru")

            # Check if ParagraphContent already exists
            existing = await db.execute(
                select(ParagraphContent).where(
                    ParagraphContent.paragraph_id == paragraph_id,
                    ParagraphContent.language == language
                )
            )
            existing_content = existing.scalar_one_or_none()

            source_hash = calculate_source_hash(content, summary, learning_objective)

            if existing_content:
                # Check if explain_text is empty or needs update
                if not existing_content.explain_text or len(existing_content.explain_text.strip()) == 0:
                    existing_content.explain_text = content
                    existing_content.source_hash = source_hash
                    existing_content.status_explain = "ready"
                    updated_count += 1
                    print(f"  Updated paragraph {paragraph_id} ({language}): {p.title[:50]}...")
                else:
                    skipped_count += 1
                    # print(f"  Skipped paragraph {paragraph_id} ({language}): already has explain_text")
            else:
                # Create new ParagraphContent
                new_content = ParagraphContent(
                    paragraph_id=paragraph_id,
                    language=language,
                    explain_text=content,
                    source_hash=source_hash,
                    status_explain="ready",
                    status_audio="empty",
                    status_slides="empty",
                    status_video="empty",
                    status_cards="empty",
                )
                db.add(new_content)
                created_count += 1
                print(f"  Created paragraph {paragraph_id} ({language}): {p.title[:50]}...")

        await db.commit()

        print(f"\n{'='*60}")
        print(f"Summary:")
        print(f"  Created: {created_count}")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total processed: {len(paragraphs)}")


if __name__ == "__main__":
    asyncio.run(copy_content_to_paragraph_contents())
