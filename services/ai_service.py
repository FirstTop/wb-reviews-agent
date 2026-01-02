"""Сервис для работы с OpenRouter API (генерация ответов на отзывы)"""
import httpx
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Сервис для генерации ответов на отзывы через OpenRouter"""
    
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.api_url = settings.OPENROUTER_API_URL
        self.model = settings.OPENROUTER_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",  # Опционально
            "X-Title": "WB Reviews Agent"  # Опционально
        }
    
    def _build_prompt(self, review_text: str, rating: int, pros: Optional[str] = None, 
                     cons: Optional[str] = None, product_info: Optional[str] = None) -> str:
        """
        Построение промпта для генерации ответа
        
        Args:
            review_text: Текст отзыва
            rating: Рейтинг отзыва (1-5)
            pros: Плюсы товара (если есть)
            cons: Минусы товара (если есть)
            product_info: Информация о товаре (опционально)
        
        Returns:
            Промпт для ИИ
        """
        prompt = f"""Ты - профессиональный менеджер по работе с клиентами интернет-магазина Wildberries.

Твоя задача - написать вежливый, профессиональный и полезный ответ на отзыв покупателя.

Рейтинг отзыва: {rating}/5

"""
        if pros:
            prompt += f"Плюсы, которые отметил покупатель:\n{pros}\n\n"
        if cons:
            prompt += f"Минусы, которые отметил покупатель:\n{cons}\n\n"
        
        prompt += f"Текст отзыва:\n{review_text}\n\n"
        
        if product_info:
            prompt += f"Информация о товаре:\n{product_info}\n\n"
        
        prompt += """Требования к ответу:
1. Будь вежливым и профессиональным
2. Благодари за отзыв
3. Если есть проблемы (низкий рейтинг) - извинись и предложи решение
4. Если отзыв положительный - поблагодари и пригласи оставить еще отзывы
5. Ответ должен быть кратким (2-4 предложения)
6. Используй деловой, но дружелюбный тон
7. Не используй эмодзи в ответе

Напиши ответ на отзыв:"""
        
        return prompt
    
    async def generate_response(self, review_text: str, rating: int, 
                               pros: Optional[str] = None, 
                               cons: Optional[str] = None,
                               product_info: Optional[str] = None) -> Optional[str]:
        """
        Генерация ответа на отзыв через OpenRouter API
        
        Args:
            review_text: Текст отзыва
            rating: Рейтинг отзыва (1-5)
            pros: Плюсы товара (опционально)
            cons: Минусы товара (опционально)
            product_info: Информация о товаре (опционально)
        
        Returns:
            Сгенерированный ответ или None в случае ошибки
        """
        try:
            prompt = self._build_prompt(review_text, rating, pros, cons, product_info)
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты профессиональный менеджер по работе с клиентами. Ты пишешь вежливые и полезные ответы на отзывы покупателей."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 300
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Извлечение сгенерированного текста
                if "choices" in data and len(data["choices"]) > 0:
                    generated_text = data["choices"][0]["message"]["content"].strip()
                    logger.info(f"Ответ успешно сгенерирован для отзыва с рейтингом {rating}")
                    return generated_text
                else:
                    logger.error(f"Неожиданная структура ответа OpenRouter: {data}")
                    return None
                    
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при генерации ответа через OpenRouter: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при генерации ответа: {e}")
            return None

