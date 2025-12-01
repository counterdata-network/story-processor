import json
import os
import unittest

import processor.classifiers as classifiers
from processor.test import test_fixture_dir
from processor.test.test_projects import TEST_EN_PROJECT


class TestModelList(unittest.TestCase):
    def test_model_download(self):
        classifiers.update_model_list()  # should write to file system
        models = classifiers.get_model_list()
        for p in models:
            assert "id" in p
            assert p["model_type_1"] in classifiers.MODEL_TYPES
            assert p["vectorizer_type_1"] in classifiers.VECTORIZER_TYPES
            assert p["filename_prefix"] is not None


class TestClassifierHelpers(unittest.TestCase):
    def test_classifier_for_project(self):
        p = TEST_EN_PROJECT.copy()
        c = classifiers.for_project(p)
        assert c.model_name() == "usa"
        p["language_model_id"] = 2
        c = classifiers.for_project(p)
        assert c.model_name() == "uruguay"
        p["language_model_id"] = 3
        c = classifiers.for_project(p)
        assert c.model_name() == "aapf"


class TestChainedClassifers(unittest.TestCase):
    def test_multiplied(self):
        project = TEST_EN_PROJECT.copy()
        project["language_model_id"] = 9
        with open(
            os.path.join(test_fixture_dir, "more_sample_stories.json"), encoding="utf-8"
        ) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        classifier = classifiers.for_project(project)
        results = classifier.classify(sample_texts)
        assert len(results["model_scores"]) == 7
        assert results["model_1_scores"] is not None
        assert len(results["model_1_scores"]) == 7
        assert results["model_2_scores"] is not None
        assert len(results["model_2_scores"]) == 7
        assert round(results["model_scores"][0], 5) == 0.96861
        assert round(results["model_scores"][1], 5) == 0.01917


class TestClassifierResults(unittest.TestCase):
    def test_classify_en(self):
        project = TEST_EN_PROJECT.copy()
        classifier = classifiers.for_project(project)
        with open(
            os.path.join(test_fixture_dir, "usa_sample_stories.json"), encoding="utf-8"
        ) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)["model_scores"]
        assert round(results[0], 5) == 0.36395
        assert round(results[1], 5) == 0.32298
        assert round(results[2], 5) == 0.33297

    def test_classify_en_aapf(self):
        project = (
            TEST_EN_PROJECT.copy()
        )  # important to copy before editing, otherwise subsequent tests get messed up
        project["language_model_id"] = 3
        classifier = classifiers.for_project(project)
        with open(
            os.path.join(test_fixture_dir, "more_sample_stories.json"), encoding="utf-8"
        ) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)["model_scores"]
        assert round(results[0], 5) == 0.78030
        assert round(results[1], 5) == 0.13698
        assert round(results[2], 5) == 0.16526
        assert round(results[3], 5) == 0.36343
        assert round(results[4], 5) == 0.35770

    def test_classify_es(self):
        project = (
            TEST_EN_PROJECT.copy()
        )  # important to copy before editing, otherwise subsequent tests get messed up
        project["language_model_id"] = 2
        classifier = classifiers.for_project(project)
        with open(
            os.path.join(test_fixture_dir, "es_sample_stories.json"), encoding="utf-8"
        ) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)["model_scores"]
        assert round(results[0], 5) == 0.83309

    def _classify_one_from(self, index, file):
        # classify one story against all the EN language models (as of 12/1/25)
        with open(os.path.join(test_fixture_dir, file), encoding="utf-8") as f:
            sample_texts = json.load(f)
        one_story = [sample_texts[index]]
        sample_texts = [dict(story_text=t) for t in one_story]
        results_by_model_id = []
        for model_id in [1, 3, 4, 5, 6, 8, 9, 10, 11, 13, 18]:
            project = TEST_EN_PROJECT.copy()
            project["language_model_id"] = model_id
            classifier = classifiers.for_project(project)
            model_result = classifier.classify(sample_texts)["model_scores"][0]
            results_by_model_id.append(model_result)
        return results_by_model_id

    def test_mmip_classify(self):
        with open(
            os.path.join(test_fixture_dir, "mc-story-2008554915.json"),
            "r",
            encoding="utf-8",
        ) as f:
            story = json.load(f)
        project = TEST_EN_PROJECT.copy()
        project["language_model_id"] = 10
        classifier = classifiers.for_project(project)
        model_result = classifier.classify([story])["model_scores"]
        assert round(model_result[0], 5) == 0.99252

    def test_classify_aapf2(self):
        with open(
            os.path.join(test_fixture_dir, "mc-story-2008554915.json"),
            "r",
            encoding="utf-8",
        ) as f:
            story = json.load(f)
        project = TEST_EN_PROJECT.copy()
        project["language_model_id"] = 5
        classifier = classifiers.for_project(project)
        model_result = classifier.classify([story])["model_scores"]
        assert round(model_result[0], 5) == 0.00789

    def test_classify_pt(self):
        with open(
            os.path.join(test_fixture_dir, "mc-story-2529994630.json"),
            "r",
            encoding="utf-8",
        ) as f:
            story = json.load(f)
        project = TEST_EN_PROJECT.copy()
        project["language_model_id"] = 15
        classifier = classifiers.for_project(project)
        model_result = classifier.classify([story])["model_scores"]
        assert round(model_result[0], 5) == 0.02196

    def test_classify_ko(self):
        project = (
            TEST_EN_PROJECT.copy()
        )  # important to copy before editing, otherwise subsequent tests get messed up
        project["language_model_id"] = 17
        project["language"] = classifiers.LANGUAGE_KO
        classifier = classifiers.for_project(project)
        with open(
            os.path.join(test_fixture_dir, "ko_sample_stories.json"), encoding="utf-8"
        ) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)["model_scores"]
        assert round(results[0], 5) == 0.19358

    def test_stories_against_all_classifiers(self):
        results_by_model_id = self._classify_one_from(6, "more_sample_stories.json")
        for r in results_by_model_id:
            assert r > 0
            assert r < 1

        results_by_model_id = self._classify_one_from(3, "more_sample_stories.json")
        for r in results_by_model_id:
            assert r > 0
            assert r < 1

        results_by_model_id = self._classify_one_from(4, "more_sample_stories.json")
        for r in results_by_model_id:
            assert r > 0
            assert r < 1

        results_by_model_id = self._classify_one_from(5, "more_sample_stories.json")
        for r in results_by_model_id:
            assert r > 0
            assert r < 1


if __name__ == "__main__":
    unittest.main()
