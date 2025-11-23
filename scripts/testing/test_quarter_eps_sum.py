"""Test _get_quarter_eps_sum function to ensure refactoring doesn't change results."""

from datetime import datetime
import pandas as pd
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from factset_report_analyzer.analysis.sp500 import (
    _get_quarter_eps_sum,
    fetch_sp500_pe_ratio,
    _parse_quarter_to_date
)


def test_quarter_eps_sum_with_real_data():
    """Test _get_quarter_eps_sum with real CSV data."""
    from factset_report_analyzer.utils.csv_storage import read_csv
    import tempfile
    
    # Load real data
    temp_path = Path(tempfile.gettempdir()) / "extracted_estimates.csv"
    df_eps = read_csv("extracted_estimates.csv", temp_path)
    
    if df_eps is None:
        print("⚠️  Cannot load CSV data. Skipping real data test.")
        return
    
    df_eps['Report_Date'] = pd.to_datetime(df_eps['Report_Date'])
    quarter_cols = [col for col in df_eps.columns if col != 'Report_Date']
    
    print(f"📊 Testing with {len(df_eps)} rows and {len(quarter_cols)} quarter columns")
    print(f"   Date range: {df_eps['Report_Date'].min()} to {df_eps['Report_Date'].max()}")
    print()
    
    # Test cases: sample different rows and dates
    test_cases = []
    
    # Test first few rows
    for idx in range(min(5, len(df_eps))):
        row = df_eps.iloc[idx]
        report_date = row['Report_Date']
        test_cases.append({
            'row': row,
            'report_date': report_date,
            'description': f"Row {idx} (Report Date: {report_date.strftime('%Y-%m-%d')})"
        })
    
    # Test middle rows
    if len(df_eps) > 10:
        for idx in range(len(df_eps) // 2, min(len(df_eps) // 2 + 3, len(df_eps))):
            row = df_eps.iloc[idx]
            report_date = row['Report_Date']
            test_cases.append({
                'row': row,
                'report_date': report_date,
                'description': f"Row {idx} (Report Date: {report_date.strftime('%Y-%m-%d')})"
            })
    
    # Test last few rows
    if len(df_eps) > 5:
        for idx in range(max(0, len(df_eps) - 3), len(df_eps)):
            row = df_eps.iloc[idx]
            report_date = row['Report_Date']
            test_cases.append({
                'row': row,
                'report_date': report_date,
                'description': f"Row {idx} (Report Date: {report_date.strftime('%Y-%m-%d')})"
            })
    
    results = []
    
    for test_case in test_cases:
        row = test_case['row']
        report_date = test_case['report_date']
        desc = test_case['description']
        
        # Test forward
        forward_result = _get_quarter_eps_sum(row, quarter_cols, report_date, 'forward')
        
        # Test trailing
        trailing_result = _get_quarter_eps_sum(row, quarter_cols, report_date, 'trailing')
        
        # Also test with price_date (as used in actual code)
        # Add 30 days to report_date to simulate price_date
        price_date = report_date + pd.Timedelta(days=30)
        forward_price_result = _get_quarter_eps_sum(row, quarter_cols, price_date, 'forward')
        trailing_price_result = _get_quarter_eps_sum(row, quarter_cols, price_date, 'trailing')
        
        results.append({
            'description': desc,
            'report_date': report_date,
            'forward': forward_result,
            'trailing': trailing_result,
            'forward_price': forward_price_result,
            'trailing_price': trailing_price_result,
        })
        
        print(f"✅ {desc}")
        print(f"   Forward (report_date): {forward_result}")
        print(f"   Trailing (report_date): {trailing_result}")
        print(f"   Forward (price_date +30d): {forward_price_result}")
        print(f"   Trailing (price_date +30d): {trailing_price_result}")
        print()
    
    # Save results to file for comparison
    results_df = pd.DataFrame(results)
    output_path = Path(__file__).parent.parent.parent / "output" / "test_quarter_eps_sum_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"💾 Results saved to: {output_path}")
    
    return results


def create_mock_test_cases():
    """Create multiple mock test cases covering various scenarios."""
    test_cases = []
    
    # Case 1: Normal case - sufficient quarters for both forward and trailing
    test_cases.append({
        'name': 'Case 1: Normal - Q2\'16 with full history',
        'data': {
            'Report_Date': datetime(2016, 6, 15),  # Q2'16
            "Q1'14": "2.5",
            "Q2'14": "2.7",
            "Q3'14": "2.9*",  # with asterisk
            "Q4'14": "3.1",
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "3.6",
            "Q4'15": "3.8",
            "Q1'16": "4.0",
            "Q2'16": "4.2",
            "Q3'16": "4.4",
            "Q4'16": "4.6",
        },
        'report_date': datetime(2016, 6, 15),  # Q2'16
        'expected_forward': 4.2 + 4.4 + 4.6,  # Q2'16 + Q3'16 + Q4'16 (only 3, so None)
        'expected_trailing': 3.4 + 3.6 + 3.8 + 4.0,  # Q2'15 + Q3'15 + Q4'15 + Q1'16 = 14.8
    })
    
    # Case 2: Early quarter - Q1'15
    test_cases.append({
        'name': 'Case 2: Early quarter - Q1\'15',
        'data': {
            'Report_Date': datetime(2015, 3, 15),  # Q1'15
            "Q1'14": "2.5",
            "Q2'14": "2.7",
            "Q3'14": "2.9",
            "Q4'14": "3.1",
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "3.6",
            "Q4'15": "3.8",
        },
        'report_date': datetime(2015, 3, 15),  # Q1'15
        'expected_forward': 3.2 + 3.4 + 3.6 + 3.8,  # Q1'15 + Q2'15 + Q3'15 + Q4'15 = 14.0
        'expected_trailing': 2.5 + 2.7 + 2.9 + 3.1,  # Q1'14 + Q2'14 + Q3'14 + Q4'14 = 11.2
    })
    
    # Case 3: Forward with exactly 4 quarters available
    test_cases.append({
        'name': 'Case 3: Forward with exactly 4 quarters',
        'data': {
            'Report_Date': datetime(2015, 6, 15),  # Q2'15
            "Q2'15": "3.4",
            "Q3'15": "3.6",
            "Q4'15": "3.8",
            "Q1'16": "4.0",
        },
        'report_date': datetime(2015, 6, 15),  # Q2'15
        'expected_forward': 3.4 + 3.6 + 3.8 + 4.0,  # Q2'15 + Q3'15 + Q4'15 + Q1'16 = 14.8
        'expected_trailing': None,  # Not enough quarters before
    })
    
    # Case 4: Trailing with exactly 4 quarters available
    test_cases.append({
        'name': 'Case 4: Trailing with exactly 4 quarters',
        'data': {
            'Report_Date': datetime(2016, 3, 15),  # Q1'16
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "3.6",
            "Q4'15": "3.8",
            "Q1'16": "4.0",
        },
        'report_date': datetime(2016, 3, 15),  # Q1'16
        'expected_forward': None,  # Not enough quarters after
        'expected_trailing': 3.2 + 3.4 + 3.6 + 3.8,  # Q1'15 + Q2'15 + Q3'15 + Q4'15 = 14.0
    })
    
    # Case 5: Insufficient quarters for forward
    test_cases.append({
        'name': 'Case 5: Insufficient quarters for forward',
        'data': {
            'Report_Date': datetime(2016, 12, 15),  # Q4'16
            "Q4'16": "4.6",
        },
        'report_date': datetime(2016, 12, 15),  # Q4'16
        'expected_forward': None,  # Only 1 quarter available
        'expected_trailing': None,  # No quarters before
    })
    
    # Case 6: Insufficient quarters for trailing
    test_cases.append({
        'name': 'Case 6: Insufficient quarters for trailing',
        'data': {
            'Report_Date': datetime(2014, 3, 15),  # Q1'14
            "Q1'14": "2.5",
        },
        'report_date': datetime(2014, 3, 15),  # Q1'14
        'expected_forward': None,  # Not enough quarters after
        'expected_trailing': None,  # No quarters before
    })
    
    # Case 7: Report date in middle of quarter range
    test_cases.append({
        'name': 'Case 7: Report date in middle of quarter range',
        'data': {
            'Report_Date': datetime(2015, 5, 15),  # Between Q1'15 and Q2'15, should be Q2'15
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "3.6",
            "Q4'15": "3.8",
            "Q1'16": "4.0",
        },
        'report_date': datetime(2015, 5, 15),  # Should map to Q2'15
        'expected_forward': 3.4 + 3.6 + 3.8 + 4.0,  # Q2'15 + Q3'15 + Q4'15 + Q1'16 = 14.8
        'expected_trailing': None,  # Only 1 quarter before (Q1'15)
    })
    
    # Case 8: Report date at quarter boundary
    test_cases.append({
        'name': 'Case 8: Report date at quarter start',
        'data': {
            'Report_Date': datetime(2015, 7, 1),  # Q3'15 start
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "3.6",
            "Q4'15": "3.8",
            "Q1'16": "4.0",
        },
        'report_date': datetime(2015, 7, 1),  # Q3'15 start
        'expected_forward': 3.6 + 3.8 + 4.0,  # Q3'15 + Q4'15 + Q1'16 (only 3, so None)
        'expected_trailing': 3.2 + 3.4,  # Q1'15 + Q2'15 (only 2, so None)
    })
    
    # Case 9: With empty/None values (should be filtered)
    test_cases.append({
        'name': 'Case 9: With empty/None values',
        'data': {
            'Report_Date': datetime(2015, 6, 15),  # Q2'15
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "",  # Empty - should be filtered
            "Q4'15": None,  # None - should be filtered
            "Q1'16": "4.0",
            "Q2'16": "4.2",
            "Q3'16": "4.4",
        },
        'report_date': datetime(2015, 6, 15),  # Q2'15
        'expected_forward': None,  # Q2'15 + Q1'16 + Q2'16 + Q3'16 (only 4, but Q3'15/Q4'15 filtered)
        'expected_trailing': None,  # Only Q1'15 before (not enough)
    })
    
    # Case 10: With zero/negative values (should be filtered)
    test_cases.append({
        'name': 'Case 10: With zero/negative values',
        'data': {
            'Report_Date': datetime(2015, 6, 15),  # Q2'15
            "Q1'15": "3.2",
            "Q2'15": "3.4",
            "Q3'15": "0",  # Zero - should be filtered
            "Q4'15": "-1.0",  # Negative - should be filtered
            "Q1'16": "4.0",
            "Q2'16": "4.2",
            "Q3'16": "4.4",
        },
        'report_date': datetime(2015, 6, 15),  # Q2'15
        'expected_forward': None,  # Q3'15 and Q4'15 filtered, not enough quarters
        'expected_trailing': None,  # Only Q1'15 before
    })
    
    # Case 11: Report date after all quarters
    test_cases.append({
        'name': 'Case 11: Report date after all quarters',
        'data': {
            'Report_Date': datetime(2017, 6, 15),  # After Q4'16
            "Q1'16": "4.0",
            "Q2'16": "4.2",
            "Q3'16": "4.4",
            "Q4'16": "4.6",
        },
        'report_date': datetime(2017, 6, 15),  # After Q4'16
        'expected_forward': None,  # No quarters after report_date
        'expected_trailing': 4.0 + 4.2 + 4.4 + 4.6,  # All 4 quarters = 16.2
    })
    
    # Case 12: Report date before all quarters
    test_cases.append({
        'name': 'Case 12: Report date before all quarters',
        'data': {
            'Report_Date': datetime(2013, 6, 15),  # Before Q1'14
            "Q1'14": "2.5",
            "Q2'14": "2.7",
            "Q3'14": "2.9",
            "Q4'14": "3.1",
        },
        'report_date': datetime(2013, 6, 15),  # Before Q1'14
        'expected_forward': 2.5 + 2.7 + 2.9 + 3.1,  # All 4 quarters = 11.2
        'expected_trailing': None,  # No quarters before report_date
    })
    
    return test_cases


def test_quarter_eps_sum_with_mock_data():
    """Test _get_quarter_eps_sum with multiple mock data cases and save results."""
    print("🧪 Testing with multiple mock data cases")
    print()
    
    test_cases = create_mock_test_cases()
    results = []
    
    for case in test_cases:
        row = pd.Series(case['data'])
        quarter_cols = [col for col in case['data'].keys() if col != 'Report_Date']
        report_date = case['report_date']
        
        # Test forward
        forward_result = _get_quarter_eps_sum(row, quarter_cols, report_date, 'forward')
        
        # Test trailing
        trailing_result = _get_quarter_eps_sum(row, quarter_cols, report_date, 'trailing')
        
        # Compare with expected
        forward_match = (forward_result == case['expected_forward']) or (
            forward_result is None and case['expected_forward'] is None
        )
        trailing_match = (trailing_result == case['expected_trailing']) or (
            trailing_result is None and case['expected_trailing'] is None
        )
        
        result = {
            'name': case['name'],
            'data': {k: str(v) if isinstance(v, datetime) else v for k, v in case['data'].items()},
            'report_date': report_date.isoformat(),
            'forward_result': forward_result,
            'trailing_result': trailing_result,
            'expected_forward': case['expected_forward'],
            'expected_trailing': case['expected_trailing'],
            'forward_match': forward_match,
            'trailing_match': trailing_match,
        }
        results.append(result)
        
        status_forward = "✅" if forward_match else "❌"
        status_trailing = "✅" if trailing_match else "❌"
        
        print(f"{status_forward} {status_trailing} {case['name']}")
        print(f"   Forward: {forward_result} (expected: {case['expected_forward']})")
        print(f"   Trailing: {trailing_result} (expected: {case['expected_trailing']})")
        print()
    
    # Save results to JSON for comparison after refactoring
    import json
    output_path = Path(__file__).parent.parent.parent / "output" / "test_quarter_eps_sum_mock_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"💾 Results saved to: {output_path}")
    print()
    
    # Summary
    forward_matches = sum(1 for r in results if r['forward_match'])
    trailing_matches = sum(1 for r in results if r['trailing_match'])
    print(f"📊 Summary:")
    print(f"   Forward matches: {forward_matches}/{len(results)}")
    print(f"   Trailing matches: {trailing_matches}/{len(results)}")
    print()
    
    return results


def test_full_pipeline_comparison():
    """Test full fetch_sp500_pe_ratio to capture all results before refactoring."""
    print("🔄 Testing full pipeline (fetch_sp500_pe_ratio)")
    print("   This will take a while...")
    print()
    
    try:
        # Test forward
        df_forward = fetch_sp500_pe_ratio(type='forward')
        print(f"✅ Forward P/E: {len(df_forward)} rows")
        
        # Test trailing
        df_trailing = fetch_sp500_pe_ratio(type='trailing')
        print(f"✅ Trailing P/E: {len(df_trailing)} rows")
        
        # Save results
        output_dir = Path(__file__).parent.parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        forward_path = output_dir / "test_pe_ratio_forward_before_refactor.csv"
        trailing_path = output_dir / "test_pe_ratio_trailing_before_refactor.csv"
        
        df_forward.to_csv(forward_path, index=False)
        df_trailing.to_csv(trailing_path, index=False)
        
        print(f"💾 Forward results saved to: {forward_path}")
        print(f"💾 Trailing results saved to: {trailing_path}")
        print()
        
        # Show sample
        print("Sample Forward P/E (first 5 rows):")
        print(df_forward.head())
        print()
        print("Sample Trailing P/E (first 5 rows):")
        print(df_trailing.head())
        print()
        
        return {
            'forward': df_forward,
            'trailing': df_trailing
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_with_saved_results():
    """Compare current results with saved results from before refactoring."""
    import json
    
    saved_path = Path(__file__).parent.parent.parent / "output" / "test_quarter_eps_sum_mock_results.json"
    
    if not saved_path.exists():
        print("⚠️  No saved results found. Run test_quarter_eps_sum_with_mock_data() first.")
        return None
    
    # Load saved results
    with open(saved_path, 'r') as f:
        saved_results = json.load(f)
    
    print("🔄 Comparing current results with saved results...")
    print()
    
    test_cases = create_mock_test_cases()
    current_results = []
    all_match = True
    
    for i, case in enumerate(test_cases):
        row = pd.Series(case['data'])
        quarter_cols = [col for col in case['data'].keys() if col != 'Report_Date']
        report_date = case['report_date']
        
        # Test current implementation
        forward_result = _get_quarter_eps_sum(row, quarter_cols, report_date, 'forward')
        trailing_result = _get_quarter_eps_sum(row, quarter_cols, report_date, 'trailing')
        
        # Compare with saved
        saved = saved_results[i]
        forward_match = (
            (forward_result == saved['forward_result']) or
            (forward_result is None and saved['forward_result'] is None)
        )
        trailing_match = (
            (trailing_result == saved['trailing_result']) or
            (trailing_result is None and saved['trailing_result'] is None)
        )
        
        if not forward_match or not trailing_match:
            all_match = False
        
        status_forward = "✅" if forward_match else "❌"
        status_trailing = "✅" if trailing_match else "❌"
        
        print(f"{status_forward} {status_trailing} {case['name']}")
        if not forward_match:
            print(f"   Forward: {forward_result} != {saved['forward_result']} (saved)")
        if not trailing_match:
            print(f"   Trailing: {trailing_result} != {saved['trailing_result']} (saved)")
        print()
    
    print("=" * 80)
    if all_match:
        print("✅ All results match! Refactoring successful.")
    else:
        print("❌ Some results don't match! Review the differences above.")
    print("=" * 80)
    print()
    
    return all_match


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        # Compare mode: compare current results with saved results
        print("=" * 80)
        print("Compare current results with saved results")
        print("=" * 80)
        print()
        compare_with_saved_results()
    else:
        # Normal mode: run tests and save results
        print("=" * 80)
        print("Test _get_quarter_eps_sum function")
        print("=" * 80)
        print()
        
        # Test 1: Mock data (multiple cases)
        mock_results = test_quarter_eps_sum_with_mock_data()
        
        # Test 2: Real data (sample rows)
        real_results = test_quarter_eps_sum_with_real_data()
        
        # Test 3: Full pipeline (optional - takes time)
        print("Run full pipeline test? (y/n): ", end="")
        # For automated testing, skip this
        # full_results = test_full_pipeline_comparison()
        
        print()
        print("=" * 80)
        print("✅ Test completed!")
        print("=" * 80)
        print()
        print("📝 Next steps:")
        print("   1. Review the test results above")
        print("   2. Refactor _get_quarter_eps_sum function")
        print("   3. Re-run with --compare flag: python test_quarter_eps_sum.py --compare")
        print("   4. Use test_full_pipeline_comparison() to verify full pipeline")

