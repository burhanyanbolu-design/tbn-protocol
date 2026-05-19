"""
TBN Billing — Stripe Subscription Management
Handles: subscription creation, API key generation, webhook events
"""

import os
import stripe
from flask import Blueprint, request, jsonify
from .access_control import generate_api_key

billing = Blueprint('billing', __name__)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')

# Stripe Price IDs — create these in Stripe dashboard
# or we create them programmatically below
PLANS = {
    'starter':  {'monthly': 9900,  'annual': 79 * 12 * 100, 'name': 'TBN Starter',  'bots': 5},
    'pro':      {'monthly': 29900, 'annual': 239 * 12 * 100, 'name': 'TBN Pro',      'bots': 25},
    'business': {'monthly': 99900, 'annual': 799 * 12 * 100, 'name': 'TBN Business', 'bots': 999},
}


@billing.route('/create-subscription', methods=['POST'])
def create_subscription():
    """Create a Stripe payment intent for a TBN subscription"""
    try:
        data    = request.get_json(force=True) or {}
        plan    = data.get('plan', 'pro')
        company = data.get('company', '').strip()
        email   = data.get('email', '').strip()
        annual  = data.get('annual', False)

        if not company or not email:
            return jsonify({'error': 'Company name and email are required'}), 400

        if plan not in PLANS:
            return jsonify({'error': 'Invalid plan'}), 400

        plan_info = PLANS[plan]
        amount    = plan_info['annual'] if annual else plan_info['monthly']

        # Create or get Stripe customer
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=email,
                name=company,
                metadata={'company': company, 'plan': plan}
            )

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='gbp',
            customer=customer.id,
            automatic_payment_methods={'enabled': True},
            metadata={
                'plan':    plan,
                'company': company,
                'email':   email,
                'annual':  str(annual),
                'service': 'TBN Protocol'
            },
            description=f"TBN {plan_info['name']} {'Annual' if annual else 'Monthly'} Subscription"
        )

        # Pre-generate API key (activated after payment confirmed)
        api_key_record = generate_api_key(
            company_name = company,
            email        = email,
            tier         = plan.upper() if plan != 'business' else 'PRO'
        )

        return jsonify({
            'client_secret':  intent.client_secret,
            'api_key':        api_key_record['api_key'],
            'plan':           plan,
            'amount':         amount,
            'customer_id':    customer.id,
        })

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e.user_message)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@billing.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload    = request.get_data()
    sig_header = request.headers.get('Stripe-Signature', '')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = stripe.Event.construct_from(request.get_json(), stripe.api_key)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    # Handle payment success
    if event['type'] == 'payment_intent.succeeded':
        intent   = event['data']['object']
        email    = intent['metadata'].get('email', '')
        company  = intent['metadata'].get('company', '')
        plan     = intent['metadata'].get('plan', '')

        # Send welcome email
        _send_welcome_email(email, company, plan)

        print(f"Payment succeeded: {company} ({email}) - {plan}")

    return jsonify({'status': 'ok'})


@billing.route('/plans', methods=['GET'])
def get_plans():
    """Return available plans"""
    return jsonify({
        'plans': [
            {'id': 'starter',  'name': 'Starter',  'monthly': 99,  'annual': 79,  'bots': 5,   'popular': False},
            {'id': 'pro',      'name': 'Pro',       'monthly': 299, 'annual': 239, 'bots': 25,  'popular': True},
            {'id': 'business', 'name': 'Business',  'monthly': 999, 'annual': 799, 'bots': 999, 'popular': False},
        ]
    })


def _send_welcome_email(email, company, plan):
    """Send welcome email after successful payment"""
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0f;color:#e0e0e0;padding:40px;border-radius:12px">
          <div style="text-align:center;margin-bottom:30px">
            <h1 style="color:#00d4ff;font-size:28px">TBN Protocol</h1>
            <p style="color:#8b949e">Trusted Bot Network</p>
          </div>
          <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:24px;margin-bottom:24px">
            <h2 style="color:#fff;margin-bottom:16px">Welcome to TBN, {company}!</h2>
            <p style="color:#8b949e;margin-bottom:16px">Your <strong style="color:#00d4ff">{plan.title()} subscription</strong> is now active.</p>
            <p style="color:#8b949e;margin-bottom:16px">Your API key has been sent separately. Keep it safe — it gives access to your TBN bots.</p>
            <a href="https://tbn.hardinai.co.uk" style="display:inline-block;background:#00d4ff;color:#000;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700">Go to Dashboard</a>
          </div>
          <p style="text-align:center;color:#484f58;font-size:12px">Questions? Email burhan@hardinai.co.uk</p>
        </div>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Welcome to TBN Protocol — Your {plan.title()} subscription is active'
        msg['From']    = 'burhan@hardinai.co.uk'
        msg['To']      = email
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL('smtp.ionos.co.uk', 465, timeout=10) as server:
            server.login('burhan@hardinai.co.uk', os.environ.get('IONOS_PASS', ''))
            server.sendmail('burhan@hardinai.co.uk', email, msg.as_string())

        print(f"Welcome email sent to {email}")
    except Exception as e:
        print(f"Welcome email failed: {e}")
