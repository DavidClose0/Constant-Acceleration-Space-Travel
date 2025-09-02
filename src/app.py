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
    max_velocity = acceleration * (travel_time / 2)

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
    st.write(f"**Maximum velocity:** {max_velocity:,.2f} m/s "
             f"({(max_velocity / 299792458) * 100:.6f}% c)")
    if fuel_mass_dec > 1e6:
        st.write(f"**Fuel mass required:** {fuel_mass_dec:.2e} kg")
    else:
        st.write(f"**Fuel mass required:** {fuel_mass_dec:,.2f} kg")
    if total_energy_dec > 1e6:
        st.write(f"**Total energy usage:** {total_energy_dec:.2e} J")
    else:
        st.write(f"**Total energy usage:** {total_energy_dec:,.2f} J")
    if liftoff_power_dec > 1e6:
        st.write(f"**Liftoff power:** {liftoff_power_dec:.2e} W")
    else:
        st.write(f"**Liftoff power:** {liftoff_power_dec:,.2f} W")
    
if st.session_state.page == "calculator":
    render_calculator_page()
elif st.session_state.page == "results":
    render_results_page()
