import streamlit as st
import re
import datetime
from google_play_scraper import app
from google_play_scraper import Sort, reviews
import pandas as pd
import plotly.express as px
import altair as alt
import time
import openai
import yaml
import pycountry
import numpy as np
from app_store_scraper import AppStore
from itunes_app_scraper.scraper import AppStoreScraper

with open("config.yml", "r") as ymlfile:
    try:
        cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
    except yaml.YAMLError as e:
        cfg = None

if cfg:
    try:
        KEY_1 = cfg['openai']['KEY_1']
        KEY_2 = cfg['openai']['KEY_2']
        ENDPOINT = cfg['openai']['ENDPOINT']

    except KeyError as e:
        KEY_1 = None
        KEY_2 = None
        ENDPOINT = None
else:
    KEY_1 = None
    KEY_2 = None
    ENDPOINT = None

openai.api_type = "azure"
openai.api_base = ENDPOINT
openai.api_version = "2023-05-15"
openai.api_key = KEY_1

dx = [
    '200','500', '1000', '2000', '5000', '10000', 'all'
]
ct = [f'{country.name} {country.flag}' for country in list(pycountry.countries)]

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

def extract_appStore_info_from_url(apple_url):
    app_info_pattern = r'/([a-zA-Z0-9\-]+)\/id(\d+)'
    gl_pattern = r"https://apps\.apple\.com/([a-z]{2})/app/.*"

    app_info_match = re.search(app_info_pattern, apple_url)
    gl_match = re.search(gl_pattern, apple_url)

    app_name, app_id = app_info_match.groups() if app_info_match else (None, None)
    gl_value = gl_match.group(1) if gl_match else "us"

    return app_name, app_id, gl_value

def extract_url_parameters(url):
    app_name, app_id, gl = extract_appStore_info_from_url(url)

    if app_id:
        hl = "en"
    else:
        id_pattern = r'id=([^&]+)'
        hl_pattern = r'hl=([^&]+)'
        gl_pattern = r'gl=([^&]+)'

        id_match = re.search(id_pattern, url)
        hl_match = re.search(hl_pattern, url)
        gl_match = re.search(gl_pattern, url)

        app_id = id_match.group(1) if id_match else None
        hl = hl_match.group(1) if hl_match else "en"
        gl = gl_match.group(1) if gl_match else "us"

    return app_name, app_id, hl, gl

@st.cache_data
def info_app_cached(app_name, app_id, hl, gl):
    try:
        if app_name:
            scraper = AppStoreScraper()
            app_details = scraper.get_app_details(app_id, country=gl, lang=hl)
            reviews = app_details['userRatingCountForCurrentVersion']
            installs = "*"
            score = app_details['averageUserRating']

        else:
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
        score, reviews, installs = 0, 0, 0

    return score, reviews, installs

@st.cache_data
def dowload_reviews_cached(app_name, app_id, hl, gl, count):
    try:
        if app_name:
            appStore = AppStore(country=gl, app_name=app_name, app_id=app_id)
            appStore.review(how_many=count)

            df = pd.DataFrame(np.array(appStore.reviews), columns=['review'])
            df = df.join(pd.DataFrame(df.pop('review').tolist()))

            name_mapping = {'date': 'at', 'review': 'content', 'rating': 'score', 'developerResponse': 'replyContent'}
            df = df.rename(columns=name_mapping)

            df['thumbsUpCount'] = pd.Series(dtype="float64")
            df['reviewCreatedVersion'] = pd.Series(dtype="float64")

            df = df[['at', 'userName', 'content', 'replyContent', 'score', 'thumbsUpCount', 'reviewCreatedVersion']]
        else:
            result, continuation_token = reviews(
                app_id,
                lang=hl,
                country=gl,
                sort=Sort.NEWEST,
                count=count,
                filter_score_with=None
            )
            df = pd.DataFrame(result)
            df = df[['at', 'userName', 'content', 'replyContent', 'score', 'thumbsUpCount', 'reviewCreatedVersion']]
    except Exception as e:
        print("An error occurred:", str(e))
        df = pd.DataFrame()
    return df

