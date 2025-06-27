from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID
import json
import logging

from ..models import User, Document, PaginationParams, SearchParams
from ..database import db
from ..metrics import track_cassandra_operation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/users", response_model=User)
@track_cassandra_operation("insert", "users")
async def create_user(user: User):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        await session.execute(
            """
            INSERT INTO users (id, username, email, created_at, profile_data)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user.id, user.username, user.email, user.created_at, json.dumps(user.profile_data))
        )
        return user
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/batch", response_model=List[User])
@track_cassandra_operation("batch_insert", "users")
async def create_users_batch(users: List[User]):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        batch = session.prepare_batch()
        for user in users:
            batch.add(
                """
                INSERT INTO users (id, username, email, created_at, profile_data)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user.id, user.username, user.email, user.created_at, json.dumps(user.profile_data))
            )
        await session.execute_batch(batch)
        return users
    except Exception as e:
        logger.error(f"Failed to create users batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=User)
@track_cassandra_operation("select", "users")
async def get_user(user_id: UUID):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = await session.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = result.one()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(
            id=row.id,
            username=row.username,
            email=row.email,
            created_at=row.created_at,
            profile_data=json.loads(row.profile_data) if row.profile_data else {}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", response_model=List[User])
@track_cassandra_operation("select_all", "users")
async def list_users(
    pagination: PaginationParams = PaginationParams(),
    username: Optional[str] = Query(None)
):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        # Note: In production, use proper pagination with paging state
        query = "SELECT * FROM users"
        params = []
        
        if username:
            query += " WHERE username = ? ALLOW FILTERING"
            params.append(username)
        
        query += f" LIMIT {pagination.page_size}"
        
        result = await session.execute(query, params if params else None)
        
        users = []
        for row in result:
            users.append(User(
                id=row.id,
                username=row.username,
                email=row.email,
                created_at=row.created_at,
                profile_data=json.loads(row.profile_data) if row.profile_data else {}
            ))
        
        return users
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}", response_model=User)
@track_cassandra_operation("update", "users")
async def update_user(user_id: UUID, user: User):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        user.id = user_id
        await session.execute(
            """
            UPDATE users
            SET username = ?, email = ?, profile_data = ?
            WHERE id = ?
            """,
            (user.username, user.email, json.dumps(user.profile_data), user_id)
        )
        return user
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
@track_cassandra_operation("delete", "users")
async def delete_user(user_id: UUID):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        await session.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        return {"message": "User deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents", response_model=Document)
@track_cassandra_operation("insert", "documents")
async def create_document(document: Document):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        await session.execute(
            """
            INSERT INTO documents (id, title, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document.id, document.title, document.content, document.tags, 
             document.created_at, document.updated_at)
        )
        return document
    except Exception as e:
        logger.error(f"Failed to create document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=Document)
@track_cassandra_operation("select", "documents")
async def get_document(document_id: UUID):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        result = await session.execute(
            "SELECT * FROM documents WHERE id = ?",
            (document_id,)
        )
        row = result.one()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return Document(
            id=row.id,
            title=row.title,
            content=row.content,
            tags=row.tags if row.tags else [],
            created_at=row.created_at,
            updated_at=row.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))