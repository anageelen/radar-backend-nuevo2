from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

from .database import Automation, Search, User, Result
from .services.search_service import SearchService
from .services.ai_service import AIService
from .celery_app import celery_app

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./radar.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

search_service = SearchService()
ai_service = AIService()

@celery_app.task
def run_automated_searches():
    """Run scheduled automated searches"""
    
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        automations = db.query(Automation).filter(
            Automation.is_active == True,
            Automation.next_run <= now
        ).all()
        
        for automation in automations:
            try:
                search = db.query(Search).filter(Search.id == automation.search_id).first()
                if not search:
                    continue
                
                search_results = search_service.search_all_sources(search.query, search.filters or {})
                
                for result_data in search_results:
                    existing = db.query(Result).filter(
                        Result.search_id == search.id,
                        Result.url == result_data["url"]
                    ).first()
                    
                    if not existing:
                        result_record = Result(
                            search_id=search.id,
                            title=result_data["title"],
                            url=result_data["url"],
                            snippet=result_data["snippet"],
                            country=result_data.get("country", "Unknown"),
                            language=result_data.get("language", "Unknown"),
                            date=result_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                            category=result_data.get("category", "Web"),
                            status=result_data.get("status", "Activo"),
                            source=result_data.get("source", "Unknown"),
                            score=result_data.get("score", 0),
                            result_metadata=result_data
                        )
                        db.add(result_record)
                
                automation.last_run = now
                
                if automation.frequency == "24h":
                    automation.next_run = now + timedelta(hours=24)
                elif automation.frequency == "weekly":
                    automation.next_run = now + timedelta(weeks=1)
                elif automation.frequency == "monthly":
                    automation.next_run = now + timedelta(days=30)
                
                db.commit()
                
            except Exception as e:
                print(f"Error running automation {automation.id}: {e}")
                continue
    
    finally:
        db.close()
    
    return f"Processed {len(automations)} automations"

@celery_app.task
def generate_column_data_async(column_id: int, search_id: int, description: str):
    """Generate column data asynchronously"""
    
    db = SessionLocal()
    try:
        results = db.query(Result).filter(Result.search_id == search_id).all()
        
        column_data = ai_service.generate_column_data(
            description,
            [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
        )
        
        from .database import ColumnValue
        for i, result in enumerate(results):
            value = column_data[i] if i < len(column_data) else "N/A"
            column_value = ColumnValue(
                column_id=column_id,
                result_id=result.id,
                value=value
            )
            db.add(column_value)
        
        db.commit()
        
    finally:
        db.close()
    
    return f"Generated data for column {column_id}"
