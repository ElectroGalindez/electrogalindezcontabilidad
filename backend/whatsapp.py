# ---------------------------
# Alertas automáticas (WhatsApp / Logs)
# ---------------------------
import pandas as pd
from backend import productos, deudas
from backend.whatsapp import enviar_whatsapp

def alertas_seguras():
    """
    Envía alertas de stock crítico y deudas vencidas.
    Si Twilio no está configurado, solo registra el mensaje en consola y en logs.
    """
    try:
        # Stock crítico
        stock_critico = [p for p in productos.list_products() if p["cantidad"] <= 5]
        if stock_critico:
            mensaje_stock = f"⚠️ ALERTA: {len(stock_critico)} productos con stock crítico: " \
                            + ", ".join(p["nombre"] for p in stock_critico)
            try:
                enviar_whatsapp(mensaje_stock)
            except Exception as e:
                print(f"[DEBUG] Mensaje WhatsApp pendiente: {mensaje_stock} (Error: {e})")

        # Deudas vencidas
        deudas_vencidas = [
            d for d in deudas.list_debts()
            if d["estado"] == "pendiente"
            and "vencimiento" in d
            and pd.to_datetime(d["vencimiento"]) < pd.Timestamp.today()
        ]
        if deudas_vencidas:
            mensaje_deudas = f"💳 ALERTA: {len(deudas_vencidas)} deudas vencidas de clientes."
            try:
                enviar_whatsapp(mensaje_deudas)
            except Exception as e:
                print(f"[DEBUG] Mensaje WhatsApp pendiente: {mensaje_deudas} (Error: {e})")

    except Exception as e:
        print(f"[ERROR] No se pudieron procesar las alertas: {e}")

# Llamada segura
alertas_seguras()
