import os
import tempfile

import pandas as pd
import streamlit as st

from pdf_processor import extract_university_result
from excel_generator import create_excel


st.set_page_config(
    page_title="University Result PDF to Excel",
    page_icon="🎓",
    layout="wide",
)


st.title("🎓 University Result PDF → Excel Converter")

st.write(
    "Upload a university result PDF and convert student results into Excel."
)

st.info(
    "Students are automatically ranked by Percentage. "
    "Rank 1 is the highest percentage. "
    "Use the search box to search by Rank, Seat No., or Student Name."
)


# ============================================================
# RANKING FUNCTION
# ============================================================

def create_rank(dataframe):

    df = dataframe.copy()

    # Remove Rank if PDF processor already created it
    if "Rank" in df.columns:
        df = df.drop(columns=["Rank"])

    # Make sure Percentage exists
    if "Percentage" not in df.columns:
        df["Percentage"] = pd.NA

    # Convert Percentage to numeric
    percentage = pd.to_numeric(
        df["Percentage"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce"
    )

    df["_percentage"] = percentage

    # Highest percentage first
    df = df.sort_values(
        by="_percentage",
        ascending=False,
        na_position="last",
        kind="stable"
    ).reset_index(drop=True)

    # Create Rank
    df["Rank"] = pd.NA

    valid = df["_percentage"].notna()

    if valid.any():

        df.loc[valid, "Rank"] = (
            df.loc[valid, "_percentage"]
            .rank(
                method="min",
                ascending=False
            )
            .astype("Int64")
        )

    df["Rank"] = df["Rank"].astype("Int64")

    # Remove temporary column
    df = df.drop(
        columns=["_percentage"]
    )

    # Put Rank at first position
    columns = list(df.columns)

    columns.remove("Rank")

    df = df[
        ["Rank"] + columns
    ]

    return df


# ============================================================
# UPLOAD PDF
# ============================================================

uploaded_file = st.file_uploader(
    "📄 Upload University Result PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    file_size = (
        len(uploaded_file.getbuffer()) / 1024
    )

    st.write(
        f"File size: {file_size:.2f} KB"
    )


    # ========================================================
    # CONVERT BUTTON
    # ========================================================

    if st.button(
        "🚀 Convert PDF to Excel",
        type="primary",
        use_container_width=True
    ):

        pdf_path = None

        try:

            # Save uploaded PDF temporarily
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".pdf"
            ) as temp_pdf:

                temp_pdf.write(
                    uploaded_file.getbuffer()
                )

                pdf_path = temp_pdf.name


            # Extract PDF
            with st.spinner(
                "🔍 Reading PDF and extracting student results..."
            ):

                dataframe = extract_university_result(
                    pdf_path
                )


            if dataframe is None or dataframe.empty:

                st.error(
                    "❌ No student records were extracted."
                )

                st.stop()


            # Remove completely empty rows
            dataframe = dataframe.dropna(
                how="all"
            ).reset_index(drop=True)


            # Create percentage if not present
            if "Percentage" not in dataframe.columns:

                dataframe["Percentage"] = pd.NA


            # Create Rank
            dataframe = create_rank(
                dataframe
            )


            # Save result
            st.session_state[
                "result_dataframe"
            ] = dataframe

            st.session_state[
                "source_filename"
            ] = uploaded_file.name


            st.success(
                f"✅ Successfully extracted "
                f"{len(dataframe)} student records!"
            )


        except Exception as error:

            st.error(
                "❌ An error occurred while converting the PDF."
            )

            st.exception(error)


        finally:

            if (
                pdf_path is not None
                and os.path.exists(pdf_path)
            ):

                os.remove(pdf_path)


# ============================================================
# DISPLAY RESULTS
# ============================================================

