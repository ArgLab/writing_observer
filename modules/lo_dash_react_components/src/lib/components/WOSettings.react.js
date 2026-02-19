import React, { Component } from 'react';
import PropTypes from 'prop-types';

function generateNewHighlightColor () {
  // Generate random RGB values
  const r = Math.floor(Math.random() * 128) + 128; // 128-255 for brighter colors
  const g = Math.floor(Math.random() * 128) + 128;
  const b = Math.floor(Math.random() * 128) + 128;

  // Convert RGB to hex
  const hex = `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
  return hex;
}

function sortOptionsIntoTree (options) {
  const optionsMap = new Map();
  options.forEach(option => optionsMap.set(option.id, option));

  const sortedOptions = [];

  function addChildren (parentId, depth) {
    options
      .filter(option => option.parent === parentId)
      .forEach(option => {
        sortedOptions.push({ ...option, depth });
        addChildren(option.id, depth + 1);
      });
  }

  addChildren('', 0);

  return sortedOptions;
}

export default class WOSettings extends Component {
  constructor (props) {
    super(props);
    this.state = {
      collapsed: {},
      showHighlight: props.options.some(option => option.types && option.types.includes('highlight')),
      showMetric: props.options.some(option => option.types && option.types.includes('metric'))
    };
    this.handleRowEvent = this.handleRowEvent.bind(this);
    this.renderRow = this.renderRow.bind(this);
    this.toggleCollapse = this.toggleCollapse.bind(this);
  }

  handleRowEvent (event, key, type, colorPicker = false) {
    const { setProps, value } = this.props;
    const currentValue = structuredClone(value);
    if (!(key in currentValue)) {
      currentValue[key] = {};
    }
    if (colorPicker) {
      currentValue[key][type].color = event.target.value;
    } else {
      const { checked } = event.target;
      if (!(type in currentValue[key])) {
        currentValue[key][type] = {};
      }
      currentValue[key][type].value = checked;
      if (type === 'highlight') {
        currentValue[key][type].color = currentValue[key][type].color || generateNewHighlightColor();
      }
    }
    setProps({ value: currentValue });
  }

  toggleCollapse (id) {
    this.setState(prevState => ({
      collapsed: {
        ...prevState.collapsed,
        [id]: !prevState.collapsed[id]
      }
    }));
  }

  renderRow (row, allRows) {
    const { collapsed, showHighlight, showMetric } = this.state;
    const { value } = this.props;
    const hasChildren = allRows.some(option => option.parent === row.id);
    const isCollapsed = collapsed[row.id] || false;

    const highlightCell = row.types && row.types.includes('highlight')
      ? (<>
        <input
          type="checkbox"
          checked={value[row.id]?.highlight.value || false}
          onChange={(e) => this.handleRowEvent(e, row.id, 'highlight')}
          className='me-1'
        />
        {value[row.id]?.highlight.value
          ? (<input
            type="color"
            value={value[row.id]?.highlight.color || '#121212'}
            onChange={(e) => this.handleRowEvent(e, row.id, 'highlight', true)}
          />)
          : null}
      </>)
      : null;
    const metricCell = (row.types && row.types.includes('metric'))
      ? <input type='checkbox' checked={value[row.id]?.metric.value || false} onChange={(e) => this.handleRowEvent(e, row.id, 'metric')} />
      : null;

    return (
      <>
        <tr key={row.id}>
          <td >
            <div style={{
              display: 'inline-block',
              paddingLeft: `${row.depth}em`
            }}>{row.label}</div>
            {hasChildren && (
              <button
                onClick={() => this.toggleCollapse(row.id)}
                style={{
                  marginLeft: '4px',
                  cursor: 'pointer',
                  background: 'none',
                  border: 'none'
                }}
              >
                {isCollapsed ? '▶' : '▼'}
              </button>
            )}
          </td>
          {showHighlight && <td className='text-center'>{highlightCell}</td>}
          {showMetric && <td className='text-center'>{metricCell}</td>}
        </tr>
        {/* Render children rows if not collapsed */}
        {!isCollapsed &&
          allRows
            .filter(child => child.parent === row.id)
            .map(child => this.renderRow(child, allRows))}
      </>
    );
  }

  render () {
    const { id, className, options } = this.props;
    const { showHighlight, showMetric } = this.state;
    const rows = sortOptionsIntoTree(options);

    return (
      <table
        key={`wo-settings-${id}`}
        className={`WOSettings ${className}`}
        id={id}
      >
        <thead>
          <tr>
            <th>Name</th>
            {showHighlight && <th className='text-center'>Highlight</th>}
            {showMetric && <th className='text-center'>Metric</th>}
          </tr>
        </thead>
        <tbody>
          {rows
            .filter(row => row.parent === '') // Start with top-level rows
            .map(row => this.renderRow(row, rows))}
        </tbody>
      </table>
    );
  }
}

WOSettings.defaultProps = {
  id: '',
  className: '',
  options: [],
  value: {}
};

WOSettings.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,

  /**
   * Classes for the outer most div.
   */
  className: PropTypes.string,

  /**
   * Dash-assigned callback that should be called to report property changes
   * to Dash, to make them available for callbacks.
   */
  setProps: PropTypes.func,

  /**
   * Array of available options
   */
  options: PropTypes.arrayOf(PropTypes.exact({
    id: PropTypes.string,
    label: PropTypes.string,
    parent: PropTypes.string,
    types: PropTypes.oneOfType([
      PropTypes.object,
      PropTypes.undefined
    ])
  })),

  /**
   * Dictionary of selected items
   */
  value: PropTypes.object

};
