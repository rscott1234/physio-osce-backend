from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os

pythonCORS(app, origins=["https://www.rebeccathetutor.co.uk", "https://rebeccathetutor.co.uk"])
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "OSCE-App Running!",
        "port": os.environ.get("PORT", "5000"),
        "features": [
            "Detailed ROM measurements",
            "Pathophysiological reasoning", 
            "Outcome measures",
            "Enhanced clinical scenarios",
            "Mandatory Red/Orange Flags",
            "Problem List",
            "Treatment Indication",
            "6 OSCE Questions (3 Core + 3 Advanced)",
            "Biopsychosocial Model Integration",
            "Anatomy & Physiology Deep Dive",
            "Evidence-Based Learning"
        ]
    })

@app.route("/generate-case", methods=["GET"])
def generate_case():
    try:
        topic = request.args.get("topic", "musculoskeletal")
        print(f"⚡ Generating enhanced OSCE case for topic: {topic}")

        # Enhanced prompt for comprehensive OSCE case generation
        prompt = f"""
        Generate a comprehensive, realistic OSCE-ready physiotherapy case study for {topic} rehabilitation.
        
        This case should be suitable for final-year physiotherapy students and test both clinical reasoning and deeper understanding.

        Return ONLY valid JSON with this exact schema:

        {{
            "patient": {{
                "name": "realistic UK name",
                "age": "appropriate age for condition",
                "occupation": "relevant occupation that impacts case",
                "chief_complaint": "primary reason for seeking physiotherapy",
                "social_history": "lifestyle factors, activity level, relevant social context, family situation",
                "goals": "specific, measurable, realistic rehabilitation goals"
            }},
            "medical": {{
                "history": "detailed onset, mechanism of injury/condition, progression, previous treatments, relevant medical history",
                "symptoms": "current symptoms with specific descriptions, pain scales (0-10), functional limitations, aggravating/easing factors",
                "examination": "specific physical examination findings including ROM measurements in degrees, strength testing (0-5 scale), special tests with results, palpation findings",
                "diagnostics": "relevant imaging results, lab findings, or other diagnostic information with specific details",
                "outcome_measures": "specific validated assessment tools appropriate for this condition with baseline scores where relevant"
            }},
            "questions": [
                {{
                    "question": "What are the potential red or orange flags in this presentation that would require immediate medical attention or referral?",
                    "answer": "detailed explanation of warning signs, when to refer, and clinical reasoning behind each flag"
                }},
                {{
                    "question": "What would be your comprehensive problem list for this patient, prioritized from primary to secondary issues?",
                    "answer": "structured problem list with primary and secondary problems, explaining the rationale for prioritization"
                }},
                {{
                    "question": "What evidence-based treatment approach would you recommend and provide detailed rationale for each intervention?",
                    "answer": "comprehensive treatment plan with specific interventions, dosage/frequency, expected outcomes, and evidence base"
                }},
                {{
                    "question": "Explain the pathophysiology of this condition, linking relevant anatomy and physiology to the patient's presentation and recovery process.",
                    "answer": "detailed explanation of underlying pathophysiology, anatomical structures involved, physiological processes, and how these relate to symptoms and recovery"
                }},
                {{
                    "question": "How does the biopsychosocial model apply to this case, and what psychological and social factors might influence the patient's recovery?",
                    "answer": "comprehensive analysis of biological, psychological, and social factors, their interactions, and impact on treatment planning and outcomes"
                }},
                {{
                    "question": "What key anatomical structures are involved in this condition, and how do their normal functions relate to the patient's current limitations?",
                    "answer": "detailed anatomical explanation including specific structures, their normal function, how dysfunction leads to symptoms, and implications for treatment"
                }}
            ]
        }}

        IMPORTANT REQUIREMENTS:
        - Make the case realistic and clinically accurate
        - Include specific measurements, timeframes, and objective findings
        - Ensure answers are detailed and educational (150-300 words each)
        - Focus on evidence-based practice and clinical reasoning
        - Make it appropriate for final-year physiotherapy students
        - Include UK-relevant context where appropriate
        - Ensure the case tests both practical skills and theoretical knowledge
        """

        print("🤖 Calling OpenAI API for enhanced case generation...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an expert physiotherapy educator and OSCE examiner with extensive clinical experience. Create comprehensive, educational cases that test both practical skills and theoretical understanding. Always respond with valid JSON only. Make answers detailed and educational to promote deep learning."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=2500,
            temperature=0.7
        )

        ai_content = response.choices[0].message.content.strip()
        print("✅ Enhanced AI response received")

        # Clean up any potential markdown formatting
        if ai_content.startswith("```json"):
            ai_content = ai_content[7:]
        if ai_content.endswith("```"):
            ai_content = ai_content[:-3]
        ai_content = ai_content.strip()

        # Parse JSON safely
        case_data = json.loads(ai_content)
        print("📋 Enhanced case parsed successfully - 6 questions generated")

if __name__ == "__main__":
    print("🏥 OSCE-Ready Enhanced Physiotherapy App Starting...")
    print("📡 Server will run on: 0.0.0.0:$PORT (Render) or 127.0.0.1:5000 (local)")
    print("🔑 Make sure OPENAI_API_KEY environment variable is set!")
    print("💡 Test endpoint: /health")
    print("🎯 Enhanced Features:")
    print("   • 6 OSCE Questions (3 Core + 3 Advanced)")
    print("   • Pathophysiology Deep Dive")
    print("   • Biopsychosocial Model Integration") 
    print("   • Detailed Educational Answers")
    print("   • Evidence-Based Clinical Reasoning")

    # Render assigns us a port via the $PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
