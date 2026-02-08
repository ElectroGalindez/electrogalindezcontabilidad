"""Twilio WhatsApp helper module."""

import os

from twilio.rest import Client


def enviar_whatsapp(mensaje, destinatario=None):
    """
    Envía un mensaje de WhatsApp usando Twilio.
    destinatario: número en formato internacional, ej: 'whatsapp:+549XXXXXXXXXX'
    """
    # Configuración desde variables de entorno
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM")
    to_whatsapp = destinatario or os.getenv("TWILIO_WHATSAPP_TO")

    missing = [
        name
        for name, value in {
            "TWILIO_ACCOUNT_SID": account_sid,
            "TWILIO_AUTH_TOKEN": auth_token,
            "TWILIO_WHATSAPP_FROM": from_whatsapp,
            "TWILIO_WHATSAPP_TO": to_whatsapp,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno para Twilio: "
            + ", ".join(missing)
            + ". Configúralas en tu .env o entorno."
        )

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=mensaje,
        from_=from_whatsapp,
        to=to_whatsapp
    )
    return message.sid
