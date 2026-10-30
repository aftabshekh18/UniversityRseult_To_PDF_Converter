

import re

import pdfplumber
import pandas as pd


SUBJECTS = [
    ("BTCOC501", "DATABASE SYSTEMS"),
    ("BTCOC502", "THEORY OF COMPUTATIONS"),
    ("BTCOC503", "SOFTWARE ENGINEERING"),
    ("BTCOE504A", "HUMAN COMPUTER INTERACTION"),
    ("BTCOF408", "FIELD TRAINING / INTERNSHIP / INDUSTRIAL TRAINING - II"),
    ("BTCOL506", "DATABASE SYSTEM AND SOFTWARE ENGINEERING LAB"),
    ("BTCOM507", "MINI PROJECT I"),
    ("BTHM505B", "BUSINESS COMMUNICATION"),
]


X_POSITIONS = [
    131,
    212.5,
    294,
    375.5,
    452,
    533.5,
    615,
    696.5,
]


def get_row(
    words,
    top,
    offset,
    tolerance=3.5
):

    target = top + offset

    return [
        word
        for word in words
        if abs(
            word["top"] - target
        ) < tolerance
    ]


def get_subject_values(
    words,
    top,
    offset,
    tolerance=3.5
):

    row = get_row(
        words,
        top,
        offset,
        tolerance
    )

    values = []

    for x_position in X_POSITIONS:

        candidates = [
            word
            for word in row
            if abs(
                word["x0"] - x_position
            ) < 14
        ]

        if candidates:

            closest = min(
                candidates,
                key=lambda word:
                abs(
                    word["x0"] - x_position
                )
            )

            values.append(
                closest["text"].strip()
            )

        else:

            values.append("")

    return values


def get_student_name(
    words,
    student_top
):

    header_words = [
        word
        for word in words
        if abs(
            word["top"] - student_top
        ) < 2
        and 105 <= word["x0"] < 260
    ]

    header_words = sorted(
        header_words,
        key=lambda word:
        word["x0"]
    )

    name_parts = []

    for word in header_words:

        text = word["text"].strip()

        if text == "06782":
            break

        if re.fullmatch(
            r"\d{14,15}",
            text
        ):
            continue

        if text.upper() in [
            "PASS",
            "FAIL"
        ]:
            continue

        name_parts.append(text)


    name = " ".join(
        name_parts
    )


    name = re.sub(
        r"^\(F\)\s*",
        "",
        name,
        flags=re.IGNORECASE
    )


    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()


    return name


def get_result(
    words,
    student_top
):

    result_words = [
        word
        for word in words
        if abs(
            word["top"] - student_top
        ) < 3
        and word["x0"] > 1450
        and word["text"].upper().strip()
        in [
            "PASS",
            "FAIL"
        ]
    ]

    if result_words:

        return (
            result_words[0]["text"]
            .upper()
            .strip()
        )

    return ""


def get_sgpa(
    words,
    student_top
):

    row = get_row(
        words,
        student_top,
        10.8,
        4
    )

    candidates = [
        word
        for word in row
        if word["x0"] > 1250
    ]

    numeric_candidates = []

    for word in candidates:

        value = word["text"].strip()

        if re.fullmatch(
            r"\d+(?:\.\d+)?",
            value
        ):

            number = float(value)

            if 0 <= number <= 10:

                numeric_candidates.append(
                    word
                )


    if numeric_candidates:

        return numeric_candidates[0][
            "text"
        ].strip()


    if candidates:

        return candidates[0][
            "text"
        ].strip()


    return ""


def get_summary_value(
    words,
    student_top,
    offset,
    minimum_x,
    maximum_x=None
):

    row = get_row(
        words,
        student_top,
        offset,
        4
    )

    candidates = []

    for word in row:

        x = word["x0"]

        if x >= minimum_x:

            if (
                maximum_x is None
                or x < maximum_x
            ):

                candidates.append(
                    word
                )


    if candidates:

        candidates = sorted(
            candidates,
            key=lambda word:
            word["x0"]
        )

        return candidates[0][
            "text"
        ].strip()


    return ""


def extract_university_result(
    pdf_path
):

    records = []


    with pdfplumber.open(
        pdf_path
    ) as pdf:

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=2,
                keep_blank_chars=False
            )


            seat_numbers = [
                word
                for word in words
                if re.fullmatch(
                    r"\d{14,15}",
                    word["text"].strip()
                )
            ]


            for seat in seat_numbers:

                seat_number = (
                    seat["text"].strip()
                )

                student_top = seat["top"]


                student_name = get_student_name(
                    words,
                    student_top
                )


                result = get_result(
                    words,
                    student_top
                )


                sgpa = get_sgpa(
                    words,
                    student_top
                )


                total_grade_point = (
                    get_summary_value(
                        words,
                        student_top,
                        27.7,
                        1250,
                        1450
                    )
                )


                total_credit = (
                    get_summary_value(
                        words,
                        student_top,
                        27.7,
                        1450
                    )
                )


                total_marks = (
                    get_summary_value(
                        words,
                        student_top,
                        42,
                        1450
                    )
                )


                ese = get_subject_values(
                    words,
                    student_top,
                    10.8
                )


                ca = get_subject_values(
                    words,
                    student_top,
                    27.7
                )


                mid = get_subject_values(
                    words,
                    student_top,
                    48
                )


                total = get_subject_values(
                    words,
                    student_top,
                    85
                )


                grade = get_subject_values(
                    words,
                    student_top,
                    105
                )


                record = {

                    "Seat No":
                        seat_number,

                    "Student Name":
                        student_name,

                    "Result":
                        result,

                    "SGPA":
                        sgpa,

                    "Total Grade Point":
                        total_grade_point,

                    "Total Credit":
                        total_credit,

                    "Total Marks":
                        total_marks,

                    "Page":
                        page_number
                }


                for index, (
                    subject_code,
                    subject_name
                ) in enumerate(
                    SUBJECTS
                ):

                    record[
                        f"{subject_code} ESE"
                    ] = ese[index]


                    record[
                        f"{subject_code} CA Internal"
                    ] = ca[index]


                    record[
                        f"{subject_code} Mid Internal"
                    ] = mid[index]


                    record[
                        f"{subject_code} Total"
                    ] = total[index]


                    record[
                        f"{subject_code} Grade"
                    ] = grade[index]


                records.append(
                    record
                )


    dataframe = pd.DataFrame(
        records
    )


    if dataframe.empty:

        raise ValueError(
            "No student records were found in the PDF."
        )


    # Remove duplicate seat numbers
    dataframe = dataframe.drop_duplicates(
        subset=["Seat No"],
        keep="first"
    ).reset_index(
        drop=True
    )


    # Convert numeric fields
    numeric_columns = [
        "SGPA",
        "Total Grade Point",
        "Total Credit",
        "Total Marks"
    ]


    for column in numeric_columns:

        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce"
        )


    # ========================================================
    # PERCENTAGE
    # ========================================================

    dataframe["Percentage"] = pd.NA


    valid_marks = (
        dataframe["Total Marks"].notna()
    )


    dataframe.loc[
        valid_marks,
        "Percentage"
    ] = (
        dataframe.loc[
            valid_marks,
            "Total Marks"
        ]
        / 700
        * 100
    ).round(2)


    dataframe["Percentage"] = pd.to_numeric(
        dataframe["Percentage"],
        errors="coerce"
    )


    return dataframe


def extract_pdf(
    pdf_path
):

    return extract_university_result(
        pdf_path
    )


