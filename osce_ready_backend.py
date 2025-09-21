from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os

app = Flask(__name__)

# ✅ Enable CORS for your website + localhost
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://www.rebeccathetutor.co.uk",
            "https://rebeccathetutor.co.uk",
            "http://localhost:5500",
            "http://127.0.0.1:5500"
        ]
    }
})

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "OSCE backend is running"})

@app.route('/generate-case')
def generate_case():
    topic = request.args.get('topic', 'general')
    
    try:
        # Prompt
        prompt = f"""Generate a detailed physiotherapy case study for {topic}. 
Return ONLY valid JSON in this exact format:

{{
  "patient": {{
    "name": "Patient Name",
    "age": "Age and gender",
    "occupation": "Job/lifestyle",
    "chief_complaint": "Main presenting problem",
    "social_history": "Living situation, support, activity level",
    "goals": "Patient's functional goals"
  }},
  "medical": {{
    "history": "Detailed medical history and onset",
    "symptoms": "Current symptoms and pain patterns",
    "examination": "Physical examination findings",
    "diagnostics": "Imaging, tests, and results",
    "outcome_measures": "Relevant assessment tools and scores"
  }},
  "questions": [
    {{
      "question": "Clinical reasoning question",
      "answer": "Detailed evidence-based answer"
    }},
    {{
      "question": "Treatment planning question",
      "answer": "Plan and rationale"
    }},
    {{
      "question": "Biopsychosocial consideration",
      "answer": "Holistic answer"
    }}
  ]
}}"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert physiotherapy educator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Clean up formatting
        if ai_response.startswith("```json"):
            ai_response = ai_response.replace("```json", "").replace("```", "").strip()
        elif ai_response.startswith("```"):
            ai_response = ai_response.replace("```", "").strip()
        
        # Parse JSON
        try:
            case_data = json.loads(ai_response)
        except json.JSONDecodeError:
            print("⚠️ JSON decode failed, using fallback.")
            return jsonify(get_fallback_case(topic))

        # Validate structure
        if not all(k in case_data for k in ["patient", "medical", "questions"]):
            print("⚠️ Missing keys, using fallback.")
            return jsonify(get_fallback_case(topic))
        
        return jsonify(case_data)

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return jsonify(get_fallback_case(topic))

def get_fallback_case(topic):
    return {
        "patient": {
            "name": "Sarah Johnson",
            "age": "45-year-old female",
            "occupation": "Office manager",
            "chief_complaint": f"Chronic {topic} pain affecting daily activities",
            "social_history": "Lives with spouse, two teenage children. Previously active in running and yoga.",
            "goals": "Return to running 5km, reduce pain during work hours, improve sleep quality"
        },
        "medical": {
            "history": f"6-month history of {topic} dysfunction following workplace injury.",
            "symptoms": "Constant aching pain (6/10), morning stiffness, worsens with sitting",
            "examination": "Reduced ROM, muscle guarding, positive provocative tests",
            "diagnostics": "MRI shows mild degenerative changes",
            "outcome_measures": "NPRS: 6/10, ODI: 34%, Fear-Avoidance elevated"
        },
        "questions": [
            {
                "question": "What are the key mechanisms contributing to chronic pain?",
                "answer": "Central sensitization, inflammatory processes, and altered pain perception."
            },
            {
                "question": "Design a treatment plan addressing biopsychosocial factors.",
                "answer": "Multimodal therapy: exercise, education, manual therapy, psychological support."
            },
            {
                "question": "How would you address fear-avoidance beliefs?",
                "answer": "Gradual exposure therapy, pain science education, and graded activity."
            }
        ]
    }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)