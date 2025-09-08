import openai
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

class AIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def interpret_search_query(self, query: str) -> Dict[str, Any]:
        """Interpret natural language search query and generate filters"""
        
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_query_interpretation(query)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI assistant that interprets search queries and generates appropriate filters for a web search system.

Given a search query, extract:
1. The main search terms
2. Relevant filters (country, language, category, status)
3. Suggested additional filters

Respond with JSON in this format:
{
    "search_terms": ["term1", "term2"],
    "filters": {
        "country": "country_code_or_null",
        "language": "language_or_null", 
        "category": "category_or_null",
        "status": "status_or_null"
    },
    "suggested_filters": ["filter1", "filter2"],
    "confidence": 0.8
}

Categories: Tecnología, Finanzas, Medio Ambiente, Salud, Ciencia, Educación, Startups, Aceleradoras
Countries: ES (España), USA, UK, DE (Alemania), FR (Francia), JP (Japón), CA (Canadá)
Languages: Español, Inglés, Alemán, Francés, Japonés
Status: Activo, Pendiente, Completado"""
                    },
                    {
                        "role": "user",
                        "content": f"Interpret this search query: '{query}'"
                    }
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"AI interpretation error: {e}")
            return self._fallback_query_interpretation(query)
    
    async def generate_column_data(self, column_name: str, column_description: str, search_results: List[Dict[str, Any]]) -> List[str]:
        """Generate data for a custom column based on search results"""
        
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_column_generation(column_name, len(search_results))
        
        try:
            context = []
            for result in search_results[:5]:  # Limit to first 5 results for context
                context.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", "")
                })
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an AI assistant that generates data for custom table columns based on search results.

Column Name: {column_name}
Column Description: {column_description}

For each search result provided, generate appropriate data for this column. 
Respond with a JSON array of strings, one for each result.

Example: ["value1", "value2", "value3"]

Keep values concise and relevant to the column purpose."""
                    },
                    {
                        "role": "user",
                        "content": f"Generate column data for these search results: {json.dumps(context)}"
                    }
                ],
                temperature=0.5
            )
            
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, list) else []
            
        except Exception as e:
            print(f"AI column generation error: {e}")
            return self._fallback_column_generation(column_name, len(search_results))
    
    async def suggest_columns(self, search_query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Suggest relevant columns based on search query and results"""
        
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_column_suggestions(search_query)
        
        try:
            sample_results = search_results[:3]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI assistant that suggests useful table columns based on search queries and results.

Suggest 3-5 relevant columns that would be useful for analyzing the search results.

Respond with JSON in this format:
[
    {
        "name": "Column Name",
        "description": "Brief description of what this column would contain"
    }
]

Focus on columns that would help users analyze, categorize, or extract insights from the search results."""
                    },
                    {
                        "role": "user",
                        "content": f"Search query: '{search_query}'\n\nSample results: {json.dumps(sample_results)}"
                    }
                ],
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, list) else []
            
        except Exception as e:
            print(f"AI column suggestion error: {e}")
            return self._fallback_column_suggestions(search_query)
    
    def _fallback_query_interpretation(self, query: str) -> Dict[str, Any]:
        """Fallback query interpretation when AI is not available"""
        
        query_lower = query.lower()
        filters = {}
        suggested_filters = []
        
        if "españa" in query_lower or "spain" in query_lower:
            filters["country"] = "ES"
        if "tecnología" in query_lower or "technology" in query_lower:
            filters["category"] = "Tecnología"
            suggested_filters.extend(["IA", "Software", "Hardware"])
        if "startup" in query_lower:
            filters["category"] = "Startups"
            suggested_filters.extend(["Financiación", "Aceleradora", "Inversión"])
        if "activo" in query_lower or "active" in query_lower:
            filters["status"] = "Activo"
        
        return {
            "search_terms": query.split(),
            "filters": filters,
            "suggested_filters": suggested_filters,
            "confidence": 0.6
        }
    
    def _fallback_column_generation(self, column_name: str, result_count: int) -> List[str]:
        """Fallback column data generation"""
        
        if "funding" in column_name.lower() or "financiación" in column_name.lower():
            return [f"€{i*100}K" for i in range(1, result_count + 1)]
        elif "stage" in column_name.lower() or "etapa" in column_name.lower():
            stages = ["Seed", "Series A", "Series B", "Growth"]
            return [stages[i % len(stages)] for i in range(result_count)]
        else:
            return [f"Data {i+1}" for i in range(result_count)]
    
    def _fallback_column_suggestions(self, search_query: str) -> List[Dict[str, str]]:
        """Fallback column suggestions"""
        
        query_lower = search_query.lower()
        
        if "startup" in query_lower:
            return [
                {"name": "Funding Stage", "description": "Current funding stage of the startup"},
                {"name": "Industry", "description": "Primary industry or sector"},
                {"name": "Founded Year", "description": "Year the company was founded"},
                {"name": "Team Size", "description": "Number of employees"}
            ]
        elif "university" in query_lower or "universidad" in query_lower:
            return [
                {"name": "Ranking", "description": "University ranking position"},
                {"name": "Research Focus", "description": "Main research areas"},
                {"name": "Student Count", "description": "Number of students"}
            ]
        else:
            return [
                {"name": "Relevance Score", "description": "Relevance to search query"},
                {"name": "Last Updated", "description": "When the information was last updated"},
                {"name": "Type", "description": "Type or category of result"}
            ]

    async def generate_filter_suggestions(self, user_message: str, context: dict = None) -> dict:
        """Generate filter suggestions based on user message for AI minichat"""
        
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_filter_suggestions(user_message)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI assistant that helps users create search filters based on their natural language requests.

