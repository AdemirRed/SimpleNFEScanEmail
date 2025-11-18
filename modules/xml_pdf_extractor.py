import os
import re
import json
from typing import List, Dict, Tuple

# PDF text extraction (optional dependencies)

def _extract_text_pdfminer(path: str) -> str:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
        text = extract_text(path) or ""
        # Remove caracteres de controle e limpa
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
        return text.strip()
    except Exception as e:
        print(f"Erro pdfminer: {e}")
        return ""


def _extract_text_pypdf(path: str) -> str:
    try:
        import PyPDF2  # type: ignore
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            texts = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    texts.append(page_text)
            combined = "\n".join(texts)
            # Remove caracteres de controle e limpa
            combined = ''.join(char for char in combined if char.isprintable() or char in '\n\r\t')
            return combined.strip()
    except Exception as e:
        print(f"Erro PyPDF2: {e}")
        return ""


def extract_text_from_pdf(path: str) -> str:
    """Extrai texto de PDF com fallback entre múltiplas bibliotecas"""
    print(f"[PDF] Tentando extrair de: {os.path.basename(path)}")
    
    # Tenta pdfminer primeiro (melhor qualidade)
    text = _extract_text_pdfminer(path)
    if text and len(text.strip()) > 50:
        print(f"[PDF] Extraído via pdfminer: {len(text)} caracteres")
        return text
    
    # Fallback para PyPDF2
    text = _extract_text_pypdf(path)
    if text and len(text.strip()) > 50:
        print(f"[PDF] Extraído via PyPDF2: {len(text)} caracteres")
        return text
    
    # Se falhou, pode ser PDF escaneado (imagem)
    print(f"[PDF] AVISO: PDF pode ser escaneado (imagem) - OCR não implementado")
    print(f"[PDF] Sugestão: Use ferramenta de OCR ou converta para PDF pesquisável")
    
    return text


# XML NFe extraction

def extract_items_from_xml(path: str) -> List[Dict]:
    """Extrai itens de uma NFe XML (NFe/NF-e padrão SEFAZ).
    Campos: descricao (xProd), quantidade (qCom), valor_unit (vUnCom), valor_total (vProd)
    """
    import xml.etree.ElementTree as ET

    ns_clean = {
        'nfeProc': 'http://www.portalfiscal.inf.br/nfe',
        'NFe': 'http://www.portalfiscal.inf.br/nfe'
    }

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return []

    # Tenta encontrar det/prod em caminhos comuns
    det_nodes = []
    # nfeProc/NFe/infNFe/det
    det_nodes = root.findall('.//{http://www.portalfiscal.inf.br/nfe}det')

    items: List[Dict] = []
    for det in det_nodes:
        prod = det.find('{http://www.portalfiscal.inf.br/nfe}prod')
        if prod is None:
            continue
        def _get(tag: str) -> str:
            el = prod.find(f'{{http://www.portalfiscal.inf.br/nfe}}{tag}')
            return (el.text or '').strip() if el is not None else ''
        xProd = _get('xProd')
        qCom = _get('qCom')
        vUnCom = _get('vUnCom')
        vProd = _get('vProd')
        def _to_float(s: str) -> float:
            s = s.replace('.', '').replace(',', '.') if s.count(',') == 1 and s.count('.') > 1 else s
            try:
                return float(s)
            except Exception:
                try:
                    return float(s.replace(',', '.'))
                except Exception:
                    return 0.0
        items.append({
            'descricao': xProd,
            'quantidade': _to_float(qCom or '0'),
            'valor_unit': _to_float(vUnCom or '0'),
            'valor_total': _to_float(vProd or '0'),
        })
    return items


# LLM extraction for PDF

