"""
Unit tests for Execution and Form Detectors.
"""

from src.execution.form_detectors import FormDetector
from src.matcher.profile_loader import load_candidate_profile


def test_form_detector_field_resolution() -> None:
    profile = load_candidate_profile()

    # 1. Full Name / First Name / Last Name
    assert FormDetector.resolve_field_value("Nama Lengkap Pelamar", profile) == "Aditya Darmawan"
    assert FormDetector.resolve_field_value("First Name", profile) == "Aditya"
    assert FormDetector.resolve_field_value("Last Name", profile) == "Darmawan"

    # 2. Contact info
    assert FormDetector.resolve_field_value("Email Address", profile) == "dantedarmawan@yahoo.com"
    assert FormDetector.resolve_field_value("Nomor WhatsApp / HP", profile) == "08115994948"
    assert FormDetector.resolve_field_value("LinkedIn Profile URL", profile) == profile.linkedin

    # 3. Experience & Skills
    exp_val = FormDetector.resolve_field_value("Total Years of Work Experience", profile)
    assert exp_val == "15"

    exp_dropdown_val = FormDetector.resolve_field_value(
        "Berapa tahun pengalaman di bidang perbankan/kredit?",
        profile,
        options=["< 1 tahun", "1-3 tahun", "3-5 tahun", "5-10 tahun", "10+ tahun"]
    )
    assert exp_dropdown_val == "10+ tahun"

    # 4. Salary
    salary_val = FormDetector.resolve_field_value("Expected Monthly Salary (IDR)", profile)
    assert salary_val == "35000000"

    # 5. Education
    edu_val = FormDetector.resolve_field_value("Highest Level of Education", profile, options=["SMA", "Diploma", "Bachelor / S1", "Master / S2"])
    assert edu_val == "Bachelor / S1"


if __name__ == "__main__":
    test_form_detector_field_resolution()
    print("All execution tests passed!")
