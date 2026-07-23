import os

def check():
    failures = False
    for p in ['engine', 'editor']:
        for r, _, files in os.walk(p):
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(r, f)
                    with open(path, 'r', encoding='utf-8') as file:
                        lines = file.readlines()
                        if len(lines) > 500:
                            print(f"{path}: {len(lines)} lines")
                            failures = True
    if not failures:
        print("All files are under 500 lines.")

if __name__ == "__main__":
    check()
