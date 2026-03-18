'''This file contains default versions of components.

This is handy for:
- Making changes in one place
- Keeping everyone on the same version

URL is where we grab the component from. Note that DBC components
change frequently.

Hashes allow us to verify file integrity / avoid man-in-the-middle
attacks

The name is currently not used, but it'd be handy to be able to
include components and component sets as lists (rather than
dictionaries) and with common names.

tested_versions is also currently not used (although a few modules
have a hacked-up version of something similar. The idea is we should
be following LATEST in dev, but on servers, flag if we're running a
version which we have not yet tested.
'''

import dash_bootstrap_components as dbc
import os

REQUIRE_JS = {
    "url": "https://requirejs.org/docs/release/2.3.6/comments/require.js",
    "hash": "d1e7687c1b2990966131bc25a761f03d6de83115512c9ce85d72e4b9819fb"
    "8733463fa0d93ca31e2e42ebee6e425d811e3420a788a0fc95f745aa349e3b01901",
    "name": "require.js"  # <-- We should switch to something like this
}
TEXT_JS = {
    "url": "https://raw.githubusercontent.com/requirejs/text/"
    "3f9d4c19b3a1a3c6f35650c5788cbea1db93197a/text.js",
    "hash": "fb8974f1633f261f77220329c7070ff214241ebd33a1434f2738572608efc"
    "8eb6699961734285e9500bbbd60990794883981fb113319503208822e6706bca0b8"
}
R_JS = {
    "url": "https://requirejs.org/docs/release/2.3.6/r.js",
    "hash": "52300a8371df306f45e981fd224b10cc586365d5637a19a24e710a2fa566f"
    "88450b8a3920e7af47ba7197ffefa707a179bc82a407f05c08508248e6b5084f457"
}
BULMA_CSS = {
    "url": "https://cdnjs.cloudflare.com/ajax/libs/bulma/0.9.0/css/"
    "bulma.min.css",
    "hash": "ec7342883fdb6fbd4db80d7b44938951c3903d2132fc3e4bf7363c6e6dc52"
    "95a478c930856177ac6257c32e1d1e10a4132c6c51d194b3174dc670ab8d116b362"
}
FONTAWESOME_JS = {
    "url": "https://use.fontawesome.com/releases/v5.3.1/js/all.js",
    "hash": "83e7b36f1545d5abe63bea9cd3505596998aea272dd05dee624b9a2c72f96"
    "62618d4bff6e51fafa25d41cb59bd97f3ebd72fd94ebd09a52c17c4c23fdca3962b"
}
SHOWDOWN_JS = {
    "url": "https://cdn.jsdelivr.net/gh/showdownjs/showdown@1.9.1/dist/showdown.js",
    "hash": "4fe14f17c2a1d0275d44e06d7e68d2b177779196c6d0c562d082eb5435eec"
    "4e710a625be524767aef3d9a1f6a5b88f912ddd71821f4a9df12ff7dd66d6fbb3c9"
}
SHOWDOWN_JS_MAP = {
    "url": "https://cdn.jsdelivr.net/gh/showdownjs/showdown@1.9.1/dist/showdown.js.map",
    "hash": "74690aa3cea07fd075942ba9e98cf7297752994b93930acb3a1baa2d3042a"
    "62b5523d3da83177f63e6c02fe2a09c8414af9e1774dad892a303e15a86dbeb29ba"
}
MUSTACHE_JS = {
    "url": "http://cdnjs.cloudflare.com/ajax/libs/mustache.js/3.1.0/"
    "mustache.min.js",
    "hash": "e7c446dc9ac2da9396cf401774efd9bd063d25920343eaed7bee9ad878840"
    "e846d48204d62755aede6f51ae6f169dcc9455f45c1b86ba1b42980ccf8f241af25"
}
D3_V5_JS = {
    "url": "https://d3js.org/d3.v5.min.js",
    "hash": "466fe57816d719048885357cccc91a082d8e5d3796f227f88a988bf36a5c2"
    "ceb7a4d25842f5f3c327a0151d682e648cd9623bfdcc7a18a70ac05cfd0ec434463"
}
BULMA_TOOLTIP_CSS = {
    "url": "https://cdn.jsdelivr.net/npm/@creativebulma/bulma-tooltip@1.2.0/"
    "dist/bulma-tooltip.min.css",
    "hash": "fc37b25fa75664a6aa91627a7b1298a09025c136085f99ba31b1861f073a0"
    "696c4756cb156531ccf5c630154d66f3059b6b589617bd6bd711ef665079f879405"
}
BOOTSTRAP_MIN_CSS = {
    "url": dbc.themes.MINTY,
    "hash": {
        "old": "b361dc857ee7c817afa9c3370f1d317db2c4be5572dd5ec3171caeb812281"
        "cf900a5a9141e5d6c7069408e2615df612fbcd31094223996154e16f2f80a348532",
        "5.1.3": "c03f5bfd8deb11ad6cec84a6201f4327f28a640e693e56466fd80d983ed54"
        "16deff1548a0f6bbad013ec278b9750d1d253bd9c5bd1f53c85fcd62adba5eedc59",
        "5.3.1": "d099dac0135309466dc6208aaa973584843a3efbb40b2c96eb7c179f5f20f"
        "80def35bbc1a7a0b08c9d5bdbed6b8e780ba7d013d18e4019e04fd82a19c076a1f8",
        "5.3.3": "54b69b378be9029cb841bce9f33e111148231ce38ae389601c10ee1fec93b"
        "bfb84839e84911e9e32e9e026a182e7225fd8531dc8344ba94ef4b467852e7162d5",
        "5.3.5": "3c9aa2c118ba4cbb2f54b2ca87528c453503ab5545983b6f5d10c6f04abd9"
        "d4feb003c80c59a092857808e439642ab45e38369980288e7afb5a11e0e7946270e",
        "5.3.6": "0d33ccd34e5244052264f2e30088c92bfd28efc2db229926932be93ba3cc4"
        "8b5f8378e12cf030c50965d1aa62a4a1a8f74493293b320aa9ef0a6b98962ab83b8"
    },
    "tested_versions": [
        'https://cdn.jsdelivr.net/npm/bootswatch@5.3.5/dist/minty/bootstrap.min.css',
        'https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/minty/bootstrap.min.css',
        "https://cdn.jsdelivr.net/npm/bootswatch@5.3.1/dist/minty/bootstrap.min.css",
        'https://cdn.jsdelivr.net/npm/bootswatch@5.1.3/dist/minty/bootstrap.min.css',
    ]
}
FONTAWESOME_CSS = {
    "url": dbc.icons.FONT_AWESOME,
    "hash": {
        "6.1.1": "535a5f3e40bc8ddf475b56c1a39a5406052b524413dea331c4e683ca99e39"
        "6dbbc11fdce1f8355730a73c52ac6a1062de1938406c6af8e4361fd346106acb6b0",
        "6.3.0": "1496214e7421773324f4b332127ea77bec822fc6739292ebb19c6abcc22a5"
        "6248e0634b4e0ca0c2fcac14dc10b8d01fa17febaa35f46731201d1ffd0ab482dd7",
        "6.7.2": "1bd8a997cca7c7abb44f3335a338feb34e69694c3cf4f2cae11ef12ed73f4"
        "f120dc15e680835f88dd71df199fb6596bea05cb569b0fb0822e8fd3ec58c6e0833"
    },
    "tested_versions": [
        "https://use.fontawesome.com/releases/v6.7.2/css/all.css",
        "https://use.fontawesome.com/releases/v6.3.0/css/all.css",
        "https://use.fontawesome.com/releases/v6.1.1/css/all.css"
    ]
}
FONTAWESOME_WOFF2 = {
    "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.woff2",
    "hash": {
        "6.1.1": "6d3fe769cc40a5790ea2e09fb775f1bd3b130d2fdae1dd552f69559e7ca4c"
        "a047862f795da0024737e59e3bcc7446f6eec1bab173758aef0b97ba89d722ffbde",
        "6.3.0": "d50c68cd4b3312f50deb66ac8ab5c37b2d4161f4e00ea077"
        "326ae76769dac650dd19e65dee8d698ba2f86a69537f38cf4010ff45227211cee8b382d9b567257a",
        "6.7.2": "140ad609f15616dff39a7ed2efa080283bb28e13e6fe00987a39774887aa2"
        "a8279f48c36816753e7522474580ee49b937e9d549674b7382f73548f159a206036"
    }
}
FONTAWESOME_TTF = {
    "url": os.path.dirname(os.path.dirname(dbc.icons.FONT_AWESOME)) + "/webfonts/fa-solid-900.ttf",
    "hash": {
        "6.1.1": "0fdd341671021d04304186c197001cf2e888d3028baaf9a5dec0f0e496959"
        "666e8a2e34aae8e79904f8e9b4c0ccae40249897cce5f5ae58d12cc1b3985e588d6",
        "6.3.0": "5a2c2b010a2496e4ed832ede8620f3bbfa9374778f3d63e4"
        "5a4aab041e174dafd9fffd3229b8b36f259cf2ef46ae7bf5cb041e280f2939884652788fc1e8ce58",
        "6.7.2": "8a0a8fc8fcf0b676588bfe28f8b1d154a16af951d31f3a527a9661189c4c2"
        "317b2d5b3b95a3e7c4a77377988fb6852e6d5dae6df48ad07957a62ae22fd2ac0bb"
    }
}

if (dbc.themes.MINTY not in BOOTSTRAP_MIN_CSS["tested_versions"]):
    print("WARN:: Unrecognized Minty URL detected: {}".format(dbc.themes.MINTY))
    print("You will need to update dash bootstrap components hash value.\n")

if (dbc.icons.FONT_AWESOME not in FONTAWESOME_CSS["tested_versions"]):
    print("WARN:: Unrecognized Fontawesome URL detected: {}".format(dbc.icons.FONT_AWESOME))
    print("You will need to update the FontAwesome bootstrap components hash value.\n")
