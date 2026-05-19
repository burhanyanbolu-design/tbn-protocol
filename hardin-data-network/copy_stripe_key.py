"""Copy Stripe key from Heathrow to TBN"""
# Read key from heathrow
with open('/var/www/heathrowblackcabs/.env') as f:
    for line in f:
        if line.startswith('STRIPE_SECRET_KEY='):
            secret_key = line.strip().split('=', 1)[1]
            break

# Read TBN env
with open('/opt/tbn-protocol/.env') as f:
    content = f.read()

# Replace placeholder
content = content.replace('STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE', f'STRIPE_SECRET_KEY={secret_key}')

# Write back
with open('/opt/tbn-protocol/.env', 'w') as f:
    f.write(content)

print(f'Done - Stripe key copied: {secret_key[:12]}...')

# Also get publishable key from heathrow if it exists
try:
    with open('/var/www/heathrowblackcabs/.env') as f:
        for line in f:
            if line.startswith('STRIPE_PUBLISHABLE_KEY='):
                pub_key = line.strip().split('=', 1)[1]
                content = content.replace('STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE', f'STRIPE_PUBLISHABLE_KEY={pub_key}')
                with open('/opt/tbn-protocol/.env', 'w') as f2:
                    f2.write(content)
                print(f'Publishable key also copied: {pub_key[:12]}...')
                break
except:
    print('No publishable key found in heathrow env')
