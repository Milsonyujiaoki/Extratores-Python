from typing import List, Dict, Any
from pydantic import BaseModel
import httpx, json, time

class PromptItem(BaseModel):
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]

def gerar_jsonl_prompts(pages: List[str], metadatas: List[Dict[str, Any]]) -> None:
    with open('batch_prompts.jsonl', 'w', encoding='utf-8') as f:
        for msg, meta in zip(pages, metadatas):
            item = PromptItem(messages=msg, metadata=meta)
            f.write(item.json() + "\n")

def enviar_job_batch_openai(jsonl_path: str, api_key: str) -> str:
    # Exemplo usando httpx, adaptar conforme OpenAI SDK Batch
    with open(jsonl_path, 'rb') as f:
        response = httpx.post(
            "https://api.openai.com/v1/batch",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": f},
            timeout=60
        )
    response.raise_for_status()
    job_id = response.json()['id']
    return job_id

def monitorar_status(job_id: str, api_key: str, intervalo: float = 15.0) -> str:
    while True:
        resp = httpx.get(
            f"https://api.openai.com/v1/batch/{job_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        status = resp.json()['status']
        if status == 'completed':
            return resp.json()['output_file_id']
        elif status in ('failed', 'cancelled'):
            raise RuntimeError(f"Job {job_id} falhou com status {status}")
        time.sleep(intervalo)
        intervalo = min(intervalo * 1.3, 60)

def baixar_saida(output_file_id: str, api_key: str, output_path: str):
    resp = httpx.get(
        f"https://api.openai.com/v1/files/{output_file_id}/content",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60
    )
    with open(output_path, 'wb') as f:
        f.write(resp.content)

# Pós-processamento, parsing etc.
