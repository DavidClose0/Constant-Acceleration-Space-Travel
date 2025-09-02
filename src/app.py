"""A Streamlit app to calculate travel time, max velocity, fuel mass, total energy consumption, 
and liftoff power for a single-stage spacecraft traveling under constant acceleration."""
import streamlit as st
from decimal import Decimal, getcontext

getcontext().prec = 10 # Set decimal precision

st.set_page_config(page_title="Constant Acceleration Space Travel", page_icon=":rocket:")
st.title("Constant Acceleration Space Travel")

# Hide number input steppers
st.markdown(
    """<style>
    div[data-testid="stNumberInput"] button[data-testid="stNumberInputStepUp"],
    div[data-testid="stNumberInput"] button[data-testid="stNumberInputStepDown"] {
        display: none;
    }
    </style>""",
    unsafe_allow_html=True,
)

# Initialize session state variables
if "page" not in st.session_state:
    st.session_state.page = "calculator"
if "distance" not in st.session_state:
    st.session_state.distance = 55760000000 # m (minimum distance from Earth to Mars)
if "dry_mass" not in st.session_state:
    st.session_state.dry_mass = 1000 # kg
if "acceleration" not in st.session_state:
    st.session_state.acceleration = 20.0 # m/s^2
if "engine" not in st.session_state:
    st.session_state.engine = "LOX/LH2"

# Define engines and effective exhaust velocities
engines = {
    "LOX/LH2": 4400, 
    "NEXT Electrostatic Ion Thruster": 40000,
    "DS4G Ion Thruster": 210000
}

def format_time(seconds):
    """Convert seconds to the format years, days, hours, minutes, seconds."""
    whole_seconds = int(seconds)
    fractional_seconds = seconds - whole_seconds

    intervals = [
        ("year", 365 * 24 * 3600),
        ("day", 24 * 3600),
        ("hour", 3600),
        ("minute", 60),
    ]
    
    result = []
    for name, count in intervals:
        value = whole_seconds // count
        # Use scientific notation for large values (will only apply to years)
        if value >= 1e6:
            result.append(f"{value:.2e} {name}s")
        elif value == 1:
            result.append(f"{value} {name}")
        # Only add 0 values if there's already a larger unit in the result
        elif value > 1 or (value == 0 and result):
            result.append(f"{value} {name}s")
        whole_seconds %= count

    final_seconds = whole_seconds + fractional_seconds
    
    if final_seconds == 1:
        result.append(f"1 second")
    else:
        result.append(f"{final_seconds:.2f} seconds")

    return ', '.join(result)


def render_calculator_page():
    """Render the calculator page."""
    st.write("""Given initial parameters, calculate travel time, max velocity, fuel mass, total 
             energy consumption, and liftoff power for a single-stage spacecraft that linearly 
             accelerates at a constant rate to the halfway point, then decelerates at the same 
             rate to the destination. Does not take into account relativity or outside forces.""")
    
    with st.form("initial_parameters"):
        st.session_state.distance = st.number_input(
            "Distance to travel (m)", 
            value=st.session_state.distance
            )
        st.session_state.dry_mass = st.number_input(
            "Dry mass of spacecraft (kg)", 
            value=st.session_state.dry_mass
            )
        st.session_state.acceleration = st.number_input(
            "Constant acceleration (m/s²)", 
            value=st.session_state.acceleration, 
            step=.1, 
            format="%.1f"
            )
        st.session_state.engine = st.selectbox(
            "Engine", 
            options=[f"{k} ({engines[k]:,} m/s effective exhaust velocity)" for k in engines.keys()], 
            index=list(engines.keys()).index(st.session_state.engine)).split(" (")[0]
        submitted = st.form_submit_button("Launch!")

        if submitted:
            # Input validation
            if st.session_state.acceleration <= 0:
                st.error("Acceleration must be greater than 0 m/s².")
                return
            if st.session_state.dry_mass <= 0:
                st.error("Dry mass must be greater than 0 kg.")
                return
            if st.session_state.distance <= 0:
                st.error("Distance must be greater than 0 m.")
                return
            st.session_state.page = "results"
            st.rerun()


