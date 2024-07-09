import streamlit as st
import streamlit_extras
import pandas as pd
import os

from streamlit_extras.stylable_container import stylable_container

custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'DM Sans', sans-serif;
}
</style>
"""

st.set_page_config(
    page_title="Mux Pricing Calculator",
    layout="wide",
    initial_sidebar_state="auto",
)
st.markdown(custom_css, unsafe_allow_html=True)


@st.cache_data
def load_pricing_csv():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the file path
    file_path = os.path.join(current_dir, 'data', 'rates.csv')
    # Load the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    return df


pricing_tiers = load_pricing_csv()

st.title('Mux Pricing Calculator')

default_values = {
    'encoding_volume': 1000,
    'live_encoding_volume': 500,
    'storage_volume': 6000,
    'streaming_volume': 20000,
    'percent_baseline': 100,
    'cold_percent': 60,
    'infrequent_percent': 10,
    'hot_percent': 30,
    'resolution_mix_720p': 100,
    'resolution_mix_1080p': 0,
    'resolution_mix_1440p': 0,
    'resolution_mix_2160p': 0,
    'bandwidth_gb': 100,
    'bandwidth_bitrate': 3.5,
    'library_size_gb': 100,
    'new_videos_per_month': 1000,
    'new_live_videos_per_month': 0,
    'avg_video_length': 5.0,
    'baseline_toggle': False,
    'data': pd.DataFrame({
        'SKU Name': ['baseline_encoding_720p', 'live_encoding_720p', 'baseline_storage_720p', 'streaming_720p'],
        'Usage Value': [1000, 500, 6000, 20000]
    })
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value


def calculate_spend(df):
    results = []
    for _, row in df.iterrows():
        filtered_pricing_df = pricing_tiers[
            (pricing_tiers['unique_key'] == row['SKU Name']) &
            (pricing_tiers['start'] <= row['Usage Value']) &
            (pricing_tiers['end'] > row['Usage Value'])
            ]
        pricing_row = filtered_pricing_df.iloc[0]
        # Set variable values
        unit_price = pricing_row['price']
        monthly_usage = row['Usage Value']
        previous_tier_spend = pricing_row['previous_tier_max_spend']
        marginal_spend = (monthly_usage - pricing_row['start']) * unit_price
        total_spend = previous_tier_spend + marginal_spend

        effective_rate = total_spend / monthly_usage
        results.append({
            'sku_category': pricing_row['sku_category'],
            'sku': row['SKU Name'],
            'usage': monthly_usage,
            'effective_rate': effective_rate,
            'total_spend': total_spend,
        })
    return pd.DataFrame(results)


def calculate_usage(resolution, source_sku, default_volume, default_resolution_mix, baseline_encoding, storage_type):
    if baseline_encoding == True:
        if st.session_state.get("baseline_toggle", default_values['baseline_toggle']) == True:
            baseline_multiplier = 1
        else:
            baseline_multiplier = 0
    elif baseline_encoding == False:
        if st.session_state.get("baseline_toggle", default_values['baseline_toggle']) == True:
            baseline_multiplier = 0
        else:
            baseline_multiplier = 1
    else:
        baseline_multiplier = 1
    if storage_type == 'cold':
        storage_multiplier = st.session_state.get("cold_percent", default_values['cold_percent']) / 100
    elif storage_type == 'infrequent':
        storage_multiplier = st.session_state.get("infrequent_percent", default_values['infrequent_percent']) / 100
    elif storage_type == 'hot':
        storage_multiplier = st.session_state.get("hot_percent", default_values['hot_percent']) / 100
    else:
        storage_multiplier = 1
    value = st.session_state.get(f"{source_sku}", default_volume) * st.session_state.get(
        "resolution_mix_" + f"{resolution}", default_resolution_mix) / 100 * baseline_multiplier * storage_multiplier
    return value


# Encoding SKUs
def update_dataframe():
    sku_usage_dict = {
        # VOD Encoding SKUs
        'baseline_encoding_720p': calculate_usage('720p', 'encoding_volume', default_values['encoding_volume'],
                                                  default_values['resolution_mix_720p'], True, None),
        'baseline_encoding_1080p': calculate_usage('1080p', 'encoding_volume', default_values['encoding_volume'],
                                                   default_values['resolution_mix_1080p'], True, None),
        'smart_encoding_720p': calculate_usage('720p', 'encoding_volume', default_values['encoding_volume'],
                                               default_values['resolution_mix_720p'],
                                               False, None),
        'smart_encoding_1080p': calculate_usage('1080p', 'encoding_volume', default_values['encoding_volume'],
                                                default_values['resolution_mix_1080p'], False, None),
        'smart_encoding_1440p': calculate_usage('1440p', 'encoding_volume', default_values['encoding_volume'],
                                                default_values['resolution_mix_1440p'], False, None),
        'smart_encoding_2160p': calculate_usage('2160p', 'encoding_volume', default_values['encoding_volume'],
                                                default_values['resolution_mix_2160p'], False, None),
        # Live Encoding SKUs
        'live_encoding_720p': calculate_usage('720p', 'live_encoding_volume', default_values['live_encoding_volume'],
                                              default_values['resolution_mix_720p'], None, None),
        'live_encoding_1080p': calculate_usage('1080p', 'live_encoding_volume', default_values['live_encoding_volume'],
                                               default_values['resolution_mix_1080p'], None, None),
        'live_encoding_1440p': calculate_usage('1440p', 'live_encoding_volume', default_values['live_encoding_volume'],
                                               default_values['resolution_mix_1440p'], None, None),
        'live_encoding_2160p': calculate_usage('2160p', 'live_encoding_volume', default_values['live_encoding_volume'],
                                               default_values['resolution_mix_2160p'], None, None),
        # Hot Smart Storage SKUs
        'smart_storage_720p': calculate_usage('720p', 'storage_volume', default_values['storage_volume'],
                                              default_values['resolution_mix_720p'],
                                              False, 'hot'),
        'smart_storage_1080p': calculate_usage('1080p', 'storage_volume', default_values['storage_volume'],
                                               default_values['resolution_mix_1080p'],
                                               False, 'hot'),
        'smart_storage_1440p': calculate_usage('1440p', 'storage_volume', default_values['storage_volume'],
                                               default_values['resolution_mix_1440p'],
                                               False, 'hot'),
        'smart_storage_2160p': calculate_usage('2160p', 'storage_volume', default_values['storage_volume'],
                                               default_values['resolution_mix_2160p'],
                                               False, 'hot'),
        # Cold Smart Storage SKUs
        'smart_cold_storage_720p': calculate_usage('720p', 'storage_volume', default_values['storage_volume'],
                                                   default_values['resolution_mix_720p'], False, 'cold'),
        'smart_cold_storage_1080p': calculate_usage('1080p', 'storage_volume', default_values['storage_volume'],
                                                    default_values['resolution_mix_1080p'],
                                                    False, 'cold'),
        'smart_cold_storage_1440p': calculate_usage('1440p', 'storage_volume', default_values['storage_volume'],
                                                    default_values['resolution_mix_1440p'],
                                                    False, 'cold'),
        'smart_cold_storage_2160p': calculate_usage('2160p', 'storage_volume', default_values['storage_volume'],
                                                    default_values['resolution_mix_2160p'],
                                                    False, 'cold'),
        # Infrequent Smart Storage SKUs
        'smart_infrequent_storage_720p': calculate_usage('720p', 'storage_volume', default_values['storage_volume'],
                                                         default_values['resolution_mix_720p'], False, 'infrequent'),
        'smart_infrequent_storage_1080p': calculate_usage('1080p', 'storage_volume', default_values['storage_volume'],
                                                          default_values['resolution_mix_1080p'], False, 'infrequent'),
        'smart_infrequent_storage_1440p': calculate_usage('1440p', 'storage_volume', default_values['storage_volume'],
                                                          default_values['resolution_mix_1440p'], False, 'infrequent'),
        'smart_infrequent_storage_2160p': calculate_usage('2160p', 'storage_volume', default_values['storage_volume'],
                                                          default_values['resolution_mix_2160p'], False, 'infrequent'),
        # Baseline Smart Storage SKUs
        'baseline_storage_720p': calculate_usage('720p', 'storage_volume', default_values['storage_volume'],
                                                 default_values['resolution_mix_720p'],
                                                 True, 'hot'),
        'baseline_storage_1080p': calculate_usage('1080p', 'storage_volume', default_values['storage_volume'],
                                                  default_values['resolution_mix_1080p'], True, 'hot'),
        'baseline_infrequent_storage_720p': calculate_usage('720p', 'storage_volume', default_values['storage_volume'],
                                                            default_values['resolution_mix_720p'],
                                                            True, 'infrequent'),
        'baseline_infrequent_storage_1080p': calculate_usage('1080p', 'storage_volume',
                                                             default_values['storage_volume'],
                                                             default_values['resolution_mix_1080p'], True,
                                                             'infrequent'),
        'baseline_cold_storage_720p': calculate_usage('720p', 'storage_volume', default_values['storage_volume'],
                                                      default_values['resolution_mix_720p'],
                                                      True, 'cold'),
        'baseline_cold_storage_1080p': calculate_usage('1080p', 'storage_volume', default_values['storage_volume'],
                                                       default_values['resolution_mix_1080p'], True, 'cold'),
        # Streaming SKUs
        'streaming_720p': calculate_usage('720p', 'streaming_volume', default_values['streaming_volume'],
                                          default_values['resolution_mix_720p'],
                                          None, None),
        'streaming_1080p': calculate_usage('1080p', 'streaming_volume', default_values['streaming_volume'],
                                           default_values['resolution_mix_1080p'],
                                           None, None),
        'streaming_1440p': calculate_usage('1440p', 'streaming_volume', default_values['streaming_volume'],
                                           default_values['resolution_mix_1440p'],
                                           None, None),
        'streaming_2160p': calculate_usage('2160p', 'streaming_volume', default_values['streaming_volume'],
                                           default_values['resolution_mix_2160p'],
                                           None, None)
    }
    usage_df = pd.DataFrame(list(sku_usage_dict.items()), columns=['SKU Name', 'Usage Value'])
    st.session_state.data = usage_df


def format_spend(input_value):
    formatted_spend = f"${input_value:,.0f}".replace('$-', '-$')
    return formatted_spend


# Define functions to update target variables
def update_usage_volumes():
    st.session_state['encoding_volume'] = st.session_state['encoding_volume_input']
    st.session_state['live_encoding_volume'] = st.session_state['live_encoding_volume_input']
    st.session_state['streaming_volume'] = st.session_state['streaming_volume_input']
    st.session_state['storage_volume'] = st.session_state['storage_volume_input']


def update_baseline_toggle():
    st.session_state['baseline_toggle'] = st.session_state['baseline_toggle_input']
    update_dataframe()

def update_gb_volumes():
    st.session_state['bandwidth_gb'] = st.session_state['bandwidth_gb_input']
    st.session_state['bandwidth_bitrate'] = st.session_state['bandwidth_bitrate_input']
    st.session_state['library_size_gb'] = st.session_state['library_size_gb_input']
    st.session_state['new_videos_per_month'] = st.session_state['new_videos_per_month_input']
    st.session_state['new_live_videos_per_month'] = st.session_state['new_live_videos_per_month_input']
    st.session_state['avg_video_length'] = st.session_state['avg_video_length_input']


def update_encoding_tier():
    st.session_state['percent_baseline'] = st.session_state['percent_baseline_input']


def update_storage_lifecycle():
    st.session_state['cold_percent'] = st.session_state['cold_percent_input']
    st.session_state['infrequent_percent'] = st.session_state['infrequent_percent_input']
    st.session_state['hot_percent'] = st.session_state['hot_percent_input']


def update_resolution_mix():
    st.session_state['resolution_mix_720p'] = st.session_state['resolution_mix_720p_input']
    st.session_state['resolution_mix_1080p'] = st.session_state['resolution_mix_1080p_input']
    st.session_state['resolution_mix_1440p'] = st.session_state['resolution_mix_1440p_input']
    st.session_state['resolution_mix_2160p'] = st.session_state['resolution_mix_2160p_input']


def update_input_variables():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.number_input("Input On Demand Minutes", min_value=0,
                        step=100, value=st.session_state.encoding_volume, key='encoding_volume_input',
                        on_change=update_usage_volumes)
    with col2:
        st.number_input("Input Live Minutes", min_value=0,
                        step=100,
                        value=st.session_state.live_encoding_volume, key='live_encoding_volume_input',
                        on_change=update_usage_volumes)
    with col3:
        st.number_input("Input Streaming Minutes", min_value=0,
                        step=1000,
                        value=st.session_state.streaming_volume, key='streaming_volume_input',
                        on_change=update_usage_volumes)
    with col4:
        st.number_input("Input Storage Minutes", min_value=0, step=100,
                        value=st.session_state.storage_volume, key='storage_volume_input',
                        on_change=update_usage_volumes)


def calculate_totals(df):
    st.session_state.spend_data = calculate_spend(df)
    spend_df = st.session_state.spend_data
    storage_spend = st.session_state.spend_data[(spend_df['sku_category'] == 'Storage')]['total_spend'].sum()
    encoding_spend = spend_df[(spend_df['sku_category'] == 'Encoding')]['total_spend'].sum()
    streaming_spend = spend_df[(spend_df['sku_category'] == 'Streaming')]['total_spend'].sum()
    total_spend = spend_df['total_spend'].sum() - 100
    total_spend_developer_plan = max(total_spend, 10)
    developer_plan_cost = 10
    mux_credits = max(-100, -1 * (storage_spend + encoding_spend + streaming_spend))
    return spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits, total_spend_developer_plan, developer_plan_cost


def display_totals(spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits,
                   total_spend_developer_plan, developer_plan_cost):
    with st.container(border=True):
        st.header("Total Spend with Mux Starter Plan ($10/month)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric('Total Monthly Spend', format_spend(total_spend_developer_plan))
        with col2:
            st.metric('Total Annual Spend', format_spend(total_spend_developer_plan * 12))
        st.write("Estimates include volume-based discounts; assumes",  st.session_state.resolution_mix_720p, "% of videos and delivery at 720p resolution and ", st.session_state.cold_percent, "% of videos in cold storage; values can be updated in Advanced Calculator.")
    with st.container(border=True):
        st.header("Monthly Spend by SKU Category")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric('Monthly Streaming Spend', format_spend(streaming_spend))
        with col2:
            st.metric('Monthly Encoding Spend', format_spend(encoding_spend))
        with col3:
            st.metric('Monthly Storage Spend', format_spend(storage_spend))
        with col4:
            st.metric('Monthly Starter Plan Cost', format_spend(developer_plan_cost))
        with col5:
            st.metric('Mux Credits (inc. w/ Starter Plan)', format_spend(mux_credits))
    with st.container(border=True):
        st.header("Spend Details (excludes Starter Plan credits)")
        st.dataframe(spend_df,
                     column_config={
                         'sku_category': 'SKU Category',
                         'sku': 'SKU Name',
                         'usage': 'Monthly Usage',
                         'effective_rate': st.column_config.NumberColumn(
                             label='Effective Rate',
                             format="$%.4f"
                         ),
                         'total_spend': st.column_config.NumberColumn(
                             label='Monthly Spend',
                             format="$%d"
                         )
                     })

def button_layouts():
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button('Update Totals'):
                update_dataframe()
        with col2:
            st.session_state.baseline_toggle = st.toggle("Use baseline encoding tier", value=False, on_change=update_baseline_toggle, key='baseline_toggle_input', help="Enables Baseline Encoding Tier for all eligible assets")
# Main App Layout

st.logo('images/Mux Logo Medium Charcoal.png', link="https://www.mux.com")


def home():
    update_dataframe()
    button_layouts()
    spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits, total_spend_developer_plan, developer_plan_cost = calculate_totals(st.session_state.data)
    with stylable_container(
      key="container_with_background",
      css_styles="""
            {
                border: 3px solid #ffcccc; /* light pink border */
                background-color: #fff7fcff; /* light pink background */
                padding: 20px; /* adjust padding as needed */
            }
            """,
    ):
        st.header("Usage")
        update_input_variables()
    display_totals(spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits,
                   total_spend_developer_plan, developer_plan_cost)


def advanced():
    button_layouts()
    # Bring in calculated variables
    spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits, total_spend_developer_plan, developer_plan_cost = calculate_totals(st.session_state.data)
    with stylable_container(
            key="container_with_background",
            css_styles="""
            {
                border: 3px solid #ffcccc; /* light pink border */
                background-color: #fff7fcff; /* light pink background */
                padding: 20px; /* adjust padding as needed */
            }
            """,
    ):
        st.header("Usage")
        update_input_variables()
    with st.container():
        st.header("Cold Storage Mix")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input("Percent Cold", min_value=0, max_value=100, step=10,
                            value=st.session_state.cold_percent, key='cold_percent_input',
                            on_change=update_storage_lifecycle)
        with col2:
            st.number_input("Percent Infrequent", min_value=0, max_value=100,
                            step=10,
                            value=st.session_state.infrequent_percent, key='infrequent_percent_input',
                            on_change=update_storage_lifecycle)
        with col3:
            st.number_input("Percent Hot", min_value=0, max_value=100, step=10,
                            value=st.session_state.hot_percent, key='hot_percent_input',
                            on_change=update_storage_lifecycle)
    if st.session_state.get("cold_percent", 60) + st.session_state.get("infrequent_percent", 10) + st.session_state.get(
            "hot_percent", 30) != 100:
        st.markdown(":red[Hot/Cold designations do not add to 100%]")

    with st.container():
        st.header("Resolution Mix")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.number_input("Percent 720p", min_value=0, max_value=100, step=10,
                            value=st.session_state.resolution_mix_720p, key='resolution_mix_720p_input',
                            on_change=update_resolution_mix)
        with col2:
            st.number_input("Percent 1080p", min_value=0, max_value=100,
                            step=10,
                            value=st.session_state.resolution_mix_1080p, key='resolution_mix_1080p_input',
                            on_change=update_resolution_mix)
        with col3:
            st.number_input("Percent 1440p", min_value=0, max_value=100,
                            step=10,
                            value=st.session_state.resolution_mix_1440p, key='resolution_mix_1440p_input',
                            on_change=update_resolution_mix)
        with col4:
            st.number_input("Percent 2160p", min_value=0, max_value=100,
                            step=10,
                            value=st.session_state.resolution_mix_2160p, key='resolution_mix_2160p_input',
                            on_change=update_resolution_mix)

    if st.session_state.resolution_mix_720p + st.session_state.resolution_mix_1080p + st.session_state.resolution_mix_1440p + st.session_state.resolution_mix_2160p != 100:
        st.markdown(":red[Resolutions do not add to 100%]")

    # Bring in Totals from main logic above
    display_totals(spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits,
                   total_spend_developer_plan, developer_plan_cost)


def calculate_gb_volumes():
    st.session_state.storage_volume = round(st.session_state.library_size_gb * 8 * 1024 / st.session_state.bandwidth_bitrate / 60)
    st.session_state.streaming_volume = round(st.session_state.bandwidth_gb * 8 * 1024 / st.session_state.bandwidth_bitrate / 60)
    # Zero out encoding volumes
    st.session_state.encoding_volume = 0
    st.session_state.live_encoding_volume = 0

def super_advanced():
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button('Update Totals'):
                calculate_gb_volumes()
                update_dataframe()
        with col2:
            st.session_state.baseline_toggle = st.toggle("Use baseline encoding tier", value=False, on_change=update_baseline_toggle, key='baseline_toggle_input', help="Enables Baseline Encoding Tier for all eligible assets")
    with stylable_container(
      key="container_with_background",
      css_styles="""
            {
                border: 3px solid #ffcccc; /* light pink border */
                background-color: #fff7fcff; /* light pink background */
                padding: 20px; /* adjust padding as needed */
            }
            """,
    ):
        st.header("CDN and Storage Usage")
        spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits, total_spend_developer_plan, developer_plan_cost = calculate_totals(st.session_state.data)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.number_input("Monthly bandwidth in GB", value=st.session_state.bandwidth_gb, min_value=0, step=10, key="bandwidth_gb_input", on_change=update_gb_volumes)
        with col2:
            st.number_input("Avg. video bitrate (MBPS)", value=st.session_state.bandwidth_bitrate, min_value=0.0, max_value=10.0, step=0.1, key="bandwidth_bitrate_input", on_change=update_gb_volumes)
        with col3:
            st.number_input("Current library size in GB", value=st.session_state.library_size_gb, min_value=0, step=10, key="library_size_gb_input", on_change=update_gb_volumes)
    display_totals(spend_df, storage_spend, encoding_spend, streaming_spend, total_spend, mux_credits,
                   total_spend_developer_plan, developer_plan_cost)

st.sidebar.title("Pages")
selection = st.sidebar.radio("Go to", ["Basic Calculator (Minutes)", "Advanced Calculator (Minutes)", "Basic Calculator (GBs)"])


if selection == "Basic Calculator (Minutes)":
    home()
elif selection == "Advanced Calculator (Minutes)":
    advanced()
elif selection == "Basic Calculator (GBs)":
    super_advanced()