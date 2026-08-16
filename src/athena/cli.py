import sys
import argparse
from athena.pipeline import AthenaVerificationPipeline

def main():
    parser = argparse.ArgumentParser(description="Athena PRGI AI Title Verification CLI")
    parser.add_argument("title", nargs="?", help="Proposed publication title to verify")
    parser.add_argument("--language", default="", help="Publication language")
    parser.add_argument("--periodicity", default="", help="Periodicity (Daily, Weekly, etc.)")
    parser.add_argument("--state", default="", help="Publication state")
    parser.add_argument("--ui", action="store_true", help="Launch Streamlit web application")

    args = parser.parse_args()

    if args.ui or not args.title:
        import subprocess
        print("Launching Athena Streamlit UI...")
        subprocess.run(["streamlit", "run", "src/athena/app.py"])
        return

    pipeline = AthenaVerificationPipeline()
    res = pipeline.verify_title(
        proposed_title=args.title,
        language=args.language,
        periodicity=args.periodicity,
        state=args.state
    )

    print("\n" + "="*60)
    print(f"ATHENA TITLE VERIFICATION REPORT: '{args.title}'")
    print("="*60)
    print(f"Decision Status:       {res['status']}")
    print(f"Approval Probability:  {res['acceptance_probability']}%")
    print(f"Rejection Probability: {res['rejection_probability']}%")
    print(f"Highest Similarity:    {res['highest_similarity']*100:.1f}%")
    print(f"Total Latency:         {res['total_latency_ms']} ms")
    print(f"Description:           {res['status_desc']}")
    
    if res["compliance"]["violations"]:
        print("\n[Violations Detected]:")
        for v in res["compliance"]["violations"]:
            print(f"  - [{v['severity']}] {v['rule']}: {v['detail']}")

    if res["top_candidates"]:
        print("\n[Top Matching Registered Titles]:")
        for c in res["top_candidates"][:5]:
            print(f"  - SN {c['sn']}: '{c['matched_title']}' ({c.get('language','')}, {c.get('state','')}) -> Score: {c['final_similarity_score']*100:.1f}%")

    if res["recommendations"]:
        print("\n[Actionable Recommendations]:")
        for r in res["recommendations"]:
            print(f"  - {r}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
