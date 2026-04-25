import hashlib
import logging
from config import CLICK_SERVICE_ID, CLICK_MERCHANT_ID, CLICK_SECRET_KEY

def generate_click_url(order_id: str, amount: float) -> str:
    """
    Generates a direct Click payment URL for a specific order.
    """
    if not CLICK_SERVICE_ID or not CLICK_MERCHANT_ID:
        logging.error("Click Service ID or Merchant ID is not configured!")
        return "#"
        
    url = (
        f"https://my.click.uz/services/pay?"
        f"service_id={CLICK_SERVICE_ID}&"
        f"merchant_id={CLICK_MERCHANT_ID}&"
        f"amount={amount}&"
        f"transaction_param={order_id}"
    )
    return url

def verify_click_signature(click_trans_id, service_id, click_paydoc_id, merchant_trans_id, amount, action, error, sign_time, sign_string):
    """
    Verifies the MD5 signature sent by Click webhook.
    """
    # Important: Click signature string format is fixed
    # md5(click_trans_id + service_id + click_paydoc_id + merchant_trans_id + amount + action + error + sign_time + secret_key)
    prepared_str = f"{click_trans_id}{service_id}{click_paydoc_id}{merchant_trans_id}{amount}{action}{error}{sign_time}{CLICK_SECRET_KEY}"
    my_sign = hashlib.md5(prepared_str.encode()).hexdigest()
    
    return my_sign == sign_string