def generate_card(title, iconname, value):
    lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.12.1/css/all.css" crossorigin="anonymous">'
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
    st.write("Example Google Play App URL: https://play.google.com/store/apps/details?id=com.eco.note&hl=en&gl=US")
    st.write("Example 🍎 Apple App URL: https://apps.apple.com/us/app/slack/id618783545")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        text_input = st.text_input("Enter Google Play App URL or 🍎 Apple App URL 👇")
        app_name, app_id, hl, gl = extract_url_parameters(text_input)
        if not app_id:
            st.warning("Warning: Invalid Google Play App URL or Apple App URL")

    with col2:
        idx = st.selectbox(
            label="Number of reviews",
            options=dx
        )

    with col3:
        gl = st.selectbox(
            label="Country/Region",
            options=ct,
            index=ct.index(gl) if gl in ct else 234
        )

    with col4:
        hl = st.selectbox(
            label="Language",
            options=lg,
            index=lg.index(hl) if hl in lg else 0
        )

    if text_input or gl:
        score, reviews, installs = info_app_cached(app_name, app_id, hl, pycountry.countries.get(flag=gl.split(" ")[-1]).alpha_2)
        if installs:
            col1, col2, col3 = st.columns(3)
            with col1:
                generate_card(f"Average Rating  {gl.split(' ')[-1]}", "fas fa-star", score)

            with col2:
                generate_card("Total Reviews", "fas fa-comments", reviews)

            with col3:
                generate_card("Total Downloads Since Release", "fas fa-download", installs)

    if text_input or hl or idx:
        try:
            if idx == 'all':
                count = 500000
            else:
                count = int(idx)
            reviews_df = dowload_reviews_cached(app_name, app_id, hl, pycountry.countries.get(flag=gl.split(" ")[-1]).alpha_2, count)
        except:
            st.warning("Warning: Invalid Number of reviews")

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

                score_colors = {
                    1: '#ff2b2b',
                    2: '#7defa1',
                    3: '#ffabab',
                    4: '#0068c9',
                    5: '#83c9ff'
                }

                filtered_df['Month'] = filtered_df['at'].dt.to_period('M').astype(str)
                df2 = filtered_df.groupby(['Month', 'score']).size().reset_index(name='Count')

                chart = alt.Chart(df2).mark_bar().encode(
                    x='Month:O',
                    y='Count:Q',
                    color=alt.Color('score:N', scale=alt.Scale(domain=list(score_colors.keys()),
                                                               range=list(score_colors.values())))
                ).properties(
                    width=600,
                    height=400
                ).properties(
                    title='Star Over Time'
                )

                st.altair_chart(chart, use_container_width=True)


            with col2:
                filtered_df = filtered_df[['at', 'userName', 'content', 'replyContent','score', 'thumbsUpCount', 'reviewCreatedVersion','Month']]
                filtered_df = filtered_df.sort_values(by='at', ascending=False)
                filtered_df.reset_index(drop=True, inplace=True)
                st.dataframe(filtered_df, height=730)

                csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Filtered Data as CSV",
                    data=csv_data,
                    file_name="filtered_data.csv",
                    key="filtered_data_csv",
                )

                content_csv_data = filtered_df[['at','content', "thumbsUpCount"]].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download content Column as CSV",
                    data=content_csv_data,
                    file_name="content_column.csv",
                    key="content_column_csv",
                )


            st.subheader("AI Chat Reviews")


            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("What is up?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""

                st.error(f"We are currently awaiting budget approval from our manager Tuong Vu to proceed with further development. Thank you for your patience.")

                # try:
                #     for response in openai.ChatCompletion.create(
                #             engine="EcoTest01",
                #             messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                #             temperature=0.7,
                #             max_tokens=4000,
                #             top_p=0.95,
                #             frequency_penalty=0,
                #             presence_penalty=0,
                #             stop=None,
                #             stream=True,
                #     ):
                #         full_response += response.choices[0].delta.get("content", "")
                #         time.sleep(0.05)
                #         message_placeholder.markdown(full_response + "▌")
                #     message_placeholder.markdown(full_response)
                #     st.session_state.messages.append({"role": "assistant", "content": full_response})
                #
                # except Exception as e:
                #     st.error(f"An error occurred: {str(e)}")



if __name__ == '__main__':
    main()