When a user describes what they want to filter, suggest appropriate filter criteria.

Respond with JSON in this format:
{
    "message": "I understand you want to filter for [description]. Here are some suggested filters:",
    "suggested_filters": [
        {
            "type": "country",
            "value": "ES",
            "label": "España"
        },
        {
            "type": "category", 
            "value": "Tecnología",
            "label": "Sector Tecnología"
        }
    ],
    "explanation": "These filters will help you find..."
}

Available filter types:
- country: ES, USA, UK, DE, FR, JP, CA
- category: Tecnología, Finanzas, Medio Ambiente, Salud, Ciencia, Educación, Startups, Aceleradoras
- language: Español, Inglés, Alemán, Francés, Japonés
- status: Activo, Pendiente, Completado
- date_range: recent, last_week, last_month, last_year
- size: small, medium, large, enterprise"""
                    },
                    {
                        "role": "user",
                        "content": f"Help me create filters for: {user_message}"
                    }
                ],
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"AI filter suggestion error: {e}")
            return self._fallback_filter_suggestions(user_message)

    async def generate_column_suggestions(self, user_message: str, context: dict = None) -> dict:
        """Generate column suggestions based on user message for AI minichat"""
        
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_column_suggestions_chat(user_message)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an AI assistant that helps users create custom table columns based on their requests.

When a user describes what column data they want, suggest appropriate column configurations.

Respond with JSON in this format:
{
    "message": "I can help you create columns for [description]. Here are some suggestions:",
    "suggested_columns": [
        {
            "name": "Column Name",
            "description": "What this column will contain",
            "type": "text|number|date|url|email"
        }
    ],
    "explanation": "These columns will help you analyze..."
}

Focus on columns that would be useful for data analysis, categorization, or extracting insights."""
                    },
                    {
                        "role": "user",
                        "content": f"Help me create columns for: {user_message}"
                    }
                ],
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"AI column suggestion error: {e}")
            return self._fallback_column_suggestions_chat(user_message)

    async def generate_support_response(self, user_message: str, conversation_history: List[dict] = None) -> dict:
        """Generate customer support response for help chat"""
        
        if not os.getenv("OPENAI_API_KEY"):
            return self._fallback_support_response(user_message)
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful customer support AI for RADAR, a meta-search platform for businesses.

RADAR helps companies:
- Search across multiple sources (Google, Bing, NewsAPI, etc.)
- Use natural language queries
- Apply dynamic filters to results
- Create custom columns with AI assistance
- Automate searches and get alerts
- Export results to Excel/PDF

You should:
- Be helpful and friendly
- Provide specific guidance about RADAR features
- Suggest solutions to user problems
- Ask clarifying questions when needed
- Keep responses concise but informative