def render_results_page():
    """Render the results page."""
    if st.button("Back"):
        st.session_state.page = "calculator"
        st.rerun()
        return
    
    st.header("Results")
    
    # Retrieve input values
    distance = st.session_state.distance
    dry_mass = st.session_state.dry_mass
    acceleration = st.session_state.acceleration
    v_e = engines[st.session_state.engine]

    # Calculations
    travel_time = 2 * (distance / acceleration) ** 0.5
    max_velocity = (acceleration * distance) ** 0.5

    # Throw error if max velocity exceeds speed of light
    if max_velocity >= 299792458:
        st.error("Maximum velocity exceeds the speed of light.")
        return

    # Use Decimal calculations to avoid range error in exp function
    dry_mass_dec = Decimal(dry_mass)
    acceleration_dec = Decimal(acceleration)
    v_e_dec = Decimal(v_e)
    max_velocity_dec = Decimal(max_velocity)

    exponent = (2 * max_velocity_dec) / v_e_dec
    fuel_mass_dec = dry_mass_dec * (exponent.exp() - 1)
    total_mass_dec = dry_mass_dec + fuel_mass_dec
    total_energy_dec = Decimal("0.5") * fuel_mass_dec * v_e_dec ** 2
    liftoff_power_dec = Decimal("0.5") * total_mass_dec * acceleration_dec * v_e_dec

    # Display results
    st.write(f"**Travel time:** {format_time(travel_time)}")    
    with st.expander("Show calculation"):
        st.latex(r'''
        \text{Use the kinematic equation:} \\
        x(t) = v_0 t + \frac{1}{2}at^2 \\
        \text{For the first half, distance } d_{half} = \frac{d_{total}}{2}, v_0=0. \\
        \text{Let } t_{half} \text{ be the time for this half:} \\
        d_{half} = \frac{1}{2} a t_{half}^2 \implies t_{half} = \sqrt{\frac{2d_{half}}{a}} \\
        t_{total} = 2 \cdot t_{half} = 2 \sqrt{\frac{2d_{half}}{a}} \\
        t_{total} = 2 \sqrt{\frac{2(d_{total}/2)}{a}} = 2\sqrt{\frac{d_{total}}{a}}
        ''')

    st.write(f"**Maximum velocity:** {max_velocity:,.2f} m/s "
             f"({(max_velocity / 299792458) * 100:.6f}% c)")
    with st.expander("Show calculation"):
        st.latex(r'''
        \text{Use the kinematic equation:} \\
        v(t) = v_0 + at \\
        \text{Max velocity is reached after done accelerating, at } t_{half}, \text{ with } v_0=0: \\
        v_{max} = a t_{half} \\
        \text{Substitute } t_{half} = \sqrt{\frac{d_{total}}{a}}: \\
        v_{max} = a \sqrt{\frac{d_{total}}{a}} = \sqrt{a^2 \frac{d_{total}}{a}} = \sqrt{a d_{total}}
        ''')

    if fuel_mass_dec > 1e6:
        st.write(f"**Fuel mass required:** {fuel_mass_dec:.2e} kg")
    else:
        st.write(f"**Fuel mass required:** {fuel_mass_dec:,.2f} kg")
    with st.expander("Show calculation"):
        st.latex(r'''
        \text{Use the rocket equation:} \\
        \Delta v = v_e \ln\left(\frac{m_{initial}}{m_{final}}\right) \\
        \text{Total } \Delta v \text{ includes acceleration and deceleration halves:} \quad \Delta v_{total} = 2v_{max} \\
        \text{The final mass is the dry mass:} \quad m_{final} = m_{dry} \\
        2v_{max} = v_e \ln\left(\frac{m_{initial}}{m_{dry}}\right) \\
        m_{initial} = m_{dry} \cdot e^{\left(\frac{2v_{max}}{v_e}\right)} \\
        \text{Fuel mass is the difference between initial and dry mass:} \\
        m_{fuel} = m_{initial} - m_{dry} = m_{dry} \left( e^{\left(\frac{2v_{max}}{v_e}\right)} - 1 \right)
        ''')

    if total_energy_dec > 1e6:
        st.write(f"**Total energy usage:** {total_energy_dec:.2e} J")
    else:
        st.write(f"**Total energy usage:** {total_energy_dec:,.2f} J")
    with st.expander("Show calculation"):
        st.latex(r'''
        \text{Use the kinetic energy formula:} \\
        E = \frac{1}{2}mv^2 \\
        \text{The total mass of the fuel } m_{fuel} \text{ is expelled at effective exhaust velocity } v_e. \\
        E_{total} = \frac{1}{2} m_{fuel} v_e^2
        ''')

    if liftoff_power_dec > 1e6:
        st.write(f"**Liftoff power:** {liftoff_power_dec:.2e} W")
    else:
        st.write(f"**Liftoff power:** {liftoff_power_dec:,.2f} W")
    with st.expander("Show calculation"):
        st.latex(r'''
        \text{Power is the kinetic energy imparted to the exhaust per second:} \\
        P = \frac{1}{2} \dot{m} v_e^2 \quad (\text{where } \dot{m} \text{ is mass flow rate}) \\
        \text{Thrust is given by: } F = \dot{m} v_e \implies \dot{m} = \frac{F}{v_e} \\
        \text{For constant acceleration, thrust at time t is: } F(t) = m(t) \cdot a \\
        \text{At liftoff (t=0), mass is at its maximum, } m_{initial}: \\
        F_0 = m_{initial} \cdot a \\
        \text{Substitute } F_0 \text{ to find the initial power } P_0: \\
        P_0 = \frac{1}{2} \left(\frac{F_0}{v_e}\right) v_e^2 = \frac{1}{2} F_0 v_e = \frac{1}{2} (m_{initial}) a v_e \\
        \text{Substitute } m_{initial} = m_{dry} + m_{fuel}: \\
        P_0 = \frac{1}{2} (m_{dry} + m_{fuel}) a v_e
        ''')
    
if st.session_state.page == "calculator":
    render_calculator_page()
elif st.session_state.page == "results":
    render_results_page()
