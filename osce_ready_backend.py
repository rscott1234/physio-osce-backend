from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os
import random

app = Flask(__name__)

# ✅ Enable CORS for your website
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
        # Enhanced prompt for unique, varied cases
        prompt = f"""Generate a completely unique and realistic physiotherapy case study for {topic}. 

IMPORTANT REQUIREMENTS:
- Always create UNIQUE patient names (avoid common names like Sarah Johnson, John Smith)
- Vary ages from 18-85 years old depending on condition appropriateness
- Use diverse ethnicities, genders, and occupations
- Make each case distinctly different from previous ones
- Include realistic red flags or complications when appropriate

Return ONLY valid JSON in this exact format:

{{
  "patient": {{
    "name": "Unique patient name (first and last)",
    "age": "Age in years and gender (e.g., 34-year-old male)",
    "occupation": "Specific job or lifestyle description",
    "chief_complaint": "Primary presenting problem in patient's words",
    "social_history": "Living situation, family support, activity level, hobbies",
    "goals": "Specific functional goals the patient wants to achieve"
  }},
  "medical": {{
    "history": "Detailed onset, mechanism of injury, progression, previous treatments",
    "symptoms": "Current pain patterns, functional limitations, aggravating/easing factors",
    "examination": "Objective findings, range of motion, strength, special tests, posture",
    "diagnostics": "Imaging results, blood work, other diagnostic tests with specific findings",
    "outcome_measures": "Specific validated assessment tools with baseline scores"
  }},
  "questions": [
    {{
      "question": "What are the key pathophysiological mechanisms underlying this patient's condition?",
      "answer": "Detailed explanation of tissue pathology, pain mechanisms, and physiological processes involved"
    }},
    {{
      "question": "Design an evidence-based treatment plan addressing all impairments identified.",
      "answer": "Comprehensive treatment approach with specific techniques, dosage, and progression rationale"
    }},
    {{
      "question": "How would you address the biopsychosocial factors present in this case?",
      "answer": "Holistic approach considering psychological, social, and lifestyle factors affecting recovery"
    }},
    {{
      "question": "What are the key red flags to monitor and when would you refer this patient?",
      "answer": "Specific warning signs, contraindications, and appropriate referral pathways"
    }},
    {{
      "question": "How would you modify treatment if the patient shows poor initial response?",
      "answer": "Alternative approaches, reassessment strategies, and clinical reasoning for treatment modification"
    }}
  ]
}}

Make this case study realistic, educational, and specific to {topic} physiotherapy. Include relevant anatomy, biomechanics, and evidence-based practice."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert physiotherapy educator creating unique, realistic case studies. Never repeat patient names or demographics. Always create fresh, diverse scenarios."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.8  # Higher temperature for more variety
        )
        
        # Get the AI response
        ai_response = response.choices[0].message.content.strip()
        
        # Clean up the response (remove markdown formatting if present)
        if ai_response.startswith('```json'):
            ai_response = ai_response.replace('```json', '').replace('```', '').strip()
        elif ai_response.startswith('```'):
            ai_response = ai_response.replace('```', '').strip()
        
        # Parse the JSON
        try:
            case_data = json.loads(ai_response)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"AI Response: {ai_response[:500]}...")
            # Return a randomized fallback case
            case_data = get_fallback_case(topic)
        
        # Validate the structure
        if not all(key in case_data for key in ['patient', 'medical', 'questions']):
            print("Invalid case structure, using fallback")
            case_data = get_fallback_case(topic)
        
        # Return the structured JSON directly
        return jsonify(case_data)
        
    except Exception as e:
        print(f"Error generating case: {e}")
        # Return randomized fallback case on any error
        return jsonify(get_fallback_case(topic))

def get_fallback_case(topic):
    """Randomized fallback case when AI fails"""
    
    # Random patient details for variety
    first_names = ["Aisha", "Carlos", "Priya", "Marcus", "Elena", "Kai", "Fatima", "Oliver", "Zara", "Diego", "Amara", "Liam"]
    last_names = ["Chen", "Rodriguez", "Patel", "Johnson", "O'Brien", "Kim", "Hassan", "Williams", "Singh", "Martinez", "Thompson", "Lee"]
    
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    age = random.randint(22, 72)
    gender = random.choice(["male", "female"])
    
    occupations = [
        "Software developer", "Teacher", "Nurse", "Construction worker", "Chef", 
        "Retail manager", "Accountant", "Mechanic", "Student", "Retiree",
        "Graphic designer", "Police officer", "Hairdresser", "Warehouse worker"
    ]
    
    occupation = random.choice(occupations)
    
    return {
        "patient": {
            "name": name,
            "age": f"{age}-year-old {gender}",
            "occupation": occupation,
            "chief_complaint": f"Persistent {topic} pain affecting daily activities and work performance",
            "social_history": f"Lives with family, enjoys recreational activities, works full-time as {occupation.lower()}. Previously active lifestyle.",
            "goals": "Return to pain-free work activities, resume recreational sports, improve sleep quality"
        },
        "medical": {
            "history": f"8-week history of {topic} dysfunction following gradual onset. Initially managed with rest and over-the-counter medication with limited improvement.",
            "symptoms": f"Moderate {topic} pain (5-7/10), morning stiffness lasting 30-60 minutes, pain increases with activity and prolonged positioning",
            "examination": "Reduced range of motion, muscle tension, altered movement patterns, positive provocative tests consistent with condition",
            "diagnostics": "Recent imaging shows mild to moderate degenerative changes appropriate for age. Blood work within normal limits.",
            "outcome_measures": f"Pain Rating Scale: 6/10, Functional Disability Index: 40%, Fear-Avoidance Beliefs elevated"
        },
        "questions": [
            {
                "question": "What are the key pathophysiological mechanisms underlying this patient's condition?",
                "answer": "The condition involves tissue inflammation, altered biomechanics, and potential central sensitization. Chronic pain patterns suggest neuroplastic changes affecting pain processing and motor control."
            },
            {
                "question": "Design an evidence-based treatment plan addressing all impairments identified.",
                "answer": "Multimodal approach including manual therapy for mobility, progressive exercise for strength and endurance, movement re-education, and pain science education. Treatment frequency 2-3x weekly initially."
            },
            {
                "question": "How would you address the biopsychosocial factors present in this case?",
                "answer": "Address fear-avoidance through education and graded exposure, consider work ergonomics, involve family support, and collaborate with other healthcare providers as needed for comprehensive care."
            },
            {
                "question": "What are the key red flags to monitor and when would you refer this patient?",
                "answer": "Monitor for progressive neurological symptoms, severe night pain, systemic symptoms, or lack of improvement after 4-6 weeks of appropriate treatment. Refer for further investigation if present."
            },
            {
                "question": "How would you modify treatment if the patient shows poor initial response?",
                "answer": "Reassess diagnosis, consider additional imaging, modify exercise prescription, increase manual therapy frequency, or refer to specialist for injection therapy or surgical consultation."
            }
        ]
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)