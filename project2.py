import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="HHS System Capacity Analytics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# UNIVERSAL CSS: Foolproof overrides for inputs in Light/Dark mode
st.markdown("""
    <style>
    /* Hide default Streamlit menus */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global Font applied ONLY to text elements */
    html, body, .stMarkdown, div, h1, h2, h3, h4, h5, h6, p, label {
        font-family: 'Georgia', serif !important;
    }

    /* =========================================================
       SIDEBAR STYLING: Force Blue Gradient & Legible Elements
       ========================================================= */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%) !important;
    }
    
    /* Sidebar Headers and Labels to White */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] label p,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #FFFFFF !important;
    }

    /* FOOLPROOF BUTTON FIX */
    [data-testid="stSidebar"] .stButton > button {
        background-color: #F7FAFC !important;
        border: 2px solid #CBD5E0 !important;
    }
    [data-testid="stSidebar"] .stButton > button * {
        color: #1A365D !important;
        font-weight: 900 !important;
    }

    /* FOOLPROOF DATE INPUT FIX */
    [data-testid="stSidebar"] .stDateInput [data-baseweb="input"], 
    [data-testid="stSidebar"] .stDateInput [data-baseweb="base-input"] {
        background-color: #F7FAFC !important;
        border-color: #CBD5E0 !important;
    }
    [data-testid="stSidebar"] .stDateInput input {
        color: #1A365D !important;
        -webkit-text-fill-color: #1A365D !important;
        font-weight: 900 !important;
    }

    /* Bulletproof fix for the Collapse/Expand Arrow Button */
    [data-testid="collapsedControl"] button, 
    [data-testid="stSidebarCollapseButton"] button {
        background-color: rgba(26, 54, 93, 0.4) !important; 
        border-radius: 4px !important;
    }
    [data-testid="collapsedControl"] svg, 
    [data-testid="stSidebarCollapseButton"] svg,
    button[kind="header"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }
    /* ========================================================= */

    /* Style Metric Cards with a clean, adaptive border */
    [data-testid="stMetric"] {
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #3182CE;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 14px !important;
        font-weight: 800 !important; 
    }
    
    [data-testid="stMetricValue"] {
        font-size: 36px !important; 
        font-weight: 900 !important; 
    }

    /* Custom Insight Cards with high-contrast Navy/Blue gradient */
    .insight-card {
        background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%);
        color: #FFFFFF;
        padding: 16px 20px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
        border-left: 6px solid #63B3ED;
    }
    .insight-card h4 {
        color: #FFFFFF !important;
        margin-top: 0;
        margin-bottom: 8px;
        font-size: 17px !important;
        font-weight: bold;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(255,255,255,0.2);
        padding-bottom: 4px;
    }
    .insight-card p {
        color: #F7FAFC !important;
        margin: 0;
        font-size: 15px !important;
        line-height: 1.5;
    }
    .alert-stat { color: #FEB2B2; font-weight: bold; font-size: 1.1em; }
    .highlight-stat { color: #9AE6B4; font-weight: bold; font-size: 1.1em; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_process_data():
    df = pd.read_csv('HHS_Unaccompanied_Alien_Children_Program.csv')
    df = df.dropna(subset=['Date']).copy()
    
    df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date_parsed'])
    
    df['Children in HHS Care'] = df['Children in HHS Care'].astype(str).str.replace(',', '').astype(float)
    df = df.sort_values('Date_parsed')
    
    df['Anomaly_Transfers'] = df['Children transferred out of CBP custody'] > df['Children in CBP custody']
    df['Anomaly_Discharges'] = df['Children discharged from HHS Care'] > df['Children in HHS Care']
    df['Has_Anomaly'] = df['Anomaly_Transfers'] | df['Anomaly_Discharges']
    
    df['Total_System_Load'] = df['Children in CBP custody'] + df['Children in HHS Care']
    df['Net_Daily_Intake'] = df['Children transferred out of CBP custody'] - df['Children discharged from HHS Care']
    
    df.set_index('Date_parsed', inplace=True)
    df['Backlog_Indicator'] = df['Net_Daily_Intake'].rolling('7D', min_periods=1).mean()
    
    full_date_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df = df.reindex(full_date_range)
    df.index.name = 'Date_parsed'
    df = df.reset_index()

    return df

df = load_and_process_data()

# TRANSPARENT CHART THEME
def style_chart(fig, title_text, subtitle_text="", height=450):
    fig.update_layout(
        title=dict(
            text=f"<b>{title_text}</b><br><span style='font-size:14px; font-style:italic; opacity:0.75;'>{subtitle_text}</span>",
            x=0.02, y=0.95,
            font=dict(size=20)
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=90, b=50, l=60, r=40),
        showlegend=False,
        height=height,
        hovermode="x unified"
    )
    fig.update_xaxes(
        showgrid=True, gridwidth=1, zeroline=False,
        title=dict(font=dict(size=16)),
        tickfont=dict(size=13)
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, zeroline=False,
        title=dict(font=dict(size=16)),
        tickfont=dict(size=13)
    )
    return fig

min_date_val = df['Date_parsed'].min().date()
max_date_val = df['Date_parsed'].max().date()
min_intake_val = int(df['Net_Daily_Intake'].min(skipna=True)) if pd.notna(df['Net_Daily_Intake'].min()) else 0
max_intake_val = int(df['Net_Daily_Intake'].max(skipna=True)) if pd.notna(df['Net_Daily_Intake'].max()) else 0

def reset_filters():
    st.session_state['date_filter'] = (min_date_val, max_date_val)
    st.session_state['intake_filter'] = (min_intake_val, max_intake_val)

with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-weight: 900; font-size: 24px;'>CONTROL PANEL</h2>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.button("🔄 Reset All Filters", use_container_width=True, on_click=reset_filters)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    date_range = st.date_input(
        "📅 Select Date Range", 
        value=(min_date_val, max_date_val), 
        min_value=min_date_val, 
        max_value=max_date_val,
        key='date_filter'
    )
    
    selected_intake_range = st.slider(
        "⚖️ Filter Net Intake Volume", 
        min_value=min_intake_val, 
        max_value=max_intake_val, 
        value=(min_intake_val, max_intake_val),
        key='intake_filter'
    )

filtered_df = df.copy()

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
    filtered_df = filtered_df[(filtered_df['Date_parsed'].dt.date >= start_d) & (filtered_df['Date_parsed'].dt.date <= end_d)]
elif isinstance(date_range, tuple) and len(date_range) == 1:
    start_d = date_range[0]
    filtered_df = filtered_df[filtered_df['Date_parsed'].dt.date >= start_d]
elif not isinstance(date_range, tuple):
    filtered_df = filtered_df[filtered_df['Date_parsed'].dt.date == date_range]

filtered_df = filtered_df[
    filtered_df['Net_Daily_Intake'].isna() |
    ((filtered_df['Net_Daily_Intake'] >= selected_intake_range[0]) & 
     (filtered_df['Net_Daily_Intake'] <= selected_intake_range[1]))
]

if filtered_df.empty:
    st.warning("No records match the selected sidebar filters. Please click 'Reset All Filters' or broaden your selection.")
    st.stop()

st.markdown("<h1 style='text-align: center; font-weight: 900; font-size: 40px; line-height: 1.2; margin-bottom: 15px;'>UAC CARE PIPELINE: CAPACITY & LOAD ANALYTICS</h1>", unsafe_allow_html=True)

with st.expander("ℹ️ Methodology, Calculations & Validation Definitions", expanded=False):
    st.markdown("""
    **Data Validation & Integrity:**
    Logical constraints (e.g., Transfers <= CBP custody, Discharges <= HHS care) are verified. Any identified anomalies are flagged below but retained to accurately reflect raw reporting conditions.
    
    **Core Calculations:**
    * **Total System Load:** `[Children in CBP Custody] + [Children in HHS Care]`. Represents the absolute count of children reliant on federal resources on any given day.
    * **Net Daily Intake Pressure:** `[Children transferred into HHS] - [Children discharged from HHS]`. An indicator of pipeline flow (positive = net inflows).
    * **7-Day Calendar Rolling Average of Reported Net Intake:** The 7-day calendar rolling average of Net Daily Intake. Used to track sustained structural pressure based on reported days.
    """)

# Display validation anomalies if any exist
total_anomalies = df['Has_Anomaly'].sum()
if total_anomalies > 0:
    st.warning(f"⚠️ **Data Validation Note:** {int(total_anomalies)} record(s) indicate logical reporting anomalies (e.g., daily transfers out exceeding total reported custody). These remain in the dataset for transparency.")

st.markdown("<hr>", unsafe_allow_html=True)

avg_sys_load = filtered_df['Total_System_Load'].mean()
peak_sys_load = filtered_df['Total_System_Load'].max()
avg_cbp_load = filtered_df['Children in CBP custody'].mean()
avg_hhs_load = filtered_df['Children in HHS Care'].mean()
avg_net_intake = filtered_df['Net_Daily_Intake'].mean()
max_net_intake = filtered_df['Net_Daily_Intake'].max()

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1: st.metric("PEAK SYS LOAD", f"{int(peak_sys_load):,}" if pd.notna(peak_sys_load) else "N/A", help="Highest combined custody count in the selected period.")
with kpi2: st.metric("AVG SYS LOAD", f"{int(avg_sys_load):,}" if pd.notna(avg_sys_load) else "N/A", help="Mean combined custody count.")
with kpi3: st.metric("AVG HHS CARE", f"{int(avg_hhs_load):,}" if pd.notna(avg_hhs_load) else "N/A", help="Mean children in HHS shelter care.")
with kpi4: st.metric("AVG CBP HOLDING", f"{int(avg_cbp_load):,}" if pd.notna(avg_cbp_load) else "N/A", help="Mean children in CBP border holding.")
with kpi5: st.metric("AVG NET INTAKE", f"{avg_net_intake:.1f}" if pd.notna(avg_net_intake) else "N/A", help="Average daily imbalance between intake and discharge.")
with kpi6: st.metric("PEAK SURGE DAY", f"{int(max_net_intake):,}" if pd.notna(max_net_intake) else "N/A", help="Maximum number of net children added in a single day.")

st.markdown("<hr>", unsafe_allow_html=True)

charts_col, insights_col = st.columns([3.2, 1], gap="large")

with charts_col:
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        fig_overview = px.line(
            filtered_df, 
            x='Date_parsed', 
            y='Total_System_Load',
            color_discrete_sequence=['#3182CE'],
            markers=True 
        )
        fig_overview = style_chart(fig_overview, "Total Federal Care Load Trajectory", "Combined daily children across all CBP and HHS facilities")
        fig_overview.update_traces(line=dict(width=2.5), marker=dict(size=5, color='#2B6CB0'), fill='tozeroy', fillcolor='rgba(49, 130, 206, 0.15)', connectgaps=False)
        st.plotly_chart(fig_overview, use_container_width=True)

    with row1_col2:
        fig_net = px.bar(
            filtered_df, 
            x='Date_parsed', 
            y='Net_Daily_Intake',
            color='Net_Daily_Intake',
            color_continuous_scale=['#38A169', '#3182CE', '#E53E3E'] 
        )
        fig_net = style_chart(fig_net, "Net Daily Intake & Pipeline Pressure", "Transfers Into HHS minus HHS Discharges")
        fig_net.update_coloraxes(showscale=False)
        st.plotly_chart(fig_net, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)
    
    with row2_col1:
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Scatter(
            x=filtered_df['Date_parsed'], y=filtered_df['Children in HHS Care'],
            name='HHS Care', line=dict(color='#38A169', width=2.5), mode='lines+markers', marker=dict(size=4), connectgaps=False
        ))
        fig_dual.add_trace(go.Scatter(
            x=filtered_df['Date_parsed'], y=filtered_df['Children in CBP custody'],
            name='CBP Custody', line=dict(color='#DD6B20', width=2.5), yaxis='y2', mode='lines+markers', marker=dict(size=4), connectgaps=False
        ))
        fig_dual = style_chart(fig_dual, "Comparative Analysis: Holding vs Care", "Contrasting CBP influx vs HHS absorption")
        
        fig_dual.update_layout(
            yaxis=dict(
                title=dict(text='HHS Population', font=dict(color='#38A169', size=15)),
                tickfont=dict(color='#38A169', size=13)
            ),
            yaxis2=dict(
                title=dict(text='CBP Population', font=dict(color='#DD6B20', size=15)),
                tickfont=dict(color='#DD6B20', size=13),
                overlaying='y',
                side='right'
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(size=13))
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    with row2_col2:
        fig_backlog = px.line(
            filtered_df,
            x='Date_parsed',
            y='Backlog_Indicator',
            color_discrete_sequence=['#D69E2E'],
            markers=False
        )
        fig_backlog = style_chart(fig_backlog, "7-Day Calendar Rolling Average", "Sustained pipeline pressure based on reported days")
        fig_backlog.add_hline(y=0, line_dash="dash", line_color="#718096", annotation_text="Equilibrium (0)")
        fig_backlog.add_hline(y=50, line_dash="dot", line_color="#E53E3E", annotation_text="Illustrative Strain (>50)")
        fig_backlog.update_traces(line=dict(width=3.5), connectgaps=False)
        st.plotly_chart(fig_backlog, use_container_width=True)

    st.markdown("<h3 style='font-weight: 900; font-size: 22px; margin-top: 15px;'>CRITICAL EVENT LEADERBOARD</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    lead_col1, lead_col2 = st.columns(2)

    with lead_col1:
        st.markdown("<h4 style='font-weight: bold; font-size: 16px; color: #C53030;'>⚠️ Top 10 Acute Pressure Events</h4>", unsafe_allow_html=True)
        top_congestion = filtered_df.dropna(subset=['Net_Daily_Intake']).sort_values('Net_Daily_Intake', ascending=False).head(10)
        top_congestion['Date'] = top_congestion['Date_parsed'].dt.strftime('%b %d, %Y')
        st.dataframe(
            top_congestion[['Date', 'Net_Daily_Intake', 'Total_System_Load', 'Children in CBP custody']].rename(columns={
                'Net_Daily_Intake': 'Net Intake Flow',
                'Total_System_Load': 'System Load',
                'Children in CBP custody': 'CBP Custody Load'
            }),
            hide_index=True,
            use_container_width=True
        )

    with lead_col2:
        st.markdown("<h4 style='font-weight: bold; font-size: 16px; color: #2F855A;'>✅ Top 10 Maximum Relief Events</h4>", unsafe_allow_html=True)
        top_relief = filtered_df.dropna(subset=['Net_Daily_Intake']).sort_values('Net_Daily_Intake', ascending=True).head(10)
        top_relief['Date'] = top_relief['Date_parsed'].dt.strftime('%b %d, %Y')
        st.dataframe(
            top_relief[['Date', 'Net_Daily_Intake', 'Children discharged from HHS Care', 'Children transferred out of CBP custody']].rename(columns={
                'Net_Daily_Intake': 'Net Intake Relief',
                'Children discharged from HHS Care': 'Discharged from HHS',
                'Children transferred out of CBP custody': 'New Transfers In'
            }),
            hide_index=True,
            use_container_width=True
        )

with insights_col:
    st.markdown("<h3 style='font-weight: 900; font-size: 22px; margin-top: 15px;'>EXECUTIVE INSIGHTS</h3>", unsafe_allow_html=True)
    st.markdown("<hr style='margin-top: 0px; margin-bottom: 15px;'>", unsafe_allow_html=True)

    valid_sys_load = filtered_df.dropna(subset=['Total_System_Load'])
    peak_load_date = valid_sys_load.loc[valid_sys_load['Total_System_Load'].idxmax(), 'Date_parsed'].strftime('%b %d, %Y') if not valid_sys_load.empty else "N/A"
    peak_load_val = int(valid_sys_load['Total_System_Load'].max()) if not valid_sys_load.empty else 0
    load_variance = ((peak_load_val - avg_sys_load) / avg_sys_load) * 100 if avg_sys_load > 0 else 0
    
    valid_intake = filtered_df.dropna(subset=['Net_Daily_Intake'])
    worst_backlog_date = valid_intake.loc[valid_intake['Net_Daily_Intake'].idxmax(), 'Date_parsed'].strftime('%b %d, %Y') if not valid_intake.empty else "N/A"
    worst_backlog_val = int(valid_intake['Net_Daily_Intake'].max()) if not valid_intake.empty else 0

    best_relief_date = valid_intake.loc[valid_intake['Net_Daily_Intake'].idxmin(), 'Date_parsed'].strftime('%b %d, %Y') if not valid_intake.empty else "N/A"
    best_relief_val = int(valid_intake['Net_Daily_Intake'].min()) if not valid_intake.empty else 0
    
    valid_cbp = filtered_df.dropna(subset=['Children in CBP custody'])
    cbp_peak_date = valid_cbp.loc[valid_cbp['Children in CBP custody'].idxmax(), 'Date_parsed'].strftime('%b %d, %Y') if not valid_cbp.empty else "N/A"
    cbp_peak_val = int(valid_cbp['Children in CBP custody'].max()) if not valid_cbp.empty else 0
    cbp_variance = ((cbp_peak_val - avg_cbp_load) / avg_cbp_load) * 100 if avg_cbp_load > 0 else 0

    st.markdown(f"""
        <div class='insight-card'>
            <h4>📈 Peak Observed System Load</h4>
            <p>Observed system load peaked on <b>{peak_load_date}</b> at <span class='alert-stat'>{peak_load_val:,}</span> children. This represents an increase of <b>+{load_variance:.1f}%</b> above the selected timeframe average of {int(avg_sys_load) if pd.notna(avg_sys_load) else 0:,}.</p>
        </div>
        
        <div class='insight-card'>
            <h4>🚨 Acute Pipeline Pressure</h4>
            <p>The highest daily pipeline pressure occurred on <b>{worst_backlog_date}</b>, where <span class='alert-stat'>+{worst_backlog_val:,}</span> more children were transferred into HHS than were discharged, indicating elevated net intake.</p>
        </div>
        
        <div class='insight-card'>
            <h4>🏢 CBP Custody Volatility</h4>
            <p>CBP custody loads show high volatility. Peak custody hit <span class='alert-stat'>{cbp_peak_val:,}</span> children on <b>{cbp_peak_date}</b>, which is <b>+{cbp_variance:.1f}%</b> above the timeframe average.</p>
        </div>

        <div class='insight-card'>
            <h4>📉 Maximum Discharge Offset</h4>
            <p>On <b>{best_relief_date}</b>, HHS discharges resulted in a net intake of <span class='highlight-stat'>{best_relief_val:,}</span>, offsetting incoming transfers.</p>
        </div>
        
        <div class='insight-card' style='border: 1px solid rgba(255,255,255,0.2); border-left: 6px solid #805AD5;'>
            <h4 style='color: #D6BCFA !important;'>🎯 Strategic Action Plan</h4>
            <p><b>1. Illustrative Vetting Target:</b> Consider expediting review processes when the 7-day pressure indicator exceeds <b>+50</b> (analytical threshold).</p>
            <p style='margin-top: 8px;'><b>2. Buffer Allocation Review:</b> Review facility allocation when CBP custody spikes significantly above average baseline levels.</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    import sys
    import streamlit as st
    from streamlit.web import cli as stcli

    if not st.runtime.exists():
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())