"""
Interactive Command-Line Interface (CLI) for Kisan Mitra AI.
Allows direct terminal querying in Hindi, English, Punjabi, Marathi, etc.
Usage:
    python3 cli.py
"""
import sys
from agent import FarmerAdvisoryAssistant
from models.indictrans2 import INDIC_LANGUAGE_MAP

def print_banner():
    print("=" * 75)
    print("🌾 KISAN MITRA AI (AI Farmer Advisory Assistant)")
    print("CS3235 Undergraduate Multimodal AI Project")
    print("Models: BharatGen AgriParam • AI4Bharat IndicTrans2 • ICAR RAG")
    print("=" * 75)

def main():
    print_banner()
    assistant = FarmerAdvisoryAssistant()

    print("\nSelect your working language:")
    langs = list(INDIC_LANGUAGE_MAP.items())
    for idx, (code, info) in enumerate(langs, 1):
        print(f"  [{idx}] {info['name']} ({code})")

    try:
        choice = input("\nEnter language number [Default 1 for Hindi]: ").strip()
        choice_idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(langs) else 0
    except (ValueError, EOFError):
        choice_idx = 0

    selected_code = langs[choice_idx][0]
    selected_name = langs[choice_idx][1]["name"]
    print(f"\n✅ Active Language set to: {selected_name} ({selected_code})")
    print("Type your questions below. Enter 'exit' or 'quit' to finish.\n")

    while True:
        try:
            query = input(f"\nFarmer [{selected_name}] > ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("धन्यवाद! Goodbye!")
                break

            response = assistant.process_query(query, user_language=selected_code)

            print("\n" + "-" * 60)
            print("🌾 Kisan Mitra Advisory:")
            print(response["answer"])

            if response.get("citations"):
                print("\n📚 Official ICAR/KVK Sources:")
                for c in response["citations"]:
                    print(f"  • Doc {c['doc_num']}: {c['title']} ({c['crop']}) — {c['source']}")

            g = response.get("groundedness", {})
            print(f"\n[Metrics] Latency: {response['latency_ms']} ms | Groundedness: {g.get('groundedness_score', 1.0)*100:.1f}%")
            if response.get("tool_used"):
                print(f"[Agentic Tool Triggered]: {response['tool_used']}")
            print("-" * 60)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

if __name__ == "__main__":
    main()
