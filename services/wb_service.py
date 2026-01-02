"""Сервис для работы с Wildberries API"""
import httpx
from typing import List, Dict, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class WBService:
    """Сервис для взаимодействия с Wildberries API"""
    
    def __init__(self):
        self.api_key = settings.WB_API_KEY
        self.base_url = settings.WB_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_reviews(self, date_from: Optional[str] = None) -> List[Dict]:
        """
        Получение отзывов из Wildberries API
        
        Args:
            date_from: Дата начала периода в формате ISO (опционально)
        
        Returns:
            Список отзывов
        """
        try:
            url = f"{self.base_url}/api/v1/feedbacks"
            params = {}
            if date_from:
                params["dateFrom"] = date_from
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Обработка структуры ответа WB API
                # Адаптируйте под реальную структуру API
                if isinstance(data, dict) and "data" in data:
                    return data["data"]
                elif isinstance(data, list):
                    return data
                else:
                    logger.warning(f"Неожиданная структура ответа WB API: {data}")
                    return []
                    
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при получении отзывов из WB API: {e}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении отзывов: {e}")
            raise
    
    async def post_response(self, review_id: str, response_text: str) -> bool:
        """
        Публикация ответа на отзыв
        
        Args:
            review_id: ID отзыва в системе WB
            response_text: Текст ответа
        
        Returns:
            True если успешно, False в противном случае
        """
        try:
            url = f"{self.base_url}/api/v1/feedbacks/{review_id}/answer"
            payload = {
                "text": response_text
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                logger.info(f"Ответ успешно опубликован на отзыв {review_id}")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при публикации ответа на отзыв {review_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при публикации ответа: {e}")
            return False
    
    def parse_review(self, wb_review_data: Dict) -> Dict:
        """
        Парсинг данных отзыва из формата WB API в наш формат
        
        Args:
            wb_review_data: Данные отзыва из WB API
        
        Returns:
            Словарь с распарсенными данными
        """
        # Адаптируйте под реальную структуру данных WB API
        return {
            "wb_review_id": str(wb_review_data.get("id", "")),
            "product_id": str(wb_review_data.get("productId", "")),
            "nm_id": str(wb_review_data.get("nmId", "")),
            "supplier_article": wb_review_data.get("supplierArticle", ""),
            "rating": wb_review_data.get("rating", 0),
            "text": wb_review_data.get("text", ""),
            "pros": wb_review_data.get("pros", ""),
            "cons": wb_review_data.get("cons", ""),
            "author": wb_review_data.get("author", ""),
            "date": wb_review_data.get("date", ""),
        }

