"""Script kiem tra bao mat token.json"""
import os
import subprocess
import sys

def run_command(cmd):
    """Chay lenh va tra ve output."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)

def check_local_file():
    """Kiem tra file token.json co ton tai local khong."""
    print("\n" + "=" * 60)
    print("[1] KIEM TRA FILE LOCAL")
    print("=" * 60)
    
    if os.path.exists("token.json"):
        print("[WARNING] File token.json TON TAI o local")
        return True
    else:
        print("[OK] File token.json KHONG ton tai o local")
        return False

def check_git_tracked():
    """Kiem tra token.json co dang duoc Git track khong."""
    print("\n" + "=" * 60)
    print("[2] KIEM TRA GIT TRACKING")
    print("=" * 60)
    
    success, output = run_command("git ls-files | findstr token")
    
    if success and "token.json" in output:
        print("[DANGER] token.json DANG DUOC TRACK boi Git!")
        print(f"   Files: {output}")
        return True
    else:
        print("[OK] token.json KHONG duoc track boi Git")
        return False

def check_git_history():
    """Kiem tra token.json co trong Git history khong."""
    print("\n" + "=" * 60)
    print("[3] KIEM TRA GIT HISTORY")
    print("=" * 60)
    
    success, output = run_command("git log --all --full-history -- token.json")
    
    if success and output:
        print("[DANGER] token.json CO TRONG GIT HISTORY!")
        print("   Token da tung duoc commit truoc day!")
        return True
    else:
        print("[OK] token.json KHONG co trong Git history")
        return False

def check_gitignore():
    """Kiem tra .gitignore co ignore token.json khong."""
    print("\n" + "=" * 60)
    print("[4] KIEM TRA .GITIGNORE")
    print("=" * 60)
    
    if not os.path.exists(".gitignore"):
        print("[WARNING] File .gitignore KHONG ton tai!")
        return False
    
    with open(".gitignore", "r", encoding="utf-8") as f:
        content = f.read()
    
    has_token = "token.json" in content
    has_wildcard = "*.json" in content
    
    if has_token or has_wildcard:
        print("[OK] .gitignore DA BAO VE token.json")
        if has_token:
            print("   - Co 'token.json'")
        if has_wildcard:
            print("   - Co '*.json'")
        return True
    else:
        print("[WARNING] .gitignore CHUA BAO VE token.json")
        print("   Can them 'token.json' hoac '*.json' vao .gitignore")
        return False

def check_remote():
    """Kiem tra token.json co tren remote repository khong."""
    print("\n" + "=" * 60)
    print("[5] KIEM TRA REMOTE REPOSITORY")
    print("=" * 60)
    
    # Kiem tra remote co ton tai khong
    success, output = run_command("git remote -v")
    if not success or not output:
        print("[INFO] Khong co remote repository")
        return False
    
    print(f"Remote: {output.split()[1] if output else 'N/A'}")
    
    # Kiem tra file tren remote
    success, output = run_command("git ls-tree -r origin/main --name-only")
    
    if success and "token.json" in output:
        print("[DANGER] token.json CO TREN REMOTE REPOSITORY!")
        print("   Token da bi CONG KHAI tren GitHub/GitLab!")
        return True
    else:
        print("[OK] token.json KHONG co tren remote")
        return False

def main():
    """Ham chinh."""
    print("\n" + "=" * 60)
    print("   KIEM TRA BAO MAT TOKEN.JSON")
    print("=" * 60)
    
    issues = []
    
    # Chay cac kiem tra
    if check_local_file():
        issues.append("File token.json ton tai local")
    
    if check_git_tracked():
        issues.append("token.json dang duoc Git track")
    
    if check_git_history():
        issues.append("token.json co trong Git history")
    
    if not check_gitignore():
        issues.append(".gitignore chua bao ve token.json")
    
    if check_remote():
        issues.append("token.json co tren remote repository")
    
    # Ket luan
    print("\n" + "=" * 60)
    print("KET LUAN")
    print("=" * 60)
    
    if not issues:
        print("\n[SUCCESS] TAT CA DEU AN TOAN!")
        print("\nToken.json:")
        print("  - Khong bi track boi Git")
        print("  - Khong co trong history")
        print("  - Khong co tren remote")
        print("  - Da duoc bao ve boi .gitignore")
        print("\n=> BAN CO THE YEN TAM!")
        
    else:
        print("\n[WARNING] PHAT HIEN VAN DE BAO MAT!")
        print("\nCac van de:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        
        print("\n" + "=" * 60)
        print("HANH DONG CAN THUC HIEN")
        print("=" * 60)
        
        if "token.json dang duoc Git track" in issues:
            print("\n1. XOA KHOI GIT TRACKING:")
            print("   git rm --cached token.json")
            print("   git commit -m 'Remove token.json from tracking'")
        
        if ".gitignore chua bao ve token.json" in issues:
            print("\n2. CAP NHAT .GITIGNORE:")
            print("   echo token.json >> .gitignore")
            print("   git add .gitignore")
            print("   git commit -m 'Add token.json to gitignore'")
        
        if "token.json co trong Git history" in issues or \
           "token.json co tren remote repository" in issues:
            print("\n3. KHAN CAP - TOKEN DA BI LO:")
            print("   a. Revoke token ngay:")
            print("      - Truy cap: https://myaccount.google.com/permissions")
            print("      - Xoa quyen truy cap cua app")
            print("   b. Xoa khoi Git history:")
            print("      - Xem file HUONG_DAN_XU_LY_TOKEN_GIT.md")
            print("   c. Tao token moi")
        
        print("\n" + "=" * 60)
        print("CHI TIET: Xem file HUONG_DAN_XU_LY_TOKEN_GIT.md")
        print("=" * 60)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
