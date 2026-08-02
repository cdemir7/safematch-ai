"""
Gemini yanıtları için paylaşılan JSON parse + token sayım yardımcıları.

Rules
-----
- Business logic yok — sadece weighting.py ve explain.py arasında paylaşılan
  savunmacı (defensive) parse/gözlem yardımcıları.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from json_repair import loads as repair_loads

logger = logging.getLogger(__name__)


def parse_json_loose(raw_text: str) -> Any | None:
    """
    Gemini yanıtını JSON olarak parse eder.

    Önce katı `json.loads` dener. Bu başarısız olursa (eksik virgül,
    kapanmamış parantez, `max_output_tokens` yüzünden yarıda kesilmiş
    string gibi LLM çıktılarında sık görülen bozukluklar) `json-repair`
    kütüphanesiyle onarmayı dener — bu kütüphane tam bu senaryo için
    yazılmıştır ve elle yazılacak regex'ten çok daha güvenilirdir (string
    içi kaçışlı tırnak, unicode gibi köşe durumları da doğru ele alır).

    Returns
    -------
    Parse edilmiş değer (dict/list/...) veya hiçbir şekilde kurtarılamazsa
    `None`. `json-repair` tamamen anlamsız girdi için boş string döner —
    bu da `None` olarak ele alınır.
    """
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    try:
        repaired = repair_loads(raw_text)
    except Exception as exc:
        logger.warning("json-repair da başarısız oldu: %s | raw: %s", exc, raw_text[:200])
        return None

    if repaired == "" or repaired is None:
        logger.warning("json-repair kurtaramadı (boş sonuç) | raw: %s", raw_text[:200])
        return None

    logger.info("Katı JSON parse başarısız oldu, json-repair ile kurtarıldı.")
    return repaired


async def log_token_usage(client: Any, model: str, contents: str, *, label: str) -> None:
    """
    Bir isteği göndermeden ÖNCE Gemini'nin kendi tokenizer'ıyla gerçek prompt
    token sayısını loglar (tahmin değil — `client.aio.models.count_tokens`
    gerçek API sonucudur). Sadece gözlemlenebilirlik içindir; hata durumunda
    isteği engellemez, sadece uyarı loglar.
    """
    try:
        result = await client.aio.models.count_tokens(model=model, contents=contents)
        logger.info("[%s] prompt token sayısı (gerçek, Gemini): %d", label, result.total_tokens)
    except Exception as exc:
        logger.warning("[%s] count_tokens başarısız: %s", label, exc)
