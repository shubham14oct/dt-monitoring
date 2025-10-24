import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# --- DGA Model Logic (Based on IEC/IEEE Standards) ---

# 1. Coordinate Conversion for Ternary Plots (Duval)
def to_cartesian(p1, p2, p3):
    """Converts normalized (100%) ternary coordinates to Cartesian (x, y) for plotting."""
    x = p2 + p3 / 2
    y = p3 * np.sqrt(3) / 2
    return x, y

def get_duval_percentages(G1, G2, G3):
    """Normalizes three gases to 100%."""
    total = G1 + G2 + G3
    if total == 0:
        return 0, 0, 0, 0
    P1 = (G1 / total) * 100
    P2 = (G2 / total) * 100
    P3 = (G3 / total) * 100
    return P1, P2, P3, total

# 2. Diagnostic Functions (Using uppercase parameters to match input keys)

def diagnose_duval_t1(H2, CH4, C2H4, C2H2, CO):
    """Duval Triangle 1: Uses CH4, C2H4, C2H2. Regions for D1, D2, T1, T2, T3, PD."""
    P_CH4, P_C2H4, P_C2H2, total = get_duval_percentages(CH4, C2H4, C2H2)
    
    if total == 0:
        return "Not Applicable (Total gas is zero)"
    
    # Simple check for T1 region based on common boundaries (P_C2H2 < 0.5, P_CH4 > 80)
    if P_C2H2 < 0.5 and P_CH4 > 80:
        diagnosis = "T1 (Thermal fault T < 300°C)"
    elif P_C2H4 > 25 and P_C2H2 < 1:
        diagnosis = "T2 (Thermal fault 300°C–700°C)"
    elif P_C2H2 > 5 and P_C2H4 > 15:
        diagnosis = "D2 (Arcing in oil)"
    elif P_C2H4 > 50 and P_C2H2 < 2:
        diagnosis = "T3 (Thermal fault T > 700°C)"
    else:
        diagnosis = "Undefined/Mixed Fault"
        
    return f"{diagnosis} (CH4: {P_CH4:.1f}%, C2H4: {P_C2H4:.1f}%, C2H2: {P_C2H2:.1f}%)"

def diagnose_duval_t4(H2, CH4, C2H4, C2H2, CO):
    """Duval Triangle 4: Uses H2, C2H2, C2H4. Regions for T3, D2, S (Stray Gassing)."""
    P_H2, P_C2H2, P_C2H4, total = get_duval_percentages(H2, C2H2, C2H4)

    if total == 0:
        return "Not Applicable (Total gas is zero)"

    if P_H2 > 80 and P_C2H2 < 5:
        diagnosis = "S (Stray Gassing / Hot metal contacts)"
    elif P_C2H4 > 60 and P_H2 < 10:
        diagnosis = "T3 (Severe Thermal Fault T > 700°C)"
    elif P_C2H2 > 15:
        diagnosis = "D2 (High Energy Arcing)"
    else:
        diagnosis = "Mixed or Undefined Region"
        
    return f"{diagnosis} (H2: {P_H2:.1f}%, C2H2: {P_C2H2:.1f}%, C2H4: {P_C2H4:.1f}%)"

def diagnose_rogers_ratio(H2, CH4, C2H4, C2H2, CO):
    """Rogers Ratio Method: Calculates 3 ratios and uses lookup table."""
    ratios = {
        'R1': CH4 / H2 if H2 > 0 else 99,
        'R2': C2H4 / CH4 if CH4 > 0 else 99,
        'R5': C2H2 / C2H4 if C2H4 > 0 else 99,
    }

    # Rogers Code Lookup Table (Simplified, R1/R2/R5 limits are approx 0.1, 1, 3 for 0/1/2)
    code = ""
    code += '0' if ratios['R1'] < 0.1 else ('2' if ratios['R1'] > 1.0 else '1')
    code += '0' if ratios['R2'] < 1.0 else ('2' if ratios['R2'] > 3.0 else '1')
    code += '0' if ratios['R5'] < 0.5 else ('2' if ratios['R5'] > 3.0 else '1')
    
    # Common codes and their diagnoses
    diagnoses = {
        '100': "T1 (Thermal Fault T < 300°C)",
        '110': "T2 (Thermal Fault 300°C–700°C)",
        '210': "T3 (Thermal Fault T > 700°C)",
        '102': "D1 (Low Energy Discharge/PD)",
        '001': "D2 (High Energy Discharge/Arcing)",
        '000': "No fault / Normal aging",
        '010': "Undefined/Mixed thermal",
        '011': "Undefined/Mixed thermal",
        '111': "Mixed thermal and electrical",
    }
    
    diag = diagnoses.get(code, "Undefined/Developing Fault")
    
    return f"Code: {code}XX, Diagnosis: {diag} (R1:{ratios['R1']:.2f}, R2:{ratios['R2']:.2f}, R5:{ratios['R5']:.2f})"

