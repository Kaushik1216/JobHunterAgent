import pytest
from pathlib import Path
from job_agent.core.criteria_parser import parse_criteria
from job_agent.exceptions import CriteriaParseError

def test_parse_valid_criteria(sample_criteria_yaml):
    config = parse_criteria(sample_criteria_yaml)
    assert config.global_filters.target_yoe == 3
    assert len(config.targets) == 1
    assert config.targets[0].company == "Stripe"

def test_missing_file():
    with pytest.raises(CriteriaParseError):
        parse_criteria(Path("does_not_exist.yaml"))

def test_empty_file(tmp_path):
    empty_file = tmp_path / "empty.yaml"
    empty_file.write_text("")
    with pytest.raises(CriteriaParseError):
        parse_criteria(empty_file)

def test_invalid_yaml(tmp_path):
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("global: {")
    with pytest.raises(CriteriaParseError):
        parse_criteria(invalid_yaml)

def test_missing_required_fields(tmp_path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("targets: []")
    with pytest.raises(CriteriaParseError):
        parse_criteria(bad_yaml)
