# 🎙️ Deploy Free TTS to LGMD Patient Page

## Option 1: Manual Deployment (If SSH keys not working)

### Step 1: Copy the HTML content

Open `lgmd-free-tts-implementation.html` and copy ALL the content (Ctrl+A, Ctrl+C)

### Step 2: SSH into server

```bash
ssh -i ~/.ssh/aws-lightsail.pem ubuntu@3.11.229.68
# or
ssh -i aws-lightsail.pem ubuntu@3.11.229.68
```

### Step 3: Find LGMD directory

```bash
# Try these locations:
ls -la /home/ubuntu/lgmd-research-agent
# or
ls -la /var/www/lgmd
# or
ls -la /opt/lgmd
```

### Step 4: Backup and create new file

```bash
# Replace /path/to/lgmd with actual path from Step 3
cd /path/to/lgmd

# Backup existing file
sudo cp patient.html patient.html.backup

# Create new file
sudo nano patient.html
```

### Step 5: Paste content

- Paste the HTML content you copied in Step 1
- Press `Ctrl+O` to save
- Press `Enter` to confirm
- Press `Ctrl+X` to exit

### Step 6: Set permissions

```bash
sudo chown www-data:www-data patient.html
sudo chmod 644 patient.html
```

### Step 7: Restart services

```bash
# Restart LGMD service (if exists)
sudo systemctl restart lgmd

# Reload nginx
sudo systemctl reload nginx
```

### Step 8: Test

Visit: https://lgmd.hardinai.co.uk/patient

---

## Option 2: Using SCP (If you have the SSH key)

```bash
# Upload file
scp -i ~/.ssh/aws-lightsail.pem lgmd-free-tts-implementation.html ubuntu@3.11.229.68:/tmp/patient.html

# SSH and deploy
ssh -i ~/.ssh/aws-lightsail.pem ubuntu@3.11.229.68

# Find LGMD directory and deploy
sudo cp /tmp/patient.html /path/to/lgmd/patient.html
sudo chown www-data:www-data /path/to/lgmd/patient.html
sudo systemctl reload nginx
```

---

## Option 3: Using Git (Easiest if LGMD is a git repo)

```bash
# On your local machine
git add lgmd-free-tts-implementation.html
git commit -m "Add free TTS to patient page"
git push origin main

# On server
ssh ubuntu@3.11.229.68
cd /path/to/lgmd
sudo git pull origin main
sudo cp lgmd-free-tts-implementation.html patient.html
sudo systemctl reload nginx
```

---

## 🔍 Finding Your SSH Key

If you can't SSH, you need to find your AWS Lightsail key:

### On Windows:
```powershell
# Check common locations
dir C:\Users\$env:USERNAME\.ssh\
dir C:\Users\$env:USERNAME\Downloads\*.pem
```

### On Mac/Linux:
```bash
# Check common locations
ls -la ~/.ssh/
ls -la ~/Downloads/*.pem
```

### Download from AWS Lightsail:
1. Go to: https://lightsail.aws.amazon.com/
2. Click "Account" → "SSH Keys"
3. Download your key
4. Save as `aws-lightsail.pem`
5. Set permissions: `chmod 400 aws-lightsail.pem`

---

## ✅ What This Does

**Before:**
- Uses paid API for text-to-speech
- Costs money per request
- Requires API keys

**After:**
- Uses browser's built-in speech synthesis
- 100% FREE
- No API needed
- Works offline
- Supports 12 languages

---

## 🎯 Features

- ✅ 12 languages supported
- ✅ Pause/Resume/Stop controls
- ✅ Progress bar
- ✅ Transcript display
- ✅ Modern UI matching LGMD design
- ✅ Mobile responsive

---

## 🧪 Test Locally First

Before deploying, test it locally:

1. Open `lgmd-free-tts-implementation.html` in Chrome/Firefox/Edge
2. Select a language
3. Click "Generate & Play Latest Update"
4. ARIA should start speaking!

If it works locally, it will work on the server.

---

## 📞 Troubleshooting

### "Permission denied (publickey)"
- You need the SSH key file
- Download from AWS Lightsail console
- Use: `ssh -i /path/to/key.pem ubuntu@3.11.229.68`

### "No such file or directory"
- LGMD might be in a different location
- Try: `sudo find / -name "lgmd*" -type d 2>/dev/null`

### "Speech not working"
- Make sure you're using HTTPS (not HTTP)
- Try a different browser (Chrome works best)
- Check browser console for errors

---

**Created:** May 9, 2026  
**Status:** Ready to deploy  
**Cost:** $0 (completely free!)