def diagnose_doernenburg(H2, CH4, C2H4, C2H2, CO):
    """Doernenburg's Method: Checks four ratios against specific limits."""
    # Doernenburg only applicable if certain gas levels are met (simplified condition here)
    if H2 < 100 or CH4 < 10 or C2H2 < 0.5 or C2H4 < 50:
        return "Inconclusive (Gas limits below Doernenburg thresholds)"

    ratios = {
        'R_ch4_h2': CH4 / H2,
        'R_c2h2_c2h4': C2H2 / C2H4,
        'R_c2h2_ch4': C2H2 / CH4,
        'R_c2h2_h2': C2H2 / H2,
    }

    # Simplified Diagnosis Logic
    if ratios['R_c2h2_c2h4'] > 0.3 and ratios['R_c2h2_ch4'] < 0.7:
        diagnosis = "D1 (Discharge/Arcing)"
    elif ratios['R_c2h2_c2h4'] < 0.3 and ratios['R_ch4_h2'] > 1.0:
        diagnosis = "T2 (Thermal fault 300°C–700°C)"
    else:
        diagnosis = "Mixed/Other fault"
        
    return f"{diagnosis} (Check thresholds in plot tab)"

# Retained the T5 function, but removed it from the summary table and tabs as requested.
def diagnose_duval_t5(H2, CH4, C2H4, C2H2, CO):
    """Duval Triangle 5: Focuses on thermal fault differentiation in DGA-R4."""
    P_CH4, P_C2H4, P_C2H2, total = get_duval_percentages(CH4, C2H4, C2H2)
    
    if total == 0:
        return "Not Applicable (Total gas is zero)"

    # Simplified T5 Logic (Focus on T2, C, HC)
    if P_C2H4 > 50 and P_CH4 > 40:
        diagnosis = "HC (Hot cellulosic materials)"
    elif P_CH4 > 70 and P_C2H4 < 10:
        diagnosis = "T1 (Thermal T < 300°C - Cellulose/Paper)"
    elif P_C2H4 > 30 and P_C2H2 < 1:
        diagnosis = "T2 (Thermal T 300°C–770°C)"
    else:
        diagnosis = "Mixed Oil Fault"
        
    return f"{diagnosis} (CH4: {P_CH4:.1f}%, C2H4: {P_C2H4:.1f}%, C2H2: {P_C2H2:.1f}%)"

def diagnose_duval_pentagon(H2, CH4, C2H4, C2H2, CO):
    """Duval Pentagon Method (Conceptual): Uses all 5 gases via ratios."""
    
    # This method is complex, requiring 5 ratios to map to 5 axes.
    # We provide a conceptual, rule-based summary diagnosis here.
    
    if C2H2 > 10 and C2H4 > 50:
        return "D2 / T3 (High Energy Arcing + Hotspot)"
    elif H2 > 500 and C2H4 < 50:
        return "PD / D1 (Partial Discharge / Low Energy Discharge)"
    elif CO > 1000 and C2H4 < 10:
        return "C (Cellulose/Paper degradation - thermal)"
    elif C2H4 > 200 and H2 < 50:
        return "T2 (Thermal Fault 300°C-700°C)"
    else:
        return "Mixed/Unclassified Fault Zone"

# --- Plotting Functions (Unchanged) ---

