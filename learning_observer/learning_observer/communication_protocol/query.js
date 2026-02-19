const DISPATCH_MODES = {}
const dispatchModes = ['parameter', 'variable', 'call', 'select', 'join', 'map', 'keys']
dispatchModes.forEach((mode) => {
  DISPATCH_MODES[mode.toUpperCase()] = mode
})

function parameter (parameterName, required = false, defaultValue = null) {
  return {
    dispatch: DISPATCH_MODES.PARAMETER,
    parameter_name: parameterName,
    required,
    default: defaultValue
  }
}

function variable (variableName) {
  return {
    dispatch: DISPATCH_MODES.VARIABLE,
    variable_name: variableName
  }
}

function call (functionName) {
  function caller (...args) {
    const kwargs = typeof args[args.length - 1] === 'object' && !Array.isArray(args[args.length - 1]) ? args.pop() : {}
    return {
      dispatch: DISPATCH_MODES.CALL,
      function_name: functionName,
      args,
      kwargs
    }
  }
  caller.__lo_name__ = functionName
  return caller
}

function select (keys, fields = null) {
  return {
    dispatch: DISPATCH_MODES.SELECT,
    keys,
    fields
  }
}

function join (left, right, leftOn = null, rightOn = null) {
  return {
    dispatch: DISPATCH_MODES.JOIN,
    left,
    right,
    left_on: leftOn,
    right_on: rightOn
  }
}

function map (func, values, valuePath = null, funcKwargs = null, parallel = false) {
  return {
    dispatch: DISPATCH_MODES.MAP,
    function_name: func.__lo_name__,
    values,
    value_path: valuePath,
    func_kwargs: funcKwargs,
    parallel
  }
}

function keys (func, { ...kwargs } = {}) {
  return {
    dispatch: DISPATCH_MODES.KEYS,
    function: func,
    kwargs
  }
}

export {
  parameter,
  call,
  variable,
  select,
  join,
  map,
  keys
}
