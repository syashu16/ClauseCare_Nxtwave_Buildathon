import os
import re
import textstat
import time
import sys
from groq import Groq
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize Colorama for Terminal Colors
init(autoreset=True)
load_dotenv()

# --- 1. CONFIGURATION & PROMPTS ---

SIMPLIFICATION_PROMPT = """You are a legal expert who explains complex legal language in simple terms.

Original Clause:
{clause}

Task: Rewrite this clause in plain, simple language that a high school student can understand.

Requirements:
- Use everyday words (avoid legal jargon)
- Break into short sentences
- Explain what it means in practice
- Highlight key obligations, deadlines, or risks
- Keep the legal meaning accurate

Format your response exactly as:
SIMPLIFIED: [your simplified version]
KEY POINTS: [bullet points of important details]
WATCH OUT: [any risks or important considerations]
"""

RISK_PROMPT = """
Analyze the following legal clause. 
Return ONLY a number between 0 and 100 indicating the risk level (0=Safe, 100=Dangerous).
Do not explain. Just the number.

Clause: {clause}
"""

# --- 2. CORE LOGIC CLASS ---

class LegalAI:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print(Fore.RED + "CRITICAL ERROR: GROQ_API_KEY not found in .env")
            sys.exit(1)
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile" 

    def get_readability(self, text):
        """Calculates Flesch Reading Ease (Higher = Easier)"""
        return textstat.flesch_reading_ease(text)

    def split_clauses(self, text):
        """Intelligent Regex splitting of legal clauses"""
        # Detects 1., 1.1, (a), Article 1, Section 5
        pattern = r'(?:\n\s*(\d+\.|[a-z]\)|\d+\.\d+|ARTICLE [IVX]+|SECTION \d+)\s+)'
        parts = re.split(pattern, text)
        
        clauses = []
        if len(parts) > 1:
            for i in range(1, len(parts), 2):
                marker = parts[i]
                content = parts[i+1] if i+1 < len(parts) else ""
                full_clause = f"{marker} {content}".strip()
                # Filter out empty or too short lines
                if len(full_clause) > 20: 
                    clauses.append(full_clause)
        else:
            # Fallback for plain text without numbers
            clauses = [p.strip() for p in text.split('\n\n') if len(p) > 20]
            
        return clauses

    def analyze_risk(self, text):
        """Calls Groq to get a 0-100 Risk Score"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": RISK_PROMPT.format(clause=text)}],
                max_tokens=10,
                temperature=0.1
            )
            raw = response.choices[0].message.content
            score = int(''.join(filter(str.isdigit, raw)))
            return score
        except:
            return 50 # Default if AI fails

    def simplify(self, text):
        """Calls Groq to Simplify text"""
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": SIMPLIFICATION_PROMPT.format(clause=text)}],
                max_tokens=800,
                temperature=0.3
            )
            duration = time.time() - start_time
            return response.choices[0].message.content, duration
        except Exception as e:
            return f"Error: {e}", 0

# --- 3. TERMINAL INTERFACE ---

def get_multiline_input():
    """Helper to capture pasted text with newlines"""
    print(Fore.YELLOW + "Paste your legal text below. Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) then Enter to save:")
    lines = sys.stdin.readlines()
    return "".join(lines)

def print_separator():
    print(Fore.CYAN + "-" * 60)

def main():
    ai = LegalAI()
    
    print(Fore.GREEN + Style.BRIGHT + "\n=== ⚖️  GenLegalAI Terminal (Dynamic Input) ===\n")
    
    # --- STEP 1: GET USER INPUT ---
    raw_text = ""
    print("How would you like to provide the text?")
    print("1. Paste text directly")
    print("2. Read from a text file")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == '1':
        raw_text = get_multiline_input()
    elif choice == '2':
        path = input(Fore.YELLOW + "Enter file path (e.g., contract.txt): ").strip()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        except FileNotFoundError:
            print(Fore.RED + "Error: File not found.")
            sys.exit(1)
    else:
        print(Fore.RED + "Invalid choice.")
        sys.exit(1)

    if len(raw_text) < 10:
        print(Fore.RED + "Text is too short to analyze.")
        sys.exit(1)

    # --- STEP 2: PROCESS CLAUSES ---
    print_separator()
    print(f"{Fore.BLUE}Scanning document structure...")
    clauses = ai.split_clauses(raw_text)
    
    if not clauses:
        print(Fore.RED + "No distinct clauses found. Treating entire text as one block.")
        clauses = [raw_text]
    else:
        print(f"{Fore.GREEN}Successfully detected {len(clauses)} distinct clauses.")

    # --- STEP 3: INTERACTIVE LOOP ---
    while True:
        print_separator()
        print("MENU:")
        print("[L] List all clauses")
        print("[A] Analyze a specific clause")
        print("[Q] Quit")
        
        cmd = input(f"\n{Fore.GREEN}Command > ").strip().upper()
        
        if cmd == 'Q':
            print("Exiting...")
            break
            
        elif cmd == 'L':
            print(Fore.YELLOW + "\n--- DETECTED CLAUSES ---")
            for idx, c in enumerate(clauses):
                preview = c[:60].replace('\n', ' ')
                print(f"{Fore.CYAN}[{idx}] {Fore.WHITE}{preview}...")
                
        elif cmd == 'A':
            try:
                idx_str = input("Enter Clause Number (e.g., 0): ")
                idx = int(idx_str)
                if idx < 0 or idx >= len(clauses):
                    print(Fore.RED + "Invalid Index number.")
                    continue
                
                target_clause = clauses[idx]
                
                print(f"\n{Fore.MAGENTA}Sending to Groq AI (Llama 3)... please wait.")
                
                # Run Analysis
                r_score_orig = ai.get_readability(target_clause)
                risk_score = ai.analyze_risk(target_clause)
                simple_text, time_taken = ai.simplify(target_clause)
                r_score_new = ai.get_readability(simple_text)
                
                # Visualization
                print_separator()
                print(f"{Fore.YELLOW}ORIGINAL CLAUSE:")
                print(f"{Fore.WHITE}{target_clause}")
                
                print("\n" + Fore.YELLOW + "RISK LEVEL:")
                if risk_score > 70:
                    print(f"{Fore.RED}🔴 HIGH RISK ({risk_score}/100)")
                elif risk_score > 40:
                    print(f"{Fore.YELLOW}🟡 MEDIUM RISK ({risk_score}/100)")
                else:
                    print(f"{Fore.GREEN}🟢 SAFE ({risk_score}/100)")
                    
                print("\n" + Fore.GREEN + f"SIMPLIFIED EXPLANATION ({time_taken:.2f}s):")
                print(f"{Fore.WHITE}{simple_text}")
                
                print_separator()
                print(f"{Fore.BLUE}Readability Score: {r_score_orig} -> {r_score_new} (Higher is better)")
                
            except ValueError:
                print(Fore.RED + "Please enter a valid number.")

if __name__ == "__main__":
    main()