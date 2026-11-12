import os
import zipfile

def build_zip():
    dest_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'frontend', 'public', 'courses', 'linux')
    os.makedirs(dest_dir, exist_ok=True)
    zip_path = os.path.join(dest_dir, 'linux-companion-files.zip')

    files = {
        'students.txt': """A101|Ravi Kumar|civil|Pune|pass|8000
A102|Sana Shaikh|computers|Indore|pass|9500
A103|Arun Das|mechanical|Kolkata|fail|0
A104|Meera Nair|civil|Kochi|pass|7000
A105|Tarun Rao|computers|Hyderabad|pass|9000
A106|Deepa Patel|electrical|Ahmedabad|pass|8500
A107|John Joseph|computers|Chennai|pass|9500
A108|Neha Sharma|mechanical|Jaipur|pass|8000
A109|Pooja Verma|civil|Bhopal|fail|0
A110|Kiran Desai|electrical|Surat|pass|7500
""",
        'numbers.txt': """42
17
89
5
12
100
23
5
42
7
""",
        'marks.txt': """RollNo Marks Grade
A101 85 A
A102 92 A+
A103 45 C
A104 78 B+
A105 88 A
A106 82 A
A107 94 A+
A108 76 B
A109 40 C
A110 74 B
""",
        'grepdemo.txt': """A101|Ravi Kumar|civil|Pune|pass|8000
A102|Sana Shaikh|computers|Indore|pass|9500
A103|Arun Das|mechanical|Kolkata|fail|0
A104|Meera Nair|civil|Kochi|pass|7000
A105|Tarun Rao|computers|Hyderabad|pass|9000
A106|Deepa Patel|electrical|Ahmedabad|pass|8500
A107|John Joseph|computers|Chennai|pass|9500
A108|Neha Sharma|mechanical|Jaipur|pass|8000
A109|Pooja Verma|civil|Bhopal|fail|0
A110|Kiran Desai|electrical|Surat|pass|7500
""",
        'seddemo.txt': """Linux is an open-source operating system.
It is widely used in servers, desktops, and embedded systems.
The Linux kernel was created by Linus Torvalds.
This student passed the examination with flying colours.
This student failed the examination and needs to re-attempt.
Many developers love using Linux for development work.
Linux provides powerful command-line utilities.
civil engineering students also learn Linux tools.
The stream editor sed allows powerful stream processing.
sed reads input line by line and applies editing commands.
""",
        'README.md': """# Linux Course Companion Code Files
Spoken Tutorial & SWAYAM Plus - Linux Course

This package contains sample datasets for hands-on practice:
- `numbers.txt`: Used in Tutorial 16 (Simple Filters) for numeric sorting and unique filtering (`sort -n`, `sort -u`).
- `marks.txt`: Used in Tutorial 16 for `head`, `tail`, `cut`, and `paste` commands.
- `grepdemo.txt`: Used in Tutorials 17 and 18 for string searching, regex matching, and case-insensitive filtering with `grep`.
- `seddemo.txt`: Used in Tutorials 19 and 20 for line selection, pattern addressing, and text replacement with `sed`.
- `students.txt`: Pipe-delimited student records used in Module 5 demonstrations, labs, and capstone project preparation.
"""
    }

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for filename, content in files.items():
            z.writestr(filename, content)

    print(f"✓ Created {zip_path} ({os.path.getsize(zip_path)} bytes)")

if __name__ == '__main__':
    build_zip()
