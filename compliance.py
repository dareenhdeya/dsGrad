"""
Compliance rules for VisionGuard.

We take the raw boxes that the YOLO model found in an image and turn them
into a simple safety verdict: COMPLIANT or VIOLATION.

Class ids (fixed during training, do not change):
0 = Person
1 = Hardhat
2 = NO-Hardhat
3 = Safety Vest
4 = NO-Safety Vest
"""

CLASS_NAMES = ["Person", "Hardhat", "NO-Hardhat", "Safety Vest", "NO-Safety Vest"]


def summarize_detections(boxes):
    """
    boxes: list of dicts, each like {"class_id": int, "class_name": str, "confidence": float, "box": [x1,y1,x2,y2]}

    Returns a compliance summary dict.
    """
    counts = {name: 0 for name in CLASS_NAMES}
    for box in boxes:
        counts[box["class_name"]] += 1

    violations = []
    if counts["NO-Hardhat"] > 0:
        violations.append("missing_helmet")
    if counts["NO-Safety Vest"] > 0:
        violations.append("missing_safety_vest")

    status = "VIOLATION" if violations else "COMPLIANT"

    return {
        "persons_detected": counts["Person"],
        "compliant_detections": counts["Hardhat"] + counts["Safety Vest"],
        "violations_detected": counts["NO-Hardhat"] + counts["NO-Safety Vest"],
        "violation_types": violations,
        "status": status,
        "class_counts": counts,
    }