Respond with JSON in this format:
{
    "message": "Your helpful response here",
    "suggested_actions": ["action1", "action2"],
    "helpful_links": [
        {
            "title": "Link Title",
            "description": "What this link helps with"
        }
    ]
}"""
                }
            ]
            
            if conversation_history:
                messages.extend(conversation_history[-5:])  # Last 5 messages for context
            
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.8
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"AI support response error: {e}")
            return self._fallback_support_response(user_message)

    def _fallback_filter_suggestions(self, user_message: str) -> dict:
        """Fallback filter suggestions when AI is not available"""
        
        message_lower = user_message.lower()
        suggested_filters = []
        
        if "españa" in message_lower or "spain" in message_lower:
            suggested_filters.append({
                "type": "country",
                "value": "ES", 
                "label": "España"
            })
        
        if "tecnología" in message_lower or "technology" in message_lower:
            suggested_filters.append({
                "type": "category",
                "value": "Tecnología",
                "label": "Sector Tecnología"
            })
        
        if "startup" in message_lower:
            suggested_filters.append({
                "type": "category",
                "value": "Startups",
                "label": "Startups"
            })
        
        return {
            "message": f"Basándome en tu solicitud '{user_message}', aquí tienes algunas sugerencias de filtros:",
            "suggested_filters": suggested_filters if suggested_filters else [
                {
                    "type": "status",
                    "value": "Activo",
                    "label": "Estado Activo"
                }
            ],
            "explanation": "Estos filtros te ayudarán a refinar tu búsqueda."
        }

    def _fallback_column_suggestions_chat(self, user_message: str) -> dict:
        """Fallback column suggestions for chat when AI is not available"""
        
        message_lower = user_message.lower()
        suggested_columns = []
        
        if "funding" in message_lower or "financiación" in message_lower:
            suggested_columns.extend([
                {
                    "name": "Funding Stage",
                    "description": "Etapa de financiación actual",
                    "type": "text"
                },
                {
                    "name": "Investment Amount",
                    "description": "Cantidad de inversión recibida",
                    "type": "number"
                }
            ])
        elif "contact" in message_lower or "contacto" in message_lower:
            suggested_columns.extend([
                {
                    "name": "Email",
                    "description": "Dirección de correo electrónico",
                    "type": "email"
                },
                {
                    "name": "Phone",
                    "description": "Número de teléfono",
                    "type": "text"
                }
            ])
        else:
            suggested_columns.extend([
                {
                    "name": "Category",
                    "description": "Categoría o tipo de resultado",
                    "type": "text"
                },
                {
                    "name": "Relevance",
                    "description": "Puntuación de relevancia",
                    "type": "number"
                }
            ])
        
        return {
            "message": f"Para tu solicitud '{user_message}', te sugiero estas columnas:",
            "suggested_columns": suggested_columns,
            "explanation": "Estas columnas te ayudarán a organizar mejor tus datos."
        }

    def _fallback_support_response(self, user_message: str) -> dict:
        """Fallback support response when AI is not available"""
        
        message_lower = user_message.lower()
        
        if "search" in message_lower or "búsqueda" in message_lower:
            return {
                "message": "Para realizar búsquedas en RADAR, simplemente escribe tu consulta en lenguaje natural en la barra de búsqueda. El sistema interpretará automáticamente tu consulta y buscará en múltiples fuentes.",
                "suggested_actions": [
                    "Prueba con consultas específicas como 'startups de tecnología en España'",
                    "Usa el botón 'Refinar búsqueda' para añadir filtros"
                ],
                "helpful_links": [
                    {
                        "title": "Guía de búsqueda",
                        "description": "Aprende a hacer búsquedas efectivas"
                    }
                ]
            }
        elif "filter" in message_lower or "filtro" in message_lower:
            return {
                "message": "Los filtros te permiten refinar tus resultados de búsqueda. Puedes aplicar filtros por país, categoría, idioma, estado y más.",
                "suggested_actions": [
                    "Haz clic en 'Refinar búsqueda' para ver opciones de filtros",
                    "Guarda tus filtros favoritos en tu perfil"
                ],
                "helpful_links": [
                    {
                        "title": "Guía de filtros",
                        "description": "Cómo usar filtros efectivamente"
                    }
                ]
            }
        elif "export" in message_lower or "exportar" in message_lower:
            return {
                "message": "Puedes exportar tus resultados a Excel o PDF. Ve a la sección de exportación y selecciona el formato que prefieras.",
                "suggested_actions": [
                    "Usa el botón 'Exportar' en la tabla de resultados",
                    "Revisa tus exportaciones en la pestaña 'PDFs Exportados' de tu perfil"
                ],
                "helpful_links": [
                    {
                        "title": "Guía de exportación",
                        "description": "Cómo exportar y gestionar tus reportes"
                    }
                ]
            }
        else:
            return {
                "message": "¡Hola! Soy el asistente de RADAR. Estoy aquí para ayudarte con cualquier pregunta sobre la plataforma. ¿En qué puedo asistirte hoy?",
                "suggested_actions": [
                    "Pregúntame sobre búsquedas, filtros, columnas o exportación",
                    "Consulta nuestros tutoriales y guías"
                ],
                "helpful_links": [
                    {
                        "title": "Documentación completa",
                        "description": "Guía completa de RADAR"
                    }
                ]
            }
