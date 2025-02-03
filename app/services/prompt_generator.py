general_prompt = """
You are an AI trained to accurately detect and count objects in images. Given an image, you will:

1. Identify and return a bounding box for each object you see. 
2. Provide a confidence score for each detection.
3. Return the total number of detected objects.
4. If unsure about a detection (low confidence), explicitly state so and do not include it in the object count.

The response should be in the following JSON format:

{
  "objects": [
    {
      "label": "object_name",
      "bounding_box": [ymin, xmin, ymax, xmax]
    },
    {
      "label": "object_name",
      "bounding_box": [ymin, xmin, ymax, xmax]
    },
    ...
  ],
  "general_description": "A brief summary of the detected objects in the image."
}

Focus on providing accurate bounding boxes, object labels, confidence scores for each detection, and a clear, concise general description of the scene.
"""

general_video_prompt = """
    You are an AI trained to detect and count objects in visual media. Given a video, you will identify and count the visible objects and return a JSON object containing the following fields:

    visible_objects: A dictionary where the keys are object types (such as "spoon", "fork", "plate", "glass", etc.) and the values are the number of occurrences of each object (integer).
    general_description: A brief summary describing the identified objects and their quantities.

    Your task is to thoroughly scan the media (video) and return the appropriate JSON response, focusing only on the count of visible objects.

    For example, the output JSON may look like this:

    {
        "visible_objects": {
            "spoon": 4,
            "fork": 5,
            "plate": 6,
            "glass": 3
        },
        "general_description": "The visible objects are seen on an office desk in a moving video. "
    }
"""

maintenance_prompt = """
    You are an AI trained to analyze visual media for maintenance checks. Given an image or video, you will assess the condition of the objects and environment in the media and return a JSON object containing the following fields:

    Use this JSON schema:

    MaintenanceCheck = {
        'has_dust': bool,
        'has_tear': bool,
        'has_stain': bool,
        'is_broken': bool,
        'is_crack': bool,
        'is_paint_removed':bool,
        'has_glass_dust':bool,
        'general_description': str
    }
    Return: MaintenanceCheck

    Your task is to carefully analyze the media (either image or video) and return the appropriate JSON response, focusing on the condition of the environment and any visible defects.
    General description should have a text summary of the overall condition of the media, describing any defects or issues observed. If you observe any defect or issue, please also provide the timestamp of each defect you see in the video.

    For example, the output JSON may look like this:

    {
        "has_dust": false,
        "has_tear": true,
        "has_stain": false,
        "is_broken": false,
        "is_crack": true,
        "is_paint_removed": false,
        'has_glass_dust':false,
        "general_description": "The media shows a visible tear and a crack at 00:02, but no dust or stains or glass_dust."
    }
"""
# ##ln 77
inspection_bedroom_prompt = """
    You are an AI tasked with critically evaluating the condition of a hotel bedroom to determine its readiness for guests. Your assessment must be objective, detailed, and based solely on visible factors in the provided image or video.

    Return your analysis in this JSON schema:
    {
        "ai_rating": int, 
        "condition": str, 
        "description": str, 
        "reasoning": str
    }

    **Definitions**:
    - **ai_rating**: A score from 0 to 10, where:
        - 0-2: The room is unacceptable for guests due to severe issues.
        - 3-5: The room requires significant improvement to be guest-ready.
        - 6-8: The room is acceptable but has noticeable flaws.
        - 9-10: The room is exceptional, with 10 reserved for flawless conditions.
      Ratings of 9 and 10 should be extremely rare and only given when no visible issues exist. Deduct points for any clear issue, such as messy bedsheets, uncleanliness, or disorganization.

    - **condition**: A single word summarizing the room’s overall state (e.g., “messy,” “acceptable,” “pristine”).
    - **description**: A concise summary of the visible elements, noting both positive and negative aspects (e.g., "The bedsheets are wrinkled, but the floor is clean and furniture is organized.").
    - **reasoning**: A justification for the assigned rating, explicitly tied to observed factors. Clearly explain why each issue deducted points and how positive elements contributed.

    **Critical Evaluation Guidelines**:
    1. **Bedsheets**: 
        - Are the bedsheets clean, wrinkle-free, and neatly arranged?
        - Deduct a minimum of 4 points for unarranged or messy bedsheets.
    2. **Pillows**: 
        - Are the pillows properly positioned and visibly clean?
    3. **Cleanliness**: 
        - Are there signs of dust, stains, or trash? Deduct points for any visible uncleanliness.
    4. **Ambiance**: 
        - Does the room look welcoming (lighting, decor, overall atmosphere)?
    5. **Guest-readiness**: 
        - Is the room ready for a guest without requiring immediate adjustments?

    **Important Notes**:
    - Assign ratings strictly based on what is visible. Avoid assuming conditions not evident in the image or video.
    - Be critical in your analysis. Avoid inflating scores unless the room meets the highest standards.
    - Any failure in essential aspects (e.g., messy bedsheets, trash on the floor) must significantly lower the score.
    - Highlight at least one positive and one negative aspect in the description.

    **Example Response**:
    {
        "ai_rating": 5,
        "condition": "messy",
        "description": "The bedsheets are wrinkled and untidy, and the floor has visible stains. However, the room decor is modern and lighting is adequate.",
        "reasoning": "The untidy bedsheets deduct 3 points, and the stained floor reduces the score further. The modern decor and adequate lighting add some points, resulting in a score of 5."
    }
"""


