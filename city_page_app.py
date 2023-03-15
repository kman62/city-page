import streamlit as st
import wikipedia
import openai
import re
import requests

from bs4 import BeautifulSoup

# Load API key
openai.api_key = st.secrets["openai"]["api_key"]

# Get the list of cities with more than 25,000 people
def get_cities():
    url = "https://en.wikipedia.org/wiki/List_of_cities_in_the_United_States_by_population"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    cities = []

    for row in soup.select("table.wikitable > tbody > tr"):
        population_cell = row.select_one("td:nth-child(4)")
        if population_cell:
            population = int(re.sub("[^0-9]", "", population_cell.text))
            if population > 25000:
                city = row.select_one("td:nth-child(2)").text.strip()
                cities.append(city)

    return cities

# Generate engaging and unique content using OpenAI GPT-3.5
def generate_content(text):
    response = openai.Completion.create(
        engine="davinci-codex-002",
        prompt=f"Rewrite the following text in an engaging and unique way using active voice, including internal links and proper H1, H2, and H3 headers in markdown format. The text should appear as if written by a copywriter with 10 years of experience in SEO:\n\n{text}",
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].text.strip()

# Main Streamlit application
def main():
    st.title("City Page Creator")

    cities = get_cities()
    selected_city = st.selectbox("Select a city:", cities)

    if st.button("Generate City Page"):
        try:
            city_summary = wikipedia.summary(selected_city)
            city_page = generate_content(city_summary)
            st.markdown(city_page)
        except Exception as e:
            st.error(f"Error generating city page: {e}")

if __name__ == "__main__":
    main()
