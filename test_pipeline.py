import time
from athena.pipeline import AthenaVerificationPipeline

def run_tests():
    print("Initializing Athena Pipeline...")
    t0 = time.time()
    pipeline = AthenaVerificationPipeline()
    print(f"Pipeline ready in {time.time() - t0:.2f}s")
    
    test_cases = [
        {"title": "A &S INDIA", "language": "English", "state": "Maharashtra", "periodicity": "Monthly"},
        {"title": "Dainik Aachran", "language": "Hindi", "state": "Madhya Pradesh", "periodicity": "Daily"},
        {"title": "Daily Aachran", "language": "Hindi", "state": "Madhya Pradesh", "periodicity": "Daily"},
        {"title": "Police Crime Branch Times", "language": "English", "state": "Delhi", "periodicity": "Weekly"},
        {"title": "Quantum Antigravity Horizons Gazette", "language": "English", "state": "Karnataka", "periodicity": "Monthly"},
    ]
    
    for tc in test_cases:
        t = tc["title"]
        print(f"\nTesting: '{t}'...")
        res = pipeline.verify_title(
            proposed_title=t,
            language=tc["language"],
            periodicity=tc["periodicity"],
            state=tc["state"]
        )
        print(f"  Status: {res['status']} | Approval Prob: {res['acceptance_probability']}% | Latency: {res['total_latency_ms']}ms")
        print(f"  Highest Similarity: {res['highest_similarity']*100:.1f}%")
        if res["compliance"]["violations"]:
            print(f"  Violations: {[v['rule'] for v in res['compliance']['violations']]}")
        if res["top_candidates"]:
            print(f"  Top Match: '{res['top_candidates'][0]['matched_title']}' (Score: {res['top_candidates'][0]['final_similarity_score']*100:.1f}%)")
        print(f"  Recommendations: {res['recommendations'][:2]}")

if __name__ == "__main__":
    run_tests()
