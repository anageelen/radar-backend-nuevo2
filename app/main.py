from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .database import get_db, create_tables, User, Search, Result, CustomColumn, ColumnValue, Automation
from .services.search_service import SearchService
from .services.ai_service import AIService

load_dotenv()

app = FastAPI(title="RADAR Backend", version="1.0.0")

search_service = SearchService()
ai_service = AIService()
security = HTTPBearer(auto_error=False)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class SearchResult(BaseModel):
    id: str
    title: str
    url: str
    country: str
    language: str
    date: str
    category: str
    status: str
    source: str
    score: int

class SearchRequest(BaseModel):
    query: str
    create_filters: Optional[bool] = False

class SearchResponse(BaseModel):
    results: List[SearchResult]
    filters: Optional[Dict[str, str]] = None

class JobRequest(BaseModel):
    query: str
    interval: str
    filters: Optional[Dict[str, Any]] = None

class UpdateItemRequest(BaseModel):
    field_name: str
    field_value: Any

class RefineRequest(BaseModel):
    search_id: Optional[int] = None
    filters: Dict[str, Any]
    query: Optional[str] = None

class ColumnRequest(BaseModel):
    search_id: int
    name: str
    description: str
    generate_data: Optional[bool] = True

class AuthRequest(BaseModel):
    email: str

class AuthResponse(BaseModel):
    access_token: str
    user_email: str

class SearchHistoryResponse(BaseModel):
    searches: List[Dict[str, Any]]
    total: int

class AIChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    search_id: Optional[int] = None

class AIChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    columns: Optional[List[Dict[str, str]]] = None

