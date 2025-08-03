from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
import google.generativeai as genai 
genai.configure(api_key='AIzaSyCQOLyBvQLEO2grPQbVhTCMMyfA0UF6DOY')
text_model = genai.GenerativeModel("gemini-2.0-flash-001")
from .models import GeneratedVideo
import requests
from django.contrib import messages
from django.shortcuts import redirect

def index(request):
    return render(request, "index.html")

def video(request):
    if request.method == "POST":
        topic = request.POST.get("topic")
        if not topic:
            messages.error(request, "Please enter a topic")
            return redirect('index')

        similar_id = check_topic_with_gemini(topic)

        if similar_id != "No":
            try:
                existing_video = GeneratedVideo.objects.get(id=similar_id)
                return render(request, "videopage.html", {'data': existing_video})
            except GeneratedVideo.DoesNotExist:
                messages.error(request, "Error: Video data not found in the database.")
                return redirect('index')
        else:
            # If Gemini returns "No", generate new data using the API
            data = apitest(topic)
            if data:
                return render(request, "videopage.html", {'data': data})
            else:
                messages.error(request, "Video generation failed. Please try again.")
                return redirect('index')

    return render(request, "videopage.html")

def check_topic_with_gemini(topic):

    try:
        # Fetch all topics from the database
        all_topics = list(GeneratedVideo.objects.values('id', 'subject', 'topic'))
        # Prepare the dictionary of existing topics
        existing_topics = {str(item['id']): {'subject': item['subject'], 'topic': item['topic']} for item in all_topics}
        # Formulate the prompt for Gemini
        prompt = f"""
        Check if the given topic '{topic}' is similar to any of the following topics:
        {existing_topics}.
        If a match is found, return the ID of the similar topic. Otherwise, return "No".
        
        Dont's :
        Do not return statements like: ///The provided topic 'polynomials' is very similar to the topic 'Polynomial' in the given dictionary. Therefore, the answer is:1///
        
        Do's :
        Just Provide the ID of the similar topic eg. ///1/// or ///2/// or ///56///
        """
        
        response = text_model.generate_content(prompt)
        result = response.text.strip()
        
        if result.isdigit():
            return int(result)
        return "No"

    except Exception as e:
        print(f"Gemini API error: {e}")
        return "No"

def apitest(topic):
    api_url = f"https://8080-idx-aivideogen-1743066534050.cluster-a3grjzek65cxex762e4mwrzl46.cloudworkstations.dev/search/?topic={topic}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        # Basic validation of expected keys
        required_keys = ["subject", "topic", "description", "thumbnail", "videoPath"]
        if not all(key in data for key in required_keys):
             print(f"Error: API response missing required keys. Data: {data}")
             return redirect('index')

        video_obj, created = GeneratedVideo.objects.create(
            topic=data['topic'],
            defaults={
                'subject': data['subject'],
                'description': data['description'],
                'thumbnail': data['thumbnail'],
                'videoPath': data['videoPath'],
            }
        )
        return data

    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, bad responses
        print(f"Error fetching data from API: {e}")
        # Redirect to an error page or back to index
        return redirect('index') # Placeholder redirect
    except Exception as e:
        # Handle other potential errors (e.g., JSON decoding, DB saving)
        print(f"An error occurred: {e}")
        return redirect('index')

def instructions(request):
    return render(request, "instructions.html")

def resources(request):
    return render(request, "resources.html")

def contact(request):
    return render(request, "contact.html")

def suggestions(request):
    return render(request, "suggestions.html")

def previous_searches_data(request):
    try:
        last_searches = GeneratedVideo.objects.values('topic', 'description', 'thumbnail').distinct().order_by('-id')[:6]

        # Prepare the data in the required format
        formatted_data = {
            "topics": [
                {
                    "title": item['topic'],
                    "description": item['description'],
                    "imageUrl": item['thumbnail']
                }
                for item in last_searches
            ]
        }
        print(formatted_data)

        if not formatted_data['topics']:
            return JsonResponse([], safe=False)
        else:
             return JsonResponse(formatted_data, safe=False)


    except Exception as e:
        print(f"Error fetching previous searches: {e}")
        return JsonResponse([], safe=False)

def search_suggestions_data(request):
    """
    Endpoint to return all unique search topics as JSON.
    """
    try:
        all_search_topics = GeneratedVideo.objects.values_list('topic', flat=True).distinct()
        return JsonResponse(list(all_search_topics), safe=False)
    except Exception as e:
        print(f"Error fetching search suggestions: {e}")
        return JsonResponse([], safe=False)

