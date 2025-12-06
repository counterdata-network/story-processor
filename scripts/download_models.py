import logging
import os

import tensorflow_hub as hub

from processor.classifiers import (
    TFHUB_MODEL_PATH_EN,
    TFHUB_MODEL_PATH_MULTI,
    download_models,
)

logger = logging.getLogger(__name__)


def _download_from_tfhub(model_url, destination_path):
    download_path = hub.resolve(model_url)
    hub.load(model_url)
    os.rename(download_path, destination_path)


def download_universal_models():
    # these download to the TFHub dir, but for compatibility with prior code we move them to our model dir
    if not os.path.exists(TFHUB_MODEL_PATH_EN):
        logger.info("Downloading Universal Sentence Encoder English model...")
        _download_from_tfhub(
            "https://tfhub.dev/google/universal-sentence-encoder/4", TFHUB_MODEL_PATH_EN
        )
        logger.info("  done")
    else:
        logger.info(
            "Universal Sentence Encoder Muiltilingual model already exists, skipping download."
        )
    if not os.path.exists(TFHUB_MODEL_PATH_MULTI):
        logger.info("Downloading Universal Sentence Encoder Multilingual model...")
        _download_from_tfhub(
            "https://tfhub.dev/google/universal-sentence-encoder-multilingual/3",
            TFHUB_MODEL_PATH_MULTI,
        )
        logger.info("  done")
    else:
        logger.info(
            "Universal Sentence Encoder English model already exists, skipping download."
        )


if __name__ == "__main__":
    # download underlying models from TFHub
    download_universal_models()
    # download project-specific-models
    download_models()
