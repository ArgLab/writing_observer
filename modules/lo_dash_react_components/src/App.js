import React, { Component } from "react";
import { BrowserRouter, Link, Routes, Route } from "react-router-dom";
import PropTypes from 'prop-types';

import "./css/index.css";
import "./css/components/WOMetrics.css"
import "./css/components/LONameTag.css"
import "./css/components/LOPanelLayout.css"
import "./css/components/LOCollapse.css"
import "bootstrap/dist/css/bootstrap.min.css"

const components = {};
const noop = () => null;

// Import all components and their respective test data dynamically
const importAll = (r) => {
  r.keys().forEach((key) => {
    const componentName = key.replace("./", "").replace(".react.js", "");
    components[componentName] = {
      component: r(key).default,
      testdata: testData(componentName),
    };
  });
};

// Load test data for the component, if available
function testData(component_name) {
  let testData = {};
  try {
    testData =
      require(`./lib/components/${component_name}.testdata.js`).default;
  } catch (error) {
    noop();
  }
  return testData;
}

importAll(require.context("./lib/components", true, /\.react.js$/));

// Display a list of installed components for navigation
function ComponentList(_props) {
  return (
    <div>
      <hr />
      <h1>Component list</h1>
      <ul>
        {Object.entries(components).map(([name, _component]) => (
          <li key={"li_" + name}>
            {" "}
            <Link to={"/components/" + name} key={"a_" + name}>
              {name}
            </Link>{" "}
          </li>
        ))}
      </ul>
    </div>
  );
}

class SetPropsWrapper extends Component {
  constructor(props) {
    super(props);
    this.state = {
      ...props,
    };
    this.setProps = this.setProps.bind(this);
  }

  setProps(newProps) {
    this.setState(newProps);
  }

  render() {
    const { component } = this.props;
    const { ...state } = this.state;
    const mergeProps = {
      ...component.testdata,
      ...state,
      setProps: this.setProps,
    };
    return <component.component {...mergeProps} />;
  }
}
SetPropsWrapper.propTypes = {
    /**
     * An object containing the React component to be rendered and any additional props to be passed to it.
     * The object must have two properties:
     * - `component`: a React component to be rendered.
     * - `testdata`: an object containing any additional props to be passed to the component.
     */
    component: PropTypes.shape({
      component: PropTypes.elementType.isRequired,
      testdata: PropTypes.object,
    }).isRequired,
  };

class App extends Component {
  constructor() {
    super();
    this.state = {
      selected: "Bart",
    };
    this.setProps = this.setProps.bind(this);
  }

  setProps(newProps) {
    this.setState(newProps);
  }

  render() {
    return (
      <div>
        <BrowserRouter>
          <Routes>
            <Route path="/" key="home" element={<ComponentList />} />
            {Object.entries(components).map(([name, component]) => (
              <Route
                key={name}
                path={"/components/" + name}
                element={
                  <div>
                    <SetPropsWrapper component={component} />
                    <ComponentList />
                  </div>
                }
              />
            ))}
          </Routes>
        </BrowserRouter>
      </div>
    );
  }
}

export default App;
