"""csv-quality script: thống kê fixture, tổng giờ theo owner, lỗi input/schema/parse exit 1, lỗi dữ liệu exit 0."""

import json
import subprocess
import sys

import pytest

import paths

SCRIPT = paths.FIXTURES_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"


def run(path, *extra, max_hours="8"):
    args = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        args += ["--max-hours", max_hours]
    return subprocess.run(args + list(extra), capture_output=True, text=True, timeout=10, encoding="utf-8")


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_fixture_statistics():
    result = run(paths.FIXTURES_DIR / "data" / "tasks.csv")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert data["hours_by_owner"] == {"An": 5, "Lan": 4, "Minh": 3}


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n")).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"))
    assert result.returncode == 0
    assert json.loads(result.stdout)["issues"] == []


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"))
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'))
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


def test_script_does_not_modify_input():
    source = paths.FIXTURES_DIR / "data" / "tasks.csv"
    before = source.read_bytes()
    run(source)
    assert source.read_bytes() == before



WORKLOAD = "task_id,owner,hours\nT01,Lan,4\nT02,Lan,5\nT03,Minh,3\nT04,Minh,abc\nT02,Lan,5\nT05,,2\n"


@pytest.mark.parametrize("max_hours, overloaded", [("8", [{"owner": "Lan", "total_hours": 9}]), ("9", [])])
def test_hours_by_owner_and_threshold(tmp_path, max_hours, overloaded):
    result = run(write_csv(tmp_path, WORKLOAD), max_hours=max_hours)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["max_hours"] == int(max_hours)
    assert data["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert data["overloaded_owners"] == overloaded  # bằng ngưỡng không phải quá tải
    assert data["excluded_rows"] == [
        {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
        {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
        {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]},
    ]
    # thống kê chất lượng vẫn tính trên toàn bộ dòng dữ liệu
    assert data["row_count"] == 6 and data["duplicate_ids"] == ["T02"]


def test_first_occurrence_with_invalid_hours_still_claims_id(tmp_path):
    """ID lần đầu có hours lỗi: lần sau vẫn bị loại vì trùng, không thay bằng lần hợp lệ đầu tiên."""
    result = run(write_csv(tmp_path, "task_id,owner,hours\nE01,Lan,abc\nE01,Lan,5\nE02,Minh,0\n"), max_hours="0")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Minh": 0}
    assert "Lan" not in data["hours_by_owner"]
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == [
        {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
        {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]},
    ]


def test_excluded_row_lists_all_reasons_in_order(tmp_path):
    data = json.loads(run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,1\n,,x,extra\nT01, ,-1\n")).stdout)
    assert data["excluded_rows"] == [
        {"line": 3, "task_id": None, "reasons": ["wrong_field_count", "missing_task_id", "missing_owner", "invalid_hours"]},
        {"line": 4, "task_id": "T01", "reasons": ["duplicate_id", "missing_owner", "invalid_hours"]},
    ]
    assert data["hours_by_owner"] == {"Lan": 1}


def test_owner_and_id_are_trimmed_but_case_sensitive(tmp_path):
    data = json.loads(run(write_csv(tmp_path, "task_id,owner,hours\n T01 , Lan ,2\nT02,lan, 3 \nT01,Lan,4\n")).stdout)
    assert data["hours_by_owner"] == {"Lan": 2, "lan": 3}
    assert data["excluded_rows"] == [{"line": 4, "task_id": "T01", "reasons": ["duplicate_id"]}]


@pytest.mark.parametrize("max_hours", [None, "-1", "abc", "nan", "inf", ""])
def test_missing_or_invalid_max_hours_rejected(tmp_path, max_hours):
    result = run(write_csv(tmp_path, WORKLOAD), max_hours=max_hours)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "--max-hours" in result.stderr