class SupportChatRequest(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = None

class SupportChatResponse(BaseModel):
    response: str
    helpful_links: Optional[List[Dict[str, str]]] = None

MOCK_RESULTS = [
    SearchResult(
        id="1",
        title="Última hora: Avance tecnológico revolucionario",
        url="https://example.com/tech-breakthrough",
        country="USA",
        language="Inglés",
        date="2024-01-15",
        category="Tecnología",
        status="Activo",
        source="TechNews",
        score=95
    ),
    SearchResult(
        id="2",
        title="Análisis de mercado: Resultados del Q4",
        url="https://example.com/market-analysis",
        country="UK",
        language="Inglés",
        date="2024-01-14",
        category="Finanzas",
        status="Pendiente",
        source="FinanceDaily",
        score=87
    ),
    SearchResult(
        id="3",
        title="Estudio del impacto del cambio climático",
        url="https://example.com/climate-study",
        country="DE",
        language="Alemán",
        date="2024-01-13",
        category="Medio Ambiente",
        status="Activo",
        source="ScienceJournal",
        score=92
    ),
    SearchResult(
        id="4",
        title="Informe de innovación en salud",
        url="https://example.com/healthcare-report",
        country="CA",
        language="Inglés",
        date="2024-01-12",
        category="Salud",
        status="Completado",
        source="MedNews",
        score=89
    ),
    SearchResult(
        id="5",
        title="Tendencias en desarrollo de IA",
        url="https://example.com/ai-trends",
        country="JP",
        language="Japonés",
        date="2024-01-11",
        category="Tecnología",
        status="Activo",
        source="AIToday",
        score=94
    )
]

@app.on_event("startup")
async def startup_event():
    print("=== RADAR Backend Starting ===")
    print(f"Python version: {sys.version}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Port: {os.getenv('PORT', 'not set')}")
    print(f"DATABASE_URL configured: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
    
    try:
        create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Warning: Database initialization failed: {e}")
        print("App will continue without database connectivity")
    
    print("=== RADAR Backend Startup Complete ===")

@app.get("/healthz")
async def healthz():
    """Health check endpoint that doesn't depend on database"""
    print(f"🔍 Healthcheck requested at {datetime.utcnow().isoformat()}")
    response = {
        "status": "ok", 
        "service": "RADAR Backend",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "port": os.getenv('PORT', 'not set')
    }
    print(f"✅ Healthcheck response: {response}")
    return response

@app.post("/auth/login", response_model=AuthResponse)
async def login(request: AuthRequest, db: Session = Depends(get_db)):
    """Simple email-based authentication"""
    
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        user = User(email=request.email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    token = f"token_{user.id}_{datetime.now().timestamp()}"
    
    return AuthResponse(
        access_token=token,
        user_email=user.email
    )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from token"""
    if not credentials:
        return None
    
    try:
        token_parts = credentials.credentials.split("_")
        if len(token_parts) >= 2:
            user_id = int(token_parts[1])
            user = db.query(User).filter(User.id == user_id).first()
            return user
    except:
        pass
    
    return None

@app.post("/ai-search", response_model=SearchResponse)
async def ai_search(
    request: SearchRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI-powered search with automatic filter generation"""
    
    interpretation = await ai_service.interpret_query(request.query)
    
    search_results = await search_service.search_all_sources(
        request.query, 
        interpretation.get("filters", {})
    )
    
    if current_user:
        search_record = Search(
            user_id=current_user.id,
            query=request.query,
            filters=interpretation.get("filters", {})
        )
        db.add(search_record)
        db.commit()
        db.refresh(search_record)
        
        for result_data in search_results:
            result_record = Result(
                search_id=search_record.id,
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
        
        db.commit()
    
    formatted_results = []
    for i, result_data in enumerate(search_results):
        formatted_results.append(SearchResult(
            id=str(i + 1),
            title=result_data["title"],
            url=result_data["url"],
            country=result_data.get("country", "Unknown"),
            language=result_data.get("language", "Unknown"),
            date=result_data.get("date", datetime.now().strftime("%Y-%m-%d")),
            category=result_data.get("category", "Web"),
            status=result_data.get("status", "Activo"),
            source=result_data.get("source", "Unknown"),
            score=result_data.get("score", 0)
        ))
    
    return SearchResponse(
        results=formatted_results,
        filters=interpretation.get("filters", {}) if request.create_filters else None
    )

@app.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query("", description="Search query"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Results per page"),
    country: Optional[str] = Query(None, description="Filter by country"),
    language: Optional[str] = Query(None, description="Filter by language"),
    category: Optional[str] = Query(None, description="Filter by category"),
    state: Optional[str] = Query(None, description="Filter by status")
):
    """Standard search with query parameters"""
    
    filtered_results = MOCK_RESULTS.copy()
    
    if q:
        filtered_results = [
            result for result in filtered_results
            if (q.lower() in result.title.lower() or
                q.lower() in result.category.lower() or
                q.lower() in result.source.lower())
        ]
    
    if country:
        filtered_results = [r for r in filtered_results if r.country == country]
    if language:
        filtered_results = [r for r in filtered_results if r.language == language]
    if category:
        filtered_results = [r for r in filtered_results if r.category == category]
    if state:
        filtered_results = [r for r in filtered_results if r.status == state]
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = filtered_results[start_idx:end_idx]
    
    return SearchResponse(results=paginated_results)

@app.get("/profile/history", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's search history for profile page"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    total = db.query(Search).filter(Search.user_id == current_user.id).count()
    
    searches = db.query(Search).filter(Search.user_id == current_user.id)\
        .order_by(Search.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    search_history = []
    for search in searches:
        results_count = db.query(Result).filter(Result.search_id == search.id).count()
        columns_count = db.query(CustomColumn).filter(CustomColumn.search_id == search.id).count()
        
        search_history.append({
            "id": search.id,
            "query": search.query,
            "filters": search.filters,
            "created_at": search.created_at.isoformat(),
            "results_count": results_count,
            "columns_count": columns_count
        })
    
    return SearchHistoryResponse(searches=search_history, total=total)

@app.put("/items/{item_id}")
async def update_item(item_id: str, update_data: Dict[str, Any]):
    """Update individual search result fields"""
    
    return {"message": f"Item {item_id} updated successfully", "data": update_data}

@app.post("/jobs")
async def create_job(request: JobRequest):
    """Schedule automated searches"""
    
    return {
        "message": "Job scheduled successfully",
        "job_id": f"job_{datetime.now().timestamp()}",
        "query": request.query,
        "interval": request.interval,
        "next_run": datetime.now().isoformat()
    }

@app.post("/refine")
async def refine_search(
    request: RefineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply dynamic filters to search results"""
    
    if request.search_id:
        search_record = db.query(Search).filter(Search.id == request.search_id).first()
        if not search_record:
            raise HTTPException(status_code=404, detail="Search not found")
        
        results = db.query(Result).filter(Result.search_id == request.search_id).all()
    else:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query required for new search")
        
        search_results = await search_service.search_all_sources(request.query, request.filters)
        
        results = []
        for result_data in search_results:
            results.append(Result(
                title=result_data["title"],
                url=result_data["url"],
                snippet=result_data["snippet"],
                country=result_data.get("country", "Unknown"),
                language=result_data.get("language", "Unknown"),
                date=result_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                category=result_data.get("category", "Web"),
                status=result_data.get("status", "Activo"),
                source=result_data.get("source", "Unknown"),
                score=result_data.get("score", 0)
            ))
    
    filtered_results = []
    for result in results:
        matches = True
        
        for filter_key, filter_value in request.filters.items():
            if filter_key == "country" and result.country != filter_value:
                matches = False
                break
            elif filter_key == "language" and result.language != filter_value:
                matches = False
                break
            elif filter_key == "category" and result.category != filter_value:
                matches = False
                break
            elif filter_key == "status" and result.status != filter_value:
                matches = False
                break
            elif filter_key == "source" and result.source != filter_value:
                matches = False
                break
        
        if matches:
            filtered_results.append(SearchResult(
                id=str(result.id) if hasattr(result, 'id') else str(len(filtered_results) + 1),
                title=result.title,
                url=result.url,
                country=result.country,
                language=result.language,
                date=result.date,
                category=result.category,
                status=result.status,
                source=result.source,
                score=result.score
            ))
    
    return SearchResponse(results=filtered_results)

@app.post("/columns")
async def create_custom_column(
    request: ColumnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create custom columns with AI-generated data"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    search_record = db.query(Search).filter(Search.id == request.search_id).first()
    if not search_record:
        raise HTTPException(status_code=404, detail="Search not found")
    
    results = db.query(Result).filter(Result.search_id == request.search_id).all()
    
    custom_column = CustomColumn(
        search_id=request.search_id,
        name=request.name,
        description=request.description,
        generated_by_ai=request.generate_data
    )
    db.add(custom_column)
    db.commit()
    db.refresh(custom_column)
    
    if request.generate_data:
        column_data = await ai_service.generate_column_data(
            request.description,
            [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
        )
        
        for i, result in enumerate(results):
            value = column_data[i] if i < len(column_data) else "N/A"
            column_value = ColumnValue(
                column_id=custom_column.id,
                result_id=result.id,
                value=value
            )
            db.add(column_value)
        
        db.commit()
    
    return {
        "message": "Custom column created successfully",
        "column_id": custom_column.id,
        "name": custom_column.name,
        "description": custom_column.description,
        "generated_data": request.generate_data
    }

@app.get("/export")
async def export_data(
    format: str = Query("excel", description="Export format: excel or pdf"),
    search_id: Optional[int] = Query(None, description="Search ID to export"),
    db: Session = Depends(get_db)
):
    """Export search results to Excel or PDF"""
    
    if format not in ["excel", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid export format")
    
    if search_id:
        results = db.query(Result).filter(Result.search_id == search_id).all()
        custom_columns = db.query(CustomColumn).filter(CustomColumn.search_id == search_id).all()
    else:
        results = db.query(Result).limit(100).all()
        custom_columns = []
    
    if format == "excel":
        import pandas as pd
        from io import BytesIO
        
        data = []
        for result in results:
            row = {
                "Title": result.title,
                "URL": result.url,
                "Country": result.country,
                "Language": result.language,
                "Date": result.date,
                "Category": result.category,
                "Status": result.status,
                "Source": result.source,
                "Score": result.score
            }
            
            for column in custom_columns:
                column_value = db.query(ColumnValue).filter(
                    ColumnValue.column_id == column.id,
                    ColumnValue.result_id == result.id
                ).first()
                row[column.name] = column_value.value if column_value else "N/A"
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='RADAR Results', index=False)
        
        return {
            "message": "Excel export prepared",
            "format": "excel",
            "records": len(data),
            "download_url": f"/downloads/radar_export_{datetime.now().timestamp()}.xlsx"
        }
    
    elif format == "pdf":
        return {
            "message": "PDF export prepared",
            "format": "pdf", 
            "records": len(results),
            "download_url": f"/downloads/radar_export_{datetime.now().timestamp()}.pdf"
        }

@app.post("/ai-chat/filters", response_model=AIChatResponse)
async def ai_chat_filters(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI chat for generating filters based on user input"""
    
    try:
        filter_suggestions = await ai_service.generate_filter_suggestions(
            request.message, 
            request.context or {}
        )
        
        return AIChatResponse(
            response=f"He analizado tu solicitud y sugiero estos filtros:",
            filters=filter_suggestions,
            suggestions=[
                "Filtrar por país específico",
                "Limitar por rango de fechas", 
                "Filtrar por categoría",
                "Ordenar por relevancia"
            ]
        )
    except Exception as e:
        return AIChatResponse(
            response="Lo siento, no pude procesar tu solicitud. ¿Podrías ser más específico sobre qué filtros necesitas?",
            suggestions=[
                "Ejemplo: 'Mostrar solo resultados de España'",
                "Ejemplo: 'Filtrar por últimos 30 días'",
                "Ejemplo: 'Solo categoría tecnología'"
            ]
        )

@app.post("/ai-chat/columns", response_model=AIChatResponse)
async def ai_chat_columns(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI chat for generating custom columns based on user input"""
    
    try:
        column_suggestions = await ai_service.generate_column_suggestions(
            request.message,
            request.search_id
        )
        
        return AIChatResponse(
            response=f"Basándome en tu búsqueda, sugiero estas columnas personalizadas:",
            columns=column_suggestions,
            suggestions=[
                "Añadir columna de análisis de sentimiento",
                "Crear columna de categorización automática",
                "Generar columna de puntuación de relevancia",
                "Añadir columna de resumen ejecutivo"
            ]
        )
    except Exception as e:
        return AIChatResponse(
            response="¿Qué tipo de información adicional te gustaría extraer de los resultados?",
            suggestions=[
                "Ejemplo: 'Quiero saber el sentimiento de cada artículo'",
                "Ejemplo: 'Necesito el tamaño de las empresas mencionadas'",
                "Ejemplo: 'Quiero categorizar por industria'"
            ]
        )

@app.post("/support/chat", response_model=SupportChatResponse)
async def support_chat(
    request: SupportChatRequest,
    current_user: User = Depends(get_current_user)
):
    """AI-powered customer support chat"""
    
    try:
        support_response = await ai_service.generate_support_response(
            request.message,
            request.user_context or {}
        )
        
        return SupportChatResponse(
            response=support_response["response"],
            helpful_links=support_response.get("links", [
                {"title": "Guía de Búsqueda", "url": "/help/search-guide"},
                {"title": "Filtros Avanzados", "url": "/help/filters"},
                {"title": "Exportar Datos", "url": "/help/export"},
                {"title": "Automatización", "url": "/help/automation"}
            ])
        )
    except Exception as e:
        return SupportChatResponse(
            response="Hola, soy el asistente de RADAR. ¿En qué puedo ayudarte hoy? Puedo ayudarte con búsquedas, filtros, exportación de datos y automatización.",
            helpful_links=[
                {"title": "Preguntas Frecuentes", "url": "/help/faq"},
                {"title": "Contactar Soporte", "url": "/help/contact"},
                {"title": "Tutoriales", "url": "/help/tutorials"}
            ]
        )

@app.get("/export/excel/advanced")
async def export_excel_advanced(
    search_id: Optional[int] = Query(None, description="Search ID to export"),
    include_columns: bool = Query(True, description="Include custom columns"),
    include_metadata: bool = Query(False, description="Include result metadata"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advanced Excel export with Graph API preparation"""
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    if search_id:
        search_record = db.query(Search).filter(Search.id == search_id).first()
        if not search_record:
            raise HTTPException(status_code=404, detail="Search not found")
        
        results = db.query(Result).filter(Result.search_id == search_id).all()
        custom_columns = db.query(CustomColumn).filter(CustomColumn.search_id == search_id).all()
    else:
        results = db.query(Result).filter(Result.search.has(user_id=current_user.id)).limit(1000).all()
        custom_columns = []
    
    import pandas as pd
    from io import BytesIO
    
    data = []
    for result in results:
        row = {
            "ID": result.id,
            "Título": result.title,
            "URL": result.url,
            "Descripción": result.snippet,
            "País": result.country,
            "Idioma": result.language,
            "Fecha": result.date,
            "Categoría": result.category,
            "Estado": result.status,
            "Fuente": result.source,
            "Puntuación": result.score,
            "Fecha Creación": result.created_at.strftime("%Y-%m-%d %H:%M:%S") if result.created_at else ""
        }
        
        if include_columns:
            for column in custom_columns:
                column_value = db.query(ColumnValue).filter(
                    ColumnValue.column_id == column.id,
                    ColumnValue.result_id == result.id
                ).first()
                row[f"Columna: {column.name}"] = column_value.value if column_value else "N/A"
        
        if include_metadata and result.result_metadata:
            for key, value in result.result_metadata.items():
                if key not in ["title", "url", "snippet"]:  # Avoid duplicates
                    row[f"Meta: {key}"] = str(value)
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Resultados RADAR', index=False)
        
        summary_data = {
            "Métrica": ["Total Resultados", "Países Únicos", "Fuentes Únicas", "Categorías Únicas"],
            "Valor": [
                len(data),
                len(df["País"].unique()) if "País" in df.columns else 0,
                len(df["Fuente"].unique()) if "Fuente" in df.columns else 0,
                len(df["Categoría"].unique()) if "Categoría" in df.columns else 0
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumen', index=False)
        
        if custom_columns:
            columns_data = []
            for column in custom_columns:
                columns_data.append({
                    "Nombre": column.name,
                    "Descripción": column.description,
                    "Generada por IA": "Sí" if column.generated_by_ai else "No",
                    "Fecha Creación": column.created_at.strftime("%Y-%m-%d %H:%M:%S") if column.created_at else ""
                })
            columns_df = pd.DataFrame(columns_data)
            columns_df.to_excel(writer, sheet_name='Columnas Personalizadas', index=False)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"radar_export_advanced_{timestamp}.xlsx"
    
    return {
        "message": "Exportación Excel avanzada preparada",
        "format": "excel_advanced",
        "records": len(data),
        "sheets": ["Resultados RADAR", "Resumen"] + (["Columnas Personalizadas"] if custom_columns else []),
        "download_url": f"/downloads/{filename}",
        "graph_api_ready": True,
        "filename": filename
    }
