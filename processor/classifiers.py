import json
import logging
import os
import pickle
import shutil
from typing import Dict, List
from urllib.parse import urlparse

import requests
import tensorflow_hub as hub

# loaded here because the non-english embeddings model needs it
import tensorflow_text  # noqa: F401

import processor.apiclient as apiclient
from processor import base_dir

logger = logging.getLogger(__name__)

# where are the models held?
FILES_DIR = os.path.join(base_dir, "files")
MODEL_DIR = os.path.join(base_dir, "files", "models")
CONFIG_DIR = os.path.join(base_dir, "config")

# constants that tell us what type of model to load and run (keep in sync with the main server)
MODEL_LINEAR_REGRESSION = "lr"
MODEL_NAIVE_BAYES = "nb"
MODEL_TYPES = [MODEL_LINEAR_REGRESSION, MODEL_NAIVE_BAYES]
VECTORIZER_TF_IDF = "tfidf"
VECTORIZER_EMBEDDINGS = "embeddings"
VECTORIZER_TYPES = [VECTORIZER_TF_IDF, VECTORIZER_EMBEDDINGS]

DEFAULT_MODEL_NAME = "usa"

LANGUAGE_EN = "en"
TFHUB_MODEL_PATH_EN = os.path.join(MODEL_DIR, "embeddings-en")
LANGUAGE_KO = "ko"
TFHUB_MODEL_PATH_MULTI = os.path.join(MODEL_DIR, "embeddings-multi")


