import os
import unittest
import pickle
import json

from processor.test import test_fixture_dir
from processor.classifiers import MODEL_DIR


class TestModels(unittest.TestCase):
    """
    Lower level model loading tests for debugging and implementation help
    """

    def test_nb_model(self):
        with open(os.path.join(MODEL_DIR, 'usa_vectorizer.p'), 'rb') as v:
            tfidf_vectorizer = pickle.load(v)
        with open(os.path.join(MODEL_DIR, 'usa_model.p'), 'rb') as m:
            nb_model = pickle.load(m)

        with open(os.path.join(test_fixture_dir, "more_sample_stories.json")) as f:
            sample_texts = json.load(f)
        vectorized_data = tfidf_vectorizer.transform(sample_texts)
        predictions = nb_model.predict_proba(vectorized_data)
        feminicide_probs = predictions[:, 1]
        assert round(feminicide_probs[0], 5) == 0.32256
        assert round(feminicide_probs[1], 5) == 0.13036
        assert round(feminicide_probs[2], 5) == 0.71464

        with open(os.path.join(test_fixture_dir, "usa_sample_stories.json")) as f:
            sample_texts = json.load(f)
        vectorized_data = tfidf_vectorizer.transform(sample_texts)
        predictions = nb_model.predict_proba(vectorized_data)
        feminicide_probs = predictions[:, 1]
        assert round(feminicide_probs[0], 5) == 0.36395
        assert round(feminicide_probs[1], 5) == 0.32298
        assert round(feminicide_probs[2], 5) == 0.33297


if __name__ == "__main__":
    unittest.main()
