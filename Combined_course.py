import requests
import json
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
youtube_api_key = os.getenv("YOUTUBE_API_KEY")

print(groq_api_key)
print(youtube_api_key)

# Initialize the language model
llm = ChatGroq(
    model_name="llama-3.1-70b-versatile",
    temperature=0,
    groq_api_key=groq_api_key
)

# Initialize Flask app
app = Flask(__name__)

# Define YouTube API integration function
def get_youtube_link(search_query, api_key):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "key": api_key,
        "maxResults": 1
    }
    response = requests.get(url, params=params)
    result = response.json()
    
    if "items" in result and result["items"]:
        video_id = result["items"][0]["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_url
    else:
        return "No video found for this query."

# Function to add YouTube video links to each chapter
def add_video_links(course_data, api_key):
    for unit in course_data.get("units", []):
        for chapter in unit.get("chapters", []):
            youtube_query = chapter["youtube_search_query"]
            video_link = get_youtube_link(youtube_query, api_key)
            chapter["youtube_video_link"] = video_link
    return course_data

# Define an endpoint to generate course content with YouTube links
@app.route('/generate_course', methods=['POST'])
def generate_course():
    data = request.json
    course_topic = data.get("course_topic", "Stock Market")  # Default to "Stock Market" if not provided

    # Invoke the LLM to generate course data in JSON format
    response = llm.invoke(f"You are an AI capable of curating course content, coming up with relevant chapter titles, and finding relevant youtube videos for each chapter. It is your job to create a course about {course_topic}. The user has requested to create chapters for each of the units. Then, for each chapter, provide a detailed youtube search query that can be used to find an informative educational video for each chapter. Each query should give an educational informative course in YouTube. The response will be strictly in JSON format with no PREAMBLE. You need to provide FIVE tough MCQs with options and correct Answer for each chapter. DO NOT PROVIDE PREAMBLE; THE DATA SHOULD BE STRICTLY JSON")

    # Clean and parse JSON response content
    cleaned_content = response.content.strip("`").strip()  # Removes backticks and surrounding whitespace
    try:
        course_data = json.loads(cleaned_content)  # Parse JSON data
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse JSON response from LLM"}), 500

    # Add YouTube video links to the course data
    updated_course_data = add_video_links(course_data, youtube_api_key)
    
    return jsonify(updated_course_data)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