def draw_duval_triangle_plot(fig, ax, G1_name, G2_name, G3_name, P1, P2, P3, fault_regions, title):
    """Draws a generic Duval triangle plot."""
    
    # 1. Base Triangle Coordinates (Normalized to a 100-unit equilateral triangle)
    A = (0, 0)
    B = (100, 0)
    C = to_cartesian(0, 50, 100) # (50, 86.6)
    
    # 2. Draw Regions (using simplified convex hulls/polygons)
    for name, region in fault_regions.items():
        # Points are defined in normalized (P1, P2, P3) format
        x_coords = []
        y_coords = []
        for p_val1, p_val2, p_val3 in region['coords']:
            x, y = to_cartesian(p_val1, p_val2, p_val3)
            x_coords.append(x)
            y_coords.append(y)
        
        # Close the polygon
        x_coords.append(x_coords[0])
        y_coords.append(y_coords[0])

        ax.plot(x_coords, y_coords, color='gray', linestyle='--', linewidth=0.5)
        ax.fill(x_coords, y_coords, color=fault_regions[name]['color'], alpha=0.3, zorder=1)
        
        # Add label (centered, simplified)
        x_center = np.mean(x_coords[:-1])
        y_center = np.mean(y_coords[:-1])
        ax.text(x_center, y_center, name, ha='center', va='center', fontsize=8, weight='bold', color=fault_regions[name]['text_color'])

    # 3. Plot the base triangle outline
    ax.plot([A[0], B[0], C[0], A[0]], [A[1], B[1], C[1], A[1]], 'k-', linewidth=2)

    # 4. Plot the User's Data Point
    user_x, user_y = to_cartesian(P1, P2, P3)
    ax.plot(user_x, user_y, 'o', color='red', markersize=10, label=f'Input Point', zorder=5, markeredgecolor='black')
    ax.text(user_x, user_y - 8, f'({G1_name}:{P1:.0f}, {G2_name}:{P2:.0f}, {G3_name}:{P3:.0f})', 
            ha='center', fontsize=7, color='red', weight='bold')

    # 5. Labels and Cosmetics
    ax.set_title(title, fontsize=12, fontweight='bold')
    
    # Corner Labels
    ax.text(A[0], A[1] - 5, G1_name + " (100%)", ha='center', fontsize=10, weight='bold')
    ax.text(B[0], B[1] - 5, G2_name + " (100%)", ha='center', fontsize=10, weight='bold')
    ax.text(C[0], C[1] + 5, G3_name + " (100%)", ha='center', fontsize=10, weight='bold')

    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 95)
    ax.axis('off') # Remove axis ticks and frame
    ax.set_aspect('equal', adjustable='box')


def plot_duval_t1(H2, CH4, C2H4, C2H2, CO):
    """Generates the Duval T1 Plot."""
    fig, ax = plt.subplots(figsize=(6, 6))
    
    P_CH4, P_C2H4, P_C2H2, total = get_duval_percentages(CH4, C2H4, C2H2)

    # Duval T1 Fault Regions (P1=CH4, P2=C2H4, P3=C2H2) - Simplified Coordinates for Matplotlib
    regions = {
        'PD': {'color': 'lightblue', 'text_color': 'blue', 'coords': [(98, 2, 0), (90, 0, 10), (95, 0, 5), (100, 0, 0)]},
        'T1': {'color': 'lightgreen', 'text_color': 'green', 'coords': [(90, 0, 10), (70, 0, 30), (80, 20, 0), (98, 2, 0)]},
        'T2': {'color': 'yellow', 'text_color': 'darkgoldenrod', 'coords': [(70, 0, 30), (50, 0, 50), (40, 60, 0), (80, 20, 0)]},
        'T3': {'color': 'orange', 'text_color': 'red', 'coords': [(40, 60, 0), (0, 100, 0), (0, 50, 50), (50, 0, 50)]},
        'D2': {'color': 'salmon', 'text_color': 'darkred', 'coords': [(0, 100, 0), (0, 0, 100), (40, 60, 0)]},
        'D1': {'color': 'purple', 'text_color': 'white', 'coords': [(0, 50, 50), (0, 0, 100), (50, 0, 50)]},
    }

    if total > 0:
        draw_duval_triangle_plot(fig, ax, "CH4", "C2H4", "C2H2", P_CH4, P_C2H4, P_C2H2, regions, "Duval Triangle 1 (T1, T2, D1, D2, PD)")
    else:
        ax.set_title("Duval Triangle 1 - No Gas Input")
        ax.text(50, 50, "Total Gas Concentration is Zero", ha='center', fontsize=12)

    st.pyplot(fig)

