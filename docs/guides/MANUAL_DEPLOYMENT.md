# Manual Deployment Guide for Windows

If the automated scripts don't work due to SSH issues, you can deploy manually.

## **Option 1: Use Git to Deploy**

Since your code is already on GitHub, you can pull the latest changes directly on the server:

### **1. SSH into your server** (using PuTTY or Windows Terminal)
```
Server: 3.11.229.68
User: ubuntu
```

### **2. Update the code on the server**
```bash
cd /opt/tbn-protocol
git pull origin main
```

### **3. Install new dependencies**
```bash
cd /opt/tbn-protocol
.venv/bin/pip install -r requirements.txt
```

### **4. Restart the service**
```bash
sudo systemctl restart tbn
sudo systemctl status tbn
```

## **Option 2: Upload Files Manually**

### **1. Use WinSCP or FileZilla to upload files**
- Server: 3.11.229.68
- User: ubuntu
- Upload your project files to: `/opt/tbn-protocol/`

### **2. SSH into server and restart**
```bash
cd /opt/tbn-protocol
sudo systemctl restart tbn
```

## **Option 3: Push to GitHub First**

### **1. Commit and push your changes**
```cmd
git add .
git commit -m "Add GitHub BICA and Certification Portal"
git push origin main
```

### **2. Pull on server**
```bash
# SSH into your server first
cd /opt/tbn-protocol
git pull origin main
.venv/bin/pip install -r requirements.txt
sudo systemctl restart tbn
```

## **Verify Deployment**

After any method, check that it's working:

1. **Visit:** https://tbn.hardinai.co.uk
2. **Check API:** https://tbn.hardinai.co.uk/api/stats
3. **Test Certification Portal:** https://tbn.hardinai.co.uk/certification/portal

## **Next Steps**

1. **Set up GitHub BICA** (optional):
   - Create GitHub repository: `burhanyanbolu-design/tbn-bica-registry`
   - Generate GitHub token
   - Add to server environment

The new features will work with local storage even without GitHub integration!