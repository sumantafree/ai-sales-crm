"""
AI Service — powered by Google Gemini (primary)
Falls back to OpenAI or keyword scoring if unavailable.
"""
import json
import re
import httpx
from typing import Optional
from core.config import settings
from database import SessionLocal
from models.lead import Lead, LeadTemperature, LeadIntent


# ── Prompts ───────────────────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are an expert sales AI assistant. Analyze this lead and return a JSON response.

Lead Information:
- Name: {name}
- Source: {source}
- Message: "{message}"
- Phone: {phone}
- Email: {email}

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
  "score": <number 0-100>,
  "temperature": "<hot|warm|cold>",
  "intent": "<buying|inquiry|casual|unknown>",
  "summary": "<2-3 sentence analysis>",
  "suggested_action": "<specific next action>",
  "reply": "<short, friendly, persuasive WhatsApp-style reply under 60 words>"
}}

Scoring guide:
- 80-100: Ready to buy, urgent signals, high engagement
- 50-79: Interested, needs nurturing
- 0-49: Cold, just browsing
Temperature: hot=80+, warm=50-79, cold=<50"""

CONTEXTUAL_REPLY_PROMPT = """You are a helpful sales assistant. Continue this conversation naturally.

Lead: {lead_name}
Previous messages:
{history}

Latest message: "{last_message}"

Write a short (max 60 words), friendly, persuasive reply that moves toward conversion.
Return ONLY the reply text, no quotes, no explanation."""


# ── Main analysis function ────────────────────────────────────────────────────

async def analyze_lead(lead_id: str):
    """Background task: run AI analysis on a lead and update the DB."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return

        prompt = ANALYSIS_PROMPT.format(
            name=lead.name or "Unknown",
            source=lead.source.value if lead.source else "unknown",
            message=lead.message or "No message provided",
            phone=lead.phone or "N/A",
            email=lead.email or "N/A",
        )

        result = await _call_ai(prompt)
        if not result:
            result = _keyword_score(lead)  # fallback

        lead.score = float(result.get("score", 0))
        lead.temperature = _parse_temp(result.get("temperature", "cold"))
        lead.intent = _parse_intent(result.get("intent", "unknown"))
        lead.ai_summary = result.get("summary", "")
        lead.ai_suggested_action = result.get("suggested_action", "")
        lead.ai_generated_reply = result.get("reply", "")

        db.commit()
        print(f"[AI] Lead {lead_id} analyzed — score: {lead.score}, temp: {lead.temperature}")
    except Exception as e:
        print(f"[AI] Error analyzing lead {lead_id}: {e}")
    finally:
        db.close()


async def generate_contextual_reply(lead: Lead, history: list) -> str:
    """Generate a context-aware reply continuing an existing conversation."""
    history_text = "\n".join([
        f"{'Lead' if m.role.value == 'user' else 'Agent'}: {m.content}"
        for m in history[-6:]
    ])
    last_message = history[-1].content if history else lead.message or ""

    prompt = CONTEXTUAL_REPLY_PROMPT.format(
        lead_name=lead.name,
        history=history_text,
        last_message=last_message,
    )

    result = await _call_ai_raw(prompt)
    return result or f"Hi {lead.name}! Thank you for reaching out. How can I help you today?"


# ── AI Router ─────────────────────────────────────────────────────────────────

async def _call_ai(prompt: str) -> Optional[dict]:
    raw = await _call_ai_raw(prompt)
    if not raw:
        return None
    return _extract_json(raw)


async def _call_ai_raw(prompt: str) -> Optional[str]:
    """Route to the configured AI provider."""
    provider = settings.AI_PROVIDER.lower()

    if provider == "gemini" and settings.GEMINI_API_KEY:
        return await _call_gemini(prompt)
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return await _call_openai(prompt)
    elif provider == "ollama":
        return await _call_ollama(prompt)
    else:
        # Auto-detect: try Gemini → OpenAI → Ollama → fallback
        if settings.GEMINI_API_KEY:
            return await _call_gemini(prompt)
        elif settings.OPENAI_API_KEY:
            return await _call_openai(prompt)
        else:
            return await _call_ollama(prompt)


# ── Gemini ────────────────────────────────────────────────────────────────────

async def _call_gemini(prompt: str) -> Optional[str]:
    """Call Google Gemini API (gemini-1.5-flash — free tier available)."""
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
            f"?key={settings.GEMINI_API_KEY}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 512,
                "responseMimeType": "text/plain",
            },
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract text from Gemini response
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "")
        return None
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None


# ── OpenAI (fallback) ─────────────────────────────────────────────────────────

async def _call_openai(prompt: str) -> Optional[str]:
    """Call OpenAI API."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[OpenAI] Error: {e}")
        return None


# ── Ollama (local fallback) ───────────────────────────────────────────────────

async def _call_ollama(prompt: str) -> Optional[str]:
    """Call local Ollama API."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 512},
                },
            )
            response.raise_for_status()
            return response.json().get("response", "")
    except Exception as e:
        print(f"[Ollama] Error: {e}")
        return None


# ── JSON extractor ────────────────────────────────────────────────────────────

def _extract_json(text: str) -> Optional[dict]:
    """Parse JSON from AI response — handles markdown code fences."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


# ── Keyword fallback (no AI needed) ──────────────────────────────────────────

def _keyword_score(lead: Lead) -> dict:
    """Score leads using keywords when AI is unavailable."""
    message = (lead.message or "").lower()
    score = 20

    hot_keywords  = ["buy", "purchase", "urgent", "asap", "now", "today",
                     "price", "cost", "deal", "interested", "need", "want"]
    warm_keywords = ["info", "inquiry", "question", "learn", "know",
                     "details", "how much", "tell me", "what is"]

    for kw in hot_keywords:
        if kw in message:
            score += 10
    for kw in warm_keywords:
        if kw in message:
            score += 5

    source_bonus = {"whatsapp": 20, "facebook": 10, "website": 5, "email": 3, "manual": 0}
    score += source_bonus.get(lead.source.value if lead.source else "", 0)
    score = min(score, 100)

    temperature = "hot" if score >= 70 else ("warm" if score >= 40 else "cold")
    intent      = "buying" if score >= 70 else ("inquiry" if score >= 40 else "casual")

    return {
        "score": score,
        "temperature": temperature,
        "intent": intent,
        "summary": f"Lead from {lead.source.value if lead.source else 'unknown'} showing {temperature} interest level.",
        "suggested_action": "Call immediately" if temperature == "hot" else "Send follow-up email",
        "reply": f"Hi {lead.name}! Thanks for reaching out. I'd love to help you. What are you looking for?",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_temp(value: str) -> LeadTemperature:
    mapping = {"hot": LeadTemperature.HOT, "warm": LeadTemperature.WARM, "cold": LeadTemperature.COLD}
    return mapping.get(str(value).lower(), LeadTemperature.COLD)


def _parse_intent(value: str) -> LeadIntent:
    mapping = {
        "buying": LeadIntent.BUYING, "inquiry": LeadIntent.INQUIRY,
        "casual": LeadIntent.CASUAL,  "unknown": LeadIntent.UNKNOWN,
    }
    return mapping.get(str(value).lower(), LeadIntent.UNKNOWN)
