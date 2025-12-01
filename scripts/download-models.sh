#!/bin/sh

python -m scripts.download_models

# English language LR model
# originally: curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder/4.tar.gz -o 4.tar.gz
# curl -SL "https://www.dropbox.com/s/6vfe4ttvoypisp5/embeddings-en.tar.gz?dl=1" -o embeddings-en.tar.gz
curl -SL "https://storage.googleapis.com/kaggle-models-data/1265/1497/bundle/archive.tar.gz?GoogleAccessId=web-data@kaggle-161607.iam.gserviceaccount.com&Expires=1764876814&Signature=w55O5%2BhHUVFLZ1wVvYERHZJ%2F%2B7%2FqQhN4x71KIBWrVvk3gTajxpi4rDfmYBFNIZBrDvnLJGd%2FcY%2FNUQj4wPXZBywfWff0bkO2jY7Pr%2Bj1FSFnif922sB9MyF%2BrOzGUD4gBBZ7J1bHO%2BdzTKQu2U718yPdGlpLF2kdFqAymbOLS%2F%2F9pZYmqgAb0j3SXUfQQ9ixvFgZstYh9ZvVhZGPNw6Wh5VNRXsgtxeGDZiEcIotOuzPMOMx1dHfS%2FtI4ddqO0oCZ8j7uPIvrZannRkjmFPwC%2Bx9e9RKFoD8ZVsbFtncBPp1Zeb844VMtJz30mf5ZBJ35Awr2KMV2JkbqaN8Ya%2BEUQ%3D%3D&response-content-disposition=attachment%3B+filename%3Duniversal-sentence-encoder-tensorflow2-universal-sentence-encoder-v2.tar.gz" -o embeddings-en.tar.gz
mkdir files/models/embeddings-en/
tar xfz embeddings-en.tar.gz -C files/models/embeddings-en/

# Multilingual language LR model (for Korean)
# originally: curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder-multilingual/3.tar.gz -o 3.tar.gz
# curl -SL "https://www.dropbox.com/scl/fi/wrpg8tqgqb9boqgwf07ec/embeddings-multi.tar.gz?rlkey=rxtqq8ggfls4jh00rrdurs5wx&dl=1" -o embeddings-multi.tar.gz
curl -SL "https://storage.googleapis.com/kaggle-models-data/1278/1516/bundle/archive.tar.gz?GoogleAccessId=web-data@kaggle-161607.iam.gserviceaccount.com&Expires=1764839029&Signature=W0Ta6INRB79KK%2BXGF8SI%2Fr28dCk1f10jCh7ckdwps8RxB6C6b6lk1y8hhSY8rSqoqcoto2NiO%2BCIRyKzl3SuFCgIpZw55LrCnBe415bZa6Y4GbKwR76hGXAACtyeZpH1vawEdhAIeRk6f%2BM1YLjPLFkofitpter0cuSHIpky4ZSgWlzz9m%2BaBryhB3Spe1ThuUxDB2UHXcU7MKR94JPTmgU7fBPMnw9YXz7ZqrAPDSNANzbyocJ4%2BNDe1n4ZBeHxN00GrpmHA2WFyNYqKHRXh0w%2FLwqAflntQi%2FI2WZ3CZhwX%2Bm8CKwjh46dkTrhhiCY%2BuE1F2bnwL8M1PyrsdqqjA%3D%3D&response-content-disposition=attachment%3B+filename%3Duniversal-sentence-encoder-tensorflow2-multilingual-v2.tar.gz" -o embeddings-multi.tar.gz
mkdir files/models/embeddings-multi/
tar xfz embeddings-multi.tar.gz -C files/models/embeddings-multi/