def plot_duval_t4(H2, CH4, C2H4, C2H2, CO):
    """Generates the Duval T4 Plot."""
    fig, ax = plt.subplots(figsize=(6, 6))
    
    P_H2, P_C2H2, P_C2H4, total = get_duval_percentages(H2, C2H2, C2H4)
    
    # Duval T4 Fault Regions (P1=H2, P2=C2H2, P3=C2H4) - Simplified Coordinates
    regions = {
        'S': {'color': 'lightgray', 'text_color': 'black', 'coords': [(95, 5, 0), (70, 30, 0), (70, 0, 30), (95, 0, 5)]},
        'T3': {'color': 'gold', 'text_color': 'orange', 'coords': [(30, 0, 70), (0, 0, 100), (0, 30, 70), (30, 70, 0)]},
        'D2': {'color': 'darkred', 'text_color': 'white', 'coords': [(0, 100, 0), (0, 70, 30), (30, 0, 70), (0, 0, 100)]},
    }

    if total > 0:
        draw_duval_triangle_plot(fig, ax, "H2", "C2H2", "C2H4", P_H2, P_C2H2, P_C2H4, regions, "Duval Triangle 4 (T3, D2, S)")
    else:
        ax.set_title("Duval Triangle 4 - No Gas Input")
        ax.text(50, 50, "Total Gas Concentration is Zero", ha='center', fontsize=12)

    st.pyplot(fig)


# --- Streamlit Application Layout ---

st.set_page_config(layout="wide", page_title="DGA Transformer Fault Portal")

