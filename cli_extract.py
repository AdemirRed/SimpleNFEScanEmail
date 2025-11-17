import os
import sys
import json
import argparse
from typing import List, Dict

# Caminho base
BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
OUT_PATH = os.path.join(TEMP_DIR, 'out_items.json')


def load_config() -> Dict:
    default = {
        "email": {"server": "imap.gmail.com", "port": 993, "address": "", "app_password": ""},
        "lmstudio": {"url": "http://127.0.0.1:1234", "model": "openai/gpt-oss-20b"},
        "search": {"include_keywords": ["nfe", "nf-e", "nota", "xml", "danfe"], "exclude_keywords": ["promo", "oferta", "newsletter"]},
    }
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                    elif isinstance(v, dict):
                        for k2, v2 in v.items():
                            data[k].setdefault(k2, v2)
                return data
    except Exception:
        pass
    return default


def main():
    parser = argparse.ArgumentParser(description='SimpleNFE CLI - Busca e extração de notas (sem UI)')
    parser.add_argument('--limit', type=int, default=20, help='Quantidade de emails para buscar (padrão: 20)')
    parser.add_argument('--types', type=str, default='pdf,xml', help='Tipos de nota: pdf,xml (padrão: ambos)')
    parser.add_argument('--include', type=str, default='', help='Palavras-chave a incluir, separadas por vírgula (sobrescreve config)')
    parser.add_argument('--exclude', type=str, default='', help='Palavras-chave a excluir, separadas por vírgula (sobrescreve config)')
    parser.add_argument('--output', type=str, default=OUT_PATH, help='Arquivo JSON de saída com os itens extraídos')
    args = parser.parse_args()

    cfg = load_config()
    types = [t.strip().upper() for t in args.types.split(',') if t.strip()]
    if not types:
        types = ['PDF', 'XML']
    include = [s.strip() for s in (args.include or '').split(',') if s.strip()] or cfg['search'].get('include_keywords', [])
    exclude = [s.strip() for s in (args.exclude or '').split(',') if s.strip()] or cfg['search'].get('exclude_keywords', [])

    from modules.email_gmail import GmailClient
    from modules.xml_pdf_extractor import extract_items_from_xml, extract_text_from_pdf, extract_items_from_pdf_via_llm

    os.makedirs(TEMP_DIR, exist_ok=True)

    print('Conectando ao Gmail...')
    client = GmailClient(cfg['email']['server'], int(cfg['email']['port']), cfg['email']['address'], cfg['email']['app_password'])

    done = 0
    def prog(d, t):
        nonlocal done
        done = d
        print(f'Buscando... {d}/{t}', end='\r', flush=True)

    print(f'Buscando anexos (tipos: {types}, limite: {args.limit})...')
    results = client.search_notes(types, int(args.limit), include, exclude, progress_cb=prog)
    print()  # nova linha após progresso
    print(f'Encontrados {len(results)} anexos candidatos.')

    if not results:
        print('Nada encontrado com os filtros. Saindo.')
        return 0

    print('Baixando anexos...')
    dl_done = 0
    def dl_cb(d, t):
        nonlocal dl_done
        dl_done = d
        print(f'Download {d}/{t}', end='\r', flush=True)

    selections = [{'uid': r['uid'], 'filename': r['filename'], 'type': r['type']} for r in results]
    downloaded = client.download_attachments(selections, TEMP_DIR, progress_cb=dl_cb)
    print()  # nova linha
    print(f'Baixados {len(downloaded)} anexos.')

    all_items: List[Dict] = []
    for idx, att in enumerate(downloaded, start=1):
        path = att['path']
        name = os.path.basename(path)
        if att.get('type') == 'XML' or path.lower().endswith('.xml'):
            print(f'[{idx}/{len(downloaded)}] Extraindo XML: {name}')
            items = extract_items_from_xml(path)
        else:
            print(f'[{idx}/{len(downloaded)}] Extraindo PDF via LM: {name} (aguarde)')
            text = extract_text_from_pdf(path)
            items = extract_items_from_pdf_via_llm(text, cfg.get('lmstudio', {}).get('url', 'http://127.0.0.1:1234'), cfg.get('lmstudio', {}).get('model', 'openai/gpt-oss-20b'))
        for it in items:
            it['documento'] = name
        all_items.extend(items)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'items': all_items}, f, ensure_ascii=False, indent=2)

    total = sum(float(it.get('valor_total', 0) or 0) for it in all_items)
    print(f'Concluído. Itens: {len(all_items)} | Total: {total:.2f}')
    print(f'Arquivo salvo em: {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
