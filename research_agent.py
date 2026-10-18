import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools import web_search, fetch_page
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash"

def run_agent(topic, depth="Quick", on_step=None):
    try:
        steps = []
        total_start = time.time()
        
        # Configure based on depth
        num_queries = 2 if depth == "Quick" else 4
        num_pages = 3 if depth == "Quick" else 6
        
        # (a) One Gemini call that returns web search queries for the topic as a JSON list of strings
        step_a_start = time.time()
        print(f"Step (a): Generating {num_queries} search queries...")
        query_prompt = f"Generate {num_queries} short web search queries for researching the topic: {topic}. Return as a JSON list of strings."
        query_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=query_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        # Parse the JSON response
        try:
            queries = json.loads(query_response.text)
            if not isinstance(queries, list):
                queries = []
            queries = [str(q) for q in queries[:num_queries] if q]
        except (json.JSONDecodeError, TypeError):
            queries = []
        
        if not queries:
            queries = [topic]
        
        # Call on_step for each query and add to steps
        for q in queries:
            step_msg = f"Searched: {q}"
            steps.append(step_msg)
            if on_step:
                on_step(step_msg)
        
        step_a_elapsed = time.time() - step_a_start
        print(f"Step (a) took {step_a_elapsed:.2f} seconds")
        
        # (b) Run web_search for each query from tools.py in parallel. Collect unique URLs and keep the top 4.
        step_b_start = time.time()
        print("Step (b): Collecting URLs from search results...")
        seen_urls = set()
        url_list = []  # To preserve order
        
        with ThreadPoolExecutor(max_workers=len(queries)) as executor:
            future_to_query = {executor.submit(web_search, q): q for q in queries}
            for future in as_completed(future_to_query):
                q = future_to_query[future]
                try:
                    results = future.result()
                    for r in results:
                        url = r.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            url_list.append(url)
                except Exception as e:
                    print(f"Error during web search for query '{q}': {e}")
                    continue
        
        # Take the top specified number of unique URLs
        top_urls = url_list[:num_pages]
        
        step_b_elapsed = time.time() - step_b_start
        print(f"Step (b) took {step_b_elapsed:.2f} seconds")
        
        # (c) Run fetch_page on those URLs in parallel with ThreadPoolExecutor
        step_c_start = time.time()
        print("Step (c): Fetching pages in parallel...")
        fetched_texts = []  # List of (url, text) for successful fetches
        with ThreadPoolExecutor(max_workers=min(num_pages, 6)) as executor:
            future_to_url = {executor.submit(fetch_page, url): url for url in top_urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    text = future.result()
                except Exception as e:
                    text = f"Error: {e}"
                
                # Call on_step for each URL and add to steps
                step_msg = f"Read: {url}"
                steps.append(step_msg)
                if on_step:
                    on_step(step_msg)
                
                # If successful, keep the text
                if not text.startswith("Error:"):
                    fetched_texts.append((url, text))
        
        step_c_elapsed = time.time() - step_c_start
        print(f"Step (c) took {step_c_elapsed:.2f} seconds")
        
        # Combine the fetched text for the final prompt, labeling each page with its URL
        used_urls = [url for url, _ in fetched_texts]
        if used_urls:
            labeled_pages = []
            for url, text in fetched_texts:
                labeled_pages.append(f"URL: {url}\n{text}")
            combined_text = "\n\n---\n\n".join(labeled_pages)
        else:
            combined_text = ""
        
        # (d) One final Gemini call with the topic and the fetched text, asking for a short bullet-point report
        step_d_start = time.time()
        print("Step (d): Generating final report...")
        if not combined_text:
            final_prompt = f"Research the topic: {topic}\n\nNo information could be gathered from the web. Write a short note stating that no information was found."
        else:
            final_prompt = f"""Research the topic: {topic}

Here is the information gathered from the web:

{combined_text}

Write a short bullet-point report using only the page texts provided. Do NOT write a Sources section."""
        
        final_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=final_prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        final_answer = final_response.text
        
        # Append the Sources section built in Python from the URLs actually fetched successfully
        if used_urls:
            sources_section = "\n\n## Sources\n" + "\n".join([f"- {url}" for url in used_urls])
            final_answer = final_answer + sources_section
        
        step_d_elapsed = time.time() - step_d_start
        print(f"Step (d) took {step_d_elapsed:.2f} seconds")
        
        total_elapsed = time.time() - total_start
        print(f"Total execution took {total_elapsed:.2f} seconds")
        
        return final_answer, steps
        
    except Exception:
        traceback.print_exc()
        raise