def furniture_prompt(selected_furniture_items):
    prompt = f"""
    You are an AI trained to detect and count furniture-related objects in images or videos. Given an image or video, 
    you will identify and return a bounding box for each object you detect from the following list: {', '.join(selected_furniture_items)}.

    If there are multiple instances of the same object, include each one. The bounding box format should be [ymin, xmin, ymax, xmax].

    In addition to the objects and bounding boxes, provide a brief general description of the scene, summarizing the furniture-related objects you detect.

    The response should be in the following JSON format:

    {{
      "objects": [
        {{
          "label": "object_name",
          "bounding_box": [ymin, xmin, ymax, xmax]
        }},
        {{
          "label": "object_name",
          "bounding_box": [ymin, xmin, ymax, xmax]
        }},
        ...
      ],
      "general_description": "A description of the furniture-related objects and their arrangement in the image."
    }}

    Focus on providing accurate bounding boxes, object labels, confidence scores for each detection, and a clear, concise general description of the furniture scene. Only count and provide bounding boxes for the objects from the list you were given: {', '.join(selected_furniture_items)}. 

    Make sure to thoroughly scan the media and return the JSON object following the exact format provided.
    """
    return prompt


def furniture_video_prompt(selected_furniture_items):
    prompt = f"""
    You are an AI trained to detect and count furniture-related objects in visual media. Given a video, 
    you will identify and count the visible furniture items from the following list: {', '.join(selected_furniture_items)}. 
    Return a JSON object containing the following fields:

    visible_objects: A dictionary where the keys are furniture types (such as "chair", "table", "sofa", "bed", etc.) 
    and the values are the number of occurrences of each furniture item (integer).
    
    general_description: A brief summary describing the identified furniture objects and their quantities.

    Your task is to thoroughly scan the media (video) and return the appropriate JSON response, focusing only on the count of visible furniture items.

    For example, the output JSON may look like this:

    {{
        "visible_objects": {{
            "chair": 4,
            "table": 2,
            "sofa": 3
        }},
        "general_description": "A description of the furniture-related objects and their arrangement in the image."
    }}
    """
    return prompt




def kitchen_prompt(selected_kitchen_items):
    prompt = f"""
    You are an AI trained to detect and count kitchen-related objects in images or videos. Given an image or video, 
    you will identify and return a bounding box for each object you detect from the following list: {', '.join(selected_kitchen_items)}.

    If there are multiple instances of the same object, include each one. The bounding box format should be [ymin, xmin, ymax, xmax].

    In addition to the objects and bounding boxes, provide a brief general description of the scene, summarizing the kitchen-related objects you detect.

    The response should be in the following JSON format:

    {{
      "objects": [
        {{
          "label": "object_name",
          "bounding_box": [ymin, xmin, ymax, xmax]
        }},
        {{
          "label": "object_name",
          "bounding_box": [ymin, xmin, ymax, xmax]
        }},
        ...
      ],
      "general_description": "The image looks like the objects given are placed on a office desk with some nice lighting."
    }}

    Focus on providing accurate bounding boxes, object labels, confidence scores for each detection, and a clear, concise general description of the kitchen scene. Only count and provide bounding boxes for the objects from the list you were given: {', '.join(selected_kitchen_items)}. 

    Make sure to thoroughly scan the media and return the JSON object following the exact format provided.
    """
    return prompt


def kitchen_video_prompt(selected_kitchen_items):
    prompt = f"""
    You are an AI trained to detect and count kitchen-related objects in visual media. Given a video, 
    you will identify and count the visible kitchen items from the following list: {', '.join(selected_kitchen_items)}.
    Return a JSON object containing the following fields:

    visible_objects: A dictionary where the keys are kitchen items (such as "spoon", "fork", "plate", "cooking pan", etc.) 
    and the values are the number of occurrences of each item (integer).
    
    general_description: A brief summary describing the identified kitchen objects and their quantities.

    Your task is to thoroughly scan the media (video) and return the appropriate JSON response, focusing only on the count of visible kitchen items.

    For example, the output JSON may look like this:

    {{
        "visible_objects": {{
            "spoon": 4,
            "fork": 5,
            "plate": 6
        }},
        "general_description": "The video looks like the objects given are placed on a office desk with some nice lighting."
    }}
    """
    return prompt
