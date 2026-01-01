from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Review(BaseModel):
    text: str
    stars: int | None = None
    product_name: str | None = None


@app.get("/")
def root():
    return {"status": "ok", "message": "wb-reviews-agent работает"}


@app.post("/answer-review")
def answer_review(review: Review):
    """
    Пока просто возвращает заглушку.
    Потом сюда прикрутим нормальный мозг (OpenRouter и логику).
    """
    base_answer = "Спасибо за отзыв!"
    if review.stars is not None and review.stars <= 3:
        base_answer += " Нам очень жаль, что впечатление получилось неидеальным. Напишите нам в чат, поможем решить вопрос."
    else:
        base_answer += " Рады, что вам понравилось!"

    return {
        "should_answer": True,
        "escalate_to_human": False,
        "answer_text": base_answer,
    }
