import logging
import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


"""
OTP USE FOR PRODCUTION ONLY!
"""

"""
KAVENEGAR OTP TEMPLATE!!!

This template is added only for demonstration purposes.
It is not functional because an API token must be purchased/activated
from Kavenegar before it can be used.
"""


def send_sms(receptor, variables, pattern_code):
    url = (
        f"https://api.kavenegar.com/v1/{settings.KAVENEGAR_API_KEY}/verify/lookup.json"
    )
    payload = {
        "receptor": receptor,
        "template": pattern_code,
        "token": variables.get("verification-code"),
        "type": "sms",
    }
    logger.info(f"Sending SMS to {receptor} with payload: {payload}")
    try:
        response = requests.post(url, data=payload, timeout=10)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text}")
        if response.status_code == 200:
            result = response.json()
            if result.get("return", {}).get("status") == 200:
                logger.info(f"SMS sent successfully to {receptor}")
            else:
                logger.error(f"API error: {result}")
        else:
            logger.error(f"Error sending SMS: {response.status_code} - {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error in send_sms: {e}", exc_info=True)
        return None


@shared_task
def send_verification_sms(mobile, code):
    logger.info(f"Starting to send SMS to {mobile} with code {code}")
    try:
        variables = {"verification-code": str(code)}
        response = send_sms(mobile, variables, "login-otp")
        if response and response.status_code == 200:
            logger.info(f"Verification SMS sent to {mobile}")
        else:
            raise Exception("Failed to send SMS")
    except Exception as e:
        logger.error(f"Error in send_verification_sms: {e}", exc_info=True)
        raise


@shared_task
def send_registry_sms(mobile, code):
    logger.info(f"Starting to send SMS to {mobile} with code {code}")
    try:
        variables = {"verification-code": str(code)}
        response = send_sms(mobile, variables, "appt-otpcode")
        if response and response.status_code == 200:
            logger.info(f"Verification SMS sent to {mobile}")
        else:
            raise Exception("Failed to send SMS")
    except Exception as e:
        logger.error(f"Error in send_verification_sms: {e}", exc_info=True)
        raise
