from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import json

app = Flask(__name__)
CORS(app)  # Allow requests from your HTML file

# Load your API key (set it in your terminal before running)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/generate-case", methods=["GET"])
def generate_case():
    topic = request.args.get("topic", "musculoskeletal")

    # Enhanced prompts for each specialty
    topic_specific_prompts = {
        "musculoskeletal": """
        Generate a realistic musculoskeletal physiotherapy case study. Include:
        - Detailed ROM measurements (degrees, end feel descriptions)
        - Strength testing (manual muscle testing grades)
        - Pain assessment (VAS scores, aggravating/easing factors, pain behavior)
        - Functional outcome measures (e.g., Oswestry, DASH, Lower Extremity Functional Scale)
        - Imaging findings with clinical correlation
        Additional questions should focus on biomechanical reasoning, tissue healing phases, and movement analysis.
        """,

        "neurological": """
        Generate a realistic neurological physiotherapy case study. Include:
        - Detailed neurological examination (reflexes, tone, sensation, coordination)
        - Functional assessments (Berg Balance Scale, Timed Up & Go, 10m walk test)
        - Cognitive/communication status if relevant
        - Imaging findings (CT/MRI with anatomical correlation)
        - Outcome measures (FIM, Barthel Index, GMFCS for pediatric)
        Additional questions should focus on neuroplasticity, motor learning principles, and pathophysiological mechanisms.
        """,

        "cardiopulmonary": """
        Generate a realistic cardiopulmonary physiotherapy case study. Include:
        - Vital signs (HR, BP, RR, SpO2 at rest and with exertion)
        - Arterial blood gas results with interpretation
        - Exercise tolerance testing (6MWT, incremental shuttle walk)
        - Chest examination findings (auscultation, percussion, palpation)
        - Relevant investigations (ECG, echocardiogram, spirometry)
        Additional questions should focus on gas exchange physiology, exercise physiology, and cardiopulmonary pathophysiology.
        """,

        "pediatric": """
        Generate a realistic pediatric physiotherapy case study. Include:
        - Developmental milestones and current functional level
        - Detailed movement analysis and motor patterns
        - Family/caregiver concerns and goals
        - Standardized assessments (GMFM, PEDI, Alberta Infant Motor Scale)
        - Growth and development considerations
        Additional questions should focus on motor development, neuroplasticity in children, and family-centered care principles.
        """,

        "elderly_rehab": """
        Generate a realistic elderly rehabilitation physiotherapy case study. Include:
        - Comprehensive geriatric assessment findings
        - Falls risk assessment (Berg Balance, Timed Up & Go, FRAT)
        - Medication review and polypharmacy considerations
        - Cognitive screening results (MMSE, MoCA)
        - Social circumstances and discharge planning needs
        - Frailty indicators and functional decline patterns
        Additional questions should focus on age-related physiological changes, multimorbidity management, and falls prevention strategies.
        """,

        "sports": """
        Generate a realistic sports rehabilitation physiotherapy case study. Include:
        - Sport-specific demands and injury mechanism
        - Detailed biomechanical analysis
        - Return-to-sport criteria and testing
        - Psychological readiness assessment
        - Performance metrics and functional testing
        - Injury prevention strategies
        Additional questions should focus on tissue healing timelines, biomechanical factors, and evidence-based return-to-sport protocols.
        """
    }

    base_prompt = f"""
    {topic_specific_prompts.get(topic, topic_specific_prompts["musculoskeletal"])}

    Please return ONLY valid JSON in this exact format:
    {{
      "title": "Descriptive case title",
      "patient": {{
        "name": "Realistic patient name",
        "age": 25,
        "occupation": "Specific occupation",
        "chiefComplaint": "Primary complaint in patient's words",
        "socialHistory": "Living situation, support systems, lifestyle factors",
        "goals": "Patient's own rehabilitation goals and expectations"
      }},
      "medical": {{
        "history": "Comprehensive medical history including comorbidities",
        "symptoms": "Detailed symptom description with timeline and behavior",
        "examination": "Thorough physical examination findings with specific measurements, ROM in degrees, strength grades, neurological signs, pain responses",
        "diagnostics": "Relevant imaging, lab results, blood gases, ECG findings with clinical interpretation",
        "outcomeMeasures": "1-2 validated outcome measures with baseline scores"
      }},
      "questions": [
        {{
          "question": "Identify any red flag(s) or orange flag(s) present in this case and explain their significance and required actions.",
          "answer": "Clear identification of flags",
          "reasoning": "Detailed explanation of why it's a flag, potential underlying pathology, and immediate clinical actions/referrals."
        }},
        {{
          "question": "From the assessment findings, generate a comprehensive physiotherapy problem list for this patient, ordered by priority.",
          "answer": "Prioritized list of problems",
          "reasoning": "Justification for each problem's inclusion and its priority based on clinical impact and patient goals."
        }},
        {{
          "question": "What physiotherapy treatment approach is indicated for this patient, and why? Include specific interventions and their rationale.",
          "answer": "Detailed treatment plan",
          "reasoning": "Explanation of the chosen interventions, their physiological basis, expected outcomes, and how they address the problem list and patient goals."
        }},
        {{
          "question": "Complex clinical reasoning question requiring pathophysiological understanding and analysis of examination findings",
          "answer": "Evidence-based answer with clear clinical reasoning",
          "reasoning": "Detailed explanation linking pathophysiology, examination findings, and treatment rationale with current evidence"
        }},
        {{
          "question": "Question focusing on prognosis, outcome prediction, or discharge planning requiring integration of multiple factors",
          "answer": "Realistic prognosis with supporting evidence",
          "reasoning": "Analysis of prognostic factors, evidence from literature, and patient-specific considerations"
        }}
      ]
    }}

    Make this case study challenging and realistic for final-year physiotherapy students preparing for practical examinations. Focus on clinical reasoning, pathophysiological understanding, and evidence-based practice. Include specific numerical values, measurements, and clinical findings that students would encounter in real practice. Ensure there are at least 5 questions in total, with the first three being the mandatory red/orange flags, problem list, and treatment indication.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": base_prompt}],
            temperature=0.8,
            max_tokens=3500  # Increased for more detailed cases and questions
        )

        ai_response = response.choices[0].message.content.strip()

        # Try to extract JSON if wrapped in markdown
        if "```json" in ai_response:
            ai_response = ai_response.split("```json")[1].split("```")[0].strip()
        elif "```" in ai_response:
            ai_response = ai_response.split("```")[1].strip()

        # Validate JSON
        try:
            json.loads(ai_response)
        except json.JSONDecodeError:
            raise Exception("Invalid JSON from AI")

        return jsonify({"case": ai_response, "source": "ai"})

    except Exception as e:
        print(f"AI Error: {e}")
        # Enhanced fallback cases
        enhanced_fallback = {
            "title": f"OSCE-Ready {topic.replace('_', ' ').title()} Case (AI Unavailable)",
            "patient": {
                "name": "System Generated Patient",
                "age": 45,
                "occupation": "Various",
                "chiefComplaint": "Please check backend connection for AI-generated cases",
                "socialHistory": "AI service temporarily unavailable",
                "goals": "Restore AI connectivity for unique case generation"
            },
            "medical": {
                "history": "OSCE-ready cases require AI backend",
                "symptoms": "Check terminal for Flask server status",
                "examination": "Ensure OpenAI API key is properly configured",
                "diagnostics": "Backend running on http://127.0.0.1:5000",
                "outcomeMeasures": "Connection Status Assessment: Failed"
            },
            "questions": [
                {
                    "question": "Identify any red flag(s) or orange flag(s) present in this case and explain their significance and required actions.",
                    "answer": "No specific red/orange flags in this fallback case. Always screen for: cauda equina, fracture, cancer, infection (red); psychosocial factors, fear-avoidance (orange).",
                    "reasoning": "Red flags indicate serious pathology requiring urgent medical attention. Orange flags highlight psychosocial factors influencing recovery. Both are critical for safe and effective physiotherapy practice."
                },
                {
                    "question": "From the assessment findings, generate a comprehensive physiotherapy problem list for this patient, ordered by priority.",
                    "answer": "1. AI connectivity issue; 2. Lack of dynamic case generation; 3. Limited learning experience.",
                    "reasoning": "The primary problem is the AI backend not providing dynamic cases, which directly impacts the app's ability to offer a comprehensive learning experience for students."
                },
                {
                    "question": "What physiotherapy treatment approach is indicated for this patient, and why? Include specific interventions and their rationale.",
                    "answer": "Troubleshooting backend connection, verifying API key, restarting server.",
                    "reasoning": "The most indicated 'treatment' for this 'patient' (the app) is to resolve the technical issues preventing AI case generation, as this is fundamental to its function."
                },
                {
                    "question": "What steps should be taken to restore AI functionality for enhanced case generation?",
                    "answer": "Verify backend is running and API key is configured",
                    "reasoning": "The enhanced case studies require AI integration to provide detailed pathophysiological reasoning and comprehensive clinical scenarios"
                },
                {
                    "question": "How do enhanced AI cases improve learning outcomes?",
                    "answer": "Provide unlimited unique scenarios with detailed clinical reasoning",
                    "reasoning": "AI-generated cases offer pathophysiological depth and clinical complexity that mirrors real examination conditions"
                }
            ]
        }
        return jsonify({"case": json.dumps(enhanced_fallback), "source": "fallback"})

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "OSCE-Ready AI Backend Running!", 
        "port": 5000,
        "features": ["Detailed ROM measurements", "Pathophysiological reasoning", "Outcome measures", "Enhanced clinical scenarios", "Mandatory Red/Orange Flags", "Problem List", "Treatment Indication"]
    })

if __name__ == "__main__":
    print("🏥 OSCE-Ready Physiotherapy AI Backend Starting...")
    print("📡 Server will run on: http://127.0.0.1:5000")
    print("🔑 Make sure OPENAI_API_KEY environment variable is set!")
    print("💡 Test endpoint: http://127.0.0.1:5000/health")
    print("🎯 New Features: Mandatory Red/Orange Flags, Problem List, Treatment Indication")
    # Render assigns us a port via the $PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
