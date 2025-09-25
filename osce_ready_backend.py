from flask import Flask, request, jsonify, redirect, session, render_template, url_for
from flask_cors import CORS
from openai import OpenAI
import json
import os
import random
import requests   # 👈 ADD THIS LINE

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")

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

# Patreon OAuth config
CLIENT_ID = os.environ.get("PATREON_CLIENT_ID")
CLIENT_SECRET = os.environ.get("PATREON_CLIENT_SECRET")
REDIRECT_URI = "https://physio-osce-backend.onrender.com/callback"

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "OSCE backend is running"})

@app.route('/generate-case')
def generate_case():
    topic = request.args.get('topic', 'general')
    
    try:
        # Enhanced prompt with 3 core + 3 random questions
        prompt = f"""Generate a completely unique and realistic physiotherapy case study for {topic}. 

--- FORMAT ---
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
      "question": "What are the key pathophysiological mechanisms underlying this patient's presentation? Explain all medical terms clearly.",
      "answer": "Detailed explanation of tissue pathology, pain mechanisms, and physiological processes with definitions"
    }},
    {{
      "question": "What red flags or concerning symptoms would prompt urgent referral in this case, and why?",
      "answer": "Specific warning signs, what each indicates, and appropriate referral pathways with reasoning"
    }},
    {{
      "question": "What is this patient's problem list, and how would you structure a comprehensive management plan?",
      "answer": "Prioritized problem list with detailed, evidence-based treatment approach and rationale"
    }},
    {{
      "question": "[SELECT ONE: What additional information from the history would be important, and why? / Which other healthcare professionals would you involve in the management plan, and what role would they play? / Which outcome measures would you use to monitor progress, and why are they appropriate? / How would the patient's social context affect your management plan? / What key examination findings help to differentiate between possible diagnoses? / What advice or education would you give this patient regarding their condition? / How would you adapt your approach if this patient were elderly/young adult/athlete? / If the patient reports worsening symptoms, how would you modify your clinical reasoning?]",
      "answer": "Comprehensive teaching-style answer with detailed reasoning and explanations"
    }},
    {{
      "question": "[SELECT DIFFERENT ONE FROM ABOVE POOL]",
      "answer": "Detailed multi-sentence explanation with clinical reasoning"
    }},
    {{
      "question": "[SELECT DIFFERENT ONE FROM ABOVE POOL]",
      "answer": "Teaching-style answer with pathophysiology and practical application"
    }}
  ]
}}

--- REQUIREMENTS ---
1. **Unique Patient Generation:**
   - Always create DISTINCT patient names, ages (18-85), occupations, and backgrounds
   - Vary ethnicities, genders, social situations, and medical histories
   - Make each case completely different from previous ones

2. **Clinical Detail Requirements:**
   - Include realistic pathophysiology specific to {topic}
   - Provide specific examination findings and diagnostic results
   - Include relevant red flags and safety considerations
   - Use appropriate medical terminology with explanations

3. **Question Requirements:**
   - Questions 1-3 are ALWAYS the core pathophysiology, red flags, and management questions as specified
   - Questions 4-6 should be randomly selected from the pool provided, ensuring variety
   - Each answer MUST be 4-6+ sentences minimum
   - Always explain technical terms (e.g., define "radiculopathy", "central sensitization", "nociception")
   - Use a teaching tone - "explaining to a physiotherapy student"
   - Include evidence-based reasoning and clinical decision-making
   - Always explain any medical terminology
   - Use a teaching tone aimed at physiotherapy students
   - ✅ Write in the 3rd person (formal academic style)
   - ✅ Never use "I" or first-person; instead use clinical/teaching phrasing
   - Use English (UK) spelling and terminology throughout (e.g. "organise", "orthopaedic", "oedema", "paediatrics")

4. **Educational Value:**
   - Make answers comprehensive enough for revision notes
   - Include practical application and clinical reasoning
   - Connect theory to practice throughout
   - Ensure answers build understanding, not just test knowledge
   - Ensure answers are comprehensive revision notes
   - Bridge theory and clinical reasoning

Make this case study realistic, educational, and specific to {topic} physiotherapy practice."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert physiotherapy educator creating unique, realistic case studies with detailed teaching-style answers. Always vary patient demographics and select different questions from the optional pool to ensure variety. Never repeat patient names or case details."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,  # Increased for longer answers
            temperature=0.8   # Higher temperature for more variety
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
        
        # Ensure we have exactly 6 questions
        if len(case_data.get('questions', [])) != 6:
            print("Incorrect number of questions, using fallback")
            case_data = get_fallback_case(topic)
        
        # Return the structured JSON directly
        return jsonify(case_data)
        
    except Exception as e:
        print(f"Error generating case: {e}")
        # Return randomized fallback case on any error
        return jsonify(get_fallback_case(topic))

def get_fallback_case(topic):
    """Randomized fallback case when AI fails - now with 6 questions including 3 core + 3 random"""
    
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
    
    # Pool of optional questions for fallback
    optional_questions = [
        {
            "question": "What additional information from the patient's history would be valuable for treatment planning?",
            "answer": "Additional history should include previous episodes, family history of similar conditions, current medications, sleep patterns, and specific functional limitations. Understanding the patient's work ergonomics, exercise history, and previous treatment responses would guide more targeted interventions and help identify contributing factors."
        },
        {
            "question": "Which healthcare professionals should be involved in this patient's care team?",
            "answer": "A multidisciplinary approach may include a GP for medical management, occupational therapist for workplace modifications, psychologist for pain coping strategies if chronic pain develops, and potentially a specialist consultant if conservative management fails. Each professional brings specific expertise to address different aspects of the biopsychosocial model."
        },
        {
            "question": "What outcome measures would be most appropriate to track this patient's progress?",
            "answer": "Validated outcome measures should include pain scales (NPRS), functional disability questionnaires specific to the condition, quality of life measures, and objective measures like range of motion or strength testing. These provide quantifiable data to demonstrate progress and guide treatment modifications."
        },
        {
            "question": "How does this patient's social and occupational context influence treatment planning?",
            "answer": "The patient's work demands, family responsibilities, and social support network significantly impact recovery. Treatment timing, exercise prescription, and return-to-work planning must consider these factors. Social determinants of health, including access to healthcare and economic pressures, may affect adherence and outcomes."
        },
        {
            "question": "What key physical examination findings would support your clinical hypothesis?",
            "answer": "Specific examination findings should correlate with the suspected pathology, including range of motion limitations, strength deficits, provocative test results, and movement quality assessment. Negative findings are equally important to rule out serious pathology and guide differential diagnosis."
        },
        {
            "question": "What patient education and self-management strategies would you prioritize?",
            "answer": "Education should focus on pain science, activity modification, ergonomic principles, and self-management techniques. Teaching patients about their condition, expected recovery timeline, and warning signs empowers them to take an active role in their recovery and prevents chronicity."
        }
    ]
    
    # Select 3 random optional questions
    selected_optional = random.sample(optional_questions, 3)
    
    # Core questions (always included)
    core_questions = [
        {
            "question": "What are the key pathophysiological mechanisms underlying this patient's presentation?",
            "answer": f"The {topic} condition involves tissue inflammation, altered biomechanics, and potential sensitization of nociceptors (pain receptors). Inflammatory mediators increase tissue sensitivity, while altered movement patterns can perpetuate dysfunction. Central sensitization may develop if symptoms persist, where the nervous system becomes hypersensitive to stimuli."
        },
        {
            "question": "What red flags or concerning symptoms would prompt urgent referral in this case?",
            "answer": "Red flags include progressive neurological symptoms (weakness, numbness), severe night pain, systemic symptoms (fever, weight loss), or signs of serious pathology. These may indicate conditions requiring immediate medical attention such as fractures, infections, or neurological compromise requiring urgent specialist review."
        },
        {
            "question": "What is this patient's problem list, and how would you structure a comprehensive management plan?",
            "answer": f"Primary problems include {topic} pain, functional limitations, and potential psychosocial factors. Management should address pain through manual therapy and modalities, restore function through progressive exercise, and prevent recurrence through education and lifestyle modification. Treatment should be evidence-based and patient-centered."
        }
    ]
    
    # Combine core + selected optional questions
    all_questions = core_questions + selected_optional
    
    return {
        "patient": {
            "name": name,
            "age": f"{age}-year-old {gender}",
            "occupation": occupation,
            "chief_complaint": f"Persistent {topic} pain affecting daily activities and work performance",
            "social_history": f"Lives with family, enjoys recreational activities, works full-time as {occupation.lower()}. Previously active lifestyle with good social support network.",
            "goals": "Return to pain-free work activities, resume recreational sports, improve sleep quality, and prevent future episodes"
        },
        "medical": {
            "history": f"8-week history of {topic} dysfunction following gradual onset. Initially managed with rest and over-the-counter medication with limited improvement. No previous episodes of similar symptoms.",
            "symptoms": f"Moderate {topic} pain (5-7/10), morning stiffness lasting 30-60 minutes, pain increases with activity and prolonged positioning. Sleep disturbance due to pain.",
            "examination": "Reduced range of motion in affected area, muscle tension and guarding, altered movement patterns, positive provocative tests consistent with condition. No neurological deficits noted.",
            "diagnostics": "Recent imaging shows mild to moderate degenerative changes appropriate for age. Blood work within normal limits. No signs of serious underlying pathology.",
            "outcome_measures": f"Numeric Pain Rating Scale: 6/10, Functional Disability Index: 40%, Fear-Avoidance Beliefs Questionnaire shows elevated scores indicating activity avoidance"
        },
        "questions": all_questions
    }


@app.route("/osce")
def premium():
    if "patreon_token" not in session:
        return redirect(
            f"https://www.patreon.com/oauth2/authorize"
            f"?response_type=code&client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&scope=identity%20identity.memberships"
        )

    resp = requests.get(
        "https://www.patreon.com/api/oauth2/v2/identity"
        "?include=memberships,memberships.currently_entitled_tiers",
        headers={"Authorization": f"Bearer {session['patreon_token']}"}
    )
    data = resp.json()

    # 👇 TEMP DEBUG - print whole response to Render logs
    print(json.dumps(data, indent=2))

    included = data.get("included", [])

    for obj in included:
        if obj.get("type") == "member":
            status = obj.get("attributes", {}).get("patron_status")
            if status == "active_patron":
                return render_template("osce.html")

    return "🔒 Access denied – you must be an active patron."

@app.route("/callback")
def callback():
    """Patreon redirects here after login"""
    code = request.args.get("code")
    token_resp = requests.post("https://www.patreon.com/api/oauth2/token", data={
        "code": code, "grant_type": "authorization_code",
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }).json()
    session["patreon_token"] = token_resp["access_token"]
    return redirect(url_for("premium"))




if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)