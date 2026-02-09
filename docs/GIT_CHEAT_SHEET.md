# Git Quick Reference - Personal Cheat Sheet

## 🚀 Quick Workflow (Most Common)

```bash
# 1. Check what changed
git status

# 2. Add all changes
git add .

# 3. Commit with message
git commit -m "Your message here"

# 4. Push to GitHub
git push
```

---

## 📝 Common Commands

### **Check Status**
```bash
git status                    # See what changed
git log                       # See commit history
git log --oneline            # Compact history
```

### **Add Files**
```bash
git add .                     # Add all changes
git add main.py              # Add specific file
git add *.py                 # Add all Python files
git add docs/                # Add entire folder
```

### **Commit**
```bash
git commit -m "Short message"
git commit -m "Title" -m "Longer description in second paragraph"
```

### **Push**
```bash
git push                      # Push to current branch
git push origin main         # Push to main branch
```

---

## 🔥 Common Scenarios

### **Scenario 1: Quick Update**
```bash
git add .
git commit -m "Updated README"
git push
```

### **Scenario 2: New Feature**
```bash
git add .
git commit -m "v1.6.0 - Added menu bar and status bar"
git push
```

### **Scenario 3: Multiple Files**
```bash
git add main.py CHANGELOG.md README.md
git commit -m "Version bump to 1.6.0"
git push
```

### **Scenario 4: Oops, Forgot Something**
```bash
git add forgotten_file.py
git commit --amend --no-edit   # Add to last commit
git push --force               # ⚠️ Use carefully!
```

---

## 🔍 Before You Commit

### **Always Check First:**
```bash
git status                    # What's changed?
git diff                      # Show exact changes
git diff main.py             # Changes in specific file
```

### **Make Sure config.py is NOT Staged:**
```bash
git status | findstr config.py
# Should NOT appear in "Changes to be committed"
```

---

## ⚠️ Undo Commands (Use Carefully!)

### **Unstage Files**
```bash
git reset HEAD main.py       # Unstage a file
git reset HEAD .             # Unstage everything
```

### **Discard Changes**
```bash
git checkout -- main.py      # Discard changes to file
git checkout -- .            # Discard ALL changes (careful!)
```

### **Undo Last Commit (Keep Changes)**
```bash
git reset --soft HEAD~1      # Undo commit, keep changes staged
git reset HEAD~1             # Undo commit, keep changes unstaged
```

### **Undo Last Commit (Delete Changes)**
```bash
git reset --hard HEAD~1      # ⚠️ DESTROYS changes!
```

---

## 🌿 Branches (When You Need Them)

### **Create and Switch**
```bash
git branch                    # List branches
git branch feature-name      # Create branch
git checkout feature-name    # Switch to branch
git checkout -b feature-name # Create + switch
```

### **Merge**
```bash
git checkout main            # Switch to main
git merge feature-name       # Merge feature into main
git push                     # Push merged code
```

### **Delete Branch**
```bash
git branch -d feature-name   # Delete local branch
```

---

## 📥 Pull Changes

### **Get Latest from GitHub**
```bash
git pull                      # Pull latest changes
git pull origin main         # Pull from specific branch
```

### **If There Are Conflicts:**
```bash
git pull
# Fix conflicts in files
git add .
git commit -m "Resolved conflicts"
git push
```

---

## 🔧 Configuration

### **First Time Setup**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### **Check Config**
```bash
git config --list            # See all settings
git config user.name         # See username
```

---

## 📊 Useful Info Commands

### **See What Changed**
```bash
git status                    # Current status
git diff                      # Unstaged changes
git diff --staged            # Staged changes
git log                       # Commit history
git log --oneline --graph    # Pretty history
```

### **See Remote Info**
```bash
git remote -v                # Show remote URLs
git branch -a                # Show all branches
```

---

## 🎯 My Thunderz Assistant Workflow

### **After Making Changes:**
```bash
# 1. Check what I changed
git status

# 2. Make sure config.py isn't staged!
git status | findstr config.py
# (Should be empty or "Untracked")

# 3. Stage my changes
git add .

# 4. Verify what's staged
git status

# 5. Commit with good message
git commit -m "v1.6.0 - Enhanced UI with menu bar and status bar"

# 6. Push to GitHub
git push

# Done! 🎉
```

---

## 💡 Good Commit Message Examples

### **Format: `type: description`**

**Good:**
```
v1.6.0 - Enhanced UI with menu bar and status bar
Fixed video looping in Glizzy module
Added keyboard shortcuts (Ctrl+1,2,3)
Updated documentation for v1.6.0
Refactored dashboard module for better performance
```

**Bad:**
```
update
fixed stuff
changes
asdf
```

---

## 📋 Pre-Commit Checklist

Before every `git commit`:

- [ ] Ran `git status` to see changes
- [ ] Verified config.py is NOT in the list
- [ ] Tested the code (`python main.py`)
- [ ] Updated CHANGELOG.md if needed
- [ ] Updated README.md if needed
- [ ] Added meaningful commit message

---

## 🔐 Security Reminders

### **NEVER Commit These:**
- config.py (has API keys!)
- __pycache__/ folders
- .pyc files
- Personal data files
- Passwords or tokens
- Local backups (backups/ folder)

### **Check .gitignore:**
```bash
cat .gitignore               # View gitignore
```

Should contain:
```
config.py
__pycache__/
*.pyc
backups/
```

---

## 🆘 Emergency Commands

### **"Oh No, I Committed config.py!"**
```bash
# If you haven't pushed yet:
git reset HEAD~1              # Undo commit
git reset HEAD config.py      # Unstage config.py
git add .                     # Re-add everything else
git commit -m "Your message"

# If you already pushed:
# 1. Remove from repo but keep local file
git rm --cached config.py
git commit -m "Remove config.py from tracking"
git push

# 2. Add to .gitignore if not already
echo config.py >> .gitignore
git add .gitignore
git commit -m "Add config.py to gitignore"
git push
```

### **"I Want to Start Over"**
```bash
git reset --hard HEAD        # Discard ALL local changes
git pull                     # Get latest from GitHub
```

### **"I Messed Up My Last Commit Message"**
```bash
git commit --amend -m "New message"
git push --force             # If already pushed
```

---

## 🎓 Learning More

### **Official Resources:**
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)

### **Interactive Learning:**
- [Learn Git Branching](https://learngitbranching.js.org/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

## 🚨 When in Doubt

```bash
# Don't know what will happen? Test first:
git status                    # See current state
git diff                      # See what would change

# Confused? Ask for help:
git status                    # Describe what you see
```

---

## 📱 Quick Reference Card

```
ADD → COMMIT → PUSH

git add .
git commit -m "Message"
git push

That's it! 🎉
```

---

**Made a mistake?** Don't panic! Git is designed to be forgiving. Most things can be undone!

**Remember:** Commit often, push regularly, and always check `git status` first! ✨
