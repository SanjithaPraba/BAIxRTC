# BAIxRTC
Building RAG-based AI agents serving international non-profit, Rewriting The Code

For Devs:
## Creating a New Branch
Before creating a new branch, ensure your local `main` branch is up to date:
```bash
git checkout main
git pull origin main  # Ensure your local main is up to date
git checkout -b <ticketNumber-new-branch-name>  # Create and switch to a new branch
source venv/bin/activate  # (or `venv\Scripts\activate` on Windows)
```

# Project Setup Instructions

## Prerequisites
Ensure you have the following installed on your system:
- Python 3.8 or later
- Git

## Setting Up the Virtual Environment
To standardize the development process, we use a virtual environment. Follow these steps to set it up:

### **1. Clone the Repository**
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### **2. Run the Setup Script**
For macOS/Linux:
```bash
chmod +x setup.sh
./setup.sh
```
For Windows (Command Prompt or PowerShell):
```bat
setup.bat
```
This will:
- Create a virtual environment named `venv`
- Install required dependencies from `requirements.txt`

### **3. Activate the Virtual Environment**
#### macOS/Linux:
```bash
source venv/bin/activate
```
#### Windows (Command Prompt):
```bat
venv\Scripts\activate
```
#### Windows (PowerShell):
```powershell
.\venv\Scripts\Activate
```

### **4. Verify Installation**
Run the following to check if all necessary packages are installed:
```bash
python -c "import langchain; import langgraph; import chromadb; print('All imports work')"
```
If no errors appear, the setup is complete.

## Adding New Dependencies
If your branch requires a new package:
```bash
pip install <package-name>
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Added new dependency: <package-name>"
git push origin <your-branch>
```

## Keeping Your Environment Up to Date
Each time you start a new branch or switch to `main`:
```bash
git pull origin main
pip install -r requirements.txt
```

## Best Practices
- **Always activate the virtual environment before running scripts.**
- **Only update `requirements.txt` when adding new dependencies.**
- **Merge only `requirements.txt` to `main` when adding dependencies.**

Happy coding!

