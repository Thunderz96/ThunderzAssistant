# 🔒 Security Guide - API Keys & Secrets

This document explains how to safely handle API keys and other sensitive information in this project.

---

## ⚠️ **NEVER Commit Secrets to GitHub!**

API keys, passwords, and other secrets should **NEVER** be committed to version control. Here's why:
- Anyone can see your GitHub repository (if public)
- Keys can be scraped by bots within minutes
- Even if you delete the commit later, the key remains in Git history
- Leaked keys can be used to rack up charges or access your accounts

---

## ✅ **How This Project Handles Secrets**

### **Two Config Files System:**

1. **`config.example.py`** ✅ Safe to commit
   - Template file with placeholder values
   - Shows what settings are available
   - Contains `YOUR_API_KEY_HERE` instead of real keys
   - **This file IS committed to GitHub**

2. **`config.py`** ❌ Never commit
   - Your actual configuration with real API keys
   - Listed in `.gitignore` (Git ignores it automatically)
   - **This file stays on your computer only**

---

## 🛠️ **Setup Instructions**

### **For First-Time Setup:**

1. Copy the example config:
   ```bash
   cp config.example.py config.py
   ```
   
   Or on Windows:
   ```cmd
   copy config.example.py config.py
   ```

2. Open `config.py` and add your real API keys:
   ```python
   NEWS_API_KEY = "abc123yourrealkey456def"  # Your actual key
   ```

3. Verify `config.py` is in `.gitignore`:
   ```bash
   cat .gitignore | grep config.py
   ```

---

## 🔍 **Check What Git Sees**

Before committing, always check what files Git will include:

```bash
# See what Git is tracking
git status

# Verify config.py is NOT listed in red or green
# It should say "nothing to commit" or only show other files

# Double-check .gitignore is working
git check-ignore config.py
# Should output: config.py (meaning it's ignored)
```

---

## 🚨 **What If I Already Committed My API Key?**

### **If you haven't pushed to GitHub yet:**

1. Remove the file from Git (but keep it on your computer):
   ```bash
   git rm --cached config.py
   ```

2. Make sure `.gitignore` includes `config.py`

3. Commit the removal:
   ```bash
   git commit -m "Remove config.py from version control"
   ```

### **If you already pushed to GitHub:**

1. **Immediately revoke/regenerate your API key** on the service's website
2. Follow the "haven't pushed" steps above
3. Consider using `git filter-branch` or BFG Repo-Cleaner to remove the key from Git history (advanced)
4. For NewsAPI, get a new key at: https://newsapi.org/account

---

## 📝 **Best Practices**

### ✅ **DO:**
- Keep secrets in `config.py` (which is gitignored)
- Use `config.example.py` as a template for others
- Document which API keys are needed in README
- Regenerate keys immediately if leaked
- Use environment variables for production deployments
- Review `git status` before every commit

### ❌ **DON'T:**
- Commit files with actual API keys
- Share screenshots with visible API keys
- Hardcode keys directly in Python files
- Remove entries from `.gitignore`
- Use the same API key across multiple projects

---

## 🔑 **API Keys Used in This Project**

### **NewsAPI.org** (Optional)
- **Purpose:** Fetch breaking news headlines
- **Get It:** https://newsapi.org/register
- **Free Tier:** 100 requests/day
- **Where to Add:** `config.py` → `NEWS_API_KEY`

### **Weather (wttr.in)** (No key needed)
- **Purpose:** Fetch weather data
- **Free:** Yes, no registration needed
- **Rate Limits:** Fair use policy

---

## 🌐 **Environment Variables (Advanced)**

For production or shared environments, you can use environment variables instead:

```python
import os

NEWS_API_KEY = os.environ.get('NEWS_API_KEY', 'YOUR_API_KEY_HERE')
```

Then set the variable in your system:
```bash
# Linux/Mac
export NEWS_API_KEY="your_actual_key"

# Windows (PowerShell)
$env:NEWS_API_KEY="your_actual_key"

# Windows (CMD)
set NEWS_API_KEY=your_actual_key
```

---

## 📚 **Additional Resources**

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Git: gitignore documentation](https://git-scm.com/docs/gitignore)
- [NewsAPI: Account management](https://newsapi.org/account)

---

## ✅ **Quick Security Checklist**

Before every `git push`, verify:

- [ ] `config.py` is listed in `.gitignore`
- [ ] `git status` doesn't show `config.py`
- [ ] No API keys are hardcoded in `.py` files
- [ ] `config.example.py` only has placeholder values
- [ ] No sensitive data in comments or commit messages

---

**Remember:** Once a secret is pushed to GitHub, consider it compromised. Always regenerate the key!

Stay safe! 🛡️
