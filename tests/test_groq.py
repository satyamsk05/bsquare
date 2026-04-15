import sys
sys.path.insert(0, ".")
from app.core.content_writer import generate_content

print("-" * 50)
print("GROQ & FALLBACK TEST")
print("-" * 50)

try:
    print("Trying to generate content...")
    result = generate_content("Say 'Groq is fast' in exactly 3 words.")
    print(f"\nFinal Result: {result}")
except Exception as e:
    print(f"\nTest failed: {e}")

print("-" * 50)
