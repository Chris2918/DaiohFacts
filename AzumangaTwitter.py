import wikipedia
import nltk
import requests
from bs4 import BeautifulSoup
import random
import tweepy
import os
import openai

# Authenticate with OpenAI API
openai.api_key = "OPENAI_API_KEY_HERE"

# Authenticate with tweepy
consumer_key = "CONSUMER_KEY_HERE"
consumer_secret = "CONSUMER_SECRET_HERE"
access_token = "ACCESS_TOKEN_HERE"
access_token_secret = "ACCESS_TOKEN_SECRET_HERE"

client = tweepy.Client(
    consumer_key=consumer_key, consumer_secret=consumer_secret,
    access_token=access_token, access_token_secret=access_token_secret
)

# Get information about Azumanga Daioh
nltk.download('punkt')

# First, we get information about the characters of Azumanga Daioh
# Create a WikipediaPage instance
page = wikipedia.WikipediaPage(title='List of Azumanga Daioh characters')

# Retrieve the content of the page
page_content = page.content

# Find the starting index of the "Major characters" section
start_index = page_content.find('== Major characters ==')

# Find the ending index of the "Major characters" section
end_index = page_content.find('== Minor characters ==')

# Extract the "Major characters" section content
major_characters_section = page_content[start_index:end_index]

# Tokenize the section into subsections using nlkt
subsections = major_characters_section.split('===')

# Initialize a list to store the limited sentences for each subsection
limited_sentences = []

# Limit each subsection to 8 sentences and store them in the list
for subsection in subsections:
    sentences = nltk.sent_tokenize(subsection.strip())
    limited_sentences.extend(sentences[:8])

# Join the limited sentences into a single string
azumanga_characters = '\n'.join(limited_sentences)

# Now, we get information about the episodes of Azumanga Daioh

# Download the NLTK corpora if not already downloaded
nltk.download('punkt')

# URL of the Azumanga Daioh Wikipedia page
epurl = 'https://en.wikipedia.org/wiki/List_of_Azumanga_Daioh_episodes'

# Send a GET request to the URL
response = requests.get(epurl)

# Check if the request was successful
if response.status_code == 200:
    # Create a BeautifulSoup object with the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the table containing the episode details
    table = soup.find('table', class_='wikitable')

    # Find all rows in the table
    rows = table.find_all('tr')

    # Create a file to write the episode details
    with open('episode_details.txt', 'w', encoding='utf-8') as file:
        # Initialize the episode counter
        episode_number = 1

        # Iterate over the rows, skipping the header row
        for row in rows[1:]:
            # Get the cells in the row
            cells = row.find_all('td')

            # Check if the row has the expected number of cells
            if len(cells) >= 2:
                # Extract the episode titles and find the first English name
                episode_titles = cells[1].find_all(text=True)
                episode_title_english = next((title for title in episode_titles if title.strip().isalpha()), '')

                # Remove additional names and extra information
                episode_title_english = episode_title_english.split('/')[0].strip()

                # Find the description cell containing the episode synopsis
                description_cell = row.find_next_sibling('tr').find('td', class_='description')

                if description_cell:
                    # Extract the episode synopsis
                    episode_synopsis = description_cell.text.strip()

                    # Tokenize the synopsis into sentences
                    sentences = nltk.sent_tokenize(episode_synopsis)

                    # Limit the synopsis to 2 sentences
                    synopsis = ' '.join(sentences[:2])

                    # Write the episode details to the file
                    file.write(f"Episode {episode_number}: {episode_title_english}\n")
                    file.write(f"Synopsis: {synopsis}\n")
                    file.write('\n')

                    # Increment the episode counter
                    episode_number += 1
            else:
                print("Skipping row with unexpected cell count")

    print("Episode details have been written to 'episode_details.txt' file.")
else:
    print("Failed to retrieve episode details from the Wikipedia page")

# Set the filename
filename = 'episode_details.txt'

# Open the file in read mode and read its contents
with open(filename, 'r', encoding='utf-8') as file:
    episode_plots = file.read()

# Print the file contents
print(episode_plots)

# List prompts and randomly select one to use for the OpenAI API
character_prompt = f"This is important, always write under 80 words. Write a fact about the characters of Azumanga Daioh using information from the contents of this page: {azumanga_characters}. Write under 50 words."

episode_prompt = f"This is important, always write under 80 words. Write a fact about the episodes of Azumanga Daioh using information from the contents of this page: {episode_plots}. Write under 50 words."

random_prompt = random.choice([character_prompt, episode_prompt])

# Use OpenAI API to generate a tweet using the page content and a prompt
completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    temperature=0.4,
    messages=[
        {"role": "system", "content": 'Write short, Twitter-style facts using given info. Start each sentence with "Did you know that?" Keep it under 50 words. Dont say that Azumanga Daioh aired with 26 episodes or it released in this year. Tell me more. Give examples of facts about episodes and characters.'},
        {"role": "user", "content": random_prompt}
    ]
)

message_content = completion['choices'][0]['message']['content']

if len(message_content.split()) > 50:
    # Use OpenAI API to summarize the long response
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.6,
        messages=[
            {"role": "system", "content": 'You are designed to summarize text in under 50 words. Always start with "Did you know that?".'},
                   {"role": "user", "content": f"Summarize this text in under 50 words: {message_content}."}
        ]
    )

    message_content = completion['choices'][0]['message']['content']
    
    # Truncate message_content to fit within Twitter's character limit
    truncated_content = message_content[:280]
    
    print(f"Selected prompt: {random_prompt}")
    
    print("OpenAI API delivered response. Response is:")
    
    print(truncated_content)

    print("Posted to Twitter! Here's the link:")
    response = client.create_tweet(text=truncated_content)
    print(f"https://twitter.com/user/status/{response.data['id']}")

