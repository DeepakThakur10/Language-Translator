import os
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from langdetect import detect
import google.generativeai as genai
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# API Key for Gemini API
API_KEY = "AIzaSyBUPZRYib1SS4FzJfG4B8rAhetw4y_Hxaw"

# Configure the Gemini API client
genai.configure(api_key=API_KEY)

# Initialize the GenerativeModel
model = genai.GenerativeModel('gemini-1.5-flash')

# Flask configuration
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Language mappings
LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
    "zh": "Chinese (Simplified)", "ar": "Arabic", "hi": "Hindi", "ko": "Korean",
    "mai": "Maithili"
}

MAX_TEXT_LENGTH = 5000

# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Render the HTML page."""
    return render_template('index.html', user=session.get('user'))

@app.route('/available_languages', methods=['GET'])
def get_languages():
    """Returns supported translation languages."""
    return jsonify({"success": True, "languages": LANGUAGES})

@app.route('/translate', methods=['POST'])
def translate():
    """Handles translation requests."""
    data = request.json
    text = data.get("text", "").strip()
    source_language = data.get("source_language", "auto")
    target_language = data.get("target_language", "en")

    # Input validation
    if not text:
        return jsonify({"success": False, "error": "No text provided"})
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"success": False, "error": f"Text exceeds {MAX_TEXT_LENGTH} characters"})
    if target_language not in LANGUAGES:
        return jsonify({"success": False, "error": "Invalid target language"})

    detected_language = None

    # Step 1: Language Detection
    if source_language == "auto":
        try:
            detect_prompt = f"Identify the language of the following text and return the ISO 639-1 code:\n\n{text}"
            detect_response = model.generate_content(
                detect_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0,
                    max_output_tokens=5
                )
            )
            detected_language = detect_response.text.strip().lower()
            source_language = detected_language if detected_language in LANGUAGES else "en"
        except Exception as e:
            return jsonify({"success": False, "error": f"Language detection failed: {str(e)}"})

    # Step 2: Translation Request
    try:
        translate_prompt = f"Translate the following text to {LANGUAGES.get(target_language, target_language)}:\n\n{text}"
        translate_response = model.generate_content(
            translate_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024
            )
        )
        translation = translate_response.text.strip()
        return jsonify({
            "success": True,
            "translated_text": translation,
            "detected_source_language": detected_language
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Translation API error: {str(e)}"})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user sign-up."""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Input validation
        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('signup'))

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please sign in.', 'error')
            return redirect(url_for('signup'))

        # Create new user
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Sign-up successful! Please sign in.', 'success')
        return redirect(url_for('signin'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Handle user sign-in."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Input validation
        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('signin'))

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('signin'))

        # Log the user in
        session['user'] = {'id': user.id, 'name': user.name, 'email': user.email}
        flash('Sign-in successful!', 'success')
        return redirect(url_for('index'))

    return render_template('signin.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))



@app.route('/payment', methods=['GET', 'POST'])
def payment():
    """Render the payment page and handle payment form submission."""
    if not session.get('user'):
        flash('Please sign in to purchase a membership.', 'error')
        return redirect(url_for('signin.html'))

    if request.method == 'POST':
        plan = request.form.get('plan')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')
        cvv = request.form.get('cvv')
        cardholder_name = request.form.get('cardholder_name')

        # Placeholder for payment processing logic
        # In a real application, you would integrate with a payment gateway like Stripe or PayPal here
        # For now, we'll simulate a successful payment
        try:
            # Simulate payment processing
            # Example: Integrate with Stripe
            # stripe.PaymentIntent.create(
            #     amount=999 if plan == 'monthly' else 8999 if plan == 'annual' else 1499,
            #     currency='usd',
            #     payment_method_types=['card'],
            #     description=f'{plan.capitalize()} Membership for {cardholder_name}',
            # )

            flash(f'Payment successful! You have subscribed to the {plan.capitalize()} plan.', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Payment failed: {str(e)}', 'error')
            return redirect(url_for('payment'))

    return render_template('process_payment.html')

@app.route('/process_payment', methods=['POST'])
def process_payment():
    """Handle payment form submission."""
    if not session.get('user'):
        flash('Please sign in to purchase a membership.', 'error')
        return redirect(url_for('signin'))

    plan = request.form.get('plan')
    card_number = request.form.get('card_number')
    expiry_date = request.form.get('expiry_date')
    cvv = request.form.get('cvv')
    cardholder_name = request.form.get('cardholder_name')

    # Placeholder for payment processing logic
    # In a real application, you would integrate with a payment gateway like Stripe or PayPal here
    # For now, we'll simulate a successful payment
    try:
        # Simulate payment processing
        # Example: Integrate with Stripe
        # stripe.PaymentIntent.create(
        #     amount=999 if plan == 'monthly' else 8999 if plan == 'annual' else 1499,
        #     currency='usd',
        #     payment_method_types=['card'],
        #     description=f'{plan.capitalize()} Membership for {cardholder_name}',
        # )

        flash(f'Payment successful! You have subscribed to the {plan.capitalize()} plan.', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Payment failed: {str(e)}', 'error')
        return redirect(url_for('process_payment'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)