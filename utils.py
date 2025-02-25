import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import folium
import streamlit as st
from typing import Tuple, Dict, Optional
from datetime import datetime
from fpdf import FPDF
import tempfile
import os
import requests
from typing import Dict, Optional
import os
import tempfile


def validate_phone_number(phone_number: str, country_code: str) -> Tuple[bool, str]:
    """
    Validate the phone number format
    """
    try:
        if not phone_number.startswith('+'):
            phone_number = f"+{country_code}{phone_number}"
        parsed_number = phonenumbers.parse(phone_number)
        return phonenumbers.is_valid_number(parsed_number), phone_number
    except Exception as e:
        return False, str(e)

def get_detailed_location(country: str, region: str = None) -> Dict[str, str]:
    """
    Get detailed location information including state and district if available
    """
    try:
        geolocator = Nominatim(user_agent="tamizh-AI | S.Tamilselvan")
        location_query = f"{region}, {country}" if region and region != "Unknown" else country
        location = geolocator.geocode(location_query, addressdetails=True)

        if location and location.raw.get('address'):
            address = location.raw['address']
            return {
                'country': address.get('country', country),
                'state': address.get('state', region),
                'district': address.get('county', address.get('district', 'Unknown')),
                'city': address.get('city', address.get('town', address.get('village', 'Unknown'))),
                'latitude': location.latitude,
                'longitude': location.longitude
            }
    except Exception as e:
        st.error(f"Error getting detailed location: {str(e)}")

    return {
        'country': country,
        'state': region,
        'district': 'Unknown',
        'city': 'Unknown',
        'latitude': None,
        'longitude': None
    }

def get_phone_info(phone_number: str) -> Dict[str, str]:
    """
    Get detailed information about the phone number
    """
    try:
        parsed_number = phonenumbers.parse(phone_number)

        # Get country
        country = geocoder.description_for_number(parsed_number, "en")

        # Get region
        region = geocoder.description_for_number(parsed_number, "en", region=True)

        # Get detailed location
        location_info = get_detailed_location(country, region)

        # Get carrier
        carrier_name = carrier.name_for_number(parsed_number, "en")

        # Get timezone
        tz = timezone.time_zones_for_number(parsed_number)

        return {
            "country": location_info['country'],
            "state": location_info['state'],
            "district": location_info['district'],
            "city": location_info['city'],
            "carrier": carrier_name if carrier_name else "Unknown",
            "timezone": tz[0] if tz else "Unknown",
            "number_type": phonenumbers.number_type(parsed_number),
            "is_valid": phonenumbers.is_valid_number(parsed_number),
            "formatted_number": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "latitude": location_info['latitude'],
            "longitude": location_info['longitude']
        }
    except Exception as e:
        st.error(f"Error getting phone information: {str(e)}")
        return {
            "country": "Error",
            "state": "Error",
            "district": "Error",
            "city": "Error",
            "carrier": "Error",
            "timezone": "Error",
            "number_type": "Error",
            "is_valid": False,
            "formatted_number": "Error",
            "latitude": None,
            "longitude": None
        }

