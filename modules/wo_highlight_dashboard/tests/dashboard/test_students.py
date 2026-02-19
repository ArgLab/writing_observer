import wo_highlight_dashboard.dashboard.students as unit


def test_fill_in_settings(fetch_nlp_options):
    settings = unit.fill_in_settings(1, 1, fetch_nlp_options, 'narrative')
    keys = settings.keys()
    assert len(keys) > 0
    for k in keys:
        assert len(settings[k]) > 0


def test_create_cards(fetch_students):
    cards = unit.create_cards(fetch_students)
    assert len(cards) == len(fetch_students)
