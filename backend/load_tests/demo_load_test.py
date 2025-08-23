#!/usr/bin/env python3
"""
Simple Load Test Demo
Quick verification that the load testing framework works
"""

import os
import sys
import time
import subprocess
import json
from datetime import datetime

def run_demo_load_test():
    """Run a quick demo load test to verify functionality"""
    
    print("🚀 Enterprise Load Testing Demo")
    print("=" * 50)
    print("Running quick verification test...")
    print("")
    
    # Configuration
    host = "http://localhost:8000"
    results_dir = "./demo_results"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create results directory
    os.makedirs(results_dir, exist_ok=True)
    
    print(f"Target Host: {host}")
    print(f"Results Directory: {results_dir}")
    print(f"Timestamp: {timestamp}")
    print("")
    
    # Demo test parameters
    demo_scenarios = [
        {
            "name": "quick_verification",
            "description": "Quick verification test - 10 users for 30 seconds",
            "users": 10,
            "spawn_rate": 2,
            "duration": 30
        },
        {
            "name": "mini_load",
            "description": "Mini load test - 50 users for 60 seconds", 
            "users": 50,
            "spawn_rate": 5,
            "duration": 60
        }
    ]
    
    results = {}
    
    for scenario in demo_scenarios:
        print(f"📊 Running {scenario['name']}...")
        print(f"   {scenario['description']}")
        print(f"   Users: {scenario['users']}, Duration: {scenario['duration']}s")
        
        # Build locust command
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", host,
            "--users", str(scenario['users']),
            "--spawn-rate", str(scenario['spawn_rate']),
            "--run-time", f"{scenario['duration']}s",
            "--headless",
            "--csv", f"{results_dir}/{scenario['name']}_{timestamp}",
            "--html", f"{results_dir}/{scenario['name']}_{timestamp}.html",
            "--loglevel", "INFO"
        ]
        
        start_time = time.time()
        
        try:
            # Run the load test
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=scenario['duration'] + 60)
            
            elapsed_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"   ✅ Completed in {elapsed_time:.1f}s")
                
                # Try to read basic stats
                stats_file = f"{results_dir}/{scenario['name']}_{timestamp}_stats.csv"
                if os.path.exists(stats_file):
                    with open(stats_file, 'r') as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            # Parse basic stats from first data line
                            headers = lines[0].strip().split(',')
                            data = lines[1].strip().split(',')
                            stats_dict = dict(zip(headers, data))
                            
                            total_requests = stats_dict.get('Request Count', '0')
                            avg_response = stats_dict.get('Average Response Time', '0')
                            rps = stats_dict.get('Requests/s', '0')
                            
                            print(f"   📈 Total Requests: {total_requests}")
                            print(f"   ⏱️  Avg Response: {avg_response}ms")
                            print(f"   🔥 Requests/sec: {rps}")
                            
                            results[scenario['name']] = {
                                "status": "success",
                                "total_requests": total_requests,
                                "avg_response_time": avg_response,
                                "requests_per_second": rps,
                                "duration": elapsed_time
                            }
                        else:
                            print(f"   ⚠️  No performance data collected")
                            results[scenario['name']] = {"status": "no_data"}
                else:
                    print(f"   ⚠️  Stats file not found: {stats_file}")
                    results[scenario['name']] = {"status": "no_stats_file"}
                    
            else:
                print(f"   ❌ Failed (exit code: {result.returncode})")
                print(f"   Error: {result.stderr}")
                results[scenario['name']] = {
                    "status": "failed",
                    "error": result.stderr,
                    "exit_code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            print(f"   ⏰ Timeout after {scenario['duration'] + 60}s")
            results[scenario['name']] = {"status": "timeout"}
            
        except FileNotFoundError:
            print(f"   ❌ Locust not found. Please install: pip install locust")
            results[scenario['name']] = {"status": "locust_not_found"}
            return False
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results[scenario['name']] = {"status": "error", "error": str(e)}
        
        print("")
    
    # Save demo results
    demo_results = {
        "timestamp": timestamp,
        "scenarios": results,
        "summary": generate_demo_summary(results)
    }
    
    results_file = f"{results_dir}/demo_results_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(demo_results, f, indent=2)
    
    print("📋 Demo Summary")
    print("=" * 30)
    
    successful_tests = sum(1 for r in results.values() if r.get("status") == "success")
    total_tests = len(results)
    
    print(f"Tests Completed: {successful_tests}/{total_tests}")
    
    if successful_tests > 0:
        print("✅ Load testing framework is working!")
        print("")
        print("🎯 Next Steps:")
        print("1. Start your FastAPI server: uvicorn app.main:app --reload")
        print("2. Run full test suite: ./run_load_tests.bat (Windows) or ./run_load_tests.sh (Linux/Mac)")
        print("3. Review HTML reports in the results directory")
        print("")
        print("📊 Enterprise Testing:")
        print("- The full suite will test 1000+ concurrent users")
        print("- Multiple scenarios: normal, peak, stress, spike, endurance")
        print("- Comprehensive performance analysis and recommendations")
    else:
        print("❌ Load testing framework needs setup")
        print("")
        print("🔧 Troubleshooting:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Ensure FastAPI server is running on http://localhost:8000")
        print("3. Check firewall and network connectivity")
    
    print(f"\nDetailed results saved to: {results_file}")
    
    return successful_tests > 0

def generate_demo_summary(results):
    """Generate summary of demo results"""
    summary = {
        "total_scenarios": len(results),
        "successful": 0,
        "failed": 0,
        "framework_status": "unknown"
    }
    
    for scenario_name, result in results.items():
        if result.get("status") == "success":
            summary["successful"] += 1
        else:
            summary["failed"] += 1
    
    if summary["successful"] > 0:
        summary["framework_status"] = "working"
    elif any(r.get("status") == "locust_not_found" for r in results.values()):
        summary["framework_status"] = "missing_dependencies"
    else:
        summary["framework_status"] = "setup_required"
    
    return summary

if __name__ == "__main__":
    try:
        success = run_demo_load_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Demo cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        sys.exit(1)