def get_location_map(phone_info: Dict[str, str]) -> Optional[folium.Map]:
    """
    Generate a detailed folium map with location information
    """
    try:
        if phone_info["latitude"] and phone_info["longitude"]:
            # Create map centered on location
            m = folium.Map(
                location=[phone_info["latitude"], phone_info["longitude"]], 
                zoom_start=8
            )

            # Add marker with popup
            folium.Marker(
                [phone_info["latitude"], phone_info["longitude"]],
                popup=folium.Popup(
                    f"""
                    <b>Location Details:</b><br>
                    Country: {phone_info['country']}<br>
                    State: {phone_info['state']}<br>
                    District: {phone_info['district']}<br>
                    City: {phone_info['city']}<br>
                    Coordinates: {phone_info['latitude']:.4f}, {phone_info['longitude']:.4f}
                    """,
                    max_width=300
                ),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

            # Add circle to show approximate area
            folium.Circle(
                [phone_info["latitude"], phone_info["longitude"]],
                radius=50000,  # 50km radius
                color='red',
                fill=True,
                popup='Approximate Area'
            ).add_to(m)

            return m
    except Exception as e:
        st.error(f"Error generating map: {str(e)}")

    return None

def add_watermark(pdf: FPDF):
    """Add a watermark to the current page"""
    # Save current settings
    original_font = pdf.font_family
    original_font_size = pdf.font_size_pt
    original_text_color = pdf.text_color

    # Set watermark properties
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(200, 200, 200)  # Light gray

    # Calculate center of page
    page_width = pdf.w
    page_height = pdf.h
    text = "Tamizh-AI | S.Tamilselvan"
    text_width = pdf.get_string_width(text)

    # Position watermark diagonally
    pdf.rotate(45, page_width/2, page_height/2)
    pdf.text(x=(page_width-text_width)/2, y=page_height/2, txt=text)
    pdf.rotate(0)

    # Restore original settings
    pdf.set_font(original_font, size=int(original_font_size))
    pdf.set_text_color(0, 0, 0)  # Reset to black

def generate_map_image(map_obj: folium.Map, filename: str) -> str:
    """
    Save the map as an HTML file
    """
    try:
        # Save map to a temporary HTML file
        map_path = f"{filename}_map.html"
        map_obj.save(map_path)
        return map_path
    except Exception as e:
        st.error(f"Error generating map: {str(e)}")
        return None

def generate_pdf_report(phone_info: Dict[str, str], timestamp: str) -> str:
    """
    Generate an enhanced PDF report with phone number analysis
    """
    number_types = {
        0: "FIXED_LINE",
        1: "MOBILE",
        2: "FIXED_LINE_OR_MOBILE",
        3: "TOLL_FREE",
        4: "PREMIUM_RATE",
        5: "SHARED_COST",
        6: "VOIP",
        7: "PERSONAL_NUMBER",
        8: "PAGER",
        9: "UAN",
        10: "UNKNOWN",
        27: "EMERGENCY",
        28: "VOICEMAIL",
    }

    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add first page
    pdf.add_page()

    # Add watermark
    add_watermark(pdf)

    # Title
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, 'Phone Number Analysis Report', 0, 1, 'C')
    pdf.ln(5)

    # Report generation time
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Generated on: {timestamp}', 0, 1, 'R')
    pdf.ln(10)

    # Number Details
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, '1. Number Details', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Formatted Number: {phone_info["formatted_number"]}', 0, 1)
    pdf.cell(0, 8, f'Validation Status: {"Valid" if phone_info["is_valid"] else "Invalid"}', 0, 1)
    pdf.cell(0, 8, f'Number Type: {number_types.get(phone_info["number_type"], "Unknown")}', 0, 1)
    pdf.ln(10)

    # Location Information
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Location Information', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Country: {phone_info["country"]}', 0, 1)
    pdf.cell(0, 8, f'State: {phone_info["state"]}', 0, 1)
    pdf.cell(0, 8, f'District: {phone_info["district"]}', 0, 1)
    pdf.cell(0, 8, f'City: {phone_info["city"]}', 0, 1)
    pdf.cell(0, 8, f'Timezone: {phone_info["timezone"]}', 0, 1)
    if phone_info["latitude"] and phone_info["longitude"]:
        pdf.cell(0, 8, f'Coordinates: {phone_info["latitude"]:.4f}, {phone_info["longitude"]:.4f}', 0, 1)
    pdf.ln(10)

    # Service Provider
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. Service Provider', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Carrier: {phone_info["carrier"]}', 0, 1)
    pdf.ln(10)

    # Additional Information
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '4. Additional Information', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, 
        'This analysis was performed using the Tamizh-AI Finder tool Create By S.Tamilselvan | Cyber Security Researcher\n\n'
        '* Location data is approximate and based on number allocation\n'
        '* Carrier information may vary based on number portability\n'
        '* Maps show estimated location with a 50km radius for privacy\n'
        '\nNote: This report is for informational purposes only.'
    )

    # Save PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf.output(tmp_file.name)
        return tmp_file.name

def generate_report(phone_info: Dict[str, str], timestamp: str) -> str:
    """
    Generate a text report of the phone number analysis
    """
    number_types = {
        0: "FIXED_LINE",
        1: "MOBILE",
        2: "FIXED_LINE_OR_MOBILE",
        3: "TOLL_FREE",
        4: "PREMIUM_RATE",
        5: "SHARED_COST",
        6: "VOIP",
        7: "PERSONAL_NUMBER",
        8: "PAGER",
        9: "UAN",
        10: "UNKNOWN",
        27: "EMERGENCY",
        28: "VOICEMAIL",
    }

    report = f"""
    PHONE NUMBER ANALYSIS REPORT
    Generated on: {timestamp}

    1. Number Details
    ----------------
    Formatted Number: {phone_info['formatted_number']}
    Validation Status: {'Valid' if phone_info['is_valid'] else 'Invalid'}
    Number Type: {number_types.get(phone_info['number_type'], 'Unknown')}

    2. Location Information
    ---------------------
    Country: {phone_info['country']}
    State: {phone_info['state']}
    District: {phone_info['district']}
    City: {phone_info['city']}
    Timezone: {phone_info['timezone']}

    3. Service Provider
    ----------------
    Carrier: {phone_info['carrier']}

    4. Additional Information
    ----------------------
    - This analysis was performed using the Tamizh-AI Finder tool Create By S.Tamilselvan | Cyber Security Researcher.
    - Location data is approximate and based on number allocation
    - Carrier information may vary based on number portability

    Note: This report is for informational purposes only.
    """
    return report



