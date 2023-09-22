import streamlit as st
import re
import datetime
from google_play_scraper import app
from google_play_scraper import Sort, reviews
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

ct = [
    'us', 'au', 'ca', 'cn', 'fr', 'de', 'it', 'kr', 'jp', 'ru', 'my', 'sg',
    'tw', 'id', 'th', 'vn', 'in', 'gb', 'mo', 'hk', 'bh', 'qa', 'az', 'lb',
    'kw', 'il', 'eg', 'br', 'cl', 'mx', 'tr', 'es', 'nl', 'no', 'pl', 'pt',
    'ph', 'sa', 'ae', 'ke', 'ng', 'nz', 'ar'
]



lg = [
    'en-us', 'af', 'am', 'ar', 'az', 'be', 'bg', 'bn', 'bs', 'ca', 'cs', 'da',
    'de', 'de-at', 'de-ch', 'el', 'en', 'en-au', 'en-ca', 'en-gb', 'en-ie',
    'en-in', 'en-nz', 'en-sg', 'en-za', 'es', 'es-419', 'es-ar', 'es-bo',
    'es-cl', 'es-co', 'es-cr', 'es-do', 'es-ec', 'es-gt', 'es-hn', 'es-mx',
    'es-ni', 'es-pa', 'es-pe', 'es-pr', 'es-py', 'es-sv', 'es-us', 'es-uy',
    'es-ve', 'et', 'eu', 'fa', 'fi', 'fil', 'fr', 'fr-ca', 'fr-ch', 'gl', 'gsw',
    'gu', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka', 'kk',
    'km', 'kn', 'ko', 'ky', 'ln', 'lo', 'lt', 'lv', 'mk', 'ml', 'mn', 'mr',
    'ms', 'my', 'no', 'ne', 'nl', 'or', 'pa', 'pl', 'pt', 'pt-br', 'pt-pt',
    'ro', 'ru', 'si', 'sk', 'sl', 'sq', 'sr', 'sr-latn', 'sv', 'sw', 'ta',
    'te', 'th', 'tr', 'uk', 'ur', 'uz', 'vi', 'zh', 'zh-cn'
]


lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.12.1/css/all.css" crossorigin="anonymous">'

def extract_url_parameters(url):
    id_pattern = r'id=([^&]+)'
    hl_pattern = r'hl=([^&]+)'
    gl_pattern = r'gl=([^&]+)'

    id_match = re.search(id_pattern, url)
    hl_match = re.search(hl_pattern, url)
    gl_match = re.search(gl_pattern, url)

    app_id = id_match.group(1) if id_match else None
    hl = hl_match.group(1) if hl_match else "en"  # Default to English ("en") if not found
    gl = gl_match.group(1) if gl_match else "us"  # Default to United States ("us") if not found

    return app_id, hl, gl

@st.cache
def info_app_cached(app_id, hl, gl):
    try:
        result = app(
            app_id,
            lang=hl,
            country=gl
        )

        reviews = result['reviews']
        installs = result['installs']
        score = result['score']

    except Exception as e:
        print("An error occurred:", str(e))
        score, reviews, installs = None, None, None

    return score, reviews, installs

@st.cache
def dowload_reviews_cached(app_id, hl, gl):
    try:
        result, continuation_token = reviews(
            app_id,
            lang=hl,  # defaults to 'en'
            country=gl,  # defaults to 'us'
            sort=Sort.NEWEST,  # defaults to Sort.NEWEST
            count=40000,  # defaults to 100
            filter_score_with=None  # defaults to None(means all score)
        )
        df = pd.DataFrame(result)
        df = df[['at', 'userName', 'content', 'replyContent', 'score', 'thumbsUpCount', 'reviewCreatedVersion']]
    except Exception as e:
        print("An error occurred:", str(e))
        df = pd.DataFrame()
    return df



