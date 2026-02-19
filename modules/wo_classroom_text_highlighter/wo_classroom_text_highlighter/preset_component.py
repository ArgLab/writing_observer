'''This creates the input and clickable badges for different
presets the user wants displayed.
TODO create a react component that does this
'''
from dash import html, dcc, clientside_callback, callback, Output, Input, State, ALL, exceptions, Patch, ctx
import dash_bootstrap_components as dbc

import wo_classroom_text_highlighter.options

_prefix = 'option-preset'
_store = f'{_prefix}-store'
_add_input = f'{_prefix}-add-input'
_add_help = f'{_prefix}-add-help'
_add_button = f'{_prefix}-add-button'
_tray = f'{_prefix}-tray'
_set_item = f'{_prefix}-set-item'
_remove_item = f'{_prefix}-remove-item'


def create_layout():
    add_preset = dbc.InputGroup([
        dbc.Input(id=_add_input, placeholder='Preset name', type='text', value=''),
        dbc.InputGroupText(html.I(className='fas fa-circle-question'), id=_add_help),
        dbc.Tooltip(
            'Save the current selected information as a preset for quick use in the future.',
            target=_add_help
        ),
        dbc.Button([
            html.I(className='fas fa-plus me-1'),
            'Preset'
        ], id=_add_button)
    ], class_name='mb-1')
    return html.Div([
        add_preset,
        html.Div(id=_tray),
        # TODO we ought to store the presets on the server instead of browser storage
        # TODO we need to migrate the old options to new ones
        dcc.Store(id=_store, data=wo_classroom_text_highlighter.options.PRESETS, storage_type='local')
    ], id=_prefix)


# disabled add preset when name already exists
clientside_callback(
    '''function (value, curr) {
        if (value.length === 0) { return true; }
        if (Object.keys(curr).includes(value)) { return true; }
        return false;
    }''',
    Output(_add_button, 'disabled'),
    Input(_add_input, 'value'),
    State(_store, 'data')
)

# clear input on add
clientside_callback(
    '''function (clicks, curr) {
        if (clicks) { return ''; }
        return curr;
    }''',
    Output(_add_input, 'value'),
    Input(_add_button, 'n_clicks'),
    State(_add_input, 'value')
)


def create_tray_item(preset):
    if preset == wo_classroom_text_highlighter.options.deselect_all:
        return dbc.Button(preset, id={'type': _set_item, 'index': preset}, color='warning')
    contents = dbc.ButtonGroup([
        dbc.Button(preset, id={'type': _set_item, 'index': preset}),
        dcc.ConfirmDialogProvider(
            dbc.Button(html.I(className='fas fa-trash fa-xs'), color='secondary'),
            id={'type': _remove_item, 'index': preset},
            message=f'Are you sure you want to delete the `{preset}` preset?'
        )
    ], class_name='preset')
    return contents


@callback(
    Output(_tray, 'children'),
    Input(_store, 'modified_timestamp'),
    State(_store, 'data')
)
def create_tray_items_from_store(ts, data):
    if ts is None and data is None:
        raise exceptions.PreventUpdate
    return [html.Div(create_tray_item(preset), className='d-inline-block me-1 mb-1') for preset in reversed(data.keys())]


@callback(
    Output(_store, 'data', allow_duplicate=True),
    Input({'type': _remove_item, 'index': ALL}, 'submit_n_clicks'),
    prevent_initial_call=True
)
def remove_item_from_store(clicks):
    if not ctx.triggered_id or all(c is None for c in clicks):
        raise exceptions.PreventUpdate
    patched_store = Patch()
    del patched_store[ctx.triggered_id['index']]
    return patched_store
