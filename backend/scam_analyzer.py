def analyze_scenario(text):
    """
    Analyze a user's UPI scenario for common warning signs.

    This is an advisory analysis.
    It does not confirm that a situation is fraudulent.
    """

    text = text.lower().strip()

    # =========================================
    # URGENT SITUATIONS
    # =========================================

    urgent_keywords = [
        "money stolen",
        "money was stolen",
        "money deducted",
        "money has been deducted",
        "unauthorized transaction",
        "unauthorised transaction",
        "fraudulent transaction",
        "already scammed",
        "account hacked",
        "account has been hacked",
        "money lost",
        "lost money",
    ]

    if any(keyword in text for keyword in urgent_keywords):
        return {
            "level": "urgent",
            "label": "Urgent Action",
            "icon": "🔴",
            "indicators": [
                "The scenario indicates that money may already have been lost or an unauthorized transaction may have occurred."
            ],
        }

    # =========================================
    # WARNING INDICATORS
    # =========================================

    indicators = []

    checks = [
        (
            ["upi pin", "pin"],
            "Someone is asking for your UPI PIN."
        ),
        (
            ["otp", "one time password"],
            "Someone is asking for an OTP."
        ),
        (
            ["qr code", "scan qr", "scan a qr"],
            "The situation involves a QR code."
        ),
        (
            [
                "unknown link",
                "suspicious link",
                "click the link",
                "link",
            ],
            "The situation involves a potentially suspicious link."
        ),
        (
            [
                "cashback",
                "refund",
                "reward",
                "prize",
            ],
            "The situation involves a cashback, refund, reward, or prize claim."
        ),
        (
            [
                "unknown app",
                "install app",
                "download app",
                "remote access",
            ],
            "The situation involves an unfamiliar or potentially risky application."
        ),
        (
            [
                "collect request",
                "payment request",
                "request money",
            ],
            "The situation involves a payment or collect request."
        ),
        (
            [
                "scammer",
                "fraud",
                "fraudster",
                "scam",
            ],
            "The user has mentioned suspected fraud or a scam."
        ),
    ]

    for keywords, message in checks:
        if any(keyword in text for keyword in keywords):
            indicators.append(message)

    # =========================================
    # CAUTION
    # =========================================

    if indicators:
        return {
            "level": "caution",
            "label": "Caution",
            "icon": "🟡",
            "indicators": indicators,
        }

    # =========================================
    # GENERAL GUIDANCE
    # =========================================

    return {
        "level": "general",
        "label": "General Guidance",
        "icon": "🟢",
        "indicators": [],
    }