def generate_card(title, iconname, value):
    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    wch_colour_box = (255, 255, 255)
    wch_colour_font = (0, 0, 0)
    fontsize = 50
    iconname = iconname
    rating = value

    htmlstr = f"""
                    <p style='background-color: rgb(
                        {wch_colour_box[0]}, 
                        {wch_colour_box[1]}, 
                        {wch_colour_box[2]}, 0.75
                    ); 
                    color: rgb(
                        {wch_colour_font[0]}, 
                        {wch_colour_font[1]}, 
                        {wch_colour_font[2]}, 0.75
                    ); 
                    font-size: {fontsize}px;    
                    border-radius: 7px; 
                    padding-top: 40px; 
                    padding-bottom: 40px; 
                    line-height:25px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);'>
                    <i class='{iconname}' style='font-size: 40px; color: #4da9df;'></i>&nbsp;{rating}</p>
                """
    st.markdown(lnk + htmlstr, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Eco Reviews Dashboard",
        layout="wide",
        page_icon="logo.png"
    )

    st.markdown("<style>div.block-container {padding-top:1rem;}</style>", unsafe_allow_html=True)
    st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; color: #4da9df;'>Eco Reviews Dashboard</h1>", unsafe_allow_html=True)
    timestamp = datetime.date.today()
    st.markdown(f"<p style='text-align: center;'>Last updated on {timestamp}</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        text_input = st.text_input("Enter Google Play App URL 👇")
        app_id, hl, gl = extract_url_parameters(text_input)
        if not app_id:
            st.warning("Warning: Invalid Google Play App URL")

    with col2:
        gl = st.selectbox(
            label="Country/Region",
            options=ct,
            index=ct.index(gl) if gl in ct else 0
        )

    with col3:
        hl = st.selectbox(
            label="Language",
            options=lg,
            index=lg.index(hl) if hl in lg else 0
        )

    if text_input or gl or hl:
        score, reviews, installs = info_app_cached(app_id, hl, gl)

        if installs:
            col1, col2, col3 = st.columns(3)
            with col1:
                generate_card("Average Rating", "fas fa-star", score)

            with col2:
                generate_card("Total Reviews", "fas fa-comments", reviews)

            with col3:
                generate_card("Total Downloads Since Release", "fas fa-download", installs)

        reviews_df = dowload_reviews_cached(app_id, hl, gl)

        if len(reviews_df) > 0:
            col1, col2 = st.columns(2)
            startDate = pd.to_datetime(reviews_df["at"]).min()
            endDate = pd.to_datetime(reviews_df["at"]).max()

            with col1:
                date1 = pd.to_datetime(st.date_input("Start Date", startDate))

            with col2:
                date2 = pd.to_datetime(st.date_input("End Date", endDate))

            reviews_filtered_df = reviews_df[(reviews_df["at"] >= date1) & (reviews_df["at"] <= date2)].copy()

            st.sidebar.header("Choose your filter: ")
            unique_versions = reviews_filtered_df["reviewCreatedVersion"].unique()
            unique_versions = [version for version in unique_versions if version is not None]

            version = st.sidebar.multiselect("Pick your version", unique_versions)
            if not version:
                version_filtered_df = reviews_filtered_df.copy()
            else:
                version_filtered_df = reviews_filtered_df[reviews_filtered_df["reviewCreatedVersion"].isin(version)]

            score = st.sidebar.multiselect("Pick the score", version_filtered_df["score"].unique())
            if not score:
                score_filtered_df = version_filtered_df.copy()
            else:
                score_filtered_df = version_filtered_df[version_filtered_df["score"].isin(score)]

            if not version and not score:
                filtered_df = reviews_filtered_df
            elif version and score:
                filtered_df = score_filtered_df
            elif version:
                filtered_df = version_filtered_df
            elif score:
                filtered_df = score_filtered_df


            with col1:
                fig1 = px.pie(filtered_df, values="score", names="score", hole=0.5)
                fig1.update_traces(text=filtered_df["score"], textposition="outside")
                fig1.update_layout(
                    title="Star Rating Pie Chart",
                )
                st.plotly_chart(fig1, use_container_width=True)

                # st.subheader("Star Over Time")
                # fig2 = go.Figure()
                # fig2.add_trace(go.Scatter(x=filtered_df['at'], y=filtered_df['score'], mode='lines+markers'))
                #
                # fig2.update_layout(
                #     title="Star Over Time",
                #     xaxis_title="Date",
                #     yaxis_title="Star",
                # )
                #
                # st.plotly_chart(fig2, use_container_width=True)

                # st.subheader("Star Over Time")

                # Sử dụng px.scatter để tạo biểu đồ với màu sắc dựa trên cột 'score'
                fig2 = px.scatter(
                    filtered_df,
                    x='at',
                    y='score',
                    color='score',  # Dựa trên giá trị cột 'score' để xác định màu sắc
                    color_continuous_scale='Viridis',  # Chọn bảng màu (có thể thay đổi)
                    title="Star Over Time",
                    labels={'at': 'Date', 'score': 'Star'},
                )

                st.plotly_chart(fig2, use_container_width=True)

            with col2:
                st.dataframe(filtered_df, height=730)

                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Filtered Data as CSV",
                    data=csv_data,
                    file_name="filtered_data.csv",
                    key="filtered_data_csv",
                )

                content_csv_data = filtered_df['content'].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download content Column as CSV",
                    data=content_csv_data,
                    file_name="content_column.csv",
                    key="content_column_csv",
                )


            st.subheader("AI Chat Reviews")

            st.info("The AI Chat Reviews feature will be launching soon. Stay tuned for updates.")


if __name__ == '__main__':
    main()