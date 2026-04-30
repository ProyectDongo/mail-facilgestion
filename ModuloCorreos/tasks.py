import imaplib
import email
import email.utils
from email.header import decode_header
from celery import shared_task
from django.conf import settings
from django.utils.timezone import make_aware, is_aware
from .models import SyncEstado, PerfilRemitente, CorreoCopia


def decodificar(valor):
    if not valor:
        return ''
    partes = decode_header(valor)
    resultado = ''
    for contenido, charset in partes:
        if isinstance(contenido, bytes):
            resultado += contenido.decode(charset or 'utf-8', errors='replace')
        else:
            resultado += str(contenido)
    return resultado.strip()


def extraer_cuerpo(msg):
    cuerpo = ''
    if msg.is_multipart():
        for parte in msg.walk():
            ct = parte.get_content_type()
            cd = str(parte.get('Content-Disposition', ''))
            if ct == 'text/plain' and 'attachment' not in cd:
                payload = parte.get_payload(decode=True)
                if payload:
                    charset = parte.get_content_charset() or 'utf-8'
                    cuerpo += payload.decode(charset, errors='replace')
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            cuerpo = payload.decode(charset, errors='replace')
    return cuerpo.strip()


def extraer_adjuntos(msg):
    nombres, tiene = [], False
    for parte in msg.walk():
        if str(parte.get('Content-Disposition', '')).startswith('attachment'):
            tiene = True
            nombre = parte.get_filename()
            if nombre:
                nombres.append(decodificar(nombre))
    return tiene, ', '.join(nombres)


@shared_task(name='ModuloCorreos.tasks.sincronizar_imap')
def sincronizar_imap():
    estado, _ = SyncEstado.objects.get_or_create(id=1)
    ultimo_uid = estado.ultimo_uid
    batch_size = settings.IMAP_BATCH_SIZE
    nuevos = 0

    try:
        imap = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        imap.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        imap.select('INBOX', readonly=True)

        _, datos = imap.uid('search', None, 'ALL')
        todos_uids = [int(u) for u in datos[0].split() if int(u) > ultimo_uid]
        lote = todos_uids[:batch_size]

        for uid in lote:
            try:
                _, data = imap.uid('fetch', str(uid), '(RFC822)')
                if not data or not data[0]:
                    continue
                raw = data[0][1]
                msg = email.message_from_bytes(raw)

                message_id = msg.get('Message-ID', f'uid-{uid}').strip()
                if CorreoCopia.objects.filter(message_id=message_id).exists():
                    ultimo_uid = max(ultimo_uid, uid)
                    continue

                asunto   = decodificar(msg.get('Subject', ''))
                de_raw   = decodificar(msg.get('From', ''))
                para_raw = decodificar(msg.get('To', ''))
                cuerpo   = extraer_cuerpo(msg)
                tiene_adj, nombres_adj = extraer_adjuntos(msg)

                nombre_r, email_r = email.utils.parseaddr(de_raw)
                email_r  = (email_r or f'uid{uid}@desconocido').lower()
                dominio  = email_r.split('@')[-1] if '@' in email_r else ''

                perfil, created = PerfilRemitente.objects.get_or_create(
                    email=email_r,
                    defaults={'nombre': nombre_r, 'dominio': dominio}
                )
                if not created and not perfil.nombre and nombre_r:
                    perfil.nombre = nombre_r
                perfil.total_correos += 1
                perfil.save()

                fecha_str = msg.get('Date', '')
                fecha_dt = None
                try:
                    fecha_dt = email.utils.parsedate_to_datetime(fecha_str)
                    if not is_aware(fecha_dt):
                        fecha_dt = make_aware(fecha_dt)
                except Exception:
                    pass

                CorreoCopia.objects.create(
                    remitente=perfil,
                    message_id=message_id,
                    de=de_raw,
                    para=para_raw,
                    asunto=asunto,
                    fecha=fecha_dt,
                    cuerpo=cuerpo,
                    tiene_adjuntos=tiene_adj,
                    nombres_adjuntos=nombres_adj,
                    uid_imap=uid,
                )
                ultimo_uid = max(ultimo_uid, uid)
                nuevos += 1

            except Exception as e:
                print(f"[IMAP] Error UID {uid}: {e}")
                continue

        imap.logout()

    except Exception as e:
        print(f"[IMAP] Error de conexión: {e}")
        return f"Error: {e}"

    estado.ultimo_uid = ultimo_uid
    estado.save()
    return f"{nuevos} nuevos — último UID: {ultimo_uid} — pendientes: {len(todos_uids) - batch_size}"


@shared_task(name='ModuloCorreos.tasks.clasificar_pendientes')
def clasificar_pendientes():
    from .clasificador import (
        detectar_tema, detectar_tono, generar_resumen,
        es_pendiente, actualizar_perfil, detectar_tipo_remitente
    )

    DOMINIOS_PERSONALES = [
        'gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com',
        'live.com', 'icloud.com', 'yahoo.es', 'hotmail.es'
    ]

    correos = CorreoCopia.objects.filter(clasificado=False).select_related('remitente')[:200]
    procesados = 0
    perfiles_afectados = set()

    for correo in correos:
        correo.tema       = detectar_tema(correo.asunto, correo.cuerpo)
        correo.tono       = detectar_tono(correo.asunto, correo.cuerpo)
        correo.resumen    = generar_resumen(correo.asunto, correo.cuerpo)
        correo.es_pendiente = es_pendiente(correo.asunto, correo.cuerpo)
        correo.clasificado  = True
        correo.save()

        if correo.remitente:
            perfiles_afectados.add(correo.remitente.id)
        procesados += 1

    for pid in perfiles_afectados:
        try:
            perfil = PerfilRemitente.objects.get(id=pid)
            perfil.tipo = detectar_tipo_remitente(perfil.email, perfil.dominio)
            perfil.es_empresa = (
                perfil.dominio not in DOMINIOS_PERSONALES and bool(perfil.dominio)
            )
            correos_perfil = list(CorreoCopia.objects.filter(remitente=perfil))
            actualizar_perfil(perfil, correos_perfil)
        except Exception as e:
            print(f"[CLASIFICADOR] Error perfil {pid}: {e}")

    return f"{procesados} correos clasificados"
