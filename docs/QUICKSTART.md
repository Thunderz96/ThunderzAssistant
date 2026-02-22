# ⚡ Quick Start Guide - Thunderz Assistant

Get up and running in 5 minutes!

## Step 1: Check Python Installation

Open a terminal (Command Prompt on Windows) and type:
```bash
python --version
```

You should see Python 3.7 or higher. If not, download Python from [python.org](https://www.python.org).

## Step 2: Navigate to the Project

In your terminal, navigate to the project folder:
```bash
cd C:\path\to\ThunderzAssistant
```

## Step 3: Install Dependencies

Install the required packages:
```bash
pip install -r requirements.txt
```

This will install the `requests` library needed for the weather and dashboard modules.

## Step 4: Run the Application

Start Thunderz Assistant:
```bash
python main.py
```

The **Daily Dashboard** loads automatically with your greeting, live clock, weather, and a daily quote!

## Step 5: Explore the Features

**Dashboard** (loads on startup):
1. See your weather, clock, and daily motivational quote
2. Add tasks in the **Quick Tasks** section
3. Check off tasks as you complete them

**Weather Checker**:
1. Click **"Weather"** in the sidebar
2. Your location's weather loads automatically
3. Or type a city name and click **"Get Weather"**

---

## Troubleshooting

### Issue: "python is not recognized"
**Solution**: Add Python to your PATH or use `py` instead of `python`

### Issue: "No module named 'requests'"
**Solution**: Run `pip install -r requirements.txt` again

### Issue: "Weather not loading"
**Solution**: 
- Check your internet connection
- Try a different city name
- Make sure the city name is spelled correctly

---

## Next Steps

### Customize the App
- Open `config.py` to change colors and settings
- Modify `main.py` to adjust the window size

### Add Version Control (Optional)
```bash
git init
git add .
git commit -m "Initial commit"
```

### Plan Your Next Module
Think about what tool would help your workflow! Some ideas:
- Habit tracker
- Quick notes
- Unit converter
- Timer

Check out `dashboard_module.py` and `weather_module.py` to see how modules are structured, then create your own!

---

## Need Help?

- Check the **README.md** for detailed documentation
- Look at the code comments - everything is explained!
- Review **CHANGELOG.md** for version history

**Happy coding! ⚡**