st.markdown("""
    <style>
    .reportview-container .main {
        padding-top: 2rem;
    }
    .stNumberInput, .stTabs {
        border-radius: 0.5rem;
        padding: 10px;
    }
    .stNumberInput label {
        font-weight: 600;
    }
    /* Style for the summary table header */
    .stTable > table > thead > tr > th {
        background-color: #f0f2f6;
        color: #1e3a8a;
        font-size: 1.0rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ Distribution Transformer DGA Fault Analysis Portal")
st.caption("Enter the gas concentrations (in ppm) below and click 'Analyze' to generate a comprehensive fault diagnosis.")

# --- Session State Management ---
# Initialize session state variable to control when analysis runs
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

# Callback function to set the state when the button is clicked
def set_analysis_state_true():
    st.session_state.analyzed = True

# --- Gas Input Sidebar ---
with st.sidebar:
    st.header("Gas Inputs (ppm)")
    
    # Gas concentrations (in ppm) - Mandatory Inputs
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        H2 = st.number_input("Hydrogen (H2)", min_value=0.0, value=150.0, step=1.0, key="input_H2")
        C2H4 = st.number_input("Ethylene (C2H4)", min_value=0.0, value=10.0, step=1.0, key="input_C2H4")
        CO = st.number_input("Carbon Monoxide (CO)", min_value=0.0, value=800.0, step=1.0, key="input_CO")
    with col_input2:
        CH4 = st.number_input("Methane (CH4)", min_value=0.0, value=25.0, step=1.0, key="input_CH4")
        C2H2 = st.number_input("Acetylene (C2H2)", min_value=0.0, value=0.5, step=0.1, format="%.1f", key="input_C2H2")
        st.number_input("Oxygen (O2)", min_value=0.0, value=5000.0, disabled=True, help="Optional Context Gas", key="input_O2")

    gas_data = {'H2': H2, 'CH4': CH4, 'C2H4': C2H4, 'C2H2': C2H2, 'CO': CO}
    
    st.markdown("---")
    
    # Analysis Trigger Button
    st.button(
        "Analyze DGA Data", 
        key="analyze_button", 
        type="primary",
        use_container_width=True,
        on_click=set_analysis_state_true
    )
    
    st.markdown("---")
    total_gases = sum(gas_data.values())
    st.metric("Total Combustible Gas (TCG)", f"{total_gases:,.1f} ppm", help="Sum of H2, CH4, C2H4, C2H2, CO")
    
# --- Main Content: Conditional Summary and Dashboard ---

if st.session_state.analyzed:
    
    st.header("Fault Analysis Summary")

    # Run only the specified diagnostic models
    analysis_results = [
        {"Model": "Duval's Triangle 1 (T1/T2/D1)", "Diagnosis": diagnose_duval_t1(**gas_data)},
        {"Model": "Duval's Triangle 4 (T3/D2/S)", "Diagnosis": diagnose_duval_t4(**gas_data)},
        {"Model": "Rogers Ratio Method (R1/R2/R5)", "Diagnosis": diagnose_rogers_ratio(**gas_data)},
        {"Model": "Doernenburg’s Method", "Diagnosis": diagnose_doernenburg(**gas_data)},
        {"Model": "Duval’s Pentagon (Conceptual)", "Diagnosis": diagnose_duval_pentagon(**gas_data)},
    ]

    # Display the summary table
    st.table(analysis_results)

    st.header("Diagnostic Model Dashboard")
    st.info("The red marker on the plots shows your input data point. The regions indicate common fault types.")

    # --- Tabbed Dashboard (Only including the requested tabs) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Duval T1", 
        "Duval T4", 
        "Rogers Ratios", 
        "Doernenburg",
        "Pentagon (Conceptual)"])

    with tab1:
        st.subheader("Duval Triangle 1: CH4 / C2H4 / C2H2")
        plot_duval_t1(**gas_data)
        st.markdown("""
            **Diagnosis Key:**
            - **PD**: Partial Discharge
            - **T1**: Thermal Fault T < 300°C
            - **T2/T3**: Thermal Fault (medium to high temp)
            - **D1/D2**: Discharge/Arcing
        """)

    with tab2:
        st.subheader("Duval Triangle 4: H2 / C2H2 / C2H4")
        plot_duval_t4(**gas_data)
        st.markdown("""
            **Diagnosis Key (High-temperature focus):**
            - **T3**: Severe Thermal Fault T > 700°C
            - **D2**: High Energy Arcing
            - **S**: Stray Gassing / Hot metal contacts
        """)

    with tab3:
        st.subheader("Rogers Ratio Method")
        st.text(f"Diagnosis: {diagnose_rogers_ratio(**gas_data)}")
        
        ratios = {
            'R1 (CH4/H2)': gas_data['CH4'] / gas_data['H2'] if gas_data['H2'] > 0 else float('inf'),
            'R2 (C2H4/CH4)': gas_data['C2H4'] / gas_data['CH4'] if gas_data['CH4'] > 0 else float('inf'),
            'R5 (C2H2/C2H4)': gas_data['C2H2'] / gas_data['C2H4'] if gas_data['C2H4'] > 0 else float('inf'),
        }
        
        st.bar_chart(ratios, color='#1e3a8a')
        st.markdown("Rogers method uses fixed ranges for three ratios (R1, R2, R5) to derive a diagnostic code.")

    with tab4:
        st.subheader("Doernenburg’s Method")
        st.text(f"Diagnosis: {diagnose_doernenburg(**gas_data)}")
        
        ratios_doernenburg = [
            {"Ratio": "CH4 / H2", "Value": gas_data['CH4'] / gas_data['H2'] if gas_data['H2'] > 0 else float('inf'), "Threshold": "> 1.0 (for T2)"},
            {"Ratio": "C2H2 / C2H4", "Value": gas_data['C2H2'] / gas_data['C2H4'] if gas_data['C2H4'] > 0 else float('inf'), "Threshold": "> 0.3 (for D1/D2)"},
            {"Ratio": "C2H2 / CH4", "Value": gas_data['C2H2'] / gas_data['CH4'] if gas_data['CH4'] > 0 else float('inf'), "Threshold": "< 0.7 (for D1)"},
        ]
        st.dataframe(ratios_doernenburg, hide_index=True)
        st.markdown("Doernenburg requires specific minimum gas levels to be applicable.")

    with tab5:
        st.subheader("Duval Pentagon (Conceptual)  ")
        st.warning("The Pentagon method uses 5 ratios for a 2D plot. A conceptual visualization is provided here.")
        st.code(f"Pentagon Diagnosis: {diagnose_duval_pentagon(**gas_data)}")
        st.markdown("The Pentagon method aims to unify the diagnoses of all 5 fault gases (H2, CH4, C2H4, C2H2, CO).")

else:
    st.info("Input your DGA gas concentrations (ppm) in the sidebar on the left and click 'Analyze DGA Data' to view the full fault analysis dashboard.")


st.markdown("---")
st.markdown("Developed for Utility Operators to rapidly assess DGA results.")

# Reset matplotlib settings to default after Streamlit uses them
plt.rcdefaults()
