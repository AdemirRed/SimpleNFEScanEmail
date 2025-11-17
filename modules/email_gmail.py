import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Callable, Optional, Tuple
import base64
import threading


def _decode(value: Optional[bytes]) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8', errors='ignore')
        except Exception:
            return value.decode('latin-1', errors='ignore')
    return str(value)


def _decode_header_value(val: str) -> str:
    try:
        decoded_parts = decode_header(val)
        out = ""
        for part, enc in decoded_parts:
            if isinstance(part, bytes):
                try:
                    out += part.decode(enc or 'utf-8', errors='ignore')
                except Exception:
                    out += part.decode('latin-1', errors='ignore')
            else:
                out += part
        return out
    except Exception:
        return val or ""


class GmailClient:
    """Cliente simples para Gmail via IMAP com suporte a múltiplas threads.
    Cada thread terá sua própria conexão IMAP isolada usando threading.local()."""

    def __init__(self, server: str, port: int, user_email: str, password: str):
        self.server = server
        self.port = int(port)
        self.user_email = user_email
        self.password = password
        # Armazena conexões por thread usando threading.local()
        self._thread_local = threading.local()

    def _get_connection(self) -> imaplib.IMAP4_SSL:
        """Retorna a conexão IMAP para a thread atual, criando se necessário."""
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            self._thread_local.conn = imaplib.IMAP4_SSL(self.server, self.port)
            self._thread_local.conn.login(self.user_email, self.password)
            self._thread_local.conn.select('INBOX')
        return self._thread_local.conn

    def connect(self):
        """Conecta a thread atual ao servidor IMAP."""
        self._get_connection()

    def disconnect(self):
        """Desconecta a conexão da thread atual."""
        try:
            if hasattr(self._thread_local, 'conn') and self._thread_local.conn is not None:
                try:
                    self._thread_local.conn.close()
                except Exception:
                    pass
                self._thread_local.conn.logout()
        finally:
            self._thread_local.conn = None

    def _ensure(self):
        """Garante conexão ativa e INBOX selecionada. Reestabelece se necessário."""
        conn = self._get_connection()
        try:
            status, _ = conn.noop()
            if status != 'OK':
                raise imaplib.IMAP4.error('NOOP failed')
        except Exception:
            # reconectar
            self._thread_local.conn = None
            conn = self._get_connection()

    def _safe_select_inbox(self):
        """Seleciona INBOX, reconectando se necessário."""
        try:
            conn = self._get_connection()
            conn.select('INBOX')
        except Exception:
            self._thread_local.conn = None
            conn = self._get_connection()

    # --- Robustez para comandos UID ---
    def _uid(self, cmd: str, *args, _retry: int = 1):
        """Executa comando UID com uma tentativa de reconexão se a resposta for inesperada.
        Retorna a tupla (status, data) como imaplib.uid.
        """
        self._ensure()
        conn = self._get_connection()
        try:
            return conn.uid(cmd, *args)
        except imaplib.IMAP4.error:
            if _retry > 0:
                self._thread_local.conn = None
                conn = self._get_connection()
                return self._uid(cmd, *args, _retry=_retry-1)
            raise
        except Exception:
            if _retry > 0:
                self._thread_local.conn = None
                conn = self._get_connection()
                return self._uid(cmd, *args, _retry=_retry-1)
            raise

    def list_recent(self, limit: int = 10, result_callback: Optional[Callable[[Dict], None]] = None) -> List[Dict]:
        """Retorna os últimos N emails com cabeçalhos básicos.
        Se result_callback for fornecido, chama-o progressivamente para cada email processado.
        """
        self._ensure()
        try:
            status, data = self._uid('search', None, 'ALL')
            if status != 'OK' or not data or not data[0]:
                return []
            all_uids = _decode(data[0]).split()
            if not all_uids:
                return []
        except Exception:
            return []
            
        recent_uids = all_uids[-int(limit):]
        results: List[Dict] = []
        for uid in reversed(recent_uids):  # mais recente primeiro
            try:
                # Primeiro tenta buscar somente campos do cabeçalho
                status, msg_data = self._uid('fetch', uid, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
                tup = None
                if status == 'OK' and msg_data:
                    for part in msg_data:
                        if isinstance(part, tuple) and len(part) >= 2:
                            tup = part
                            break
                if tup is not None:
                    raw_headers = tup[1]
                    msg = email.message_from_bytes(raw_headers)
                    subject = _decode_header_value(msg.get('Subject', ''))
                    from_ = _decode_header_value(msg.get('From', ''))
                    date_ = _decode_header_value(msg.get('Date', ''))
                else:
                    # Fallback: pega a mensagem completa e extrai cabeçalhos
                    status, msg_full = self._uid('fetch', uid, '(BODY.PEEK[])')
                    if status != 'OK' or not msg_full:
                        continue
                    raw_email = None
                    for part in msg_full:
                        if isinstance(part, tuple) and len(part) >= 2:
                            raw_email = part[1]
                            break
                    if not raw_email:
                        continue
                    msg = email.message_from_bytes(raw_email)
                    subject = _decode_header_value(msg.get('Subject', ''))
                    from_ = _decode_header_value(msg.get('From', ''))
                    date_ = _decode_header_value(msg.get('Date', ''))
                item = {
                    'uid': uid,
                    'subject': subject,
                    'from': from_,
                    'date': date_,
                }
                results.append(item)
                # Callback progressivo
                if result_callback:
                    try:
                        result_callback(item)
                    except Exception:
                        pass
            except Exception:
                continue
        return results

    def count_inbox(self) -> int:
        """Retorna a quantidade de emails na INBOX."""
        self._ensure()
        # Método confiável: usar SEARCH ALL e contar
        status, data = self._uid('search', None, 'ALL')
        if status != 'OK' or not data:
            return 0
        return len(_decode(data[0]).split())

    def _iter_message_attachments(self, msg) -> List[Tuple[str, str]]:
        """Retorna lista (filename, content_type)."""
        found = []
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get('Content-Disposition') or '')
                if 'attachment' in content_disposition.lower():
                    filename = _decode_header_value(part.get_filename() or '')
                    content_type = (part.get_content_type() or '').lower()
                    found.append((filename, content_type))
        else:
            # mensagens simples com anexo inline
            filename = _decode_header_value(msg.get_filename() or '')
            if filename:
                found.append((filename, (msg.get_content_type() or '').lower()))
        return found

    def download_attachments(self, selections: List[Dict], download_dir: str,
                              progress_cb: Optional[Callable[[int, int], None]] = None) -> List[Dict]:
        """Baixa anexos especificados por UID+filename.
        selections: [{uid, filename, type}] onde type é 'PDF' ou 'XML'.
        Retorna lista com {uid, filename, path, type}
        """
        import os
        os.makedirs(download_dir, exist_ok=True)
        self._ensure()

        # Agrupa por UID
        by_uid: Dict[str, List[Dict]] = {}
        for s in selections:
            by_uid.setdefault(str(s['uid']), []).append(s)

        out: List[Dict] = []
        uids = list(by_uid.keys())
        total = len(uids)
        for i, uid in enumerate(uids, start=1):
            if progress_cb:
                progress_cb(i, total)
            try:
                status, msg_data = self._uid('fetch', uid, '(BODY.PEEK[])')
                if status != 'OK' or not msg_data:
                    continue
                tup = None
                for part in msg_data:
                    if isinstance(part, tuple):
                        tup = part
                        break
                if not tup:
                    continue
                msg = email.message_from_bytes(tup[1])
                wanted = {s['filename'] for s in by_uid[uid] if s.get('filename')}
                types_map = {s['filename']: s.get('type', '') for s in by_uid[uid]}
                if msg.is_multipart():
                    for part in msg.walk():
                        disp = str(part.get('Content-Disposition') or '')
                        if 'attachment' not in disp.lower():
                            continue
                        fname = _decode_header_value(part.get_filename() or '')
                        if wanted and fname not in wanted:
                            continue
                        payload = part.get_payload(decode=True) or b''
                        if not payload:
                            continue
                        path = os.path.join(download_dir, fname)
                        with open(path, 'wb') as f:
                            f.write(payload)
                        out.append({'uid': uid, 'filename': fname, 'path': path, 'type': types_map.get(fname, '')})
                else:
                    fname = _decode_header_value(msg.get_filename() or '')
                    if fname and (not wanted or fname in wanted):
                        payload = msg.get_payload(decode=True) or b''
                        if payload:
                            path = os.path.join(download_dir, fname)
                            with open(path, 'wb') as f:
                                f.write(payload)
                            out.append({'uid': uid, 'filename': fname, 'path': path, 'type': types_map.get(fname, '')})
            except Exception:
                continue
        return out

    def search_notes(
        self,
        note_types,  # List[str] ou str: 'PDF', 'XML' ou ambos
        limit: int,
        include_keywords: List[str],
        exclude_keywords: List[str],
        progress_cb: Optional[Callable[[int, int], None]] = None,
        result_callback: Optional[Callable[[Dict], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> List[Dict]:
        """Busca anexos PDF/XML nos últimos N emails, aplicando filtros.
        Retorna lista de dicts: {date, from, subject, filename, type, uid}
        Se result_callback for fornecido, chama-o progressivamente para cada resultado encontrado.
        Se cancel_check for fornecido, verifica periodicamente se deve cancelar.
        """
        self._ensure()
        status, data = self._uid('search', None, 'ALL')
        if status != 'OK':
            return []
        all_uids = _decode(data[0]).split()
        # Limitar para evitar scans gigantes que derrubam a conexão
        lim = int(limit)
        if lim <= 0:
            return []
        # Cap suave para estabilidade (pode ser ajustado nas preferências futuramente)
        MAX_SCAN = 5000
        if lim > MAX_SCAN:
            lim = MAX_SCAN
        to_scan = list(reversed(all_uids[-lim:]))  # mais recente primeiro
        results: List[Dict] = []

        # Normaliza tipos
        if isinstance(note_types, str):
            types_set = {note_types.upper()}
        else:
            types_set = {t.upper() for t in (note_types or [])}
        if not types_set:
            types_set = {"PDF", "XML"}

        target_exts = set()
        if "PDF" in types_set:
            target_exts.add('.pdf')
        if "XML" in types_set:
            target_exts.add('.xml')

        print(f"[GMAIL] Buscando em {len(to_scan)} emails mais recentes")
        print(f"[GMAIL] Tipos aceitos: {types_set}")
        print(f"[GMAIL] Extensões aceitas: {target_exts}")
        print(f"[GMAIL] Include keywords: {include_keywords}")
        print(f"[GMAIL] Exclude keywords: {exclude_keywords}")

        total = len(to_scan)
        for idx, uid in enumerate(to_scan, start=1):
            # Verifica cancelamento
            if cancel_check and cancel_check():
                print(f"[GMAIL] Busca cancelada pelo usuário após {idx-1}/{total} emails")
                break
                
            if progress_cb:
                progress_cb(idx, total)
            try:
                # BODY.PEEK[] evita marcar como lido e é mais estável no Gmail
                # Verificação periódica da conexão
                if idx % 50 == 0:
                    self._ensure()
                status, msg_data = self._uid('fetch', uid, '(BODY.PEEK[])')
                if status != 'OK' or not msg_data:
                    continue
                # Em algumas respostas há itens extra; filtra tuplas
                tup = None
                for part in msg_data:
                    if isinstance(part, tuple):
                        tup = part
                        break
                if not tup:
                    continue
                raw_email = tup[1]
                msg = email.message_from_bytes(raw_email)
            except Exception:
                # Pula mensagens com resposta inesperada
                continue

            subject = _decode_header_value(msg.get('Subject', ''))
            from_ = _decode_header_value(msg.get('From', ''))
            date_ = _decode_header_value(msg.get('Date', ''))

            # Filtros por palavras-chave (subject e from)
            subj_from_text = f"{subject} {from_}".lower()
            
            # Verifica exclusões no subject/from primeiro
            if exclude_keywords and any(k.lower() in subj_from_text for k in exclude_keywords):
                continue

            # Se há keywords de inclusão, verifica se o EMAIL (subject/from) contém alguma
            # Isso permite encontrar notas fiscais mesmo que o nome do anexo não tenha as keywords
            email_has_keyword = False
            if include_keywords:
                email_has_keyword = any(k.lower() in subj_from_text for k in include_keywords)
                # Se o email não tem keywords, pula este email inteiro
                if not email_has_keyword:
                    continue

            attachments = self._iter_message_attachments(msg)
            if attachments:
                print(f"[GMAIL] UID {uid}: {len(attachments)} anexo(s) - {[f for f, _ in attachments]}")
                if email_has_keyword:
                    print(f"[GMAIL]   Email contém keywords - subject: '{subject[:50]}...'")
            
            for fname, ctype in attachments:
                fname_l = (fname or '').lower()
                if not fname_l:
                    print(f"[GMAIL]   - Anexo sem nome, pulando")
                    continue
                if not any(fname_l.endswith(ext) for ext in target_exts):
                    print(f"[GMAIL]   - '{fname}' não termina com {target_exts}, pulando")
                    continue
                
                # Se o EMAIL já passou pelo filtro de keywords, aceita o anexo
                # Caso contrário, verifica se o nome do arquivo contém keywords
                if include_keywords and not email_has_keyword:
                    # Email não tem keywords, verifica apenas o nome do arquivo
                    file_has_keyword = any(k.lower() in fname_l for k in include_keywords)
                    if not file_has_keyword:
                        print(f"[GMAIL]   - '{fname}' não contém keywords {include_keywords}, pulando")
                        continue
                
                # Exclusões: se alguma keyword de exclusão estiver no nome, pula
                if exclude_keywords and any(k.lower() in fname_l for k in exclude_keywords):
                    print(f"[GMAIL]   - '{fname}' contém keyword de exclusão, pulando")
                    continue
                
                print(f"[GMAIL]   ✓ '{fname}' ACEITO!")
                result_item = {
                    'uid': uid,
                    'date': date_,
                    'from': from_,
                    'subject': subject,
                    'filename': fname,
                    'type': 'PDF' if fname_l.endswith('.pdf') else 'XML'
                }
                results.append(result_item)
                # Callback progressivo
                if result_callback:
                    result_callback(result_item)
        return results

    def fetch_email(self, uid: str) -> Dict:
        """Baixa o email completo e retorna metadados, texto e HTML."""
        self._ensure()
        try:
            status, msg_data = self._uid('fetch', uid, '(BODY.PEEK[])')
            if status != 'OK' or not msg_data:
                raise RuntimeError('Falha ao obter email')
            tup = None
            for part in msg_data:
                if isinstance(part, tuple) and len(part) >= 2:
                    tup = part
                    break
            if not tup:
                raise RuntimeError('Resposta inesperada do servidor')
            raw_email = tup[1]
            msg = email.message_from_bytes(raw_email)
        except Exception as e:
            raise RuntimeError(f'Erro ao buscar email: {e}')

        subject = _decode_header_value(msg.get('Subject', ''))
        from_ = _decode_header_value(msg.get('From', ''))
        date_ = _decode_header_value(msg.get('Date', ''))

        # Extrair HTML e texto
        body_text = ""
        body_html = ""
        cid_map: Dict[str, str] = {}
        
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                disp = str(part.get('Content-Disposition') or '')
                # captura imagens inline com Content-ID para renderização no navegador
                content_id = (part.get('Content-ID') or '').strip()
                try:
                    payload = part.get_payload(decode=True)
                except Exception:
                    payload = None
                if content_id and payload and 'attachment' not in disp.lower():
                    # normaliza CID: remove <>
                    cid_clean = content_id
                    if cid_clean.startswith('<') and cid_clean.endswith('>'):
                        cid_clean = cid_clean[1:-1]
                    try:
                        b64 = base64.b64encode(payload).decode('ascii')
                        data_uri = f"data:{ctype};base64,{b64}"
                        # mapeia com e sem prefixo cid:
                        cid_map[cid_clean] = data_uri
                        cid_map[f"cid:{cid_clean}"] = data_uri
                    except Exception:
                        pass
                # conteúdo textual do corpo (ignora anexos)
                if 'attachment' in disp.lower():
                    continue
                
                try:
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        decoded = payload.decode(charset, errors='ignore')
                        if ctype == 'text/html' and not body_html:
                            body_html = decoded
                        elif ctype == 'text/plain' and not body_text:
                            body_text = decoded
                except Exception:
                    continue
        else:
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    decoded = payload.decode(charset, errors='ignore')
                    ctype = msg.get_content_type()
                    if ctype == 'text/html':
                        body_html = decoded
                    else:
                        body_text = decoded
            except Exception:
                try:
                    body_text = _decode(msg.get_payload())
                except Exception:
                    body_text = "Erro ao decodificar conteúdo do email"

        attachments = self._iter_message_attachments(msg)
        return {
            'uid': uid,
            'subject': subject,
            'from': from_,
            'date': date_,
            'body_text': body_text,
            'body_html': body_html,
            'attachments': [{'filename': a[0], 'content_type': a[1]} for a in attachments],
            'cid_map': cid_map
        }
