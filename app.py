import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import time
from main import load_data, filter_time_period, compute_alignment, find_top_allies_and_enemies, analyze_alignment_shift

# Set page config for a wider layout
st.set_page_config(
    page_title="UN Voting Patterns Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .stats-container {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 20px;
    }
    .big-number {
        font-size: 24px;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-title {
        font-size: 16px;
        color: #666;
    }
    .stButton > button {
        width: 100%;
        margin-top: 20px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'run_analysis' not in st.session_state:
    st.session_state.run_analysis = False

# Load country coordinates data
@st.cache_data
def load_country_coords():
    return {
        # Existing major countries with corrected names
        "CHINA": {"lat": 35.8617, "lon": 104.1954},
        "RUSSIAN FEDERATION": {"lat": 61.5240, "lon": 105.3188},
        "UNITED STATES": {"lat": 37.0902, "lon": -95.7129},
        "JAPAN": {"lat": 36.2048, "lon": 138.2529},
        "GERMANY": {"lat": 51.1657, "lon": 10.4515},
        "UNITED KINGDOM": {"lat": 55.3781, "lon": -3.4360},
        "FRANCE": {"lat": 46.2276, "lon": 2.2137},
        "INDIA": {"lat": 20.5937, "lon": 78.9629},
        "ITALY": {"lat": 41.8719, "lon": 12.5674},
        
        # Adding first 20 countries from CSV order
        "SENEGAL": {"lat": 14.4974, "lon": -14.4524},
        "MALAYSIA": {"lat": 4.2105, "lon": 101.9758},
        "VENEZUELA (BOLIVARIAN REPUBLIC OF)": {"lat": 6.4238, "lon": -66.5897},
        "ANGOLA": {"lat": -11.2027, "lon": 17.8739},
        "URUGUAY": {"lat": -32.5228, "lon": -55.7658},
        "SPAIN": {"lat": 40.4637, "lon": -3.7492},
        "EGYPT": {"lat": 26.8206, "lon": 30.8025},
        "NEW ZEALAND": {"lat": -40.9006, "lon": 174.8860},
        "UKRAINE": {"lat": 48.3794, "lon": 31.1656},
        "NIGER": {"lat": 17.6078, "lon": 8.0817},
        "SAINT VINCENT AND THE GRENADINES": {"lat": 13.2528, "lon": -61.1971},
        "ESTONIA": {"lat": 58.5953, "lon": 25.0136},
        "SOUTH AFRICA": {"lat": -30.5595, "lon": 22.9375},
        "VIET NAM": {"lat": 14.0583, "lon": 108.2772},
        "BELGIUM": {"lat": 50.8503, "lon": 4.3517},
        "TUNISIA": {"lat": 33.8869, "lon": 9.5375},
        "INDONESIA": {"lat": -0.7893, "lon": 113.9213},
        "DOMINICAN REPUBLIC": {"lat": 18.7357, "lon": -70.1627},
        "BRAZIL": {"lat": -14.2350, "lon": -51.9253},
        "UNITED REPUBLIC OF TANZANIA": {"lat": -6.3690, "lon": 34.8888},
        
        # Additional important countries
        "PAKISTAN": {"lat": 30.3753, "lon": 69.3451},
        "NIGERIA": {"lat": 9.0820, "lon": 8.6753},
        "BANGLADESH": {"lat": 23.6850, "lon": 90.3563},
        "MEXICO": {"lat": 23.6345, "lon": -102.5528},
        "PHILIPPINES": {"lat": 12.8797, "lon": 121.7740},
        "ETHIOPIA": {"lat": 9.1450, "lon": 40.4897},
        "DEMOCRATIC REPUBLIC OF THE CONGO": {"lat": -4.0383, "lon": 21.7587},
        "TURKEY": {"lat": 38.9637, "lon": 35.2433},
        "IRAN (ISLAMIC REPUBLIC OF)": {"lat": 32.4279, "lon": 53.6880},
        "THAILAND": {"lat": 15.8700, "lon": 100.9925},
        "MYANMAR": {"lat": 21.9162, "lon": 95.9560},
        "KENYA": {"lat": -0.0236, "lon": 37.9062},
        "REPUBLIC OF KOREA": {"lat": 35.9078, "lon": 127.7669},
        "COLOMBIA": {"lat": 4.5709, "lon": -74.2973},
        "UGANDA": {"lat": 1.3733, "lon": 32.2903},
        "ARGENTINA": {"lat": -38.4161, "lon": -63.6167},
        "ALGERIA": {"lat": 28.0339, "lon": 1.6596},
        "SUDAN": {"lat": 15.8277, "lon": 30.8167},
        "IRAQ": {"lat": 33.2232, "lon": 43.6793},
        "AFGHANISTAN": {"lat": 33.9391, "lon": 67.7100},
        "POLAND": {"lat": 51.9194, "lon": 19.1451},
        "CANADA": {"lat": 56.1304, "lon": -106.3468},
        "MOROCCO": {"lat": 31.7917, "lon": -7.0926},
        "SAUDI ARABIA": {"lat": 23.8859, "lon": 45.0792},
        "UZBEKISTAN": {"lat": 41.3775, "lon": 64.5853},
        "PERU": {"lat": -9.1900, "lon": -75.0152},
        "MOZAMBIQUE": {"lat": -18.6657, "lon": 35.5296},
        "GHANA": {"lat": 7.9465, "lon": -1.0232},
        "YEMEN": {"lat": 15.5527, "lon": 48.5164},
        "NEPAL": {"lat": 28.3949, "lon": 84.1240},
        
        # Adding more countries from the CSV list
        "BENIN": {"lat": 9.3077, "lon": 2.3158},
        "DENMARK": {"lat": 56.2639, "lon": 9.5018},
        "ROMANIA": {"lat": 45.9432, "lon": 24.9668},
        "GREECE": {"lat": 39.0742, "lon": 21.8243},
        "AUSTRIA": {"lat": 47.5162, "lon": 14.5501},
        "SWITZERLAND": {"lat": 46.8182, "lon": 8.2275},
        "CYPRUS": {"lat": 35.1264, "lon": 33.4299},
        "FIJI": {"lat": -17.7134, "lon": 178.0650},
        "BULGARIA": {"lat": 42.7339, "lon": 25.4858},
        "CUBA": {"lat": 21.5218, "lon": -77.7812},
        "ZAMBIA": {"lat": -13.1339, "lon": 27.8493},
        "SOUTH SUDAN": {"lat": 6.8770, "lon": 31.3070},
        "MONACO": {"lat": 43.7384, "lon": 7.4246},
        "REPUBLIC OF MOLDOVA": {"lat": 47.4116, "lon": 28.3699},
        "SAN MARINO": {"lat": 43.9424, "lon": 12.4578},
        "BURUNDI": {"lat": -3.3731, "lon": 29.9189},
        "HUNGARY": {"lat": 47.1625, "lon": 19.5033},
        "CAMBODIA": {"lat": 12.5657, "lon": 104.9910},
        "MALAWI": {"lat": -13.2543, "lon": 34.3015},
        "NAURU": {"lat": -0.5228, "lon": 166.9315},
        "NICARAGUA": {"lat": 12.8654, "lon": -85.2072},
        "BRUNEI DARUSSALAM": {"lat": 4.5353, "lon": 114.7277},
        "MALDIVES": {"lat": 3.2028, "lon": 73.2207},
        "SIERRA LEONE": {"lat": 8.4606, "lon": -11.7799},
        "CABO VERDE": {"lat": 16.5388, "lon": -23.0418},
        "PAPUA NEW GUINEA": {"lat": -6.3149, "lon": 143.9555},
        "MARSHALL ISLANDS": {"lat": 7.1315, "lon": 171.1845},
        "AZERBAIJAN": {"lat": 40.1431, "lon": 47.5769},
        "MADAGASCAR": {"lat": -18.7669, "lon": 46.8691},
        "CAMEROON": {"lat": 7.3697, "lon": 12.3547},
        "SAMOA": {"lat": -13.7590, "lon": -172.1046},
        "LIBYA": {"lat": 26.3351, "lon": 17.2283},
        "BAHRAIN": {"lat": 26.0667, "lon": 50.5577},
        "GUINEA": {"lat": 9.9456, "lon": -9.6966},
        "EQUATORIAL GUINEA": {"lat": 1.6508, "lon": 10.2679},
        "KYRGYZSTAN": {"lat": 41.2044, "lon": 74.7661},
        "ERITREA": {"lat": 15.1794, "lon": 39.7823},
        "KUWAIT": {"lat": 29.3117, "lon": 47.4818},
        "ARMENIA": {"lat": 40.0691, "lon": 45.0382},
        "MAURITANIA": {"lat": 21.0079, "lon": -10.9408},
        "SINGAPORE": {"lat": 1.3521, "lon": 103.8198},
        "CENTRAL AFRICAN REPUBLIC": {"lat": 6.6111, "lon": 20.9394},
        "LIECHTENSTEIN": {"lat": 47.1660, "lon": 9.5554},
        "NETHERLANDS": {"lat": 52.1326, "lon": 5.2913},
        "SERBIA": {"lat": 44.0165, "lon": 21.0059},
        "HAITI": {"lat": 18.9712, "lon": -72.2852},
        "IRELAND": {"lat": 53.1424, "lon": -7.6921},
        "KAZAKHSTAN": {"lat": 48.0196, "lon": 66.9237},
        "DJIBOUTI": {"lat": 11.8251, "lon": 42.5903},
        "DEMOCRATIC PEOPLE'S REPUBLIC OF KOREA": {"lat": 40.3399, "lon": 127.5101},
        "BOSNIA AND HERZEGOVINA": {"lat": 43.9159, "lon": 17.6791},
        "SWEDEN": {"lat": 60.1282, "lon": 18.6435},
        "ZIMBABWE": {"lat": -19.0154, "lon": 29.1549},
        "SOMALIA": {"lat": 5.1521, "lon": 46.1996},
        "SLOVAKIA": {"lat": 48.6690, "lon": 19.6990},
        "AUSTRALIA": {"lat": -25.2744, "lon": 133.7751},
        "KIRIBATI": {"lat": -3.3704, "lon": -168.7340},
        "QATAR": {"lat": 25.3548, "lon": 51.1839},
        "LITHUANIA": {"lat": 55.1694, "lon": 23.8813},
        "ICELAND": {"lat": 64.9631, "lon": -19.0208},
        
        # Adding final batch of countries
        "LUXEMBOURG": {"lat": 49.8153, "lon": 6.1296},
        "COMOROS": {"lat": -11.6455, "lon": 43.3333},
        "SRI LANKA": {"lat": 7.8731, "lon": 80.7718},
        "GUYANA": {"lat": 4.8604, "lon": -58.9302},
        "TONGA": {"lat": -21.1789, "lon": -175.1982},
        "VANUATU": {"lat": -15.3767, "lon": 166.9592},
        "LESOTHO": {"lat": -29.6099, "lon": 28.2336},
        "GUINEA-BISSAU": {"lat": 11.8037, "lon": -15.1804},
        "BOTSWANA": {"lat": -22.3285, "lon": 24.6849},
        "COSTA RICA": {"lat": 9.7489, "lon": -83.7534},
        "TAJIKISTAN": {"lat": 38.8610, "lon": 71.2761},
        "LIBERIA": {"lat": 6.4281, "lon": -9.4295},
        "GABON": {"lat": -0.8037, "lon": 11.6094},
        "ECUADOR": {"lat": -1.8312, "lon": -78.1834},
        "ESWATINI": {"lat": -26.5225, "lon": 31.4659},
        "SEYCHELLES": {"lat": -4.6796, "lon": 55.4920},
        "SAINT KITTS AND NEVIS": {"lat": 17.3578, "lon": -62.7830},
        "SOLOMON ISLANDS": {"lat": -9.6457, "lon": 160.1562},
        "MAURITIUS": {"lat": -20.3484, "lon": 57.5522},
        "ANDORRA": {"lat": 42.5063, "lon": 1.5218},
        "SAO TOME AND PRINCIPE": {"lat": 0.1864, "lon": 6.6131},
        "BELARUS": {"lat": 53.7098, "lon": 27.9534},
        "PALAU": {"lat": 7.5150, "lon": 134.5825},
        "GEORGIA": {"lat": 42.3154, "lon": 43.3569},
        "CZECHIA": {"lat": 49.8175, "lon": 15.4730},
        "FINLAND": {"lat": 61.9241, "lon": 25.7482},
        "ISRAEL": {"lat": 31.0461, "lon": 34.8516},
        "HONDURAS": {"lat": 15.1998, "lon": -86.2419},
        "MALI": {"lat": 17.5707, "lon": -3.9962},
        "NORTH MACEDONIA": {"lat": 41.6086, "lon": 21.7453},
        
        # Adding final set of countries
        "LEBANON": {"lat": 33.8547, "lon": 35.8623},
        "BARBADOS": {"lat": 13.1939, "lon": -59.5432},
        "BHUTAN": {"lat": 27.5142, "lon": 90.4336},
        "MALTA": {"lat": 35.9375, "lon": 14.3754},
        "SURINAME": {"lat": 3.9193, "lon": -56.0278},
        "UNITED ARAB EMIRATES": {"lat": 23.4241, "lon": 53.8478},
        "CROATIA": {"lat": 45.1000, "lon": 15.2000},
        "RWANDA": {"lat": -1.9403, "lon": 29.8739},
        "CONGO": {"lat": -0.2280, "lon": 15.8277},
        "GUATEMALA": {"lat": 15.7835, "lon": -90.2308},
        "ANTIGUA AND BARBUDA": {"lat": 17.0608, "lon": -61.7964},
        "LATVIA": {"lat": 56.8796, "lon": 24.6032},
        "TOGO": {"lat": 8.6195, "lon": 0.8248},
        "GRENADA": {"lat": 12.1165, "lon": -61.6790},
        "NAMIBIA": {"lat": -22.9576, "lon": 18.4904},
        "SYRIAN ARAB REPUBLIC": {"lat": 34.8021, "lon": 38.9968},
        "NORWAY": {"lat": 60.4720, "lon": 8.4689},
        "CHILE": {"lat": -35.6751, "lon": -71.5430},
        "DOMINICA": {"lat": 15.4150, "lon": -61.3710},
        "ALBANIA": {"lat": 41.1533, "lon": 20.1683},
        "TRINIDAD AND TOBAGO": {"lat": 10.6918, "lon": -61.2225},
        "PANAMA": {"lat": 8.5380, "lon": -80.7821},
        "MONTENEGRO": {"lat": 42.7087, "lon": 19.3744},
        "OMAN": {"lat": 21.4735, "lon": 55.9754},
        "SLOVENIA": {"lat": 46.1512, "lon": 14.9955},
        "BAHAMAS": {"lat": 25.0343, "lon": -77.3963},
        "JAMAICA": {"lat": 18.1096, "lon": -77.2975},
        "BOLIVIA (PLURINATIONAL STATE OF)": {"lat": -16.2902, "lon": -63.5887},
        "SAINT LUCIA": {"lat": 13.9094, "lon": -60.9789},
        "MONGOLIA": {"lat": 46.8625, "lon": 103.8467},
        "PORTUGAL": {"lat": 39.3999, "lon": -8.2245},
        "EL SALVADOR": {"lat": 13.7942, "lon": -88.8965},
        "GAMBIA": {"lat": 13.4432, "lon": -15.3101},
        "TURKMENISTAN": {"lat": 38.9697, "lon": 59.5563},
        "MICRONESIA (FEDERATED STATES OF)": {"lat": 7.4256, "lon": 150.5508},
        "TIMOR-LESTE": {"lat": -8.8742, "lon": 125.7275},
        "BELIZE": {"lat": 17.1899, "lon": -88.4976},
        "CHAD": {"lat": 15.4542, "lon": 18.7322},
        "BURKINA FASO": {"lat": 12.2383, "lon": -1.5616},
        "LAO PEOPLE'S DEMOCRATIC REPUBLIC": {"lat": 19.8563, "lon": 102.4955},
        "TUVALU": {"lat": -7.1095, "lon": 177.6493},
        "JORDAN": {"lat": 30.5852, "lon": 36.2384},
        "PARAGUAY": {"lat": -23.4425, "lon": -58.4438},
        "COTE D'IVOIRE": {"lat": 7.5400, "lon": -5.5471}
    }

# Load and cache the data
@st.cache_data
def load_cached_data():
    return load_data("UN_DATA.csv")

# Main app
def main():
    st.title("🌍 UN Voting Patterns Analysis")
    st.markdown("Analyze voting patterns and relationships between countries in the United Nations")

    # Load data
    if not st.session_state.data_loaded:
        with st.spinner("Loading UN voting data..."):
            df = load_cached_data()
            st.session_state.df = df
            st.session_state.data_loaded = True
    
    df = st.session_state.df

    # Sidebar controls
    with st.sidebar:
        st.header("Analysis Parameters")
        
        # Country selection
        available_countries = sorted(df.columns.tolist()[11:])  # Adjust index based on your data
        selected_country = st.selectbox(
            "Select Country to Analyze",
            available_countries,
            index=available_countries.index("UNITED STATES") if "UNITED STATES" in available_countries else 0
        )
        
        # Date range selection
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )
        
        # Analysis parameters
        min_votes = st.slider("Minimum Votes Required", 5, 100, 20, 
                            help="Minimum number of votes required to consider a country in the analysis")
        top_n = st.slider("Number of Top Allies/Enemies", 3, 10, 5,
                         help="Number of top aligned and opposed countries to display")
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Run Analysis", use_container_width=True):
                st.session_state.run_analysis = True
        with col2:
            if st.button("🔁 Reset", use_container_width=True):
                st.session_state.run_analysis = False

    # Display analysis status
    if st.session_state.run_analysis:
        st.sidebar.success("✅ Analysis complete!")
    
    # Rest of the main content
    if st.session_state.run_analysis:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Filter data
        status_text.text("Filtering data by date range...")
        progress_bar.progress(20)
        filtered_df = filter_time_period(df, start_date, end_date)
        
        # Compute alignments
        status_text.text("Computing voting alignments...")
        progress_bar.progress(40)
        percentages, vote_counts = compute_alignment(filtered_df, selected_country)
        
        # Get top allies and enemies
        status_text.text("Finding top allies and enemies...")
        progress_bar.progress(60)
        allies, enemies, allies_pct, enemies_pct, allies_votes, enemies_votes = find_top_allies_and_enemies(
            percentages, vote_counts, top_n=top_n, min_votes=min_votes
        )
        
        # Analyze shifts
        status_text.text("Analyzing alignment shifts...")
        progress_bar.progress(80)
        shift_results = analyze_alignment_shift(
            df, selected_country, start_date, end_date, min_votes=min_votes
        )
        
        progress_bar.progress(100)
        status_text.text("Analysis complete!")
        
        # Clear progress indicators after a short delay
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

        # Rest of the visualization code remains the same
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🤝 Top Allies")
            fig_allies = go.Figure()
            fig_allies.add_trace(go.Bar(
                x=[f"{country}<br>({votes} votes)" for country, votes in zip(allies, allies_votes)],
                y=[pct * 100 for pct in allies_pct],
                marker_color='rgb(26, 118, 255)',
                text=[f"{pct*100:.1f}%" for pct in allies_pct],
                textposition='auto',
            ))
            fig_allies.update_layout(
                title=f"Top {top_n} Allies",
                yaxis_title="Vote Alignment (%)",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig_allies, use_container_width=True)

        with col2:
            st.subheader("⚔️ Top Opponents")
            fig_enemies = go.Figure()
            fig_enemies.add_trace(go.Bar(
                x=[f"{country}<br>({votes} votes)" for country, votes in zip(enemies, enemies_votes)],
                y=[pct * 100 for pct in enemies_pct],
                marker_color='rgb(255, 64, 64)',
                text=[f"{pct*100:.1f}%" for pct in enemies_pct],
                textposition='auto',
            ))
            fig_enemies.update_layout(
                title=f"Top {top_n} Opponents",
                yaxis_title="Vote Alignment (%)",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig_enemies, use_container_width=True)

        # Alignment Shifts Analysis
        st.subheader("📊 Alignment Shifts Over Time")
        if shift_results[0]:  # If there are significant shifts
            country, direction, shift_value, first_half, second_half, first_votes, second_votes = shift_results
            
            # Create a before/after comparison chart
            shift_data = pd.DataFrame({
                'Period': ['First Half', 'Second Half'],
                'Alignment': [first_half * 100, second_half * 100],
                'Votes': [first_votes, second_votes]
            })
            
            fig_shift = go.Figure()
            fig_shift.add_trace(go.Bar(
                x=shift_data['Period'],
                y=shift_data['Alignment'],
                text=[f"{val:.1f}%<br>({votes} votes)" for val, votes in zip(shift_data['Alignment'], shift_data['Votes'])],
                textposition='auto',
                marker_color=['rgb(158,202,225)', 'rgb(94,158,217)'],
            ))
            fig_shift.update_layout(
                title=f"Biggest Shift: {country}<br>{abs(shift_value*100):.1f}% {'increase' if direction == 'positive' else 'decrease'}",
                yaxis_title="Vote Alignment (%)",
                showlegend=False,
                height=400
            )
            st.plotly_chart(fig_shift, use_container_width=True)

        # Map visualization
        st.subheader("🗺️ Global Voting Alignment Map")
        coords = load_country_coords()
        
        # Prepare data for the map
        map_data = []
        missing_coords = []
        for country, alignment in percentages.items():
            if alignment is not None and vote_counts[country] >= min_votes:
                if country in coords:
                    map_data.append({
                        "country": country,
                        "lat": coords[country]["lat"],
                        "lon": coords[country]["lon"],
                        "alignment": alignment * 100,
                        "votes": vote_counts[country]
                    })
                else:
                    missing_coords.append(country)
        
        if missing_coords:
            st.warning(
                "Some countries with sufficient votes are not shown on the map due to missing coordinates: " +
                ", ".join(missing_coords[:5]) + 
                ("..." if len(missing_coords) > 5 else "")
            )
        
        if map_data:
            map_df = pd.DataFrame(map_data)
            
            # Create the map visualization
            fig_map = px.scatter_mapbox(
                map_df,
                lat="lat",
                lon="lon",
                color="alignment",
                size="votes",
                hover_name="country",
                hover_data={
                    "alignment": ":.1f",
                    "votes": True,
                    "lat": False,
                    "lon": False
                },
                color_continuous_scale=["#ff0d0d", "#ffd000", "#1e88e5"],  # Red -> Yellow -> Blue
                size_max=25,  # Reduced from 50 to 25
                zoom=1.5,     # Slightly increased zoom
                title=f"Global Voting Alignment with {selected_country}"
            )
            
            fig_map.update_layout(
                mapbox_style="carto-positron",
                height=600,
                margin={"r":0,"t":30,"l":0,"b":0},
                coloraxis_colorbar_title="Alignment %",
                # Update marker settings for better visibility
                mapbox=dict(
                    zoom=1.5
                ),
                # Improve color bar appearance
                coloraxis=dict(
                    colorbar=dict(
                        title=dict(text="Alignment %", side="right"),
                        thickness=15,
                        len=0.9,
                        x=0.95
                    )
                )
            )
            
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Insufficient data for map visualization. Try adjusting the minimum votes threshold or date range.")
    else:
        # Show initial message
        st.info("👆 Set your analysis parameters in the sidebar and click 'Run Analysis' to start")
        
        # Add some example insights
        st.markdown("""
        ### What you can discover:
        - Find out which countries vote most similarly to your selected country
        - Identify the strongest opponents in UN voting patterns
        - Track how relationships between countries have changed over time
        - Visualize global voting alignment patterns on an interactive map
        
        ### Tips:
        - Try different minimum vote thresholds to focus on more significant relationships
        - Adjust the date range to analyze specific historical periods
        - Compare different countries to understand various diplomatic alignments
        """)

if __name__ == "__main__":
    main()