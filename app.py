import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configure the page
st.set_page_config(
    page_title="CH-161 Marks Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("📊 CH-161 Occupational Health and Safety - Marks Dashboard")
st.markdown("Enter your registration number to view your marks and class statistics.")


@st.cache_data
def load_data():
    """Load and process data from the CSV file"""
    try:
        # Try different possible file names
        csv_files = [
            "CH-161 Mid and Quiz Marks-Fall 2025 Sec A-E & J_3rd Nov 2025.csv",
            "data.csv"
        ]

        df = None
        used_file = None

        for file_name in csv_files:
            if os.path.exists(file_name):
                try:
                    # Read the CSV file with error handling
                    df = pd.read_csv(file_name)

                    # Debug: Show what columns we actually have
                    #st.sidebar.write("Raw columns:", list(df.columns))
                    #st.sidebar.write("DataFrame shape:", df.shape)

                    used_file = file_name
                    st.sidebar.success(f"✓ Loaded: {file_name}")
                    break
                except Exception as e:
                    st.sidebar.error(f"Error reading {file_name}: {str(e)}")
                    continue

        if df is None:
            st.error("❌ CSV file not found. Please make sure the CSV file is in the same directory as this script.")
            st.info("""
            **Troubleshooting tips:**
            1. Make sure your CSV file is named: `CH-161 Mid and Quiz Marks-Fall 2025 Sec A-E & J_3rd Nov 2025.csv`
            2. Place the CSV file in the same folder as this Python script
            3. Check that the file is not open in Excel or another program
            """)
            return pd.DataFrame(), pd.DataFrame()

        # Display file info
        #st.sidebar.write(f"**File loaded:** {used_file}")
        #st.sidebar.write(f"**Total records:** {len(df)}")

        # Show the first few rows for debugging
        #st.sidebar.write("First few rows:")
        #st.sidebar.write(df.head())

        # Clean column names (remove any extra spaces and special characters)
        df.columns = df.columns.str.strip()

        # Show available columns for debugging
        #st.sidebar.write("**Columns found:**", list(df.columns))

        # Check what columns we actually have and map them
        column_mapping = {}
        available_columns = list(df.columns)

        # Try to find the correct columns
        expected_columns = {
            'REG#': ['REG#', 'REG', 'Registration', 'Registration Number'],
            'Quiz Marks (Out of 10)': ['Quiz Marks (Out of 10)', 'Quiz Marks', 'Quiz'],
            'Mid Marks (Out of 40)': ['Mid Marks  (Out of 40)', 'Mid Marks', 'Mid'],
            'Total Marks': ['Total Marks', 'Total', 'Total Marks '],
            '%': ['%', 'Percentage', 'Percent'],
            'Section': ['Section', 'Sec', 'Group']
        }

        # Map available columns to expected names
        for expected_name, possible_names in expected_columns.items():
            for possible_name in possible_names:
                if possible_name in available_columns:
                    column_mapping[possible_name] = expected_name
                    break

        # If we found matches, rename the columns
        if column_mapping:
            df = df.rename(columns=column_mapping)
            #st.sidebar.write("After column mapping:", list(df.columns))

        # Check if we have the essential columns
        essential_columns = ['REG#', 'Total Marks', 'Section']
        missing_essential = [col for col in essential_columns if col not in df.columns]

        if missing_essential:
            st.error(f"❌ Missing essential columns: {missing_essential}")
            st.info(f"Available columns are: {list(df.columns)}")
            return pd.DataFrame(), pd.DataFrame()

        # Clean the data
        # Remove any rows with missing registration numbers
        df = df[df['REG#'].notna() & (df['REG#'].astype(str).str.strip() != '')]

        # Convert REG# to string for consistent searching
        df['REG#'] = df['REG#'].astype(str).str.strip()

        # Clean section names
        if 'Section' in df.columns:
            df['Section'] = df['Section'].astype(str).str.strip()
        else:
            # If no section column, create a dummy one
            df['Section'] = 'Unknown'

        # Ensure numeric columns are properly formatted
        numeric_columns = ['Quiz Marks (Out of 10)', 'Mid Marks (Out of 40)', 'Total Marks']
        for col in numeric_columns:
            if col in df.columns:
                # Convert to string first to handle any formatting issues, then to numeric
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

        # Handle percentage column if it exists
        if '%' in df.columns:
            df['%'] = df['%'].astype(str).str.replace('%', '').str.strip()
            df['%'] = pd.to_numeric(df['%'], errors='coerce')
        else:
            # Calculate percentage from total marks if not available
            df['%'] = (df['Total Marks'] / 50) * 100

        # Calculate ranks
        df['Overall Rank'] = df['Total Marks'].rank(ascending=False, method='min').astype(int)
        df['Rank in Section'] = df.groupby('Section')['Total Marks'].rank(ascending=False, method='min').astype(int)

        # Calculate section statistics
        section_stats = df.groupby('Section').agg({
            'Total Marks': ['count', 'mean', 'max', 'min']
        }).round(2)

        # Flatten the column names
        section_stats.columns = ['Student Count', 'Average Marks', 'Highest Marks', 'Lowest Marks']
        section_stats = section_stats.reset_index()

        st.sidebar.success("✓ Data processed successfully!")
        return df, section_stats

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        import traceback
        st.sidebar.error(f"Detailed error: {traceback.format_exc()}")
        return pd.DataFrame(), pd.DataFrame()


# Load data
df, section_stats = load_data()

# Rest of your existing code continues here...
# [The rest of your code remains the same as in the previous version]

# Sidebar for registration number input
st.sidebar.header("🔍 Student Search")
st.sidebar.markdown("Enter your registration number below:")

# Only show the input if data is loaded
if not df.empty:
    reg_number = st.sidebar.text_input(
        "Registration Number:",
        placeholder="e.g., 2025360",
        key="reg_input"
    )

    # Display sample registration numbers for testing
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Sample Registration Numbers")

    # Get samples from each section
    samples = []
    for section in sorted(df['Section'].unique()):
        section_sample = df[df['Section'] == section].head(2)
        samples.extend(section_sample['REG#'].tolist())

    for reg in samples[:8]:  # Show max 8 samples
        if st.sidebar.button(f"📝 {reg}", key=f"sample_{reg}"):
            st.session_state.reg_input = reg
            st.rerun()

# Main content area
if not df.empty:
    # Check if we have a registration number to search for
    reg_number_to_search = reg_number if 'reg_number' in locals() else None

    # If we're using session state (from sample buttons)
    if 'reg_input' in st.session_state and st.session_state.reg_input:
        reg_number_to_search = st.session_state.reg_input

    if reg_number_to_search and reg_number_to_search.strip():
        # Search for student
        student_data = df[df['REG#'] == reg_number_to_search.strip()]

        if not student_data.empty:
            student = student_data.iloc[0]
            section = student['Section']
            overall_rank = student['Overall Rank']
            section_rank = student['Rank in Section']
            total_students = len(df)
            section_students = len(df[df['Section'] == section])

            st.success(f"✅ Marks found for Registration Number: {reg_number_to_search}")

            # Create columns for student info and marks
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("👤 Student Details")
                st.write(f"**Registration Number:** {student['REG#']}")
                st.write(f"**Section:** {section}")

                st.subheader("📊 Marks Summary")
                if 'Quiz Marks (Out of 10)' in df.columns:
                    st.write(f"**Quiz Marks:** {student['Quiz Marks (Out of 10)']:.2f}/10")
                if 'Mid Marks (Out of 40)' in df.columns:
                    st.write(f"**Mid Marks:** {student['Mid Marks (Out of 40)']:.2f}/40")
                st.write(f"**Total Marks:** {student['Total Marks']:.2f}/50")
                st.write(f"**Percentage:** {student['%']:.2f}%")

                st.subheader("🏆 Ranking")
                st.write(f"**Overall Rank:** {overall_rank} out of {total_students} students")
                st.write(f"**Section Rank:** {section_rank} out of {section_students} students")

                # Performance indicator
                overall_percentile = ((total_students - overall_rank) / total_students) * 100
                section_percentile = ((section_students - section_rank) / section_students) * 100

                st.subheader("📈 Performance Percentile")
                st.write(f"**Overall:** Top {overall_percentile:.1f}% of class")
                st.write(f"**In Section {section}:** Top {section_percentile:.1f}%")

            with col2:
                # Marks visualization
                fig_marks = go.Figure()

                categories = []
                student_scores = []

                if 'Quiz Marks (Out of 10)' in df.columns:
                    categories.append('Quiz (Out of 10)')
                    student_scores.append(student['Quiz Marks (Out of 10)'])

                if 'Mid Marks (Out of 40)' in df.columns:
                    categories.append('Mid (Out of 40)')
                    student_scores.append(student['Mid Marks (Out of 40)'])

                categories.append('Total (Out of 50)')
                student_scores.append(student['Total Marks'])

                percentages = []
                for i, score in enumerate(student_scores):
                    if categories[i] == 'Quiz (Out of 10)':
                        percentages.append((score / 10) * 100)
                    elif categories[i] == 'Mid (Out of 40)':
                        percentages.append((score / 40) * 100)
                    else:
                        percentages.append(student['%'])

                if categories:  # Only create chart if we have data
                    fig_marks.add_trace(go.Bar(
                        name='Your Score',
                        x=categories,
                        y=student_scores,
                        text=[f'{score:.1f}<br>({pct:.1f}%)' for score, pct in zip(student_scores, percentages)],
                        textposition='auto',
                        marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(categories)]
                    ))

                    fig_marks.update_layout(
                        title="Your Marks Breakdown",
                        yaxis_title="Marks",
                        showlegend=False,
                        height=400
                    )

                    st.plotly_chart(fig_marks, use_container_width=True)

                # Rank visualization
                fig_rank = go.Figure()

                rank_categories = ['Overall Rank', 'Section Rank']
                rank_values = [overall_rank, section_rank]
                total_counts = [total_students, section_students]

                fig_rank.add_trace(go.Bar(
                    x=rank_categories,
                    y=[total_students - overall_rank, section_students - section_rank],
                    name='Students Below You',
                    marker_color='lightgreen',
                    text=[f'Rank: {overall_rank}', f'Rank: {section_rank}'],
                    textposition='auto'
                ))

                fig_rank.add_trace(go.Bar(
                    x=rank_categories,
                    y=[overall_rank - 1, section_rank - 1],
                    name='Students Above You',
                    marker_color='lightcoral'
                ))

                fig_rank.update_layout(
                    title="Ranking Position",
                    yaxis_title="Number of Students",
                    barmode='stack',
                    height=300
                )

                st.plotly_chart(fig_rank, use_container_width=True)

            # Section comparison and statistics
            st.subheader("📊 Section and Class Statistics")

            col1, col2 = st.columns(2)

            with col1:
                # Section statistics
                section_data = df[df['Section'] == section]

                st.write(f"**Section {section} Statistics:**")
                st.write(f"- Number of Students: {len(section_data)}")
                st.write(f"- Average Total Marks: {section_data['Total Marks'].mean():.2f}")
                st.write(f"- Highest Total Marks: {section_data['Total Marks'].max():.2f}")
                st.write(f"- Lowest Total Marks: {section_data['Total Marks'].min():.2f}")

                # Section distribution
                fig_section = px.histogram(
                    section_data,
                    x='Total Marks',
                    title=f"Section {section} - Marks Distribution",
                    nbins=15,
                    color_discrete_sequence=['#1f77b4']
                )
                fig_section.add_vline(
                    x=student['Total Marks'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Your Score",
                    annotation_position="top left"
                )
                fig_section.update_layout(showlegend=False)
                st.plotly_chart(fig_section, use_container_width=True)

            with col2:
                # Overall class statistics
                st.write("**Overall Class Statistics:**")
                st.write(f"- Total Students: {len(df)}")
                st.write(f"- Average Total Marks: {df['Total Marks'].mean():.2f}")
                st.write(f"- Highest Total Marks: {df['Total Marks'].max():.2f}")
                st.write(f"- Lowest Total Marks: {df['Total Marks'].min():.2f}")

                # Overall distribution
                fig_overall = px.histogram(
                    df,
                    x='Total Marks',
                    title="Overall Class - Marks Distribution",
                    nbins=20,
                    color_discrete_sequence=['#ff7f0e']
                )
                fig_overall.add_vline(
                    x=student['Total Marks'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Your Score",
                    annotation_position="top left"
                )
                fig_overall.update_layout(showlegend=False)
                st.plotly_chart(fig_overall, use_container_width=True)

        else:
            st.error("❌ No student found with this registration number. Please check your entry.")
            st.info("💡 Try clicking one of the sample registration numbers in the sidebar")

    else:
        # Show overall statistics when no registration number is entered
        st.info("👆 Enter your registration number in the sidebar to view your marks.")

        st.subheader("📊 Overall Class Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Students", len(df))

        with col2:
            st.metric("Average Total Marks", f"{df['Total Marks'].mean():.2f}")

        with col3:
            st.metric("Highest Total Marks", f"{df['Total Marks'].max():.2f}")

        with col4:
            st.metric("Lowest Total Marks", f"{df['Total Marks'].min():.2f}")

        # Overall distribution
        fig = px.histogram(
            df,
            x='Total Marks',
            title="Overall Class Marks Distribution",
            nbins=20,
            color_discrete_sequence=['#636efa']
        )
        st.plotly_chart(fig, use_container_width=True)

        # Section-wise performance
        st.subheader("📈 Section-wise Performance")

        col1, col2 = st.columns(2)

        with col1:
            fig_section_avg = px.bar(
                section_stats,
                x='Section',
                y='Average Marks',
                title="Average Marks by Section",
                color='Average Marks',
                color_continuous_scale='viridis'
            )
            st.plotly_chart(fig_section_avg, use_container_width=True)

        with col2:
            fig_section_count = px.pie(
                section_stats,
                values='Student Count',
                names='Section',
                title="Student Distribution by Section"
            )
            st.plotly_chart(fig_section_count, use_container_width=True)

        # Top 10 students
        st.subheader("🏆 Top 10 Students Overall")
        top_10 = df.nlargest(10, 'Total Marks')[['REG#', 'Section', 'Total Marks', '%', 'Overall Rank']]
        st.dataframe(top_10.style.format({'Total Marks': '{:.1f}', '%': '{:.1f}%'}))

else:
    st.warning("📁 Please make sure your CSV file is in the correct location and try again.")

# Footer
st.markdown("---")
st.markdown(
    "**Note:** This dashboard displays quiz and midterm marks for CH-161 Occupational Health and Safety. "
    "Final marks will be updated after the final exam."
)
