import anthropic
import os
import json
import re

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def call_claude(prompt: str, max_tokens: int = 500) -> str:
    """Base function — all AI features use this"""
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text

def parse_ai_json(response: str) -> dict:
    """Safely parse JSON from AI response"""
    clean = re.sub(r'```json|```', '', response).strip()
    return json.loads(clean)

def categorize_expense(description: str) -> str:
    """AI categorizes expense automatically"""
    from app.services.redis_client import redis_client
    cache_key = f"category:{description.lower().strip()}"
    cached = redis_client.get(cache_key)
    if cached:
        return cached  

    prompt = f"""
You are an expense categorizer.
Given this expense description: "{description}"

Return ONLY one word from this list:
Food, Transport, Shopping, Entertainment, Healthcare, Utilities, Education, Other

Rules:
- Food = restaurants, groceries, delivery apps like Swiggy/Zomato
- Transport = Uber, Ola, fuel, train, bus, flight
- Shopping = clothes, electronics, Amazon purchases
- Entertainment = movies, games, subscriptions like Netflix
- Healthcare = medicine, doctor, hospital
- Utilities = electricity, water, internet, phone bills
- Education = books, courses, tuition fees
- Other = anything that doesn't fit above

Return ONLY the category word. Nothing else.
"""

    category = call_claude(prompt, max_tokens=10).strip()
    valid = ["Food", "Transport", "Shopping", "Entertainment",
             "Healthcare", "Utilities", "Education", "Other"]
    if category not in valid:
        category = "Other"
    redis_client.setex(cache_key, 2592000, category)

    return category

def get_expense_insights(user_message: str, expense_data: dict) -> str:
    """RAG chatbot — answers questions about user's actual expenses"""

    prompt = f"""
You are a helpful personal finance assistant.
You have access to the user's expense data below.
Answer their question conversationally in 2-3 lines maximum.
Use Indian Rupee (₹) for amounts.

User's expense data:
{json.dumps(expense_data, indent=2)}

User question: {user_message}

Answer directly and helpfully. If data is insufficient, say so honestly.
"""

    return call_claude(prompt, max_tokens=200)

def scan_receipt(image_base64: str) -> dict:
    """Extract expense details from receipt image"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": """Extract from this receipt:
Return ONLY valid JSON, nothing else:
{"merchant": "store name", "amount": 0.0, "date": "YYYY-MM-DD", "category": "Food"}

If you cannot find a field, use null.
Category must be one of: Food, Transport, Shopping, Entertainment, Healthcare, Utilities, Education, Other"""
                }
            ]
        }]
    )

    try:
        return parse_ai_json(message.content[0].text)
    except:
        return {"merchant": None, "amount": None, "date": None, "category": "Other"}