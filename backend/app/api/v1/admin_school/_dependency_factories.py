"""
Factory functions for generating School Admin dependencies.

Provides reusable patterns for:
1. Entity dependencies (User, Student, Teacher, Parent, Class)
2. Content dependencies (Textbook, Test - with read/write variants)
3. Hierarchical dependencies (Chapter→Textbook, Paragraph→Chapter, Question→Test, Option→Question)
"""

from typing import Any, Callable, Tuple, TypeVar

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_school_id
from app.core.database import get_db

T = TypeVar('T')


def create_entity_dependency(
    entity_name: str,
    repo_class_path: str,
    repo_method: str = "get_by_id",
    id_param_name: str = None,
    extra_kwargs: dict = None
) -> Callable:
    """
    Factory for simple entity dependencies with school ownership check.

    Use for: User, Student, Teacher, Parent, SchoolClass

    Args:
        entity_name: Human-readable name for error messages
        repo_class_path: Full import path to repository class
        repo_method: Repository method to call (default: "get_by_id")
        id_param_name: Path parameter name (default: "{entity_name.lower()}_id")
        extra_kwargs: Additional kwargs for repo method (e.g., load_user=True)

    Returns:
        FastAPI dependency function
    """
    param_name = id_param_name or f"{entity_name.lower()}_id"
    kwargs = extra_kwargs or {}

    async def dependency(
        entity_id: int,
        school_id: int = Depends(get_current_user_school_id),
        db: AsyncSession = Depends(get_db)
    ):
        # Dynamic import to avoid circular imports
        module_path, class_name = repo_class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        repo_class = getattr(module, class_name)

        repo = repo_class(db)
        method = getattr(repo, repo_method)

        # Call with appropriate signature
        if kwargs:
            entity = await method(entity_id, school_id, **kwargs)
        else:
            entity = await method(entity_id)

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} {entity_id} not found"
            )

        # School ownership check (for entities without school_id in repo method)
        if hasattr(entity, 'school_id') and not kwargs:
            if entity.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to this {entity_name.lower()}"
                )

        return entity

    # Rename function parameters for FastAPI
    dependency.__annotations__ = {
        param_name: int,
        "school_id": int,
        "db": AsyncSession,
        "return": Any
    }

    return dependency


def create_content_dependency(
    entity_name: str,
    repo_class_path: str,
    repo_method: str = "get_by_id",
    id_param_name: str = None,
    extra_kwargs: dict = None,
    write_mode: bool = False
) -> Callable:
    """
    Factory for content dependencies with global/school distinction.

    Use for: Textbook, Test

    Args:
        entity_name: Human-readable name for error messages
        repo_class_path: Full import path to repository class
        repo_method: Repository method to call
        id_param_name: Path parameter name
        extra_kwargs: Additional kwargs for repo method
        write_mode: If True, reject global content (school_id=NULL)

    Returns:
        FastAPI dependency function
    """
    param_name = id_param_name or f"{entity_name.lower()}_id"
    kwargs = extra_kwargs or {}

    async def dependency(
        entity_id: int,
        school_id: int = Depends(get_current_user_school_id),
        db: AsyncSession = Depends(get_db)
    ):
        module_path, class_name = repo_class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        repo_class = getattr(module, class_name)

        repo = repo_class(db)
        method = getattr(repo, repo_method)

        if kwargs:
            entity = await method(entity_id, **kwargs)
        else:
            entity = await method(entity_id)

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} {entity_id} not found"
            )

        # Write mode: reject global content
        if write_mode and entity.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot modify global {entity_name.lower()}s. Contact SUPER_ADMIN."
            )

        # Access check
        if entity.school_id is not None and entity.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to this {entity_name.lower()}"
            )

        return entity

    dependency.__annotations__ = {
        param_name: int,
        "school_id": int,
        "db": AsyncSession,
        "return": Any
    }

    return dependency


def create_hierarchical_dependency(
    entity_name: str,
    entity_repo_path: str,
    parent_chain: list[Tuple[str, str, str]],
    id_param_name: str = None,
    write_mode: bool = False,
    return_chain: bool = False
) -> Callable:
    """
    Factory for hierarchical content dependencies.

    Use for: Chapter→Textbook, Paragraph→Chapter→Textbook,
             Question→Test, Option→Question→Test

    Args:
        entity_name: Human-readable name for error messages
        entity_repo_path: Full import path to entity's repository
        parent_chain: List of (parent_name, repo_path, foreign_key) tuples
            Example: [("textbook", "app.repos.TextbookRepository", "textbook_id")]
        id_param_name: Path parameter name
        write_mode: If True, reject global content
        return_chain: If True, returns tuple of (entity, *parents)

    Returns:
        FastAPI dependency function
    """
    param_name = id_param_name or f"{entity_name.lower()}_id"

    async def dependency(
        entity_id: int,
        school_id: int = Depends(get_current_user_school_id),
        db: AsyncSession = Depends(get_db)
    ):
        # Get main entity
        module_path, class_name = entity_repo_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        repo_class = getattr(module, class_name)

        repo = repo_class(db)
        entity = await repo.get_by_id(entity_id)

        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_name} {entity_id} not found"
            )

        # Traverse parent chain
        current = entity
        parents = []
        root_entity = None

        for parent_name, parent_repo_path, foreign_key in parent_chain:
            parent_id = getattr(current, foreign_key)

            p_module_path, p_class_name = parent_repo_path.rsplit('.', 1)
            p_module = __import__(p_module_path, fromlist=[p_class_name])
            p_repo_class = getattr(p_module, p_class_name)

            p_repo = p_repo_class(db)

            # Handle Test repo special case (load_questions param)
            if "TestRepository" in parent_repo_path:
                parent = await p_repo.get_by_id(parent_id, load_questions=False)
            else:
                parent = await p_repo.get_by_id(parent_id)

            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent {parent_name} not found"
                )

            parents.append(parent)
            current = parent
            root_entity = parent

        # Access check on root entity (textbook or test)
        if root_entity and hasattr(root_entity, 'school_id'):
            if write_mode and root_entity.school_id is None:
                entity_type = parent_chain[-1][0]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cannot modify {entity_name.lower()}s in global {entity_type}s. Contact SUPER_ADMIN."
                )

            if root_entity.school_id is not None and root_entity.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied to this {entity_name.lower()}"
                )

        if return_chain:
            return (entity, *parents)
        return entity

    dependency.__annotations__ = {
        param_name: int,
        "school_id": int,
        "db": AsyncSession,
        "return": Any
    }

    return dependency