class Classifier:
    """
    This is a wrapper around all our classifiers, so the implementation details don't matter to the consumer. Based on
    the model the project refers to, it decides how to load and run the associated models.
    """

    def __init__(self, model_config: Dict, project: Dict):
        self.config = model_config
        self.project = project
        self._init()

    def model_name(self) -> str:
        return self.config["filename_prefix"]

    def _path_to_file(self, filename: str) -> str:
        return os.path.join(
            MODEL_DIR, self.config["filename_prefix"] + "_" + filename + ".p"
        )

    def _init(self):
        # Classifier 1 is always defined
        with open(self._path_to_file("1_model"), "rb") as m:  # load model
            self._model_1 = pickle.load(m)
        if self.config["vectorizer_type_1"] == VECTORIZER_TF_IDF:  # load vectorizer
            with open(self._path_to_file("1_vectorizer"), "rb") as v:
                self._vectorizer_1 = pickle.load(v)
        elif self.config["vectorizer_type_1"] == VECTORIZER_EMBEDDINGS:
            try:
                model_path = (
                    TFHUB_MODEL_PATH_EN
                    if self.project["language"] == LANGUAGE_EN
                    else TFHUB_MODEL_PATH_MULTI
                )
                if self.project["language"].lower() == LANGUAGE_EN:
                    self._vectorizer_1 = hub.load(model_path)
                elif self.project["language"].lower() == LANGUAGE_KO:
                    self._vectorizer_1 = hub.load(model_path)
                else:
                    raise RuntimeError(
                        "Unsupported embeddings language '{}' for project {}".format(
                            self.project["language"], self.project["id"]
                        )
                    )
            except OSError as ose:
                # probably the cached SavedModel doesn't exist anymore
                logger.error(ose)
                raise RuntimeError(
                    "Project {} - model {} - can't load _vectorizer_1 from {} - did you run /scripts/download-models.sh?".format(
                        self.project["id"],
                        self.project["language_model_id"],
                        model_path,
                    )
                )
        else:
            raise RuntimeError(
                "Unknown vectorizer 1 type '{}' for project {}".format(
                    self.config["vectorizer_type_1"], self.project["id"]
                )
            )
        # Classifier 2 could also exist
        if self.config["chained_models"]:
            with open(self._path_to_file("2_model"), "rb") as m:  # load model
                self._model_2 = pickle.load(m)
            if self.config["vectorizer_type_2"] == VECTORIZER_TF_IDF:  # load vectorizer
                with open(self._path_to_file("2_vectorizer"), "rb") as v:
                    self._vectorizer_2 = pickle.load(v)
            elif self.config["vectorizer_type_2"] == VECTORIZER_EMBEDDINGS:
                try:
                    model_path = (
                        TFHUB_MODEL_PATH_EN
                        if self.project["language"] == LANGUAGE_EN
                        else TFHUB_MODEL_PATH_MULTI
                    )
                    if self.project["language"].lower() == LANGUAGE_EN:
                        self._vectorizer_2 = hub.load(model_path)
                    elif self.project["language"].lower() == LANGUAGE_KO:
                        self._vectorizer_2 = hub.load(model_path)
                    else:
                        raise RuntimeError(
                            "Unsupported embeddings language '{}' for project {}".format(
                                self.project["language"], self.project["id"]
                            )
                        )
                except OSError:
                    # probably the cached SavedModel doesn't exist anymore
                    raise RuntimeError(
                        "Project {} - model {} - can't load _vectorizer_2 from {} - did you run /scripts/download-models.sh?".format(
                            self.project["id"],
                            self.project["language_model_id"],
                            model_path,
                        )
                    )
            else:
                raise RuntimeError(
                    "Unknown vectorizer 2 type '{}' for project {}".format(
                        self.config["vectorizer_type_2"], self.project["id"]
                    )
                )

    def classify(self, stories: List[Dict]) -> Dict[str, List[float]]:
        """

        :param stories:
        :return: a dict with 3 entries:
                * `model_1_scores`: scores from model 1 (None if only one model)
                * `model_2_scores`: scores from model 2 (None if only one model)
                * `model_scores`: list of single, or combined model scores
        """
        # only execute if there are stories
        if not stories:
            return dict(
                model_1_scores=None,
                model_2_scores=None,
                model_scores=[],
            )

        story_texts = [s["story_text"] for s in stories]

        # Classifier 1 always exists (but only chained models have classifier_2
        # vectorize first (turn words/sentences into vectors)
        try:
            if self.config["vectorizer_type_1"] == VECTORIZER_TF_IDF:
                vectorized_data_1 = self._vectorizer_1.transform(story_texts)
            elif self.config["vectorizer_type_1"] == VECTORIZER_EMBEDDINGS:
                vectorized_data_1 = self._vectorizer_1(story_texts)
            else:
                raise RuntimeError(
                    "Unknown vectorizer1 type of {} on project {}".format(
                        self.config["vectorizer_type_1"], self.project["id"]
                    )
                )
        except AttributeError as ae:
            logger.error(ae)
            raise RuntimeError(
                "Project {} model missing vectorizer".format(self.project["id"])
            )

        # now run model against vectors (turn vectors into probabilities)
        try:
            predictions_1 = self._model_1.predict_proba(vectorized_data_1)
            true_probs_1 = predictions_1[
                :, 1
            ]  # grab the list of probabilities that these *are* feminicide stories
        except ValueError as ve:
            logger.exception(ve)
            raise RuntimeError(
                "Model {} failed to run ({}/{})".format(
                    self.config["id"],
                    self.config["model_1"],
                    self.config["vectorizer_type_1"],
                )
            )

        if not self.config["chained_models"]:
            return dict(
                model_1_scores=None, model_2_scores=None, model_scores=true_probs_1
            )

        # Classifier 2 could also exist
        if self.config["vectorizer_type_2"] == VECTORIZER_TF_IDF:
            vectorized_data_2 = self._vectorizer_2.transform(story_texts)
        elif self.config["vectorizer_type_2"] == VECTORIZER_EMBEDDINGS:
            vectorized_data_2 = self._vectorizer_2(story_texts)
        else:
            raise RuntimeError(
                "Unknown vectorizer2 type of {} on project {}".format(
                    self.config["vectorizer_type_2"], self.project["id"]
                )
            )

        # now run model against vectors (turn vectors into probabilities)
        try:
            predictions_2 = self._model_2.predict_proba(vectorized_data_2)
            true_probs_2 = predictions_2[
                :, 1
            ]  # grab the list of probabilities that these *are* feminicide stories
        except ValueError as ve:
            logger.exception(ve)
            raise RuntimeError(
                "Model {} failed to run ({}/{})".format(
                    self.config["id"],
                    self.config["model_2"],
                    self.config["vectorizer_type_2"],
                )
            )

        # with chained models we just return the multiplied probs (for now)
        combined_probs = true_probs_1 * true_probs_2
        return dict(
            model_1_scores=true_probs_1,
            model_2_scores=true_probs_2,
            model_scores=combined_probs,
        )


