import streamlit as st
import pandas as pd
from utils import (
    validate_phone_number, get_phone_info, get_location_map, 
    generate_report, generate_pdf_report,
    get_ip_info, get_ip_location_map, generate_ip_report, generate_ip_pdf_report
)
import streamlit.components.v1 as components
from datetime import datetime
import base64

# Country codes data
country_codes = pd.DataFrame([
    {"country": "Afghanistan", "code": "93"},
    {"country": "Albania", "code": "355"},
    {"country": "Algeria", "code": "213"},
    {"country": "Andorra", "code": "376"},
    {"country": "Angola", "code": "244"},
    {"country": "Argentina", "code": "54"},
    {"country": "Armenia", "code": "374"},
    {"country": "Australia", "code": "61"},
    {"country": "Austria", "code": "43"},
    {"country": "Azerbaijan", "code": "994"},
    {"country": "Bahrain", "code": "973"},
    {"country": "Bangladesh", "code": "880"},
    {"country": "Belarus", "code": "375"},
    {"country": "Belgium", "code": "32"},
    {"country": "Bhutan", "code": "975"},
    {"country": "Bolivia", "code": "591"},
    {"country": "Brazil", "code": "55"},
    {"country": "Bulgaria", "code": "359"},
    {"country": "Canada", "code": "1"},
    {"country": "Chile", "code": "56"},
    {"country": "China", "code": "86"},
    {"country": "Colombia", "code": "57"},
    {"country": "Costa Rica", "code": "506"},
    {"country": "Croatia", "code": "385"},
    {"country": "Cuba", "code": "53"},
    {"country": "Cyprus", "code": "357"},
    {"country": "Czech Republic", "code": "420"},
    {"country": "Denmark", "code": "45"},
    {"country": "Egypt", "code": "20"},
    {"country": "Estonia", "code": "372"},
    {"country": "Finland", "code": "358"},
    {"country": "France", "code": "33"},
    {"country": "Germany", "code": "49"},
    {"country": "Greece", "code": "30"},
    {"country": "Hong Kong", "code": "852"},
    {"country": "Hungary", "code": "36"},
    {"country": "India", "code": "91"},
    {"country": "Indonesia", "code": "62"},
    {"country": "Iran", "code": "98"},
    {"country": "Iraq", "code": "964"},
    {"country": "Ireland", "code": "353"},
    {"country": "Israel", "code": "972"},
    {"country": "Italy", "code": "39"},
    {"country": "Japan", "code": "81"},
    {"country": "Jordan", "code": "962"},
    {"country": "Kazakhstan", "code": "7"},
    {"country": "Kenya", "code": "254"},
    {"country": "Kuwait", "code": "965"},
    {"country": "Latvia", "code": "371"},
    {"country": "Lebanon", "code": "961"},
    {"country": "Libya", "code": "218"},
    {"country": "Malaysia", "code": "60"},
    {"country": "Maldives", "code": "960"},
    {"country": "Mexico", "code": "52"},
    {"country": "Netherlands", "code": "31"},
    {"country": "New Zealand", "code": "64"},
    {"country": "Nigeria", "code": "234"},
    {"country": "North Korea", "code": "850"},
    {"country": "Norway", "code": "47"},
    {"country": "Oman", "code": "968"},
    {"country": "Pakistan", "code": "92"},
    {"country": "Palestine", "code": "970"},
    {"country": "Peru", "code": "51"},
    {"country": "Philippines", "code": "63"},
    {"country": "Poland", "code": "48"},
    {"country": "Portugal", "code": "351"},
    {"country": "Qatar", "code": "974"},
    {"country": "Romania", "code": "40"},
    {"country": "Russia", "code": "7"},
    {"country": "Saudi Arabia", "code": "966"},
    {"country": "Serbia", "code": "381"},
    {"country": "Singapore", "code": "65"},
    {"country": "South Africa", "code": "27"},
    {"country": "South Korea", "code": "82"},
    {"country": "Spain", "code": "34"},
    {"country": "Sri Lanka", "code": "94"},
    {"country": "Sweden", "code": "46"},
    {"country": "Switzerland", "code": "41"},
    {"country": "Syria", "code": "963"},
    {"country": "Taiwan", "code": "886"},
    {"country": "Thailand", "code": "66"},
    {"country": "Turkey", "code": "90"},
    {"country": "UAE", "code": "971"},
    {"country": "UK", "code": "44"},
    {"country": "USA", "code": "1"},
    {"country": "Ukraine", "code": "380"},
    {"country": "Vietnam", "code": "84"},
    {"country": "Yemen", "code": "967"},
    {"country": "Zimbabwe", "code": "263"}
])