if "result_dataframe" in st.session_state:

    dataframe = st.session_state[
        "result_dataframe"
    ].copy()


    # ========================================================
    # SUMMARY
    # ========================================================

    st.subheader(
        "📊 Result Summary"
    )


    col1, col2, col3, col4, col5 = st.columns(5)


    with col1:

        st.metric(
            "Total Students",
            len(dataframe)
        )


    with col2:

        if "Result" in dataframe.columns:

            pass_count = (
                dataframe["Result"]
                .astype(str)
                .str.upper()
                .str.strip()
                .eq("PASS")
                .sum()
            )

        else:

            pass_count = 0

        st.metric(
            "PASS",
            int(pass_count)
        )


    with col3:

        if "Result" in dataframe.columns:

            fail_count = (
                dataframe["Result"]
                .astype(str)
                .str.upper()
                .str.strip()
                .eq("FAIL")
                .sum()
            )

        else:

            fail_count = 0

        st.metric(
            "FAIL",
            int(fail_count)
        )


    with col4:

        if "SGPA" in dataframe.columns:

            sgpa_values = pd.to_numeric(
                dataframe["SGPA"],
                errors="coerce"
            )

            average_sgpa = (
                sgpa_values.mean()
            )

        else:

            average_sgpa = None


        st.metric(
            "Average SGPA",
            (
                f"{average_sgpa:.2f}"
                if pd.notna(average_sgpa)
                else "N/A"
            )
        )


    with col5:

        if "Percentage" in dataframe.columns:

            percentage_values = pd.to_numeric(
                dataframe["Percentage"],
                errors="coerce"
            )

            average_percentage = (
                percentage_values.mean()
            )

        else:

            average_percentage = None


        st.metric(
            "Average Percentage",
            (
                f"{average_percentage:.2f}%"
                if pd.notna(average_percentage)
                else "N/A"
            )
        )


    # ========================================================
    # SEARCH
    # ========================================================

    st.subheader(
        "🔎 Search Student"
    )


    search_text = st.text_input(
        "Search by Rank, Seat No., or Student Name",
        placeholder="Enter rank, seat number, or student name..."
    )


    if search_text.strip():

        search_value = (
            search_text
            .strip()
            .lower()
        )


        # Rank
        rank_match = (
            dataframe["Rank"]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False,
                regex=False
            )
        )


        # Seat Number
        if "Seat No" in dataframe.columns:

            seat_match = (
                dataframe["Seat No"]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    na=False,
                    regex=False
                )
            )

        else:

            seat_match = pd.Series(
                False,
                index=dataframe.index
            )


        # Student Name
        if "Student Name" in dataframe.columns:

            name_match = (
                dataframe["Student Name"]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    na=False,
                    regex=False
                )
            )

        else:

            name_match = pd.Series(
                False,
                index=dataframe.index
            )


        filtered_dataframe = dataframe[
            rank_match
            | seat_match
            | name_match
        ].copy()


    else:

        filtered_dataframe = dataframe.copy()


    st.write(
        f"Showing {len(filtered_dataframe)} "
        f"of {len(dataframe)} student records."
    )


    # ========================================================
    # TABLE
    # ========================================================

    st.subheader(
        "📋 Student Results"
    )


    st.dataframe(
        filtered_dataframe,
        use_container_width=True,
        height=550,
        hide_index=True
    )


    # ========================================================
    # DOWNLOAD EXCEL
    # ========================================================

    st.subheader(
        "📥 Download Excel"
    )


    excel_path = None


    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".xlsx"
        ) as temp_excel:

            excel_path = temp_excel.name


        with st.spinner(
            "📊 Creating Excel file..."
        ):

            create_excel(
                dataframe,
                excel_path
            )


        with open(
            excel_path,
            "rb"
        ) as excel_file:

            excel_data = excel_file.read()


        st.success(
            "✅ Excel file created successfully!"
        )


        st.download_button(
            label="📥 Download University Result Excel",
            data=excel_data,
            file_name="University_Result_Ranked.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )


    except Exception as error:

        st.error(
            "❌ Unable to create Excel file."
        )

        st.exception(error)


    finally:

        if (
            excel_path is not None
            and os.path.exists(excel_path)
        ):

            os.remove(excel_path)


else:

    st.write(
        "👆 Please upload a PDF file to begin."
    )


st.markdown("---")

st.caption(
    "University Result PDF → Excel Converter | Final Year Project"
)