def get_ip_info(ip_address: str) -> Dict[str, str]:
    """
    Get detailed information about an IP address
    """
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/')
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": data.get("ip", "Unknown"),
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "postal": data.get("postal", "Unknown"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "timezone": data.get("timezone", "Unknown"),
                "org": data.get("org", "Unknown"),
                "asn": data.get("asn", "Unknown"),
                "isp": data.get("org", "Unknown").split()[0] if data.get("org") else "Unknown"
            }
        else:
            st.error(f"Error getting IP information: {response.status_code}")
            return {
                "ip": ip_address,
                "city": "Error",
                "region": "Error",
                "country": "Error",
                "postal": "Error",
                "latitude": None,
                "longitude": None,
                "timezone": "Error",
                "org": "Error",
                "asn": "Error",
                "isp": "Error"
            }
    except Exception as e:
        st.error(f"Error getting IP information: {str(e)}")
        return {
            "ip": ip_address,
            "city": "Error",
            "region": "Error",
            "country": "Error",
            "postal": "Error",
            "latitude": None,
            "longitude": None,
            "timezone": "Error",
            "org": "Error",
            "asn": "Error",
            "isp": "Error"
        }

def generate_ip_report(ip_info: Dict[str, str], timestamp: str) -> str:
    """
    Generate a text report of the IP address analysis
    """
    report = f"""
    IP ADDRESS ANALYSIS REPORT
    Generated on: {timestamp}

    1. IP Information
    ----------------
    IP Address: {ip_info['ip']}
    ISP: {ip_info['isp']}
    Organization: {ip_info['org']}
    ASN: {ip_info['asn']}

    2. Location Information
    ---------------------
    Country: {ip_info['country']}
    Region: {ip_info['region']}
    City: {ip_info['city']}
    Postal Code: {ip_info['postal']}
    Timezone: {ip_info['timezone']}

    3. Additional Information
    ----------------------
    - This analysis was performed using the Tamizh-AI Finder tool
    - Location data is approximate and based on IP geolocation
    - Some information may be limited due to privacy settings or VPN usage

    Note: This report is for informational purposes only.
    """
    return report

def generate_ip_pdf_report(ip_info: Dict[str, str], timestamp: str) -> str:
    """
    Generate an enhanced PDF report with IP address analysis
    """
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add first page
    pdf.add_page()

    # Add watermark
    add_watermark(pdf)

    # Title
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 10, 'IP Address Analysis Report', 0, 1, 'C')
    pdf.ln(5)

    # Report generation time
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, f'Generated on: {timestamp}', 0, 1, 'R')
    pdf.ln(10)

    # IP Information
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, '1. IP Information', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'IP Address: {ip_info["ip"]}', 0, 1)
    pdf.cell(0, 8, f'ISP: {ip_info["isp"]}', 0, 1)
    pdf.cell(0, 8, f'Organization: {ip_info["org"]}', 0, 1)
    pdf.cell(0, 8, f'ASN: {ip_info["asn"]}', 0, 1)
    pdf.ln(10)

    # Location Information
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Location Information', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f'Country: {ip_info["country"]}', 0, 1)
    pdf.cell(0, 8, f'Region: {ip_info["region"]}', 0, 1)
    pdf.cell(0, 8, f'City: {ip_info["city"]}', 0, 1)
    pdf.cell(0, 8, f'Postal Code: {ip_info["postal"]}', 0, 1)
    pdf.cell(0, 8, f'Timezone: {ip_info["timezone"]}', 0, 1)
    if ip_info["latitude"] and ip_info["longitude"]:
        pdf.cell(0, 8, f'Coordinates: {ip_info["latitude"]:.4f}, {ip_info["longitude"]:.4f}', 0, 1)
    pdf.ln(10)


    # Additional Information
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. Additional Information', 1, 1, 'L', True)
    pdf.ln(5)

    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, 
        'This analysis was performed using the Tamizh-AI Finder tool\n\n'
        '* Location data is approximate and based on IP geolocation\n'
        '* Some information may be limited due to privacy settings or VPN usage\n'
        '* Maps show estimated location with a 50km radius for privacy\n'
        '\nNote: This report is for informational purposes only.'
    )

    # Save PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf.output(tmp_file.name)
        return tmp_file.name

def get_ip_location_map(ip_info: Dict[str, str]) -> Optional[folium.Map]:
    """
    Generate a detailed folium map with IP location information
    """
    try:
        if ip_info["latitude"] and ip_info["longitude"]:
            # Create map centered on location
            m = folium.Map(
                location=[ip_info["latitude"], ip_info["longitude"]], 
                zoom_start=8
            )

            # Add marker with popup
            folium.Marker(
                [ip_info["latitude"], ip_info["longitude"]],
                popup=folium.Popup(
                    f"""
                    <b>IP Location Details:</b><br>
                    IP: {ip_info['ip']}<br>
                    Country: {ip_info['country']}<br>
                    Region: {ip_info['region']}<br>
                    City: {ip_info['city']}<br>
                    ISP: {ip_info['isp']}<br>
                    Coordinates: {ip_info['latitude']:.4f}, {ip_info['longitude']:.4f}
                    """,
                    max_width=300
                ),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

            # Add circle to show approximate area
            folium.Circle(
                [ip_info["latitude"], ip_info["longitude"]],
                radius=50000,  # 50km radius
                color='red',
                fill=True,
                popup='Approximate Area'
            ).add_to(m)

            return m
    except Exception as e:
        st.error(f"Error generating map: {str(e)}")

    return None