def for_project(project: Dict) -> Classifier:
    """
    This is a factory method to return a Classifer for the project based on the `language_model_id`
    """
    model_list = get_model_list()
    try:
        matching_models = [
            m for m in model_list if int(m["id"]) == int(project["language_model_id"])
        ]
        model_config = matching_models[0]
        logger.debug("Project {} - model {}".format(project["id"], model_config["id"]))
    except Exception as e:
        logger.exception(
            "Can't find model for project {}, language_model_id {} ({})".format(
                project["id"], project["language_model_id"], e
            )
        )
        raise RuntimeError(
            "Can't find model for project {}, language_model_id {} ({})".format(
                project["id"], project["language_model_id"], e
            )
        )
    return Classifier(model_config, project)


def get_model_list() -> List[Dict]:
    """
    Get the locally cached list of models
    :return:
    """
    try:
        with open(os.path.join(CONFIG_DIR, "language-models.json"), "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(
            "no existing language-models.json found, going with an empty list of models"
        )
        return []


def update_model_list() -> List[Dict]:
    """
    Fetch and save list of models from the central server.
    :return: List of models that are new, or have new versions, so they can be downloaded
    """
    # load the (potentially) updated list of models from the central server
    model_list = apiclient.get_language_models_list()
    if len(model_list) == 0:
        raise RuntimeError("Fetched empty model list was empty - bailing unhappily")
    logger.info(f"Loaded list of {len(model_list)} models from main server.")

    # preload the existing list of models that are cached locally (will be empty list if first time)
    existing_models = get_model_list()

    # update only if the version number has changed, or if the model is new
    updated_models = []
    for model in model_list:
        existing_model = next(
            (m for m in existing_models if m["id"] == model["id"]), None
        )
        if not existing_model or existing_model.get("version") != model.get("version"):
            updated_models.append(model)

    # before returning, make sure that the model files that we've assumed exist, actually exist
    for model in [m for m in model_list if m not in updated_models]:
        # get extra safe .p name
        for u in model["model_1_files"]:
            model_file1 = _model_file_path(
                u, MODEL_DIR, model["filename_prefix"] + "_1"
            )
            # if model 1 files don't exist, add the model to be updated, and skip the check for model 2 files
            if not os.path.isfile(model_file1):
                updated_models.append(model)
                break
        else:
            for u in model["model_2_files"]:
                # get extra safe .p name and check that it exists
                model_file2 = _model_file_path(
                    u, MODEL_DIR, model["filename_prefix"] + "_2"
                )
                if not os.path.isfile(model_file2):
                    updated_models.append(model)
                    break

    # save new model information and send updated model list for download
    with open(os.path.join(CONFIG_DIR, "language-models.json"), "w") as f:
        json.dump(model_list, f)
    logger.debug(f"{len(updated_models)} model(s) to update.")

    return updated_models


def download_models() -> bool:
    """
    Models are stored centrally on the server. We need to retrieve and store them here.
    Returns success or failure bool - if False you probably want to suspend what you were doing and bail out
    """
    try:
        models_to_update = update_model_list()
        if not models_to_update:
            logger.info("No models to update. All versions are up-to-date.")
            return True
        logger.info(f"Downloading {len(models_to_update)} new or updated models:")
        for m in models_to_update:
            logger.info("  {} - {}".format(m["id"], m["name"]))
            for u in m["model_1_files"]:
                _download_file(u, MODEL_DIR, m["filename_prefix"] + "_1")
            for u in m["model_2_files"]:
                _download_file(u, MODEL_DIR, m["filename_prefix"] + "_2")
        return True
    except Exception as e:
        logger.error(f"Couldn't get the models - bailing out cowardly. Error: {e}")
        return False


def _model_file_path(url: str, dest_dir: str, prefix: str) -> str:
    """Generate a safe filename with the given prefix"""
    url_parts = urlparse(url)
    local_filename = url_parts.path.split("/")[-1]
    filename_parts = local_filename.split("_")
    extra_safe_filename = prefix + "_" + filename_parts[-1]
    file_path = os.path.join(dest_dir, extra_safe_filename)

    return file_path


def _download_file(url: str, dest_dir: str, prefix: str):
    """
    This expects the files to either end with "_model.p" or "_vectorizer.p". It renames them here so that
    there is less of a convention that needs to be maintained on the central server.
    :param url:
    :param dest_dir:
    :param prefix:
    :return:
    """
    # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    extra_safe_filename = _model_file_path(url, dest_dir, prefix)
    logger.info("    to {}".format(extra_safe_filename))
    with requests.get(url, stream=True) as r:
        with open(os.path.join(dest_dir, extra_safe_filename), "wb") as f:
            shutil.copyfileobj(r.raw, f)
