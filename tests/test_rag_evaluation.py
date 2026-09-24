
import requests


API_URL = "http://127.0.0.1:8000"


TEST_CASES = [
    {
        "name": "UPI PIN safety",
        "question": "Should I share my UPI PIN with someone?",
        "expected_level": "general",
        "expected_concepts": [
            ["pin"],
            ["share", "confidential", "private"],
        ],
    },
    {
        "name": "Bank employee PIN request",
        "question": "Someone says they are from my bank and asks for my UPI PIN. What should I do?",
        "expected_level": "general",
        "expected_concepts": [
            ["pin"],
            ["share", "confidential", "private", "do not"],
        ],
    },
    {
        "name": "QR code definition",
        "question": "What is a QR code?",
        "expected_level": "general",
        "expected_concepts": [
            ["qr"],
            ["payment", "transaction"],
        ],
    },
    {
        "name": "Unknown QR code",
        "question": "Someone I don't know sent me a QR code and asked me to scan it. What should I do?",
        "expected_level": "caution",
        "expected_concepts": [
            ["qr"],
            ["do not scan", "not scan", "avoid", "cautious"],
        ],
    },
    {
        "name": "QR refund warning",
        "question": "Someone is asking me to scan a QR code to receive a refund.",
        "expected_level": "caution",
        "expected_concepts": [
            ["qr"],
            ["refund"],
            ["verify", "cautious", "do not scan", "not scan"],
        ],
    },
    {
        "name": "QR reward warning",
        "question": "Someone sent me a QR code and said I will receive ₹5,000 if I scan it.",
        "expected_level": "caution",
        "expected_concepts": [
            ["qr"],
            ["scan"],
            ["verify", "cautious", "do not scan", "not scan"],
        ],
    },
    {
        "name": "Cashback offer",
        "question": "I received a message saying I won a cashback reward and need to scan a QR code.",
        "expected_level": "caution",
        "expected_concepts": [
            ["cashback", "reward"],
            ["qr"],
            ["verify", "cautious", "do not scan", "not scan"],
        ],
    },
    {
        "name": "Suspicious link",
        "question": "Someone sent me a suspicious link for a UPI refund. What should I do?",
        "expected_level": "caution",
        "expected_concepts": [
            ["link"],
            ["suspicious", "avoid", "do not"],
            ["verify", "official"],
        ],
    },
    {
        "name": "Unknown app",
        "question": "Someone asked me to install an unknown app to complete a UPI refund.",
        "expected_level": "caution",
        "expected_concepts": [
            ["app"],
            ["install", "unknown"],
            ["avoid", "do not", "verify"],
        ],
    },
    {
        "name": "Suspicious link and app",
        "question": "Someone sent me a suspicious link and asked me to install an unknown app for a UPI refund. What should I do?",
        "expected_level": "caution",
        "expected_concepts": [
            ["link"],
            ["app"],
            ["verify", "avoid", "do not"],
        ],
    },
    {
        "name": "Collect request",
        "question": "I received an unexpected UPI collect request. What should I do?",
        "expected_level": "caution",
        "expected_concepts": [
            ["collect", "request"],
            ["verify", "reject", "do not"],
        ],
    },
    {
        "name": "Unexpected payment request",
        "question": "Someone I don't know sent me a payment request. Should I accept it?",
        "expected_level": "caution",
        "expected_concepts": [
            ["payment", "request"],
            ["verify", "reject", "do not"],
        ],
    },
    {
        "name": "Money stolen",
        "question": "Money was stolen from my account. What should I do?",
        "expected_level": "urgent",
        "expected_concepts": [
            ["bank", "banking"],
            ["transaction"],
            ["official"],
            ["evidence", "screenshot", "upi id"],
        ],
    },
    {
        "name": "Unauthorized transaction",
        "question": "I see an unauthorized UPI transaction in my account.",
        "expected_level": "urgent",
        "expected_concepts": [
            ["bank", "banking"],
            ["transaction"],
            ["official"],
            ["report", "reporting"],
        ],
    },
    {
        "name": "Account hacked",
        "question": "I think my account has been hacked and money may be at risk.",
        "expected_level": "urgent",
        "expected_concepts": [
            ["bank", "banking", "official"],
            ["report", "contact"],
        ],
    },
    {
        "name": "General UPI safety",
        "question": "Is UPI safe to use?",
        "expected_level": "general",
        "expected_concepts": [
            ["upi"],
            ["safe", "safety"],
        ],
    },
    {
        "name": "Transaction verification",
        "question": "What should I check before making a UPI payment?",
        "expected_level": "general",
        "expected_concepts": [
            ["transaction", "payment"],
            ["recipient", "amount", "details"],
        ],
    },
    {
        "name": "PIN follow-up concept",
        "question": "Why should I keep my UPI PIN private?",
        "expected_level": "general",
        "expected_concepts": [
            ["pin"],
            ["private", "confidential", "share"],
        ],
    },
    {
        "name": "Unknown knowledge question",
        "question": "What is the history of the UPI logo design?",
        "expected_level": "general",
        "expected_concepts": [
            ["trusted knowledge", "not contain", "not enough"],
        ],
    },
    {
        "name": "Safe transaction check",
        "question": "How can I verify the details before authorizing a UPI transaction?",
        "expected_level": "general",
        "expected_concepts": [
            ["transaction"],
            ["verify", "check"],
            ["recipient", "amount", "details"],
        ],
    },
]


