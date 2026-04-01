from recordclass import dataobject, asdict

# Define a set of indicators with the kind of filtering/summariation we want
#
# Academic Language, Latinate Words, Low Frequency Words, Adjectives, Adverbs,
#    Sentences, Paragraphs --
#    just need to have lexicalfeatures in the pipeline to run.
#
# Transition Words, Ordinal Transition Words --
#    -- shouldonly need syntaxdiscoursefeats in the pipeline to run
#
# Information Sources, Attributions, Citations, Quoted Words, Informal Language
# Argument Words, Emotion Words, Character Trait Words, Concrete Details --
#     Need lexicalfeatures + syntaxdiscoursefeats + viewpointfeatures to run
#
# Main idea sentences, supporting idea sentences, supporting detail sentences --
#     Need the full pipeline to run, though the main dependencies are on
#     lexicalclusters and contentsegmentation
#
# Format for this list: Label, type of indicator (Token or Doc), indicator name,
# filter (if needed), summary function to use
SPAN_INDICATORS = [
    # language
    ('Academic Language', 'Token', 'is_academic', None, 'percent', 'language'),
    ('Informal Language', 'Token', 'vwp_interactive', None, 'percent', 'language'),
    ('Latinate Words', 'Token', 'is_latinate', None, 'percent', 'language'),
    ('Opinion Words', 'Token', 'vwp_evaluation', None, 'total', 'language'),
    ('Emotion Words', 'Token', 'vwp_emotionword', None, 'percent', 'language'),
    # vwp_emotion_states looks for noun/emotion word pairs (takes a lot of resources) - ignoring for now
    # Argumentation
    # ('Argumentation', 'Token', 'vwp_argumentation', None, 'percent'),  # most resource heavy - ignoring for now
    ('Argument Words', 'Token', 'vwp_argumentword', None, 'percent', 'argumentation'),  # more surfacey # TODO needs new label
    ('Explicit argument', 'Token', 'vwp_explicit_argument', None, 'percent', 'argumentation'),  # surfacey # TODO needs new label
    # statements
    ('Statements of Opinion', 'Doc', 'vwp_statements_of_opinion', None, 'percent', 'statements'),
    ('Statements of Fact', 'Doc', 'vwp_statements_of_fact', None, 'percent', 'statements'),
    # Transitions
    # eventually we want to exclude \n\n as transitions using `[('!=', ['introductory'])]`
    # however the introductory category also includes "let us" and "let's"
    # no highlighting is shown on the new lines, so we won't remove it for now.
    ('Transition Words', 'Doc', 'transitions', None, 'counts', 'transitions'),
    #
    ('Positive Transition Words', 'Doc', 'transitions', [('==', ['positive'])], 'total', 'transitions'),
    ('Conditional Transition Words', 'Doc', 'transitions', [('==', ['conditional'])], 'total', 'transitions'),
    ('Consequential Transition Words', 'Doc', 'transitions', [('==', ['consequential'])], 'total', 'transitions'),
    ('Contrastive Transition Words', 'Doc', 'transitions', [('==', ['contrastive'])], 'total', 'transitions'),
    ('Counterpoint Transition Words', 'Doc', 'transitions', [('==', ['counterpoint'])], 'total', 'transitions'),
    ('Comparative Transition Words', 'Doc', 'transitions', [('==', ['comparative'])], 'total', 'transitions'),
    ('Cross Referential Transition Words', 'Doc', 'transitions', [('==', ['crossreferential'])], 'total', 'transitions'),
    ('Illustrative Transition Words', 'Doc', 'transitions', [('==', ['illustrative'])], 'total', 'transitions'),
    ('Negative Transition Words', 'Doc', 'transitions', [('==', ['negative'])], 'total', 'transitions'),
    ('Emphatic Transition Words', 'Doc', 'transitions', [('==', ['emphatic'])], 'total', 'transitions'),
    ('Evenidentiary Transition Words', 'Doc', 'transitions', [('==', ['evidentiary'])], 'total', 'transitions'),
    ('General Transition Words', 'Doc', 'transitions', [('==', ['general'])], 'total', 'transitions'),
    ('Ordinal Transition Words', 'Doc', 'transitions', [('==', ['ordinal'])], 'total', 'transitions'),
    ('Purposive Transition Words', 'Doc', 'transitions', [('==', ['purposive'])], 'total', 'transitions'),
    ('Periphrastic Transition Words', 'Doc', 'transitions', [('==', ['periphrastic'])], 'total', 'transitions'),
    ('Hypothetical Transition Words', 'Doc', 'transitions', [('==', ['hypothetical'])], 'total', 'transitions'),
    ('Summative Transition Words', 'Doc', 'transitions', [('==', ['summative'])], 'total', 'transitions'),
    ('Introductory Transition Words', 'Doc', 'transitions', [('==', ['introductory'])], 'total', 'transitions'),
    # pos_
    ('Adjectives', 'Token', 'pos_', [('==', ['ADJ'])], 'total', 'pos'),
    ('Adverbs', 'Token', 'pos_', [('==', ['ADV'])], 'total', 'pos'),
    ('Nouns', 'Token', 'pos_', [('==', ['NOUN'])], 'total', 'pos'),
    ('Proper Nouns', 'Token', 'pos_', [('==', ['PROPN'])], 'total', 'pos'),
    ('Verbs', 'Token', 'pos_', [('==', ['VERB'])], 'total', 'pos'),
    ('Numbers', 'Token', 'pos_', [('==', ['NUM'])], 'total', 'pos'),
    ('Prepositions', 'Token', 'pos_', [('==', ['ADP'])], 'total', 'pos'),
    ('Coordinating Conjunction', 'Token', 'pos_', [('==', ['CCONJ'])], 'total', 'pos'),
    ('Subordinating Conjunction', 'Token', 'pos_', [('==', ['SCONJ'])], 'total', 'pos'),
    ('Auxiliary Verb', 'Token', 'pos_', [('==', ['AUX'])], 'total', 'pos'),
    ('Pronoun', 'Token', 'pos_', [('==', ['PRON'])], 'total', 'pos'),
    # sentence variety
    # The general 'Sentence Types' will return a complex object of all sentence types
    # that we do not yet handle.
    # ('Sentence Types', 'Doc', 'sentence_types', None, 'counts'),
    ('Simple Sentences', 'Doc', 'sentence_types', [('==', ['Simple'])], 'total', 'sentence_type'),
    ('Simple with Complex Predicates', 'Doc', 'sentence_types', [('==', ['SimpleComplexPred'])], 'total', 'sentence_type'),
    ('Simple with Compound Predicates', 'Doc', 'sentence_types', [('==', ['SimpleCompoundPred'])], 'total', 'sentence_type'),
    ('Simple with Compound Complex Predicates', 'Doc', 'sentence_types', [('==', ['SimpleCompoundComplexPred'])], 'total', 'sentence_type'),
    ('Compound Sentences', 'Doc', 'sentence_types', [('==', ['Compound'])], 'total', 'sentence_type'),
    ('Complex Sentences', 'Doc', 'sentence_types', [('==', ['Complex'])], 'total', 'sentence_type'),
    ('Compound Complex Sentences', 'Doc', 'sentence_types', [('==', ['CompoundComplex'])], 'total', 'sentence_type'),
    # Sources/Attributes/Citations/Quotes
    ('Information Sources', 'Token', 'vwp_source', None, 'percent', 'source_information'),
    ('Attributions', 'Token', 'vwp_attribution', None, 'percent', 'source_information'),
    ('Citations', 'Token', 'vwp_cite', None, 'percent', 'source_information'),
    ('Quoted Words', 'Token', 'vwp_quoted', None, 'percent', 'source_information'),
    # Dialogue
    ('Direct Speech Verbs', 'Doc', 'vwp_direct_speech', None, 'percent', 'dialogue'),
    ('Indirect Speech', 'Token', 'vwp_in_direct_speech', None, 'percent', 'dialogue'),
    # vwp_quoted - already used above
    # tone
    ('Positive Tone', 'Token', 'vwp_tone', [('>', [.4])], 'percent', 'tone'),
    ('Negative Tone', 'Token', 'vwp_tone', [('<', [-.4])], 'percent', 'tone'),
    # details
    ('Concrete Details', 'Token', 'concrete_details', None, 'percent', 'details'),
    ('Main Idea Sentences', 'Doc', 'main_ideas', None, 'total', 'details'),
    ('Supporting Idea Sentences', 'Doc', 'supporting_ideas', None, 'total', 'details'),
    ('Supporting Detail Sentences', 'Doc', 'supporting_details', None, 'total', 'details'),
    # Other items
    ('Polysyllabic Words', 'Token', 'nSyll', [('>', [3])], 'percent', 'other'),
    ('Low Frequency Words', 'Token', 'max_freq', [('<', [4])], 'percent', 'other'),
    ('Sentences', 'Doc', 'sents', None, 'total', 'other'),
    ('Paragraphs', 'Doc', 'delimiter_\n', None, 'total', 'other'),
    ('Character Trait Words', 'Token', 'vwp_character', None, 'percent', 'other'),
    ('In Past Tense', 'Token', 'in_past_tense_scope', None, 'percent', 'other'),
    ('Explicit Claims', 'Doc', 'vwp_propositional_attitudes', None, 'percent', 'other'),
    ('Social Awareness', 'Doc', 'vwp_social_awareness', None, 'percent', 'other')
]

# Create indicator dict to easily refer to each tuple above by name
INDICATORS = {}
INDICATOR_W_IDS = []
for indicator in SPAN_INDICATORS:
    id = indicator[0].lower().replace(' ', '_')
    INDICATOR_W_IDS.append((id, ) + indicator)
    INDICATORS[id] = (id, ) + indicator


class NLPIndicators(dataobject):
    id: str
    name: str
    type: str
    parent: str
    filters: list
    function: str
    category: str
    # tooltip: str


indicators = map(lambda ind: NLPIndicators(*ind), INDICATOR_W_IDS)
INDICATOR_JSONS = [asdict(ind) for ind in indicators]

INDICATOR_CATEGORIES = {
    'language': 'Language',
    'argumentation': 'Argumentation',
    'statements': 'Statements',
    'transitions': 'Transition Words',
    'pos': 'Parts of Speech',
    'sentence_type': 'Sentence Types',
    'source_information': 'Source Information',
    'dialogue': 'Dialogue',
    'tone': 'Tone',
    'details': 'Details',
    'other': 'Other'
}
