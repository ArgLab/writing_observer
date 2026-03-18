from dash import html
import dash_bootstrap_components as dbc

import wo_highlight_dashboard.dashboard.settings_options as unit
import wo_highlight_dashboard.dashboard.settings_defaults as defaults


def test_create_metric_label(fetch_nlp_options):
    for opt in fetch_nlp_options:
        result = unit.create_metric_label(opt)
        assert isinstance(result, dbc.Badge)
        assert result.children == opt['name']
        assert result.color == 'info'


def test_create_highlight_label(fetch_nlp_options):
    for opt in fetch_nlp_options:
        result = unit.create_highlight_label(opt)
        assert isinstance(result, html.Span)
        assert result.children == opt['name']
        assert result.className == f"{opt.get('id')}_highlight"


def test_create_generic_label(fetch_nlp_options):
    for opt in fetch_nlp_options:
        result = unit.create_highlight_label(opt)
        assert isinstance(result, html.Span)
        assert result.children == opt['name']


def test_create_checklist_options(fetch_nlp_options):
    items = ['metrics', 'indicators', 'highlight']
    for i in items:
        default = defaults.general[i]['selected']
        options = unit.create_checklist_options(default, fetch_nlp_options, i)
        assert len(options) == len(default)
