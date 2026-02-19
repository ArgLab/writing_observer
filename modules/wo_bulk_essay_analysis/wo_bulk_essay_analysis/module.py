import learning_observer.communication_protocol.query as q
import learning_observer.downloads as d
from learning_observer.dash_integration import thirdparty_url

import wo_bulk_essay_analysis.gpt
import wo_bulk_essay_analysis.dashboard.layout


NAME = "Writing Observer - Classroom AI Feedback Assistant"

DASH_PAGES = [
    {
        "MODULE": wo_bulk_essay_analysis.dashboard.layout,
        "LAYOUT": wo_bulk_essay_analysis.dashboard.layout.layout,
        "ASSETS": 'assets',
        "TITLE": "Classroom AI Feedback Assistant",
        "DESCRIPTION": "The Classroom AI Feedback Assistant is a robust educational tool that leverages AI to simultaneously analyze and provide feedback on large batches of essays, delivering comprehensive insights and constructive critiques for educators in diverse group settings.",
        "SUBPATH": "bulk-essay-analysis",
        "CSS": [
            thirdparty_url("css/bootstrap.min.css"),
            thirdparty_url("css/fontawesome_all.css")
        ],
        "SCRIPTS": [
            thirdparty_url('pdf.js'),
            thirdparty_url('pdf.worker.js'),
            thirdparty_url('mammoth.js')
        ]
    }
]


THIRD_PARTY = {
    # PDF parser for reading in files clientside
    'pdf.js': {
        'url': 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.9.179/pdf.min.js',
        'hash': {
            '3.9.179': 'c1dd581c4d2fec33c43eecb394a4335f25da58dcda361efe422ddbb32e640'
            'e548547b75cb8e0db9ec0746480eb3d34a63c23c89296ea22a7ab22b6f37e726ef2'
        }
    },
    'pdf.worker.js': {
        'url': 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.9.179/pdf.worker.min.js',
        'hash': {
            '3.9.179': '0fc109e44fb5af718c31f1a15e1479850ef259efa42dcdd2cdd975387df3b'
            '3ebb7dad9946bd3d00bdcd29527dc753fde4b950b2a7a052bd8f66ee643bb736767'
        }
    },
    # Docx parser for reading in files clientside
    'mammoth.js': {
        'url': 'https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.9.0/mammoth.browser.min.js',
        'hash': {
            '1.9.0': '7e77162c6d0103528615896ba72fcca385ab2f64699cd06d744a6d740c16179'
            '322e02e2d45adf1c4d8720f6c8ac7c54e19c6a061eb0814f2abb4b80738d8766a'
        }
    },
    "css/bootstrap.min.css": d.BOOTSTRAP_MIN_CSS,
    "css/fontawesome_all.css": d.FONTAWESOME_CSS,
    "webfonts/fa-solid-900.woff2": d.FONTAWESOME_WOFF2,
    "webfonts/fa-solid-900.ttf": d.FONTAWESOME_TTF
}

COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/wo_bulk_essay_analysis/dash/bulk-essay-analysis",
    "icon": {
        "type": "fas",
        "icon": "fa-lightbulb"
    }
}]
