'''
Each variable displays the defaults for each type of essay.
Ideally, users can select multiple (deep merge) to see both general
and argumentative for instance.

In the future, we probably want the dashboard more flexible with
different types of modules being plugged in (metrics/highlighter/etc.).
This information will probably want to be handled a bit nicer once
we understand the full workflow of the plugability.
'''
import writing_observer.nlp_indicators

all_options = writing_observer.nlp_indicators.INDICATORS.keys()
general = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': ['sentences', 'paragraphs', 'pos_'],
        'selected': ['sentences', 'paragraphs']
    },
    'highlight': {
        'options': [
            'informal_language', 'transition_words', 'low_frequency_words',
            'positive_tone', 'negative_tone',
            'polysyllabic_words', 'academic_language'
        ],
        'selected': []
    },
    'indicators': {
        'options': [
            'academic_language', 'informal_language', 'latinate_words',
            'polysyllabic_words', 'low_frequency_words'
        ],
        'selected': ['academic_language', 'informal_language']
    }
}
argumentative = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': [],
        'selected': []
    },
    'highlight': {
        'options': [
            'main_idea_sentences', 'supporting_idea_sentences', 'supporting_detail_sentences',
            'argument_words', 'explicit_argument',
            'statements_of_opinion', 'statements_of_fact',
            'explicit_claims',
        ],
        'selected': ['main_idea_sentences', 'supporting_idea_sentences']
    },
    'indicators': {
        'options': ['opinion_words', 'argument_words', 'information_sources', 'attributions', 'citations'],
        'selected': []
    }
}
narrative = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': [],
        'selected': []
    },
    'highlight': {
        'options': [
            'direct_speech_verbs', 'indirect_speech',
            'in_past_tense', 'social_awareness',
            'character_trait_words', 'concrete_details', 
        ],
        'selected': ['character_trait_words', 'concrete_details']
    },
    'indicators': {
        'options': ['emotion_words', 'character_trait_words'],
        'selected': ['character_trait_words']
    }
}
source_based = {
    'sort_by': {
        'options': [],
        'selected': []
    },
    'metrics': {
        'options': [],
        'selected': []
    },
    'highlight': {
        'options': ['information_sources', 'attributions', 'citations', 'quoted_words'],
        'selected': []
    },
    'indicators': {
        'options': [],
        'selected': []
    }
}


def combine_dicts(dicts):
    # Initialize a dictionary with the same structure as input dicts
    combined = {
        'sort_by': {
            'options': [],
            'selected': []
        },
        'metrics': {
            'options': [],
            'selected': []
        },
        'highlight': {
            'options': [],
            'selected': []
        },
        'indicators': {
            'options': [],
            'selected': []
        }
    }

    # Iterate over input dicts
    for d in dicts:
        # Iterate over keys and subkeys of each input dict
        for key, subdict in d.items():
            for subkey, value in subdict.items():
                # Append values to the corresponding list in the combined dict
                combined[key][subkey].extend(value)

    return combined


overall = {
    'sort_by': {
        'options': all_options,
        'selected': []
    },
    'metrics': {
        'options': all_options,
        'selected': []
    },
    'highlight': {
        'options': all_options,
        'selected': []
    },
    'indicators': {
        'options': all_options,
        'selected': []
    }
}
general_argumentative = combine_dicts([general, argumentative, source_based])
general_narrative = combine_dicts([general, narrative, source_based])
