'''
This implements a search for a particular standard using a
relatively small, fast neural network.

Load time is a little bit annoying (3-4 seconds), but queries
run quickly.

It can be used directly, or to return a set of all possible
results, with the final results then pruned by an LLM

Perhaps this ought to be teased out into its own library. This should
definitely not be placed in anything imported in __init__.py or
ccss.py, since most uses of ccss probably won't use this, and it adds
to startup time.
'''

import json

from sentence_transformers import SentenceTransformer, util
import torch

# Load the model. This is a relatively small model (80MB)
model = SentenceTransformer('all-MiniLM-L6-v2')

standard_keys, standard_texts = zip(*json.load(open("ccss.json")).items())

# Encode all standard_texts to get their embeddings
embeddings = model.encode(standard_texts, convert_to_tensor=True)


def search(query, *args, max_result_count=5):
    '''
    Fast (imperfect) semantic similarity search.

    Fast enough to work in realtime (e.g. for autocomplete)

    From best to worst.

    `max_result_count` can be set to `None` to return all standards
    items
    '''
    # Encode the query
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Use cosine similarity to find the most similar
    # standard_texts to the query
    cos_similarities = util.pytorch_cos_sim(query_embedding, embeddings)[0]

    # Get the index of the most similar sentence
    top_match_index = torch.argmax(cos_similarities).item()
    top_match_indices = cos_similarities.argsort(descending=True)
    if max_result_count:
        top_match_indices = top_match_indices[:max_result_count]

    result_standard_texts = [standard_texts[i] for i in top_match_indices]
    result_standard_keys = [standard_keys[i] for i in top_match_indices]
    return zip(result_standard_keys, result_standard_texts)


if __name__ == '__main__':
    for key, text in search("division", max_result_count=10):
        print(f"{key}: {text}")
