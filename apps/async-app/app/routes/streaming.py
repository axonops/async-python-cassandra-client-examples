from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime, timedelta
import json
import logging
import asyncio

from ..models import SensorData
from ..database import db
from ..metrics import track_cassandra_operation, stream_buffer_size
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


async def sensor_data_generator(
    device_id: Optional[UUID] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    batch_size: int = 100
) -> AsyncGenerator[str, None]:
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    # Build query
    query = "SELECT * FROM sensor_data"
    params = []
    conditions = []
    
    if device_id:
        conditions.append("device_id = ?")
        params.append(device_id)
    
    if start_time:
        conditions.append("timestamp >= ?")
        params.append(start_time)
    
    if end_time:
        conditions.append("timestamp <= ?")
        params.append(end_time)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ALLOW FILTERING"
    
    try:
        result = await session.execute_async(query, params if params else None)
        
        buffer = []
        async for row in result:
            data = {
                "device_id": str(row.device_id),
                "timestamp": row.timestamp.isoformat(),
                "temperature": row.temperature,
                "humidity": row.humidity,
                "pressure": row.pressure,
                "metadata": json.loads(row.metadata) if row.metadata else {}
            }
            buffer.append(json.dumps(data))
            
            if len(buffer) >= batch_size:
                stream_buffer_size.labels(stream_type="sensor_data").set(len(buffer))
                yield "\n".join(buffer) + "\n"
                buffer = []
                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming client
        
        if buffer:
            yield "\n".join(buffer) + "\n"
            
    except Exception as e:
        logger.error(f"Error streaming sensor data: {e}")
        yield json.dumps({"error": str(e)}) + "\n"


@router.get("/stream/sensor-data")
async def stream_sensor_data(
    device_id: Optional[UUID] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    batch_size: int = Query(100, ge=1, le=1000)
):
    return StreamingResponse(
        sensor_data_generator(device_id, start_time, end_time, batch_size),
        media_type="application/x-ndjson"
    )


@router.post("/sensor-data/generate/{count}")
@track_cassandra_operation("batch_insert", "sensor_data")
async def generate_sensor_data(count: int, device_id: Optional[UUID] = None):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    if count > 10000:
        raise HTTPException(status_code=400, detail="Count cannot exceed 10000")
    
    device_id = device_id or UUID("00000000-0000-0000-0000-000000000001")
    
    try:
        batch_size = settings.batch_size
        inserted = 0
        
        for i in range(0, count, batch_size):
            batch = session.prepare_batch()
            current_batch_size = min(batch_size, count - i)
            
            for j in range(current_batch_size):
                timestamp = datetime.utcnow() - timedelta(seconds=i+j)
                sensor_data = SensorData(
                    device_id=device_id,
                    timestamp=timestamp,
                    temperature=20 + (j % 10),
                    humidity=40 + (j % 20),
                    pressure=1013 + (j % 5),
                    metadata={"batch": i, "index": j}
                )
                
                batch.add(
                    """
                    INSERT INTO sensor_data 
                    (device_id, timestamp, temperature, humidity, pressure, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (sensor_data.device_id, sensor_data.timestamp, 
                     sensor_data.temperature, sensor_data.humidity,
                     sensor_data.pressure, json.dumps(sensor_data.metadata))
                )
            
            await session.execute_batch(batch)
            inserted += current_batch_size
            
            if i % 1000 == 0 and i > 0:
                logger.info(f"Inserted {inserted}/{count} sensor records")
        
        return {"message": f"Generated {count} sensor data records", "device_id": str(device_id)}
        
    except Exception as e:
        logger.error(f"Failed to generate sensor data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream/large-dataset/{size}")
async def stream_large_dataset(size: int = 1000):
    async def generate():
        for i in range(size):
            data = {
                "index": i,
                "timestamp": datetime.utcnow().isoformat(),
                "data": f"Record {i} of {size}",
                "value": i * 1.5
            }
            yield json.dumps(data) + "\n"
            
            if i % 100 == 0:
                stream_buffer_size.labels(stream_type="large_dataset").set(i)
                await asyncio.sleep(0.001)
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.get("/stream/documents")
async def stream_documents(
    page_size: int = Query(100, ge=1, le=1000),
    title_filter: Optional[str] = Query(None)
):
    session = db.get_session()
    if not session:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    async def generate():
        query = "SELECT * FROM documents"
        params = []
        
        if title_filter:
            query += " WHERE title = ? ALLOW FILTERING"
            params.append(title_filter)
        
        try:
            result = await session.execute_async(query, params if params else None)
            
            buffer = []
            async for row in result:
                doc = {
                    "id": str(row.id),
                    "title": row.title,
                    "content": row.content[:200] + "..." if len(row.content) > 200 else row.content,
                    "tags": row.tags if row.tags else [],
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat()
                }
                buffer.append(json.dumps(doc))
                
                if len(buffer) >= page_size:
                    yield "\n".join(buffer) + "\n"
                    buffer = []
                    await asyncio.sleep(0.01)
            
            if buffer:
                yield "\n".join(buffer) + "\n"
                
        except Exception as e:
            logger.error(f"Error streaming documents: {e}")
            yield json.dumps({"error": str(e)}) + "\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")