# Page configuration
st.set_page_config(
    page_title="Tamizh-AI Finder | S.Tamilselvan",
    page_icon="📱",
    layout="wide"
)

# Load custom CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Title and description
st.title("📱 Tamizh-AI Finder | S.Tamilselvan")
st.markdown("Track mobile numbers and IP addresses to find their approximate locations")

# Initialize session state
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'reports' not in st.session_state:
    st.session_state.reports = {}
if 'ip_search_history' not in st.session_state:
    st.session_state.ip_search_history = []
if 'ip_reports' not in st.session_state:
    st.session_state.ip_reports = {}

# Sidebar with combined history
with st.sidebar:
    st.header("Search History")

    # Phone number history
    st.subheader("📞 Phone Numbers")
    if st.session_state.search_history:
        for number in st.session_state.search_history:
            if st.button(f"📞 {number}", key=f"history_{number}"):
                if number in st.session_state.reports:
                    st.text_area("Previous Report", 
                                st.session_state.reports[number],
                                height=300)
    else:
        st.info("No recent phone searches")

    # IP address history
    st.subheader("🌐 IP Addresses")
    if st.session_state.ip_search_history:
        for ip in st.session_state.ip_search_history:
            if st.button(f"🌐 {ip}", key=f"ip_history_{ip}"):
                if ip in st.session_state.ip_reports:
                    st.text_area("Previous Report", 
                                st.session_state.ip_reports[ip],
                                height=300)
    else:
        st.info("No recent IP searches")

# Main content tabs
tab1, tab2 = st.tabs(["📞 Phone Number Lookup", "🌐 IP Address Lookup"])

with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        # Input section
        st.subheader("Enter Mobile Number Details")

        # Country selection with search
        selected_country = st.selectbox(
            "Select Country",
            options=country_codes["country"].tolist(),
            index=int(country_codes[country_codes["country"] == "India"].index[0]),
            help="Search and select your country"
        )

        # Get country code
        country_code = country_codes[country_codes["country"] == selected_country]["code"].iloc[0]

        # Phone number input
        phone_number = st.text_input(
            "Enter Mobile Number",
            placeholder=f"Enter number without country code (e.g., 9876543210)"
        )

        if st.button("Track Number", type="primary"):
            if phone_number:
                # Validate number
                is_valid, formatted_number = validate_phone_number(phone_number, country_code)

                if is_valid:
                    # Add to search history
                    if formatted_number not in st.session_state.search_history:
                        st.session_state.search_history.insert(0, formatted_number)
                        if len(st.session_state.search_history) > 5:
                            st.session_state.search_history.pop()

                    # Get phone information
                    phone_info = get_phone_info(formatted_number)

                    # Generate timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Generate and store report
                    report = generate_report(phone_info, timestamp)
                    st.session_state.reports[formatted_number] = report

                    # Display results
                    st.markdown("### Results")

                    # Display metrics in three rows
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Country", phone_info["country"])
                    with col_info2:
                        st.metric("State", phone_info["state"])
                    with col_info3:
                        st.metric("District", phone_info["district"])

                    col_info4, col_info5, col_info6 = st.columns(3)
                    with col_info4:
                        st.metric("City", phone_info["city"])
                    with col_info5:
                        st.metric("Carrier", phone_info["carrier"])
                    with col_info6:
                        st.metric("Timezone", phone_info["timezone"])

                    col_info7, col_info8, col_info9 = st.columns(3)
                    with col_info7:
                        st.metric("Valid Number", "Yes" if phone_info["is_valid"] else "No")
                    with col_info8:
                        st.metric("Formatted Number", phone_info["formatted_number"])
                    with col_info9:
                        if phone_info["latitude"] and phone_info["longitude"]:
                            st.metric("Coordinates", f"{phone_info['latitude']:.4f}, {phone_info['longitude']:.4f}")

                    # Display detailed report
                    with st.expander("📄 View Detailed Report", expanded=True):
                        st.text(report)

                        # Generate and provide PDF download
                        pdf_path = generate_pdf_report(phone_info, timestamp)
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"phone_report_{formatted_number}_{timestamp.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )

                    # Generate and display map
                    if phone_info["country"] != "Unknown":
                        st.markdown("### 🗺️ Location Map")
                        map_data = get_location_map(phone_info)
                        if map_data:
                            # Generate and save map HTML
                            map_path = f"phone_{formatted_number}_map.html"
                            map_data.save(map_path)
                            
                            # Display map
                            map_html = map_data._repr_html_()
                            components.html(map_html, height=400)
                            
                            # Add download button for HTML map
                            with open(map_path, "rb") as map_file:
                                map_bytes = map_file.read()
                                st.download_button(
                                    label="📥 Download Location Map",
                                    data=map_bytes,
                                    file_name=map_path,
                                    mime="text/html"
                                )

                            # Add map legend
                            st.markdown("""
                            **Map Legend:**
                            - 📍 Red Marker: Approximate Location
                            - 🔴 Red Circle: Potential Area (50km radius)
                            """)
                else:
                    st.error("Invalid phone number format. Please check and try again.")
            else:
                st.warning("Please enter a phone number.")

    with col2:
        st.markdown("""
        ### How to use
        1. Select the country from the dropdown
        2. Enter the mobile number without country code
        3. Click "Track Number" to get details

        ### Features
        - Country and region detection
        - State and district information
        - Carrier information
        - Timezone details
        - Interactive map visualization
        - Detailed PDF reports
        - Search history tracking
        """)