def extract_items_from_pdf_via_llm(pdf_text: str, lm_url: str, model: str) -> List[Dict]:
    """Envia o texto do PDF ao LM Studio e pede os itens em JSON.
    Retorna lista de itens com chaves: descricao, quantidade, valor_unit, valor_total
    """
    import requests  # type: ignore

    print(f"[DEBUG] Iniciando extração via LM Studio")
    print(f"[DEBUG] URL: {lm_url}, Modelo: {model}")
    print(f"[DEBUG] Tamanho do texto PDF: {len(pdf_text)} caracteres")

    if not pdf_text or len(pdf_text.strip()) < 50:
        print(f"[DEBUG] Texto muito curto, retornando vazio")
        raise Exception(f"Texto do PDF muito curto ({len(pdf_text)} caracteres)")

    # Testa conexão primeiro
    try:
        print(f"[DEBUG] Testando conexão com LM Studio...")
        test_response = requests.get(f"{lm_url}/v1/models", timeout=5)
        print(f"[DEBUG] LM Studio respondeu: {test_response.status_code}")
        if test_response.status_code == 200:
            models = test_response.json()
            print(f"[DEBUG] Modelos disponíveis: {models}")
    except requests.exceptions.ConnectionError:
        raise Exception(f"LM Studio NÃO está rodando em {lm_url}. Inicie o servidor Local Server na porta 1234.")
    except requests.exceptions.Timeout:
        raise Exception(f"LM Studio não respondeu em {lm_url}. Servidor pode estar travado.")
    except Exception as e:
        print(f"[DEBUG] Aviso ao testar conexão: {e}")

    system = (
        "Você é um assistente especializado em extração de dados de DANFE (nota fiscal eletrônica). "
        "Extraia APENAS os itens/produtos da nota fiscal. "
        "Retorne SOMENTE um objeto JSON válido no formato:\n"
        '{"items": [{"descricao": "string", "quantidade": number, "valor_unit": number, "valor_total": number}]}\n'
        "Use ponto (.) como separador decimal. NÃO adicione comentários, explicações ou texto extra. "
        "Responda APENAS com o JSON."
    )

    user = (
        "Extraia os itens desta nota fiscal e retorne o JSON:\n\n"
        + pdf_text[:50000]
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0,
        "max_tokens": 4096,  # Aumentado para 4096
        "stream": False
    }

    try:
        print(f"[DEBUG] Enviando requisição para {lm_url}/v1/chat/completions")
        print(f"[DEBUG] Aguardando resposta (SEM TIMEOUT - aguarde o modelo terminar)...")
        r = requests.post(f"{lm_url}/v1/chat/completions", json=payload, timeout=None)
        print(f"[DEBUG] Status code: {r.status_code}")
        
        if r.status_code != 200:
            print(f"[DEBUG] Erro HTTP {r.status_code}: {r.text[:500]}")
            raise Exception(f"LM Studio retornou erro {r.status_code}: {r.text[:200]}")
            
        r.raise_for_status()
        data = r.json()
        print(f"[DEBUG] Resposta recebida do LM Studio")
        
        # Tenta extrair content ou reasoning
        msg = data.get('choices', [{}])[0].get('message', {})
        content = msg.get('content', '').strip()
        reasoning = msg.get('reasoning', '').strip()
        
        print(f"[DEBUG] Content ({len(content)} caracteres): {content[:500]}...")
        print(f"[DEBUG] Reasoning ({len(reasoning)} caracteres): {reasoning[:500]}...")
        
        # Prefere content, mas usa reasoning se content vazio
        text_to_parse = content if content else reasoning
        
        if not text_to_parse:
            raise Exception("LM Studio retornou resposta vazia (sem content nem reasoning)")
        
        print(f"[DEBUG] Usando {'content' if content else 'reasoning'} para parsing")
            
        print(f"[DEBUG] Usando {'content' if content else 'reasoning'} para parsing")
            
        # tenta parsear JSON
        try:
            parsed = json.loads(text_to_parse)
            print(f"[DEBUG] JSON parseado com sucesso")
        except Exception as e:
            print(f"[DEBUG] Falha ao parsear JSON direto: {e}")
            # tenta extrair bloco JSON do reasoning/content
            m = re.search(r'\{[\s\S]*?"items"[\s\S]*?\[[\s\S]*?\][\s\S]*?\}', text_to_parse)
            if not m:
                print(f"[DEBUG] Texto completo para análise: {text_to_parse[:2000]}")
                raise Exception(f"Não foi possível extrair JSON da resposta. Texto: {text_to_parse[:300]}...")
            try:
                parsed = json.loads(m.group(0))
                print(f"[DEBUG] JSON extraído e parseado com sucesso")
            except Exception as e2:
                raise Exception(f"Falha ao parsear JSON extraído: {e2}. JSON: {m.group(0)[:300]}")
                
        items = parsed.get('items', [])
        print(f"[DEBUG] Itens extraídos: {len(items)}")
        
        if not items:
            raise Exception(f"LM Studio retornou 0 itens. Resposta: {str(parsed)[:500]}")
            
        # normaliza tipos numéricos
        norm_items: List[Dict] = []
        for it in items:
            def _f(x):
                try:
                    return float(str(x).replace(',', '.'))
                except Exception:
                    return 0.0
            norm_items.append({
                'descricao': str(it.get('descricao', '')).strip(),
                'quantidade': _f(it.get('quantidade', 0)),
                'valor_unit': _f(it.get('valor_unit', 0)),
                'valor_total': _f(it.get('valor_total', 0)),
            })
        print(f"[DEBUG] {len(norm_items)} itens normalizados com sucesso")
        return norm_items
    except requests.exceptions.ConnectionError as e:
        print(f"[DEBUG] Erro de conexão: {e}")
        raise Exception("LM Studio não está rodando ou não está acessível em " + lm_url)
    except requests.exceptions.Timeout:
        print(f"[DEBUG] Timeout (não deveria acontecer com timeout=None)")
        raise Exception("Timeout ao aguardar resposta do LM Studio. Isso é inesperado.")
    except Exception as e:
        print(f"[DEBUG] Erro geral: {type(e).__name__}: {e}")
        raise Exception(f"Erro ao chamar LM Studio: {str(e)}")
