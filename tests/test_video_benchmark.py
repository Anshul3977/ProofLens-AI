import cv2
import pytest

from prooflens.synthetic import reference_image
from prooflens.video import score_frame
from prooflens.video_benchmark import compare_selections


def test_comparison_uses_same_candidates_and_reports_bad_selections():
    source = reference_image()
    candidates = [score_frame(cv2.GaussianBlur(source, (31, 31), 10), 0, 10),
                  score_frame(source, 1, 10), score_frame(source.copy(), 2, 10),
                  score_frame(cv2.flip(source, 1), 3, 10),
                  score_frame(cv2.rotate(source, cv2.ROTATE_180), 4, 10)]
    labels = {0: "blurred", 1: "appearance_A", 2: "appearance_A", 3: "appearance_B", 4: "appearance_C"}
    report = compare_selections(candidates, labels)
    methods = report["methods"]
    assert report["candidate_count"] == 5
    assert methods["uniform"]["quality_eligibility_precision"] == pytest.approx(2 / 3)
    assert methods["quality_and_diversity"]["quality_eligibility_precision"] == 1
    assert methods["quality_and_diversity"]["appearance_classes_covered"] == 3
    assert methods["top_quality"]["selected_count"] == 3


def test_comparison_empty_candidates():
    with pytest.raises(ValueError):
        compare_selections([], {})