with tab2:
    st.subheader("Enter IP Address Details")

    # IP address input
    ip_address = st.text_input(
        "Enter IP Address",
        placeholder="Enter IP address (e.g., 8.8.8.8)"
    )

    if st.button("Track IP", type="primary"):
        if ip_address:
            # Get IP information
            ip_info = get_ip_info(ip_address)

            # Generate timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Add to search history
            if ip_address not in st.session_state.ip_search_history:
                st.session_state.ip_search_history.insert(0, ip_address)
                if len(st.session_state.ip_search_history) > 5:
                    st.session_state.ip_search_history.pop()

            # Generate and store report
            report = generate_ip_report(ip_info, timestamp)
            st.session_state.ip_reports[ip_address] = report

            # Display results
            st.markdown("### Results")

            # Display metrics in three rows
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("IP Address", ip_info["ip"])
            with col_info2:
                st.metric("Country", ip_info["country"])
            with col_info3:
                st.metric("Region", ip_info["region"])

            col_info4, col_info5, col_info6 = st.columns(3)
            with col_info4:
                st.metric("City", ip_info["city"])
            with col_info5:
                st.metric("ISP", ip_info["isp"])
            with col_info6:
                st.metric("Timezone", ip_info["timezone"])

            col_info7, col_info8, col_info9 = st.columns(3)
            with col_info7:
                st.metric("Organization", ip_info["org"])
            with col_info8:
                st.metric("ASN", ip_info["asn"])
            with col_info9:
                if ip_info["latitude"] and ip_info["longitude"]:
                    st.metric("Coordinates", f"{ip_info['latitude']:.4f}, {ip_info['longitude']:.4f}")

            # Display detailed report
            with st.expander("📄 View Detailed Report", expanded=True):
                st.text(report)

                # Generate and provide PDF download
                pdf_path = generate_ip_pdf_report(ip_info, timestamp)
                with open(pdf_path, "rb") as pdf_file:
                    pdf_bytes = pdf_file.read()
                st.download_button(
                    label="📥 Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"ip_report_{ip_address}_{timestamp.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

            # Generate and display map
            if ip_info["country"] != "Unknown":
                st.markdown("### 🗺️ Location Map")
                map_data = get_ip_location_map(ip_info)
                if map_data:
                    map_html = map_data._repr_html_()
                    components.html(map_html, height=400)

                    # Add map legend
                    st.markdown("""
                    **Map Legend:**
                    - 📍 Red Marker: Approximate Location
                    - 🔴 Red Circle: Potential Area (50km radius)
                    """)
        else:
            st.warning("Please enter an IP address.")

# Information box
st.sidebar.markdown("""
### How to use
1. Choose the lookup type (Phone or IP)
2. Enter the number or IP address
3. Click "Track" to get details

### Features
- Phone number tracking
- IP address lookup
- Location mapping
- Detailed PDF reports
- Search history
""")

# Footer
st.markdown("---")
st.markdown(
    """
    <style>
        .custom-button {
            display: inline-block;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: bold;
            color: white !important;
            background: linear-gradient(45deg, #ff416c, #ff4b2b);
            border-radius: 12px;
            text-decoration: none !important;
            transition: 0.3s;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        }
        .custom-button:hover, 
        .custom-button:focus, 
        .custom-button:visited, 
        .custom-button:active {
            background: linear-gradient(45deg, #ff4b2b, #ff416c);
            transform: scale(1.05);
            text-decoration: none !important;
            color: white !important;
        }
    </style>
    <a class="custom-button" href="https://tamilselvan-portfolio-s.web.app/" target="_blank">
        Created by Cyber Security Researcher S.Tamilselvan
    </a>
    """,
    unsafe_allow_html=True
)