def concept_group_found(answer, concept_group):
    """
    Return True when at least one acceptable word/phrase
    from a concept group appears in the answer.
    """

    answer_lower = answer.lower()

    return any(
        concept.lower() in answer_lower
        for concept in concept_group
    )


def run_test(test_case):

    response = requests.post(
        f"{API_URL}/chat",
        json={
            "question": test_case["question"],
            "history": [],
        },
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    actual_level = result["safety"]["level"]
    answer = result["answer"]

    level_passed = (
        actual_level == test_case["expected_level"]
    )

    concept_results = []

    for concept_group in test_case["expected_concepts"]:

        found = concept_group_found(
            answer,
            concept_group
        )

        concept_results.append(found)

    concepts_passed = all(
        concept_results
    )

    passed = (
        level_passed
        and concepts_passed
    )

    return {
        "passed": passed,
        "actual_level": actual_level,
        "expected_level": test_case["expected_level"],
        "concept_results": concept_results,
        "answer": answer,
    }


def main():

    print("\n")
    print("=" * 60)
    print("UPI SAFETY ASSISTANT - RAG EVALUATION")
    print("=" * 60)

    total = len(TEST_CASES)
    passed_count = 0

    for index, test_case in enumerate(
        TEST_CASES,
        start=1
    ):

        print("\n")
        print(
            f"Test {index}/{total}: "
            f"{test_case['name']}"
        )

        print(
            f"Question: "
            f"{test_case['question']}"
        )

        try:

            result = run_test(test_case)

            if result["passed"]:
                print("Result: PASS")
                passed_count += 1
            else:
                print("Result: FAIL")

            print(
                f"Expected safety: "
                f"{result['expected_level']}"
            )

            print(
                f"Actual safety: "
                f"{result['actual_level']}"
            )

            print(
                f"Concept checks: "
                f"{result['concept_results']}"
            )

            print(
                f"Answer: "
                f"{result['answer']}"
            )

        except Exception as error:

            print("Result: ERROR")

            print(
                f"Error: "
                f"{error}"
            )

    print("\n")
    print("=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    print(
        f"Passed: "
        f"{passed_count}/{total}"
    )

    print(
        f"Failed: "
        f"{total - passed_count}/{total}"
    )

    accuracy = (
        passed_count / total
    ) * 100

    print(
        f"Pass rate: "
        f"{accuracy:.2f}%"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
