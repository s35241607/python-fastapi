#!/usr/bin/env python3
"""
Load Test Report Generator
Analyzes load test results and generates comprehensive performance reports
"""

import os
import sys
import csv
import json
import glob
from datetime import datetime
from typing import Dict, List, Any
import statistics
import argparse


class LoadTestAnalyzer:
    """Analyzes load test results and generates reports"""
    
    def __init__(self, results_dir: str, timestamp: str):
        self.results_dir = results_dir
        self.timestamp = timestamp
        self.scenarios = {}
        
    def analyze_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """Analyze a single test scenario"""
        csv_file = os.path.join(self.results_dir, f"{scenario_name}_{self.timestamp}_stats.csv")
        
        if not os.path.exists(csv_file):
            return {"error": f"Results file not found: {csv_file}"}
        
        analysis = {
            "scenario": scenario_name,
            "timestamp": self.timestamp,
            "metrics": {},
            "endpoints": [],
            "performance_grade": "N/A"
        }
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if not rows:
                return {"error": "No data in results file"}
            
            # Analyze overall performance
            total_requests = sum(int(row.get('Request Count', 0)) for row in rows)
            total_failures = sum(int(row.get('Failure Count', 0)) for row in rows)
            
            # Calculate weighted averages
            response_times = []
            rps_values = []
            
            for row in rows:
                request_count = int(row.get('Request Count', 0))
                if request_count > 0:
                    avg_response = float(row.get('Average Response Time', 0))
                    rps = float(row.get('Requests/s', 0))
                    
                    # Weight by request count
                    response_times.extend([avg_response] * request_count)
                    rps_values.append(rps)
                    
                    # Store endpoint data
                    analysis["endpoints"].append({
                        "name": row.get('Name', 'Unknown'),
                        "method": row.get('Method', 'Unknown'),
                        "request_count": request_count,
                        "failure_count": int(row.get('Failure Count', 0)),
                        "avg_response_time": avg_response,
                        "min_response_time": float(row.get('Min Response Time', 0)),
                        "max_response_time": float(row.get('Max Response Time', 0)),
                        "rps": rps,
                        "failure_rate": (int(row.get('Failure Count', 0)) / request_count * 100) if request_count > 0 else 0
                    })
            
            # Calculate overall metrics
            analysis["metrics"] = {
                "total_requests": total_requests,
                "total_failures": total_failures,
                "failure_rate": (total_failures / total_requests * 100) if total_requests > 0 else 0,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "median_response_time": statistics.median(response_times) if response_times else 0,
                "p95_response_time": self.percentile(response_times, 95) if response_times else 0,
                "p99_response_time": self.percentile(response_times, 99) if response_times else 0,
                "total_rps": sum(rps_values),
                "max_rps": max(rps_values) if rps_values else 0
            }
            
            # Performance grading
            analysis["performance_grade"] = self.grade_performance(analysis["metrics"])
            
        except Exception as e:
            analysis["error"] = f"Analysis failed: {str(e)}"
        
        return analysis
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def grade_performance(self, metrics: Dict[str, float]) -> str:
        """Grade overall performance based on enterprise requirements"""
        score = 0
        
        # Response time scoring (40% of grade)
        avg_response = metrics.get("avg_response_time", 0)
        if avg_response <= 500:  # Excellent
            score += 40
        elif avg_response <= 1000:  # Good
            score += 32
        elif avg_response <= 2000:  # Acceptable
            score += 24
        elif avg_response <= 5000:  # Poor
            score += 16
        else:  # Failing
            score += 0
        
        # Throughput scoring (30% of grade)
        total_rps = metrics.get("total_rps", 0)
        if total_rps >= 200:  # Excellent
            score += 30
        elif total_rps >= 150:  # Good
            score += 24
        elif total_rps >= 100:  # Acceptable
            score += 18
        elif total_rps >= 50:  # Poor
            score += 12
        else:  # Failing
            score += 0
        
        # Reliability scoring (30% of grade)
        failure_rate = metrics.get("failure_rate", 0)
        if failure_rate <= 0.1:  # Excellent
            score += 30
        elif failure_rate <= 0.5:  # Good
            score += 24
        elif failure_rate <= 1.0:  # Acceptable
            score += 18
        elif failure_rate <= 5.0:  # Poor
            score += 12
        else:  # Failing
            score += 0
        
        # Convert to letter grade
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Acceptable)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "F (Failing)"
    
    def analyze_all_scenarios(self) -> Dict[str, Any]:
        """Analyze all test scenarios"""
        scenarios = [
            "enterprise_normal",
            "enterprise_peak", 
            "enterprise_stress",
            "enterprise_spike",
            "enterprise_endurance"
        ]
        
        results = {
            "timestamp": self.timestamp,
            "scenarios": {},
            "summary": {},
            "recommendations": []
        }
        
        for scenario in scenarios:
            analysis = self.analyze_scenario(scenario)
            if "error" not in analysis:
                results["scenarios"][scenario] = analysis
        
        # Generate summary
        if results["scenarios"]:
            results["summary"] = self.generate_summary(results["scenarios"])
            results["recommendations"] = self.generate_recommendations(results["scenarios"])
        
        return results
    
    def generate_summary(self, scenarios: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall summary of all scenarios"""
        summary = {
            "total_requests": 0,
            "total_failures": 0,
            "overall_failure_rate": 0,
            "best_performance": None,
            "worst_performance": None,
            "enterprise_readiness": "Unknown"
        }
        
        best_score = 0
        worst_score = 100
        
        for scenario_name, scenario_data in scenarios.items():
            metrics = scenario_data.get("metrics", {})
            
            summary["total_requests"] += metrics.get("total_requests", 0)
            summary["total_failures"] += metrics.get("total_failures", 0)
            
            # Track best and worst performing scenarios
            grade = scenario_data.get("performance_grade", "F (Failing)")
            score = self.extract_score_from_grade(grade)
            
            if score > best_score:
                best_score = score
                summary["best_performance"] = {
                    "scenario": scenario_name,
                    "grade": grade,
                    "rps": metrics.get("total_rps", 0),
                    "avg_response_time": metrics.get("avg_response_time", 0)
                }
            
            if score < worst_score:
                worst_score = score
                summary["worst_performance"] = {
                    "scenario": scenario_name,
                    "grade": grade,
                    "rps": metrics.get("total_rps", 0),
                    "avg_response_time": metrics.get("avg_response_time", 0)
                }
        
        # Calculate overall failure rate
        if summary["total_requests"] > 0:
            summary["overall_failure_rate"] = (summary["total_failures"] / summary["total_requests"]) * 100
        
        # Determine enterprise readiness
        if best_score >= 80 and summary["overall_failure_rate"] <= 1.0:
            summary["enterprise_readiness"] = "Ready for Production"
        elif best_score >= 70:
            summary["enterprise_readiness"] = "Needs Optimization"
        else:
            summary["enterprise_readiness"] = "Not Ready - Requires Major Improvements"
        
        return summary
    
    def extract_score_from_grade(self, grade: str) -> int:
        """Extract numeric score from letter grade"""
        if "A" in grade:
            return 90
        elif "B" in grade:
            return 80
        elif "C" in grade:
            return 70
        elif "D" in grade:
            return 60
        else:
            return 50
    
    def generate_recommendations(self, scenarios: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        # Analyze patterns across scenarios
        high_response_times = []
        high_failure_rates = []
        low_throughput = []
        
        for scenario_name, scenario_data in scenarios.items():
            metrics = scenario_data.get("metrics", {})
            
            if metrics.get("avg_response_time", 0) > 2000:
                high_response_times.append(scenario_name)
            
            if metrics.get("failure_rate", 0) > 1.0:
                high_failure_rates.append(scenario_name)
            
            if metrics.get("total_rps", 0) < 100:
                low_throughput.append(scenario_name)
        
        # Generate specific recommendations
        if high_response_times:
            recommendations.append(
                f"⚠️  High response times detected in: {', '.join(high_response_times)}. "
                "Consider: database query optimization, caching implementation, "
                "connection pooling tuning, or horizontal scaling."
            )
        
        if high_failure_rates:
            recommendations.append(
                f"🔴 High failure rates in: {', '.join(high_failure_rates)}. "
                "Review: error handling, timeout configurations, resource limits, "
                "and system stability under load."
            )
        
        if low_throughput:
            recommendations.append(
                f"📉 Low throughput in: {', '.join(low_throughput)}. "
                "Optimize: async operations, database connections, "
                "worker processes, and remove bottlenecks."
            )
        
        # General enterprise recommendations
        recommendations.extend([
            "✅ Implement comprehensive monitoring and alerting for production",
            "✅ Set up auto-scaling policies based on load testing thresholds", 
            "✅ Regular load testing should be integrated into CI/CD pipeline",
            "✅ Consider implementing circuit breakers for external dependencies"
        ])
        
        return recommendations
    
    def generate_html_report(self, analysis: Dict[str, Any]) -> str:
        """Generate comprehensive HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enterprise Load Test Report - {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ background: #e7f3ff; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        .scenario {{ margin-bottom: 30px; border: 1px solid #ddd; border-radius: 8px; padding: 20px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
        .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .grade-A {{ color: #28a745; }}
        .grade-B {{ color: #17a2b8; }}
        .grade-C {{ color: #ffc107; }}
        .grade-D {{ color: #fd7e14; }}
        .grade-F {{ color: #dc3545; }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; }}
        .ready {{ color: #28a745; font-weight: bold; }}
        .needs-work {{ color: #ffc107; font-weight: bold; }}
        .not-ready {{ color: #dc3545; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Enterprise Load Test Report</h1>
            <h2>Ticket Management System Performance Analysis</h2>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Test Run: {self.timestamp}</p>
        </div>
        
        <div class="summary">
            <h2>📊 Executive Summary</h2>
        """
        
        summary = analysis.get("summary", {})
        readiness = summary.get("enterprise_readiness", "Unknown")
        readiness_class = "ready" if "Ready" in readiness else ("needs-work" if "Optimization" in readiness else "not-ready")
        
        html += f"""
            <p><strong>Enterprise Readiness:</strong> <span class="{readiness_class}">{readiness}</span></p>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{summary.get('total_requests', 0):,}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary.get('overall_failure_rate', 0):.2f}%</div>
                    <div class="metric-label">Overall Failure Rate</div>
                </div>
        """
        
        if summary.get("best_performance"):
            best = summary["best_performance"]
            html += f"""
                <div class="metric">
                    <div class="metric-value">{best['scenario'].replace('_', ' ').title()}</div>
                    <div class="metric-label">Best Performing Scenario</div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        # Scenario details
        for scenario_name, scenario_data in analysis.get("scenarios", {}).items():
            metrics = scenario_data.get("metrics", {})
            grade = scenario_data.get("performance_grade", "N/A")
            grade_class = f"grade-{grade[0]}" if grade != "N/A" else ""
            
            html += f"""
        <div class="scenario">
            <h3>📈 {scenario_name.replace('_', ' ').title()} Test</h3>
            <p><strong>Performance Grade:</strong> <span class="{grade_class}">{grade}</span></p>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{metrics.get('total_requests', 0):,}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics.get('avg_response_time', 0):.0f}ms</div>
                    <div class="metric-label">Avg Response Time</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics.get('total_rps', 0):.1f}</div>
                    <div class="metric-label">Requests/Second</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{metrics.get('failure_rate', 0):.2f}%</div>
                    <div class="metric-label">Failure Rate</div>
                </div>
            </div>
            
            <h4>Endpoint Performance</h4>
            <table>
                <thead>
                    <tr>
                        <th>Endpoint</th>
                        <th>Requests</th>
                        <th>Avg Response (ms)</th>
                        <th>RPS</th>
                        <th>Failure Rate</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for endpoint in scenario_data.get("endpoints", []):
                html += f"""
                    <tr>
                        <td>{endpoint.get('name', 'Unknown')}</td>
                        <td>{endpoint.get('request_count', 0):,}</td>
                        <td>{endpoint.get('avg_response_time', 0):.0f}</td>
                        <td>{endpoint.get('rps', 0):.1f}</td>
                        <td>{endpoint.get('failure_rate', 0):.2f}%</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
        </div>
            """
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            html += """
        <div class="recommendations">
            <h2>💡 Performance Recommendations</h2>
            <ul>
            """
            
            for rec in recommendations:
                html += f"<li>{rec}</li>"
            
            html += """
            </ul>
        </div>
            """
        
        html += """
    </div>
</body>
</html>
        """
        
        return html
    
    def save_json_report(self, analysis: Dict[str, Any]) -> str:
        """Save analysis as JSON for programmatic access"""
        filename = os.path.join(self.results_dir, f"load_test_analysis_{self.timestamp}.json")
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return filename
    
    def save_html_report(self, analysis: Dict[str, Any]) -> str:
        """Save comprehensive HTML report"""
        filename = os.path.join(self.results_dir, f"load_test_report_{self.timestamp}.html")
        
        html_content = self.generate_html_report(analysis)
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename


def main():
    parser = argparse.ArgumentParser(description='Generate load test performance reports')
    parser.add_argument('results_dir', help='Directory containing load test results')
    parser.add_argument('timestamp', help='Timestamp of the test run')
    
    args = parser.parse_args()
    
    analyzer = LoadTestAnalyzer(args.results_dir, args.timestamp)
    analysis = analyzer.analyze_all_scenarios()
    
    # Save reports
    json_file = analyzer.save_json_report(analysis)
    html_file = analyzer.save_html_report(analysis)
    
    print(f"\n=== Load Test Analysis Complete ===")
    print(f"JSON Report: {json_file}")
    print(f"HTML Report: {html_file}")
    
    # Print summary to console
    summary = analysis.get("summary", {})
    print(f"\nEnterprise Readiness: {summary.get('enterprise_readiness', 'Unknown')}")
    print(f"Total Requests Processed: {summary.get('total_requests', 0):,}")
    print(f"Overall Failure Rate: {summary.get('overall_failure_rate', 0):.2f}%")
    
    if summary.get("best_performance"):
        best = summary["best_performance"]
        print(f"Best Performance: {best['scenario']} ({best['grade']})")
    
    print(f"\nDetailed analysis available in: {html_file}")


if __name__ == "__main__":
    main()